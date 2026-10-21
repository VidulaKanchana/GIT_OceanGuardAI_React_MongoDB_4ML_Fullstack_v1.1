import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.db.connection import get_database
from app.api.v1.auth import get_current_user
from app.schemas.ml import (
    C1RiskRequest, C1RiskResponse,
    C2FishingZoneRequest, C2FishingZoneResponse,
    C3MarketForecastRequest, C3MarketDecisionResponse,
    C4FuelPredictRequest, C4FuelPredictResponse,
    IntegratedTripPlanRequest, IntegratedTripPlanResponse
)
from app.ml.component_1_safety.predict import c1_predictor
from app.ml.component_2_fishing.predict import c2_predictor
from app.ml.component_3_market.predict import c3_predictor
from app.ml.component_4_fuel.predict import c4_predictor

router = APIRouter(tags=["Machine Learning & Intelligence"])

@router.post("/ml/c1/predict", response_model=C1RiskResponse)
def predict_c1_risk(req: C1RiskRequest, current_user: dict = Depends(get_current_user)):
    data = req.model_dump() if hasattr(req, 'model_dump') else req.dict()
    res = c1_predictor.predict(data)
    # Save prediction history in DB
    db = get_database()
    db.prediction_history.insert_one({
        "component": "C1",
        "user_id": current_user["user_id"],
        "input": data,
        "output": res,
        "created_at": datetime.utcnow().isoformat()
    })
    return res

@router.post("/ml/c2/predict", response_model=C2FishingZoneResponse)
def predict_c2_zones(req: C2FishingZoneRequest, current_user: dict = Depends(get_current_user)):
    candidate_zones = c2_predictor.recommend_zones(
        departure_port_id=req.departure_port_id,
        target_species=req.target_species,
        max_distance_km=req.max_distance_km
    )
    return {
        "target_species": req.target_species,
        "departure_port_id": req.departure_port_id,
        "candidate_zones": candidate_zones,
        "model_version": "C2-STGCN-SpatialAttn-v1.0",
        "scientific_disclaimer": "HABITAT SUITABILITY ONLY. NOT VERIFIED CATCH PROBABILITY OR SAFE NAVIGATION."
    }

@router.post("/ml/c3/predict", response_model=C3MarketDecisionResponse)
def predict_c3_market(req: C3MarketForecastRequest, current_user: dict = Depends(get_current_user)):
    res = c3_predictor.predict_market_decision(
        species_id=req.species_id,
        catch_kg=req.catch_kg,
        current_port_id=req.current_port_id,
        storage_temp_c=req.storage_temp_c,
        hours_stored=req.hours_stored
    )
    return res

@router.post("/ml/c4/predict", response_model=C4FuelPredictResponse)
def predict_c4_fuel(req: C4FuelPredictRequest, current_user: dict = Depends(get_current_user)):
    data = req.model_dump() if hasattr(req, 'model_dump') else req.dict()
    res = c4_predictor.predict(data)
    return res

@router.post("/trip-planning/evaluate", response_model=IntegratedTripPlanResponse)
def evaluate_integrated_trip(req: IntegratedTripPlanRequest, current_user: dict = Depends(get_current_user)):
    db = get_database()
    vessel = db.vessels.find_one({"vessel_id": req.vessel_id})
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel '{req.vessel_id}' not found.")

    # 1. C1 Safety Evaluation
    c1_out = c1_predictor.predict({
        "vessel_type": vessel.get("vessel_type", "OFRP"),
        "vessel_length_m": vessel.get("length_m", 6.5),
        "vessel_beam_m": vessel.get("beam_m", 1.8),
        "lightship_mass_kg": vessel.get("lightship_mass_kg", 950.0),
        "payload_mass_kg": req.payload_mass_kg,
        "assumed_payload_limit_kg": vessel.get("payload_limit_kg", 1200.0),
        "assumed_lightship_freeboard_m": vessel.get("lightship_freeboard_m", 0.9),
        "planned_trip_duration_h": req.planned_duration_h
    })

    # 2. C2 Fishing Ground Recommendation
    candidate_zones = c2_predictor.recommend_zones(
        departure_port_id=req.departure_port_id,
        target_species=req.target_species,
        max_distance_km=150.0
    )
    best_zone = candidate_zones[0] if candidate_zones else {
        "zone_id": "C2Z005", "latitude": 5.22, "longitude": 80.22,
        "sst_c": 28.15, "chlorophyll_a": 0.17, "habitat_suitability_index": 0.77,
        "distance_km": 90.6, "travel_time_h": 14.0, "estimated_fuel_l": 96.7, "pareto_rank": 1
    }

    # 3. C4 Physics Fuel Requirement
    c4_out = c4_predictor.predict({
        "vessel_length_m": vessel.get("length_m", 6.5),
        "vessel_beam_m": vessel.get("beam_m", 1.8),
        "displacement_mass_kg": vessel.get("lightship_mass_kg", 950.0) + req.payload_mass_kg,
        "travel_roundtrip_distance_km": best_zone["distance_km"] * 2.0,
        "planned_duration_h": req.planned_duration_h,
        "available_fuel_l": req.available_fuel_l
    })

    # Overall recommendation synthesis
    if c1_out["risk_label"] == "Danger":
        rec = "ABORT_HIGH_RISK: Extreme wave or loading conditions predicted. Departure not advised."
    elif c4_out["fuel_sufficiency_status"] == "CRITICAL":
        rec = "ABORT_FUEL_DEFICIENT: Available fuel is below minimum requirement to complete voyage."
    elif c1_out["risk_label"] == "Caution" or c4_out["fuel_sufficiency_status"] == "DEFICIENT":
        rec = "CAUTION_ADVISED: Heightened risk or narrow fuel reserves. Proceed with extra vigilance."
    else:
        rec = "PROCEED_WITH_TRIP: Favorable safety index and adequate fuel margins."

    plan_eval_id = f"EVAL-{uuid.uuid4().hex[:6].upper()}"
    return {
        "trip_evaluation_id": plan_eval_id,
        "c1_safety": c1_out,
        "c2_recommended_zone": best_zone,
        "c4_fuel_plan": c4_out,
        "workflow_recommendation": rec,
        "created_at": datetime.utcnow().isoformat()
    }
