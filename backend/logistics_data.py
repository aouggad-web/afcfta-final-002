"""
Logistics API endpoints for African maritime ports
"""
import json
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException

# Determine data file path with fallback
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "json"
PORTS_FILE = DATA_DIR / "ports_africains.json"
if not PORTS_FILE.exists():
    PORTS_FILE = ROOT_DIR / "ports_africains.json"

def load_ports_data():
    """Load African ports data from JSON file"""
    with open(PORTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_ports(country_iso: Optional[str] = None) -> List[dict]:
    """
    Get all ports or filter by country ISO code
    """
    ports = load_ports_data()
    
    if country_iso:
        country_iso = country_iso.upper()
        ports = [p for p in ports if p['country_iso'] == country_iso]
    
    return ports

def get_port_by_id(port_id: str) -> Optional[dict]:
    """
    Get detailed port information by port ID
    """
    ports = load_ports_data()
    
    for port in ports:
        if port['port_id'] == port_id:
            return port
    
    return None

def get_ports_by_type(port_type: str) -> List[dict]:
    """
    Get ports filtered by type (Hub Transhipment, Hub Regional, Maritime Commercial)
    """
    ports = load_ports_data()
    return [p for p in ports if p.get('port_type', '').lower() == port_type.lower()]

def get_top_ports_by_teu(limit: int = 20) -> List[dict]:
    """
    Get top ports by container throughput (TEU)
    """
    ports = load_ports_data()
    
    # Filter ports with TEU data and sort by TEU descending
    ports_with_teu = [
        p for p in ports 
        if p.get('latest_stats', {}).get('container_throughput_teu')
    ]
    
    sorted_ports = sorted(
        ports_with_teu, 
        key=lambda x: x['latest_stats']['container_throughput_teu'],
        reverse=True
    )
    
    return sorted_ports[:limit]

def search_ports(query: str) -> List[dict]:
    """
    Search ports by name or UN LOCODE
    """
    ports = load_ports_data()
    query_lower = query.lower()
    
    results = [
        p for p in ports 
        if query_lower in p['port_name'].lower() 
        or query_lower in p.get('un_locode', '').lower()
        or query_lower in p['country_name'].lower()
    ]
    
    return results
