import json
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_tariff_cache = {}

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

def get_tariff_line(country_iso3, hs_code):
    data = load_country_tariffs(country_iso3)
    if not data: return None
    hss = hs_code[:6]
    for line in data.get('tariff_lines', []):
        if line.get('hs6') == hss or line.get('code') == hs_code:
            return line
    return None

def get_sub_positions(country_iso3, hs6):
    line = get_tariff_line(country_iso3, hs6)
    return line.get('sub_positions', []) if line else []

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
