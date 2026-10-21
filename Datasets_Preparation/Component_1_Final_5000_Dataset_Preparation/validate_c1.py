"""Re-run independent post-generation invariants for C1 artifacts."""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent
m=pd.read_csv(P/'C1_Master_5000_Trips.csv')
w=pd.read_csv(P/'C1_BiLSTM_Weather_60000_Steps.csv')
v=pd.read_csv(P/'C1_Vessel_Registry_250.csv')
checks={}
def check(name, condition):
    checks[name]=bool(condition)
    if not checks[name]: raise AssertionError(f'FAIL {name}')
check('master_exact_5000',len(m)==5000)
check('weather_exact_60000',len(w)==60000)
check('registry_250',len(v)==250)
check('trip_pk_unique',m.trip_id.is_unique)
check('composite_weather_pk_unique',not w.duplicated(['trip_id','step_index']).any())
check('each_trip_has_12_steps',w.groupby('trip_id').step_index.nunique().eq(12).all())
check('join_complete',set(m.trip_id)==set(w.trip_id))
check('foreign_key_registry_valid',set(m.vessel_id).issubset(set(v.vessel_id)))
check('missing_cells_zero',int(m.isnull().sum().sum()+w.isnull().sum().sum()+v.isnull().sum().sum())==0)
check('all_dri_bounds',m.heuristic_dri_score.between(0,100).all())
check('label_consistency',((m.heuristic_dri_score<35)&(m.proxy_risk_label=='Safe')|
    m.heuristic_dri_score.between(35,65,inclusive='left')&(m.proxy_risk_label=='Caution')|
    (m.heuristic_dri_score>=65)&(m.proxy_risk_label=='Danger')).all())
check('wind_gust_above_mean',w.wind_gust_proxy_ms.ge(w.wind_speed_10m_ms).all())
check('wave_steepness_constraint',w.wave_steepness.le(.082).all())
check('positive_physics',m.estimated_loaded_freeboard_m.gt(0).all() and m.estimated_loaded_draft_m.gt(0).all())
check('wave_length_equation',np.allclose(w.wave_length_deep_m,9.80665*w.wave_peak_period_s**2/(2*np.pi),atol=.02))
vv=v.set_index('vessel_id')
calculated=m.payload_mass_kg/(1025*m.vessel_length_m*m.vessel_beam_m*m.vessel_id.map(vv.waterplane_coefficient_cwp))
check('buoyancy_immersion_equation',np.allclose(calculated,m.estimated_extra_draft_m,atol=.002))
check('freeboard_equation',np.allclose(m.assumed_lightship_freeboard_m-m.estimated_extra_draft_m,m.estimated_loaded_freeboard_m,atol=.004))
check('splits_3500_750_750',m.dataset_split.value_counts().to_dict()=={'train':3500,'validation':750,'test':750})
check('dates_train_pre_2025',(pd.to_datetime(m.loc[m.dataset_split=='train','decision_timestamp_local'])<pd.Timestamp('2025-01-01')).all())
check('dates_val_2025_h1',pd.to_datetime(m.loc[m.dataset_split=='validation','decision_timestamp_local']).between('2025-01-01','2025-06-30 23:59:59').all())
check('dates_test_2025_h2',(pd.to_datetime(m.loc[m.dataset_split=='test','decision_timestamp_local'])>=pd.Timestamp('2025-07-01')).all())
check('sensitivity_quantile_order',(m.sensitivity_p05_dri_score<=m.sensitivity_p95_dri_score).all())
check('all_synthetic_provenance',(m.weather_provenance=='synthetic_forecast_not_observed').all())
check('time_step_index_0_to_11',(w.groupby('trip_id').step_index.agg(['min','max']).eq([0,11]).all(axis=1)).all())
res={'result':'PASS' if all(checks.values()) else 'FAIL','tests':checks,'count_pass':sum(checks.values()),'total_tests':len(checks),
     'limitations':['Checks prove internal consistency only; do not establish empirical validity','All labels are heuristics, not accident outcomes']}
(P/'C1_Independent_QA.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps(res,indent=2))
