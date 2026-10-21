import torch
import torch.nn as nn
import torch.nn.functional as F

class PINNCompositeLoss(nn.Module):
    """
    Composite loss for Physics-Informed Neural Network:
    L_total = lambda_data * L_data + lambda_physics * L_physics + lambda_constraints * L_positivity
    """
    def __init__(self, lambda_data: float = 1.0, lambda_physics: float = 0.3, lambda_positivity: float = 0.5):
        super().__init__()
        self.lambda_data = lambda_data
        self.lambda_physics = lambda_physics
        self.lambda_positivity = lambda_positivity
        self.mse = nn.MSELoss()

    def forward(self, pred_fuel: torch.Tensor, target_fuel: torch.Tensor, physics_fuel: torch.Tensor):
        # 1. Data Loss against target
        l_data = self.mse(pred_fuel, target_fuel)
        
        # 2. Physics Consistency Loss against physical hydrodynamic baseline
        l_physics = self.mse(pred_fuel, physics_fuel)
        
        # 3. Positivity Constraint (Fuel consumption must be strictly positive)
        l_positivity = torch.mean(F.relu(-pred_fuel) ** 2)
        
        total_loss = (self.lambda_data * l_data + 
                      self.lambda_physics * l_physics + 
                      self.lambda_positivity * l_positivity)
        
        return {
            "total_loss": total_loss,
            "loss_data": l_data,
            "loss_physics": l_physics,
            "loss_positivity": l_positivity
        }
