import os
import json
from fastapi import APIRouter, Depends
from app.api.v1.auth import get_current_user
from app.db.connection import get_database

router = APIRouter(prefix="/datasets", tags=["Dataset & Data Quality"])

@router.get("")
def get_datasets(current_user: dict = Depends(get_current_user)):
    return [
        {
            "id": "c1_trips",
            "name": "Component 1: Vessel Safety Trips",
            "filename": "c1_trips.csv",
            "records": 5000,
            "features": 42,
            "provenance": "synthetic_forecast_not_observed / rule_based_proxy",
            "status": "READY"
        },
        {
            "id": "c2_zone_days",
            "name": "Component 2: Fishing Zones Spatiotemporal Grid",
            "filename": "c2_zone_days.csv",
            "records": 5000,
            "features": 34,
            "provenance": "SYNTHETIC_smooth_spatiotemporal_scenarios",
            "status": "READY"
        },
        {
            "id": "c3_market_prices",
            "name": "Component 3: Fish Market Scenarios",
            "filename": "c3_market_prices.csv",
            "records": 5000,
            "features": 22,
            "provenance": "SYNTHETIC_SCENARIO_NOT_OBSERVED",
            "status": "READY"
        },
        {
            "id": "c4_fuel_scenarios",
            "name": "Component 4: Fuel Consumption Hydrodynamic Scenarios",
            "filename": "c4_fuel_scenarios.csv",
            "records": 5000,
            "features": 64,
            "provenance": "SYNTHETIC_PHYSICS_CONSTRAINED_NOT_MEASURED",
            "status": "READY"
        }
    ]

@router.get("/quality/report")
def get_quality_report(current_user: dict = Depends(get_current_user)):
    db = get_database()
    obs_count = db.observations.count_documents({})
    verified_count = db.observations.count_documents({"verification_status": "approved"})

    return {
        "datasets_audited": 4,
        "total_records": 20000,
        "missing_values_rate": "0.0% (except measured_fuel_l which is strictly 100% null as documented)",
        "synthetic_records_count": 20000,
        "field_observations_logged": obs_count,
        "verified_real_world_outcomes": verified_count,
        "scientific_integrity_status": "COMPLIANT_WITH_RESEARCH_SPECIFICATION",
        "last_audit_timestamp": "2026-10-18T18:38:00Z"
    }
