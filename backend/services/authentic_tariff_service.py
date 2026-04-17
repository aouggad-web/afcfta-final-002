import json
import os
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Base directory for tariff data files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Cache for loaded tariff data
_tariff_cache: Dict[str, Dict] = {}

def load_country_tariffs(country_iso3: str) -> Optional[Dict]:
    """Load tariff data for a specific country."""
    global _tariff_cache
    if country_iso3 in _tariff_cache:
        return _tariff_cache[country_iso3]
    file_path = os.path.join(DATA_DIR, f'{country_iso3}_tariffs.json')
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _tariff_cache[country_iso3] = data
        return data
    except Exception as e:
        logger.error(f"Error loading tariffs for {country_iso3}: {e}")
        return None

def get_available_countries() -> List[Dict[str, Any]]:
    """Get list of countries with authentic tariff data."""
    countries = []
    if not os.path.exists(DATA_DIR):
        return countries
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('_tariffs.json'):
            iso3 = filename.replace('_tariffs.json', '')
            data = load_country_tariffs(iso3)
            if data:
                summary = data.get('summary', {})
                countries.append({
                    'iso3': iso3,
                    'country_code': data.get('country_code', iso3),
                    'total_lines': summary.get('total_tariff_lines', 0),
                    'vat_rate': summary.get('vat_rate_pct', 0)
                })
    countries.sort(key=lambda x: x['iso3'])
    return countries

def get_tariff_line(country_iso3: str, hs_code: str) -> Optional[Dict]:
    data = load_country_tariffs(country_iso3)
    if not data: return None
    hs6 = hs_code[:6]
    if '_hs6_index' not in data:
        data['_hs6_index'] = {line['hs6']: line for line in data['tariff_lines']}
    tariff_line = data['_hs6_index'].get(hs6)
    if tariff_line and len(hs_code) > 6:
        sub_positions = tariff_line.get('sub_positions', [])
        for sp in sub_positions:
            if sp['code'] == hs_code or sp['code'].startswith(hs_code):
                result = dict(tariff_line)
                result['matched_sub_position'] = sp
                result['dd_rate'] = sp['dd']
                return result
    return tariff_line

def calculate_import_taxes(
    country_iso3: str, 
    hs_code: str, 
    cif_value: float,
    apply_zlecaf: bool = False,
    language: str = 'fr'
) -> Dict[str, Any]:
    """
    Calculates detailed import taxes using country-specific methodologies.
    Supports Algerian (DZA), Tunisian (TUN), and Moroccan (MAR) cascade logic.
    """
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line: return {'error': 'Data not found'}
    
    # 1. Exchange Rates & Base
    exchange_rates = {'DZA': 135.0, 'TUN': 3.10, 'MAR': 10.0}
    rate = exchange_rates.get(country_iso3, 1.0)
    base_local = cif_value * rate
    
    # 2. Extract Rates
    dd_rate = tariff_line.get('dd_rate', tariff_line.get('dd', 0)) / 100
    vat_rate = tariff_line.get('vat_rate', 20 if country_iso3 == 'MAR' else 19) / 100
    
    # --- CALCULATION LOGIC ---
    if country_iso3 == 'MAR':
        # MOROCCAN CASCADE (ADII)
        di_amt = base_local * dd_rate  # Droit d'Importation
        tpi_amt = base_local * 0.0025  # Taxe Parafiscale (0.25%)
        tva_base = base_local + di_amt + tpi_amt
        tva_amt = tva_base * vat_rate
        total_taxes = di_amt + tpi_amt + tva_amt
        methodology = "Moroccan Official Cascade (ADII)"
        currency = 'MAD'

    elif country_iso3 == 'TUN':
        # TUNISIAN CASCADE (2026)
        dc_rate = tariff_line.get('dc_rate', 0) / 100
        dd_amt = base_local * dd_rate
        dc_amt = (base_local + dd_amt) * dc_rate
        rpd_amt = (dd_amt + dc_amt) * 0.03
        tva_base = base_local + dd_amt + dc_amt + rpd_amt
        tva_amt = tva_base * vat_rate
        air_base = tva_base + tva_amt
        air_amt = air_base * 0.10
        total_taxes = dd_amt + dc_amt + rpd_amt + tva_amt + air_amt
        methodology = "Tunisian Cascade (RPD + AIR)"
        currency = 'TND'
    
    elif country_iso3 == 'DZA':
        # ALGERIAN CASCADE
        dd_amt = base_local * dd_rate
        tcs_amt = base_local * 0.03
        prct_amt = base_local * 0.02
        tva_base = base_local + dd_amt + tcs_amt + prct_amt
        tva_amt = tva_base * vat_rate
        total_taxes = dd_amt + tcs_amt + prct_amt + tva_amt + 3500
        methodology = "Algerian Official Cascade"
        currency = 'DZD'
    
    else:
        # STANDARD REGIME
        dd_amt = base_local * dd_rate
        tva_amt = (base_local + dd_amt) * vat_rate
        total_taxes = dd_amt + tva_amt
        methodology = "Standard Comparison"
        currency = 'USD'

    return {
        'hs_code': hs_code,
        'country': country_iso3,
        'total_taxes': round(total_taxes, 2),
        'methodology': methodology,
        'currency': currency,
        'base_value_local': round(base_local, 2)
    }
