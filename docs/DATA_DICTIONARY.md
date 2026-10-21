# OceanGuard AI — Comprehensive Data Dictionary

This document defines the schema, data types, physical units, permissible ranges, and roles of every variable across the four research datasets.

## Component 1: Vessel Safety Trips (`c1_trips.csv`)

| Column Name | Type | Missing | Sample Value | Role / Physical Meaning |
|---|---|---|---|---|
| `trip_id` | object | 0 | `C1T00001` | Variable in pipeline |
| `decision_timestamp_local` | object | 0 | `2024-02-22T03:00:00` | Variable in pipeline |
| `year` | int64 | 0 | `2024` | Variable in pipeline |
| `month` | int64 | 0 | `2` | Variable in pipeline |
| `zone_id` | object | 0 | `Z06` | Variable in pipeline |
| `zone_description` | object | 0 | `Matara Offshore` | Variable in pipeline |
| `zone_lat` | float64 | 0 | `5.58` | Variable in pipeline |
| `zone_lon` | float64 | 0 | `80.48` | Variable in pipeline |
| `vessel_id` | object | 0 | `V241` | Variable in pipeline |
| `vessel_type` | object | 0 | `OFRP` | Variable in pipeline |
| `vessel_length_m` | float64 | 0 | `6.868` | Variable in pipeline |
| `vessel_beam_m` | float64 | 0 | `1.671` | Variable in pipeline |
| `lightship_mass_kg` | float64 | 0 | `1097.508` | Variable in pipeline |
| `payload_mass_kg` | float64 | 0 | `345.238` | Variable in pipeline |
| `total_displacement_mass_proxy_kg` | float64 | 0 | `1442.746` | Variable in pipeline |
| `assumed_payload_limit_kg` | float64 | 0 | `530.196` | Variable in pipeline |
| `payload_limit_ratio` | float64 | 0 | `0.651` | Variable in pipeline |
| `assumed_lightship_freeboard_m` | float64 | 0 | `0.67` | Variable in pipeline |
| `estimated_extra_draft_m` | float64 | 0 | `0.042` | Variable in pipeline |
| `estimated_loaded_draft_m` | float64 | 0 | `0.277` | Variable in pipeline |
| `estimated_loaded_freeboard_m` | float64 | 0 | `0.628` | Variable in pipeline |
| `planned_trip_duration_h` | float64 | 0 | `7.25` | Variable in pipeline |
| `forecast_window_steps` | int64 | 0 | `12` | Variable in pipeline |
| `worst_forecast_step_index` | int64 | 0 | `11` | Variable in pipeline |
| `forecast_max_wind_ms` | float64 | 0 | `18.157` | Variable in pipeline |
| `forecast_max_gust_ms` | float64 | 0 | `24.135` | Variable in pipeline |
| `forecast_max_wave_height_m` | float64 | 0 | `2.127` | Variable in pipeline |
| `forecast_min_pressure_hpa` | float64 | 0 | `1009.519` | Variable in pipeline |
| `forecast_min_visibility_km` | float64 | 0 | `6.329` | Variable in pipeline |
| `worst_wave_peak_period_s` | float64 | 0 | `8.694` | Variable in pipeline |
| `worst_wave_steepness` | float64 | 0 | `0.01803` | Variable in pipeline |
| `worst_lateral_wind_force_proxy_n` | float64 | 0 | `1672.49` | Variable in pipeline |
| `heuristic_dri_score` | float64 | 0 | `49.764` | Variable in pipeline |
| `sensitivity_p05_dri_score` | float64 | 0 | `43.709` | Variable in pipeline |
| `sensitivity_p95_dri_score` | float64 | 0 | `51.106` | Variable in pipeline |
| `proxy_risk_label` | object | 0 | `Caution` | Variable in pipeline |
| `dominant_proxy_risk_factor` | object | 0 | `wave_length_exposure` | Variable in pipeline |
| `scenario_sampling_stratum` | object | 0 | `severe` | Variable in pipeline |
| `dataset_split` | object | 0 | `train` | Variable in pipeline |
| `label_provenance` | object | 0 | `rule_based_synthetic_proxy_not_incide...` | Variable in pipeline |
| `weather_provenance` | object | 0 | `synthetic_forecast_not_observed` | Variable in pipeline |
| `vessel_provenance` | object | 0 | `synthetic_design_not_measured` | Variable in pipeline |

