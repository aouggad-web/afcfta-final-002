"""
Logistics Air Cargo data loader for African airports
"""
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

# Determine data file path with fallback
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "json"
AIRPORTS_FILE = DATA_DIR / "airports_africains.json"
if not AIRPORTS_FILE.exists():
    AIRPORTS_FILE = ROOT_DIR / "airports_africains.json"

def load_airports_data():
    """Load African airports data, merging enhanced aviation logistics fields when available."""
    global _airports_cache
    if _airports_cache is not None:
        return _airports_cache

    with open(AIRPORTS_FILE, 'r', encoding='utf-8') as f:
        airports = json.load(f)

    _load_enhanced_airport_index()
    if _enhanced_airport_index:
        for airport in airports:
            airport_id = airport.get('airport_id')
            enhanced = _enhanced_airport_index.get(airport_id)
            if not enhanced:
                continue
            for key in ("actors", "routes", "airport_authority", "logistics_network"):
                if key in enhanced and enhanced[key]:
                    airport[key] = enhanced[key]

    _airports_cache = airports
    return _airports_cache

def get_all_airports(country_iso: Optional[str] = None) -> List[dict]:
    """
    Get all airports or filter by country ISO code
    """
    airports = load_airports_data()
    
    if country_iso:
        country_iso = country_iso.upper()
        airports = [a for a in airports if a['country_iso'] == country_iso]
    
    return airports

def get_airport_by_id(airport_id: str) -> Optional[dict]:
    """
    Get detailed airport information by airport ID
    """
    airports = load_airports_data()
    
    for airport in airports:
        if airport['airport_id'] == airport_id:
            return airport
    
    return None

def get_top_airports_by_cargo(limit: int = 20) -> List[dict]:
    """
    Get top airports by cargo throughput (tons)
    """
    airports = load_airports_data()
    
    # Filter airports with cargo data and sort by cargo descending
    airports_with_cargo = [
        a for a in airports 
        if a.get('historical_stats') and len(a['historical_stats']) > 0
    ]
    
    sorted_airports = sorted(
        airports_with_cargo,
        key=lambda x: x['historical_stats'][0].get('cargo_throughput_tons', 0),
        reverse=True
    )
    
    return sorted_airports[:limit]

def search_airports(query: str) -> List[dict]:
    """
    Search airports by name or IATA code
    """
    airports = load_airports_data()
    query_lower = query.lower()
    
    results = [
        a for a in airports 
        if query_lower in a['airport_name'].lower() 
        or query_lower in a.get('iata_code', '').lower()
        or query_lower in a['country_name'].lower()
    ]
    
    return results

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two coordinates in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

def _distance_rate(distance_km: float) -> float:
    """Get USD/kg base rate from distance tiers."""
    for band in AIR_DISTANCE_BANDS:
        if distance_km <= band["max_km"]:
            return band["rate_usd_per_kg"]
    return AIR_DISTANCE_BANDS[-1]["rate_usd_per_kg"]

