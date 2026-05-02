import json
import os
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_tariff_cache = {}
_nomenclature_cache = {}
_available_countries_cache = None

# Only allow well-formed ISO 2- or 3-letter country codes to prevent path traversal.
_ISO_CODE_RE = re.compile(r'^[A-Z]{2,3}$')


def _validate_iso3(country_iso3: str) -> str:
    """Normalise to uppercase and reject codes that could traverse the filesystem."""
    code = country_iso3.upper().strip()
    if not _ISO_CODE_RE.match(code):
        raise ValueError(f'Invalid country code: {country_iso3!r}')
    return code

_COUNTRY_NAMES = {
    'DZA': 'Algérie', 'MAR': 'Maroc', 'TUN': 'Tunisie', 'EGY': 'Égypte',
    'LBY': 'Libye', 'NGA': 'Nigeria', 'ZAF': 'Afrique du Sud', 'KEN': 'Kenya',
    'ETH': 'Éthiopie', 'GHA': 'Ghana', 'CIV': "Côte d'Ivoire", 'SEN': 'Sénégal',
    'CMR': 'Cameroun', 'AGO': 'Angola', 'TZA': 'Tanzanie', 'UGA': 'Ouganda',
    'BWA': 'Botswana', 'BEN': 'Bénin', 'BFA': 'Burkina Faso', 'BDI': 'Burundi',
    'CPV': 'Cap-Vert', 'CAF': 'Centrafrique', 'COM': 'Comores', 'COG': 'Congo',
    'COD': 'RD Congo', 'DJI': 'Djibouti', 'ERI': 'Érythrée', 'GAB': 'Gabon',
    'GMB': 'Gambie', 'GIN': 'Guinée', 'GNB': 'Guinée-Bissau', 'GNQ': 'Guinée Équatoriale',
    'LBR': 'Libéria', 'LSO': 'Lesotho', 'MDG': 'Madagascar', 'MWI': 'Malawi',
    'MLI': 'Mali', 'MRT': 'Mauritanie', 'MUS': 'Maurice', 'MOZ': 'Mozambique',
    'NAM': 'Namibie', 'NER': 'Niger', 'RWA': 'Rwanda', 'STP': 'Sao Tomé-et-Príncipe',
    'SYC': 'Seychelles', 'SLE': 'Sierra Leone', 'SOM': 'Somalie', 'SDN': 'Soudan',
    'SSD': 'Soudan du Sud', 'SWZ': 'Eswatini', 'TGO': 'Togo', 'ZMB': 'Zambie',
    'ZWE': 'Zimbabwe',
}


def load_country_tariffs(country_iso3):
    global _tariff_cache
    country_iso3 = _validate_iso3(country_iso3)
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
        logger.error(f'Error loading tariffs for {country_iso3}: {e}')
        return None


def load_nomenclature_map(country_iso3):
    """Load nomenclature map for countries with extended sub-positions (like DZA)."""
    global _nomenclature_cache
    country_iso3 = _validate_iso3(country_iso3)
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
    if not data:
        return None
    hs6 = hs_code[:6]
    for line in data.get('tariff_lines', []):
        if line.get('hs6') == hs6 or line.get('code') == hs_code:
            return line
    return None


def get_sub_positions(country_iso3, hs6):
    """
    Return all national sub-positions for a given HS6 code.

    Merges sub-positions from two sources so that every national position is
    returned even when tariff_lines only carries a subset:

    1. Sub-positions with explicit DD rates stored inside the parent
       tariff_line (``line['sub_positions']``).
    2. All entries in the optional ``{ISO3}_nomenclature_map.json`` file that
       begin with the requested HS6 prefix (e.g. DZA_nomenclature_map.json
       contains 7610909910 which is missing from tariff_lines).

    The parent DD rate is used as the fallback rate for positions that only
    appear in the nomenclature map.
    """
    hs6_normalized = hs6[:6]
    line = get_tariff_line(country_iso3, hs6_normalized)
    parent_dd_rate_pct = line.get('dd_rate', 0) if line else 0

    # Build index from tariff_lines sub_positions (have explicit DD rates)
    merged: Dict[str, dict] = {}
    if line:
        for sp in line.get('sub_positions', []):
            code = sp.get('code', '')
            if code:
                merged[code] = {
                    'code': code,
                    'national_code': code,
                    'digits': sp.get('digits', len(code)),
                    'description_fr': sp.get('description_fr', sp.get('description_en', '')),
                    'description_en': sp.get('description_en', sp.get('description_fr', '')),
                    'dd_rate': sp.get('dd', parent_dd_rate_pct),
                    'source': sp.get('source', f'Nomenclature nationale {country_iso3}'),
                }

    # Merge with nomenclature_map – adds positions missing from tariff_lines
    # and enriches descriptions for existing ones
    nomenclature = load_nomenclature_map(country_iso3)
    if nomenclature:
        for code, description in nomenclature.items():
            if not (code.startswith(hs6_normalized) and len(code) > 6):
                continue
            if code not in merged:
                merged[code] = {
                    'code': code,
                    'national_code': code,
                    'digits': len(code),
                    'description_fr': description,
                    'description_en': description,
                    'dd_rate': parent_dd_rate_pct,
                    'source': f'Nomenclature DGD {country_iso3}',
                }
            else:
                # Enrich with official description when the tariff_lines entry
                # only has a generic placeholder (e.g. "Autres - Autre")
                if not merged[code].get('description_fr'):
                    merged[code]['description_fr'] = description
                if not merged[code].get('description_en'):
                    merged[code]['description_en'] = description

    result = sorted(merged.values(), key=lambda x: x['code'])
    logger.debug(f'get_sub_positions({country_iso3}, {hs6_normalized}): {len(result)} positions')
    return result


