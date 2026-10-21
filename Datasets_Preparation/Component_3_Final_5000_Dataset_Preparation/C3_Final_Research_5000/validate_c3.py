#!/usr/bin/env python3
"""Independent recomputation of generated C3 data and basic TFT leakage checks."""
import csv, json, math
from pathlib import Path
from collections import Counter,defaultdict
from datetime import date, timedelta
import numpy as np
ROOT=Path(__file__).resolve().parent

def load(filename):
 with (ROOT/filename).open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
M=load('C3_Master_5000_Daily_Market_Prices.csv')
S=load('C3_Lot_Decision_Scenarios_1250.csv')
O=load('C3_Option_Economics_5000.csv')
T=load('C3_Option_Temperature_20000_Segments.csv')
SP=load('C3_Species_Assumptions.csv')
GROUP=load('C3_TFT_Group_Index.csv')
passlog=[]
def check(name,pred):
 if not pred: raise AssertionError(f'FAILED: {name}')
 passlog.append({'test':name,'result':'PASS'})

def eq(a,b,tol=.04):return abs(float(a)-float(b))<=tol
check('Primary exactly 5,000 rows',len(M)==5000)
check('Decision 1,250 rows',len(S)==1250)
check('Options 5,000 rows',len(O)==5000)
check('Temperature 20,000 rows',len(T)==20000)
check('Exactly 5 species',len(set(r['species_id'] for r in M))==5)
check('Exactly 5 markets',len(set(r['market_id'] for r in M))==5)
check('Exactly 200 distinct dates',len(set(r['date'] for r in M))==200)
check('Date bounds 2025-01-01 through 2025-07-19',min(r['date'] for r in M)=='2025-01-01' and max(r['date'] for r in M)=='2025-07-19')
check('Each market×species =200 days',set(Counter((r['market_id'],r['species_id']) for r in M).values())=={200})
check('Each date has 25 records',set(Counter(r['date'] for r in M).values())=={25})
check('Market rows unique composite date key',len(set((r['date'],r['market_id'],r['species_id']) for r in M))==5000)
check('All market record IDs distinct',len(set(r['record_id'] for r in M))==5000)
check('Zero blank cells master',all(all(str(v).strip() for v in r.values()) for r in M))
check('Every master row synthetic provenance',all(r['data_provenance']=='SYNTHETIC_SCENARIO_NOT_OBSERVED' for r in M))
check('Positive prices and simulated supply',all(float(r['price_lkr_per_kg'])>0 and float(r['supply_kg_simulated'])>0 for r in M))
check('Demand index positive',all(float(r['demand_index_simulated'])>0 for r in M))
check('Weekend consistent with date',all(int(r['weekend_known_future'])==int(date.fromisoformat(r['date']).weekday()>=5) for r in M))
check('Month consistent with date',all(int(r['month_known_future'])==date.fromisoformat(r['date']).month for r in M))
check('Chronological train,val,test dates',all(r['data_split']==('train' if int(r['calendar_day_index'])<140 else 'validation' if int(r['calendar_day_index'])<170 else 'test') for r in M))
check('Synthetic structural market price recomputed',all(eq(r['price_lkr_per_kg'],float(r['base_price_assumed_lkr_kg'])*float(r['market_multiplier_assumed'])*float(r['demand_index_simulated'])**.48*float(r['supply_ratio_simulated'])**(-.40)*float(r['market_shock_index_simulated']),.02) for r in M))
check('Supply ratio consistent with supply and baseline',all(eq(float(r['supply_kg_simulated'])/float(r['baseline_supply_kg_assumed']),r['supply_ratio_simulated'],.00001) for r in M))
check('Distinct option IDs',len(set(r['option_id'] for r in O))==len(O))
check('Exactly 4 options per scenario',set(Counter(r['scenario_id'] for r in O).values())=={4})
check('Required choices per scenario',all(Counter(r['action'] for r in O if r['scenario_id']==sid)==Counter({'SELL_NOW':1,'WAIT_24H':1,'TRANSPORT_NOW':2}) for sid in set(r['scenario_id'] for r in O)))
check('Every decision scenario has four temp histories',set(Counter(r['option_id'] for r in T).values())=={4})
check('Segments in 1 to 4 sequence',all(set(int(s['segment_sequence']) for s in T if s['option_id']==oid)=={1,2,3,4} for oid in set(s['option_id'] for s in T)))
check('No negative durations in temperature history',all(float(r['duration_h'])>=0 for r in T))
check('Temperature < reasonable scenario range 0..12C',all(0<=float(r['fish_temperature_c_simulated'])<=12 for r in T))
check('Every simulated option retains same lot weight across its four choices',all(max(float(o['lot_weight_kg']) for o in O if o['scenario_id']==sid)-min(float(o['lot_weight_kg']) for o in O if o['scenario_id']==sid)<.001 for sid in set(r['scenario_id'] for r in O)))
sp_lookup={p['species_id']:p for p in SP}
opt_sp={o['option_id']:sp_lookup[o['species_id']] for o in O}
check('Arrhenius rate recomputed independently',all(eq(seg['k_per_hour_arrhenius_assumed'],float(opt_sp[seg['option_id']]['k_ref_per_h_assumption'])*math.exp(-float(opt_sp[seg['option_id']]['Arrhenius_Ea_j_per_mol_assumption'])/8.314462618*(1/(float(seg['fish_temperature_c_simulated'])+273.15)-1/273.15)),1e-6) for seg in T))
check('Spoilage dose equals k × hours',all(eq(seg['spoilage_dose_increment'],float(seg['k_per_hour_arrhenius_assumed'])*float(seg['duration_h']),1e-6) for seg in T))
dose_sums=defaultdict(float)
for seg in T: dose_sums[seg['option_id']]+=float(seg['spoilage_dose_increment'])
check('Option damage dose equals all segment damages',all(eq(o['cold_chain_spoilage_dose'],dose_sums[o['option_id']],1e-6) for o in O))
check('Option freshness equals exp(-dose)',all(eq(o['freshness_quality_proxy_0_1'],math.exp(-dose_sums[o['option_id']]),1e-6) for o in O))
check('Freshness always between 0 and 1',all(0<float(o['freshness_quality_proxy_0_1'])<=1 for o in O))
check('Monotonic quality valuation multiplier',all(eq(o['quality_discount_multiplier_assumption'],1-.22*(1-float(o['freshness_quality_proxy_0_1'])),1e-6) for o in O))
check('Saleable fraction proxy recomputed',all(eq(o['saleable_fraction_assumption'],.98-.065*(1-float(o['freshness_quality_proxy_0_1'])),1e-6) for o in O))
check('Market fees, travel and ice net return formula',all(eq(o['expected_net_return_lkr'],float(o['estimated_saleable_kg'])*float(o['decision_time_price_estimate_lkr_kg'])*float(o['quality_discount_multiplier_assumption'])*(.984)-float(o['transport_cost_lkr'])-float(o['ice_cost_lkr'])-float(o['handling_cost_lkr']),.18) for o in O))
check('Ex-post economics recomputed',all(eq(o['ex_post_net_return_lkr'],float(o['estimated_saleable_kg'])*float(o['ex_post_next_day_or_same_day_price_lkr_kg'])*float(o['quality_discount_multiplier_assumption'])*(.984)-float(o['transport_cost_lkr'])-float(o['ice_cost_lkr'])-float(o['handling_cost_lkr']),.18) for o in O))
check('Net returns all finite',all(math.isfinite(float(o['expected_net_return_lkr'])) for o in O))
check('Transport distances zero if not transporting',all(float(o['estimated_route_km_synthetic'])==0 for o in O if o['action']!='TRANSPORT_NOW'))
check('Only transport options have positive route distances',all(float(o['estimated_route_km_synthetic'])>0 for o in O if o['action']=='TRANSPORT_NOW'))
check('No negative transport or icing costs',all(float(o['transport_cost_lkr'])>=0 and float(o['ice_cost_lkr'])>=0 for o in O))
check('Transport costs = km×175 LKR/km',all(eq(o['transport_cost_lkr'],float(o['estimated_route_km_synthetic'])*175,.02) for o in O))
check('No ex-post future price used in immediate price forecast',all(eq(o['decision_time_price_estimate_lkr_kg'],o['observed_same_day_synthetic_quote_lkr_kg'],.001) for o in O if o['action']!='WAIT_24H'))
check('At least some wait forecasts differ from ex-post tomorrow',any(not eq(o['decision_time_price_estimate_lkr_kg'],o['ex_post_next_day_or_same_day_price_lkr_kg'],.01) for o in O if o['action']=='WAIT_24H'))
option_per_scenario=defaultdict(list)
for o in O: option_per_scenario[o['scenario_id']].append(o)
check('Recommended option has maximum *predicted* net return',all(s['scenario_best_option_id']==max(option_per_scenario[s['scenario_id']],key=lambda x:float(x['expected_net_return_lkr']))['option_id'] for s in S))
check('Oracle chosen from *ex-post* and kept separate',all(s['ex_post_oracle_best_option_id_FOR_EVALUATION_ONLY']==max(option_per_scenario[s['scenario_id']],key=lambda x:float(x['ex_post_net_return_lkr']))['option_id'] for s in S))
check('Non-negative ex-post regret',all(float(s['ex_post_regret_lkr_FOR_EVALUATION_ONLY'])>=-.01 for s in S))
check('Every recommendation marked NOT food safety approval',all(s['requires_food_safety_verification']=='YES_NOT_SAFETY_APPROVAL' for s in S))
check('Biological kinetic parameters positive',all(float(r['Arrhenius_Ea_j_per_mol_assumption'])>0 and float(r['k_ref_per_h_assumption'])>0 for r in SP))
check('All species proxy params uncalibrated',all('UNCALIBRATED' in r['source_status'] for r in SP))
check('TFT group count 25',len(GROUP)==25)
for sp_name in ['train','validation','test']:
 data=np.load(ROOT/f'C3_TFT_{sp_name}_28to7.npz')
 enc=data['encoder_x']; fut=data['future_known_x']; tar=data['target_price_lkr_kg']; d=data['forecast_start_day']
 check(f'TFT {sp_name} tensor shape',(enc.ndim==3 and enc.shape[1:]==(28,3) and fut.shape==(len(enc),7,5) and tar.shape==(len(enc),7)))
 check(f'TFT {sp_name} target-only temporal split',bool(np.all((d+7<=140) if sp_name=='train' else ((d>=140)&(d+7<=170)) if sp_name=='validation' else ((d>=170)&(d+7<=200)))))
 check(f'TFT {sp_name} finite tensors',bool(np.all(np.isfinite(enc)) and np.all(np.isfinite(tar))))
check('TFT total non-crossing windows',sum(len(np.load(ROOT/f'C3_TFT_{sp}_28to7.npz')['encoder_x']) for sp in ['train','validation','test'])==3850)
check('Price target correlates with npz labels exactly',all(eq(float(np.load(ROOT/'C3_TFT_test_28to7.npz')['target_price_lkr_kg'][0][i]),
  float(next(r['price_lkr_per_kg'] for r in M if int(r['calendar_day_index'])==170+i and r['market_id']=='M_PELIYAGODA' and r['species_id']=='SP_SKIPJACK')),.01) for i in range(7)))

report={'status':'PASS','checks_passed':len(passlog),'checks_failed':0,'external_validation':'NOT_PERFORMED','test_results':passlog}
(ROOT/'C3_QA_Report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f'ALL {len(passlog)} QA TESTS PASSED (DATA QUALITY ONLY, NOT EXTERNAL EMPIRICAL VALIDATION)')
