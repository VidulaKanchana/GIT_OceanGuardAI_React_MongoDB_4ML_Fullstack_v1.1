import os
import sys
import json
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd
import numpy as np

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.ml.component_4_fuel.physics import calculate_hydrodynamic_resistance
from app.ml.component_4_fuel.losses import PINNCompositeLoss
from app.ml.component_4_fuel.model import C4PINN

FUEL_FEATURES = [
    'vessel_length_m', 'vessel_beam_m', 'displacement_mass_kg', 
    'engine_rated_kw_assumed', 'travel_roundtrip_distance_km_scenario', 
    'outbound_speed_kn_model', 'forecast_wave_hs_m_c1_synthetic', 
    'forecast_wind_speed_ms_c1_synthetic', 'planned_duration_h_c1'
]

def train_c4(epochs: int = 15, batch_size: int = 64, lr: float = 0.002):
    print("=== Training Component 4: Physics-Informed Fuel Predictor (PINN) ===")
    c4_path = os.path.join(settings.DATASETS_DIR, "c4_fuel_scenarios.csv")
    if not os.path.exists(c4_path):
        raise FileNotFoundError(f"C4 dataset not found at {c4_path}")

    df = pd.read_csv(c4_path)
    print(f"Loaded {len(df)} fuel scenario records from {c4_path}")

    # Splits from dataset_split_vessel_group column
    train_mask = df['dataset_split_vessel_group'] == 'train'
    val_mask = df['dataset_split_vessel_group'] == 'validation'
    test_mask = df['dataset_split_vessel_group'] == 'test'

    train_df = df[train_mask].reset_index(drop=True)
    val_df = df[val_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)
    print(f"Vessel-group aware splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # Compute hydrodynamic physics prior for every row
    def compute_physics_priors(data_df):
        priors = []
        for _, r in data_df.iterrows():
            res = calculate_hydrodynamic_resistance(
                vessel_length_m=r['vessel_length_m'],
                vessel_beam_m=r['vessel_beam_m'],
                displacement_mass_kg=r['displacement_mass_kg'],
                speed_knots=r['outbound_speed_kn_model'],
                wave_hs_m=r['forecast_wave_hs_m_c1_synthetic'],
                wind_speed_ms=r['forecast_wind_speed_ms_c1_synthetic']
            )
            # transit hours = distance / speed
            speed_kmh = r['outbound_speed_kn_model'] * 1.852
            transit_hours = r['travel_roundtrip_distance_km_scenario'] / (speed_kmh + 1e-6)
            transit_fuel = res['fuel_rate_l_h'] * transit_hours
            fishing_fuel = 1.8 * max(0.5, r['planned_duration_h_c1'] - transit_hours)
            priors.append(transit_fuel + fishing_fuel)
        return np.array(priors, dtype=np.float32)

    physics_train = compute_physics_priors(train_df)
    physics_val = compute_physics_priors(val_df)
    physics_test = compute_physics_priors(test_df)

    # Feature Normalization (fit on train only)
    mean_vec = train_df[FUEL_FEATURES].mean().values.astype(np.float32)
    std_vec = train_df[FUEL_FEATURES].std().values.astype(np.float32) + 1e-6

    X_train = ((train_df[FUEL_FEATURES].values - mean_vec) / std_vec).astype(np.float32)
    X_val = ((val_df[FUEL_FEATURES].values - mean_vec) / std_vec).astype(np.float32)
    X_test = ((test_df[FUEL_FEATURES].values - mean_vec) / std_vec).astype(np.float32)

    y_train = train_df['fuel_consumption_l_model'].values.astype(np.float32)
    y_val = val_df['fuel_consumption_l_model'].values.astype(np.float32)
    y_test = test_df['fuel_consumption_l_model'].values.astype(np.float32)

    train_ds = TensorDataset(torch.tensor(X_train), torch.tensor(y_train), torch.tensor(physics_train))
    val_ds = TensorDataset(torch.tensor(X_val), torch.tensor(y_val), torch.tensor(physics_val))
    test_ds = TensorDataset(torch.tensor(X_test), torch.tensor(y_test), torch.tensor(physics_test))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = C4PINN(in_features=len(FUEL_FEATURES), hidden_dims=[64, 64, 32], dropout=0.15)
    model.to(device)

    loss_fn = PINNCompositeLoss(lambda_data=1.0, lambda_physics=0.25, lambda_positivity=0.5)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    artifact_dir = os.path.join(settings.MODEL_ARTIFACTS_DIR, "c4")
    os.makedirs(artifact_dir, exist_ok=True)
    best_val_mae = float('inf')

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_mae = 0.0
        total = 0

        for x_b, y_b, phys_b in train_loader:
            x_b, y_b, phys_b = x_b.to(device), y_b.to(device), phys_b.to(device)
            optimizer.zero_grad()

            pred_fuel, neural_only = model(x_b, phys_b)
            losses = loss_fn(pred_fuel, y_b, phys_b)
            losses["total_loss"].backward()
            optimizer.step()

            train_loss += losses["total_loss"].item() * len(x_b)
            train_mae += torch.abs(pred_fuel - y_b).sum().item()
            total += len(x_b)

        avg_train_loss = train_loss / total
        avg_train_mae = train_mae / total

        # Validation
        model.eval()
        val_mae = 0.0
        val_total = 0
        with torch.no_grad():
            for x_b, y_b, phys_b in val_loader:
                x_b, y_b, phys_b = x_b.to(device), y_b.to(device), phys_b.to(device)
                pred_fuel, _ = model(x_b, phys_b)
                val_mae += torch.abs(pred_fuel - y_b).sum().item()
                val_total += len(x_b)

        avg_val_mae = val_mae / val_total
        print(f"Epoch {epoch}/{epochs} | Train Loss: {avg_train_loss:.4f}, Train MAE: {avg_train_mae:.2f}L | Val MAE: {avg_val_mae:.2f}L")

        if avg_val_mae < best_val_mae:
            best_val_mae = avg_val_mae
            torch.save(model.state_dict(), os.path.join(artifact_dir, "best_c4_model.pt"))

    # Save normalization parameters
    scaler_params = {
        "features": FUEL_FEATURES,
        "mean": mean_vec.tolist(),
        "std": std_vec.tolist(),
        "best_val_mae": float(best_val_mae)
    }
    with open(os.path.join(artifact_dir, "scaler_params.json"), "w") as f:
        json.dump(scaler_params, f, indent=2)

    # Test Evaluation
    model.load_state_dict(torch.load(os.path.join(artifact_dir, "best_c4_model.pt")))
    model.eval()
    test_mae = 0.0
    test_rmse = 0.0
    test_total = 0

    with torch.no_grad():
        for x_b, y_b, phys_b in test_loader:
            x_b, y_b, phys_b = x_b.to(device), y_b.to(device), phys_b.to(device)
            pred_fuel, _ = model(x_b, phys_b)
            test_mae += torch.abs(pred_fuel - y_b).sum().item()
            test_rmse += torch.square(pred_fuel - y_b).sum().item()
            test_total += len(x_b)

    final_test_mae = test_mae / test_total
    final_test_rmse = np.sqrt(test_rmse / test_total)
    print(f"\nFinal Test Evaluation => Fuel MAE: {final_test_mae:.2f}L, RMSE: {final_test_rmse:.2f}L")

    eval_summary = {
        "component": "C4_Physics_Informed_Fuel_Predictor",
        "architecture": "Physics-Informed Neural Network (PINN) with ITTC-1957 Constraints",
        "test_mae_liters": float(final_test_mae),
        "test_rmse_liters": float(final_test_rmse),
        "best_val_mae_liters": float(best_val_mae),
        "epochs_trained": epochs
    }
    with open(os.path.join(artifact_dir, "evaluation_metrics.json"), "w") as f:
        json.dump(eval_summary, f, indent=2)

    print(f"C4 Model Artifacts saved to {artifact_dir}")

if __name__ == "__main__":
    train_c4(epochs=10)
