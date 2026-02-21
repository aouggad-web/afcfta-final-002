"""
Authentic Tariff Data Service
Loads and provides access to real tariff data from African countries
Data format: enhanced_v2 (HS6 with sub-positions, taxes, advantages, formalities)
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Base directory for tariff data files
TARIFF_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Cache for loaded tariff data
_tariff_cache: Dict[str, Dict] = {}


def load_country_tariffs(country_iso3: str) -> Optional[Dict]:
    """
    Load tariff data for a specific country
    
    Args:
        country_iso3: ISO3 country code (e.g., 'DZA', 'ETH')
    
    Returns:
        Complete tariff data dictionary or None if not found
    """
    global _tariff_cache
    
    # Check cache first
    if country_iso3 in _tariff_cache:
        return _tariff_cache[country_iso3]
    
    # Try to load from file
    file_path = os.path.join(TARIFF_DATA_DIR, f'{country_iso3}_tariffs.json')
    
    if not os.path.exists(file_path):
        logger.warning(f"Tariff file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Cache the data
        _tariff_cache[country_iso3] = data
        logger.info(f"Loaded tariffs for {country_iso3}: {data['summary']['total_tariff_lines']} lines")
        
        return data
    except Exception as e:
        logger.error(f"Error loading tariffs for {country_iso3}: {e}")
        return None


def get_available_countries() -> List[Dict[str, Any]]:
    """
    Get list of countries with authentic tariff data
    
    Returns:
        List of country info dictionaries
    """
    countries = []
    
    if not os.path.exists(TARIFF_DATA_DIR):
        logger.warning(f"Tariff data directory not found: {TARIFF_DATA_DIR}")
        return countries
    
    for filename in os.listdir(TARIFF_DATA_DIR):
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
    
    # Sort by ISO3 code
    countries.sort(key=lambda x: x['iso3'])
    
    return countries


def get_tariff_line(country_iso3: str, hs_code: str) -> Optional[Dict]:
    """
    Get tariff line for a specific HS code
    
    Args:
        country_iso3: ISO3 country code
        hs_code: HS code (6-12 digits)
    
    Returns:
        Tariff line data or None
    """
    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    
    hs6 = hs_code[:6]
    
    # Build index if not exists
    if '_hs6_index' not in data:
        data['_hs6_index'] = {line['hs6']: line for line in data['tariff_lines']}
    
    tariff_line = data['_hs6_index'].get(hs6)
    
    if tariff_line and len(hs_code) > 6:
        # Try to find specific sub-position rate
        sub_positions = tariff_line.get('sub_positions', [])
        for sp in sub_positions:
            if sp['code'] == hs_code or sp['code'].startswith(hs_code):
                # Return tariff line with sub-position specific DD rate
                result = dict(tariff_line)
                result['matched_sub_position'] = sp
                result['dd_rate'] = sp['dd']
                return result
    
    return tariff_line


def get_sub_positions(country_iso3: str, hs6: str) -> List[Dict]:
    """
    Get all sub-positions for an HS6 code
    
    Args:
        country_iso3: ISO3 country code
        hs6: 6-digit HS code
    
    Returns:
        List of sub-positions with their rates
    """
    tariff_line = get_tariff_line(country_iso3, hs6)
    if not tariff_line:
        return []
    
    return tariff_line.get('sub_positions', [])


def get_taxes_detail(country_iso3: str, hs_code: str) -> List[Dict]:
    """
    Get detailed tax breakdown for an HS code
    
    Args:
        country_iso3: ISO3 country code
        hs_code: HS code
    
    Returns:
        List of tax components with rates
    """
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line:
        return []
    
    return tariff_line.get('taxes_detail', [])


def get_fiscal_advantages(country_iso3: str, hs_code: str) -> List[Dict]:
    """
    Get fiscal advantages (including ZLECAf exemptions) for an HS code
    
    Args:
        country_iso3: ISO3 country code
        hs_code: HS code
    
    Returns:
        List of fiscal advantages
    """
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line:
        return []
    
    return tariff_line.get('fiscal_advantages', [])


def get_administrative_formalities(country_iso3: str, hs_code: str) -> List[Dict]:
    """
    Get required administrative formalities for an HS code
    
    Args:
        country_iso3: ISO3 country code
        hs_code: HS code
    
    Returns:
        List of required documents/formalities
    """
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
    Calculate detailed import taxes for a product
    
    Args:
        country_iso3: ISO3 country code
        hs_code: HS code (6-12 digits)
        cif_value: CIF value in USD
        apply_zlecaf: Whether to apply ZLECAf preferential rates
        language: Language for descriptions ('fr' or 'en')
    
    Returns:
        Detailed tax calculation breakdown
    """
    tariff_line = get_tariff_line(country_iso3, hs_code)
    
    if not tariff_line:
        return {
            'error': f'No tariff data found for {country_iso3}/{hs_code}',
            'hs_code': hs_code,
            'country': country_iso3
        }
    
    # Get description
    desc_key = f'description_{language}'
    description = tariff_line.get(desc_key, tariff_line.get('description_fr', ''))
    
    # Get tax rates
    dd_rate = tariff_line['dd_rate'] / 100  # Convert to decimal
    vat_rate = tariff_line.get('vat_rate', 19) / 100
    other_taxes_rate = tariff_line.get('other_taxes_rate', 0) / 100
    
    # Check for sub-position specific rate
    sub_pos_info = None
    if 'matched_sub_position' in tariff_line:
        sub_pos_info = tariff_line['matched_sub_position']
    
    # Get detailed taxes
    taxes_detail = tariff_line.get('taxes_detail', [])
    
    # Apply ZLECAf exemptions if requested
    zlecaf_dd_rate = 0  # DD is exempt under ZLECAf
    fiscal_advantages = tariff_line.get('fiscal_advantages', [])
    
    # Calculate NPF (Normal) regime
    dd_amount = round(cif_value * dd_rate, 2)
    vat_base_npf = cif_value + dd_amount
    vat_amount_npf = round(vat_base_npf * vat_rate, 2)
    other_taxes_npf = round(cif_value * other_taxes_rate, 2)
    total_npf = round(cif_value + dd_amount + vat_amount_npf + other_taxes_npf, 2)
    
    # Calculate ZLECAf regime
    dd_amount_zlecaf = 0  # Exempt
    vat_base_zlecaf = cif_value  # VAT on CIF only (no DD)
    vat_amount_zlecaf = round(vat_base_zlecaf * vat_rate, 2)
    other_taxes_zlecaf = round(cif_value * other_taxes_rate, 2)
    total_zlecaf = round(cif_value + dd_amount_zlecaf + vat_amount_zlecaf + other_taxes_zlecaf, 2)
    
    # Savings
    savings = round(total_npf - total_zlecaf, 2)
    savings_pct = round((savings / total_npf) * 100, 1) if total_npf > 0 else 0
    
    # Build response
    result = {
        'hs_code': hs_code,
        'hs6': hs_code[:6],
        'description': description,
        'country_iso3': country_iso3,
        'cif_value': cif_value,
        'currency': 'USD',
        'data_source': 'authentic_tariff',
        
        # Rates
        'rates': {
            'dd_rate_pct': tariff_line['dd_rate'],
            'vat_rate_pct': tariff_line.get('vat_rate', 19),
            'other_taxes_pct': tariff_line.get('other_taxes_rate', 0),
            'total_rate_pct': tariff_line.get('total_taxes_pct', 0)
        },
        
        # NPF Calculation
        'npf_calculation': {
            'regime': 'NPF',
            'cif_value': cif_value,
            'dd': {'rate_pct': tariff_line['dd_rate'], 'amount': dd_amount},
            'vat': {'rate_pct': tariff_line.get('vat_rate', 19), 'base': vat_base_npf, 'amount': vat_amount_npf},
            'other_taxes': {'rate_pct': tariff_line.get('other_taxes_rate', 0), 'amount': other_taxes_npf},
            'total_taxes': round(dd_amount + vat_amount_npf + other_taxes_npf, 2),
            'total_to_pay': total_npf
        },
        
        # ZLECAf Calculation
        'zlecaf_calculation': {
            'regime': 'ZLECAf',
            'cif_value': cif_value,
            'dd': {'rate_pct': 0, 'amount': dd_amount_zlecaf, 'exempt': True},
            'vat': {'rate_pct': tariff_line.get('vat_rate', 19), 'base': vat_base_zlecaf, 'amount': vat_amount_zlecaf},
            'other_taxes': {'rate_pct': tariff_line.get('other_taxes_rate', 0), 'amount': other_taxes_zlecaf},
            'total_taxes': round(dd_amount_zlecaf + vat_amount_zlecaf + other_taxes_zlecaf, 2),
            'total_to_pay': total_zlecaf
        },
        
        # Savings
        'savings': {
            'amount': savings,
            'percentage': savings_pct
        },
        
        # Detailed tax breakdown
        'taxes_detail': taxes_detail,
        
        # Fiscal advantages
        'fiscal_advantages': fiscal_advantages,
        
        # Administrative formalities
        'administrative_formalities': tariff_line.get('administrative_formalities', []),
        
        # Sub-position info
        'sub_position': sub_pos_info,
        'has_sub_positions': tariff_line.get('has_sub_positions', False),
        'sub_position_count': tariff_line.get('sub_position_count', 0)
    }
    
    return result


