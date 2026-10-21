import torch
from torch.utils.data import Dataset
import numpy as np

class C2Dataset(Dataset):
    def __init__(self, spatiotemporal_tensor: np.ndarray, yft_targets: np.ndarray, skipjack_targets: np.ndarray):
        # spatiotemporal_tensor: [num_samples, num_nodes, temporal_window, in_features]
        # yft_targets: [num_samples, num_nodes]
        # skipjack_targets: [num_samples, num_nodes]
        self.x = torch.tensor(spatiotemporal_tensor, dtype=torch.float32)
        self.y_yft = torch.tensor(yft_targets, dtype=torch.float32)
        self.y_skipjack = torch.tensor(skipjack_targets, dtype=torch.float32)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return {
            "x": self.x[idx],
            "y_yft": self.y_yft[idx],
            "y_skipjack": self.y_skipjack[idx]
        }
