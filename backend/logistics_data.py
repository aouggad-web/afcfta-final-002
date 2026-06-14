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


# Region mapping for the 54 African countries (ISO3 → region label).
# Used to group ports/airports by region in the UI (Afrique du Nord, de l'Ouest, etc.).
REGION_BY_ISO = {
    # Afrique du Nord
    "DZA": "Afrique du Nord", "EGY": "Afrique du Nord", "LBY": "Afrique du Nord",
    "MAR": "Afrique du Nord", "TUN": "Afrique du Nord", "SDN": "Afrique du Nord",
    "ESH": "Afrique du Nord", "MRT": "Afrique du Nord",
    # Afrique de l'Ouest
    "BEN": "Afrique de l'Ouest", "BFA": "Afrique de l'Ouest", "CIV": "Afrique de l'Ouest",
    "CPV": "Afrique de l'Ouest", "GMB": "Afrique de l'Ouest", "GHA": "Afrique de l'Ouest",
    "GIN": "Afrique de l'Ouest", "GNB": "Afrique de l'Ouest", "LBR": "Afrique de l'Ouest",
    "MLI": "Afrique de l'Ouest", "NER": "Afrique de l'Ouest", "NGA": "Afrique de l'Ouest",
    "SEN": "Afrique de l'Ouest", "SLE": "Afrique de l'Ouest", "TGO": "Afrique de l'Ouest",
    # Afrique Centrale
    "AGO": "Afrique Centrale", "CMR": "Afrique Centrale", "CAF": "Afrique Centrale",
    "TCD": "Afrique Centrale", "COG": "Afrique Centrale", "COD": "Afrique Centrale",
    "GNQ": "Afrique Centrale", "GAB": "Afrique Centrale", "STP": "Afrique Centrale",
    # Afrique de l'Est
    "BDI": "Afrique de l'Est", "COM": "Afrique de l'Est", "DJI": "Afrique de l'Est",
    "ERI": "Afrique de l'Est", "ETH": "Afrique de l'Est", "KEN": "Afrique de l'Est",
    "MDG": "Afrique de l'Est", "MWI": "Afrique de l'Est", "MUS": "Afrique de l'Est",
    "MOZ": "Afrique de l'Est", "RWA": "Afrique de l'Est", "SYC": "Afrique de l'Est",
    "SOM": "Afrique de l'Est", "SSD": "Afrique de l'Est", "TZA": "Afrique de l'Est",
    "UGA": "Afrique de l'Est", "ZMB": "Afrique de l'Est", "ZWE": "Afrique de l'Est",
    # Afrique Australe
    "BWA": "Afrique Australe", "ZAF": "Afrique Australe", "LSO": "Afrique Australe",
    "NAM": "Afrique Australe", "SWZ": "Afrique Australe",
}


def _enrich_port(port: dict) -> dict:
    """Annotate a port dict with derived fields (region) for the UI."""
    iso = (port.get("country_iso") or "").upper()
    if iso and not port.get("region"):
        port["region"] = REGION_BY_ISO.get(iso, "Autre")
    return port


def load_ports_data():
    """Load African ports data from JSON file"""
    ports_path = ROOT_DIR / "data" / "json" / "ports_africains.json"
    with open(ports_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_ports(country_iso: Optional[str] = None) -> List[dict]:
    """
    Get all ports or filter by country ISO code
    """
    ports = load_ports_data()
    if country_iso:
        country_iso = country_iso.upper()
        ports = [p for p in ports if p['country_iso'] == country_iso]
    return [_enrich_port(p) for p in ports]

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
