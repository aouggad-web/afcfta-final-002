"""
Logistics Air Cargo data loader for African airports
"""
import json
from pathlib import Path
from typing import List, Optional

ROOT_DIR = Path(__file__).parent.parent

def load_airports_data():
    """Load African airports data from JSON file"""
    airports_path = ROOT_DIR / "data" / "json" / "airports_africains.json"
    with open(airports_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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
