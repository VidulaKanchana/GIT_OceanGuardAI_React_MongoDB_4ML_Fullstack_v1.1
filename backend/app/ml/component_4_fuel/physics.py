import numpy as np
from typing import Dict, Any

# Seawater and air physical constants
RHO_SEAWATER = 1025.0 # kg/m^3
RHO_AIR = 1.225 # kg/m^3
KINEMATIC_VISCOSITY_SEAWATER = 1.188e-6 # m^2/s at 27 deg C
GRAVITY = 9.80665 # m/s^2

def calculate_hydrodynamic_resistance(
    vessel_length_m: float,
    vessel_beam_m: float,
    displacement_mass_kg: float,
    speed_knots: float,
    wave_hs_m: float = 1.0,
    wind_speed_ms: float = 8.0,
    propulsive_efficiency: float = 0.55,
    bsfc_kg_kwh: float = 0.25,
    maintenance_factor: float = 1.05
) -> Dict[str, float]:
    """
    Computes vessel resistance, power, and fuel rate using ITTC-1957 friction formulation
    and naval architectural principles.
    """
    # Convert speed from knots to m/s (1 knot = 0.514444 m/s)
    speed_ms = max(0.5, speed_knots * 0.514444)
    displacement_volume_m3 = displacement_mass_kg / RHO_SEAWATER

    # 1. Non-dimensional Flow Numbers
    reynolds_number = (speed_ms * vessel_length_m) / KINEMATIC_VISCOSITY_SEAWATER
    froude_number = speed_ms / np.sqrt(GRAVITY * vessel_length_m)

    # 2. ITTC-1957 Frictional Resistance Coefficient
    cf = 0.075 / np.square(np.log10(max(reynolds_number, 1e4)) - 2.0)

    # 3. Wetted Surface Area Estimation (Denny-Mumford approximation)
    wetted_surface_m2 = 1.7 * vessel_length_m * (displacement_volume_m3 / (vessel_length_m * vessel_beam_m + 1e-6)) + (displacement_volume_m3 / (vessel_length_m + 1e-6))
    wetted_surface_m2 = max(4.0, wetted_surface_m2)

    # Frictional Resistance: Rf = 0.5 * rho * V^2 * S * Cf
    rf_n = 0.5 * RHO_SEAWATER * np.square(speed_ms) * wetted_surface_m2 * cf

    # 4. Residuary Resistance Heuristic (scales steeply with Froude number)
    cr = 0.0015 * np.power(max(0.1, froude_number), 2.8)
    rr_n = 0.5 * RHO_SEAWATER * np.square(speed_ms) * wetted_surface_m2 * cr

    # 5. Added Wave Resistance Heuristic (Gerritsma & Beukelman proxy)
    r_wave_n = 0.5 * RHO_SEAWATER * GRAVITY * np.square(wave_hs_m) * vessel_beam_m * 0.12

    # 6. Aerodynamic Wind Drag
    frontal_area_m2 = vessel_beam_m * 1.5 # Approximate superstructure cross-section
    cd_air = 0.75
    r_air_n = 0.5 * RHO_AIR * np.square(wind_speed_ms) * frontal_area_m2 * cd_air

    # Total Resistance
    total_resistance_n = rf_n + rr_n + r_wave_n + r_air_n

    # 7. Effective Power Pe = Rt * V (Watts -> kW)
    effective_power_kw = (total_resistance_n * speed_ms) / 1000.0

    # 8. Brake Power Pb = Pe / eta
    brake_power_kw = effective_power_kw / max(0.2, propulsive_efficiency)

    # 9. Fuel Consumption Rate (Liters per hour)
    # Marine diesel density ~ 0.85 kg/L
    fuel_rate_kg_h = brake_power_kw * bsfc_kg_kwh * maintenance_factor
    fuel_rate_l_h = fuel_rate_kg_h / 0.85

    return {
        "reynolds_number": float(reynolds_number),
        "froude_number": float(froude_number),
        "cf_friction_coeff": float(cf),
        "wetted_surface_m2": float(wetted_surface_m2),
        "frictional_resistance_n": float(rf_n),
        "residuary_resistance_n": float(rr_n),
        "wave_resistance_n": float(r_wave_n),
        "air_drag_n": float(r_air_n),
        "total_resistance_n": float(total_resistance_n),
        "effective_power_kw": float(effective_power_kw),
        "brake_power_kw": float(brake_power_kw),
        "fuel_rate_l_h": float(fuel_rate_l_h)
    }
