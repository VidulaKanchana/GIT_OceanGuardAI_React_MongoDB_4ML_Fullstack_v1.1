import numpy as np
from typing import List, Dict, Any

def non_dominated_sorting(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Computes Pareto frontier and Pareto ranks using non-dominated sorting.
    Objectives:
    - Maximize: HSI (higher is better)
    - Minimize: Distance km (lower is better)
    - Minimize: Fuel Liters (lower is better)
    """
    N = len(candidates)
    if N == 0:
        return []

    # S[p]: list of candidates that candidate p dominates
    # n[p]: count of candidates that dominate candidate p
    S = [[] for _ in range(N)]
    n = [0 for _ in range(N)]
    ranks = [0 for _ in range(N)]
    fronts = [[]]

    for p in range(N):
        p_hsi = candidates[p]['habitat_suitability_index']
        p_dist = candidates[p]['distance_km']
        p_fuel = candidates[p]['estimated_fuel_l']

        for q in range(N):
            if p == q:
                continue
            q_hsi = candidates[q]['habitat_suitability_index']
            q_dist = candidates[q]['distance_km']
            q_fuel = candidates[q]['estimated_fuel_l']

            # p dominates q if p is >= in all objectives and strictly > in at least one
            # Note: for distance and fuel, <= is better
            dominates = (
                (p_hsi >= q_hsi and p_dist <= q_dist and p_fuel <= q_fuel) and
                (p_hsi > q_hsi or p_dist < q_dist or p_fuel < q_fuel)
            )
            is_dominated = (
                (q_hsi >= p_hsi and q_dist <= p_dist and q_fuel <= p_fuel) and
                (q_hsi > p_hsi or q_dist < p_dist or q_fuel < p_fuel)
            )

            if dominates:
                S[p].append(q)
            elif is_dominated:
                n[p] += 1

        if n[p] == 0:
            ranks[p] = 1
            fronts[0].append(p)

    # Compute subsequent fronts
    curr_front_idx = 0
    while len(fronts[curr_front_idx]) > 0:
        next_front = []
        for p in fronts[curr_front_idx]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    ranks[q] = curr_front_idx + 2
                    next_front.append(q)
        curr_front_idx += 1
        fronts.append(next_front)

    for i in range(N):
        candidates[i]['pareto_rank'] = ranks[i] if ranks[i] > 0 else len(fronts)

    # Sort primarily by Pareto rank (1 is best), secondarily by HSI descending
    candidates.sort(key=lambda x: (x['pareto_rank'], -x['habitat_suitability_index']))
    return candidates
