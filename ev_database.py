"""
EV RouteIQ — EV Vehicle Database
20 popular electric vehicles with real-world specifications.
"""

EV_DATABASE = {
    "tesla_model3_sr": {
        "id": "tesla_model3_sr",
        "name": "Tesla Model 3 Standard Range",
        "brand": "Tesla", "model": "Model 3",
        "battery_kwh": 57.5, "range_km": 438, "mass_kg": 1752,
        "efficiency_wh_km": 131, "regen": True, "regen_efficiency": 0.75,
        "icon": "🚗", "color": "#E31937"
    },
    "tesla_model3_lr": {
        "id": "tesla_model3_lr",
        "name": "Tesla Model 3 Long Range",
        "brand": "Tesla", "model": "Model 3 LR",
        "battery_kwh": 82.0, "range_km": 629, "mass_kg": 1847,
        "efficiency_wh_km": 130, "regen": True, "regen_efficiency": 0.75,
        "icon": "🚗", "color": "#E31937"
    },
    "tesla_modely": {
        "id": "tesla_modely",
        "name": "Tesla Model Y Long Range",
        "brand": "Tesla", "model": "Model Y",
        "battery_kwh": 82.0, "range_km": 533, "mass_kg": 2003,
        "efficiency_wh_km": 154, "regen": True, "regen_efficiency": 0.75,
        "icon": "🚙", "color": "#E31937"
    },
    "nissan_leaf_40": {
        "id": "nissan_leaf_40",
        "name": "Nissan Leaf 40 kWh",
        "brand": "Nissan", "model": "Leaf",
        "battery_kwh": 40.0, "range_km": 270, "mass_kg": 1579,
        "efficiency_wh_km": 148, "regen": True, "regen_efficiency": 0.65,
        "icon": "🚗", "color": "#003087"
    },
    "nissan_leaf_plus": {
        "id": "nissan_leaf_plus",
        "name": "Nissan Leaf Plus 62 kWh",
        "brand": "Nissan", "model": "Leaf Plus",
        "battery_kwh": 62.0, "range_km": 385, "mass_kg": 1717,
        "efficiency_wh_km": 161, "regen": True, "regen_efficiency": 0.65,
        "icon": "🚗", "color": "#003087"
    },
    "tata_nexon_ev": {
        "id": "tata_nexon_ev",
        "name": "Tata Nexon EV Max",
        "brand": "Tata", "model": "Nexon EV",
        "battery_kwh": 40.5, "range_km": 437, "mass_kg": 1615,
        "efficiency_wh_km": 131, "regen": True, "regen_efficiency": 0.60,
        "icon": "🚙", "color": "#1C3F94"
    },
    "tata_tiago_ev": {
        "id": "tata_tiago_ev",
        "name": "Tata Tiago EV",
        "brand": "Tata", "model": "Tiago EV",
        "battery_kwh": 24.0, "range_km": 315, "mass_kg": 1215,
        "efficiency_wh_km": 114, "regen": True, "regen_efficiency": 0.60,
        "icon": "🚗", "color": "#1C3F94"
    },
    "mg_zs_ev": {
        "id": "mg_zs_ev",
        "name": "MG ZS EV Excite",
        "brand": "MG", "model": "ZS EV",
        "battery_kwh": 50.3, "range_km": 461, "mass_kg": 1620,
        "efficiency_wh_km": 147, "regen": True, "regen_efficiency": 0.65,
        "icon": "🚙", "color": "#A50034"
    },
    "hyundai_ioniq5": {
        "id": "hyundai_ioniq5",
        "name": "Hyundai IONIQ 5 Long Range",
        "brand": "Hyundai", "model": "IONIQ 5",
        "battery_kwh": 77.4, "range_km": 507, "mass_kg": 2100,
        "efficiency_wh_km": 153, "regen": True, "regen_efficiency": 0.72,
        "icon": "🚙", "color": "#002C5F"
    },
    "hyundai_kona": {
        "id": "hyundai_kona",
        "name": "Hyundai Kona Electric",
        "brand": "Hyundai", "model": "Kona Electric",
        "battery_kwh": 64.0, "range_km": 484, "mass_kg": 1685,
        "efficiency_wh_km": 132, "regen": True, "regen_efficiency": 0.70,
        "icon": "🚙", "color": "#002C5F"
    },
    "kia_ev6": {
        "id": "kia_ev6",
        "name": "Kia EV6 Long Range",
        "brand": "Kia", "model": "EV6",
        "battery_kwh": 77.4, "range_km": 528, "mass_kg": 2055,
        "efficiency_wh_km": 147, "regen": True, "regen_efficiency": 0.72,
        "icon": "🚙", "color": "#05141F"
    },
    "bmw_i4": {
        "id": "bmw_i4",
        "name": "BMW i4 eDrive40",
        "brand": "BMW", "model": "i4",
        "battery_kwh": 83.9, "range_km": 590, "mass_kg": 2050,
        "efficiency_wh_km": 142, "regen": True, "regen_efficiency": 0.73,
        "icon": "🚗", "color": "#1C69D4"
    },
    "vw_id4": {
        "id": "vw_id4",
        "name": "Volkswagen ID.4 Pro",
        "brand": "Volkswagen", "model": "ID.4",
        "battery_kwh": 77.0, "range_km": 520, "mass_kg": 2124,
        "efficiency_wh_km": 148, "regen": True, "regen_efficiency": 0.70,
        "icon": "🚙", "color": "#00B1EB"
    },
    "chevy_bolt": {
        "id": "chevy_bolt",
        "name": "Chevrolet Bolt EV",
        "brand": "Chevrolet", "model": "Bolt EV",
        "battery_kwh": 65.0, "range_km": 417, "mass_kg": 1625,
        "efficiency_wh_km": 156, "regen": True, "regen_efficiency": 0.68,
        "icon": "🚗", "color": "#C8102E"
    },
    "audi_etron": {
        "id": "audi_etron",
        "name": "Audi e-tron 55 quattro",
        "brand": "Audi", "model": "e-tron",
        "battery_kwh": 95.0, "range_km": 441, "mass_kg": 2490,
        "efficiency_wh_km": 215, "regen": True, "regen_efficiency": 0.70,
        "icon": "🚙", "color": "#BB0A21"
    },
    "byd_atto3": {
        "id": "byd_atto3",
        "name": "BYD Atto 3",
        "brand": "BYD", "model": "Atto 3",
        "battery_kwh": 60.5, "range_km": 480, "mass_kg": 1750,
        "efficiency_wh_km": 151, "regen": True, "regen_efficiency": 0.65,
        "icon": "🚙", "color": "#1DB954"
    },
    "rivian_r1t": {
        "id": "rivian_r1t",
        "name": "Rivian R1T Adventure",
        "brand": "Rivian", "model": "R1T",
        "battery_kwh": 135.0, "range_km": 505, "mass_kg": 2930,
        "efficiency_wh_km": 267, "regen": True, "regen_efficiency": 0.70,
        "icon": "🛻", "color": "#00A651"
    },
    "mg_comet": {
        "id": "mg_comet",
        "name": "MG Comet EV",
        "brand": "MG", "model": "Comet EV",
        "battery_kwh": 17.3, "range_km": 230, "mass_kg": 900,
        "efficiency_wh_km": 99, "regen": True, "regen_efficiency": 0.60,
        "icon": "🚗", "color": "#A50034"
    },
    "tata_punch_ev": {
        "id": "tata_punch_ev",
        "name": "Tata Punch EV Long Range",
        "brand": "Tata", "model": "Punch EV",
        "battery_kwh": 35.0, "range_km": 421, "mass_kg": 1398,
        "efficiency_wh_km": 124, "regen": True, "regen_efficiency": 0.62,
        "icon": "🚙", "color": "#1C3F94"
    },
    "custom": {
        "id": "custom",
        "name": "Custom Vehicle",
        "brand": "Custom", "model": "User Defined",
        "battery_kwh": 60.0, "range_km": 400, "mass_kg": 1800,
        "efficiency_wh_km": 150, "regen": True, "regen_efficiency": 0.65,
        "icon": "🚘", "color": "#888888"
    }
}


def get_vehicle(vehicle_id: str) -> dict:
    """Return EV specs by ID. Falls back to custom if not found."""
    return EV_DATABASE.get(vehicle_id, EV_DATABASE["custom"])


def list_vehicles() -> list:
    """Return sorted list of all vehicles for frontend dropdown."""
    return sorted(
        [{"id": k, "name": v["name"], "brand": v["brand"],
          "battery_kwh": v["battery_kwh"], "range_km": v["range_km"],
          "mass_kg": v["mass_kg"], "icon": v["icon"], "color": v["color"]}
         for k, v in EV_DATABASE.items()],
        key=lambda x: (x["brand"], x["name"])
    )


def get_brands() -> list:
    """Return unique sorted list of brands."""
    return sorted(set(v["brand"] for v in EV_DATABASE.values()))
