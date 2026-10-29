import torch
import torch.nn as nn
import torch.nn.functional as F

class TemporalAttention(nn.Module):
    """Bahdanau-style additive attention over Bi-LSTM hidden sequences."""
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Linear(hidden_dim, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, lstm_outputs: torch.Tensor):
        # lstm_outputs: [batch_size, seq_len, hidden_dim]
        energy = torch.tanh(self.attn(lstm_outputs)) # [batch, seq_len, hidden_dim]
        scores = self.v(energy).squeeze(-1) # [batch, seq_len]
        weights = F.softmax(scores, dim=-1) # [batch, seq_len]
        context = torch.bmm(weights.unsqueeze(1), lstm_outputs).squeeze(1) # [batch, hidden_dim]
        return context, weights

class C1BiLSTMAttention(nn.Module):
    """
    Component 1: Bidirectional LSTM with Attention Mechanism for Vessel Safety Risk.
    Fuses static vessel hydro-vulnerability with dynamic temporal weather sequence.
    """
    def __init__(
        self,
        static_dim: int = 6,
        num_vessel_types: int = 4.2,
        vessel_embed_dim: int = 8,
        temporal_dim: int = 7,
        lstm_hidden_dim: int = 32,
        lstm_layers: int = 2,
        dropout: float = 0.2
    ):
        super().__init__()
        # 1. Static Vessel Encoder
        self.vessel_embed = nn.Embedding(num_vessel_types, vessel_embed_dim)
        self.static_dense = nn.Sequential(
            nn.Linear(static_dim + vessel_embed_dim, 32),
            nn.LayerNorm(32),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # 2. Temporal Weather Encoder & Bi-LSTM
        self.temporal_proj = nn.Linear(temporal_dim, 32)
        self.bilstm = nn.LSTM(
            input_size=32,
            hidden_size=lstm_hidden_dim,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if lstm_layers > 1 else 0.0
        )
        
        # 3. Attention Layer
        bilstm_out_dim = lstm_hidden_dim * 2
        self.attention = TemporalAttention(bilstm_out_dim)

        # 4. Feature Fusion Layer
        fusion_dim = 32 + bilstm_out_dim
        self.fusion = nn.Sequential(
            nn.Linear(fusion_dim, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU()
        )

        # 5. Dual Prediction Heads
        # Classification head: Safe (0), Caution (1), Danger (2)
        self.classifier = nn.Linear(32, 3)
        # Regression head: Dynamic Risk Index score (0 - 100)
        self.dri_regressor = nn.Sequential(
            nn.Linear(32, 1),
            nn.Sigmoid() # normalized to 0-1, scaled to 0-100 in forward
        )

    def forward(self, static_feats: torch.Tensor, vessel_type_idx: torch.Tensor, temporal_seq: torch.Tensor):
        # Static branch
        v_emb = self.vessel_embed(vessel_type_idx) # [batch, vessel_embed_dim]
        static_combined = torch.cat([static_feats, v_emb], dim=-1)
        static_encoded = self.static_dense(static_combined) # [batch, 32]

        # Temporal branch
        proj = F.relu(self.temporal_proj(temporal_seq)) # [batch, seq_len, 32]
        lstm_out, _ = self.bilstm(proj) # [batch, seq_len, bilstm_out_dim]
        temp_context, attn_weights = self.attention(lstm_out) # [batch, bilstm_out_dim]

        # Fusion
        fused = torch.cat([static_encoded, temp_context], dim=-1)
        latent = self.fusion(fused)

        # Heads
        logits = self.classifier(latent) # [batch, 3]
        dri_score = self.dri_regressor(latent).squeeze(-1) * 100.0 # [batch]

        return {
            "logits": logits,
            "dri_score": dri_score,
            "attention_weights": attn_weights
        }
