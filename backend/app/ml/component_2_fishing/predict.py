import os
import json
import torch
import numpy as np
import pandas as pd
from typing import Dict, Any, List

from app.core.config import settings
from app.ml.component_2_fishing.graph import haversine_distance_km
from app.ml.component_2_fishing.model import C2STGCN
from app.ml.component_2_fishing.optimization import non_dominated_sorting

PORT_COORDINATES = {
    "P_GALLE": (6.033, 80.217),
    "P_MIRISSA": (5.945, 80.455),
    "P_TANGALLE": (6.024, 80.796),
    "P_NEGOMBO": (7.208, 79.835),
    "P_PELIYAGODA": (6.965, 79.885),
    "P_BERUWALA": (6.478, 79.982),
    "P_TRINCOMALEE": (8.571, 81.233)
}

class C2Predictor:
    def __init__(self):
        self.artifact_dir = os.path.join(settings.MODEL_ARTIFACTS_DIR, "c2")
        self.model_path = os.path.join(self.artifact_dir, "best_c2_model.pt")
        self.meta_path = os.path.join(self.artifact_dir, "graph_metadata.json")
        self.adj_path = os.path.join(self.artifact_dir, "norm_adj.npy")
        self.model = None
        self.metadata = None
        self.adj_matrix = None
        self.device = torch.device("cpu")
        self._load()

    def _load(self):
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path) and os.path.exists(self.adj_path):
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)
            self.adj_matrix = np.load(self.adj_path)
            N = self.metadata["num_nodes"]
            T = self.metadata["temporal_window"]
            F_in = len(self.metadata["features"])
            
            self.model = C2STGCN(num_nodes=N, in_features=F_in, temporal_window=T, hidden_dim=32, dropout=0.0)
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

    def recommend_zones(self, departure_port_id: str, target_species: str = "SP_YELLOWFIN", max_distance_km: float = 150.0) -> List[Dict[str, Any]]:
        port_lat, port_lon = PORT_COORDINATES.get(departure_port_id, (6.033, 80.217))
        
        # Load zone coordinates from c2 dataset
        c2_path = os.path.join(settings.DATASETS_DIR, "c2_zone_days.csv")
        df_c2 = pd.read_csv(c2_path)
        zones_unique = df_c2[['zone_id', 'zone_latitude_deg', 'zone_longitude_deg']].drop_duplicates(subset=['zone_id']).sort_values('zone_id').reset_index(drop=True)
        
        candidates = []
        # Get latest day's predictions or environmental values
        latest_day = df_c2['date_utc'].max()
        df_latest = df_c2[df_c2['date_utc'] == latest_day].set_index('zone_id')

        for _, z in zones_unique.iterrows():
            zid = z['zone_id']
            zlat = float(z['zone_latitude_deg'])
            zlon = float(z['zone_longitude_deg'])
            dist = haversine_distance_km(port_lat, port_lon, zlat, zlon)
            
            if dist > max_distance_km:
                continue

            # Fetch or predict HSI
            if zid in df_latest.index:
                row = df_latest.loc[zid]
                hsi = float(row['yft_habitat_suitability_index']) if target_species == "SP_YELLOWFIN" else float(row['skipjack_habitat_suitability_index'])
                sst = float(row['sst_c'])
                chla = float(row['chlorophyll_a_mg_m3'])
            else:
                hsi = 0.65
                sst = 28.2
                chla = 0.18

            # Physics-based trip speed and fuel estimate (assuming 6 knots ~ 11.1 km/h transit)
            speed_kmh = 11.1
            travel_time_h = round((dist * 2.0) / speed_kmh + 3.0, 1) # roundtrip transit + 3 hrs fishing operations
            # Typical small-scale craft fuel consumption: ~0.45 L/km transit + 1.8 L/hr operations
            estimated_fuel_l = round((dist * 2.0 * 0.45) + (3.0 * 1.8), 1)

            candidates.append({
                "zone_id": zid,
                "latitude": round(zlat, 4),
                "longitude": round(zlon, 4),
                "sst_c": round(sst, 2),
                "chlorophyll_a": round(chla, 3),
                "habitat_suitability_index": round(hsi, 3),
                "distance_km": round(dist, 1),
                "travel_time_h": travel_time_h,
                "estimated_fuel_l": estimated_fuel_l
            })

        # Run Pareto Multi-Objective Optimization
        pareto_ranked = non_dominated_sorting(candidates)
        return pareto_ranked[:15] # Top 15 Pareto-optimal candidate fishing zones

c2_predictor = C2Predictor()
