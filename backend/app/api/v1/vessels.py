import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.connection import get_database
from app.api.v1.auth import get_current_user
from app.schemas.vessel import VesselCreate, VesselUpdate, VesselResponse

router = APIRouter(prefix="/vessels", tags=["Vessels"])

@router.get("", response_model=List[VesselResponse])
def get_vessels(vessel_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = get_database()
    query = {}
    if vessel_type:
        query["vessel_type"] = vessel_type
    
    # If fisherman, return their own vessels plus active fleet reference
    if current_user.get("role") == "fisherman":
        # allow viewing user's own vessels, or all if none
        user_vessels = list(db.vessels.find({"owner_id": current_user["user_id"]}))
        if user_vessels:
            return user_vessels

    vessels = list(db.vessels.find(query).limit(50))
    return vessels

@router.post("", response_model=VesselResponse)
def create_vessel(vessel_in: VesselCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    vessel_id = f"V{uuid.uuid4().hex[:4].upper()}"
    vessel_doc = {
        "vessel_id": vessel_id,
        "owner_id": current_user["user_id"],
        "name": vessel_in.name,
        "vessel_type": vessel_in.vessel_type,
        "length_m": vessel_in.length_m,
        "beam_m": vessel_in.beam_m,
        "lightship_mass_kg": vessel_in.lightship_mass_kg,
        "payload_limit_kg": vessel_in.payload_limit_kg,
        "lightship_freeboard_m": vessel_in.lightship_freeboard_m,
        "home_port_id": vessel_in.home_port_id,
        "provenance": "user_registered",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    db.vessels.insert_one(vessel_doc)
    return vessel_doc

@router.get("/{vessel_id}", response_model=VesselResponse)
def get_vessel(vessel_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    v = db.vessels.find_one({"vessel_id": vessel_id})
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vessel '{vessel_id}' not found.")
    return v

@router.patch("/{vessel_id}", response_model=VesselResponse)
def update_vessel(vessel_id: str, vessel_update: VesselUpdate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    v = db.vessels.find_one({"vessel_id": vessel_id})
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vessel '{vessel_id}' not found.")

    update_data = {k: v for k, v in vessel_update.dict(exclude_unset=True).items()}
    if update_data:
        db.vessels.update_one({"vessel_id": vessel_id}, {"$set": update_data})
        v.update(update_data)
    return v
