import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.connection import get_database
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/rescue", tags=["Rescue & Emergency Operations"])

class EmergencyEventCreate(BaseModel):
    vessel_id: str
    latitude: float
    longitude: float
    distress_type: str # CAPSIZING_RISK, ENGINE_FAILURE, MEDICAL_EMERGENCY, SINKING, ADRIFT
    description: Optional[str] = "Distress signal initiated by skipper"
    souls_on_board: int = 3
    is_offline_sync: bool = False

@router.post("/emergency")
def report_emergency(evt_in: EmergencyEventCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    event_id = f"SOS-{uuid.uuid4().hex[:6].upper()}"
    event_doc = {
        "event_id": event_id,
        "reported_by": current_user["user_id"],
        "vessel_id": evt_in.vessel_id,
        "latitude": evt_in.latitude,
        "longitude": evt_in.longitude,
        "distress_type": evt_in.distress_type,
        "description": evt_in.description,
        "souls_on_board": evt_in.souls_on_board,
        "status": "TRANSMITTED_TO_SHORE_STATION",
        "transmission_timestamp": datetime.utcnow().isoformat(),
        "is_offline_sync": evt_in.is_offline_sync,
        "maritime_disclaimer": "CRITICAL: This application is an experimental ICT aid and NOT a replacement for IMO-certified GMDSS, EPIRB, or VHF Ch 16."
    }
    db.rescue_events.insert_one(event_doc)
    event_doc["_id"] = str(event_doc.get("_id"))
    return event_doc

@router.get("/events")
def get_emergency_events(current_user: dict = Depends(get_current_user)):
    db = get_database()
    events = list(db.rescue_events.find().sort("transmission_timestamp", -1).limit(50))
    for e in events:
        if "_id" in e:
            e["_id"] = str(e["_id"])
    return events
