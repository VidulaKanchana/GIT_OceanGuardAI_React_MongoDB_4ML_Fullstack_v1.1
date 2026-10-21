import os
import sys
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.ml.component_2_fishing.graph import build_zone_graph
from app.ml.component_2_fishing.model import C2STGCN
from app.ml.component_2_fishing.dataset import C2Dataset

ENV_FEATURES = [
    'sst_c', 'chlorophyll_a_mg_m3', 'ocean_current_u_ms', 
    'ocean_current_v_ms', 'ocean_current_speed_ms', 'sst_front_gradient_c_per_km'
]

def train_c2(epochs: int = 15, lr: float = 0.002, window_size: int = 5):
    print("=== Training Component 2: Fishing Ground Recommendation (ST-GCN + Spatial Attention) ===")
    c2_path = os.path.join(settings.DATASETS_DIR, "c2_zone_days.csv")
    if not os.path.exists(c2_path):
        raise FileNotFoundError(f"C2 dataset not found at {c2_path}")

    df = pd.read_csv(c2_path)
    print(f"Loaded {len(df)} zone-day records from {c2_path}")

    # Build Graph
    norm_adj, dist_mat, zone_to_idx = build_zone_graph(df)
    N = len(zone_to_idx)
    print(f"Constructed spatial graph: {N} zone nodes, Adjacency shape: {norm_adj.shape}")

    # Sort chronologically by date and zone
    df['date_utc'] = pd.to_datetime(df['date_utc'])
    dates = sorted(df['date_utc'].unique())
    num_days = len(dates)
    print(f"Total chronological days: {num_days} ({dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')})")

    # Pivot into 3D array: [num_days, N, num_features]
    F_count = len(ENV_FEATURES)
    data_cube = np.zeros((num_days, N, F_count), dtype=np.float32)
    yft_cube = np.zeros((num_days, N), dtype=np.float32)
    skipjack_cube = np.zeros((num_days, N), dtype=np.float32)

    date_to_t = {d: t for t, d in enumerate(dates)}

    for _, row in df.iterrows():
        t = date_to_t[row['date_utc']]
        n = zone_to_idx[row['zone_id']]
        data_cube[t, n, :] = row[ENV_FEATURES].values
        yft_cube[t, n] = row['yft_habitat_suitability_index']
        skipjack_cube[t, n] = row['skipjack_habitat_suitability_index']

    # Normalize feature cube using training days only
    train_days_cutoff = 35
    val_days_cutoff = 43

    mean_f = np.mean(data_cube[:train_days_cutoff], axis=(0, 1), keepdims=True)
    std_f = np.std(data_cube[:train_days_cutoff], axis=(0, 1), keepdims=True) + 1e-6
    data_cube = (data_cube - mean_f) / std_f

    # Create sliding windows of size window_size
    samples_X = []
    samples_yft = []
    samples_skipjack = []

    for t in range(window_size, num_days):
        window = data_cube[t - window_size:t] # [window_size, N, F]
        window = np.transpose(window, (1, 0, 2)) # [N, window_size, F]
        samples_X.append(window)
        samples_yft.append(yft_cube[t])
        samples_skipjack.append(skipjack_cube[t])

    samples_X = np.array(samples_X)
    samples_yft = np.array(samples_yft)
    samples_skipjack = np.array(samples_skipjack)

    # Temporal Splits
    n_train = train_days_cutoff - window_size
    n_val = val_days_cutoff - train_days_cutoff

    train_X, train_yft, train_skj = samples_X[:n_train], samples_yft[:n_train], samples_skipjack[:n_train]
    val_X, val_yft, val_skj = samples_X[n_train:n_train+n_val], samples_yft[n_train:n_train+n_val], samples_skipjack[n_train:n_train+n_val]
    test_X, test_yft, test_skj = samples_X[n_train+n_val:], samples_yft[n_train+n_val:], samples_skipjack[n_train+n_val:]

    print(f"Sample counts: Train={len(train_X)}, Val={len(val_X)}, Test={len(test_X)}")

    train_ds = C2Dataset(train_X, train_yft, train_skj)
    val_ds = C2Dataset(val_X, val_yft, val_skj)
    test_ds = C2Dataset(test_X, test_yft, test_skj)

    train_loader = DataLoader(train_ds, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=4, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=4, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = C2STGCN(num_nodes=N, in_features=F_count, temporal_window=window_size, hidden_dim=32)
    model.to(device)

    adj_tensor = torch.tensor(norm_adj, dtype=torch.float32, device=device)
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    artifact_dir = os.path.join(settings.MODEL_ARTIFACTS_DIR, "c2")
    os.makedirs(artifact_dir, exist_ok=True)
    best_val_loss = float('inf')

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            x_b = batch["x"].to(device)
            y_yft = batch["y_yft"].to(device)
            y_skj = batch["y_skipjack"].to(device)

            optimizer.zero_grad()
            out = model(x_b, adj_tensor)
            l_yft = loss_fn(out["yft_hsi"], y_yft)
            l_skj = loss_fn(out["skipjack_hsi"], y_skj)
            loss = l_yft + l_skj

            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(x_b)

        avg_train_loss = train_loss / len(train_ds)

        model.eval()
        val_loss = 0.0
        val_mae = 0.0
        with torch.no_grad():
            for batch in val_loader:
                x_b = batch["x"].to(device)
                y_yft = batch["y_yft"].to(device)
                y_skj = batch["y_skipjack"].to(device)

                out = model(x_b, adj_tensor)
                l_yft = loss_fn(out["yft_hsi"], y_yft)
                l_skj = loss_fn(out["skipjack_hsi"], y_skj)
                loss = l_yft + l_skj

                val_loss += loss.item() * len(x_b)
                val_mae += (torch.abs(out["yft_hsi"] - y_yft).mean() + torch.abs(out["skipjack_hsi"] - y_skj).mean()).item() * 0.5 * len(x_b)

        avg_val_loss = val_loss / len(val_ds)
        avg_val_mae = val_mae / len(val_ds)
        print(f"Epoch {epoch}/{epochs} | Train Loss: {avg_train_loss:.5f} | Val Loss: {avg_val_loss:.5f}, Val HSI MAE: {avg_val_mae:.4f}")

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), os.path.join(artifact_dir, "best_c2_model.pt"))

    # Save Graph & Scaler Metadata
    graph_metadata = {
        "num_nodes": N,
        "zone_to_idx": zone_to_idx,
        "features": ENV_FEATURES,
        "mean_f": mean_f.squeeze().tolist(),
        "std_f": std_f.squeeze().tolist(),
        "temporal_window": window_size
    }
    with open(os.path.join(artifact_dir, "graph_metadata.json"), "w") as f:
        json.dump(graph_metadata, f, indent=2)

    np.save(os.path.join(artifact_dir, "norm_adj.npy"), norm_adj)
    np.save(os.path.join(artifact_dir, "dist_matrix.npy"), dist_mat)

    # Test Evaluation
    model.load_state_dict(torch.load(os.path.join(artifact_dir, "best_c2_model.pt")))
    model.eval()
    test_mae = 0.0
    with torch.no_grad():
        for batch in test_loader:
            x_b = batch["x"].to(device)
            y_yft = batch["y_yft"].to(device)
            y_skj = batch["y_skipjack"].to(device)
            out = model(x_b, adj_tensor)
            test_mae += (torch.abs(out["yft_hsi"] - y_yft).mean() + torch.abs(out["skipjack_hsi"] - y_skj).mean()).item() * 0.5 * len(x_b)

    avg_test_mae = test_mae / len(test_ds)
    print(f"\nFinal Test Evaluation => Average HSI Prediction MAE: {avg_test_mae:.4f}")

    eval_summary = {
        "component": "C2_Fishing_Ground_Recommendation",
        "architecture": "Spatiotemporal Graph Convolutional Network (ST-GCN) with Spatial Attention",
        "spatial_nodes": N,
        "test_hsi_mae": float(avg_test_mae),
        "best_val_loss": float(best_val_loss),
        "temporal_window": window_size
    }
    with open(os.path.join(artifact_dir, "evaluation_metrics.json"), "w") as f:
        json.dump(eval_summary, f, indent=2)

    print(f"C2 Model Artifacts saved to {artifact_dir}")

if __name__ == "__main__":
    train_c2(epochs=10)
