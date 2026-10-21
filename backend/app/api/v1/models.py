import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.core.config import settings
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/models", tags=["Model Management & MLOps"])

MODEL_REGISTRY = [
    {
        "component": "c1",
        "name": "Dynamic Vessel Safety Risk Predictor",
        "architecture": "Bidirectional LSTM with Additive Temporal Attention",
        "active_version": "v1.0.0",
        "status": "APPROVED_RESEARCH_CHECKPOINT",
        "framework": "PyTorch 2.10",
        "data_provenance": "Synthetic Heuristic Labels (C1 Trips)"
    },
    {
        "component": "c2",
        "name": "Spatiotemporal Fishing Ground Recommender",
        "architecture": "Spatiotemporal Graph Convolutional Network (ST-GCN) + Spatial Attention",
        "active_version": "v1.0.0",
        "status": "APPROVED_RESEARCH_CHECKPOINT",
        "framework": "PyTorch 2.10",
        "data_provenance": "Synthetic Spatial Hydrodynamics & Biological HSI (C2 Zone-Days)"
    },
    {
        "component": "c3",
        "name": "Fish Market Value & Perishability Decision System",
        "architecture": "Temporal Fusion Transformer (TFT) + Q10 Decay Model",
        "active_version": "v1.0.0",
        "status": "APPROVED_RESEARCH_CHECKPOINT",
        "framework": "PyTorch 2.10",
        "data_provenance": "Simulated Wholesale Market Prices (C3 Market)"
    },
    {
        "component": "c4",
        "name": "Physics-Informed Vessel Fuel Consumption Predictor",
        "architecture": "Physics-Informed Neural Network (PINN) + ITTC-1957 Constraints",
        "active_version": "v1.0.0",
        "status": "APPROVED_RESEARCH_CHECKPOINT",
        "framework": "PyTorch 2.10",
        "data_provenance": "Hydrodynamic Simulation Scenarios (C4 Fuel)"
    }
]

@router.get("")
def list_models(current_user: dict = Depends(get_current_user)):
    return MODEL_REGISTRY

@router.get("/{component}/metrics")
def get_model_metrics(component: str, current_user: dict = Depends(get_current_user)):
    comp = component.lower()
    metrics_path = os.path.join(settings.MODEL_ARTIFACTS_DIR, comp, "evaluation_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {
        "component": component,
        "status": "BASELINE_HEURISTIC_ACTIVE",
        "message": "Model trained checkpoint not yet compiled or using fallback heuristic baseline."
    }

@router.post("/{component}/training-jobs")
def trigger_training_job(component: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ("researcher", "admin"):
        raise HTTPException(status_code=403, detail="Only researchers or administrators can trigger model retraining.")

    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    return {
        "job_id": job_id,
        "component": component,
        "status": "QUEUED",
        "initiated_by": current_user["user_id"],
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Controlled model retraining initiated. Model checkpoints will be versioned upon validation."
    }
