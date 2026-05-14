"""
EV RouteIQ — Advanced Physics Engine
Improved Crr model with speed, temperature, tire pressure, and weather corrections.
Based on: SAE J2452, ISO 28580, NRC Canada, Wallentowitz (2004), Wong (1993)
"""

# ── Base Crr Values per Road Surface Class ───────────────────
BASE_CRR = {
    'dry_asphalt_smooth':    0.0105,
    'dry_asphalt_slight':    0.0140,
    'dry_asphalt_severe':    0.0250,
    'dry_concrete_smooth':   0.0120,
    'dry_concrete_slight':   0.0140,
    'dry_concrete_severe':   0.0250,
    'dry_gravel':            0.0250,
    'dry_mud':               0.1250,
    'fresh_snow':            0.0400,
    'ice':                   0.0200,
    'melted_snow':           0.0500,
    'water_asphalt_smooth':  0.0130,
    'water_asphalt_slight':  0.0180,
    'water_asphalt_severe':  0.0300,
    'water_concrete_smooth': 0.0150,
    'water_concrete_slight': 0.0180,
    'water_concrete_severe': 0.0350,
    'water_gravel':          0.0350,
    'water_mud':             0.2000,
    'wet_asphalt_smooth':    0.0135,
    'wet_asphalt_slight':    0.0180,
    'wet_asphalt_severe':    0.0300,
    'wet_concrete_smooth':   0.0150,
    'wet_concrete_slight':   0.0180,
    'wet_concrete_severe':   0.0350,
    'wet_gravel':            0.0350,
    'wet_mud':               0.2000,
}