## Component 2: Fishing Zone Spatiotemporal Days (`c2_zone_days.csv`)

| Column Name | Type | Missing | Sample Value | Role / Physical Meaning |
|---|---|---|---|---|
| `record_id` | object | 0 | `C2R00001` | Variable in pipeline |
| `date_utc` | object | 0 | `2025-01-01` | Variable in pipeline |
| `zone_id` | object | 0 | `C2Z001` | Variable in pipeline |
| `zone_latitude_deg` | float64 | 0 | `5.22` | Variable in pipeline |
| `zone_longitude_deg` | float64 | 0 | `79.78` | Variable in pipeline |
| `c1_nearest_centroid_id` | object | 0 | `Z05` | Variable in pipeline |
| `sst_c` | float64 | 0 | `28.42119` | Variable in pipeline |
| `chlorophyll_a_mg_m3` | float64 | 0 | `0.130989` | Variable in pipeline |
| `ocean_current_u_ms` | float64 | 0 | `0.08361` | Variable in pipeline |
| `ocean_current_v_ms` | float64 | 0 | `0.069906` | Variable in pipeline |
| `ocean_current_speed_ms` | float64 | 0 | `0.108984` | Variable in pipeline |
| `sst_front_gradient_c_per_km` | float64 | 0 | `0.0214604` | Variable in pipeline |
| `yft_temperature_response` | float64 | 0 | `0.98184` | Variable in pipeline |
| `yft_food_response` | float64 | 0 | `0.435195` | Variable in pipeline |
| `yft_habitat_suitability_index` | float64 | 0 | `0.72272` | Variable in pipeline |
| `yft_synthetic_uncalibrated_probability` | float64 | 0 | `0.593866` | Variable in pipeline |
| `skipjack_temperature_response` | float64 | 0 | `0.995078` | Variable in pipeline |
| `skipjack_food_response` | float64 | 0 | `0.39575` | Variable in pipeline |
| `skipjack_habitat_suitability_index` | float64 | 0 | `0.713378` | Variable in pipeline |
| `skipjack_synthetic_uncalibrated_probability` | float64 | 0 | `0.594321` | Variable in pipeline |
| `galle_great_circle_km` | float64 | 0 | `102.6668` | Variable in pipeline |
| `mirissa_great_circle_km` | float64 | 0 | `110.4568` | Variable in pipeline |
| `tangalle_great_circle_km` | float64 | 0 | `143.6594` | Variable in pipeline |
| `galle_estimated_oneway_route_km` | float64 | 0 | `118.0669` | Variable in pipeline |
| `galle_roundtrip_km` | float64 | 0 | `236.1337` | Variable in pipeline |
| `galle_travel_time_h` | float64 | 0 | `15.9378` | Variable in pipeline |
| `galle_scenario_transit_fuel_l` | float64 | 0 | `95.6265` | Variable in pipeline |
| `galle_scenario_site_fuel_l` | float64 | 0 | `11.4875` | Variable in pipeline |
| `galle_scenario_fuel_l` | float64 | 0 | `107.114` | Variable in pipeline |
| `galle_scenario_fuel_cost_lkr` | float64 | 0 | `32134.2` | Variable in pipeline |
| `time_split` | object | 0 | `context_only` | Variable in pipeline |
| `environment_provenance` | object | 0 | `SYNTHETIC_smooth_spatiotemporal_scena...` | Variable in pipeline |
| `catch_label_provenance` | object | 0 | `SYNTHETIC_BIOLOGICAL_HEURISTIC_NO_OBS...` | Variable in pipeline |
| `navigation_status` | object | 0 | `SIMULATION_ONLY_NOT_FOR_REAL_NAVIGATION` | Variable in pipeline |

## Component 3: Fish Market Scenarios (`c3_market_prices.csv`)

