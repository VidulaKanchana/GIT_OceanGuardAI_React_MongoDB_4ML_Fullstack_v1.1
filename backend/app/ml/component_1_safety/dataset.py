import torch
from torch.utils.data import Dataset
import numpy as np

class C1Dataset(Dataset):
    def __init__(self, static_feats: np.ndarray, vessel_types: np.ndarray, temporal_seqs: np.ndarray, labels: np.ndarray, dri_scores: np.ndarray):
        self.static_feats = torch.tensor(static_feats, dtype=torch.float32)
        self.vessel_types = torch.tensor(vessel_types, dtype=torch.long)
        self.temporal_seqs = torch.tensor(temporal_seqs, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long)
        self.dri_scores = torch.tensor(dri_scores, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "static_feats": self.static_feats[idx],
            "vessel_type_idx": self.vessel_types[idx],
            "temporal_seq": self.temporal_seqs[idx],
            "label": self.labels[idx],
            "dri_score": self.dri_scores[idx]
        }
