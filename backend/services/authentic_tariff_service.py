import json
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_tariff_cache = {}
_nomenclature_cache = {}

def load_country_tariffs(country_iso3):
    global _tariff_cache
    if country_iso3 in _tariff_cache: return _tariff_cache[country_iso3]
    file_path = os.path.join(DATA_DIR, f'{country_iso3}_tariffs.json')
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
        _tariff_cache[country_iso3] = data
        return data
    except Exception as e:
        logger.error(f'Error loading tariffs for {country_iso3}: {e}')
        return None

def load_nomenclature_map(country_iso3):
    """Load nomenclature map for countries with extended sub-positions (like DZA)"""
    global _nomenclature_cache
    if country_iso3 in _nomenclature_cache:
        return _nomenclature_cache[country_iso3]
    
    file_path = os.path.join(DATA_DIR, f'{country_iso3}_nomenclature_map.json')
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _nomenclature_cache[country_iso3] = data
        logger.info(f'Loaded nomenclature map for {country_iso3}: {len(data)} entries')
        return data
    except Exception as e:
        logger.error(f'Error loading nomenclature map for {country_iso3}: {e}')
        return None

def get_tariff_line(country_iso3, hs_code):
    data = load_country_tariffs(country_iso3)
    if not data: return None
    hss = hs_code[:6]
    for line in data.get('tariff_lines', []):
        if line.get('hs6') == hss or line.get('code') == hs_code:
            return line
    return None

def get_sub_positions(country_iso3, hs6):
    """
    Get sub-positions for a given HS6 code.
    For countries with nomenclature_map (like DZA), use that to generate sub-positions.
    """
    # First try to get from tariff_lines
    line = get_tariff_line(country_iso3, hs6)
    if line and line.get('sub_positions'):
        return line.get('sub_positions', [])
    
    # For DZA and other countries with nomenclature_map, generate from map
    nomenclature = load_nomenclature_map(country_iso3)
    if nomenclature:
        sub_positions = []
        hs6_normalized = hs6[:6]
        
        # Find all codes that start with this HS6
        for code, description in nomenclature.items():
            if code.startswith(hs6_normalized) and len(code) > 6:
                sub_positions.append({
                    'code': code,
                    'national_code': code,
                    'description': description,
                    'denomination': description,
                    'dd_rate': 0.0,  # Default, would need to be looked up from actual tariff data
                    'source': 'nomenclature_map'
                })
        
        # Sort by code
        sub_positions.sort(key=lambda x: x['code'])
        logger.info(f'Found {len(sub_positions)} sub-positions for {country_iso3}/{hs6} from nomenclature')
        return sub_positions
    
    return []

def get_taxes_detail(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get('taxes', {}) if line else {}

def get_fiscal_advantages(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get('fiscal_advantages', []) if line else []

def get_administrative_formalities(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get('administrative_formalities', []) if line else []

def search_tariff_lines(country_iso3, query, language='fr', limit=20):
    data = load_country_tariffs(country_iso3)
    results = []
    if not data: return []
    q = query.lower()
    for line in data.get('tariff_lines', []):
        desc = line.get('designation', '')
        if q in desc.lower():
            results.append(line)
        if len(results) >= limit: break
    return results

def get_country_summary(country_iso3):
    data = load_country_tariffs(country_iso3)
    if not data: return None
    return {'total_lines': len(data.get('tariff_lines', []))}

def calculate_import_taxes(country_iso3, hs_code, cif_value, apply_zlecaf=False, language='fr'):
    line = get_tariff_line(country_iso3, hs_code)
    if not line: return {'error': 'Not Found'}
    return {'hs_code': hs_code, 'total_taxes': 0}

def get_available_countries():
    return [{'iso3': 'DZA', 'name': 'Algerie'}]