| Column Name | Type | Missing | Sample Value | Role / Physical Meaning |
|---|---|---|---|---|
| `record_id` | object | 0 | `C3M00001` | Variable in pipeline |
| `date` | object | 0 | `2025-01-01` | Variable in pipeline |
| `market_id` | object | 0 | `M_PELIYAGODA` | Variable in pipeline |
| `market_name` | object | 0 | `Peliyagoda Central Fish Market` | Variable in pipeline |
| `market_port_id` | object | 0 | `P_PELIYAGODA` | Variable in pipeline |
| `species_id` | object | 0 | `SP_SKIPJACK` | Variable in pipeline |
| `species_name` | object | 0 | `Skipjack tuna` | Variable in pipeline |
| `calendar_day_index` | int64 | 0 | `0` | Variable in pipeline |
| `day_of_week_mon0` | int64 | 0 | `2` | Variable in pipeline |
| `weekend_known_future` | int64 | 0 | `0` | Variable in pipeline |
| `month_known_future` | int64 | 0 | `1` | Variable in pipeline |
| `base_price_assumed_lkr_kg` | float64 | 0 | `740.0` | Variable in pipeline |
| `market_multiplier_assumed` | float64 | 0 | `1.03` | Variable in pipeline |
| `supply_kg_simulated` | float64 | 0 | `2049.34` | Variable in pipeline |
| `baseline_supply_kg_assumed` | float64 | 0 | `1800.0` | Variable in pipeline |
| `supply_ratio_simulated` | float64 | 0 | `1.1385229` | Variable in pipeline |
| `demand_index_simulated` | float64 | 0 | `0.8325553` | Variable in pipeline |
| `market_shock_index_simulated` | float64 | 0 | `0.9483323` | Variable in pipeline |
| `price_lkr_per_kg` | float64 | 0 | `628.48` | Variable in pipeline |
| `data_split` | object | 0 | `train` | Variable in pipeline |
| `data_provenance` | object | 0 | `SYNTHETIC_SCENARIO_NOT_OBSERVED` | Variable in pipeline |
| `price_safety_status` | object | 0 | `NOT_REAL_MARKET_QUOTE` | Variable in pipeline |

## Component 4: Fuel Consumption Scenarios (`c4_fuel_scenarios.csv`)

