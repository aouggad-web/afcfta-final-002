import json
import os
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Base directory for tariff data files
# Note: This is relative to the backend/ directory
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
        logger.warning(f"Tariff file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        _tariff_cache[country_iso3] = data
        logger.info(f"Loaded tariffs for {country_iso3}")
        return data
    except Exception as e:
        logger.error(f"Error loading tariffs for {country_iso3}: {e}")
        return None

def get_available_countries() -> List[Dict[str, Any]]:
    """Get list of countries with authentic tariff data."""
    countries = []
    
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Tariff data directory not found: {DATA_DIR}")
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
                    'total_sub_positions': summary.get('total_sub_positions', 0),
                    'total_positions': summary.get('total_positions', 0),
                    'vat_rate': summary.get('vat_rate_pct', 0),
                    'vat_source': summary.get('vat_source', ''),
                    'dd_range': summary.get('dd_rate_range', {}),
                    'chapters_covered': summary.get('chapters_covered', 0),
                    'has_detailed_taxes': summary.get('has_detailed_taxes', False),
                    'data_format': data.get('data_format', 'unknown'),
                    'generated_at': data.get('generated_at', '')
                })
    
    countries.sort(key=lambda x: x['iso3'])
    return countries

def get_tariff_line(country_iso3: str, hs_code: str) -> Optional[Dict]:
    """Get tariff line for a specific HS code."""
    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    
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

def get_sub_positions(country_iso3: str, hs6: str) -> List[Dict]:
    """Get all sub-positions for an HS6 code."""
    tariff_line = get_tariff_line(country_iso3, hs6)
    if not tariff_line:
        return []
    
    return tariff_line.get('sub_positions', [])

def get_taxes_detail(country_iso3: str, hs_code: str) -> List[Dict]:
    """Get detailed tax breakdown for an HS code."""
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line:
        return []
    
    return tariff_line.get('taxes_detail', [])

def get_fiscal_advantages(country_iso3: str, hs_code: str) -> List[Dict]:
    """Get fiscal advantages for an HS code."""
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line:
        return []
    
    return tariff_line.get('fiscal_advantages', [])

def get_administrative_formalities(country_iso3: str, hs_code: str) -> List[Dict]:
    """Get required administrative formalities for an HS code."""
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line:
        return []
    
    return tariff_line.get('administrative_formalities', [])

def calculate_import_taxes(
    country_iso3: str, 
    hs_code: str, 
    cif_value: float,
    apply_zlecaf: bool = False,
    language: str = 'fr'
) -> Dict[str, Any]:
    """
    Calculates detailed import taxes using the official methodology.
    Includes special cascade logic for Algeria (DZA).
    """
    tariff_line = get_tariff_line(country_iso3, hs_code)
    
    if not tariff_line:
        return {
            'error': f'No tariff data found for {country_iso3}/{hs_code}',
            'hs_code': hs_code,
            'country': country_iso3
        }
    
    # 1. Base Values
    exchange_rate = 135.0  # Default USD/DZD estimate for calculation
    base_usd = cif_value
    base_local = cif_value * (exchange_rate if country_iso3 == 'DZA' else 1.0)
    currency = 'DZD' if country_iso3 == 'DZA' else 'USD'
    
    dd_rate = tariff_line.get('dd_rate', tariff_line.get('dd', 0)) / 100
    vat_rate = tariff_line.get('vat_rate', 19 if country_iso3 == 'DZA' else 15) / 100
    
    # Specific taxes for Algeria
    tcs_rate = 0.03 if country_iso3 == 'DZA' else 0.0
    prct_rate = 0.02 if country_iso3 == 'DZA' else 0.0
    daps_rate = tariff_line.get('daps_rate', 0) / 100
    
    # --- NPF (Normal) Calculation ---
    # Droits de Douane (DD)
    dd_amount_npf = base_local * dd_rate
    
    # Taxes on Customs Value only (Algeria PRCT & TCS)
    tcs_amount_npf = base_local * tcs_rate
    prct_amount_npf = base_local * prct_rate
    daps_amount_npf = base_local * daps_rate
    
    # VAT Cascade (Base = CAF + DD + TCS + PRCT + DAPS)
    vat_base_npf = base_local + dd_amount_npf + tcs_amount_npf + prct_amount_npf + daps_amount_npf
    vat_amount_npf = vat_base_npf * vat_rate
    
    fixed_fees = 3500 if country_iso3 == 'DZA' else 0
    total_taxes_npf = dd_amount_npf + tcs_amount_npf + prct_amount_npf + daps_amount_npf + vat_amount_npf + fixed_fees
    
    # --- AfCFTA Calculation ---
    dd_amount_zlecaf = 0  # Preferential rate
    tcs_amount_zlecaf = base_local * tcs_rate
    prct_amount_zlecaf = base_local * prct_rate
    daps_amount_zlecaf = base_local * daps_rate
    
    vat_base_zlecaf = base_local + dd_amount_zlecaf + tcs_amount_zlecaf + prct_amount_zlecaf + daps_amount_zlecaf
    vat_amount_zlecaf = vat_base_zlecaf * vat_rate
    
    total_taxes_zlecaf = dd_amount_zlecaf + tcs_amount_zlecaf + prct_amount_zlecaf + daps_amount_zlecaf + vat_amount_zlecaf + fixed_fees
    
    # Savings
    savings = total_taxes_npf - total_taxes_zlecaf
    savings_pct = (savings / total_taxes_npf * 100) if total_taxes_npf > 0 else 0
    
    return {
        'hs_code': hs_code,
        'description': tariff_line.get(f'description_{language}', tariff_line.get('description_fr', '')),
        'country_iso3': country_iso3,
        'cif_value_usd': base_usd,
        'base_value_local': base_local,
        'currency': currency,
        'npf_calculation': {
            'dd': dd_amount_npf,
            'tcs': tcs_amount_npf,
            'prct': prct_amount_npf,
            'daps': daps_amount_npf,
            'vat': vat_amount_npf,
            'fixed_fees': fixed_fees,
            'total_taxes': total_taxes_npf
        },
        'zlecaf_calculation': {
            'dd': dd_amount_zlecaf,
            'tcs': tcs_amount_zlecaf,
            'prct': prct_amount_zlecaf,
            'daps': daps_amount_zlecaf,
            'vat': vat_amount_zlecaf,
            'fixed_fees': fixed_fees,
            'total_taxes': total_taxes_zlecaf
        },
        'savings': {
            'amount': savings,
            'percentage': round(savings_pct, 2)
        },
        'methodology': 'Algerian Official Cascade (DZD)' if country_iso3 == 'DZA' else 'Standard NPF/AfCFTA Comparison'
    }

def search_tariff_lines(
    country_iso3: str, 
    query: str, 
    language: str = 'fr',
    limit: int = 20
) -> List[Dict]:
    """Search tariff lines by description or HS code."""
    data = load_country_tariffs(country_iso3)
    if not data:
        return []
    
    query_lower = query.lower()
    results = []
    
    desc_key = f'description_{language}'
    
    for line in data['tariff_lines']:
        if line['hs6'].startswith(query):
            results.append(line)
            continue
        
        desc = line.get(desc_key, line.get('description_fr', '')).lower()
        if query_lower in desc:
            results.append(line)
        
        if len(results) >= limit:
            break
    
    return results

def get_country_summary(country_iso3: str) -> Optional[Dict]:
    """Get summary statistics for a country's tariff data."""
    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    
    return data['summary']

def init_tariff_data():
    """Initialize and preload tariff data."""
    countries = get_available_countries()
    return countries
