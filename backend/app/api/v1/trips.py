import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.connection import get_database
from app.api.v1.auth import get_current_user
from app.schemas.trip import TripCreate, TripUpdate, TripResponse
from app.ml.component_1_safety.predict import c1_predictor
from app.ml.component_4_fuel.predict import c4_predictor

router = APIRouter(prefix="/trips", tags=["Trips"])

@router.get("", response_model=List[TripResponse])
def get_trips(vessel_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = get_database()
    query = {}
    if vessel_id:
        query["vessel_id"] = vessel_id
    if current_user.get("role") == "fisherman":
        query["skipper_id"] = current_user["user_id"]

    trips = list(db.trips.find(query).sort("created_at", -1).limit(50))
    return trips

@router.post("", response_model=TripResponse)
def create_trip(trip_in: TripCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    vessel = db.vessels.find_one({"vessel_id": trip_in.vessel_id})
    if not vessel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vessel '{trip_in.vessel_id}' not found.")

    trip_id = f"TRIP-{uuid.uuid4().hex[:6].upper()}"

    # Auto-run C1 Safety Assessment
    c1_eval = c1_predictor.predict({
        "vessel_type": vessel.get("vessel_type", "OFRP"),
        "vessel_length_m": vessel.get("length_m", 6.5),
        "vessel_beam_m": vessel.get("beam_m", 1.8),
        "lightship_mass_kg": vessel.get("lightship_mass_kg", 950.0),
        "payload_mass_kg": trip_in.initial_cargo_kg,
        "assumed_payload_limit_kg": vessel.get("payload_limit_kg", 1200.0),
        "assumed_lightship_freeboard_m": vessel.get("lightship_freeboard_m", 0.9),
        "planned_trip_duration_h": trip_in.planned_duration_h
    })

    # Auto-run C4 Fuel Estimate (estimate 40km roundtrip)
    c4_eval = c4_predictor.predict({
        "vessel_length_m": vessel.get("length_m", 6.5),
        "vessel_beam_m": vessel.get("beam_m", 1.8),
        "displacement_mass_kg": vessel.get("lightship_mass_kg", 950.0) + trip_in.initial_cargo_kg,
        "travel_roundtrip_distance_km": 45.0,
        "planned_duration_h": trip_in.planned_duration_h,
        "available_fuel_l": 30.0
    })

    trip_doc = {
        "trip_id": trip_id,
        "skipper_id": current_user["user_id"],
        "vessel_id": trip_in.vessel_id,
        "departure_port_id": trip_in.departure_port_id,
        "target_zone_id": trip_in.target_zone_id or "C2Z005",
        "target_species": trip_in.target_species,
        "planned_departure": trip_in.planned_departure,
        "planned_duration_h": trip_in.planned_duration_h,
        "initial_cargo_kg": trip_in.initial_cargo_kg,
        "status": "planned",
        "catches": [],
        "actual_fuel_consumed_l": None,
        "c1_assessment": c1_eval,
        "c4_fuel_estimate": c4_eval,
        "created_at": datetime.utcnow().isoformat()
    }

    db.trips.insert_one(trip_doc)
    return trip_doc

@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    trip = db.trips.find_one({"trip_id": trip_id})
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trip '{trip_id}' not found.")
    return trip

@router.patch("/{trip_id}", response_model=TripResponse)
def update_trip(trip_id: str, trip_update: TripUpdate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    trip = db.trips.find_one({"trip_id": trip_id})
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trip '{trip_id}' not found.")

    update_dict = trip_update.dict(exclude_unset=True)
    if "catches" in update_dict and update_dict["catches"]:
        # serialize catches
        update_dict["catches"] = [c if isinstance(c, dict) else c.dict() for c in update_dict["catches"]]

    if update_dict:
        db.trips.update_one({"trip_id": trip_id}, {"$set": update_dict})
        trip.update(update_dict)

    return trip