| Column Name | Type | Missing | Sample Value | Role / Physical Meaning |
|---|---|---|---|---|
| `scenario_id` | object | 0 | `C4T00001` | Variable in pipeline |
| `c1_trip_id` | object | 0 | `C1T00001` | Variable in pipeline |
| `c1_record_date_local` | object | 0 | `2024-02-22T03:00:00` | Variable in pipeline |
| `vessel_id` | object | 0 | `V241` | Variable in pipeline |
| `vessel_type` | object | 0 | `OFRP` | Variable in pipeline |
| `c1_zone_id` | object | 0 | `Z06` | Variable in pipeline |
| `c2_spatial_nearest_zone_id` | object | 0 | `C2Z067` | Variable in pipeline |
| `c2_zone_spatial_offset_km` | float64 | 0 | `4.427` | Variable in pipeline |
| `zone_link_scope` | object | 0 | `SPATIAL_ONLY_C1_2024_C2_2025_NOT_TEMP...` | Variable in pipeline |
| `vessel_length_m` | float64 | 0 | `6.868` | Variable in pipeline |
| `vessel_beam_m` | float64 | 0 | `1.671` | Variable in pipeline |
| `block_coefficient_assumed` | float64 | 0 | `0.442` | Variable in pipeline |
| `lightship_mass_kg` | float64 | 0 | `1097.508` | Variable in pipeline |
| `payload_mass_kg` | float64 | 0 | `345.238` | Variable in pipeline |
| `displacement_mass_kg` | float64 | 0 | `1442.746` | Variable in pipeline |
| `loaded_draft_m_approx` | float64 | 0 | `0.277483` | Variable in pipeline |
| `wetted_surface_m2_approx` | float64 | 0 | `12.1661` | Variable in pipeline |
| `engine_rated_hp_assumed` | float64 | 0 | `18.34` | Variable in pipeline |
| `engine_rated_kw_assumed` | float64 | 0 | `13.6761` | Variable in pipeline |
| `engine_age_years_assumed` | float64 | 0 | `17.45` | Variable in pipeline |
| `engine_continuous_limit_kw_assumed` | float64 | 0 | `9.7912` | Variable in pipeline |
| `propulsive_efficiency_assumed` | float64 | 0 | `0.5188` | Variable in pipeline |
| `bsfc_optimum_kg_kwh_assumed` | float64 | 0 | `0.2654` | Variable in pipeline |
| `maintenance_factor_assumed` | float64 | 0 | `1.1079` | Variable in pipeline |
| `forecast_wave_hs_m_c1_synthetic` | float64 | 0 | `2.127` | Variable in pipeline |
| `wave_peak_period_s_c1_synthetic` | float64 | 0 | `8.694` | Variable in pipeline |
| `forecast_wind_speed_ms_c1_synthetic` | float64 | 0 | `18.157` | Variable in pipeline |
| `wave_heading_cos_synthetic` | float64 | 0 | `-0.60659` | Variable in pipeline |
| `wind_heading_cos_synthetic` | float64 | 0 | `-0.05663` | Variable in pipeline |
| `along_current_outbound_ms_assumed` | float64 | 0 | `-0.24431` | Variable in pipeline |
| `planned_duration_h_c1` | float64 | 0 | `7.25` | Variable in pipeline |
| `travel_oneway_distance_nm_scenario` | float64 | 0 | `6.46318` | Variable in pipeline |
| `travel_roundtrip_distance_km_scenario` | float64 | 0 | `23.9396` | Variable in pipeline |
| `planned_outbound_hours` | float64 | 0 | `1.32902` | Variable in pipeline |
| `planned_inbound_hours` | float64 | 0 | `1.25061` | Variable in pipeline |
| `fishing_operations_hours` | float64 | 0 | `4.67037` | Variable in pipeline |
| `outbound_speed_kn_model` | float64 | 0 | `5.33802` | Variable in pipeline |
| `inbound_speed_kn_model` | float64 | 0 | `4.69314` | Variable in pipeline |
| `outbound_effective_power_kw` | float64 | 0 | `5.0797` | Variable in pipeline |
| `inbound_effective_power_kw` | float64 | 0 | `5.0797` | Variable in pipeline |
| `outbound_brake_power_kw` | float64 | 0 | `9.79124` | Variable in pipeline |
| `inbound_brake_power_kw` | float64 | 0 | `9.79124` | Variable in pipeline |
| `outbound_friction_n` | float64 | 0 | `134.2913` | Variable in pipeline |
| `outbound_residuary_heuristic_n` | float64 | 0 | `148.0291` | Variable in pipeline |
| `outbound_wave_resistance_heuristic_n` | float64 | 0 | `1565.0796` | Variable in pipeline |
| `outbound_air_resistance_n` | float64 | 0 | `2.3788` | Variable in pipeline |
| `outbound_total_resistance_n` | float64 | 0 | `1849.7788` | Variable in pipeline |
| `transit_fuel_l_model` | float64 | 0 | `8.86621` | Variable in pipeline |
| `fishing_auxiliary_kw_model` | float64 | 0 | `1.8174` | Variable in pipeline |
| `fishing_fuel_l_model` | float64 | 0 | `3.21395` | Variable in pipeline |
| `fuel_consumption_l_model` | float64 | 0 | `12.08017` | Variable in pipeline |
| `sensitivity_low_l_scenario` | float64 | 0 | `10.00911` | Variable in pipeline |
| `sensitivity_high_l_scenario` | float64 | 0 | `14.77254` | Variable in pipeline |
| `reserve_fraction_assumed_research_only` | float64 | 0 | `0.27544` | Variable in pipeline |
| `reserve_fuel_l_scenario` | float64 | 0 | `3.32733` | Variable in pipeline |
| `fuel_plus_reserve_l_scenario` | float64 | 0 | `15.4075` | Variable in pipeline |
| `available_fuel_l_simulated` | float64 | 0 | `9.18827` | Variable in pipeline |
| `fuel_comparison_flag_research_only` | object | 0 | `SCENARIO_BELOW_MODEL_REQUIREMENT` | Variable in pipeline |
| `speed_limited_on_any_leg` | bool | 0 | `True` | Variable in pipeline |
| `dataset_split_vessel_group` | object | 0 | `train` | Variable in pipeline |
| `measured_fuel_l` | float64 | 5000 | `NULL` | Variable in pipeline |
| `fuel_target_provenance` | object | 0 | `SYNTHETIC_PHYSICS_CONSTRAINED_NOT_MEA...` | Variable in pipeline |
| `confidence_status` | object | 0 | `UNCALIBRATED_NO_REAL_WORLD_CONFIDENCE` | Variable in pipeline |
| `operational_use` | object | 0 | `PROHIBITED_RESEARCH_SIMULATION_ONLY` | Variable in pipeline |

