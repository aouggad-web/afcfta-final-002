"""
Logistics API endpoints for African maritime ports
"""
import json
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException

# Determine data file paths with fallback
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "json"
PORTS_FILE = DATA_DIR / "ports_africains.json"
if not PORTS_FILE.exists():
    PORTS_FILE = ROOT_DIR / "ports_africains.json"

# Enhanced ports file (enriched agent data + logistics_network)
ENHANCED_PORTS_FILE = DATA_DIR / "ports_africains_enhanced_maritime_logistics.json"

# Cache
_ports_cache = None
_enhanced_index = {}  # port_id -> enhanced data

def _load_enhanced_port_index():
    """Load enhanced port data indexed by port_id."""
    global _enhanced_index
    if _enhanced_index or not ENHANCED_PORTS_FILE.exists():
        return
    try:
        with open(ENHANCED_PORTS_FILE, 'r', encoding='utf-8') as f:
            enh = json.load(f)
        for port in enh.get('enhanced_locations', []):
            pid = port.get('port_id')
            if pid:
                _enhanced_index[pid] = port
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️ Could not load enhanced ports file: {e}")

def load_ports_data():
    """Load African ports data, merging enriched agent/logistics_network fields from enhanced file."""
    global _ports_cache
    if _ports_cache is not None:
        return _ports_cache
    ports_path = ROOT_DIR / "data" / "json" / "ports_africains.json"
    with open(ports_path, 'r', encoding='utf-8') as f:
        ports = json.load(f)
    # Merge enhanced data if available
    _load_enhanced_port_index()
    if _enhanced_index:
        for port in ports:
            pid = port.get('port_id')
            enh = _enhanced_index.get(pid)
            if enh:
                # Merge enriched agents (services, certifications, cargo_types, operating_hours)
                if 'agents' in enh:
                    port['agents'] = enh['agents']
                # Merge logistics_network if present
                if 'logistics_network' in enh:
                    port['logistics_network'] = enh['logistics_network']
    _ports_cache = ports
    return _ports_cache
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