def search_tariff_lines(
    country_iso3: str, 
    query: str, 
    language: str = 'fr',
    limit: int = 20
) -> List[Dict]:
    """
    Search tariff lines by description or HS code
    
    Args:
        country_iso3: ISO3 country code
        query: Search query (description or HS code)
        language: Language for descriptions
        limit: Maximum results
    
    Returns:
        List of matching tariff lines
    """
    data = load_country_tariffs(country_iso3)
    if not data:
        return []
    
    query_lower = query.lower()
    results = []
    
    desc_key = f'description_{language}'
    
    for line in data['tariff_lines']:
        # Match by HS code
        if line['hs6'].startswith(query):
            results.append(line)
            continue
        
        # Match by description
        desc = line.get(desc_key, line.get('description_fr', '')).lower()
        if query_lower in desc:
            results.append(line)
        
        if len(results) >= limit:
            break
    
    return results


def get_country_summary(country_iso3: str) -> Optional[Dict]:
    """
    Get summary statistics for a country's tariff data
    
    Args:
        country_iso3: ISO3 country code
    
    Returns:
        Summary dictionary or None
    """
    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    
    return data['summary']


# Initialize - preload available country data
def init_tariff_data():
    """Initialize and preload tariff data"""
    countries = get_available_countries()
    logger.info(f"Initialized authentic tariff data for {len(countries)} countries: {[c['iso3'] for c in countries]}")
    return countries
