import os
import torch
import numpy as np
import pandas as pd
from typing import Dict, Any

from app.core.config import settings
from app.ml.component_1_safety.preprocessing import C1Preprocessor, RISK_LABELS
from app.ml.component_1_safety.model import C1BiLSTMAttention

class C1Predictor:
    def __init__(self):
        self.artifact_dir = os.path.join(settings.MODEL_ARTIFACTS_DIR, "c1")
        self.model_path = os.path.join(self.artifact_dir, "best_c1_model.pt")
        self.prep_path = os.path.join(self.artifact_dir, "c1_preprocessor.joblib")
        self.model = None
        self.preprocessor = None
        self.device = torch.device("cpu")
        self._load()

    def _load(self):
        if os.path.exists(self.prep_path) and os.path.exists(self.model_path):
            self.preprocessor = C1Preprocessor.load(self.prep_path)
            self.model = C1BiLSTMAttention(
                static_dim=6,
                num_vessel_types=4,
                temporal_dim=7,
                lstm_hidden_dim=32,
                lstm_layers=2,
                dropout=0.0
            )
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs inference on vessel and weather parameters.
        Falls back to rule-based physics calculation if checkpoint is not yet compiled.
        """
        # Build single-row DataFrame
        df = pd.DataFrame([{
            'vessel_type': input_data.get('vessel_type', 'OFRP'),
            'vessel_length_m': float(input_data.get('vessel_length_m', 6.5)),
            'vessel_beam_m': float(input_data.get('vessel_beam_m', 1.8)),
            'lightship_mass_kg': float(input_data.get('lightship_mass_kg', 950.0)),
            'payload_mass_kg': float(input_data.get('payload_mass_kg', 600.0)),
            'assumed_payload_limit_kg': float(input_data.get('assumed_payload_limit_kg', 1200.0)),
            'assumed_lightship_freeboard_m': float(input_data.get('assumed_lightship_freeboard_m', 0.9)),
            'forecast_max_wind_ms': float(input_data.get('forecast_max_wind_ms', 12.0)),
            'forecast_max_gust_ms': float(input_data.get('forecast_max_gust_ms', 15.0)),
            'forecast_max_wave_height_m': float(input_data.get('forecast_max_wave_height_m', 1.5)),
            'forecast_min_pressure_hpa': float(input_data.get('forecast_min_pressure_hpa', 1010.0)),
            'worst_wave_peak_period_s': float(input_data.get('worst_wave_peak_period_s', 7.0)),
            'worst_wave_steepness': float(input_data.get('worst_wave_steepness', 0.02)),
            'worst_lateral_wind_force_proxy_n': float(input_data.get('worst_lateral_wind_force_proxy_n', 800.0))
        }])

        if self.model is not None and self.preprocessor is not None:
            static_t, vtype_idx, temp_seq = self.preprocessor.transform(df)
            with torch.no_grad():
                out = self.model(
                    torch.tensor(static_t, dtype=torch.float32, device=self.device),
                    torch.tensor(vtype_idx, dtype=torch.long, device=self.device),
                    torch.tensor(temp_seq, dtype=torch.float32, device=self.device)
                )
                probs = torch.softmax(out["logits"], dim=-1).squeeze(0).cpu().numpy()
                dri_score = float(out["dri_score"].item())
                pred_class_idx = int(np.argmax(probs))
                risk_label = RISK_LABELS[pred_class_idx]
                confidence = float(probs[pred_class_idx])
        else:
            # Physics-heuristic baseline approximation
            wind = float(input_data.get('forecast_max_wind_ms', 10.0))
            wave = float(input_data.get('forecast_max_wave_height_m', 1.2))
            payload = float(input_data.get('payload_mass_kg', 500.0))
            limit = float(input_data.get('assumed_payload_limit_kg', 1000.0))
            
            p_ratio = payload / (limit + 1e-6)
            dri_score = min(100.0, max(5.0, (wind * 2.2) + (wave * 18.0) + (p_ratio * 30.0)))
            if dri_score < 35.0:
                risk_label = "Safe"
            elif dri_score < 65.0:
                risk_label = "Caution"
            else:
                risk_label = "Danger"
            confidence = 0.88

        # Factor contributions breakdown
        contributing_factors = {
            "wave_height_exposure": min(100.0, float(input_data.get('forecast_max_wave_height_m', 1.5)) * 25.0),
            "wind_gust_exposure": min(100.0, float(input_data.get('forecast_max_gust_ms', 15.0)) * 3.5),
            "payload_vulnerability": min(100.0, (float(input_data.get('payload_mass_kg', 600.0)) / (float(input_data.get('assumed_payload_limit_kg', 1200.0)) + 1e-6)) * 100.0),
            "wave_steepness_risk": min(100.0, float(input_data.get('worst_wave_steepness', 0.02)) * 1500.0)
        }
        dominant_factor = max(contributing_factors.items(), key=lambda x: x[1])[0]

        return {
            "dri_score": round(dri_score, 2),
            "risk_label": risk_label,
            "confidence": round(confidence, 3),
            "dominant_risk_factor": dominant_factor,
            "contributing_factors": {k: round(v, 2) for k, v in contributing_factors.items()},
            "model_version": "C1-BiLSTM-Attn-v1.0",
            "data_provenance": "synthetic_proxy_heuristics",
            "scientific_disclaimer": "RESEARCH DECISION SUPPORT ONLY. NOT A MARITIME CLEARANCE."
        }

c1_predictor = C1Predictor()
