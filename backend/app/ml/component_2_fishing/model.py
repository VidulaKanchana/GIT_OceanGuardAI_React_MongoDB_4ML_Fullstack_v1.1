import torch
import torch.nn as nn
import torch.nn.functional as F

class GraphConvolutionLayer(nn.Module):
    """Spatial Graph Convolution: Z = A_norm * X * W + b."""
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        self.bias = nn.Parameter(torch.FloatTensor(out_features))
        nn.init.xavier_uniform_(self.weight)
        nn.init.zeros_(self.bias)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor):
        # x: [batch, num_nodes, in_features] or [num_nodes, in_features]
        # adj_norm: [num_nodes, num_nodes]
        support = torch.matmul(x, self.weight)
        if support.dim() == 3:
            # Batch mode: support [batch, N, out_f]
            # adj_norm: [N, N]
            out = torch.matmul(adj_norm.unsqueeze(0), support) + self.bias
        else:
            out = torch.matmul(adj_norm, support) + self.bias
        return out

class SpatialAttention(nn.Module):
    """Computes spatial attention weights across zone graph."""
    def __init__(self, in_features: int):
        super().__init__()
        self.w_attn = nn.Linear(in_features, in_features)
        self.v_attn = nn.Linear(in_features, 1, bias=False)

    def forward(self, x: torch.Tensor):
        # x: [batch, num_nodes, features]
        energy = torch.tanh(self.w_attn(x))
        scores = self.v_attn(energy) # [batch, num_nodes, 1]
        weights = F.softmax(scores, dim=1) # [batch, num_nodes, 1]
        attended = x * weights
        return attended, weights

class C2STGCN(nn.Module):
    """
    Component 2: Spatiotemporal Graph Convolutional Network with Spatial Attention.
    Models oceanographic dynamic features (SST, Chlorophyll-a, currents, front gradients)
    across the coastal/offshore spatial graph to predict species-specific Habitat Suitability Index.
    """
    def __init__(
        self,
        num_nodes: int = 100,
        in_features: int = 6, # sst, chla, curr_u, curr_v, curr_speed, sst_gradient
        temporal_window: int = 5,
        hidden_dim: int = 32,
        dropout: float = 0.2
    ):
        super().__init__()
        self.num_nodes = num_nodes
        
        # 1. Temporal 1D Convolution over historical window
        self.temporal_conv = nn.Conv1d(
            in_channels=in_features,
            out_channels=hidden_dim,
            kernel_size=3,
            padding=1
        )
        self.temporal_bn = nn.BatchNorm1d(hidden_dim)

        # 2. Graph Convolution Layers
        self.gcn1 = GraphConvolutionLayer(hidden_dim, hidden_dim)
        self.gcn_bn1 = nn.BatchNorm1d(num_nodes)
        self.gcn2 = GraphConvolutionLayer(hidden_dim, hidden_dim)
        self.gcn_bn2 = nn.BatchNorm1d(num_nodes)

        # 3. Spatial Attention
        self.spatial_attention = SpatialAttention(hidden_dim)

        # 4. Multi-objective Species Prediction Heads (Output in [0, 1])
        # Yellowfin tuna (YFT) HSI head
        self.head_yft = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        # Skipjack tuna HSI head
        self.head_skipjack = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor):
        # x shape: [batch, num_nodes, temporal_window, in_features]
        batch_size, N, T, F_in = x.shape
        
        # Reshape for 1D Temporal Convolution: [(batch * N), F_in, T]
        x_reshaped = x.view(batch_size * N, T, F_in).permute(0, 2, 1)
        temp_out = F.relu(self.temporal_bn(self.temporal_conv(x_reshaped))) # [(batch * N), hidden_dim, T]
        # Max-pool over temporal dimension
        temp_pooled = torch.max(temp_out, dim=-1)[0] # [(batch * N), hidden_dim]
        
        # Reshape to [batch, num_nodes, hidden_dim]
        h_spatial = temp_pooled.view(batch_size, N, -1)

        # Spatial Graph Convolution 1
        h1 = F.relu(self.gcn1(h_spatial, adj_norm))
        h1 = self.gcn_bn1(h1)
        h1 = F.dropout(h1, p=0.2, training=self.training)

        # Spatial Graph Convolution 2
        h2 = F.relu(self.gcn2(h1, adj_norm))
        h2 = self.gcn_bn2(h2)

        # Spatial Attention
        h_attn, attn_weights = self.spatial_attention(h2)

        # Predictions for each node
        yft_hsi = self.head_yft(h_attn).squeeze(-1) # [batch, num_nodes]
        skipjack_hsi = self.head_skipjack(h_attn).squeeze(-1) # [batch, num_nodes]

        return {
            "yft_hsi": yft_hsi,
            "skipjack_hsi": skipjack_hsi,
            "attention_weights": attn_weights
        }
