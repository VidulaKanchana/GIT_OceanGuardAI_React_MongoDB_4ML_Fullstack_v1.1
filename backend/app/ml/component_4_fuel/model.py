import torch
import torch.nn as nn
import torch.nn.functional as F

class C4PINN(nn.Module):
    """
    Component 4: Physics-Informed / Physics-Guided Neural Network (PINN).
    Predicts vessel trip fuel consumption under physical hydrodynamic constraints.
    Features combined:
      [length_m, beam_m, displacement_kg, engine_kw, distance_km, speed_kn, wave_hs_m, wind_speed_ms, duration_h]
    """
    def __init__(self, in_features: int = 9, hidden_dims: list = [64, 64, 32], dropout: float = 0.15):
        super().__init__()
        layers = []
        curr_dim = in_features
        for h_dim in hidden_dims:
            layers.append(nn.Linear(curr_dim, h_dim))
            layers.append(nn.LayerNorm(h_dim))
            layers.append(nn.SiLU()) # Smooth Swish activation for physical derivatives
            layers.append(nn.Dropout(dropout))
            curr_dim = h_dim

        self.neural_backbone = nn.Sequential(*layers)
        
        # Dual output heads:
        # 1. Direct fuel consumption head (Liters)
        self.fuel_head = nn.Sequential(
            nn.Linear(curr_dim, 16),
            nn.SiLU(),
            nn.Linear(16, 1),
            nn.Softplus() # Enforces strictly non-negative fuel prediction > 0
        )
        
        # 2. Physics-correction parameter head (adapts engine maintenance/BSFC factor)
        self.physics_factor_head = nn.Sequential(
            nn.Linear(curr_dim, 1),
            nn.Sigmoid() # Scale factor ~ 0.8 - 1.2
        )

    def forward(self, x: torch.Tensor, physics_prior: torch.Tensor = None):
        latent = self.neural_backbone(x)
        neural_fuel = self.fuel_head(latent).squeeze(-1) # [batch]

        if physics_prior is not None:
            # Physics-guided blending: scale physics prior with learned adaptation factor
            correction = 0.8 + 0.4 * self.physics_factor_head(latent).squeeze(-1)
            guided_fuel = 0.7 * neural_fuel + 0.3 * (physics_prior * correction)
            return guided_fuel, neural_fuel
        else:
            return neural_fuel, neural_fuel
