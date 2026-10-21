from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class CatchItem(BaseModel):
    species_id: str
    species_name: str
    weight_kg: float
    storage_temp_c: float = 4.0
    catch_time: Optional[str] = None

class TripBase(BaseModel):
    vessel_id: str
    departure_port_id: str
    target_zone_id: Optional[str] = None
    target_species: Optional[str] = "SP_YELLOWFIN"
    planned_departure: str
    planned_duration_h: float
    initial_cargo_kg: float = 0.0

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    target_zone_id: Optional[str] = None
    status: Optional[str] = None  # planned, active, completed, cancelled
    actual_fuel_consumed_l: Optional[float] = None
    catches: Optional[List[CatchItem]] = None

class TripResponse(TripBase):
    trip_id: str
    skipper_id: str
    status: str
    catches: List[CatchItem] = []
    actual_fuel_consumed_l: Optional[float] = None
    c1_assessment: Optional[Dict[str, Any]] = None
    c2_recommendation: Optional[Dict[str, Any]] = None
    c4_fuel_estimate: Optional[Dict[str, Any]] = None
    created_at: str
