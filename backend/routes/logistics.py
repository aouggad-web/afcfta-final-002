"""
Logistics routes - Ports, Airports, Land corridors, Free Zones
Multimodal logistics platform for African trade infrastructure
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from free_zones_data import get_free_zones_by_country
from logistics_air_data import (
    get_airport_by_id,
    get_all_airports,
    get_top_airports_by_cargo,
    search_airports,
)
from logistics_air_fees_data import (
    get_air_fee_airports,
    get_air_freight_cost,
    get_commodity_types,
)
from logistics_bulk_fees_data import (
    _FREIGHT_OVERRIDES,
    _MULTIPLIER_BOUNDS,
    BULK_PORT_ATTRIBUTES,
    VESSEL_CLASSES,
    get_bulk_freight_cost,
)
from logistics_data import (
    get_all_ports,
    get_port_by_id,
    get_ports_by_type,
    get_top_ports_by_teu,
    search_ports,
)
from logistics_fees_data import (
    PORTS,
    get_all_port_thc,
    get_all_shipping_routes,
    get_fee_ports,
    get_port_thc,
    get_route_between,
    get_routes_from_port,
    get_total_cost,
)
from logistics_land_data import (
    get_all_corridors,
    get_all_nodes,
    get_all_operators,
    get_corridor_by_id,
    get_corridors_by_country,
    get_corridors_statistics,
    get_nodes_by_type,
    get_operators_by_type,
    get_osbp_nodes,
    search_corridors,
)
from logistics_land_fees_data import get_cargo_types as get_land_cargo_types
from logistics_land_fees_data import (
    get_land_corridors_list,
    get_land_freight_cost,
)
from logistics_operators_data import (
    LOGISTICS_OPERATORS,
    get_all_operators_with_contacts,
    get_operator_by_id,
    get_operators_by_country,
    get_operators_summary,
)
from services.multimodal_freight_service import (
    COUNTRY_DEFAULT_AIRPORT,
    COUNTRY_PORTS,
    LANDLOCKED_AFRICA,
    LANDLOCKED_GATEWAYS,
    compare_multimodal,
)
from services.shipment_estimator import classify_bulk_commodity

# Optional cache integration
try:
    from services.cache_service import cache_get, cache_set, generate_cache_key

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

router = APIRouter(prefix="/logistics")

# ==========================================
# MARITIME PORTS ENDPOINTS
# ==========================================


@router.get("/ports")
async def get_ports(country_iso: Optional[str] = None):
    """
    Get all maritime ports or filter by country ISO code
    Query params:
    - country_iso: Filter ports by country (e.g., MAR, NGA, ZAF)
    """
    if CACHE_AVAILABLE:
        cache_key = generate_cache_key("logistics:ports", country_iso or "all")
        cached = cache_get(cache_key)
        if cached:
            return cached

    try:
        ports = get_all_ports(country_iso=country_iso)
        result = {"count": len(ports), "ports": ports}
        if CACHE_AVAILABLE:
            cache_set(cache_key, result, "countries")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading ports data: {str(e)}")


@router.get("/ports/search")
async def search_ports_endpoint(q: str):
    """
    Search ports by name, UN LOCODE, or country name
    Query params:
    - q: Search query string
    """
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    results = search_ports(q)
    return {"query": q, "count": len(results), "results": results}


@router.get("/ports/type/{port_type}")
async def get_ports_filtered_by_type(port_type: str):
    """
    Get ports filtered by type
    Port types: Hub Transhipment, Hub Regional, Maritime Commercial
    """
    valid_types = ["Hub Transhipment", "Hub Regional", "Maritime Commercial"]
    if port_type not in valid_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid port type. Valid types: {', '.join(valid_types)}"
        )
    ports = get_ports_by_type(port_type)
    return {"port_type": port_type, "count": len(ports), "ports": ports}


@router.get("/ports/top/teu")
async def get_top_ports_teu(limit: int = 20):
    """
    Get top ports by container throughput (TEU)
    Query params:
    - limit: Number of ports to return (default: 20, max: 50)
    """
    if limit > 50:
        limit = 50
    ports = get_top_ports_by_teu(limit=limit)
    return {"count": len(ports), "ports": ports}


@router.get("/ports/{port_id}")
async def get_port_details(port_id: str):
    """Get detailed information for a specific port"""
    port = get_port_by_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port {port_id} not found")
    return port


@router.get("/statistics")
async def get_logistics_statistics():
    """Get global logistics statistics for African ports (cached 2 h)."""
    if CACHE_AVAILABLE:
        cache_key = generate_cache_key("logistics:statistics")
        cached = cache_get(cache_key)
        if cached:
            return cached

    all_ports = get_all_ports()

    total_teu = sum(p.get("latest_stats", {}).get("container_throughput_teu", 0) for p in all_ports)
    total_cargo = sum(p.get("latest_stats", {}).get("cargo_throughput_tons", 0) for p in all_ports)

    # Count ports by type
    port_types: dict = {}
    for port in all_ports:
        ptype = port.get("port_type", "Unknown")
        port_types[ptype] = port_types.get(ptype, 0) + 1

    # Count ports by country
    ports_by_country: dict = {}
    for port in all_ports:
        country = port.get("country_name", "Unknown")
        ports_by_country[country] = ports_by_country.get(country, 0) + 1

    result = {
        "total_ports": len(all_ports),
        "total_container_throughput_teu": total_teu,
        "total_cargo_throughput_tons": total_cargo,
        "ports_by_type": port_types,
        "ports_by_country": dict(
            sorted(ports_by_country.items(), key=lambda x: x[1], reverse=True)
        ),
        "year": 2024,
    }
    if CACHE_AVAILABLE:
        cache_set(cache_key, result, "countries")
    return result


# ==========================================
# AIR CARGO ENDPOINTS
# ==========================================


@router.get("/air/airports")
async def get_airports(country_iso: Optional[str] = None):
    """
    Get all airports or filter by country ISO code
    Query params:
    - country_iso: Filter airports by country (e.g., ZAF, ETH, KEN)
    """
    try:
        airports = get_all_airports(country_iso=country_iso)
        return {"count": len(airports), "airports": airports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading airports data: {str(e)}")


@router.get("/air/airports/top/cargo")
async def get_top_airports_cargo(limit: int = 20):
    """
    Get top airports by cargo throughput (tons)
    Query params:
    - limit: Number of airports to return (default: 20, max: 50)
    """
    if limit > 50:
        limit = 50
    airports = get_top_airports_by_cargo(limit=limit)
    return {"count": len(airports), "airports": airports}


@router.get("/air/airports/search")
async def search_airports_endpoint(q: str):
    """
    Search airports by name, IATA code, or country name
    Query params:
    - q: Search query string
    """
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    results = search_airports(q)
    return {"query": q, "count": len(results), "results": results}


@router.get("/air/airports/{airport_id}")
async def get_airport_details(airport_id: str):
    """Get detailed information for a specific airport"""
    airport = get_airport_by_id(airport_id)
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport {airport_id} not found")
    return airport


@router.get("/air/statistics")
async def get_air_logistics_statistics():
    """Get global air cargo statistics for African airports"""
    all_airports = get_all_airports()

    total_cargo = sum(
        (
            a.get("historical_stats", [{}])[0].get("cargo_throughput_tons", 0)
            if a.get("historical_stats")
            else 0
        )
        for a in all_airports
    )
    total_mail = sum(
        (
            a.get("historical_stats", [{}])[0].get("mail_throughput_tons", 0)
            if a.get("historical_stats")
            else 0
        )
        for a in all_airports
    )

    airports_by_country = {}
    for airport in all_airports:
        country = airport.get("country_name", "Unknown")
        airports_by_country[country] = airports_by_country.get(country, 0) + 1

    return {
        "total_airports": len(all_airports),
        "total_cargo_throughput_tons": total_cargo,
        "total_mail_throughput_tons": total_mail,
        "airports_by_country": dict(
            sorted(airports_by_country.items(), key=lambda x: x[1], reverse=True)
        ),
        "year": 2024,
    }


# ==========================================
# AIR FREIGHT CALCULATOR ENDPOINTS
# ==========================================


@router.get("/air/fees/airports")
async def get_air_freight_airports():
    """Liste des aéroports africains sélectionnables dans le calculateur de fret aérien."""
    airports = get_air_fee_airports()
    return {
        "count": len(airports),
        "airports": airports,
        "data_year": 2024,
        "source": "IATA TACT 2024, registre cargo panafricain (64 aéroports)",
    }


@router.get("/air/fees/commodities")
async def get_air_freight_commodities():
    """Types de marchandise et leurs coefficients de tarification."""
    return {"commodities": get_commodity_types()}


@router.get("/air/fees/cost")
async def get_air_freight_cost_endpoint(
    origin: str,
    destination: str,
    weight_kg: float,
    volume_m3: Optional[float] = None,
    commodity: str = "general",
):
    """
    Calcule le coût de fret aérien (poids taxable + surcharges) entre deux aéroports.

    Query params :
    - origin / destination : codes IATA (ex: NBO, LOS)
    - weight_kg : poids brut réel (kg)
    - volume_m3 : volume total (m³, optionnel) — pour le poids volumétrique (167 kg/m³)
    - commodity : general | perishable | pharma | dangerous | valuable | live
    """
    if weight_kg <= 0:
        raise HTTPException(status_code=400, detail="weight_kg doit être supérieur à 0")
    result = get_air_freight_cost(
        origin.upper(), destination.upper(), weight_kg, volume_m3, commodity
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aéroports invalides ou identiques ({origin.upper()} → {destination.upper()}).",
        )
    return result


# ==========================================
# FREE ZONES ENDPOINTS
# ==========================================


@router.get("/free-zones")
async def get_free_zones(country_iso: Optional[str] = None):
    """
    Get African Free Trade Zones (Zones Franches)
    Query params:
    - country_iso: Filter by country (e.g., MAR, DZA, EGY)
    """
    try:
        zones = get_free_zones_by_country(country_iso)
        return {"count": len(zones), "zones": zones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading free zones data: {str(e)}")


# ==========================================
# LAND CORRIDORS ENDPOINTS
# ==========================================


@router.get("/land/corridors")
async def get_land_corridors(
    corridor_type: str = None, importance: str = None, country_iso: str = None
):
    """
    Get all land corridors (road/rail) with optional filters

    Query parameters:
    - corridor_type: 'road', 'rail', 'multimodal'
    - importance: 'high', 'medium'
    - country_iso: ISO3 country code (e.g., 'CIV')
    """
    if country_iso:
        corridors = get_corridors_by_country(country_iso)
    else:
        corridors = get_all_corridors(corridor_type=corridor_type, importance=importance)

    return {"count": len(corridors), "corridors": corridors}


@router.get("/land/corridors/{corridor_id}")
async def get_land_corridor_details(corridor_id: str):
    """Get detailed information for a specific land corridor"""
    corridor = get_corridor_by_id(corridor_id)
    if not corridor:
        raise HTTPException(status_code=404, detail=f"Corridor {corridor_id} not found")
    return corridor


@router.get("/land/nodes")
async def get_land_nodes(node_type: str = None, osbp_only: bool = False):
    """
    Get all logistical nodes (border crossings, dry ports, terminals)

    Query parameters:
    - node_type: 'border_crossing', 'dry_port', 'rail_terminal', 'intermodal_hub'
    - osbp_only: true to get only One-Stop Border Posts
    """
    if osbp_only:
        nodes = get_osbp_nodes()
    elif node_type:
        nodes = get_nodes_by_type(node_type)
    else:
        nodes = get_all_nodes()

    return {"count": len(nodes), "nodes": nodes}


@router.get("/land/operators")
async def get_land_operators(operator_type: str = None):
    """
    Get all land transport operators

    Query parameters:
    - operator_type: 'rail_operator', 'trucking_company'
    """
    if operator_type:
        operators = get_operators_by_type(operator_type)
    else:
        operators = get_all_operators()

    return {"count": len(operators), "operators": operators}


@router.get("/land/search")
async def search_land_corridors(q: str):
    """Search corridors by name, country, or description"""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    results = search_corridors(q)
    return {"query": q, "count": len(results), "results": results}


@router.get("/land/statistics")
async def get_land_logistics_statistics():
    """Get global statistics about African land corridors"""
    return get_corridors_statistics()


# ==========================================
# LAND FREIGHT CALCULATOR ENDPOINTS
# ==========================================


@router.get("/land/fees/corridors")
async def get_land_freight_corridors():
    """Liste des corridors terrestres sélectionnables dans le calculateur de fret."""
    corridors = get_land_corridors_list()
    return {
        "count": len(corridors),
        "corridors": corridors,
        "data_year": 2024,
        "source": "PIDA, Banque Mondiale SSATP, UNECA — corridors africains 2024",
    }


@router.get("/land/fees/cargo-types")
async def get_land_freight_cargo_types():
    """Types de marchandise et coefficients pour le fret terrestre."""
    return {"cargo_types": get_land_cargo_types()}


@router.get("/land/fees/cost")
async def get_land_freight_cost_endpoint(
    corridor_id: str,
    mode: str = "road",
    weight_tons: float = 30.0,
    cargo_type: str = "general",
):
    """
    Calcule le coût de fret terrestre (route/rail) sur un corridor africain.

    Query params :
    - corridor_id : identifiant du corridor (ex: CORR-ABIDJAN-LAGOS-002)
    - mode : 'road' ou 'rail' (selon disponibilité du corridor)
    - weight_tons : tonnage transporté (tonnes, défaut 30 = un camion)
    - cargo_type : general | container | perishable | dangerous | bulk
    """
    if weight_tons <= 0:
        raise HTTPException(status_code=400, detail="weight_tons doit être supérieur à 0")
    result = get_land_freight_cost(corridor_id, mode, weight_tons, cargo_type)
    if not result:
        raise HTTPException(status_code=404, detail=f"Corridor '{corridor_id}' introuvable.")
    return result


# ==========================================
# PORT-TO-PORT SHIPPING FEES ENDPOINTS
# ==========================================


@router.get("/fees/ports")
async def get_fee_calculator_ports():
    """
    Liste des ports africains sélectionnables dans le calculateur de fret maritime.
    Retourne locode, nom, pays, drapeau et région pour chaque port couvert.
    """
    ports = get_fee_ports()
    return {
        "count": len(ports),
        "ports": ports,
        "data_year": 2024,
        "source": "Drewry Maritime Research 2024, UNCTAD MRTS 2024, barèmes portuaires officiels",
    }


@router.get("/fees/routes")
async def get_shipping_routes(origin: Optional[str] = None):
    """
    Get port-to-port maritime shipping fee data for African routes.

    Query params:
    - origin: UN LOCODE of origin port (e.g. MAPTM, NGAPP). Omit to get all routes.

    Returns ocean freight rates (2024), transit times, carriers, and data sources.
    No mocked data — all rates sourced from published carrier tariffs and UNCTAD/World Bank benchmarks.
    """
    try:
        if origin:
            routes = get_routes_from_port(origin.upper())
            if not routes:
                return {
                    "origin_locode": origin.upper(),
                    "count": 0,
                    "routes": [],
                    "message": f"No routes found departing from {origin.upper()}",
                }
            return {"origin_locode": origin.upper(), "count": len(routes), "routes": routes}
        routes = get_all_shipping_routes()
        return {
            "count": len(routes),
            "routes": routes,
            "data_year": 2024,
            "source": "Drewry Maritime Research, UNCTAD MRTS 2024, Maersk/CMA CGM/MSC published tariffs",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading shipping fees data: {str(e)}")


@router.get("/fees/route")
async def get_single_route_fees(origin: str, destination: str):
    """
    Get the shipping fee between two specific ports.

    Query params:
    - origin: UN LOCODE of origin port (e.g. MAPTM)
    - destination: UN LOCODE of destination port (e.g. NGAPP)

    Returns ocean freight rate, transit time, carriers, and data source.
    """
    route = get_route_between(origin.upper(), destination.upper())
    if not route:
        raise HTTPException(
            status_code=404,
            detail=f"No direct shipping route found between {origin.upper()} and {destination.upper()}. "
            "Check /api/logistics/fees/routes for available routes.",
        )
    return route


@router.get("/fees/cost")
async def get_total_shipping_cost(origin: str, destination: str, container_type: str = "teu"):
    """
    Compute the all-in shipping cost (ocean freight + THC at origin + THC at destination).

    Query params:
    - origin: UN LOCODE of origin port (e.g. MAPTM)
    - destination: UN LOCODE of destination port (e.g. NGAPP)
    - container_type: 'teu' (20ft), 'feu' (40ft standard), or 'feu_hc' (40ft high-cube). Default: teu

    Returns itemised cost breakdown in USD.
    """
    valid_types = ["teu", "feu", "feu_hc"]
    ctype = container_type.lower()
    if ctype not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid container_type '{container_type}'. Valid values: {', '.join(valid_types)}",
        )
    result = get_total_cost(origin.upper(), destination.upper(), ctype)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No shipping route found between {origin.upper()} and {destination.upper()}.",
        )
    return result


@router.get("/fees/thc")
async def get_terminal_handling_charges(locode: Optional[str] = None):
    """
    Get Terminal Handling Charges (THC) for African ports.

    Query params:
    - locode: UN LOCODE of a specific port (e.g. MAPTM). Omit to get all ports.

    Returns official THC rates in USD for TEU, FEU, and FEU HC containers.
    Source: Individual port authority tariff books (2024 editions).
    """
    if locode:
        thc = get_port_thc(locode.upper())
        if not thc:
            raise HTTPException(
                status_code=404, detail=f"THC data not available for port {locode.upper()}."
            )
        return thc
    return {
        "count": len(get_all_port_thc()),
        "ports": get_all_port_thc(),
        "data_year": 2024,
        "source": "Official port authority tariff books 2024 (TMPA, ANP, NPA, KPA, Transnet, etc.)",
    }


# =============================================================================
# INTERVENANTS LOGISTIQUES — Opérateurs avec contacts réels
# =============================================================================


@router.get("/operators")
async def get_logistics_operators(category: Optional[str] = None):
    """
    Retourne tous les intervenants logistiques africains avec leurs coordonnées réelles.

    Catégories disponibles :
    - armateurs : Compagnies maritimes (MSC, Maersk, CMA CGM…)
    - port_operators : Opérateurs de terminaux (DP World, APM Terminals, Bolloré…)
    - transitaires : Freight forwarders (DHL, DSV, Kuehne+Nagel, GEODIS…)
    - rail_operators : Compagnies ferroviaires (ONCF, SNTF, Transnet, KRC…)
    - trucking_companies : Transporteurs routiers
    - air_cargo : Compagnies cargo aérien
    - customs_agents : Commissionnaires en douane & Autorités douanières
    - regulatory_bodies : Organismes de régulation & associations
    """
    data = get_all_operators_with_contacts(category)
    summary = get_operators_summary()
    if category and category not in data:
        raise HTTPException(
            status_code=404,
            detail=f"Catégorie '{category}' inconnue. Catégories: {list(LOGISTICS_OPERATORS.keys())}",
        )
    return {
        "operators": data,
        "summary": summary,
        "data_source": "Sites officiels des opérateurs (HQ vérifiés), Lloyd's List, IATA, BIMCO, UNCTAD 2025",
        "last_updated": "Juin 2026",
    }


@router.get("/operators/summary")
async def get_logistics_operators_summary():
    """Résumé statistique des intervenants logistiques."""
    return get_operators_summary()


@router.get("/operators/country/{country_iso}")
async def get_operators_for_country(country_iso: str):
    """
    Retourne tous les intervenants logistiques présents dans un pays donné.
    country_iso : code ISO-3 du pays (ex: DZA, MAR, NGA, KEN…)
    """
    operators = get_operators_by_country(country_iso.upper())
    if not operators:
        return {
            "country_iso": country_iso.upper(),
            "count": 0,
            "operators": [],
            "message": f"Aucun intervenant référencé pour {country_iso.upper()}",
        }
    return {
        "country_iso": country_iso.upper(),
        "count": len(operators),
        "operators": operators,
    }


@router.get("/operators/{operator_id}")
async def get_single_operator(operator_id: str):
    """
    Retourne le détail complet d'un intervenant logistique par son ID.
    Exemple: msc, maersk, cmacgm, dhl_global, oncf, sntf…
    """
    operator = get_operator_by_id(operator_id.lower())
    if not operator:
        raise HTTPException(status_code=404, detail=f"Opérateur '{operator_id}' non trouvé.")
    return operator


# ==========================================
# MULTIMODAL FREIGHT COMPARATOR ENDPOINTS
# ==========================================


@router.get("/multimodal/countries")
async def get_multimodal_supported_countries():
    """
    Return the list of African countries supported by the multimodal comparator,
    indicating which ones are landlocked (sea+corridor combinations available).
    """
    coastal = sorted(COUNTRY_PORTS.keys())
    air_only = sorted(set(COUNTRY_DEFAULT_AIRPORT.keys()) - set(coastal) - LANDLOCKED_AFRICA)
    landlocked = sorted(LANDLOCKED_AFRICA)
    return {
        "coastal_countries": coastal,
        "landlocked_countries": landlocked,
        "air_only_countries": air_only,
        "all_supported": sorted(
            set(COUNTRY_DEFAULT_AIRPORT.keys()) | set(COUNTRY_PORTS.keys()) | LANDLOCKED_AFRICA
        ),
        "landlocked_gateways": LANDLOCKED_GATEWAYS,
    }


@router.get("/multimodal/compare")
async def compare_freight_modes(
    origin: str,
    destination: str,
    weight_kg: float = 1000.0,
    volume_m3: float = 0.0,
    container_type: str = "teu",
    air_commodity: str = "general",
    land_cargo_type: str = "container",
    include_future: bool = True,
):
    """
    Compare freight options (sea, air, land, sea+land combo) between two countries.

    Returns operational routes ranked by cost, plus planned / under-construction
    future corridors (Transsaharienne, Train Alger-Tamanrasset, Lagos-Calabar rail…)
    annotated with their status when ``include_future=True``.
    """
    if weight_kg <= 0:
        raise HTTPException(status_code=400, detail="weight_kg must be > 0")
    if origin.upper() == destination.upper():
        raise HTTPException(status_code=400, detail="origin and destination must differ")
    return compare_multimodal(
        origin_country=origin,
        destination_country=destination,
        weight_kg=weight_kg,
        volume_m3=volume_m3,
        container_type=container_type,
        air_commodity=air_commodity,
        land_cargo_type=land_cargo_type,
        include_future=include_future,
    )


# ==========================================
# BULK CARRIER (VRAQUIER) ENDPOINTS
# ==========================================


def _freight_market_freshness() -> dict:
    """État du facteur de marché live (proxy BDRY) lu depuis fret_vraquier.json."""
    ov = _FREIGHT_OVERRIDES or {}
    any_entry = next(iter(ov.values()), None)
    is_live = bool(any_entry and any_entry.get("is_live"))
    return {
        "is_live": is_live,
        "as_of": (any_entry or {}).get("as_of"),
        "proxy": (any_entry or {}).get("proxy"),
        "source": (any_entry or {}).get("source"),
        "multiplier_bounds": list(_MULTIPLIER_BOUNDS),
        "per_class_multiplier": {cls: (ov.get(cls) or {}).get("multiplier") for cls in ov},
    }


@router.get("/bulk/vessel-classes")
async def get_bulk_vessel_classes():
    """Classes de navires vraquiers (référence) + fraîcheur du facteur de marché."""
    classes = [
        {
            "id": cid,
            "label": spec["label"],
            "min_dwt": spec["min_dwt"],
            "max_dwt": spec["max_dwt"],
            "max_parcel_t": spec["max_parcel_t"],
            "loaded_draft_m": spec["loaded_draft_m"],
            "co2_g_per_tkm": spec["co2_g_per_tkm"],
        }
        for cid, spec in VESSEL_CLASSES.items()
    ]
    return {"vessel_classes": classes, "market": _freight_market_freshness()}


@router.get("/bulk/ports")
async def get_bulk_ports():
    """Ports du registre avec leurs attributs vrac connus (tirant d'eau, terminaux).

    Un port sans attributs vrac renseignés n'applique AUCUNE contrainte (marqué
    ``bulk_verified: False`` et ``max_draft_m: null``) — jamais de blocage inventé.
    """
    out = []
    for locode, p in sorted(PORTS.items()):
        attrs = BULK_PORT_ATTRIBUTES.get(locode)
        out.append(
            {
                "locode": locode,
                "name": p.get("name"),
                "country_iso3": p.get("iso"),
                "max_draft_m": (attrs or {}).get("max_draft_m"),
                "bulk_terminals": (attrs or {}).get("bulk_terminals") or [],
                "attributes_known": attrs is not None,
                "attributes_verified": bool((attrs or {}).get("verified")),
            }
        )
    return {"ports": out, "count": len(out)}


@router.get("/bulk/cost")
async def get_bulk_cost(
    origin: str,
    destination: str,
    tonnes: float,
    hs_code: Optional[str] = None,
):
    """Coût de fret vraquier modélisé entre deux ports (LOCODE) pour un tonnage.

    Si ``hs_code`` est fourni, la classification vrac restreint les classes de
    navire admissibles et signale le seuil de bascule conteneur→vraquier ainsi
    que le vrac liquide (marché tanker, hors périmètre).
    """
    if tonnes <= 0:
        raise HTTPException(status_code=400, detail="tonnes must be > 0")
    o, d = (origin or "").upper(), (destination or "").upper()
    if o == d:
        raise HTTPException(status_code=400, detail="origin and destination must differ")
    if o not in PORTS or d not in PORTS:
        raise HTTPException(status_code=400, detail="unknown port LOCODE")

    bulk = classify_bulk_commodity(hs_code) if hs_code else None
    commodity = None
    if bulk:
        commodity = {
            "label": bulk.get("label"),
            "category": bulk.get("category"),
            "is_liquid": bulk.get("is_liquid"),
            "container_threshold_tonnes": bulk.get("container_threshold_tonnes"),
            "vessel_classes": bulk.get("vessel_classes"),
        }
        if bulk.get("is_liquid"):
            return {
                "available": False,
                "reason": "liquid_bulk",
                "commodity": commodity,
                "note": (
                    f"{bulk.get('label', 'Produit liquide')} relève du marché pétrolier "
                    "(navires-citernes) — hors périmètre du fret vraquier (vrac sec)."
                ),
            }
        threshold = bulk.get("container_threshold_tonnes")
        if threshold and tonnes < threshold:
            return {
                "available": False,
                "reason": "below_threshold",
                "commodity": commodity,
                "note": (
                    f"Lot de {tonnes:g} t sous le seuil de bascule vraquier "
                    f"({threshold:g} t) pour {bulk.get('label')} — expédition conteneurisée "
                    "(ensachée) recommandée."
                ),
            }

    result = get_bulk_freight_cost(o, d, tonnes, allowed_classes=(bulk or {}).get("vessel_classes"))
    if not result:
        raise HTTPException(status_code=422, detail="bulk freight cost unavailable for this pair")
    return {"available": True, "commodity": commodity, "cost": result}
