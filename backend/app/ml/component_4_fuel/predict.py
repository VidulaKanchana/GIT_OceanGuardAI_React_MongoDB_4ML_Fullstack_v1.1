import os
import json
import torch
import numpy as np
from typing import Dict, Any

from app.core.config import settings
from app.ml.component_4_fuel.physics import calculate_hydrodynamic_resistance
from app.ml.component_4_fuel.model import C4PINN

class C4Predictor:
    def __init__(self):
        self.artifact_dir = os.path.join(settings.MODEL_ARTIFACTS_DIR, "c4")
        self.model_path = os.path.join(self.artifact_dir, "best_c4_model.pt")
        self.scaler_path = os.path.join(self.artifact_dir, "scaler_params.json")
        self.model = None
        self.scaler = None
        self.device = torch.device("cpu")
        self._load()

    def _load(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            with open(self.scaler_path, "r") as f:
                self.scaler = json.load(f)
            self.model = C4PINN(in_features=len(self.scaler["features"]), hidden_dims=[64, 64, 32], dropout=0.0)
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs Physics-Informed Neural Network prediction combined with ITTC-1957 hydrodynamic calculations.
        """
        length_m = float(input_data.get('vessel_length_m', 6.8))
        beam_m = float(input_data.get('vessel_beam_m', 1.7))
        displacement_kg = float(input_data.get('displacement_mass_kg', 1450.0))
        speed_kn = float(input_data.get('planned_speed_kn', 5.5))
        dist_km = float(input_data.get('travel_roundtrip_distance_km', 45.0))
        wave_hs_m = float(input_data.get('forecast_wave_hs_m', 1.4))
        wind_speed_ms = float(input_data.get('forecast_wind_speed_ms', 10.0))
        duration_h = float(input_data.get('planned_duration_h', 10.0))
        available_fuel_l = input_data.get('available_fuel_l', None)
        if available_fuel_l is not None:
            available_fuel_l = float(available_fuel_l)

        # 1. Physics Calculations
        physics_res = calculate_hydrodynamic_resistance(
            vessel_length_m=length_m,
            vessel_beam_m=beam_m,
            displacement_mass_kg=displacement_kg,
            speed_knots=speed_kn,
            wave_hs_m=wave_hs_m,
            wind_speed_ms=wind_speed_ms
        )

        speed_kmh = max(1.0, speed_kn * 1.852)
        transit_hours = dist_km / speed_kmh
        fishing_hours = max(0.0, duration_h - transit_hours)

        physics_transit_fuel = physics_res['fuel_rate_l_h'] * transit_hours
        fishing_auxiliary_rate = 1.8 # typical small generator/slow trolling fuel rate L/h
        physics_fishing_fuel = fishing_auxiliary_rate * fishing_hours
        physics_total_fuel = physics_transit_fuel + physics_fishing_fuel

        # 2. Neural PINN Prediction
        if self.model is not None and self.scaler is not None:
            mean = np.array(self.scaler["mean"])
            std = np.array(self.scaler["std"])
            raw_features = np.array([
                length_m, beam_m, displacement_kg,
                float(input_data.get('engine_rated_kw_assumed', 15.0)),
                dist_km, speed_kn, wave_hs_m, wind_speed_ms, duration_h
            ], dtype=np.float32)
            norm_features = (raw_features - mean) / std

            with torch.no_grad():
                x_t = torch.tensor(norm_features, dtype=torch.float32).unsqueeze(0)
                phys_t = torch.tensor([physics_total_fuel], dtype=torch.float32)
                pred_total, _ = self.model(x_t, phys_t)
                predicted_total = float(pred_total.item())
        else:
            predicted_total = physics_total_fuel

        predicted_transit = round(predicted_total * (transit_hours / max(0.1, duration_h)), 2)
        predicted_fishing = round(max(0.0, predicted_total - predicted_transit), 2)
        recommended_reserve = round(predicted_total * 0.20, 2) # Standard 20% maritime contingency reserve
        total_required = round(predicted_total + recommended_reserve, 2)

        # Fuel Sufficiency Status
        if available_fuel_l is not None:
            if available_fuel_l >= total_required:
                status = "SUFFICIENT"
            elif available_fuel_l >= predicted_total:
                status = "DEFICIENT" # Covers trip but breaches safety reserve margin!
            else:
                status = "CRITICAL" # Insufficient to even complete projected trip!
        else:
            status = "SUFFICIENT"

        return {
            "predicted_transit_fuel_l": predicted_transit,
            "predicted_fishing_fuel_l": predicted_fishing,
            "predicted_total_fuel_l": round(predicted_total, 2),
            "recommended_reserve_l": recommended_reserve,
            "total_required_fuel_l": total_required,
            "available_fuel_l": available_fuel_l,
            "fuel_sufficiency_status": status,
            "physics_metrics": {
                "frictional_resistance_n": round(physics_res["frictional_resistance_n"], 1),
                "residuary_resistance_n": round(physics_res["residuary_resistance_n"], 1),
                "wave_resistance_n": round(physics_res["wave_resistance_n"], 1),
                "air_drag_n": round(physics_res["air_drag_n"], 1),
                "total_resistance_n": round(physics_res["total_resistance_n"], 1),
                "effective_power_kw": round(physics_res["effective_power_kw"], 2),
                "brake_power_kw": round(physics_res["brake_power_kw"], 2),
                "reynolds_number": round(physics_res["reynolds_number"], 0),
                "froude_number": round(physics_res["froude_number"], 3)
            },
            "model_version": "C4-PINN-ITTC1957-v1.0",
            "scientific_disclaimer": "PHYSICS-GUIDED ESTIMATION. DOES NOT GUARANTEE VOYAGE SAFETY."
        }

c4_predictor = C4Predictor()
