import os
import sys
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np

# Path setup
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.ml.component_1_safety.preprocessing import C1Preprocessor, RISK_LABELS
from app.ml.component_1_safety.model import C1BiLSTMAttention
from app.ml.component_1_safety.dataset import C1Dataset

def train_c1(epochs: int = 15, batch_size: int = 64, lr: float = 0.001):
    print("=== Training Component 1: Dynamic Vessel Safety Risk (Bi-LSTM + Attention) ===")
    c1_path = os.path.join(settings.DATASETS_DIR, "c1_trips.csv")
    if not os.path.exists(c1_path):
        raise FileNotFoundError(f"C1 dataset not found at {c1_path}")

    df = pd.read_csv(c1_path)
    print(f"Loaded {len(df)} records from {c1_path}")

    # Splits from dataset_split column
    train_df = df[df['dataset_split'] == 'train'].reset_index(drop=True)
    val_df = df[df['dataset_split'] == 'validation'].reset_index(drop=True)
    test_df = df[df['dataset_split'] == 'test'].reset_index(drop=True)
    
    if len(val_df) == 0:
        val_df = df.sample(frac=0.15, random_state=42).reset_index(drop=True)
        train_df = df.drop(val_df.index).reset_index(drop=True)

    print(f"Splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # Preprocessing
    preprocessor = C1Preprocessor()
    preprocessor.fit(train_df)

    X_train_static, X_train_vtype, X_train_temp = preprocessor.transform(train_df)
    X_val_static, X_val_vtype, X_val_temp = preprocessor.transform(val_df)
    X_test_static, X_test_vtype, X_test_temp = preprocessor.transform(test_df)

    y_train_cls = np.array([RISK_LABELS.index(lbl) for lbl in train_df['proxy_risk_label']])
    y_val_cls = np.array([RISK_LABELS.index(lbl) for lbl in val_df['proxy_risk_label']])
    y_test_cls = np.array([RISK_LABELS.index(lbl) for lbl in test_df['proxy_risk_label']])

    y_train_dri = train_df['heuristic_dri_score'].values.astype(np.float32)
    y_val_dri = val_df['heuristic_dri_score'].values.astype(np.float32)
    y_test_dri = test_df['heuristic_dri_score'].values.astype(np.float32)

    train_ds = C1Dataset(X_train_static, X_train_vtype, X_train_temp, y_train_cls, y_train_dri)
    val_ds = C1Dataset(X_val_static, X_val_vtype, X_val_temp, y_val_cls, y_val_dri)
    test_ds = C1Dataset(X_test_static, X_test_vtype, X_test_temp, y_test_cls, y_test_dri)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    # Initialize model
    model = C1BiLSTMAttention(
        static_dim=X_train_static.shape[1],
        num_vessel_types=4,
        temporal_dim=X_train_temp.shape[2],
        lstm_hidden_dim=32,
        lstm_layers=2,
        dropout=0.2
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Using device: {device}")

    # Loss & Optimizer
    # Class weights for potential imbalance
    class_counts = np.bincount(y_train_cls, minlength=3)
    weights = torch.tensor([len(y_train_cls) / (3.0 * c + 1e-6) for c in class_counts], dtype=torch.float32).to(device)
    ce_loss_fn = nn.CrossEntropyLoss(weight=weights)
    mse_loss_fn = nn.MSELoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_loss = float('inf')
    artifact_dir = os.path.join(settings.MODEL_ARTIFACTS_DIR, "c1")
    os.makedirs(artifact_dir, exist_ok=True)

    metrics_history = []

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_correct = 0
        total_train = 0

        for batch in train_loader:
            static_f = batch["static_feats"].to(device)
            vtype_idx = batch["vessel_type_idx"].to(device)
            temp_seq = batch["temporal_seq"].to(device)
            labels = batch["label"].to(device)
            dri_target = batch["dri_score"].to(device)

            optimizer.zero_grad()
            out = model(static_f, vtype_idx, temp_seq)
            
            l_cls = ce_loss_fn(out["logits"], labels)
            l_reg = mse_loss_fn(out["dri_score"], dri_target)
            loss = l_cls + 0.01 * l_reg  # combined loss

            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(labels)
            preds = torch.argmax(out["logits"], dim=1)
            train_correct += (preds == labels).sum().item()
            total_train += len(labels)

        train_acc = train_correct / total_train
        avg_train_loss = train_loss / total_train

        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        val_dri_mae = 0.0

        with torch.no_grad():
            for batch in val_loader:
                static_f = batch["static_feats"].to(device)
                vtype_idx = batch["vessel_type_idx"].to(device)
                temp_seq = batch["temporal_seq"].to(device)
                labels = batch["label"].to(device)
                dri_target = batch["dri_score"].to(device)

                out = model(static_f, vtype_idx, temp_seq)
                l_cls = ce_loss_fn(out["logits"], labels)
                l_reg = mse_loss_fn(out["dri_score"], dri_target)
                loss = l_cls + 0.01 * l_reg

                val_loss += loss.item() * len(labels)
                preds = torch.argmax(out["logits"], dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += len(labels)
                val_dri_mae += torch.abs(out["dri_score"] - dri_target).sum().item()

        val_acc = val_correct / val_total
        avg_val_loss = val_loss / val_total
        avg_val_mae = val_dri_mae / val_total

        print(f"Epoch {epoch}/{epochs} | Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.3f} | Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.3f}, DRI MAE: {avg_val_mae:.2f}")

        metrics_history.append({
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "train_acc": train_acc,
            "val_loss": avg_val_loss,
            "val_acc": val_acc,
            "val_dri_mae": avg_val_mae
        })

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), os.path.join(artifact_dir, "best_c1_model.pt"))
            preprocessor.save(os.path.join(artifact_dir, "c1_preprocessor.joblib"))

    # Test evaluation
    model.load_state_dict(torch.load(os.path.join(artifact_dir, "best_c1_model.pt")))
    model.eval()
    test_correct = 0
    test_total = 0
    test_dri_mae = 0.0

    with torch.no_grad():
        for batch in test_loader:
            static_f = batch["static_feats"].to(device)
            vtype_idx = batch["vessel_type_idx"].to(device)
            temp_seq = batch["temporal_seq"].to(device)
            labels = batch["label"].to(device)
            dri_target = batch["dri_score"].to(device)

            out = model(static_f, vtype_idx, temp_seq)
            preds = torch.argmax(out["logits"], dim=1)
            test_correct += (preds == labels).sum().item()
            test_total += len(labels)
            test_dri_mae += torch.abs(out["dri_score"] - dri_target).sum().item()

    test_acc = test_correct / test_total
    test_mae = test_dri_mae / test_total
    print(f"\nFinal Test Evaluation => Accuracy: {test_acc:.4f}, DRI MAE: {test_mae:.2f}")

    eval_summary = {
        "component": "C1_Safety_Prediction",
        "architecture": "Bidirectional LSTM with Additive Temporal Attention",
        "test_accuracy": float(test_acc),
        "test_dri_mae": float(test_mae),
        "best_val_loss": float(best_val_loss),
        "epochs_trained": epochs,
        "classes": RISK_LABELS,
        "history": metrics_history
    }

    with open(os.path.join(artifact_dir, "evaluation_metrics.json"), "w") as f:
        json.dump(eval_summary, f, indent=2)

    print(f"Saved artifacts to {artifact_dir}")

if __name__ == "__main__":
    train_c1(epochs=10)
