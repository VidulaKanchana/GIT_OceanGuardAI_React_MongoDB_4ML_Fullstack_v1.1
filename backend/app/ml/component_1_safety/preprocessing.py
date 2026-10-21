import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

STATIC_NUM_COLS = [
    'vessel_length_m', 'vessel_beam_m', 'lightship_mass_kg', 
    'payload_mass_kg', 'assumed_payload_limit_kg', 'assumed_lightship_freeboard_m'
]

TEMPORAL_NUM_COLS = [
    'forecast_max_wind_ms', 'forecast_max_gust_ms', 
    'forecast_max_wave_height_m', 'forecast_min_pressure_hpa',
    'worst_wave_peak_period_s', 'worst_wave_steepness',
    'worst_lateral_wind_force_proxy_n'
]

VESSEL_TYPES = ['OFRP', 'IDAY', 'IMUL', 'NBSB']
RISK_LABELS = ['Safe', 'Caution', 'Danger']

class C1Preprocessor:
    def __init__(self):
        self.static_mean = {}
        self.static_std = {}
        self.temporal_mean = {}
        self.temporal_std = {}
        self.is_fitted = False

    def compute_physics_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derive hydro-physical features with dimensional consistency."""
        df = df.copy()
        # Loading ratio = payload / payload limit
        df['payload_limit_ratio'] = df['payload_mass_kg'] / (df['assumed_payload_limit_kg'] + 1e-6)
        
        # Estimated displacement = lightship + payload
        df['total_displacement_mass_proxy_kg'] = df['lightship_mass_kg'] + df['payload_mass_kg']
        
        # Approximate extra draft from payload (assuming freshwater/seawater block density ~1025 kg/m3)
        waterplane_area = df['vessel_length_m'] * df['vessel_beam_m'] * 0.7  # approximate waterplane coefficient
        df['estimated_extra_draft_m'] = df['payload_mass_kg'] / (waterplane_area * 1025.0 + 1e-6)
        
        # Loaded freeboard = lightship freeboard - extra draft
        df['estimated_loaded_freeboard_m'] = np.maximum(0.05, df['assumed_lightship_freeboard_m'] - df['estimated_extra_draft_m'])
        
        # Wave steepness = wave height / wave length (lambda ~ 1.56 * T^2)
        wave_length = 1.56 * np.square(df['worst_wave_peak_period_s']) + 1e-6
        df['computed_wave_steepness'] = df['forecast_max_wave_height_m'] / wave_length
        
        return df

    def fit(self, df: pd.DataFrame):
        df_phys = self.compute_physics_features(df)
        for col in STATIC_NUM_COLS:
            self.static_mean[col] = float(df_phys[col].mean())
            self.static_std[col] = float(df_phys[col].std()) if df_phys[col].std() > 0 else 1.0
            
        for col in TEMPORAL_NUM_COLS:
            self.temporal_mean[col] = float(df_phys[col].mean())
            self.temporal_std[col] = float(df_phys[col].std()) if df_phys[col].std() > 0 else 1.0
            
        self.is_fitted = True

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted.")
        df_phys = self.compute_physics_features(df)
        
        # Static numeric features normalized
        static_feats = []
        for col in STATIC_NUM_COLS:
            norm = (df_phys[col].values - self.static_mean[col]) / self.static_std[col]
            static_feats.append(norm)
        static_tensor = np.column_stack(static_feats)
        
        # Vessel type category indices (0-3)
        vessel_type_indices = np.array([
            VESSEL_TYPES.index(vt) if vt in VESSEL_TYPES else 0 
            for vt in df_phys['vessel_type']
        ])
        
        # Temporal features normalized (synthetic 6-step time window constructed around forecast peak)
        temporal_feats = []
        for col in TEMPORAL_NUM_COLS:
            norm = (df_phys[col].values - self.temporal_mean[col]) / self.temporal_std[col]
            temporal_feats.append(norm)
        temporal_base = np.column_stack(temporal_feats) # [N, num_temporal_feats]
        
        # Construct synthetic forecast window of 6 sequence steps around the forecast
        # steps represent [t-2, t-1, t_worst, t+1, t+2, t+3]
        N = len(df_phys)
        T = 6
        F = len(TEMPORAL_NUM_COLS)
        temporal_seq = np.zeros((N, T, F), dtype=np.float32)
        step_factors = [0.85, 0.92, 1.0, 0.95, 0.88, 0.80]
        for t, factor in enumerate(step_factors):
            temporal_seq[:, t, :] = temporal_base * factor
            
        return static_tensor.astype(np.float32), vessel_type_indices.astype(np.int64), temporal_seq.astype(np.float32)

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> 'C1Preprocessor':
        return joblib.load(filepath)
