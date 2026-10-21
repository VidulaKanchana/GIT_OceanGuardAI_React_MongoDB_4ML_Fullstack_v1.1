from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Component 1: Vessel Safety Risk ---
class C1RiskRequest(BaseModel):
    vessel_id: Optional[str] = None
    vessel_type: str = "OFRP"
    vessel_length_m: float = 6.5
    vessel_beam_m: float = 1.8
    lightship_mass_kg: float = 950.0
    payload_mass_kg: float = 600.0
    forecast_max_wind_ms: float = 12.0
    forecast_max_gust_ms: float = 15.0
    forecast_max_wave_height_m: float = 1.5
    forecast_min_pressure_hpa: float = 1010.0
    worst_wave_peak_period_s: float = 7.0
    worst_wave_steepness: float = 0.02
    worst_lateral_wind_force_proxy_n: float = 800.0
    planned_trip_duration_h: float = 12.0

class C1RiskResponse(BaseModel):
    dri_score: float = Field(..., ge=0, le=100, description="Dynamic Risk Index (0-100)")
    risk_label: str = Field(..., description="Safe, Caution, Danger")
    confidence: float
    dominant_risk_factor: str
    contributing_factors: Dict[str, float]
    model_version: str = "C1-BiLSTM-Attn-v1.0"
    data_provenance: str = "synthetic_proxy_heuristics"
    scientific_disclaimer: str = "RESEARCH DECISION SUPPORT ONLY. NOT A MARITIME CLEARANCE."

# --- Component 2: Fishing Ground Recommendation ---
class C2FishingZoneRequest(BaseModel):
    departure_port_id: str = "P_GALLE"
    target_species: str = "SP_YELLOWFIN"
    date_utc: Optional[str] = "2025-01-01"
    max_distance_km: Optional[float] = 150.0

class RecommendedZone(BaseModel):
    zone_id: str
    latitude: float
    longitude: float
    sst_c: float
    chlorophyll_a: float
    habitat_suitability_index: float
    distance_km: float
    travel_time_h: float
    estimated_fuel_l: float
    pareto_rank: int

class C2FishingZoneResponse(BaseModel):
    target_species: str
    departure_port_id: str
    candidate_zones: List[RecommendedZone]
    model_version: str = "C2-STGCN-SpatialAttn-v1.0"
    scientific_disclaimer: str = "HABITAT SUITABILITY ONLY. NOT VERIFIED CATCH PROBABILITY OR SAFE NAVIGATION."

# --- Component 3: Market Decision Engine ---
class C3MarketForecastRequest(BaseModel):
    species_id: str = "SP_YELLOWFIN"
    catch_kg: float = 100.0
    storage_temp_c: float = 4.0
    hours_stored: float = 6.0
    current_port_id: str = "P_GALLE"

class MarketOption(BaseModel):
    market_id: str
    market_name: str
    port_id: str
    forecasted_price_lkr_kg: float
    estimated_quality_ratio: float
    expected_revenue_lkr: float
    transport_cost_lkr: float
    ice_storage_cost_lkr: float
    expected_net_return_lkr: float
    transport_distance_km: float
    decision_type: str  # SELL_NOW, WAIT, TRANSPORT

class C3MarketDecisionResponse(BaseModel):
    species_id: str
    initial_catch_kg: float
    storage_temp_c: float
    hours_since_catch: float
    quality_retention_percent: float
    recommended_decision: str
    market_evaluations: List[MarketOption]
    model_version: str = "C3-TFT-Perishability-v1.0"
    scientific_disclaimer: str = "SIMULATION FORECAST ONLY. DOES NOT CERTIFY FOOD SAFETY."

# --- Component 4: Physics-Informed Fuel Predictor ---
class C4FuelPredictRequest(BaseModel):
    vessel_id: Optional[str] = None
    vessel_type: str = "OFRP"
    vessel_length_m: float = 6.8
    vessel_beam_m: float = 1.7
    displacement_mass_kg: float = 1450.0
    engine_rated_kw_assumed: float = 15.0
    travel_roundtrip_distance_km: float = 45.0
    planned_speed_kn: float = 5.5
    forecast_wave_hs_m: float = 1.4
    forecast_wind_speed_ms: float = 10.0
    planned_duration_h: float = 10.0
    available_fuel_l: Optional[float] = 25.0

class C4FuelPredictResponse(BaseModel):
    predicted_transit_fuel_l: float
    predicted_fishing_fuel_l: float
    predicted_total_fuel_l: float
    recommended_reserve_l: float
    total_required_fuel_l: float
    available_fuel_l: Optional[float]
    fuel_sufficiency_status: str  # SUFFICIENT, DEFICIENT, CRITICAL
    physics_metrics: Dict[str, float]
    model_version: str = "C4-PINN-ITTC1957-v1.0"
    scientific_disclaimer: str = "PHYSICS-GUIDED ESTIMATION. DOES NOT GUARANTEE VOYAGE SAFETY."

# --- Integrated Trip Evaluation ---
class IntegratedTripPlanRequest(BaseModel):
    vessel_id: str
    departure_port_id: str
    target_species: str = "SP_YELLOWFIN"
    planned_departure: str
    planned_duration_h: float
    payload_mass_kg: float = 500.0
    available_fuel_l: float = 30.0

class IntegratedTripPlanResponse(BaseModel):
    trip_evaluation_id: str
    c1_safety: C1RiskResponse
    c2_recommended_zone: RecommendedZone
    c4_fuel_plan: C4FuelPredictResponse
    workflow_recommendation: str  # PROCEED_WITH_TRIP, CAUTION_ADVISED, ABORT_HIGH_RISK
    created_at: str
