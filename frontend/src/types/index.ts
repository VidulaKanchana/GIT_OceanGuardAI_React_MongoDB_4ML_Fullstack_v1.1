export type UserRole = 'fisherman' | 'researcher' | 'admin';

export interface User {
  user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: UserRole;
  full_name: string;
  user_id: string;
}

export interface Vessel {
  vessel_id: string;
  owner_id: string;
  name: string;
  vessel_type: string;
  length_m: number;
  beam_m: number;
  lightship_mass_kg: number;
  payload_limit_kg: number;
  lightship_freeboard_m: number;
  home_port_id: string;
  provenance: string;
  is_active: boolean;
  created_at: string;
}

export interface CatchItem {
  species_id: string;
  species_name: string;
  weight_kg: number;
  storage_temp_c: number;
  catch_time?: string;
}

export interface Trip {
  trip_id: string;
  skipper_id: string;
  vessel_id: string;
  departure_port_id: string;
  target_zone_id: string;
  target_species: string;
  planned_departure: string;
  planned_duration_h: number;
  initial_cargo_kg: number;
  status: 'planned' | 'active' | 'completed' | 'cancelled';
  catches: CatchItem[];
  actual_fuel_consumed_l?: number;
  c1_assessment?: C1RiskResult;
  c4_fuel_estimate?: C4FuelResult;
  created_at: string;
}

export interface C1RiskResult {
  dri_score: number;
  risk_label: 'Safe' | 'Caution' | 'Danger';
  confidence: number;
  dominant_risk_factor: string;
  contributing_factors: Record<string, number>;
  model_version: string;
  data_provenance: string;
  scientific_disclaimer: string;
}

export interface RecommendedZone {
  zone_id: string;
  latitude: number;
  longitude: number;
  sst_c: number;
  chlorophyll_a: number;
  habitat_suitability_index: number;
  distance_km: number;
  travel_time_h: number;
  estimated_fuel_l: number;
  pareto_rank: number;
}

export interface C2FishingZoneResult {
  target_species: string;
  departure_port_id: string;
  candidate_zones: RecommendedZone[];
  model_version: string;
  scientific_disclaimer: string;
}

export interface MarketOption {
  market_id: string;
  market_name: string;
  port_id: string;
  forecasted_price_lkr_kg: number;
  estimated_quality_ratio: number;
  expected_revenue_lkr: number;
  transport_cost_lkr: number;
  ice_storage_cost_lkr: number;
  expected_net_return_lkr: number;
  transport_distance_km: number;
  decision_type: 'SELL_NOW' | 'WAIT' | 'TRANSPORT';
}

export interface C3MarketResult {
  species_id: string;
  initial_catch_kg: number;
  storage_temp_c: number;
  hours_since_catch: number;
  quality_retention_percent: number;
  recommended_decision: string;
  market_evaluations: MarketOption[];
  model_version: string;
  scientific_disclaimer: string;
}

export interface C4FuelResult {
  predicted_transit_fuel_l: number;
  predicted_fishing_fuel_l: number;
  predicted_total_fuel_l: number;
  recommended_reserve_l: number;
  total_required_fuel_l: number;
  available_fuel_l?: number;
  fuel_sufficiency_status: 'SUFFICIENT' | 'DEFICIENT' | 'CRITICAL';
  physics_metrics: {
    frictional_resistance_n: number;
    residuary_resistance_n: number;
    wave_resistance_n: number;
    air_drag_n: number;
    total_resistance_n: number;
    effective_power_kw: number;
    brake_power_kw: number;
    reynolds_number: number;
    froude_number: number;
  };
  model_version: string;
  scientific_disclaimer: string;
}

export interface IntegratedTripEvaluation {
  trip_evaluation_id: string;
  c1_safety: C1RiskResult;
  c2_recommended_zone: RecommendedZone;
  c4_fuel_plan: C4FuelResult;
  workflow_recommendation: string;
  created_at: string;
}

export interface Observation {
  observation_id: string;
  submitted_by: string;
  type: string;
  vessel_id?: string;
  trip_id?: string;
  latitude?: number;
  longitude?: number;
  payload: Record<string, any>;
  data_origin: 'observed' | 'synthetic' | 'derived' | 'verified_outcome';
  verification_status: 'pending_review' | 'approved' | 'rejected';
  timestamp: string;
  review_notes?: string;
}

export interface EmergencyEvent {
  event_id: string;
  reported_by: string;
  vessel_id: string;
  latitude: number;
  longitude: number;
  distress_type: string;
  description: string;
  souls_on_board: number;
  status: string;
  transmission_timestamp: string;
  is_offline_sync: boolean;
  maritime_disclaimer: string;
}
