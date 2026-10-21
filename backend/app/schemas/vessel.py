from typing import Optional, List
from pydantic import BaseModel

class VesselBase(BaseModel):
    name: str
    vessel_type: str  # OFRP, IDAY, IMUL, NBSB
    length_m: float
    beam_m: float
    lightship_mass_kg: float
    payload_limit_kg: float
    lightship_freeboard_m: float
    home_port_id: str = "P_GALLE"

class VesselCreate(VesselBase):
    pass

class VesselUpdate(BaseModel):
    name: Optional[str] = None
    vessel_type: Optional[str] = None
    length_m: Optional[float] = None
    beam_m: Optional[float] = None
    lightship_mass_kg: Optional[float] = None
    payload_limit_kg: Optional[float] = None
    lightship_freeboard_m: Optional[float] = None
    home_port_id: Optional[str] = None
    is_active: Optional[bool] = None

class VesselResponse(VesselBase):
    vessel_id: str
    owner_id: str
    provenance: str
    is_active: bool
    created_at: str
