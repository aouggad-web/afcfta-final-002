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
    """Find a corridor that connects the two countries (operational corridors preferred).

    Returns the best-matching corridor; planned/under-construction corridors
    are kept as fallback if no operational corridor exists.
    """
    corridors = get_land_corridors_list()
    a, b = country_a.upper(), country_b.upper()
    operational: List[Tuple[int, Dict[str, Any]]] = []
    future: List[Tuple[int, Dict[str, Any]]] = []
    for c in corridors:
        countries = [x.upper() for x in c.get("countries", [])]
        if a in countries and b in countries:
            score = abs(countries.index(a) - countries.index(b))
            status = (c.get("status") or "Opérationnel").lower()
            if any(k in status for k in ("planifi", "constr", "étude", "etude", "faisabilit")):
                future.append((score, c))
            else:
                operational.append((score, c))
    if operational:
        operational.sort(key=lambda x: x[0])
        return operational[0][1]
    if future:
        future.sort(key=lambda x: x[0])
        return future[0][1]
    return None


def _find_all_corridors_for_pair(country_a: str, country_b: str) -> List[Dict[str, Any]]:
    """Return all corridors connecting the two countries, operational first then future."""
    corridors = get_land_corridors_list()
    a, b = country_a.upper(), country_b.upper()
    matches = []
    for c in corridors:
        countries = [x.upper() for x in c.get("countries", [])]
        if a in countries and b in countries:
            matches.append(c)
    return matches


def _corridor_phase(c: Dict[str, Any]) -> str:
    """Return normalized phase: 'operational' | 'under_construction' | 'planned' | 'study'."""
    status = (c.get("status") or "").lower()
    if any(k in status for k in ("opérationnel", "operational", "réhabilitation")):
        return "operational"
    if "constr" in status:
        return "under_construction"
    if "planifi" in status:
        return "planned"
    if "étude" in status or "etude" in status or "faisabilit" in status:
        return "study"
    return "operational"


