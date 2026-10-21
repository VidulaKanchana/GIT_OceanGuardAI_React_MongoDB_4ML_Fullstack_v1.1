import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.db.connection import get_database
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/observations", tags=["Observations & Data Provenance"])

class ObservationCreate(BaseModel):
    type: str  # CATCH_RECORD, FUEL_LOG, WEATHER_STATION, SATELLITE_MEASUREMENT
    vessel_id: Optional[str] = None
    trip_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    payload: Dict[str, Any]
    data_origin: str = "observed"  # observed, synthetic, derived, verified_outcome

class ObservationReview(BaseModel):
    verification_status: str  # approved, rejected, pending_review
    review_notes: Optional[str] = None

@router.get("")
def get_observations(
    obs_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {}
    if obs_type:
        query["type"] = obs_type
    if status_filter:
        query["verification_status"] = status_filter

    observations = list(db.observations.find(query).sort("timestamp", -1).limit(100))
    # serialize MongoDB ObjectIds
    for o in observations:
        if "_id" in o:
            o["_id"] = str(o["_id"])
    return observations

@router.post("")
def create_observation(obs_in: ObservationCreate, current_user: dict = Depends(get_current_user)):
    db = get_database()
    obs_id = f"OBS-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "observation_id": obs_id,
        "submitted_by": current_user["user_id"],
        "type": obs_in.type,
        "vessel_id": obs_in.vessel_id,
        "trip_id": obs_in.trip_id,
        "latitude": obs_in.latitude,
        "longitude": obs_in.longitude,
        "payload": obs_in.payload,
        "data_origin": obs_in.data_origin,
        "verification_status": "pending_review",
        "timestamp": datetime.utcnow().isoformat()
    }
    db.observations.insert_one(doc)
    doc["_id"] = str(doc.get("_id"))
    return doc

@router.post("/{obs_id}/review")
def review_observation(obs_id: str, review: ObservationReview, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ("researcher", "admin"):
        raise HTTPException(status_code=403, detail="Only researchers or administrators can review observation data.")

    db = get_database()
    obs = db.observations.find_one({"observation_id": obs_id})
    if not obs:
        raise HTTPException(status_code=404, detail=f"Observation '{obs_id}' not found.")

    update_fields = {
        "verification_status": review.verification_status,
        "reviewed_by": current_user["user_id"],
        "reviewed_at": datetime.utcnow().isoformat(),
        "review_notes": review.review_notes
    }
    if review.verification_status == "approved":
        update_fields["data_origin"] = "verified_outcome"

    db.observations.update_one({"observation_id": obs_id}, {"$set": update_fields})
    obs.update(update_fields)
    obs["_id"] = str(obs["_id"])
    return obs
