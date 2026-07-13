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

from logistics_air_fees_data import _airport_registry as air_registry
from logistics_air_fees_data import (
    get_air_freight_cost,
)
from logistics_fees_data import (
    PORT_THC,
    PORTS,
    SHIPPING_ROUTES,
)
from logistics_fees_data import get_total_cost as sea_get_total_cost
from logistics_land_fees_data import (
    get_land_corridors_list,
    get_land_freight_cost,
)
from logistics_operators_data import LOGISTICS_OPERATORS

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

# PROBLÈME RÉSOLU : l'option aérienne était systématiquement proposée quel que
# soit le poids (ex. un conteneur de ciment de 26 t se voyait chiffrer un fret
# aérien) — l'aérien reste par nature réservé aux envois légers/à haute
# valeur, jamais à un conteneur complet de marchandise en vrac. Plafond
# général convenu : en-dessous de 1000 kg. Les marchandises en vrac (ciment,
# minerai, céréales...) sont exclues de l'aérien quel que soit le poids, voir
# `is_bulk` dans `_air_option` / `compare_multimodal`.
AIR_FREIGHT_MAX_KG_GENERAL = 1000.0

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
    "DZA": "ALG",
    "EGY": "CAI",
    "MAR": "CMN",
    "TUN": "TUN",
    "LBY": "TIP",
    "SEN": "DKR",
    "CIV": "ABJ",
    "GHA": "ACC",
    "NGA": "LOS",
    "MLI": "BKO",
    "BFA": "OUA",
    "NER": "NIM",
    "BEN": "COO",
    "TGO": "LFW",
    "CMR": "DLA",
    "GAB": "LBV",
    "COG": "BZV",
    "COD": "FIH",
    "AGO": "LAD",
    "TCD": "NDJ",
    "CAF": "BGF",
    "KEN": "NBO",
    "TZA": "DAR",
    "UGA": "EBB",
    "RWA": "KGL",
    "BDI": "BJM",
    "ETH": "ADD",
    "DJI": "JIB",
    "ZAF": "JNB",
    "BWA": "GBE",
    "NAM": "WDH",
    "ZMB": "LUN",
    "ZWE": "HRE",
    "MOZ": "MPM",
    "MWI": "LLW",
    "LSO": "MSU",
    "SWZ": "MTS",
    "MUS": "MRU",
    "MDG": "TNR",
    "SSD": "JUB",
}

# Preferred "main" container port per country. Used only to order each country's
# ports (preferred first). Countries not listed fall back to alphabetical order.
_PREFERRED_PORT: Dict[str, str] = {
    "MAR": "MAPTM",
    "DZA": "DZALG",
    "TUN": "TNRAD",
    "EGY": "EGPSD",
    "LBY": "LYTIP",
    "SEN": "SNDKR",
    "CIV": "CIABJ",
    "GHA": "GHTEM",
    "NGA": "NGAPP",
    "CMR": "CMDLA",
    "COG": "CGPNR",
    "AGO": "AOLAD",
    "KEN": "KEMBA",
    "TZA": "TZDAR",
    "DJI": "DJJIB",
    "ZAF": "ZADUR",
    "MOZ": "MZMPM",
    "MUS": "MUPLU",
    "NAM": "NAWVB",
}


def _build_country_ports() -> Dict[str, List[str]]:
    """Map each ISO3 country to its container ports, derived from the maritime
    module's authoritative PORTS registry (no hard-coding). The preferred main
    port (when known) is ordered first so it is treated as the representative."""
    out: Dict[str, List[str]] = {}
    for locode, p in PORTS.items():
        iso = (p.get("iso") or "").upper()
        if not iso:
            continue
        out.setdefault(iso, []).append(locode)
    for iso, locodes in out.items():
        pref = _PREFERRED_PORT.get(iso)
        locodes.sort(key=lambda lc: (lc != pref, lc))
    return out


# Country ISO3 → list of all port LOCODEs (preferred port first).
COUNTRY_PORTS: Dict[str, List[str]] = _build_country_ports()

