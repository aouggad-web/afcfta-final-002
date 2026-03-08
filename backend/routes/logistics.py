"""
Logistics routes - Ports, Airports, Land corridors, Free Zones
Multimodal logistics platform for African trade infrastructure
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from logistics_data import (
    get_all_ports,
    get_port_by_id,
    get_ports_by_type,
    get_top_ports_by_teu,
    search_ports
)
from logistics_air_data import (
    get_all_airports,
    get_airport_by_id,
    get_top_airports_by_cargo,
    search_airports
)
from free_zones_data import get_free_zones_by_country
from logistics_fees_data import (
    get_all_shipping_routes,
    get_routes_from_port,
    get_route_between,
    get_port_thc,
    get_all_port_thc,
    get_total_cost,
)
from logistics_land_data import (
    get_all_corridors,
    get_corridors_by_country,
    get_corridor_by_id,
    get_all_nodes,
    get_nodes_by_type,
    get_osbp_nodes,
    get_all_operators,
    get_operators_by_type,
    search_corridors,
    get_corridors_statistics
)

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

@router.get("/ports/{port_id}")
async def get_port_details(port_id: str):
    """Get detailed information for a specific port"""
    port = get_port_by_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port {port_id} not found")
    return port

@router.get("/ports/type/{port_type}")
async def get_ports_filtered_by_type(port_type: str):
    """
    Get ports filtered by type
    Port types: Hub Transhipment, Hub Regional, Maritime Commercial
    """
    valid_types = ["Hub Transhipment", "Hub Regional", "Maritime Commercial"]
    if port_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid port type. Valid types: {', '.join(valid_types)}"
        )
    ports = get_ports_by_type(port_type)
    return {
        "port_type": port_type,
        "count": len(ports),
        "ports": ports
    }

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
    return {
        "count": len(ports),
        "ports": ports
    }

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
    return {
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/statistics")
async def get_logistics_statistics():
    """Get global logistics statistics for African ports (cached 2 h)."""
    if CACHE_AVAILABLE:
        cache_key = generate_cache_key("logistics:statistics")
        cached = cache_get(cache_key)
        if cached:
            return cached

    all_ports = get_all_ports()
    
    total_teu = sum(
        p.get('latest_stats', {}).get('container_throughput_teu', 0) 
        for p in all_ports
    )
    total_cargo = sum(
        p.get('latest_stats', {}).get('cargo_throughput_tons', 0) 
        for p in all_ports
    )
    
    # Count ports by type
    port_types: dict = {}
    for port in all_ports:
        ptype = port.get('port_type', 'Unknown')
        port_types[ptype] = port_types.get(ptype, 0) + 1
    
    # Count ports by country
    ports_by_country: dict = {}
    for port in all_ports:
        country = port.get('country_name', 'Unknown')
        ports_by_country[country] = ports_by_country.get(country, 0) + 1
    
    result = {
        "total_ports": len(all_ports),
        "total_container_throughput_teu": total_teu,
        "total_cargo_throughput_tons": total_cargo,
        "ports_by_type": port_types,
        "ports_by_country": dict(sorted(ports_by_country.items(), key=lambda x: x[1], reverse=True)),
        "year": 2024
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
        return {
            "count": len(airports),
            "airports": airports
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading airports data: {str(e)}")

@router.get("/air/airports/{airport_id}")
async def get_airport_details(airport_id: str):
    """Get detailed information for a specific airport"""
    airport = get_airport_by_id(airport_id)
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport {airport_id} not found")
    return airport

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
    return {
        "count": len(airports),
        "airports": airports
    }

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
    return {
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/air/statistics")
async def get_air_logistics_statistics():
    """Get global air cargo statistics for African airports"""
    all_airports = get_all_airports()
    
    total_cargo = sum(
        a.get('historical_stats', [{}])[0].get('cargo_throughput_tons', 0) if a.get('historical_stats') else 0
        for a in all_airports
    )
    total_mail = sum(
        a.get('historical_stats', [{}])[0].get('mail_throughput_tons', 0) if a.get('historical_stats') else 0
        for a in all_airports
    )
    
    airports_by_country = {}
    for airport in all_airports:
        country = airport.get('country_name', 'Unknown')
        airports_by_country[country] = airports_by_country.get(country, 0) + 1
    
    return {
        "total_airports": len(all_airports),
        "total_cargo_throughput_tons": total_cargo,
        "total_mail_throughput_tons": total_mail,
        "airports_by_country": dict(sorted(airports_by_country.items(), key=lambda x: x[1], reverse=True)),
        "year": 2024
    }

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
        return {
            "count": len(zones),
            "zones": zones
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading free zones data: {str(e)}")

# ==========================================
# LAND CORRIDORS ENDPOINTS
# ==========================================

@router.get("/land/corridors")
async def get_land_corridors(
    corridor_type: str = None,
    importance: str = None,
    country_iso: str = None
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
    
    return {
        "count": len(corridors),
        "corridors": corridors
    }

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
    
    return {
        "count": len(nodes),
        "nodes": nodes
    }

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
    
    return {
        "count": len(operators),
        "operators": operators
    }

@router.get("/land/search")
async def search_land_corridors(q: str):
    """Search corridors by name, country, or description"""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    results = search_corridors(q)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/land/statistics")
async def get_land_logistics_statistics():
    """Get global statistics about African land corridors"""
    return get_corridors_statistics()


# ==========================================
# PORT-TO-PORT SHIPPING FEES ENDPOINTS
# ==========================================

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
                    "message": f"No routes found departing from {origin.upper()}"
                }
            return {
                "origin_locode": origin.upper(),
                "count": len(routes),
                "routes": routes
            }
        routes = get_all_shipping_routes()
        return {
            "count": len(routes),
            "routes": routes,
            "data_year": 2024,
            "source": "Drewry Maritime Research, UNCTAD MRTS 2024, Maersk/CMA CGM/MSC published tariffs"
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
                   "Check /api/logistics/fees/routes for available routes."
        )
    return route


@router.get("/fees/cost")
async def get_total_shipping_cost(
    origin: str,
    destination: str,
    container_type: str = "teu"
):
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
            detail=f"Invalid container_type '{container_type}'. Valid values: {', '.join(valid_types)}"
        )
    result = get_total_cost(origin.upper(), destination.upper(), ctype)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No shipping route found between {origin.upper()} and {destination.upper()}."
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
                status_code=404,
                detail=f"THC data not available for port {locode.upper()}."
            )
        return thc
    return {
        "count": len(get_all_port_thc()),
        "ports": get_all_port_thc(),
        "data_year": 2024,
        "source": "Official port authority tariff books 2024 (TMPA, ANP, NPA, KPA, Transnet, etc.)"
    }
