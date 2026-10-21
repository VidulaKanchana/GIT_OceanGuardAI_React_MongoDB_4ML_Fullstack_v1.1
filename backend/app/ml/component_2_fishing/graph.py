import numpy as np
import pandas as pd
from typing import Tuple, Dict

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute Great-Circle geodesic distance in kilometers between two geographic points."""
    R = 6371.0 # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2.0) ** 2 + 
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0) ** 2)
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return R * c

def build_zone_graph(df_zones: pd.DataFrame, sigma_km: float = 25.0, distance_threshold_km: float = 60.0) -> Tuple[np.ndarray, np.ndarray, Dict[str, int]]:
    """
    Constructs normalized spatial graph adjacency matrix for fishing zones using Gaussian RBF kernel.
    """
    zones_unique = df_zones[['zone_id', 'zone_latitude_deg', 'zone_longitude_deg']].drop_duplicates(subset=['zone_id']).sort_values('zone_id').reset_index(drop=True)
    N = len(zones_unique)
    zone_to_idx = {row['zone_id']: idx for idx, row in zones_unique.iterrows()}
    
    coords = zones_unique[['zone_latitude_deg', 'zone_longitude_deg']].values
    dist_matrix = np.zeros((N, N), dtype=np.float32)
    
    for i in range(N):
        for j in range(i, N):
            d = haversine_distance_km(coords[i, 0], coords[i, 1], coords[j, 0], coords[j, 1])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d
            
    # Gaussian RBF Kernel with distance cutoff
    adj_matrix = np.exp(-np.square(dist_matrix) / (2.0 * sigma_km ** 2))
    adj_matrix[dist_matrix > distance_threshold_km] = 0.0
    np.fill_diagonal(adj_matrix, 1.0) # Self-loops
    
    # Symmetric Laplacian Normalization D^(-1/2) * A * D^(-1/2)
    degrees = np.sum(adj_matrix, axis=1)
    d_inv_sqrt = np.power(degrees, -0.5)
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
    d_mat_inv_sqrt = np.diag(d_inv_sqrt)
    normalized_adj = np.dot(np.dot(d_mat_inv_sqrt, adj_matrix), d_mat_inv_sqrt)
    
    return normalized_adj.astype(np.float32), dist_matrix.astype(np.float32), zone_to_idx