def get_taxes_detail(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get('taxes_detail', line.get('taxes', [])) if line else []


def get_fiscal_advantages(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get('fiscal_advantages', []) if line else []


def get_administrative_formalities(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get('administrative_formalities', []) if line else []


def search_tariff_lines(country_iso3, query, language='fr', limit=20):
    """Search tariff lines by HS code prefix or description keyword.

    Also searches the nomenclature map so that extended national codes
    (e.g. 7610909910) are discoverable by both code and description.
    """
    data = load_country_tariffs(country_iso3)
    if not data:
        return []
    q = query.lower().strip()
    desc_key = 'description_fr' if language == 'fr' else 'description_en'
    results = []
    for line in data.get('tariff_lines', []):
        hs6 = line.get('hs6', '')
        desc = line.get(desc_key, line.get('description_fr', line.get('designation', '')))
        if hs6.startswith(q) or q in desc.lower():
            results.append(line)
        if len(results) >= limit:
            break

    # Also search the nomenclature map for extended national codes
    if len(results) < limit:
        nomenclature = load_nomenclature_map(country_iso3)
        if nomenclature:
            for code, description in nomenclature.items():
                if code.startswith(q) or q in description.lower():
                    results.append({
                        'hs6': code[:6],
                        'national_code': code,
                        'description_fr': description,
                        'description_en': description,
                        'source': f'Nomenclature DGD {country_iso3}',
                    })
                    if len(results) >= limit:
                        break
    return results


def get_country_summary(country_iso3):
    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    summary = data.get('summary', {})
    tariff_lines = data.get('tariff_lines', [])
    nomenclature = load_nomenclature_map(country_iso3)
    return {
        'country_iso3': country_iso3,
        'total_lines': len(tariff_lines),
        'total_sub_positions': summary.get('total_sub_positions', sum(
            len(l.get('sub_positions', [])) for l in tariff_lines
        )),
        'total_national_positions': len(nomenclature) if nomenclature else 0,
        'chapters_covered': summary.get('chapters_covered', len(
            {l.get('chapter', '') for l in tariff_lines}
        )),
        'vat_rate_pct': summary.get('vat_rate_pct', 0),
        'dd_rate_range': summary.get('dd_rate_range', {}),
        'generated_at': data.get('generated_at', ''),
        'data_format': data.get('data_format', ''),
    }


def calculate_import_taxes(country_iso3, hs_code, cif_value, apply_zlecaf=False, language='fr'):
    """Calculate import taxes for a country/HS code/CIF value combination.

    Supports both HS6 codes and extended national sub-position codes (8-12
    digits).  For Algeria (DZA) and any country that has a nomenclature map,
    sub-position-level descriptions are returned even for codes that only
    appear in the nomenclature file.

    Returns a dict compatible with the frontend CalculatorTab component.
    """
    hs_code_clean = hs_code.replace('.', '').replace(' ', '')
    hs6 = hs_code_clean[:6]

    line = get_tariff_line(country_iso3, hs6)
    if not line:
        return {'error': f'Tariff line not found for {country_iso3}/{hs6}'}

    # Resolve DD rate: prefer sub-position specific rate when available
    dd_rate_pct = line.get('dd_rate', 0)
    sub_position_info = None

    if len(hs_code_clean) > 6:
        # Look for explicit rate in tariff_lines sub_positions
        for sp in line.get('sub_positions', []):
            if sp.get('code') == hs_code_clean:
                dd_rate_pct = sp.get('dd', dd_rate_pct)
                break

        # Resolve description: check nomenclature_map first (most complete)
        nomenclature = load_nomenclature_map(country_iso3)
        sp_desc = ''
        if nomenclature:
            sp_desc = nomenclature.get(hs_code_clean, '')
        if not sp_desc:
            for sp in line.get('sub_positions', []):
                if sp.get('code') == hs_code_clean:
                    sp_desc = sp.get('description_fr', sp.get('description_en', ''))
                    break

        sub_position_info = {
            'code': hs_code_clean,
            'description': sp_desc,
            'description_fr': sp_desc,
            'description_en': sp_desc,
        }

    vat_rate_pct = line.get('vat_rate', 0)
    other_taxes_pct = line.get('other_taxes_rate', 0)
    zlecaf_rate_pct = line.get('zlecaf_rate', 0) or 0

    # NPF (normal) calculation
    dd_amount = round(cif_value * dd_rate_pct / 100, 2)
    vat_base_npf = cif_value + dd_amount
    vat_amount_npf = round(vat_base_npf * vat_rate_pct / 100, 2)
    other_taxes_amount_npf = round(cif_value * other_taxes_pct / 100, 2)
    total_npf = round(cif_value + dd_amount + vat_amount_npf + other_taxes_amount_npf, 2)

    # ZLECAf calculation (DD reduced / exempted)
    dd_amount_zlecaf = round(cif_value * zlecaf_rate_pct / 100, 2)
    vat_base_zlecaf = cif_value + dd_amount_zlecaf
    vat_amount_zlecaf = round(vat_base_zlecaf * vat_rate_pct / 100, 2)
    other_taxes_amount_zlecaf = round(cif_value * other_taxes_pct / 100, 2)
    total_zlecaf = round(cif_value + dd_amount_zlecaf + vat_amount_zlecaf + other_taxes_amount_zlecaf, 2)

    savings_amount = round(total_npf - total_zlecaf, 2)
    savings_pct = round(savings_amount / total_npf * 100, 2) if total_npf > 0 else 0

    all_sub_positions = get_sub_positions(country_iso3, hs6)

    desc_key = 'description_fr' if language == 'fr' else 'description_en'
    description = line.get(desc_key, line.get('description_fr', ''))

    return {
        'hs_code': hs_code_clean,
        'hs6': hs6,
        'description': description,
        'description_fr': line.get('description_fr', ''),
        'description_en': line.get('description_en', ''),
        'country_iso3': country_iso3,
        'cif_value': cif_value,
        'generated_at': data.get('generated_at', '') if (data := load_country_tariffs(country_iso3)) else '',
        'rates': {
            'dd_rate_pct': dd_rate_pct,
            'zlecaf_rate_pct': zlecaf_rate_pct,
            'vat_rate_pct': vat_rate_pct,
            'other_taxes_pct': other_taxes_pct,
            'total_rate_pct': dd_rate_pct + vat_rate_pct + other_taxes_pct,
        },
        'npf_calculation': {
            'dd': {'base': cif_value, 'rate_pct': dd_rate_pct, 'amount': dd_amount},
            'vat': {'base': vat_base_npf, 'rate_pct': vat_rate_pct, 'amount': vat_amount_npf},
            'other_taxes': {'base': cif_value, 'rate_pct': other_taxes_pct, 'amount': other_taxes_amount_npf},
            'total_to_pay': total_npf,
        },
        'zlecaf_calculation': {
            'dd': {'base': cif_value, 'rate_pct': zlecaf_rate_pct, 'amount': dd_amount_zlecaf},
            'vat': {'base': vat_base_zlecaf, 'rate_pct': vat_rate_pct, 'amount': vat_amount_zlecaf},
            'other_taxes': {'base': cif_value, 'rate_pct': other_taxes_pct, 'amount': other_taxes_amount_zlecaf},
            'total_to_pay': total_zlecaf,
        },
        'savings': {
            'amount': savings_amount,
            'percentage': savings_pct,
        },
        'taxes_detail': line.get('taxes_detail', []),
        'fiscal_advantages': line.get('fiscal_advantages', []),
        'administrative_formalities': line.get('administrative_formalities', []),
        'has_sub_positions': len(all_sub_positions) > 0,
        'sub_position_count': len(all_sub_positions),
        'sub_position': sub_position_info,
        'data_source': 'authentic_tariff',
        'data_format': 'enhanced_v2',
    }


def get_available_countries():
    """Return list of countries that have tariff data files available (cached)."""
    global _available_countries_cache
    if _available_countries_cache is not None:
        return _available_countries_cache
    countries = []
    try:
        for fname in sorted(os.listdir(DATA_DIR)):
            if not fname.endswith('_tariffs.json') or fname.startswith('.'):
                continue
            iso3 = fname.replace('_tariffs.json', '').upper()
            data = load_country_tariffs(iso3)
            if not data:
                continue
            summary = data.get('summary', {})
            countries.append({
                'iso3': iso3,
                'name': _COUNTRY_NAMES.get(iso3, iso3),
                'total_lines': len(data.get('tariff_lines', [])),
                'total_positions': summary.get('total_positions', 0),
                'chapters_covered': summary.get('chapters_covered', 0),
                'has_nomenclature_map': os.path.exists(
                    os.path.join(DATA_DIR, f'{iso3}_nomenclature_map.json')
                ),
            })
    except Exception as e:
        logger.error(f'Error listing available countries: {e}')
    _available_countries_cache = countries
    return countries