def calculate_air_freight_cost(
    origin_airport_id: str,
    destination_airport_id: str,
    weight_kg: float,
    service_level: str = "standard",
    cargo_type: str = "general",
    volume_m3: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate all-in air freight cost between two airports.
    Includes freight, fuel surcharge, security, terminal handling and documentation.
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be greater than 0")
    if volume_m3 is not None and volume_m3 <= 0:
        raise ValueError("volume_m3 must be greater than 0 when provided")

    service_key = service_level.lower()
    if service_key not in AIR_SERVICE_MULTIPLIERS:
        raise ValueError(f"Invalid service_level '{service_level}'. Valid values: {', '.join(AIR_SERVICE_MULTIPLIERS.keys())}")

    cargo_key = cargo_type.lower()
    if cargo_key not in AIR_CARGO_MULTIPLIERS:
        raise ValueError(f"Invalid cargo_type '{cargo_type}'. Valid values: {', '.join(AIR_CARGO_MULTIPLIERS.keys())}")

    origin = get_airport_by_id(origin_airport_id)
    destination = get_airport_by_id(destination_airport_id)
    if not origin:
        raise ValueError(f"Origin airport {origin_airport_id} not found")
    if not destination:
        raise ValueError(f"Destination airport {destination_airport_id} not found")

    if origin_airport_id == destination_airport_id:
        raise ValueError("origin_airport_id and destination_airport_id must be different")

    distance_km = _haversine_km(
        float(origin["geo_lat"]),
        float(origin["geo_lon"]),
        float(destination["geo_lat"]),
        float(destination["geo_lon"])
    )
    base_rate = _distance_rate(distance_km)

    volumetric_weight_kg = volume_m3 * VOLUMETRIC_FACTOR_AIR_KG_PER_M3 if volume_m3 is not None else 0.0
    chargeable_weight_kg = max(weight_kg, volumetric_weight_kg)

    service_multiplier = AIR_SERVICE_MULTIPLIERS[service_key]
    cargo_multiplier = AIR_CARGO_MULTIPLIERS[cargo_key]

    freight_base_usd = chargeable_weight_kg * base_rate * service_multiplier * cargo_multiplier
    fuel_surcharge_usd = freight_base_usd * FUEL_SURCHARGE_RATE
    security_fee_usd = chargeable_weight_kg * SECURITY_FEE_USD_PER_KG
    origin_terminal_usd = max(TERMINAL_HANDLING_MIN_USD, chargeable_weight_kg * TERMINAL_HANDLING_USD_PER_KG)
    destination_terminal_usd = max(TERMINAL_HANDLING_MIN_USD, chargeable_weight_kg * TERMINAL_HANDLING_USD_PER_KG)

    total_cost_usd = (
        freight_base_usd
        + fuel_surcharge_usd
        + security_fee_usd
        + origin_terminal_usd
        + destination_terminal_usd
        + DOCUMENTATION_FEE_USD
    )

    return {
        "origin_airport_id": origin_airport_id,
        "destination_airport_id": destination_airport_id,
        "origin_airport": origin.get("airport_name"),
        "destination_airport": destination.get("airport_name"),
        "origin_iata": origin.get("iata_code"),
        "destination_iata": destination.get("iata_code"),
        "distance_km": round(distance_km, 1),
        "weight_kg": round(weight_kg, 2),
        "volume_m3": round(volume_m3, 3) if volume_m3 is not None else None,
        "volumetric_weight_kg": round(volumetric_weight_kg, 2),
        "chargeable_weight_kg": round(chargeable_weight_kg, 2),
        "service_level": service_key,
        "cargo_type": cargo_key,
        "pricing": {
            "distance_rate_usd_per_kg": base_rate,
            "service_multiplier": service_multiplier,
            "cargo_multiplier": cargo_multiplier,
            "fuel_surcharge_rate": FUEL_SURCHARGE_RATE,
            "security_fee_usd_per_kg": SECURITY_FEE_USD_PER_KG,
            "terminal_handling_usd_per_kg": TERMINAL_HANDLING_USD_PER_KG,
            "terminal_handling_min_usd": TERMINAL_HANDLING_MIN_USD,
            "documentation_fee_usd": DOCUMENTATION_FEE_USD,
        },
        "cost_breakdown_usd": {
            "freight_base_usd": round(freight_base_usd, 2),
            "fuel_surcharge_usd": round(fuel_surcharge_usd, 2),
            "security_fee_usd": round(security_fee_usd, 2),
            "origin_terminal_handling_usd": round(origin_terminal_usd, 2),
            "destination_terminal_handling_usd": round(destination_terminal_usd, 2),
            "documentation_fee_usd": DOCUMENTATION_FEE_USD,
            "total_cost_usd": round(total_cost_usd, 2),
        },
        "methodology": "Distance-tiered rate model with service and cargo multipliers (2026 air cargo benchmark model).",
    }
