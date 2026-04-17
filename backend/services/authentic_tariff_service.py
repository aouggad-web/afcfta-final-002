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
    if country_iso3 in _tariff_cache: return _tariff_cache[country_iso3]
    file_path = os.path.join(DATA_DIR, f'{country_iso3}_tariffs.json')
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
        _tariff_cache[country_iso3] = data
        return data
    except Exception as e:
        logger.error(f"Error loading tariffs for {country_iso3}: {e}")
        return None

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
    Calculates detailed import taxes using the Unified African Cascade Method.
    
    Step 1: Customs Duties (DD) on CIF Value
    Step 2: Parafiscal Taxes on CIF Value
    Step 3: VAT (TVA) on (CIF + DD + Parafiscal)
    Step 4: Advance Tax on (CIF) or (Total TTC) - country dependent
    """
    tariff_line = get_tariff_line(country_iso3, hs_code)
    if not tariff_line: return {'error': 'Tariff line not found'}

    # Setup country parameters
    exchange_rates = {'DZA': 135.0, 'TUN': 3.10, 'MAR': 10.0}
    rate = exchange_rates.get(country_iso3, 1.0)
    base_caf = cif_value * rate
    
    dd_rate = (tariff_line.get('dd_rate', tariff_line.get('dd', 0))) / 100
    tva_rate = 0.19 # Default
    if country_iso3 == 'MAR': tva_rate = 0.20
    elif country_iso3 == 'TUN': tva_rate = 0.19

    # --- THE CASCADE ---
    
    # 1. Droits de Douane (Base: CAF)
    dd_amount = base_caf * dd_rate
    
    # 2. Taxes Parafiscales (Base: CAF)
    # Algeria: TCS (3%) + PRCT (2%) | Morocco: TPI (0.25%) | Tunisia: RPD + DC
    parafiscal_amt = 0
    if country_iso3 == 'DZA':
        parafiscal_amt = base_caf * 0.05 # 3% TCS + 2% PRCT
    elif country_iso3 == 'MAR':
        parafiscal_amt = base_caf * 0.0025 # 0.25% TPI
    elif country_iso3 == 'TUN':
        # Special case: Tunisia DC is on (CAF + DD)
        dc_amt = (base_caf + dd_amount) * (tariff_line.get('dc_rate', 0) / 100)
        rpd_amt = (dd_amount + dc_amt) * 0.03
        parafiscal_amt = dc_amt + rpd_amt

    # 3. TVA (Base: CAF + DD + Parafiscal)
    tva_base = base_caf + dd_amount + parafiscal_amt
    tva_amount = tva_base * tva_rate
    
    # 4. Avance sur Impôt
    advance_tax_amt = 0
    if country_iso3 == 'TUN':
        # Tunisia AIR (10%) on Total TTC (CAF + DD + DC + RPD + TVA)
        advance_tax_amt = (tva_base + tva_amount) * 0.10
    elif country_iso3 == 'DZA':
        # Algeria PRCT is already in parafiscal (on CAF only)
        advance_tax_amt = 0 

    # Final Totals
    fixed_fees = 3500 if country_iso3 == 'DZA' else (2.0 if country_iso3 == 'TUN' else 0)
    total_to_pay = dd_amount + parafiscal_amt + tva_amount + advance_tax_amt + fixed_fees

    return {
        'hs_code': hs_code,
        'country': country_iso3,
        'currency': 'DZD' if country_iso3 == 'DZA' else ('TND' if country_iso3 == 'TUN' else 'MAD'),
        'calculation_cascade': {
            'step1_customs_duty': round(dd_amount, 2),
            'step2_parafiscal': round(parafiscal_amt, 2),
            'step3_tva': round(tva_amount, 2),
            'step4_advance_tax': round(advance_tax_amt, 2),
            'fixed_fees': fixed_fees
        },
        'total_to_pay': round(total_to_pay, 2),
        'methodology': 'Unified African Cascade (v2026)'
    }

def get_available_countries():
    return [{'iso3': 'DZA', 'name': 'Algérie'}, {'iso3': 'TUN', 'name': 'Tunisie'}, {'iso3': 'MAR', 'name': 'Maroc'}]
