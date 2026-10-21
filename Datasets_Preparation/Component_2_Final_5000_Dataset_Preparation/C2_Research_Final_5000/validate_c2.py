"""Independent post-generation recalculation of CSV and NPZ; does NOT validate catch ecology."""
import csv, math, json
from collections import Counter
from pathlib import Path
import numpy as np
P=Path(__file__).parent

def read(name):
    with (P/name).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
master=read('C2_Master_5000_ZoneDays.csv')
nodes=read('C2_Zone_Registry_100.csv')
edges=read('C2_Graph_Edges_360.csv')
recs=read('C2_Pareto_Example_Recommendations.csv')
manifest=json.loads((P/'C2_Method_Provenance_and_Parameters.json').read_text())
pars=manifest['species_parameters_are_assumptions_not_established_thresholds']
s=manifest['physics_and_cost_scenario'];checks={}
checks['master_exact_5000']=len(master)==5000
checks['zones_exact_100']=len(nodes)==100
checks['exact_50_dates']=len({r['date_utc'] for r in master})==50
checks['all_days_exact_100_nodes']=all(v==100 for v in Counter(r['date_utc'] for r in master).values())
checks['all_nodes_exact_50_days']=all(v==50 for v in Counter(r['zone_id'] for r in master).values())
checks['unique_record_ids']=len({r['record_id'] for r in master})==5000
checks['unique_zone_date_pairs']=len({(r['zone_id'],r['date_utc']) for r in master})==5000
checks['all_synthetic_no_observed_catch']=all('SYNTHETIC' in r['catch_label_provenance'] for r in master)
checks['all_navigation_warnings']=all(r['navigation_status']=='SIMULATION_ONLY_NOT_FOR_REAL_NAVIGATION' for r in master)
checks['spatial_grid_safe_decimal_bounds_scenario_only']=all(5.20<=float(r['zone_latitude_deg'])<=5.80 and 79.7<=float(r['zone_longitude_deg'])<=80.8 for r in master)
checks['edge_count_360']=len(edges)==360
pairs={(r['source_zone_id'],r['target_zone_id']) for r in edges}
checks['all_edges_bidirectional']=all((v,u) in pairs for u,v in pairs)
checks['no_self_neighbor_edges']=all(u!=v for u,v in pairs)
checks['correct_current_speed_vector_norm']=all(abs(float(r['ocean_current_speed_ms'])-math.hypot(float(r['ocean_current_u_ms']),float(r['ocean_current_v_ms'])))<2e-6 for r in master)
checks['chlorophyll_positive']=all(float(r['chlorophyll_a_mg_m3'])>0 for r in master)
checks['front_nonnegative']=all(float(r['sst_front_gradient_c_per_km'])>=0 for r in master)

def suitability(row,species):
    p=pars[species];T=float(row['sst_c']);C=float(row['chlorophyll_a_mg_m3']);G=float(row['sst_front_gradient_c_per_km']);V=float(row['ocean_current_speed_ms']);
    t=math.exp(-.5*((T-p['temperature_optimum_c'])/p['temperature_sigma_c'])**2)
    food=C/(C+p['food_half_saturation_mg_m3']);front=1-math.exp(-G/.026);cur=math.exp(-.5*((V-.22)/.23)**2)
    w=p['score_weights'];return w['temp']*t+w['food']*food+w['front']*front+w['current']*cur