# Country ISO3 → single representative sea port. Derived from COUNTRY_PORTS so it
# stays in sync with the maritime registry. Kept for backward compatibility.
COUNTRY_DEFAULT_PORT: Dict[str, str] = {
    iso: locodes[0] for iso, locodes in COUNTRY_PORTS.items() if locodes
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


def _land_carriers(countries: List[str], corridor_mode: str) -> List[str]:
    """Transport companies able to operate a land/rail corridor.

    For rail corridors we match national rail operators by `country_iso`;
    for road / multimodal corridors we match pan-African trucking companies
    whose `africa_presence` intersects the corridor's countries.
    Returns de-duplicated company names (max 5). Empty when none are known.
    """
    cset = {str(c).upper() for c in (countries or []) if c}
    if not cset:
        return []
    names: List[str] = []
    if corridor_mode == "rail":
        for op in LOGISTICS_OPERATORS.get("rail_operators", []):
            op_countries = {str(op.get("country_iso") or "").upper()}
            op_countries |= {str(c).upper() for c in (op.get("countries") or [])}
            op_countries.discard("")
            if op_countries & cset:
                names.append(op["name"])
    else:  # road / multimodal
        for op in LOGISTICS_OPERATORS.get("trucking_companies", []):
            presence = {str(p).upper() for p in op.get("africa_presence", [])}
            if presence & cset:
                names.append(op["name"])
    seen: set = set()
    out: List[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out[:5]


def _union_carriers(*lists: List[str]) -> List[str]:
    """De-duplicated union of several carrier-name lists, order preserved."""
    seen: set = set()
    out: List[str] = []
    for lst in lists:
        for n in lst or []:
            if n not in seen:
                seen.add(n)
                out.append(n)
    return out


def _rail_then_road_option(
    origin_country: str,
    destination_country: str,
    weight_tonnes: float,
    cargo_type: str = "container",
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
        c
        for c in corridors
        if (c.get("type") or "").lower() == "rail"
        and origin in [x.upper() for x in c.get("countries", [])]
        and c.get("start_node")
        and c.get("end_node")
    ]

    for rail in rail_corridors:
        rail_end_node = rail["end_node"]
        # Compute rail leg cost
        rail_data = get_land_freight_cost(
            rail["corridor_id"],
            "rail",
            weight_tonnes,
            cargo_type,
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
                road["corridor_id"],
                "road",
                weight_tonnes,
                cargo_type,
            )
            if not road_data:
                continue
            road_dist = road_data.get("length_km") or road.get("length_km", 0)
            road_co2 = _co2_kg(weight_tonnes, road_dist, "road")

            rail_carriers = rail_data.get("operators") or _land_carriers(
                rail.get("countries", []), "rail"
            )
            road_carriers = road_data.get("operators") or _land_carriers(
                road.get("countries", []), "road"
            )

            total_cost = round(
                (rail_data.get("total_cost_usd") or 0) + (road_data.get("total_cost_usd") or 0)
            )
            tmin = (rail_data.get("transit_days_min") or 0) + (
                road_data.get("transit_days_min") or 0
            )
            tmax = (rail_data.get("transit_days_max") or 0) + (
                road_data.get("transit_days_max") or 0
            )
            total_dist = rail_dist + road_dist
            total_co2 = round(rail_co2 + road_co2, 1)

            rail_phase = _corridor_phase(rail)
            road_phase = _corridor_phase(road)
            phase = (
                "operational"
                if rail_phase == road_phase == "operational"
                else (
                    "planned"
                    if "planned" in (rail_phase, road_phase) or "study" in (rail_phase, road_phase)
                    else "under_construction"
                )
            )
            is_future = phase != "operational"

            options.append(
                {
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
                            "carriers": rail_carriers,
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
                            "carriers": road_carriers,
                        },
                    ],
                    "carriers": _union_carriers(rail_carriers, road_carriers),
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
                }
            )

    return options


def _format_sea_option(
    sea: Dict[str, Any],
    weight_tonnes: float,
    label: str,
    label_en: str,
) -> Dict[str, Any]:
    """Build a multimodal 'sea direct' option dict from a maritime-module cost
    result (output of logistics_fees_data.get_total_cost)."""
    dist_km = sea["distance_nm"] * NM_TO_KM
    co2 = _co2_kg(weight_tonnes, dist_km, "sea")
    notes = sea.get("notes", "") or ""
    if sea.get("is_modeled"):
        notes = (notes + " " if notes else "") + "Tarif maritime estimé (modèle calibré ±15-20 %)."
    return {
        "mode": "sea",
        "label": label,
        "label_en": label_en,
        "icon": "ship",
        "origin_locode": sea["origin_locode"],
        "destination_locode": sea["destination_locode"],
        "is_modeled": sea.get("is_modeled", False),
        "frequency": sea.get("frequency"),
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
        "carriers": sea.get("carriers", []),
        "total_cost_usd": sea["total_cost_usd"],
        "container_type": str(sea.get("container_type", "teu")).lower(),
        "transit_days_min": sea["transit_days_min"],
        "transit_days_max": sea["transit_days_max"],
        "co2_kg": co2,
        "distance_km": round(dist_km),
        "available": True,
        "feasibility": "high",
        "notes": notes,
        "source": sea.get("source", "Maritime — Drewry / CMA CGM / MSC rate cards 2024"),
    }