# ── Road Surface Descriptions ─────────────────────────────────
ROAD_INFO = {
    'dry_asphalt_smooth':    {'desc': 'New/very smooth asphalt, excellent microtexture.',      'crr_range': '0.010–0.011', 'safety': 'High',   'safety_color': '#00FF88'},
    'dry_asphalt_slight':    {'desc': 'Slightly worn asphalt, small cracks but generally good.','crr_range': '0.013–0.015', 'safety': 'High',   'safety_color': '#00FF88'},
    'dry_asphalt_severe':    {'desc': 'Severely worn asphalt, potholes and rough patches.',     'crr_range': '0.020–0.030', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'dry_concrete_smooth':   {'desc': 'Smooth concrete surface, good finish (new slab).',       'crr_range': '0.011–0.013', 'safety': 'High',   'safety_color': '#00FF88'},
    'dry_concrete_slight':   {'desc': 'Slightly worn concrete with small joints/texture.',      'crr_range': '0.013–0.015', 'safety': 'High',   'safety_color': '#00FF88'},
    'dry_concrete_severe':   {'desc': 'Rough/damaged concrete with large joints and spalling.', 'crr_range': '0.020–0.030', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'dry_gravel':            {'desc': 'Loose/compacted gravel surface.',                        'crr_range': '0.020–0.030', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'dry_mud':               {'desc': 'Dry sticky mud that deforms heavily under tyre load.',   'crr_range': '0.100–0.150', 'safety': 'Low',    'safety_color': '#FF4444'},
    'fresh_snow':            {'desc': 'Newly fallen uncompacted snow layer.',                   'crr_range': '0.030–0.050', 'safety': 'Low',    'safety_color': '#FF4444'},
    'ice':                   {'desc': 'Glazed or hard-packed ice, very low surface friction.',  'crr_range': '0.015–0.030', 'safety': 'Low',    'safety_color': '#FF4444'},
    'melted_snow':           {'desc': 'Packed/wet snow, slushy layer — high deformation.',     'crr_range': '0.040–0.060', 'safety': 'Low',    'safety_color': '#FF4444'},
    'water_asphalt_smooth':  {'desc': 'Thin water film on smooth asphalt.',                    'crr_range': '0.012–0.014', 'safety': 'High',   'safety_color': '#00FF88'},
    'water_asphalt_slight':  {'desc': 'Water pooling in shallow depressions on asphalt.',      'crr_range': '0.016–0.020', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'water_asphalt_severe':  {'desc': 'Deep standing water / hydroplaning risk on asphalt.',   'crr_range': '0.025–0.035', 'safety': 'Low',    'safety_color': '#FF4444'},
    'water_concrete_smooth': {'desc': 'Thin water cover on smooth concrete.',                  'crr_range': '0.014–0.016', 'safety': 'High',   'safety_color': '#00FF88'},
    'water_concrete_slight': {'desc': 'Small water patches on concrete surface/joints.',       'crr_range': '0.016–0.020', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'water_concrete_severe': {'desc': 'Significant standing water on concrete slabs.',         'crr_range': '0.030–0.040', 'safety': 'Low',    'safety_color': '#FF4444'},
    'water_gravel':          {'desc': 'Gravel with water filling voids — high drag.',          'crr_range': '0.030–0.040', 'safety': 'Low',    'safety_color': '#FF4444'},
    'water_mud':             {'desc': 'Very soft saturated mud — tyres sink and deform a lot.','crr_range': '0.150–0.250', 'safety': 'Low',    'safety_color': '#FF4444'},
    'wet_asphalt_smooth':    {'desc': 'Smooth asphalt with a uniform wet film.',              'crr_range': '0.012–0.015', 'safety': 'High',   'safety_color': '#00FF88'},
    'wet_asphalt_slight':    {'desc': 'Slightly wet asphalt with some texture.',               'crr_range': '0.016–0.020', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'wet_asphalt_severe':    {'desc': 'Wet + rough asphalt; combined water and roughness.',   'crr_range': '0.024–0.036', 'safety': 'Low',    'safety_color': '#FF4444'},
    'wet_concrete_smooth':   {'desc': 'Smooth concrete with thin water film.',                 'crr_range': '0.014–0.016', 'safety': 'High',   'safety_color': '#00FF88'},
    'wet_concrete_slight':   {'desc': 'Slightly wet concrete with minor texture.',             'crr_range': '0.016–0.020', 'safety': 'Medium', 'safety_color': '#FFD700'},
    'wet_concrete_severe':   {'desc': 'Rough/wet concrete with deep joints and water.',        'crr_range': '0.030–0.040', 'safety': 'Low',    'safety_color': '#FF4444'},
    'wet_gravel':            {'desc': 'Gravel that is wet — stones + water = high losses.',    'crr_range': '0.030–0.040', 'safety': 'Low',    'safety_color': '#FF4444'},
    'wet_mud':               {'desc': 'Saturated mud — deep tyre sink and viscous losses.',   'crr_range': '0.150–0.250', 'safety': 'Low',    'safety_color': '#FF4444'},
}

# ── Weather Condition Multipliers ─────────────────────────────
WEATHER_MULTIPLIERS = {
    'clear':        1.00,
    'clouds':       1.02,
    'drizzle':      1.08,
    'rain':         1.15,
    'heavy_rain':   1.25,
    'thunderstorm': 1.30,
    'snow':         1.40,
    'blizzard':     1.60,
    'mist':         1.05,
    'fog':          1.08,
    'haze':         1.03,
    'dust':         1.05,
    'sand':         1.10,
    'ice_storm':    1.50,
}

# ── Ideal reference surface ───────────────────────────────────
IDEAL_CRR    = 0.010   # New dry smooth asphalt (best case)
GRAVITY      = 9.81    # m/s²
REF_SPEED    = 60.0    # km/h reference speed for Crr
REF_TEMP     = 20.0    # °C reference temperature
REF_PRESSURE = 2.3     # bar optimal tire pressure


def calculate_adjusted_crr(
    surface_class: str,
    speed_kmh: float = 60.0,
    temperature_c: float = 20.0,
    tire_pressure_bar: float = 2.3,
    weather_condition: str = 'clear'
) -> dict:
    """
    Calculate adjusted rolling resistance coefficient using physics factors.

    Factors applied:
      1. Speed factor     (SAE J2452)        — Crr rises with speed
      2. Temperature factor (NRC Canada)     — Cold increases Crr (rubber stiffness)
      3. Tire pressure factor (ISO 28580)    — Under-inflation raises Crr
      4. Weather multiplier (Wong 1993)      — Rain/snow multiplier

    Returns dict with base_crr, adjusted_crr, and all factors.
    """
    base_crr = BASE_CRR.get(surface_class, 0.020)

    # 1. Speed factor (SAE J2452 longitudinal model)
    #    Crr increases by ~0.6% for every 10 km/h above 60 km/h
    speed_delta  = (speed_kmh - REF_SPEED) / 10.0
    speed_factor = 1.0 + max(0, speed_delta) * 0.006
    # Slight decrease at very low speeds (city) — minimal effect
    if speed_kmh < 30:
        speed_factor = 0.97

    # 2. Temperature factor (NRC Canada rubber stiffness model)
    #    Below 20°C: +1.5% per 10°C drop
    #    Above 40°C: -0.5% per 10°C rise (minor benefit)
    if temperature_c < REF_TEMP:
        temp_factor = 1.0 + 0.015 * ((REF_TEMP - temperature_c) / 10.0)
    elif temperature_c > 40:
        temp_factor = 1.0 - 0.005 * ((temperature_c - 40) / 10.0)
    else:
        temp_factor = 1.0

    # 3. Tire pressure factor (ISO 28580)
    #    For every bar below optimal: Crr rises ~10%
    if tire_pressure_bar < REF_PRESSURE:
        pressure_deficit = REF_PRESSURE - tire_pressure_bar
        pressure_factor  = 1.0 + pressure_deficit * 0.10
    elif tire_pressure_bar > REF_PRESSURE + 0.5:
        # Over-inflation gives marginal Crr improvement but hurts grip
        pressure_factor = 0.97
    else:
        pressure_factor = 1.0

    # 4. Weather multiplier (Wong 1993, automotive engineering tables)
    weather_key = weather_condition.lower().replace(' ', '_')
    weather_mul = WEATHER_MULTIPLIERS.get(weather_key, 1.0)

    # Combined adjusted Crr
    adjusted_crr = base_crr * speed_factor * temp_factor * pressure_factor * weather_mul
    adjusted_crr = round(adjusted_crr, 6)

    return {
        'surface_class'   : surface_class,
        'base_crr'        : base_crr,
        'adjusted_crr'    : adjusted_crr,
        'speed_factor'    : round(speed_factor, 4),
        'temp_factor'     : round(temp_factor, 4),
        'pressure_factor' : round(pressure_factor, 4),
        'weather_factor'  : round(weather_mul, 4),
        'speed_kmh'       : speed_kmh,
        'temperature_c'   : temperature_c,
        'tire_pressure_bar': tire_pressure_bar,
        'weather'         : weather_condition,
    }


def calculate_ev_energy(
    adjusted_crr: float,
    vehicle_mass_kg: float,
    distance_km: float = 100.0,
    speed_kmh: float = 60.0,
    regen_efficiency: float = 0.70
) -> dict:
    """
    Calculate EV energy consumption using vehicle dynamics.

    Formula: F_rr = Crr × m × g
             E_rr = F_rr × d  (in Joules → converted to kWh and MJ)

    Also computes aerodynamic drag contribution at given speed.
    """
    distance_m = distance_km * 1000.0

    # Rolling resistance force (Newtons)
    F_rr = adjusted_crr * vehicle_mass_kg * GRAVITY

    # Aerodynamic drag (simplified, Cd=0.28 avg EV, A=2.4 m²)
    Cd, A, rho = 0.28, 2.4, 1.225   # air density kg/m³
    v_ms       = speed_kmh / 3.6
    F_drag     = 0.5 * Cd * A * rho * v_ms ** 2

    # Total tractive force at constant speed
    F_total = F_rr + F_drag

    # Energy (Joules)
    E_joules_rr   = F_rr    * distance_m
    E_joules_drag = F_drag  * distance_m
    E_joules_total= F_total * distance_m

    # Convert to useful units
    E_mj_total   = E_joules_total / 1_000_000
    E_kwh_total  = E_joules_total / 3_600_000
    E_kwh_per_km = E_kwh_total / distance_km * 1000  # Wh/km

    # Ideal surface energy (smooth dry asphalt at same conditions)
    F_ideal     = IDEAL_CRR * vehicle_mass_kg * GRAVITY + F_drag
    E_ideal_kwh = (F_ideal * distance_m) / 3_600_000

    # Energy overhead vs ideal (%)
    energy_overhead_pct = ((E_kwh_total - E_ideal_kwh) / E_ideal_kwh) * 100 if E_ideal_kwh > 0 else 0

    # Fuel equivalent (petrol: 34.2 MJ/L, CO₂: 2.3 kg/L)
    fuel_litres_equiv = E_mj_total / 34.2
    co2_kg            = fuel_litres_equiv * 2.3

    # Regenerative braking (assume 30% of energy can be recovered in city)
    regen_kwh = E_kwh_total * 0.30 * regen_efficiency

    return {
        'distance_km'         : distance_km,
        'F_rolling_N'         : round(F_rr, 2),
        'F_aero_N'            : round(F_drag, 2),
        'F_total_N'           : round(F_total, 2),
        'energy_kwh'          : round(E_kwh_total, 3),
        'energy_mj'           : round(E_mj_total, 3),
        'energy_wh_per_km'    : round(E_kwh_per_km, 2),
        'energy_overhead_pct' : round(energy_overhead_pct, 1),
        'fuel_litres_equiv'   : round(fuel_litres_equiv, 3),
        'co2_kg'              : round(co2_kg, 3),
        'regen_kwh'           : round(regen_kwh, 3),
        'net_energy_kwh'      : round(E_kwh_total - regen_kwh, 3),
    }


def calculate_remaining_range(
    battery_kwh: float,
    soc_percent: float,
    energy_wh_per_km: float,
    temperature_c: float = 20.0
) -> dict:
    """
    Calculate estimated remaining driving range for an EV.

    Accounts for:
    - Current state of charge (SOC)
    - Temperature penalty on battery capacity (real-world EV behaviour)
    - Energy consumption on current road surface
    """
    # Temperature penalty on usable battery (lithium-ion characteristics)
    if temperature_c < 0:
        temp_penalty = 0.75    # 25% capacity loss in freezing conditions
    elif temperature_c < 10:
        temp_penalty = 0.85    # 15% loss in cold
    elif temperature_c < 20:
        temp_penalty = 0.93    # 7% loss in cool
    elif temperature_c < 35:
        temp_penalty = 1.00    # Optimal range
    else:
        temp_penalty = 0.97    # 3% minor loss in extreme heat

    usable_kwh   = battery_kwh * (soc_percent / 100.0) * temp_penalty
    range_km     = (usable_kwh * 1000.0) / energy_wh_per_km if energy_wh_per_km > 0 else 0

    # Time estimates at 60 km/h
    drive_hours  = range_km / 60.0

    return {
        'battery_kwh'        : battery_kwh,
        'soc_percent'        : soc_percent,
        'usable_kwh'         : round(usable_kwh, 2),
        'temp_penalty_pct'   : round((1 - temp_penalty) * 100, 1),
        'estimated_range_km' : round(range_km, 1),
        'drive_hours'        : round(drive_hours, 2),
        'energy_wh_per_km'   : round(energy_wh_per_km, 1),
        'temperature_c'      : temperature_c,
    }


def calculate_road_quality_score(surface_class: str) -> int:
    """
    Returns a road quality score 0–100.
    100 = perfect (dry smooth asphalt), 0 = worst (wet/water mud).
    """
    crr = BASE_CRR.get(surface_class, 0.020)
    crr_min, crr_max = 0.010, 0.200
    score = int(100 * (1 - (crr - crr_min) / (crr_max - crr_min)))
    return max(0, min(100, score))


def get_road_surface_info(surface_class: str) -> dict:
    """Returns full road surface info dict."""
    info   = ROAD_INFO.get(surface_class, {})
    base_crr = BASE_CRR.get(surface_class, 0.020)
    score  = calculate_road_quality_score(surface_class)

    # Energy available / reduced (relative to ideal dry_asphalt_smooth)
    energy_available = round(min(100, (IDEAL_CRR / base_crr) * 100), 2)
    energy_reduced   = round(100 - energy_available, 2)

    return {
        'surface_class'   : surface_class,
        'description'     : info.get('desc', 'No description available'),
        'crr_range'       : info.get('crr_range', 'N/A'),
        'mean_crr'        : base_crr,
        'safety'          : info.get('safety', 'Medium'),
        'safety_color'    : info.get('safety_color', '#FFD700'),
        'quality_score'   : score,
        'energy_available': energy_available,
        'energy_reduced'  : energy_reduced,
    }


def get_recommended_speed(surface_class: str) -> int:
    """Returns recommended max speed (km/h) based on surface condition."""
    speed_map = {
        'dry_asphalt_smooth':    120,
        'dry_asphalt_slight':    100,
        'dry_asphalt_severe':     60,
        'dry_concrete_smooth':   110,
        'dry_concrete_slight':    90,
        'dry_concrete_severe':    60,
        'dry_gravel':             50,
        'dry_mud':                30,
        'fresh_snow':             40,
        'ice':                    20,
        'melted_snow':            30,
        'water_asphalt_smooth':   90,
        'water_asphalt_slight':   70,
        'water_asphalt_severe':   40,
        'water_concrete_smooth':  80,
        'water_concrete_slight':  70,
        'water_concrete_severe':  40,
        'water_gravel':           40,
        'water_mud':              20,
        'wet_asphalt_smooth':    100,
        'wet_asphalt_slight':     80,
        'wet_asphalt_severe':     50,
        'wet_concrete_smooth':    90,
        'wet_concrete_slight':    80,
        'wet_concrete_severe':    50,
        'wet_gravel':             45,
        'wet_mud':                20,
    }
    return speed_map.get(surface_class, 60)


def compare_routes(route_a_surfaces: list, route_b_surfaces: list,
                   vehicle_mass_kg: float, battery_kwh: float,
                   soc_percent: float = 100.0,
                   speed_kmh: float = 60.0,
                   temperature_c: float = 20.0,
                   tire_pressure_bar: float = 2.3,
                   weather_condition: str = 'clear') -> dict:
    """
    Compare energy cost of two routes given their surface classifications.

    Each route is a list of (surface_class, distance_km) tuples.
    Returns winner, energy savings, and detailed breakdowns.
    """
    def calc_route(surfaces):
        total_energy  = 0.0
        total_dist    = 0.0
        segment_data  = []
        for surface, dist_km in surfaces:
            crr_info   = calculate_adjusted_crr(
                surface, speed_kmh, temperature_c,
                tire_pressure_bar, weather_condition)
            energy_info = calculate_ev_energy(
                crr_info['adjusted_crr'], vehicle_mass_kg, dist_km, speed_kmh)
            total_energy += energy_info['energy_kwh']
            total_dist   += dist_km
            segment_data.append({
                'surface': surface, 'distance_km': dist_km,
                'energy_kwh': energy_info['energy_kwh'],
                'crr': crr_info['adjusted_crr'],
                'quality_score': calculate_road_quality_score(surface)
            })
        range_info = calculate_remaining_range(
            battery_kwh, soc_percent - (total_energy / battery_kwh * 100),
            total_energy / total_dist * 1000 if total_dist > 0 else 150,
            temperature_c)
        return {'total_energy_kwh': round(total_energy, 3),
                'total_distance_km': round(total_dist, 2),
                'segments': segment_data,
                'remaining_range_km': range_info['estimated_range_km'],
                'avg_crr': round(sum(s['crr'] for s in segment_data) / len(segment_data), 6)}

    result_a = calc_route(route_a_surfaces)
    result_b = calc_route(route_b_surfaces)

    energy_saved = abs(result_a['total_energy_kwh'] - result_b['total_energy_kwh'])
    winner = 'A' if result_a['total_energy_kwh'] <= result_b['total_energy_kwh'] else 'B'

    return {
        'route_a': result_a,
        'route_b': result_b,
        'winner': winner,
        'energy_saved_kwh': round(energy_saved, 3),
        'energy_saved_pct': round(energy_saved / max(result_a['total_energy_kwh'],
                                                       result_b['total_energy_kwh']) * 100, 1),
    }
