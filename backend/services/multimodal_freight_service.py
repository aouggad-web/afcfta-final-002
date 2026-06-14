"""
Multimodal Freight Comparator
==============================
Compares freight cost / transit-days / CO2 across 4 route options:
  1. Sea direct (port to port)
  2. Air direct (airport to airport)
  3. Land direct (corridor only - for connected coastal/border countries)
  4. Sea + Land combo (gateway port -> corridor -> landlocked destination)

CO2 emission factors (g CO2-eq per ton-km, well-to-wheel):
  - Sea (container vessel): 10
  - Rail freight: 22
  - Road freight (HGV): 62
  - Air freight (long-haul cargo): 602
  Source: IPCC AR6, IEA Transport 2023, GLEC Framework v3
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from logistics_fees_data import (
    PORT_THC,
    get_total_cost as sea_get_total_cost,
    SHIPPING_ROUTES,
)
from logistics_air_fees_data import (
    _airport_registry as air_registry,
    get_air_freight_cost,
)
from logistics_land_fees_data import (
    get_land_corridors_list,
    get_land_freight_cost,
)

logger = logging.getLogger(__name__)

# CO2 emission factors (g CO2-eq per ton-km)
CO2_FACTORS_G_PER_TKM = {
    "sea": 10,
    "rail": 22,
    "road": 62,
    "air": 602,
    "multimodal": 36,  # weighted avg sea+rail+road
}

# Conversions
NM_TO_KM = 1.852
TEU_CAPACITY_KG = 21_600  # max payload of a 20' container
FEU_CAPACITY_KG = 26_400  # max payload of a 40' container

# Landlocked African countries (ISO3) - need port + corridor combo
LANDLOCKED_AFRICA = {
    "BFA",  # Burkina Faso
    "BDI",  # Burundi
    "CAF",  # Central African Rep.
    "TCD",  # Chad
    "ETH",  # Ethiopia
    "LSO",  # Lesotho
    "MWI",  # Malawi
    "MLI",  # Mali
    "NER",  # Niger
    "RWA",  # Rwanda
    "SSD",  # South Sudan
    "SWZ",  # Eswatini
    "UGA",  # Uganda
    "ZMB",  # Zambia
    "ZWE",  # Zimbabwe
    "BWA",  # Botswana
}

# Country ISO3 → list of (port LOCODE, port country, corridor preference) entries.
# These are the canonical gateway ports for landlocked countries.
LANDLOCKED_GATEWAYS: Dict[str, List[Dict[str, str]]] = {
    "MLI": [
        {"port": "SNDKR", "port_country": "SEN", "via": "Bamako-Dakar"},
        {"port": "CIABJ", "port_country": "CIV", "via": "Bamako-Abidjan"},
    ],
    "BFA": [
        {"port": "CIABJ", "port_country": "CIV", "via": "Ouagadougou-Abidjan"},
        {"port": "GHTEM", "port_country": "GHA", "via": "Ouagadougou-Tema"},
    ],
    "NER": [
        {"port": "NGAPP", "port_country": "NGA", "via": "Niamey-Lagos"},
        {"port": "GHTEM", "port_country": "GHA", "via": "Niamey-Tema"},
    ],
    "TCD": [
        {"port": "CMDLA", "port_country": "CMR", "via": "N'Djamena-Douala"},
    ],
    "CAF": [
        {"port": "CMDLA", "port_country": "CMR", "via": "Bangui-Douala"},
    ],
    "UGA": [
        {"port": "KEMBA", "port_country": "KEN", "via": "Kampala-Mombasa (Northern Corridor)"},
    ],
    "RWA": [
        {"port": "KEMBA", "port_country": "KEN", "via": "Kigali-Mombasa (Northern Corridor)"},
        {"port": "TZDAR", "port_country": "TZA", "via": "Kigali-Dar es Salaam (Central Corridor)"},
    ],
    "BDI": [
        {"port": "TZDAR", "port_country": "TZA", "via": "Bujumbura-Dar es Salaam"},
    ],
    "SSD": [
        {"port": "KEMBA", "port_country": "KEN", "via": "Juba-Mombasa"},
    ],
    "ETH": [
        {"port": "DJJIB", "port_country": "DJI", "via": "Addis Ababa-Djibouti"},
    ],
    "ZMB": [
        {"port": "TZDAR", "port_country": "TZA", "via": "Lusaka-Dar es Salaam (TAZARA)"},
        {"port": "ZADUR", "port_country": "ZAF", "via": "Lusaka-Durban (North-South)"},
    ],
    "ZWE": [
        {"port": "ZADUR", "port_country": "ZAF", "via": "Harare-Durban (North-South)"},
        {"port": "MZMPM", "port_country": "MOZ", "via": "Harare-Maputo (Beira Corridor)"},
    ],
    "MWI": [
        {"port": "MZMPM", "port_country": "MOZ", "via": "Lilongwe-Beira (Beira Corridor)"},
        {"port": "TZDAR", "port_country": "TZA", "via": "Lilongwe-Dar es Salaam"},
    ],
    "BWA": [
        {"port": "ZADUR", "port_country": "ZAF", "via": "Gaborone-Durban"},
    ],
    "LSO": [
        {"port": "ZADUR", "port_country": "ZAF", "via": "Maseru-Durban"},
    ],
    "SWZ": [
        {"port": "ZADUR", "port_country": "ZAF", "via": "Mbabane-Durban"},
    ],
}

# Map country ISO3 to default IATA airport for the main city
COUNTRY_DEFAULT_AIRPORT: Dict[str, str] = {
    "DZA": "ALG", "EGY": "CAI", "MAR": "CMN", "TUN": "TUN", "LBY": "TIP",
    "SEN": "DKR", "CIV": "ABJ", "GHA": "ACC", "NGA": "LOS", "MLI": "BKO",
    "BFA": "OUA", "NER": "NIM", "BEN": "COO", "TGO": "LFW", "CMR": "DLA",
    "GAB": "LBV", "COG": "BZV", "COD": "FIH", "AGO": "LAD", "TCD": "NDJ",
    "CAF": "BGF", "KEN": "NBO", "TZA": "DAR", "UGA": "EBB", "RWA": "KGL",
    "BDI": "BJM", "ETH": "ADD", "DJI": "JIB", "ZAF": "JNB", "BWA": "GBE",
    "NAM": "WDH", "ZMB": "LUN", "ZWE": "HRE", "MOZ": "MPM", "MWI": "LLW",
    "LSO": "MSU", "SWZ": "MTS", "MUS": "MRU", "MDG": "TNR", "SSD": "JUB",
}

# Map country ISO3 to default sea port LOCODE
COUNTRY_DEFAULT_PORT: Dict[str, str] = {
    "MAR": "MAPTM", "DZA": "DZALG", "TUN": "TNRAD", "EGY": "EGPSD",
    "LBY": "EGALY",  # fallback (Libyan ports not in dataset)
    "SEN": "SNDKR", "CIV": "CIABJ", "GHA": "GHTEM", "NGA": "NGAPP",
    "CMR": "CMDLA", "COG": "CGPNR", "AGO": "AOLAD",
    "KEN": "KEMBA", "TZA": "TZDAR", "DJI": "DJJIB",
    "ZAF": "ZADUR", "MOZ": "MZMPM", "MUS": "MUPLU", "NAM": "NAWVB",
}


def _co2_kg(weight_tonnes: float, distance_km: float, mode: str) -> float:
    """Calculate CO2 emissions in kg."""
    if weight_tonnes <= 0 or distance_km <= 0:
        return 0.0
    factor = CO2_FACTORS_G_PER_TKM.get(mode, CO2_FACTORS_G_PER_TKM["road"])
    return round(weight_tonnes * distance_km * factor / 1000.0, 1)


def _avg_transit(rmin: Optional[int], rmax: Optional[int]) -> Optional[float]:
    if rmin is None and rmax is None:
        return None
    if rmin is None:
        return rmax
    if rmax is None:
        return rmin
    return (rmin + rmax) / 2.0


def _find_corridor_for_pair(country_a: str, country_b: str) -> Optional[Dict[str, Any]]:
    """Find a corridor that connects the two countries (in either direction)."""
    corridors = get_land_corridors_list()
    a, b = country_a.upper(), country_b.upper()
    best = None
    for c in corridors:
        countries = [x.upper() for x in c.get("countries", [])]
        if a in countries and b in countries:
            # Prefer corridors where a and b are endpoints or close in chain
            score = abs(countries.index(a) - countries.index(b))
            if best is None or score < best[0]:
                best = (score, c)
    return best[1] if best else None


def _sea_option(
    origin_country: str, destination_country: str,
    weight_kg: float, container_type: str = "teu",
) -> Optional[Dict[str, Any]]:
    """Sea-only option (port to port)."""
    o_port = COUNTRY_DEFAULT_PORT.get(origin_country.upper())
    d_port = COUNTRY_DEFAULT_PORT.get(destination_country.upper())
    if not o_port or not d_port or o_port == d_port:
        return None
    sea = sea_get_total_cost(o_port, d_port, container_type.lower())
    if not sea:
        return None
    weight_tonnes = weight_kg / 1000.0
    dist_km = sea["distance_nm"] * NM_TO_KM
    co2 = _co2_kg(weight_tonnes, dist_km, "sea")
    return {
        "mode": "sea",
        "label": "Maritime direct",
        "label_en": "Sea direct",
        "icon": "ship",
        "segments": [
            {
                "mode": "sea",
                "from": sea["origin_port"],
                "from_locode": sea["origin_locode"],
                "to": sea["destination_port"],
                "to_locode": sea["destination_locode"],
                "distance_km": round(dist_km),
                "transit_days_min": sea["transit_days_min"],
                "transit_days_max": sea["transit_days_max"],
                "cost_usd": sea["total_cost_usd"],
                "carriers": sea.get("carriers", []),
            }
        ],
        "total_cost_usd": sea["total_cost_usd"],
        "container_type": container_type.lower(),
        "transit_days_min": sea["transit_days_min"],
        "transit_days_max": sea["transit_days_max"],
        "co2_kg": co2,
        "distance_km": round(dist_km),
        "available": True,
        "feasibility": "high",
        "notes": sea.get("notes", ""),
        "source": sea.get("source", "Maritime — Drewry / CMA CGM / MSC rate cards 2024"),
    }


def _air_option(
    origin_country: str, destination_country: str,
    weight_kg: float, commodity: str = "general",
    volume_m3: float = 0.0,
) -> Optional[Dict[str, Any]]:
    """Air-only option (airport to airport)."""
    o_iata = COUNTRY_DEFAULT_AIRPORT.get(origin_country.upper())
    d_iata = COUNTRY_DEFAULT_AIRPORT.get(destination_country.upper())
    if not o_iata or not d_iata or o_iata == d_iata:
        return None
    air = get_air_freight_cost(
        origin_iata=o_iata, destination_iata=d_iata,
        weight_kg=weight_kg, volume_m3=volume_m3, commodity=commodity,
    )
    if not air:
        return None
    weight_tonnes = weight_kg / 1000.0
    co2 = _co2_kg(weight_tonnes, air["distance_km"], "air")
    return {
        "mode": "air",
        "label": "Aérien direct",
        "label_en": "Air direct",
        "icon": "plane",
        "segments": [
            {
                "mode": "air",
                "from": air["origin_airport"],
                "from_iata": air["origin_iata"],
                "to": air["destination_airport"],
                "to_iata": air["destination_iata"],
                "distance_km": air["distance_km"],
                "transit_days_min": air["transit_days_min"],
                "transit_days_max": air["transit_days_max"],
                "cost_usd": air["total_cost_usd"],
                "carriers": air.get("carriers", []),
            }
        ],
        "total_cost_usd": air["total_cost_usd"],
        "transit_days_min": air["transit_days_min"],
        "transit_days_max": air["transit_days_max"],
        "co2_kg": co2,
        "distance_km": air["distance_km"],
        "available": True,
        "feasibility": "high",
        "notes": air.get("notes", ""),
        "source": air.get("source", "Air — IATA TACT 2024"),
    }


def _land_option(
    origin_country: str, destination_country: str,
    weight_tonnes: float, cargo_type: str = "general",
) -> Optional[Dict[str, Any]]:
    """Land-only option using a single corridor connecting both countries."""
    corridor = _find_corridor_for_pair(origin_country, destination_country)
    if not corridor:
        return None
    land = get_land_freight_cost(
        corridor["corridor_id"], "road", weight_tonnes, cargo_type,
    )
    if not land:
        return None
    dist_km = land.get("length_km") or corridor.get("length_km", 0)
    co2 = _co2_kg(weight_tonnes, dist_km, "road")
    return {
        "mode": "land",
        "label": f"Terrestre — {corridor['name']}",
        "label_en": f"Land — {corridor['name']}",
        "icon": "truck",
        "segments": [
            {
                "mode": "road",
                "from": corridor.get("start_node"),
                "to": corridor.get("end_node"),
                "corridor_id": corridor["corridor_id"],
                "corridor_name": corridor["name"],
                "countries": corridor.get("countries", []),
                "distance_km": dist_km,
                "transit_days_min": land.get("transit_days_min"),
                "transit_days_max": land.get("transit_days_max"),
                "cost_usd": land.get("total_cost_usd"),
            }
        ],
        "total_cost_usd": land.get("total_cost_usd"),
        "transit_days_min": land.get("transit_days_min"),
        "transit_days_max": land.get("transit_days_max"),
        "co2_kg": co2,
        "distance_km": dist_km,
        "available": True,
        "feasibility": "medium",
        "notes": "Corridor terrestre direct — convient pour pays voisins.",
        "source": "Banque Mondiale SSATP / UNECA / AfDB",
    }


def _sea_then_land_option(
    origin_country: str, destination_country: str,
    weight_kg: float, container_type: str,
    weight_tonnes: float, cargo_type: str = "container",
) -> List[Dict[str, Any]]:
    """For landlocked destinations: sea (origin port -> gateway port) + land (gateway -> destination)."""
    dest = destination_country.upper()
    gateways = LANDLOCKED_GATEWAYS.get(dest, [])
    if not gateways:
        return []
    origin_port = COUNTRY_DEFAULT_PORT.get(origin_country.upper())
    if not origin_port:
        return []

    options: List[Dict[str, Any]] = []
    for gw in gateways:
        gw_port = gw["port"]
        gw_country = gw["port_country"]
        if origin_port == gw_port:
            continue

        # Leg 1: sea
        sea = sea_get_total_cost(origin_port, gw_port, container_type.lower())
        if not sea:
            continue

        # Leg 2: corridor from gateway country to landlocked country
        corridor = _find_corridor_for_pair(gw_country, dest)
        if not corridor:
            continue
        land = get_land_freight_cost(
            corridor["corridor_id"], "road", weight_tonnes, cargo_type,
        )
        if not land:
            continue

        sea_dist_km = sea["distance_nm"] * NM_TO_KM
        land_dist_km = land.get("length_km") or corridor.get("length_km", 0)
        sea_co2 = _co2_kg(weight_tonnes, sea_dist_km, "sea")
        land_co2 = _co2_kg(weight_tonnes, land_dist_km, "road")

        total_cost = round((sea["total_cost_usd"] or 0) + (land.get("total_cost_usd") or 0))
        tmin = (sea["transit_days_min"] or 0) + (land.get("transit_days_min") or 0)
        tmax = (sea["transit_days_max"] or 0) + (land.get("transit_days_max") or 0)

        options.append({
            "mode": "multimodal",
            "label": f"Maritime + Terrestre — via {sea['destination_port']}",
            "label_en": f"Sea + Land — via {sea['destination_port']}",
            "icon": "ship-truck",
            "via_port": sea["destination_port"],
            "via_port_locode": gw_port,
            "via_country": gw_country,
            "corridor_name": corridor["name"],
            "segments": [
                {
                    "mode": "sea",
                    "leg": 1,
                    "from": sea["origin_port"],
                    "from_locode": sea["origin_locode"],
                    "to": sea["destination_port"],
                    "to_locode": sea["destination_locode"],
                    "distance_km": round(sea_dist_km),
                    "transit_days_min": sea["transit_days_min"],
                    "transit_days_max": sea["transit_days_max"],
                    "cost_usd": sea["total_cost_usd"],
                    "carriers": sea.get("carriers", []),
                    "co2_kg": sea_co2,
                },
                {
                    "mode": "road",
                    "leg": 2,
                    "from": corridor.get("start_node"),
                    "to": corridor.get("end_node"),
                    "corridor_id": corridor["corridor_id"],
                    "corridor_name": corridor["name"],
                    "countries": corridor.get("countries", []),
                    "distance_km": land_dist_km,
                    "transit_days_min": land.get("transit_days_min"),
                    "transit_days_max": land.get("transit_days_max"),
                    "cost_usd": land.get("total_cost_usd"),
                    "co2_kg": land_co2,
                },
            ],
            "total_cost_usd": total_cost,
            "container_type": container_type.lower(),
            "transit_days_min": tmin,
            "transit_days_max": tmax,
            "co2_kg": round(sea_co2 + land_co2, 1),
            "distance_km": round(sea_dist_km + land_dist_km),
            "available": True,
            "feasibility": "high",
            "notes": (
                f"Trajet maritime de {sea['origin_port']} à {sea['destination_port']} "
                f"puis corridor « {corridor['name']} » jusqu'à destination."
            ),
            "source": (
                "Maritime: Drewry/CMA CGM/MSC 2024 · "
                "Terrestre: Banque Mondiale SSATP / UNECA / AfDB"
            ),
        })
    return options


def compare_multimodal(
    origin_country: str,
    destination_country: str,
    weight_kg: float,
    volume_m3: float = 0.0,
    container_type: str = "teu",
    air_commodity: str = "general",
    land_cargo_type: str = "container",
) -> Dict[str, Any]:
    """Main comparator: returns all viable route options."""
    options: List[Dict[str, Any]] = []
    weight_tonnes = max(weight_kg / 1000.0, 0.0)

    sea_opt = _sea_option(origin_country, destination_country, weight_kg, container_type)
    if sea_opt:
        options.append(sea_opt)

    air_opt = _air_option(
        origin_country, destination_country, weight_kg, air_commodity, volume_m3,
    )
    if air_opt:
        options.append(air_opt)

    land_opt = _land_option(
        origin_country, destination_country, weight_tonnes, land_cargo_type,
    )
    if land_opt:
        options.append(land_opt)

    multimodal_opts = _sea_then_land_option(
        origin_country, destination_country, weight_kg, container_type,
        weight_tonnes, land_cargo_type,
    )
    options.extend(multimodal_opts)

    # Sort by total_cost_usd ascending; mark cheapest, fastest, greenest
    if options:
        for o in options:
            o["transit_days_avg"] = _avg_transit(
                o.get("transit_days_min"), o.get("transit_days_max"),
            )
        cheapest_idx = min(
            range(len(options)),
            key=lambda i: options[i].get("total_cost_usd") or float("inf"),
        )
        fastest_idx = min(
            range(len(options)),
            key=lambda i: options[i].get("transit_days_avg") or float("inf"),
        )
        greenest_idx = min(
            range(len(options)),
            key=lambda i: options[i].get("co2_kg") or float("inf"),
        )
        options[cheapest_idx]["is_cheapest"] = True
        options[fastest_idx]["is_fastest"] = True
        options[greenest_idx]["is_greenest"] = True

    return {
        "origin_country": origin_country.upper(),
        "destination_country": destination_country.upper(),
        "is_destination_landlocked": destination_country.upper() in LANDLOCKED_AFRICA,
        "weight_kg": weight_kg,
        "volume_m3": volume_m3,
        "container_type": container_type.lower(),
        "options": options,
        "options_count": len(options),
        "co2_methodology": {
            "factors_g_per_tkm": CO2_FACTORS_G_PER_TKM,
            "source": "IPCC AR6, IEA Transport 2023, GLEC Framework v3",
        },
        "data_year": 2024,
    }