def _sea_options(
    origin_country: str,
    destination_country: str,
    weight_kg: float,
    container_type: str = "teu",
) -> List[Dict[str, Any]]:
    """Direct sea options (port → port) drawn from the maritime module's full
    route matrix. Enumerates every origin-country port × destination-country port
    pair, then surfaces the cheapest route plus — only when it uses a different
    port pair and is meaningfully faster — a second 'fastest' alternative."""
    o_ports = COUNTRY_PORTS.get(origin_country.upper(), [])
    d_ports = COUNTRY_PORTS.get(destination_country.upper(), [])
    if not o_ports or not d_ports:
        return []
    weight_tonnes = weight_kg / 1000.0

    candidates: List[Dict[str, Any]] = []
    for o_port in o_ports:
        for d_port in d_ports:
            if o_port == d_port:
                continue
            sea = sea_get_total_cost(o_port, d_port, container_type.lower())
            if sea:
                candidates.append(sea)
    if not candidates:
        return []

    def _avg_days(s: Dict[str, Any]) -> float:
        return ((s.get("transit_days_min") or 0) + (s.get("transit_days_max") or 0)) / 2.0

    cheapest = min(candidates, key=lambda s: s.get("total_cost_usd") or float("inf"))
    fastest = min(candidates, key=_avg_days)

    cheapest_pair = (cheapest["origin_locode"], cheapest["destination_locode"])
    fastest_pair = (fastest["origin_locode"], fastest["destination_locode"])

    ch_days, fa_days = _avg_days(cheapest), _avg_days(fastest)
    meaningfully_faster = fastest_pair != cheapest_pair and (
        (ch_days - fa_days) >= 2 or (ch_days and (ch_days - fa_days) / ch_days >= 0.15)
    )
    if not meaningfully_faster:
        return [_format_sea_option(cheapest, weight_tonnes, "Maritime direct", "Sea direct")]

    return [
        _format_sea_option(
            cheapest,
            weight_tonnes,
            "Maritime direct — option économique",
            "Sea direct — cheapest",
        ),
        _format_sea_option(
            fastest,
            weight_tonnes,
            "Maritime direct — option rapide",
            "Sea direct — fastest",
        ),
    ]


