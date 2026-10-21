from typing import Dict, Any, List
from app.ml.component_3_market.perishability import calculate_quality_retention, estimate_ice_storage_cost

# Distance matrix in kilometers between major fish markets & landing ports in Sri Lanka
MARKET_DISTANCES_KM = {
    ("P_GALLE", "M_GALLE"): 2.0,
    ("P_GALLE", "M_PELIYAGODA"): 122.0,
    ("P_GALLE", "M_NEGOMBO"): 155.0,
    ("P_GALLE", "M_MIRISSA"): 35.0,
    ("P_GALLE", "M_TANGALLE"): 82.0,

    ("P_MIRISSA", "M_MIRISSA"): 1.5,
    ("P_MIRISSA", "M_GALLE"): 35.0,
    ("P_MIRISSA", "M_PELIYAGODA"): 152.0,
    ("P_MIRISSA", "M_NEGOMBO"): 185.0,
    ("P_MIRISSA", "M_TANGALLE"): 48.0,

    ("P_TANGALLE", "M_TANGALLE"): 1.0,
    ("P_TANGALLE", "M_MIRISSA"): 48.0,
    ("P_TANGALLE", "M_GALLE"): 82.0,
    ("P_TANGALLE", "M_PELIYAGODA"): 198.0,
    ("P_TANGALLE", "M_NEGOMBO"): 230.0,

    ("P_NEGOMBO", "M_NEGOMBO"): 2.0,
    ("P_NEGOMBO", "M_PELIYAGODA"): 34.0,
    ("P_NEGOMBO", "M_GALLE"): 155.0,
    ("P_NEGOMBO", "M_MIRISSA"): 185.0,
    ("P_NEGOMBO", "M_TANGALLE"): 230.0,
    
    ("P_PELIYAGODA", "M_PELIYAGODA"): 0.5,
    ("P_PELIYAGODA", "M_NEGOMBO"): 34.0,
    ("P_PELIYAGODA", "M_GALLE"): 122.0,
    ("P_PELIYAGODA", "M_MIRISSA"): 152.0,
    ("P_PELIYAGODA", "M_TANGALLE"): 198.0
}

MARKET_PORT_MAP = {
    "M_PELIYAGODA": "Peliyagoda Central Fish Market",
    "M_NEGOMBO": "Negombo Market",
    "M_GALLE": "Galle Harbour Market",
    "M_MIRISSA": "Mirissa Market",
    "M_TANGALLE": "Tangalle Market"
}

def get_intermarket_distance(port_id: str, market_id: str) -> float:
    return MARKET_DISTANCES_KM.get((port_id, market_id), 120.0)

def evaluate_market_decisions(
    species_id: str,
    catch_kg: float,
    current_port_id: str,
    storage_temp_c: float,
    hours_stored: float,
    market_price_quotes: Dict[str, float]
) -> Dict[str, Any]:
    """
    Evaluates economic alternatives:
    1. SELL NOW at current landing port
    2. WAIT (cold storage holding for 24h)
    3. TRANSPORT to alternative markets (freight costs + transit quality loss)
    
    Expected Net Return = Expected Sales Revenue - Transport Cost - Ice/Storage Cost
    """
    options = []
    current_quality = calculate_quality_retention(species_id, storage_temp_c, hours_stored)

    # Base truck freight cost in Sri Lanka: ~65 LKR per km (refrigerated small lorry / pickup)
    transport_rate_per_km = 65.0

    for m_id, m_name in MARKET_PORT_MAP.items():
        price_per_kg = market_price_quotes.get(m_id, 950.0)
        dist_km = get_intermarket_distance(current_port_id, m_id)

        # Case A: Local port market -> SELL NOW
        if dist_km <= 5.0:
            quality_ratio = current_quality
            revenue = catch_kg * price_per_kg * quality_ratio
            transport_cost = 500.0 # Nominal harbour handling
            storage_cost = 0.0
            net_return = revenue - transport_cost - storage_cost

            options.append({
                "market_id": m_id,
                "market_name": m_name,
                "port_id": current_port_id,
                "forecasted_price_lkr_kg": round(price_per_kg, 2),
                "estimated_quality_ratio": round(quality_ratio, 3),
                "expected_revenue_lkr": round(revenue, 2),
                "transport_cost_lkr": round(transport_cost, 2),
                "ice_storage_cost_lkr": round(storage_cost, 2),
                "expected_net_return_lkr": round(net_return, 2),
                "transport_distance_km": round(dist_km, 1),
                "decision_type": "SELL_NOW"
            })

            # Case B: WAIT (holding locally for 24h)
            wait_hours = hours_stored + 24.0
            wait_quality = calculate_quality_retention(species_id, 2.0, wait_hours) # stored in ice at 2C
            # Forecast assumption for next day: +5% price premium or seasonal variation
            wait_price = price_per_kg * 1.05
            wait_rev = catch_kg * wait_price * wait_quality
            ice_cost = estimate_ice_storage_cost(catch_kg, 24.0, target_temp_c=2.0)
            wait_net = wait_rev - 500.0 - ice_cost

            options.append({
                "market_id": f"{m_id}_WAIT_24H",
                "market_name": f"{m_name} (Hold 24h with Ice)",
                "port_id": current_port_id,
                "forecasted_price_lkr_kg": round(wait_price, 2),
                "estimated_quality_ratio": round(wait_quality, 3),
                "expected_revenue_lkr": round(wait_rev, 2),
                "transport_cost_lkr": 500.0,
                "ice_storage_cost_lkr": round(ice_cost, 2),
                "expected_net_return_lkr": round(wait_net, 2),
                "transport_distance_km": round(dist_km, 1),
                "decision_type": "WAIT"
            })

        # Case C: TRANSPORT to other market
        else:
            transit_hours = dist_km / 50.0 # 50 km/h truck speed
            dest_hours = hours_stored + transit_hours
            dest_quality = calculate_quality_retention(species_id, 2.0, dest_hours)
            revenue = catch_kg * price_per_kg * dest_quality
            transport_cost = dist_km * transport_rate_per_km
            ice_cost = estimate_ice_storage_cost(catch_kg, transit_hours, target_temp_c=2.0)
            net_return = revenue - transport_cost - ice_cost

            options.append({
                "market_id": m_id,
                "market_name": m_name,
                "port_id": current_port_id,
                "forecasted_price_lkr_kg": round(price_per_kg, 2),
                "estimated_quality_ratio": round(dest_quality, 3),
                "expected_revenue_lkr": round(revenue, 2),
                "transport_cost_lkr": round(transport_cost, 2),
                "ice_storage_cost_lkr": round(ice_cost, 2),
                "expected_net_return_lkr": round(net_return, 2),
                "transport_distance_km": round(dist_km, 1),
                "decision_type": "TRANSPORT"
            })

    # Find optimal recommendation based on highest expected net return
    best_opt = max(options, key=lambda x: x["expected_net_return_lkr"])
    recommended_decision = f"{best_opt['decision_type']}: {best_opt['market_name']} (Expected Net: LKR {best_opt['expected_net_return_lkr']:,.2f})"

    return {
        "species_id": species_id,
        "initial_catch_kg": catch_kg,
        "storage_temp_c": storage_temp_c,
        "hours_since_catch": hours_stored,
        "quality_retention_percent": round(current_quality * 100.0, 1),
        "recommended_decision": recommended_decision,
        "market_evaluations": options,
        "model_version": "C3-TFT-Perishability-v1.0",
        "scientific_disclaimer": "SIMULATION FORECAST ONLY. DOES NOT CERTIFY FOOD SAFETY."
    }
