"""Independent post-export cross-file verification for C4 (internal-only)."""
import csv,json,math,collections
from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent
C1=D.parent/'C1_Research_Final_5000' if (D.parent/'C1_Research_Final_5000').exists() else D/'upstream_source_data'; C2=D.parent/'C2_Research_Final_5000' if (D.parent/'C2_Research_Final_5000').exists() else D/'upstream_source_data'
def read(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
r=read(D/'C4_Master_5000_Trip_Scenarios.csv');legs=read(D/'C4_Physics_Legs_10000.csv');eng=read(D/'C4_Synthetic_Engine_Registry_250.csv')
a=read(C1/'C1_Master_5000_Trips.csv');z=read(C2/'C2_Zone_Registry_100.csv')
checks={}
def chk(name,value):checks[name]=bool(value); assert checks[name],f'FAILED: {name}'
chk('exact_master_count_5000',len(r)==5000)
chk('exact_leg_count_10000',len(legs)==10000)
chk('exact_vessel_registry_count_250',len(eng)==250)
chk('unique_scenario_id',len({x['scenario_id'] for x in r})==5000)
chk('unique_c1_trip_ids',len({x['c1_trip_id'] for x in r})==5000)
chk('unique_leg_ids',len({x['leg_id'] for x in legs})==10000)
chk('measured_fuel_intentionally_empty',all(not x['measured_fuel_l'] for x in r))
chk('explicit_provenance_labels',all('SYNTHETIC' in x['fuel_target_provenance'] for x in r))
chk('no_operational_use',all(x['operational_use']=='PROHIBITED_RESEARCH_SIMULATION_ONLY' for x in r))
chk('no_missing_non_measurement_features',all(all(v!='' for k,v in x.items() if k!='measured_fuel_l') for x in r))
chk('all_vessel_classes',set(x['vessel_type'] for x in r)=={'OFRP','IDAY','IMUL'})
chk('all_c2_zone_spatial_link_valid',set(x['c2_spatial_nearest_zone_id'] for x in r).issubset(set(y['zone_id'] for y in z)))
chk('spatial_only_tag_all',all('NOT_TEMPORAL_JOIN' in x['zone_link_scope'] for x in r))
c1d={x['trip_id']:x for x in a}
chk('c1_trip_and_vessel_matching',all(x['c1_trip_id'] in c1d and x['vessel_id']==c1d[x['c1_trip_id']]['vessel_id'] for x in r))
chk('c1_unchanged_weather_height',all(abs(float(x['forecast_wave_hs_m_c1_synthetic'])-float(c1d[x['c1_trip_id']]['forecast_max_wave_height_m']))<1e-8 for x in r))
chk('c1_unchanged_displacement',all(abs(float(x['displacement_mass_kg'])-float(c1d[x['c1_trip_id']]['total_displacement_mass_proxy_kg']))<1e-8 for x in r))
chk('c1_unchanged_duration',all(abs(float(x['planned_duration_h_c1'])-float(c1d[x['c1_trip_id']]['planned_trip_duration_h']))<1e-8 for x in r))
chk('positive_fuel',all(float(x['fuel_consumption_l_model'])>0 for x in r))
chk('positive_speed',all(float(x['outbound_speed_kn_model'])>0 and float(x['inbound_speed_kn_model'])>0 for x in r))
chk('positive_distance',all(float(x['travel_roundtrip_distance_km_scenario'])>0 for x in r))
chk('positive_vessel_dimensions',all(float(x['vessel_beam_m'])>0 and float(x['vessel_length_m'])>0 for x in r))
chk('physically_possible_efficiency',all(0<float(x['propulsive_efficiency_assumed'])<1 for x in r))
chk('bsfc_positive',all(float(x['bsfc_optimum_kg_kwh_assumed'])>0 for x in r))
chk('draft_buoyancy',all(abs(float(x['loaded_draft_m_approx'])-float(x['displacement_mass_kg'])/(1025*float(x['block_coefficient_assumed'])*float(x['vessel_length_m'])*float(x['vessel_beam_m'])))<.002 for x in r))
chk('fuel_reserve_addition',all(abs(float(x['fuel_consumption_l_model'])+float(x['reserve_fuel_l_scenario'])-float(x['fuel_plus_reserve_l_scenario']))<.0002 for x in r))
chk('reserve_fraction_arithmetic',all(abs(float(x['fuel_consumption_l_model'])*float(x['reserve_fraction_assumed_research_only'])-float(x['reserve_fuel_l_scenario']))<.025 for x in r))
chk('fuel_total_sum',all(abs(float(x['fuel_consumption_l_model'])-float(x['transit_fuel_l_model'])-float(x['fishing_fuel_l_model']))<.0002 for x in r))
chk('trip_time_sum',all(abs(float(x['planned_outbound_hours'])+float(x['planned_inbound_hours'])+float(x['fishing_operations_hours'])-float(x['planned_duration_h_c1']))<.0002 for x in r))
chk('scenario_fuel_threshold_flag',all((x['fuel_comparison_flag_research_only']=='SCENARIO_ABOVE_MODEL_REQUIREMENT') == (float(x['available_fuel_l_simulated'])>=float(x['fuel_plus_reserve_l_scenario'])) for x in r))
chk('sensitivity_interval_contains_fuel',all(float(x['sensitivity_low_l_scenario'])<float(x['fuel_consumption_l_model'])<float(x['sensitivity_high_l_scenario']) for x in r))
by=collections.defaultdict(list)
for x in legs:by[x['scenario_id']].append(x)
chk('two_legs_per_trip',all(len(by[x['scenario_id']])==2 for x in r))
chk('two_leg_directions',all({l['direction'] for l in by[x['scenario_id']]}=={'inbound','outbound'} for x in r))
chk('r_components_sum',all(abs(float(x['total_resistance_n'])-sum(float(x[y]) for y in ('frictional_resistance_n','residuary_resistance_heuristic_n','wave_added_resistance_heuristic_n','aerodynamic_resistance_n')))<.0003 for x in legs))
chk('leg_power_R_times_V',all(abs(float(x['effective_power_kw'])-float(x['total_resistance_n'])*float(x['assumed_speed_through_water_kn'])*.514444/1000)<.0005 for x in legs))
chk('leg_not_above_assumed_power_limit',all(float(x['brake_power_kw'])<=float(x['engine_continuous_kw_assumed'])+.0003 for x in legs))
chk('leg_fuel_bsfc_density',all(abs(float(x['leg_fuel_l'])-float(x['brake_power_kw'])*float(x['travel_time_h'])*float(x['bsfc_kg_per_kwh'])/.84)<.0005 for x in legs))
chk('sum_leg_fuel_master',all(abs(sum(float(l['leg_fuel_l']) for l in by[x['scenario_id']])-float(x['transit_fuel_l_model']))<.0002 for x in r))
chk('same_one_way_distance_legs',all(abs(float(l[0]['travel_distance_nm'])-float(l[1]['travel_distance_nm']))<.0001 for l in by.values()))
chk('distance_nm_km_conversion',all(abs(float(x['travel_roundtrip_distance_km_scenario'])-float(x['travel_oneway_distance_nm_scenario'])*2*1.852)<.0002 for x in r))
chk('split_codes_only',set(x['dataset_split_vessel_group'] for x in r)=={'train','validation','test'})
split={s:{x['vessel_id'] for x in r if x['dataset_split_vessel_group']==s} for s in ('train','validation','test')}
chk('vessel_holdout_no_leak',not (split['train']&split['validation'] or split['train']&split['test'] or split['validation']&split['test']))
N=np.load(D/'C4_PINN_Model_Ready_5000.npz')
chk('npz_5000_and_20_features',N['X_raw'].shape==(5000,20) and N['labels_synthetic_l'].shape==(5000,))
chk('npz_label_matches_master',np.allclose(N['labels_synthetic_l'],[float(x['fuel_consumption_l_model']) for x in r],rtol=1e-6,atol=1e-5))
chk('npz_train_normalization_center',np.max(np.abs(N['X_standardized'][N['split_code']==0].mean(axis=0)))<.001)
report={'passed':all(checks.values()),'independent_checks_passed':sum(checks.values()),'check_categories':checks,'science_note':'Only deterministic consistency checks, NOT external physical validation or PINN model performance.','required_future_work':['logged vessel fuel-use volumes or mass over known time','actual engine rpm, horsepower, engine condition','GNSS speed over ground and current/wave measured contemporaneously','wetted area/hull calibration via CAD or tow testing','held-out trials by different real vessels and weather conditions']}
(D/'C4_Independent_Validation_44_Checks.json').write_text(json.dumps(report,indent=2))
print('INDEPENDENT CHECKS:',sum(checks.values()),'PASS; results:',report['passed'])