def _air_option(
    origin_country: str,
    destination_country: str,
    weight_kg: float,
    commodity: str = "general",
    volume_m3: float = 0.0,
    is_bulk: bool = False,
) -> Optional[Dict[str, Any]]:
    """Air-only option (airport to airport).

    Returns ``None`` (no air option offered) when the cargo is a bulk
    commodity (never flown, regardless of weight — cement, ores, cereals...)
    or when the weight exceeds ``AIR_FREIGHT_MAX_KG_GENERAL``: air freight is
    not a realistic mode for a full container load of low-value goods.
    """
    if is_bulk:
        return None
    if weight_kg is None or weight_kg > AIR_FREIGHT_MAX_KG_GENERAL:
        return None
    o_iata = COUNTRY_DEFAULT_AIRPORT.get(origin_country.upper())
    d_iata = COUNTRY_DEFAULT_AIRPORT.get(destination_country.upper())
    if not o_iata or not d_iata or o_iata == d_iata:
        return None
    air = get_air_freight_cost(
        origin_iata=o_iata,
        destination_iata=d_iata,
        weight_kg=weight_kg,
        volume_m3=volume_m3,
        commodity=commodity,
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
        "carriers": air.get("carriers", []),
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
    origin_country: str,
    destination_country: str,
    weight_tonnes: float,
    cargo_type: str = "general",
) -> List[Dict[str, Any]]:
    """Land-only options. Returns one per matching corridor, ordered by status."""
    corridors = _find_all_corridors_for_pair(origin_country, destination_country)
    options: List[Dict[str, Any]] = []
    for corridor in corridors:
        # For planned/under-construction corridors, still compute the modeled cost
        # so the user sees the projected economics.
        land = get_land_freight_cost(
            corridor["corridor_id"],
            corridor.get("type", "road"),
            weight_tonnes,
            cargo_type,
        )
        if not land:
            continue
        dist_km = land.get("length_km") or corridor.get("length_km", 0)
        co2 = _co2_kg(weight_tonnes, dist_km, "road")
        phase = _corridor_phase(corridor)
        mode_mode = corridor.get("type", "road")  # road / rail / multimodal
        land_carriers = land.get("operators") or _land_carriers(
            corridor.get("countries", []), mode_mode
        )
        # Rail uses lower CO2 factor
        if mode_mode == "rail":
            co2 = _co2_kg(weight_tonnes, dist_km, "rail")
        is_future = phase != "operational"

        options.append(
            {
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
                        "mode": (
                            "rail"
                            if mode_mode == "rail"
                            else ("multimodal" if mode_mode == "multimodal" else "road")
                        ),
                        "from": corridor.get("start_node"),
                        "to": corridor.get("end_node"),
                        "corridor_id": corridor["corridor_id"],
                        "corridor_name": corridor["name"],
                        "countries": corridor.get("countries", []),
                        "distance_km": dist_km,
                        "transit_days_min": land.get("transit_days_min"),
                        "transit_days_max": land.get("transit_days_max"),
                        "cost_usd": land.get("total_cost_usd"),
                        "carriers": land_carriers,
                    }
                ],
                "carriers": land_carriers,
                "total_cost_usd": land.get("total_cost_usd"),
                "transit_days_min": land.get("transit_days_min"),
                "transit_days_max": land.get("transit_days_max"),
                "co2_kg": co2,
                "distance_km": dist_km,
                "available": not is_future,
                "feasibility": "medium" if not is_future else "future",
                "notes": (
                    corridor.get("infra_details")
                    or "Corridor terrestre direct — convient pour pays voisins."
                ),
                "source": corridor.get("source_org") or "Banque Mondiale SSATP / UNECA / AfDB",
            }
        )
    return options


def _sea_then_land_option(
    origin_country: str,
    destination_country: str,
    weight_kg: float,
    container_type: str,
    weight_tonnes: float,
    cargo_type: str = "container",
) -> List[Dict[str, Any]]:
    """For landlocked destinations: sea (origin port -> gateway port) + land (gateway -> destination)."""
    dest = destination_country.upper()
    gateways = LANDLOCKED_GATEWAYS.get(dest, [])
    if not gateways:
        return []
    origin_ports = COUNTRY_PORTS.get(origin_country.upper(), [])
    if not origin_ports:
        return []

    options: List[Dict[str, Any]] = []
    for gw in gateways:
        gw_port = gw["port"]
        gw_country = gw["port_country"]

        # Leg 1: cheapest sea leg from any origin-country port to the gateway port
        sea_candidates = []
        for o_port in origin_ports:
            if o_port == gw_port:
                continue
            s = sea_get_total_cost(o_port, gw_port, container_type.lower())
            if s:
                sea_candidates.append(s)
        if not sea_candidates:
            continue
        sea = min(sea_candidates, key=lambda s: s.get("total_cost_usd") or float("inf"))

        # Leg 2: each corridor from gateway country to landlocked country
        corridors = _find_all_corridors_for_pair(gw_country, dest)
        for corridor in corridors:
            land = get_land_freight_cost(
                corridor["corridor_id"],
                corridor.get("type", "road"),
                weight_tonnes,
                cargo_type,
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
            land_carriers = land.get("operators") or _land_carriers(
                corridor.get("countries", []), land_mode
            )

            options.append(
                {
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
                            "carriers": land_carriers,
                        },
                    ],
                    "carriers": _union_carriers(sea.get("carriers", []), land_carriers),
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
                }
            )
    return options