def _rail_then_road_option(
    origin_country: str, destination_country: str,
    weight_tonnes: float, cargo_type: str = "container",
) -> List[Dict[str, Any]]:
    """Rail-then-road chaining.

    Useful for scenarios like Alger→Ouagadougou:
      Leg 1: Rail Alger → Tamanrasset (corridor CORR-RAIL-ALGER-TAM-019)
      Leg 2: Road Tamanrasset → Ouagadougou via Niamey (corridor CORR-TRANSSAH-OUAGA-021)

    Logic:
      1. Find rail corridor(s) that start in origin country.
      2. For each rail terminus (start_node + country), look for road corridors
         that start at the same node/country and contain destination country.
    """
    corridors = get_land_corridors_list()
    origin = origin_country.upper()
    dest = destination_country.upper()
    options: List[Dict[str, Any]] = []

    rail_corridors = [
        c for c in corridors
        if (c.get("type") or "").lower() == "rail"
        and origin in [x.upper() for x in c.get("countries", [])]
        and c.get("start_node") and c.get("end_node")
    ]

    for rail in rail_corridors:
        rail_end_node = rail["end_node"]
        # Compute rail leg cost
        rail_data = get_land_freight_cost(
            rail["corridor_id"], "rail", weight_tonnes, cargo_type,
        )
        if not rail_data:
            continue
        rail_dist = rail_data.get("length_km") or rail.get("length_km", 0)
        rail_co2 = _co2_kg(weight_tonnes, rail_dist, "rail")

        # Find road corridors that start at the rail terminus and reach destination
        for road in corridors:
            if (road.get("type") or "").lower() != "road":
                continue
            road_countries = [x.upper() for x in road.get("countries", [])]
            if dest not in road_countries:
                continue
            # Match by start_node (e.g., "Tamanrasset" == "Tamanrasset")
            if road.get("start_node") != rail_end_node:
                continue
            road_data = get_land_freight_cost(
                road["corridor_id"], "road", weight_tonnes, cargo_type,
            )
            if not road_data:
                continue
            road_dist = road_data.get("length_km") or road.get("length_km", 0)
            road_co2 = _co2_kg(weight_tonnes, road_dist, "road")

            total_cost = round((rail_data.get("total_cost_usd") or 0) + (road_data.get("total_cost_usd") or 0))
            tmin = (rail_data.get("transit_days_min") or 0) + (road_data.get("transit_days_min") or 0)
            tmax = (rail_data.get("transit_days_max") or 0) + (road_data.get("transit_days_max") or 0)
            total_dist = rail_dist + road_dist
            total_co2 = round(rail_co2 + road_co2, 1)

            rail_phase = _corridor_phase(rail)
            road_phase = _corridor_phase(road)
            phase = (
                "operational" if rail_phase == road_phase == "operational"
                else "planned" if "planned" in (rail_phase, road_phase) or "study" in (rail_phase, road_phase)
                else "under_construction"
            )
            is_future = phase != "operational"

            options.append({
                "mode": "multimodal",
                "corridor_mode": "rail_road",
                "label": f"Rail + Route — via {rail_end_node}",
                "label_en": f"Rail + Road — via {rail_end_node}",
                "icon": "rail-truck",
                "via_node": rail_end_node,
                "corridor_name": f"{rail['name']} → {road['name']}",
                "phase": phase,
                "status": rail.get("status") if is_future else "Opérationnel",
                "is_future": is_future,
                "segments": [
                    {
                        "mode": "rail",
                        "leg": 1,
                        "from": rail.get("start_node"),
                        "to": rail.get("end_node"),
                        "corridor_id": rail["corridor_id"],
                        "corridor_name": rail["name"],
                        "countries": rail.get("countries", []),
                        "distance_km": rail_dist,
                        "transit_days_min": rail_data.get("transit_days_min"),
                        "transit_days_max": rail_data.get("transit_days_max"),
                        "cost_usd": rail_data.get("total_cost_usd"),
                        "co2_kg": rail_co2,
                        "status": rail.get("status"),
                    },
                    {
                        "mode": "road",
                        "leg": 2,
                        "from": road.get("start_node"),
                        "to": road.get("end_node"),
                        "corridor_id": road["corridor_id"],
                        "corridor_name": road["name"],
                        "countries": road.get("countries", []),
                        "distance_km": road_dist,
                        "transit_days_min": road_data.get("transit_days_min"),
                        "transit_days_max": road_data.get("transit_days_max"),
                        "cost_usd": road_data.get("total_cost_usd"),
                        "co2_kg": road_co2,
                        "status": road.get("status"),
                    },
                ],
                "total_cost_usd": total_cost,
                "transit_days_min": tmin,
                "transit_days_max": tmax,
                "co2_kg": total_co2,
                "distance_km": total_dist,
                "available": not is_future,
                "feasibility": "high" if not is_future else "future",
                "notes": (
                    f"Rail {rail['name']} ({rail_dist} km) puis route "
                    f"{road['name']} ({road_dist} km). Économise 60-80% des émissions vs Aérien."
                ),
                "source": (
                    f"Rail: {rail.get('source_org') or 'PIDA'} · "
                    f"Route: {road.get('source_org') or 'Banque Mondiale SSATP'}"
                ),
            })

    return options


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
) -> List[Dict[str, Any]]:
    """Land-only options. Returns one per matching corridor, ordered by status."""
    corridors = _find_all_corridors_for_pair(origin_country, destination_country)
    options: List[Dict[str, Any]] = []
    for corridor in corridors:
        # For planned/under-construction corridors, still compute the modeled cost
        # so the user sees the projected economics.
        land = get_land_freight_cost(
            corridor["corridor_id"], corridor.get("type", "road"), weight_tonnes, cargo_type,
        )
        if not land:
            continue
        dist_km = land.get("length_km") or corridor.get("length_km", 0)
        co2 = _co2_kg(weight_tonnes, dist_km, "road")
        phase = _corridor_phase(corridor)
        mode_mode = corridor.get("type", "road")  # road / rail / multimodal
        # Rail uses lower CO2 factor
        if mode_mode == "rail":
            co2 = _co2_kg(weight_tonnes, dist_km, "rail")
        is_future = phase != "operational"

        options.append({
            "mode": "land",
            "corridor_mode": mode_mode,
            "label": f"Terrestre — {corridor['name']}",
            "label_en": f"Land — {corridor['name']}",
            "icon": "rail" if mode_mode == "rail" else "truck",
            "phase": phase,
            "status": corridor.get("status"),
            "is_future": is_future,
            "segments": [
                {
                    "mode": "rail" if mode_mode == "rail" else ("multimodal" if mode_mode == "multimodal" else "road"),
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
            "available": not is_future,
            "feasibility": "medium" if not is_future else "future",
            "notes": (
                corridor.get("infra_details") or
                "Corridor terrestre direct — convient pour pays voisins."
            ),
            "source": corridor.get("source_org") or "Banque Mondiale SSATP / UNECA / AfDB",
        })
    return options


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

        # Leg 2: each corridor from gateway country to landlocked country
        corridors = _find_all_corridors_for_pair(gw_country, dest)
        for corridor in corridors:
            land = get_land_freight_cost(
                corridor["corridor_id"], corridor.get("type", "road"), weight_tonnes, cargo_type,
            )
            if not land:
                continue

            sea_dist_km = sea["distance_nm"] * NM_TO_KM
            land_dist_km = land.get("length_km") or corridor.get("length_km", 0)
            sea_co2 = _co2_kg(weight_tonnes, sea_dist_km, "sea")
            land_mode = corridor.get("type", "road")
            co2_mode = "rail" if land_mode == "rail" else "road"
            land_co2 = _co2_kg(weight_tonnes, land_dist_km, co2_mode)

            total_cost = round((sea["total_cost_usd"] or 0) + (land.get("total_cost_usd") or 0))
            tmin = (sea["transit_days_min"] or 0) + (land.get("transit_days_min") or 0)
            tmax = (sea["transit_days_max"] or 0) + (land.get("transit_days_max") or 0)

            phase = _corridor_phase(corridor)
            is_future = phase != "operational"

            options.append({
                "mode": "multimodal",
                "corridor_mode": land_mode,
                "label": (
                    f"Maritime + {'Rail' if land_mode == 'rail' else 'Terrestre'} — "
                    f"via {sea['destination_port']} → {corridor['name']}"
                ),
                "label_en": f"Sea + {'Rail' if land_mode == 'rail' else 'Land'} — via {sea['destination_port']}",
                "icon": "ship-rail" if land_mode == "rail" else "ship-truck",
                "via_port": sea["destination_port"],
                "via_port_locode": gw_port,
                "via_country": gw_country,
                "corridor_name": corridor["name"],
                "phase": phase,
                "status": corridor.get("status"),
                "is_future": is_future,
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
                        "mode": co2_mode,
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
                "available": not is_future,
                "feasibility": "high" if not is_future else "future",
                "notes": (
                    f"Trajet maritime de {sea['origin_port']} à {sea['destination_port']} "
                    f"puis corridor « {corridor['name']} » jusqu'à destination."
                ),
                "source": (
                    "Maritime: Drewry/CMA CGM/MSC 2024 · "
                    f"Terrestre: {corridor.get('source_org') or 'Banque Mondiale SSATP / UNECA / AfDB'}"
                ),
            })
    return options


def _roi_interpretation(
    future_label: str,
    ref_label: str,
    weight_kg: float,
    cost_saving: float,
    co2_saving: float,
    time_saving_days: float,
) -> str:
    """Phrase la comparaison route future vs route actuelle, en gérant le cas où
    la route future est en fait plus chère/plus polluante (mauvaise alternative
    de coût mais potentiellement plus rapide ou plus fiable)."""
    tons = f"{weight_kg / 1000:.0f}"
    if cost_saving >= 0 and co2_saving >= 0:
        return (
            f"Si la route « {future_label} » devient opérationnelle, "
            f"chaque expédition de {tons} t économisera "
            f"${round(cost_saving):,} USD et {round(co2_saving):,} kg CO₂ "
            f"vs la meilleure option actuelle ({ref_label})."
        )
    parts = []
    if cost_saving >= 0:
        parts.append(f"économisera ${round(cost_saving):,} USD")
    else:
        parts.append(f"coûtera ${round(-cost_saving):,} USD de plus")
    if co2_saving >= 0:
        parts.append(f"évitera {round(co2_saving):,} kg CO₂")
    else:
        parts.append(f"émettra {round(-co2_saving):,} kg CO₂ de plus")
    time_note = ""
    if time_saving_days > 0:
        time_note = f" Délai réduit de {time_saving_days:.1f} j."
    elif time_saving_days < 0:
        time_note = f" Délai allongé de {-time_saving_days:.1f} j."
    return (
        f"La route « {future_label} » {' et '.join(parts)} par expédition de {tons} t "
        f"vs la meilleure option actuelle ({ref_label}).{time_note} "
        "Cette route future peut néanmoins présenter d'autres avantages (fiabilité, "
        "diversification des itinéraires, désenclavement) non capturés par ce seul calcul de coût."
    )


def compare_multimodal(
    origin_country: str,
    destination_country: str,
    weight_kg: float,
    volume_m3: float = 0.0,
    container_type: str = "teu",
    air_commodity: str = "general",
    land_cargo_type: str = "container",
    include_future: bool = True,
) -> Dict[str, Any]:
    """Main comparator: returns all viable route options (operational + future)."""
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

    land_opts = _land_option(
        origin_country, destination_country, weight_tonnes, land_cargo_type,
    )
    options.extend(land_opts)

    # Rail-then-road chaining (e.g. Train Alger-Tamanrasset + Route Tam-Ouagadougou)
    rail_road_opts = _rail_then_road_option(
        origin_country, destination_country, weight_tonnes, land_cargo_type,
    )
    options.extend(rail_road_opts)

    multimodal_opts = _sea_then_land_option(
        origin_country, destination_country, weight_kg, container_type,
        weight_tonnes, land_cargo_type,
    )
    options.extend(multimodal_opts)

    # Filter out future options if not requested
    if not include_future:
        options = [o for o in options if not o.get("is_future")]

    # Annotate each
    for o in options:
        o["transit_days_avg"] = _avg_transit(
            o.get("transit_days_min"), o.get("transit_days_max"),
        )
        # Default values for badges so frontend can read consistently
        o.setdefault("phase", "operational")
        o.setdefault("status", "Opérationnel")
        o.setdefault("is_future", False)

    # Compute "best of" badges only among OPERATIONAL options to avoid suggesting
    # a planned/under-construction route as "the cheapest right now".
    operational_idxs = [i for i, o in enumerate(options) if not o.get("is_future")]
    if operational_idxs:
        cheapest = min(operational_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf"))
        fastest = min(operational_idxs, key=lambda i: options[i].get("transit_days_avg") or float("inf"))
        greenest = min(operational_idxs, key=lambda i: options[i].get("co2_kg") or float("inf"))
        options[cheapest]["is_cheapest"] = True
        options[fastest]["is_fastest"] = True
        options[greenest]["is_greenest"] = True

    # Among future options, surface savings opportunities (best future cost / CO2)
    future_idxs = [i for i, o in enumerate(options) if o.get("is_future")]
    if future_idxs:
        future_cheapest = min(future_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf"))
        future_greenest = min(future_idxs, key=lambda i: options[i].get("co2_kg") or float("inf"))
        options[future_cheapest]["is_future_cheapest"] = True
        options[future_greenest]["is_future_greenest"] = True

    # ROI Infrastructure: compute BEFORE the final sort so indices stay valid.
    roi = None
    if operational_idxs and future_idxs:
        non_air_ops = [i for i in operational_idxs if options[i].get("mode") != "air"]
        ref_idx = (
            min(non_air_ops, key=lambda i: options[i].get("total_cost_usd") or float("inf"))
            if non_air_ops else None
        )
        if ref_idx is None:
            # Fallback: best operational including air
            ref_idx = min(operational_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf"))
        # Also keep the air-direct option for "vs air" comparison
        air_idx = next((i for i in operational_idxs if options[i].get("mode") == "air"), None)
        air_ref = options[air_idx] if air_idx is not None else None

        # Best future by cost
        best_future_cost = min(future_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf"))
        best_future_co2 = min(future_idxs, key=lambda i: options[i].get("co2_kg") or float("inf"))
        best_future_time = min(future_idxs, key=lambda i: options[i].get("transit_days_avg") or float("inf"))

        bf_cost = options[best_future_cost]
        bf_co2 = options[best_future_co2]
        bf_time = options[best_future_time]

        # Computed savings per TEU
        cost_saving_per_teu = (ref.get("total_cost_usd") or 0) - (bf_cost.get("total_cost_usd") or 0)
        co2_saving_per_teu = (ref.get("co2_kg") or 0) - (bf_co2.get("co2_kg") or 0)
        time_saving_days = ((ref.get("transit_days_avg") or 0) - (bf_time.get("transit_days_avg") or 0))

        # vs Air
        cost_saving_vs_air = None
        co2_saving_vs_air = None
        time_loss_vs_air = None
        if air_ref:
            cost_saving_vs_air = (air_ref.get("total_cost_usd") or 0) - (bf_cost.get("total_cost_usd") or 0)
            co2_saving_vs_air = (air_ref.get("co2_kg") or 0) - (bf_co2.get("co2_kg") or 0)
            time_loss_vs_air = (bf_time.get("transit_days_avg") or 0) - (air_ref.get("transit_days_avg") or 0)

        # Annual projection (assume 100 TEU/year typical SME flow — conservative)
        teu_per_year_default = 100
        annual_cost_savings = round(cost_saving_per_teu * teu_per_year_default)
        annual_co2_savings_tonnes = round((co2_saving_per_teu * teu_per_year_default) / 1000.0, 1)

        roi = {
            "reference_operational": {
                "label": ref.get("label"),
                "mode": ref.get("mode"),
                "cost_usd": ref.get("total_cost_usd"),
                "transit_days_avg": ref.get("transit_days_avg"),
                "co2_kg": ref.get("co2_kg"),
            },
            "best_future_cost": {
                "label": bf_cost.get("label"),
                "status": bf_cost.get("status"),
                "cost_usd": bf_cost.get("total_cost_usd"),
                "transit_days_avg": bf_cost.get("transit_days_avg"),
                "co2_kg": bf_cost.get("co2_kg"),
            },
            "best_future_co2": {
                "label": bf_co2.get("label"),
                "status": bf_co2.get("status"),
                "co2_kg": bf_co2.get("co2_kg"),
            },
            "best_future_time": {
                "label": bf_time.get("label"),
                "status": bf_time.get("status"),
                "transit_days_avg": bf_time.get("transit_days_avg"),
            },
            "per_shipment": {
                "cost_savings_usd": round(cost_saving_per_teu),
                "cost_savings_pct": (
                    round((cost_saving_per_teu / ref["total_cost_usd"]) * 100, 1)
                    if ref.get("total_cost_usd") else None
                ),
                "co2_savings_kg": round(co2_saving_per_teu),
                "co2_savings_pct": (
                    round((co2_saving_per_teu / ref["co2_kg"]) * 100, 1)
                    if ref.get("co2_kg") else None
                ),
                "time_savings_days": round(time_saving_days, 1),
                "cost_savings_vs_air_usd": round(cost_saving_vs_air) if cost_saving_vs_air is not None else None,
                "cost_savings_vs_air_pct": (
                    round((cost_saving_vs_air / air_ref["total_cost_usd"]) * 100, 1)
                    if air_ref and air_ref.get("total_cost_usd") else None
                ),
                "co2_savings_vs_air_kg": round(co2_saving_vs_air) if co2_saving_vs_air is not None else None,
                "time_loss_vs_air_days": round(time_loss_vs_air, 1) if time_loss_vs_air is not None else None,
            },
            "annual_projection": {
                "teu_per_year_assumption": teu_per_year_default,
                "annual_cost_savings_usd": annual_cost_savings,
                "annual_co2_savings_tonnes": annual_co2_savings_tonnes,
            },
            "interpretation": _roi_interpretation(
                bf_cost.get("label"), ref.get("label"), weight_kg,
                cost_saving_per_teu, co2_saving_per_teu, time_saving_days,
            ),
        }

    # Sort: operational first (by cost), then future
    options.sort(key=lambda o: (
        1 if o.get("is_future") else 0,
        o.get("total_cost_usd") or float("inf"),
    ))

    return {
        "origin_country": origin_country.upper(),
        "destination_country": destination_country.upper(),
        "is_destination_landlocked": destination_country.upper() in LANDLOCKED_AFRICA,
        "weight_kg": weight_kg,
        "volume_m3": volume_m3,
        "container_type": container_type.lower(),
        "options": options,
        "options_count": len(options),
        "operational_count": sum(1 for o in options if not o.get("is_future")),
        "future_count": sum(1 for o in options if o.get("is_future")),
        "roi_infrastructure": roi,
        "co2_methodology": {
            "factors_g_per_tkm": CO2_FACTORS_G_PER_TKM,
            "source": "IPCC AR6, IEA Transport 2023, GLEC Framework v3",
        },
        "data_year": 2024,
    }
