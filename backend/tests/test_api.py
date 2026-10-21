import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.main import app
from scripts.seed_db import seed
from app.db.connection import get_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    seed()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoints(client):
    r1 = client.get("/health/live")
    assert r1.status_code == 200
    assert r1.json()["status"] == "alive"

    r2 = client.get("/health/ready")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ready"

def test_auth_flow(client):
    # Login as seeded user
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@oceanguard.ai",
        "password": "AdminPass123!"
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    token = data["access_token"]

    # Verify /me endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@oceanguard.ai"

def test_vessel_endpoints(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "fisherman@oceanguard.ai",
        "password": "FishermanPass123!"
    })
    assert login_res.status_code == 200, f"Fisherman login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List vessels
    v_res = client.get("/api/v1/vessels", headers=headers)
    assert v_res.status_code == 200
    vessels = v_res.json()
    assert len(vessels) > 0
    v_id = vessels[0]["vessel_id"]

    # Get single vessel
    single_res = client.get(f"/api/v1/vessels/{v_id}", headers=headers)
    assert single_res.status_code == 200
    assert single_res.json()["vessel_id"] == v_id

def test_ml_component_1_safety(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "fisherman@oceanguard.ai",
        "password": "FishermanPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "vessel_type": "OFRP",
        "vessel_length_m": 6.8,
        "vessel_beam_m": 1.7,
        "lightship_mass_kg": 1000.0,
        "payload_mass_kg": 400.0,
        "forecast_max_wind_ms": 14.0,
        "forecast_max_wave_height_m": 1.8,
        "forecast_min_pressure_hpa": 1008.0
    }
    res = client.post("/api/v1/ml/c1/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "dri_score" in data
    assert "risk_label" in data
    assert data["risk_label"] in ("Safe", "Caution", "Danger")
    assert 0.0 <= data["dri_score"] <= 100.0

def test_ml_component_2_fishing_zones(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "fisherman@oceanguard.ai",
        "password": "FishermanPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "departure_port_id": "P_GALLE",
        "target_species": "SP_YELLOWFIN",
        "max_distance_km": 120.0
    }
    res = client.post("/api/v1/ml/c2/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "candidate_zones" in data
    assert len(data["candidate_zones"]) > 0
    top_zone = data["candidate_zones"][0]
    assert "habitat_suitability_index" in top_zone
    assert "pareto_rank" in top_zone

def test_ml_component_3_market_decision(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "fisherman@oceanguard.ai",
        "password": "FishermanPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "species_id": "SP_YELLOWFIN",
        "catch_kg": 150.0,
        "current_port_id": "P_GALLE",
        "storage_temp_c": 3.0,
        "hours_stored": 8.0
    }
    res = client.post("/api/v1/ml/c3/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "recommended_decision" in data
    assert "quality_retention_percent" in data
    assert "market_evaluations" in data
    assert len(data["market_evaluations"]) > 0

def test_ml_component_4_fuel(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "fisherman@oceanguard.ai",
        "password": "FishermanPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "vessel_length_m": 6.8,
        "vessel_beam_m": 1.7,
        "displacement_mass_kg": 1450.0,
        "travel_roundtrip_distance_km": 40.0,
        "planned_speed_kn": 5.5,
        "available_fuel_l": 25.0
    }
    res = client.post("/api/v1/ml/c4/predict", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_total_fuel_l" in data
    assert data["predicted_total_fuel_l"] > 0
    assert "fuel_sufficiency_status" in data

def test_integrated_trip_pipeline(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "fisherman@oceanguard.ai",
        "password": "FishermanPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch a vessel id
    vessels = client.get("/api/v1/vessels", headers=headers).json()
    v_id = vessels[0]["vessel_id"]

    eval_payload = {
        "vessel_id": v_id,
        "departure_port_id": "P_GALLE",
        "target_species": "SP_YELLOWFIN",
        "planned_departure": "2026-10-19T04:00:00",
        "planned_duration_h": 12.0,
        "payload_mass_kg": 400.0,
        "available_fuel_l": 35.0
    }
    res = client.post("/api/v1/trip-planning/evaluate", json=eval_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "trip_evaluation_id" in data
    assert "c1_safety" in data
    assert "c2_recommended_zone" in data
    assert "c4_fuel_plan" in data
    assert "workflow_recommendation" in data