def _land_then_sea_option(
    origin_country: str,
    destination_country: str,
    weight_kg: float,
    container_type: str,
    weight_tonnes: float,
    cargo_type: str = "container",
) -> List[Dict[str, Any]]:
    """For landlocked ORIGINS (ex. Éthiopie, Ouganda, Rwanda...) : land (origine
    -> port passerelle) + sea (port passerelle -> port de destination).

    Symétrique de _sea_then_land_option (qui ne couvre que les DESTINATIONS
    enclavées) — sans cette fonction, un pays enclavé qui EXPORTE n'a aucune
    route terre+mer modélisée, seulement l'avion et d'éventuels corridors
    routiers directs (souvent non opérationnels/mégaprojets encore en
    construction) : le comparateur recommandait alors systématiquement
    l'aérien pour des pays comme l'Éthiopie, même pour des envois lourds/
    bon marché où le fret aérien n'est jamais compétitif dans la réalité.
    """
    origin = origin_country.upper()
    gateways = LANDLOCKED_GATEWAYS.get(origin, [])
    if not gateways:
        return []
    dest_ports = COUNTRY_PORTS.get(destination_country.upper(), [])
    if not dest_ports:
        return []

    options: List[Dict[str, Any]] = []
    for gw in gateways:
        gw_port = gw["port"]
        gw_country = gw["port_country"]

        # Leg 1: corridor from the landlocked origin to its gateway country.
        corridors = _find_all_corridors_for_pair(origin, gw_country)

        # Leg 2: cheapest sea leg from the gateway port to any destination port.
        sea_candidates = []
        for d_port in dest_ports:
            if d_port == gw_port:
                continue
            s = sea_get_total_cost(gw_port, d_port, container_type.lower())
            if s:
                sea_candidates.append(s)
        if not sea_candidates:
            continue
        sea = min(sea_candidates, key=lambda s: s.get("total_cost_usd") or float("inf"))

        for corridor in corridors:
            land = get_land_freight_cost(
                corridor["corridor_id"],
                corridor.get("type", "road"),
                weight_tonnes,
                cargo_type,
            )
            if not land:
                continue

            sea_dist_km = sea["distance_nm"] * NM_TO_KM
            land_dist_km = land.get("length_km") or corridor.get("length_km", 0)
            sea_co2 = _co2_kg(weight_tonnes, sea_dist_km, "sea")
            land_mode = corridor.get("type", "road")
            co2_mode = "rail" if land_mode == "rail" else "road"
            land_co2 = _co2_kg(weight_tonnes, land_dist_km, co2_mode)

            total_cost = round((land.get("total_cost_usd") or 0) + (sea["total_cost_usd"] or 0))
            tmin = (land.get("transit_days_min") or 0) + (sea["transit_days_min"] or 0)
            tmax = (land.get("transit_days_max") or 0) + (sea["transit_days_max"] or 0)

            phase = _corridor_phase(corridor)
            is_future = phase != "operational"
            land_carriers = land.get("operators") or _land_carriers(
                corridor.get("countries", []), land_mode
            )

            options.append(
                {
                    "mode": "multimodal",
                    "corridor_mode": land_mode,
                    "label": (
                        f"{'Rail' if land_mode == 'rail' else 'Terrestre'} + Maritime — "
                        f"via {corridor['name']} → {sea['origin_port']}"
                    ),
                    "label_en": f"{'Rail' if land_mode == 'rail' else 'Land'} + Sea — via {sea['origin_port']}",
                    "icon": "truck-ship" if land_mode != "rail" else "rail-ship",
                    "via_port": sea["origin_port"],
                    "via_port_locode": gw_port,
                    "via_country": gw_country,
                    "corridor_name": corridor["name"],
                    "phase": phase,
                    "status": corridor.get("status"),
                    "is_future": is_future,
                    "segments": [
                        {
                            "mode": co2_mode,
                            "leg": 1,
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
                            "carriers": land_carriers,
                        },
                        {
                            "mode": "sea",
                            "leg": 2,
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
                    ],
                    "carriers": _union_carriers(sea.get("carriers", []), land_carriers),
                    "total_cost_usd": total_cost,
                    "container_type": container_type.lower(),
                    "transit_days_min": tmin,
                    "transit_days_max": tmax,
                    "co2_kg": round(sea_co2 + land_co2, 1),
                    "distance_km": round(sea_dist_km + land_dist_km),
                    "available": not is_future,
                    "feasibility": "high" if not is_future else "future",
                    "notes": (
                        f"Corridor « {corridor['name']} » jusqu'à {sea['origin_port']} "
                        f"puis trajet maritime vers {sea['destination_port']}."
                    ),
                    "source": (
                        "Maritime: Drewry/CMA CGM/MSC 2024 · "
                        f"Terrestre: {corridor.get('source_org') or 'Banque Mondiale SSATP / UNECA / AfDB'}"
                    ),
                }
            )
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
    land_cargo_type: Optional[str] = None,
    include_future: bool = True,
    is_bulk_commodity: bool = False,
    bulk_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Main comparator: returns all viable route options (operational + future).

    ``is_bulk_commodity`` flags a genuine bulk raw material (cement, ores,
    cereals, coal, crude oil, fertilizers...) identified from its HS code —
    see ``services.shipment_estimator.classify_bulk_commodity``. It never
    travels by air (regardless of weight) and defaults the land leg to the
    "bulk" cargo type instead of "container" unless the caller explicitly
    picked a different ``land_cargo_type``.
    """
    options: List[Dict[str, Any]] = []
    weight_tonnes = max(weight_kg / 1000.0, 0.0)
    effective_land_cargo_type = land_cargo_type or ("bulk" if is_bulk_commodity else "container")

    sea_opts = _sea_options(origin_country, destination_country, weight_kg, container_type)
    if is_bulk_commodity:
        for o in sea_opts:
            o["bulk_cargo_note"] = (
                f"{bulk_label or 'Marchandise en vrac'} : le tarif conteneurisé ci-dessus "
                "est utilisé comme repère faute de données de fret vraquier (bulk carrier) "
                "dans ce comparateur — le coût réel d'un affrètement en vrac diffère."
            )
    options.extend(sea_opts)

    air_opt = _air_option(
        origin_country,
        destination_country,
        weight_kg,
        air_commodity,
        volume_m3,
        is_bulk=is_bulk_commodity,
    )
    if air_opt:
        options.append(air_opt)

    land_opts = _land_option(
        origin_country,
        destination_country,
        weight_tonnes,
        effective_land_cargo_type,
    )
    options.extend(land_opts)

    # Rail-then-road chaining (e.g. Train Alger-Tamanrasset + Route Tam-Ouagadougou)
    rail_road_opts = _rail_then_road_option(
        origin_country,
        destination_country,
        weight_tonnes,
        effective_land_cargo_type,
    )
    options.extend(rail_road_opts)

    multimodal_opts = _sea_then_land_option(
        origin_country,
        destination_country,
        weight_kg,
        container_type,
        weight_tonnes,
        effective_land_cargo_type,
    )
    options.extend(multimodal_opts)

    # Symétrique : origine enclavée (ex. Éthiopie exportatrice) — terre jusqu'au
    # port passerelle puis mer. Sans cette option, un pays enclavé qui EXPORTE
    # n'avait que l'aérien ou des corridors directs souvent non opérationnels.
    land_sea_opts = _land_then_sea_option(
        origin_country,
        destination_country,
        weight_kg,
        container_type,
        weight_tonnes,
        effective_land_cargo_type,
    )
    options.extend(land_sea_opts)

    # Filter out future options if not requested
    if not include_future:
        options = [o for o in options if not o.get("is_future")]

    # Annotate each
    for o in options:
        o["transit_days_avg"] = _avg_transit(
            o.get("transit_days_min"),
            o.get("transit_days_max"),
        )
        # Default values for badges so frontend can read consistently
        o.setdefault("phase", "operational")
        o.setdefault("status", "Opérationnel")
        o.setdefault("is_future", False)

    # Compute "best of" badges only among OPERATIONAL options to avoid suggesting
    # a planned/under-construction route as "the cheapest right now".
    operational_idxs = [i for i, o in enumerate(options) if not o.get("is_future")]
    if operational_idxs:
        cheapest = min(
            operational_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf")
        )
        fastest = min(
            operational_idxs, key=lambda i: options[i].get("transit_days_avg") or float("inf")
        )
        greenest = min(operational_idxs, key=lambda i: options[i].get("co2_kg") or float("inf"))
        options[cheapest]["is_cheapest"] = True
        options[fastest]["is_fastest"] = True
        options[greenest]["is_greenest"] = True

    # Among future options, surface savings opportunities (best future cost / CO2)
    future_idxs = [i for i, o in enumerate(options) if o.get("is_future")]
    if future_idxs:
        future_cheapest = min(
            future_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf")
        )
        future_greenest = min(future_idxs, key=lambda i: options[i].get("co2_kg") or float("inf"))
        options[future_cheapest]["is_future_cheapest"] = True
        options[future_greenest]["is_future_greenest"] = True

    # ROI Infrastructure: compute BEFORE the final sort so indices stay valid.
    roi = None
    if operational_idxs and future_idxs:
        non_air_ops = [i for i in operational_idxs if options[i].get("mode") != "air"]
        ref_idx = (
            min(non_air_ops, key=lambda i: options[i].get("total_cost_usd") or float("inf"))
            if non_air_ops
            else None
        )
        if ref_idx is None:
            # Fallback: best operational including air
            ref_idx = min(
                operational_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf")
            )
        ref = options[ref_idx]
        # Also keep the air-direct option for "vs air" comparison
        air_idx = next((i for i in operational_idxs if options[i].get("mode") == "air"), None)
        air_ref = options[air_idx] if air_idx is not None else None

        # Best future by cost
        best_future_cost = min(
            future_idxs, key=lambda i: options[i].get("total_cost_usd") or float("inf")
        )
        best_future_co2 = min(future_idxs, key=lambda i: options[i].get("co2_kg") or float("inf"))
        best_future_time = min(
            future_idxs, key=lambda i: options[i].get("transit_days_avg") or float("inf")
        )

        bf_cost = options[best_future_cost]
        bf_co2 = options[best_future_co2]
        bf_time = options[best_future_time]

        # Computed savings per TEU
        cost_saving_per_teu = (ref.get("total_cost_usd") or 0) - (
            bf_cost.get("total_cost_usd") or 0
        )
        co2_saving_per_teu = (ref.get("co2_kg") or 0) - (bf_co2.get("co2_kg") or 0)
        time_saving_days = (ref.get("transit_days_avg") or 0) - (
            bf_time.get("transit_days_avg") or 0
        )

        # vs Air
        cost_saving_vs_air = None
        co2_saving_vs_air = None
        time_loss_vs_air = None
        if air_ref:
            cost_saving_vs_air = (air_ref.get("total_cost_usd") or 0) - (
                bf_cost.get("total_cost_usd") or 0
            )
            co2_saving_vs_air = (air_ref.get("co2_kg") or 0) - (bf_co2.get("co2_kg") or 0)
            time_loss_vs_air = (bf_time.get("transit_days_avg") or 0) - (
                air_ref.get("transit_days_avg") or 0
            )

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
                    if ref.get("total_cost_usd")
                    else None
                ),
                "co2_savings_kg": round(co2_saving_per_teu),
                "co2_savings_pct": (
                    round((co2_saving_per_teu / ref["co2_kg"]) * 100, 1)
                    if ref.get("co2_kg")
                    else None
                ),
                "time_savings_days": round(time_saving_days, 1),
                "cost_savings_vs_air_usd": (
                    round(cost_saving_vs_air) if cost_saving_vs_air is not None else None
                ),
                "cost_savings_vs_air_pct": (
                    round((cost_saving_vs_air / air_ref["total_cost_usd"]) * 100, 1)
                    if air_ref and air_ref.get("total_cost_usd")
                    else None
                ),
                "co2_savings_vs_air_kg": (
                    round(co2_saving_vs_air) if co2_saving_vs_air is not None else None
                ),
                "time_loss_vs_air_days": (
                    round(time_loss_vs_air, 1) if time_loss_vs_air is not None else None
                ),
            },
            "annual_projection": {
                "teu_per_year_assumption": teu_per_year_default,
                "annual_cost_savings_usd": annual_cost_savings,
                "annual_co2_savings_tonnes": annual_co2_savings_tonnes,
            },
            "interpretation": _roi_interpretation(
                bf_cost.get("label"),
                ref.get("label"),
                weight_kg,
                cost_saving_per_teu,
                co2_saving_per_teu,
                time_saving_days,
            ),
        }

    # Sort: operational first (by cost), then future
    options.sort(
        key=lambda o: (
            1 if o.get("is_future") else 0,
            o.get("total_cost_usd") or float("inf"),
        )
    )

    return {
        "origin_country": origin_country.upper(),
        "destination_country": destination_country.upper(),
        "is_destination_landlocked": destination_country.upper() in LANDLOCKED_AFRICA,
        "weight_kg": weight_kg,
        "volume_m3": volume_m3,
        "container_type": container_type.lower(),
        "land_cargo_type": effective_land_cargo_type,
        "is_bulk_commodity": is_bulk_commodity,
        "bulk_label": bulk_label if is_bulk_commodity else None,
        "air_excluded": air_opt is None,
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