checks['independent_species_suitability_formula_yft']=all(abs(suitability(r,'yellowfin')-float(r['yft_habitat_suitability_index']))<6e-6 for r in master)
checks['independent_species_suitability_formula_skipjack']=all(abs(suitability(r,'skipjack')-float(r['skipjack_habitat_suitability_index']))<6e-6 for r in master)
checks['independent_probability_formula_yft']=all(abs(1/(1+math.exp(-(-2.8+4.4*float(r['yft_habitat_suitability_index']))))-float(r['yft_synthetic_uncalibrated_probability']))<3e-6 for r in master)
checks['independent_probability_formula_skipjack']=all(abs(1/(1+math.exp(-(-2.65+4.25*float(r['skipjack_habitat_suitability_index']))))-float(r['skipjack_synthetic_uncalibrated_probability']))<3e-6 for r in master)
checks['independent_route_factor']=all(abs(float(r['galle_estimated_oneway_route_km'])-float(r['galle_great_circle_km'])*s['route_factor'])<1e-3 for r in master)
checks['independent_roundtrip']=all(abs(float(r['galle_roundtrip_km'])-2*float(r['galle_estimated_oneway_route_km']))<3e-4 for r in master)
checks['independent_transit_duration']=all(abs(float(r['galle_travel_time_h'])-float(r['galle_roundtrip_km'])/(s['speed_knots']*s['one_nautical_mile_km']))<2e-4 for r in master)
checks['independent_stationkeeping_formula']=all(abs(float(r['galle_scenario_site_fuel_l'])-s['site_fishing_hours']*(s['site_idle_fuel_lph']+s['site_current_sensitivity_lph_per_ms']*float(r['ocean_current_speed_ms'])))<1e-4 for r in master)
checks['independent_fuel_sum']=all(abs(float(r['galle_scenario_fuel_l'])-(float(r['galle_scenario_transit_fuel_l'])+float(r['galle_scenario_site_fuel_l'])))<2e-4 for r in master)
checks['independent_fuel_cost']=all(abs(float(r['galle_scenario_fuel_cost_lkr'])-float(r['galle_scenario_fuel_l'])*s['illustrative_fuel_price_lkr_per_l'])<0.06 for r in master)
with np.load(P/'C2_STGCN_Model_Ready_43_Windows.npz') as z:
  X=z['X'];Y=z['y_suitability'];adj=z['normalized_adjacency'];train=z['train_indices'];val=z['val_indices'];test=z['test_indices'];dates=z['target_dates'];
  means=z['feature_mean_train'];stds=z['feature_std_train']
  checks['tensor_shape_X']=X.shape==(43,7,100,5)
  checks['tensor_shape_Y']=Y.shape==(43,100,2)
  checks['tensor_shape_adj']=adj.shape==(100,100)
  checks['tensor_dates_start_end']=str(dates[0])=='2025-01-08' and str(dates[-1])=='2025-02-19'
  checks['adjacency_stochastic_rows']=bool(np.allclose(adj.sum(axis=1),1,atol=1e-6))
  checks['split_29_7_7']=tuple(map(len,(train,val,test)))==(29,7,7)
  checks['disjoint_split']=len(set(train)&set(test))==0 and len(set(train)&set(val))==0 and len(set(val)&set(test))==0
  checks['train_only_centering']=bool(np.allclose(X[train].mean(axis=(0,1,2)),0,atol=.001))
  checks['positive_std']=bool(np.all(stds>0))
  checks['targets_match_master_last_day']=all(abs(float(master[4900+k]['yft_habitat_suitability_index'])-float(Y[-1,k,0]))<2e-6 for k in range(100))
# Compare each Pareto set exactly using recomputed differences, no generator imports.
last={r['zone_id']:r for r in master[-100:]}
port_dist={'P_GALLE':'galle_great_circle_km','P_MIRISSA':'mirissa_great_circle_km','P_TANGALLE':'tangalle_great_circle_km'}
for species,score_key in [('yellowfin','yft_habitat_suitability_index'),('skipjack','skipjack_habitat_suitability_index')]:
  for port,dist_key in port_dist.items():
    cand=[]
    for k,r in last.items():
      d=float(r[dist_key])*s['route_factor']; fuel=2*d/(s['speed_knots']*s['one_nautical_mile_km'])*s['fuel_burn_l_per_h']
      fuel+=s['site_fishing_hours']*(s['site_idle_fuel_lph']+s['site_current_sensitivity_lph_per_ms']*float(r['ocean_current_speed_ms']))
      cand.append((k,float(r[score_key]),d,fuel*s['illustrative_fuel_price_lkr_per_l']))
    found=set()
    for a in cand:
      if not any(b!=a and b[1]>=a[1] and b[2]<=a[2] and b[3]<=a[3] and (b[1]>a[1] or b[2]<a[2] or b[3]<a[3]) for b in cand):found.add(a[0])
    published={r['pareto_zone_id'] for r in recs if r['port_id']==port and r['target_species']==species}
    checks[f'pareto_{species}_{port}']=found==published
report={'independent_numeric_tests':len(checks),'passed':sum(checks.values()),'failed':[k for k,v in checks.items() if not v], 'tests':checks,
 'disclaimer':'Internal scenario self-consistency, not external biological/field validation.'}
(P/'C2_External_Recalculation_QA.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('independent validation:',report['passed'],'/',report['independent_numeric_tests'])
assert not report['failed'],report['failed']
