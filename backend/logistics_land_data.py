"""
Logistique Terrestre - Gestion des corridors routiers et ferroviaires africains
Charge et expose les données des corridors terrestres, nœuds logistiques et opérateurs
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path

# Data file paths
_BASE = os.path.join(os.path.dirname(__file__), '..', 'data', 'json')
DATA_FILE = os.path.join(_BASE, 'corridors_terrestres.json')
ENHANCED_FILE = os.path.join(_BASE, 'corridors_terrestres_enhanced_logistics.json')

# Cache global
_corridors_data = None

def load_corridors_data():
    """Charge les données des corridors, en fusionnant les données enrichies si disponibles."""
    global _corridors_data
    if _corridors_data is None:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                corridors = data.get('corridors', [])

            # Merge enhanced logistics_network data when available
            try:
                with open(ENHANCED_FILE, 'r', encoding='utf-8') as f:
                    enh_data = json.load(f)
                enh_index = {c['corridor_id']: c for c in enh_data.get('enhanced_corridors', []) if 'corridor_id' in c}
                for corridor in corridors:
                    cid = corridor.get('corridor_id')
                    enh = enh_index.get(cid)
                    if enh and 'logistics_network' in enh:
                        corridor['logistics_network'] = enh['logistics_network']
            except Exception:
                pass  # Enhanced file optional

            _corridors_data = corridors
            print(f"✅ Loaded {len(_corridors_data)} land corridors")
        except FileNotFoundError:
            print(f"❌ File not found: {DATA_FILE}")
            _corridors_data = []
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            _corridors_data = []
    return _corridors_data

def get_all_corridors(corridor_type: Optional[str] = None, importance: Optional[str] = None) -> List[Dict]:
    """
    Récupère tous les corridors avec filtres optionnels
    
    Args:
        corridor_type: 'road', 'rail', 'multimodal' (optionnel)
        importance: 'high', 'medium' (optionnel)
    
    Returns:
        Liste des corridors filtrés
    """
    corridors = load_corridors_data()
    
    if corridor_type:
        corridors = [c for c in corridors if c.get('corridor_type') == corridor_type]
    
    if importance:
        corridors = [c for c in corridors if c.get('importance') == importance]
    
    return corridors

def get_corridor_by_id(corridor_id: str) -> Optional[Dict]:
    """Récupère un corridor par son ID"""
    corridors = load_corridors_data()
    for corridor in corridors:
        if corridor.get('corridor_id') == corridor_id:
            return corridor
    return None

def get_corridors_by_country(country_iso: str) -> List[Dict]:
    """Récupère tous les corridors passant par un pays donné"""
    corridors = load_corridors_data()
    return [
        c for c in corridors 
        if country_iso in c.get('countries_spanned', [])
    ]

def get_all_nodes() -> List[Dict]:
    """Récupère tous les nœuds logistiques de tous les corridors"""
    corridors = load_corridors_data()
    all_nodes = []
    
    for corridor in corridors:
        nodes = corridor.get('nodes', [])
        for node in nodes:
            node_with_corridor = node.copy()
            node_with_corridor['corridor_id'] = corridor.get('corridor_id')
            node_with_corridor['corridor_name'] = corridor.get('corridor_name')
            all_nodes.append(node_with_corridor)
    
    return all_nodes

def get_nodes_by_type(node_type: str) -> List[Dict]:
    """
    Récupère les nœuds par type
    Types: 'border_crossing', 'dry_port', 'rail_terminal', 'intermodal_hub'
    """
    all_nodes = get_all_nodes()
    return [n for n in all_nodes if n.get('node_type') == node_type]

def get_osbp_nodes() -> List[Dict]:
    """Récupère tous les postes-frontières OSBP (One-Stop Border Post)"""
    all_nodes = get_all_nodes()
    return [n for n in all_nodes if n.get('is_osbp') == True]

def get_all_operators() -> List[Dict]:
    """Récupère tous les opérateurs de tous les corridors"""
    corridors = load_corridors_data()
    all_operators = []
    
    for corridor in corridors:
        operators = corridor.get('operators', [])
        for operator in operators:
            operator_with_corridor = operator.copy()
            operator_with_corridor['corridor_id'] = corridor.get('corridor_id')
            operator_with_corridor['corridor_name'] = corridor.get('corridor_name')
            all_operators.append(operator_with_corridor)
    
    return all_operators

def get_operators_by_type(operator_type: str) -> List[Dict]:
    """
    Récupère les opérateurs par type
    Types: 'rail_operator', 'trucking_company'
    """
    all_operators = get_all_operators()
    return [o for o in all_operators if o.get('operator_type') == operator_type]

def get_corridors_statistics() -> Dict:
    """Calcule des statistiques globales sur les corridors"""
    corridors = load_corridors_data()
    
    total_length = sum(c.get('length_km', 0) for c in corridors)
    total_freight = sum(c.get('stats', {}).get('freight_throughput_tons', 0) for c in corridors if c.get('stats'))
    
    by_type = {}
    for corridor in corridors:
        ctype = corridor.get('corridor_type', 'unknown')
        by_type[ctype] = by_type.get(ctype, 0) + 1
    
    by_status = {}
    for corridor in corridors:
        status = corridor.get('status', 'unknown')
        by_status[status] = by_status.get(status, 0) + 1
    
    all_nodes = get_all_nodes()
    osbp_count = len([n for n in all_nodes if n.get('is_osbp')])
    
    all_operators = get_all_operators()
    rail_operators = len([o for o in all_operators if o.get('operator_type') == 'rail_operator'])
    trucking_companies = len([o for o in all_operators if o.get('operator_type') == 'trucking_company'])
    
    return {
        'total_corridors': len(corridors),
        'total_length_km': total_length,
        'total_freight_throughput_tons': total_freight,
        'corridors_by_type': by_type,
        'corridors_by_status': by_status,
        'total_nodes': len(all_nodes),
        'osbp_count': osbp_count,
        'total_operators': len(all_operators),
        'rail_operators_count': rail_operators,
        'trucking_companies_count': trucking_companies
    }

def search_corridors(query: str) -> List[Dict]:
    """Recherche de corridors par nom ou pays"""
    corridors = load_corridors_data()
    query_lower = query.lower()
    
    results = []
    for corridor in corridors:
        # Search in corridor name
        if query_lower in corridor.get('corridor_name', '').lower():
            results.append(corridor)
            continue
        
        # Search in countries
        for country in corridor.get('countries_spanned', []):
            if query_lower in country.lower():
                results.append(corridor)
                break
        
        # Search in description
        if query_lower in corridor.get('description', '').lower():
            results.append(corridor)
    
    return results

# Initialize data on module import
load_corridors_data()
