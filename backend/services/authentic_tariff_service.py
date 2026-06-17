import json
import os
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CRAWLED_DIR = os.path.join(DATA_DIR, 'crawled')
_tariff_cache = {}
_nomenclature_cache = {}
_crawled_index_cache = {}   # {ISO3: {hs_code_10: sub_position_entry}}
_available_countries_cache = None
_postgres_provider_cache = None


def load_crawled_position_index(country_iso3: str) -> dict:
    """
    Load and index the crawled DZA_tariffs.json (or similar) by hs_code.
    Returns {hs_code_10digits: entry_dict} for fast per-position lookup.
    Cached in memory after first load.
    """
    global _crawled_index_cache
    country_iso3 = _validate_iso3(country_iso3)
    if country_iso3 in _crawled_index_cache:
        return _crawled_index_cache[country_iso3]

    file_path = os.path.join(CRAWLED_DIR, f'{country_iso3}_tariffs.json')
    if not os.path.exists(file_path):
        _crawled_index_cache[country_iso3] = {}
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        index = {}
        for sp in data.get('sub_positions', []):
            code = sp.get('hs_code', '').replace('.', '').replace(' ', '')
            if code:
                index[code] = sp
        _crawled_index_cache[country_iso3] = index
        logger.info(f'Loaded crawled position index for {country_iso3}: {len(index)} entries')
        return index
    except Exception as e:
        logger.error(f'Error loading crawled index for {country_iso3}: {e}')
        _crawled_index_cache[country_iso3] = {}
        return {}

# Only allow well-formed ISO 2- or 3-letter country codes to prevent path traversal.
_ISO_CODE_RE = re.compile(r'^[A-Z]{2,3}$')


def _validate_iso3(country_iso3: str) -> str:
    """Normalise to uppercase and reject codes that could traverse the filesystem."""
    code = country_iso3.upper().strip()
    if not _ISO_CODE_RE.match(code):
        raise ValueError(f'Invalid country code: {country_iso3!r}')
    return code


def _get_postgres_provider():
    """Return PostgreSQL tariff provider when available, else None."""
    global _postgres_provider_cache
    if _postgres_provider_cache is False:
        return None
    if _postgres_provider_cache is not None:
        return _postgres_provider_cache
    try:
        from services.postgres_tariff_service import get_postgres_tariff_service
        _postgres_provider_cache = get_postgres_tariff_service()
        return _postgres_provider_cache
    except Exception as e:
        logger.info(f'PostgreSQL tariff provider unavailable, using ETL fallback: {e}')
        _postgres_provider_cache = False
        return None


def _log_etl_fallback(operation: str, country_iso3: str, hs_code: str = '', reason: str = ''):
    context = f'{operation} {country_iso3}'
    if hs_code:
        context += f'/{hs_code}'
    if reason:
        context += f' ({reason})'
    logger.warning(f'Tariff ETL fallback activated: {context}')

# ── Per-country tax cascade profiles ──────────────────────────────────────────
# Each entry defines:
#   taxes_order: order in which taxes are applied
#   tax_bases:   {tax_code: ('BASE_FORMULA', [codes_already_computed_to_add])}
#     BASE_FORMULA = 'CIF'        → base = CIF value
#                   'DD_AMOUNT'   → base = the DD amount already computed (e.g. CAC)
#   source: official legal reference
#
# Rules are sourced from official customs legislation per country.
# ──────────────────────────────────────────────────────────────────────────────
_ECOWAS_UEMOA = {   # shared base profile for UEMOA/CEDEAO members
    'taxes_order': ['DD', 'RS', 'PCS', 'TVA'],
    'tax_bases': {
        'DD':  ('CIF', []),
        'RS':  ('CIF', []),    # Redevance Statistique: base CIF (UEMOA)
        'PCS': ('CIF', []),    # Prélèvement Communautaire de Solidarité: base CIF
        'TVA': ('CIF', ['DD']),  # TVA base = CIF + DD (OHADA/UEMOA practice)
    },
    'source': 'TEC CEDEAO / Code CGI UEMOA — TVA base = CIF+DD',
}
_CEMAC = {           # shared base profile for CEMAC members
    'taxes_order': ['DD', 'TCI', 'CAC', 'TVA'],
    'tax_bases': {
        'DD':  ('CIF', []),
        'TCI': ('CIF', []),        # Taxe Communautaire d'Intégration: base CIF
        'CAC': ('DD_AMOUNT', []),  # Centimes Additionnels Communaux: % of DD amount
        'TVA': ('CIF', ['DD', 'TCI']),  # Directive TVA CEMAC: base = CIF+DD+TCI
    },
    'source': 'Tarif Extérieur Commun CEMAC — Directive TVA CEMAC art. 9',
}
_EAC = {             # EAC common profile (Kenya, Tanzania, Uganda, Rwanda, Burundi)
    'taxes_order': ['DD', 'IDF', 'TVA'],
    'tax_bases': {
        'DD':  ('CIF', []),
        'IDF': ('CIF', []),        # Import Declaration Fee: base CIF
        'TVA': ('CIF', ['DD']),    # EAC Customs Management Act: base = CIF+DD
    },
    'source': 'EAC Customs Management Act — VAT base = CIF+DD',
}

COUNTRY_TAX_PROFILES = {
    # ── Algérie — DGD (douane.gov.dz / conformepro.dz) ───────────────────────
    # DAPS, DD, PRCT, TCS : base = CIF
    # TVA : base = CIF + DAPS + DD  (art. 21 CTCA)
    'DZA': {
        'taxes_order': ['DAPS', 'DD', 'PRCT', 'TCS', 'TVA'],
        'tax_bases': {
            'DAPS': ('CIF', []),
            'DD':   ('CIF', []),
            'PRCT': ('CIF', []),
            'TCS':  ('CIF', []),
            'TVA':  ('CIF', ['DAPS', 'DD']),  # art. 21 CTCA
        },
        'source': 'douane.gov.dz — art. 21 CTCA (TVA base = CIF+DAPS+DD)',
    },
    # ── Maroc — ADII (douane.gov.ma) ──────────────────────────────────────────
    # DD, TPI : base = CIF
    # TVA : base = CIF + DD + TPI  (CGI Maroc art. 96)
    'MAR': {
        'taxes_order': ['DD', 'TPI', 'TVA'],
        'tax_bases': {
            'DD':  ('CIF', []),
            'TPI': ('CIF', []),
            'TVA': ('CIF', ['DD', 'TPI']),  # CGI Maroc art. 96
        },
        'source': 'douane.gov.ma — CGI Maroc art. 96 (TVA base = CIF+DD+TPI)',
    },
    # ── Ghana — UNIPASS/ICUMS (external.unipassghana.com) ────────────────────
    # DD, ECOWAS Levy : base = CIF
    # GETFUND, NHIL, VAT : base = CIF + DD + ECOWAS  (VAT Act 870)
    'GHA': {
        'taxes_order': ['DD', 'CEDEAO', 'TVA', 'NHIL', 'GETFUND'],
        'tax_bases': {
            'DD':      ('CIF', []),
            'CEDEAO':  ('CIF', []),
            'TVA':     ('CIF', ['DD', 'CEDEAO']),   # VAT Act 870 s.7
            'NHIL':    ('CIF', ['DD', 'CEDEAO']),   # NHIL Act
            'GETFUND': ('CIF', ['DD', 'CEDEAO']),   # GETFUND Act
        },
        'source': 'UNIPASS Ghana — VAT Act 870 (VAT/NHIL/GETFUND base = CIF+DD+ECOWAS)',
    },
    # ── Nigeria — NCS (customs.gov.ng, ECOWAS CET) ───────────────────────────
    # DD, ECOWAS, CISS : base = CIF
    # VAT : base = CIF + DD  (VAITA Nigeria s.2)
    'NGA': {
        'taxes_order': ['DD', 'CEDEAO', 'CISS', 'TVA'],
        'tax_bases': {
            'DD':     ('CIF', []),
            'CEDEAO': ('CIF', []),
            'CISS':   ('CIF', []),
            'TVA':    ('CIF', ['DD']),  # VAITA s.2
        },
        'source': 'customs.gov.ng — VAITA Nigeria s.2 (VAT base = CIF+DD)',
    },
    # ── Afrique du Sud — SARS (sars.gov.za) ──────────────────────────────────
    # VAT : base = CIF + DD  (VAT Act s.13(2))
    'ZAF': {
        'taxes_order': ['DD', 'TVA'],
        'tax_bases': {
            'DD':  ('CIF', []),
            'TVA': ('CIF', ['DD']),  # VAT Act s.13(2)
        },
        'source': 'sars.gov.za — VAT Act s.13(2) (VAT base = CIF+DD)',
    },
    # ── Kenya / EAC — KRA (kra.go.ke) ────────────────────────────────────────
    # IDF (3.5%): base CIF  (Finance Act 2022)
    # VAT (16%): base = CIF + DD  (VAT Act Cap 476)
    'KEN': {**_EAC, 'source': 'kra.go.ke — VAT Act Cap 476 / Finance Act 2022'},
    # ── Tanzanie / EAC — TRA ──────────────────────────────────────────────────
    'TZA': {**_EAC, 'source': 'TRA Tanzania — VAT Act Cap 148'},
    # ── Ouganda / EAC — URA ───────────────────────────────────────────────────
    'UGA': {**_EAC, 'source': 'URA Uganda — VAT Act Cap 349'},
    # ── Rwanda / EAC — RRA ────────────────────────────────────────────────────
    'RWA': {**_EAC, 'source': 'RRA Rwanda — VAT Act Cap 349'},
    # ── Burundi / EAC — OBR ───────────────────────────────────────────────────
    'BDI': {**_EAC, 'source': 'OBR Burundi — EAC CMA'},
    # ── Égypte — ECA (customs.gov.eg/Services/Tarif) ───────────────────────────
    # TVA : base = CIF uniquement  (Loi n°67/2016 art. 29)
    'EGY': {
        'taxes_order': ['DD', 'TVA'],
        'tax_bases': {
            'DD':  ('CIF', []),
            'TVA': ('CIF', []),  # Loi 67/2016 art. 29: TVA base = CIF (pas CIF+DD)
        },
        'source': 'Egyptian Customs Authority (customs.gov.eg/Services/Tarif) — Loi TVA n°67/2016 art. 29 (TVA base = CIF)',
    },
    # ── Éthiopie — ECC (customs.erca.gov.et) ─────────────────────────────────
    # SUR (Excise): base = CIF + DD
    # TVA (15%): base = CIF + DD + SUR  (Ethiopian Customs/Tax Authority)
    'ETH': {
        'taxes_order': ['DD', 'SUR', 'TVA'],
        'tax_bases': {
            'DD':  ('CIF', []),
            'SUR': ('CIF', ['DD']),         # Excise base = CIF + DD
            'TVA': ('CIF', ['DD', 'SUR']),  # VAT base = CIF + DD + Excise
        },
        'source': 'customs.erca.gov.et — ERCA (TVA base = CIF+DD+SUR)',
    },
    # ── Tunisie — DGD (douane.gov.tn) ────────────────────────────────────────
    # TCL : base CIF
    # TVA : base = CIF + DD  (CTVA Tunisie art. 6)
    'TUN': {
        'taxes_order': ['DD', 'TCL', 'TVA'],
        'tax_bases': {
            'DD':  ('CIF', []),
            'TCL': ('CIF', []),
            'TVA': ('CIF', ['DD']),  # CTVA art. 6
        },
        'source': 'douane.gov.tn — CTVA art. 6 (TVA base = CIF+DD)',
    },
    # ── UEMOA / CEDEAO members ────────────────────────────────────────────────
    'SEN': {**_ECOWAS_UEMOA, 'source': 'douanes.sn / TEC CEDEAO — CGI Sénégal'},
    'CIV': {**_ECOWAS_UEMOA, 'source': 'guce.gouv.ci / TEC CEDEAO — CGI Côte d\'Ivoire'},
    'BEN': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Bénin'},
    'BFA': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Burkina Faso'},
    'MLI': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Mali'},
    'NER': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Niger'},
    'TGO': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Togo'},
    'GIN': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Guinée'},
    'GNB': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO — CGI Guinée-Bissau'},
    'GMB': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO'},
    'SLE': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO'},
    'LBR': {**_ECOWAS_UEMOA, 'source': 'TEC CEDEAO'},
    # ── CEMAC members ─────────────────────────────────────────────────────────
    'CMR': {**_CEMAC, 'source': 'douanes.cm — Directive TVA CEMAC art. 9'},
    'GAB': {**_CEMAC, 'source': 'CEMAC Tarif des Douanes'},
    'COG': {**_CEMAC, 'source': 'CEMAC Tarif des Douanes'},
    'CAF': {**_CEMAC, 'source': 'CEMAC Tarif des Douanes'},
    'GNQ': {**_CEMAC, 'source': 'CEMAC Tarif des Douanes'},
    'TCD': {**_CEMAC, 'source': 'CEMAC Tarif des Douanes'},
}

# Human-readable labels for each tax code
_TAX_LABELS = {
    'DD':      'Droits de Douane',
    'DAPS':    'Droit Additionnel Provisoire de Sauvegarde',
    'PRCT':    'Prélèvement à la Compensation du Transport',
    'TCS':     'Taxe Complémentaire de Sauvegarde',
    'TVA':     'Taxe sur la Valeur Ajoutée',
    'TPI':     "Taxe Parafiscale à l'Importation",
    'CEDEAO':  'Prélèvement Communautaire CEDEAO',
    'GETFUND': 'Ghana Education Trust Fund Levy',
    'NHIL':    'National Health Insurance Levy',
    'CISS':    'Comprehensive Import Supervision Scheme',
    'IDF':     'Import Declaration Fee',
    'TCI':     "Taxe Communautaire d'Intégration",
    'CAC':     'Centimes Additionnels Communaux',
    'RS':      'Redevance Statistique',
    'PCS':     'Prélèvement Communautaire de Solidarité',
    'SUR':     'Taxe Additionnelle / Accises',
    'TCL':     'Taxe de Compensation des Licences',
    'D.D':     'Droits de Douane',
    'T.V.A':   'Taxe sur la Valeur Ajoutée',
}

def _normalize_tax_code(code: str) -> str:
    """Normalise 'D.D' → 'DD', 'T.V.A' → 'TVA', etc."""
    return code.replace('.', '').replace(' ', '').upper()


def compute_tax_cascade(cif_value: float, taxes_rates: dict, country_iso3: str) -> dict:
    """
    Compute import taxes using the official cascade method for each country.

    Args:
        cif_value:    CIF value of the goods
        taxes_rates:  {normalized_code: rate_pct}  e.g. {'DD': 30, 'DAPS': 60, 'TVA': 19}
        country_iso3: ISO-3 country code

    Returns a dict with:
        steps:          list of per-tax calculation steps (base, rate, amount)
        total_taxes:    total tax amount (excluding CIF)
        total_to_pay:   CIF + total_taxes
        effective_rate_pct:  (total_taxes / cif_value) × 100
        legal_source:   official legal reference used
    """
    profile = COUNTRY_TAX_PROFILES.get(country_iso3)

    # ── Default profile for unmapped countries ────────────────────────────────
    # All taxes on CIF; TVA on CIF+DD (most common pattern)
    if not profile:
        ordered_codes = list(taxes_rates.keys())
        bases = {c: ('CIF', []) for c in ordered_codes}
        # If TVA or T.V.A present, apply on CIF+DD
        for vat_alias in ('TVA', 'T.V.A'):
            if vat_alias in bases:
                bases[vat_alias] = ('CIF', ['DD'] if 'DD' in bases else [])
        profile = {'taxes_order': ordered_codes, 'tax_bases': bases,
                   'source': f'Profil par défaut (TVA base = CIF+DD)'}

    taxes_order = profile['taxes_order']
    tax_bases   = profile['tax_bases']
    legal_source = profile.get('source', '')

    # Build a normalized lookup: norm_code → rate
    norm_rates = {_normalize_tax_code(k): v for k, v in taxes_rates.items()}

    # Add any taxes present in the data but not in the profile (apply on CIF)
    for code in list(norm_rates.keys()):
        if code not in [_normalize_tax_code(c) for c in taxes_order]:
            taxes_order = list(taxes_order) + [code]
            tax_bases[code] = ('CIF', [])

    # Compute amounts in order, tracking each computed amount for cascade reuse
    computed_amounts: dict = {}   # norm_code → amount
    steps = []
    cumulative = cif_value

    for raw_code in taxes_order:
        norm_code = _normalize_tax_code(raw_code)
        rate = norm_rates.get(norm_code, 0.0)
        if rate == 0:
            continue

        base_formula, add_codes = tax_bases.get(raw_code, tax_bases.get(norm_code, ('CIF', [])))

        # Compute the base value
        if base_formula == 'DD_AMOUNT':
            # e.g. CAC = % of DD_amount
            base_value = computed_amounts.get('DD', 0.0)
        else:
            # 'CIF' + optional already-computed amounts
            base_value = cif_value
            for dep_code in add_codes:
                base_value += computed_amounts.get(_normalize_tax_code(dep_code), 0.0)

        amount = round(base_value * rate / 100, 2)
        computed_amounts[norm_code] = amount
        cumulative = round(cumulative + amount, 2)

        label = _TAX_LABELS.get(norm_code, _TAX_LABELS.get(raw_code, raw_code))
        if base_formula == 'DD_AMOUNT':
            base_desc = 'DD_montant'
        elif add_codes:
            base_desc = 'CIF + ' + ' + '.join(add_codes)
        else:
            base_desc = 'CIF'

        steps.append({
            'code':         norm_code,
            'label':        label,
            'rate_pct':     rate,
            'base_formula': base_desc,
            'base_value':   round(base_value, 2),
            'amount':       amount,
            'cumulative':   cumulative,
        })

    total_taxes = round(sum(s['amount'] for s in steps), 2)
    total_to_pay = round(cif_value + total_taxes, 2)
    effective_rate_pct = round(total_taxes / cif_value * 100, 2) if cif_value > 0 else 0.0

    return {
        'steps':               steps,
        'total_taxes':         total_taxes,
        'total_to_pay':        total_to_pay,
        'effective_rate_pct':  effective_rate_pct,
        'legal_source':        legal_source,
    }


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
    country_iso3 = _validate_iso3(country_iso3)
    hs_code_clean = hs_code.replace('.', '').replace(' ', '')
    hs6 = hs_code_clean[:6]

    provider = _get_postgres_provider()
    if provider:
        try:
            regulatory = provider.get_regulatory_details(country_iso3, hs6)
            country_info = provider.get_country_info(country_iso3) or {}
            if regulatory and regulatory.get('success'):
                measures = regulatory.get('measures', []) or []
                requirements = regulatory.get('requirements', []) or []
                taxes_detail = [
                    {
                        'tax': _normalize_tax_code(str(m.get('code') or m.get('type') or '')),
                        'rate': float(m.get('rate', 0) or 0),
                        'observation': m.get('name', m.get('type', '')),
                        'source': 'postgres',
                    }
                    for m in measures
                    if (m.get('code') or m.get('type'))
                ]
                other_taxes_rate = round(sum(
                    t['rate'] for t in taxes_detail
                    if t['tax'] not in ('DD', 'TVA')
                ), 4)
                sub_positions = provider.get_sub_positions(country_iso3, hs6, 'fr') or []
                normalized_sub_positions = [
                    {
                        'code': sp.get('code'),
                        'digits': sp.get('digits', len(sp.get('code', ''))),
                        'description_fr': sp.get('description_fr', sp.get('description_en', '')),
                        'description_en': sp.get('description_en', sp.get('description_fr', '')),
                        'dd': float(sp.get('dd', 0) or 0),
                        'source': 'postgres',
                    }
                    for sp in sub_positions
                    if sp.get('code')
                ]
                fiscal_advantages = [
                    {
                        'tax_code': m.get('code'),
                        'condition_fr': f"ZLECAF applicable: {m.get('name', m.get('type', ''))}",
                        'condition_en': f"AfCFTA applicable: {m.get('name', m.get('type', ''))}",
                        'reduced_rate_pct': m.get('zlecaf_rate'),
                    }
                    for m in measures
                    if m.get('zlecaf_applicable') and m.get('zlecaf_rate') is not None
                ]
                return {
                    'hs6': hs6,
                    'code': hs_code_clean,
                    'description_fr': regulatory.get('description', ''),
                    'description_en': regulatory.get('description', ''),
                    'dd_rate': float(regulatory.get('taxes', {}).get('dd_rate', 0) or 0),
                    'zlecaf_rate': float(regulatory.get('taxes', {}).get('zlecaf_rate', 0) or 0),
                    'vat_rate': float(country_info.get('vat_rate', 0) or 0),
                    'other_taxes_rate': other_taxes_rate,
                    'taxes_detail': taxes_detail,
                    'fiscal_advantages': fiscal_advantages,
                    'administrative_formalities': requirements,
                    'sub_positions': normalized_sub_positions,
                    'source': 'postgres',
                    'data_source': 'postgres',
                }
            _log_etl_fallback('get_tariff_line', country_iso3, hs6, 'postgres-miss')
        except Exception as e:
            _log_etl_fallback('get_tariff_line', country_iso3, hs6, f'postgres-error: {e}')

    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    for line in data.get('tariff_lines', []):
        if line.get('hs6') == hs6 or line.get('code') == hs_code_clean:
            return line
    return None


def get_sub_positions(country_iso3, hs6, language='fr'):
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
    country_iso3 = _validate_iso3(country_iso3)
    hs6_normalized = hs6.replace('.', '').replace(' ', '')[:6]

    provider = _get_postgres_provider()
    if provider:
        try:
            postgres_positions = provider.get_sub_positions(country_iso3, hs6_normalized, language) or []
            if postgres_positions:
                return [
                    {
                        'code': sp.get('code'),
                        'national_code': sp.get('code'),
                        'digits': sp.get('digits', len(sp.get('code', ''))),
                        'description_fr': sp.get('description_fr', sp.get('description_en', '')),
                        'description_en': sp.get('description_en', sp.get('description_fr', '')),
                        'dd_rate': float(sp.get('dd', 0) or 0),
                        'source': 'postgres',
                    }
                    for sp in postgres_positions
                    if sp.get('code')
                ]
            _log_etl_fallback('get_sub_positions', country_iso3, hs6_normalized, 'postgres-miss')
        except Exception as e:
            _log_etl_fallback('get_sub_positions', country_iso3, hs6_normalized, f'postgres-error: {e}')

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
                    'source': sp.get('source', f'Nomenclature nationale DGD {country_iso3}'),
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

    Priority order:
    1. Crawled authentic sub-positions (10-digit, e.g. DZA 17 114 positions from CSV)
    2. ETL tariff_lines (HS6-level)
    3. Nomenclature map (extended national codes)
    """
    country_iso3 = _validate_iso3(country_iso3)
    q = query.lower().strip()
    results = []
    seen_codes = set()

    provider = _get_postgres_provider()
    if provider:
        try:
            pg_results = provider.search_commodities(country_iso3, query, limit=limit, language=language) or []
            if pg_results:
                return [
                    {
                        'hs6': r.get('hs6', ''),
                        'national_code': r.get('code', r.get('hs6', '')),
                        'description_fr': r.get('description', ''),
                        'description_en': r.get('description', ''),
                        'dd_rate': r.get('dd_rate', 0),
                        'zlecaf_rate': r.get('zlecaf_rate', 0),
                        'source': 'postgres',
                    }
                    for r in pg_results
                ]
            _log_etl_fallback('search_tariff_lines', country_iso3, reason='postgres-miss')
        except Exception as e:
            _log_etl_fallback('search_tariff_lines', country_iso3, reason=f'postgres-error: {e}')

    # ── 1. Crawled sub-positions (authentic, 10-digit) ──────────────────────
    crawled_index = load_crawled_position_index(country_iso3)
    if crawled_index:
        for code, sp in crawled_index.items():
            name = (sp.get('name') or sp.get('description') or sp.get('designation') or '').lower()
            if code.startswith(q) or q in name:
                taxes = sp.get('taxes', {})
                dd = taxes.get('DD', {}).get('rate', 0)
                tva = taxes.get('TVA', {}).get('rate', 0)
                tcs = taxes.get('TCS', {}).get('rate', 0)
                prct = taxes.get('PRCT', {}).get('rate', 0)
                daps = taxes.get('DAPS', {}).get('rate', 0)
                # Effective rate = total_taxes / CIF×100 (cascade, not sum of rates)
                ref_cascade = compute_tax_cascade(
                    100.0,
                    {c: r for c, r in [('DD', dd), ('DAPS', daps), ('PRCT', prct), ('TCS', tcs), ('TVA', tva)] if r > 0},
                    country_iso3
                )
                results.append({
                    'hs6': code[:6],
                    'national_code': code,
                    'description_fr': sp.get('name') or sp.get('description') or '',
                    'description_en': sp.get('name') or sp.get('description') or '',
                    'designation': sp.get('designation') or sp.get('name') or '',
                    'dd_rate': dd,
                    'tva_rate': tva,
                    'tcs_rate': tcs,
                    'prct_rate': prct,
                    'daps_rate': daps,
                    'effective_rate': ref_cascade['effective_rate_pct'],
                    'total_rate': ref_cascade['effective_rate_pct'],  # kept for compat
                    'advantages': sp.get('advantages', []),
                    'source': 'douane.gov.dz',
                    'source_quality': 'crawled_authentic',
                })
                seen_codes.add(code)
                if len(results) >= limit:
                    return results

    # ── 2. ETL tariff_lines (HS6-level) ─────────────────────────────────────
    if len(results) < limit:
        data = load_country_tariffs(country_iso3)
        if data:
            desc_key = 'description_fr' if language == 'fr' else 'description_en'
            for line in data.get('tariff_lines', []):
                hs6 = line.get('hs6', '')
                desc = line.get(desc_key, line.get('description_fr', line.get('designation', '')))
                if hs6 not in seen_codes and (hs6.startswith(q) or q in desc.lower()):
                    results.append(line)
                    seen_codes.add(hs6)
                    if len(results) >= limit:
                        return results

    # ── 3. Nomenclature map (extended national codes) ────────────────────────
    if len(results) < limit:
        nomenclature = load_nomenclature_map(country_iso3)
        if nomenclature:
            for code, description in nomenclature.items():
                if code not in seen_codes and (code.startswith(q) or q in description.lower()):
                    results.append({
                        'hs6': code[:6],
                        'national_code': code,
                        'description_fr': description,
                        'description_en': description,
                        'source': f'Nomenclature DGD {country_iso3}',
                    })
                    seen_codes.add(code)
                    if len(results) >= limit:
                        break

    return results


def get_country_summary(country_iso3):
    country_iso3 = _validate_iso3(country_iso3)
    provider = _get_postgres_provider()
    if provider:
        try:
            country = provider.get_country_info(country_iso3)
            if country:
                return {
                    'country_iso3': country_iso3,
                    'total_lines': int(country.get('total_positions', 0) or 0),
                    'total_sub_positions': int(country.get('total_positions', 0) or 0),
                    'total_national_positions': int(country.get('total_positions', 0) or 0),
                    'chapters_covered': country.get('chapters_covered', 0),
                    'vat_rate_pct': float(country.get('vat_rate', 0) or 0),
                    'dd_rate_range': {},
                    'generated_at': country.get('last_updated', ''),
                    'data_format': 'postgres',
                }
            _log_etl_fallback('get_country_summary', country_iso3, reason='postgres-miss')
        except Exception as e:
            _log_etl_fallback('get_country_summary', country_iso3, reason=f'postgres-error: {e}')

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

    country_data = load_country_tariffs(country_iso3)
    line = get_tariff_line(country_iso3, hs6)
    if not line:
        return {'error': f'Tariff line not found for {country_iso3}/{hs6}'}
    is_postgres_line = line.get('data_source') == 'postgres' or line.get('source') == 'postgres'

    # Resolve DD rate: prefer sub-position specific rate when available
    dd_rate_pct = line.get('dd_rate', 0)
    sub_position_info = None

    # --- Priority 1: crawled authentic JSON (per-position taxes) ---
    # For countries that have a crawled/{ISO3}_tariffs.json with per-position
    # tax rates (source_quality=crawled_authentic), these rates take precedence
    # over the ETL-computed rates in the main DZA_tariffs.json.
    crawled_sp_entry = None
    if not is_postgres_line:
        crawled_index = load_crawled_position_index(country_iso3)
        if crawled_index and hs_code_clean in crawled_index:
            crawled_sp_entry = crawled_index[hs_code_clean]

    if len(hs_code_clean) > 6:
        if crawled_sp_entry:
            # Use crawled per-position DD rate (authentic, sourced from douane.gov.dz)
            crawled_taxes = crawled_sp_entry.get('taxes', {})
            if 'DD' in crawled_taxes:
                dd_rate_pct = float(crawled_taxes['DD'].get('rate', dd_rate_pct))
        else:
            # Fall back to ETL tariff_lines sub_positions
            for sp in line.get('sub_positions', []):
                if sp.get('code') == hs_code_clean:
                    dd_rate_pct = sp.get('dd', dd_rate_pct)
                    break

        # Resolve description: crawled name > nomenclature_map > sub_positions
        sp_desc = ''
        if crawled_sp_entry:
            sp_desc = crawled_sp_entry.get('name', '') or crawled_sp_entry.get('description', '')
        if not sp_desc:
            nomenclature = load_nomenclature_map(country_iso3)
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

    # Extract DAPS and other individual taxes:
    # If crawled entry has per-position taxes, use them as primary source;
    # otherwise fall back to taxes_detail from the ETL line.
    if (not is_postgres_line) and crawled_sp_entry and crawled_sp_entry.get('taxes'):
        crawled_taxes = crawled_sp_entry['taxes']
        taxes_detail = {
            k: {'label': v.get('name', k), 'rate': v.get('rate', 0), 'source': v.get('source', 'crawled')}
            for k, v in crawled_taxes.items() if isinstance(v, dict)
        }
        # Inherit VAT and ZLECAf from ETL line (not always in crawled)
        if 'TVA' in crawled_taxes:
            vat_rate_pct = float(crawled_taxes['TVA'].get('rate', vat_rate_pct))
    else:
        taxes_detail = line.get('taxes_detail', {})

    # ── Normalise taxes_detail: accept both dict and list formats ─────────────
    # Dict format (crawled DZA): {'DD': {'rate': 30, 'name': '...'}, ...}
    # List format (ETL):         [{'tax': 'D.D', 'rate': 20, 'observation': '...'}, ...]
    if isinstance(taxes_detail, list):
        taxes_detail = {
            _normalize_tax_code(item.get('tax', item.get('code', ''))): {
                'rate':  float(item.get('rate', 0) or 0),
                'label': item.get('observation', item.get('label', item.get('tax', ''))),
                'source': 'etl',
            }
            for item in taxes_detail
            if item.get('tax') or item.get('code')
        }
    elif not isinstance(taxes_detail, dict):
        taxes_detail = {}

    daps_rate_pct = 0.0
    prct_rate_pct = 0.0
    tcs_rate_pct  = 0.0
    individual_taxes = []
    for tax_code, tax_info in taxes_detail.items():
        if not isinstance(tax_info, dict):
            continue
        norm = _normalize_tax_code(tax_code)
        rate = float(tax_info.get('rate', 0) or 0)
        if rate == 0:
            continue
        label = tax_info.get('label', tax_info.get('name', _TAX_LABELS.get(norm, tax_code)))
        individual_taxes.append({'code': norm, 'label': label, 'rate_pct': rate})
        if norm == 'DAPS':
            daps_rate_pct = rate
        elif norm == 'PRCT':
            prct_rate_pct = rate
        elif norm == 'TCS':
            tcs_rate_pct  = rate
        # Capture VAT from taxes_detail when not already set from crawled source
        elif norm in ('TVA', 'TVAI') and vat_rate_pct == 0:
            vat_rate_pct = rate

    # ── Resolve PRCT / TCS when not explicitly in taxes_detail ───────────────
    # Only add PRCT fallback if other_taxes_pct is not already covered by an
    # explicit individual tax (e.g. TPI for MAR already covers the 0.25%).
    _covered_other = sum(
        t['rate_pct'] for t in individual_taxes
        if t['code'] not in ('DD', 'TVA', 'DAPS')
    )
    if prct_rate_pct == 0 and other_taxes_pct > 0 and round(_covered_other, 4) < round(other_taxes_pct, 4):
        prct_rate_pct = other_taxes_pct
        if not any(t['code'] == 'PRCT' for t in individual_taxes):
            individual_taxes.insert(0, {
                'code': 'PRCT',
                'label': 'Prélèvement à la Compensation du Transport',
                'rate_pct': other_taxes_pct
            })

    # ── Build rates dict for cascade engine ──────────────────────────────────
    # Normalised code → rate_pct  (only non-zero taxes)
    taxes_for_cascade: dict = {}
    if daps_rate_pct > 0:
        taxes_for_cascade['DAPS'] = daps_rate_pct
    if dd_rate_pct > 0:
        taxes_for_cascade['DD'] = dd_rate_pct
    if prct_rate_pct > 0:
        taxes_for_cascade['PRCT'] = prct_rate_pct
    if tcs_rate_pct > 0:
        taxes_for_cascade['TCS'] = tcs_rate_pct
    if vat_rate_pct > 0:
        taxes_for_cascade['TVA'] = vat_rate_pct
    # Add any other taxes from individual_taxes not yet covered
    for t in individual_taxes:
        c = _normalize_tax_code(t['code'])
        if c not in taxes_for_cascade and t.get('rate_pct', 0) > 0:
            taxes_for_cascade[c] = t['rate_pct']

    # ── NPF cascade (régime normal / Most-Favoured-Nation) ───────────────────
    npf_cascade = compute_tax_cascade(cif_value, taxes_for_cascade, country_iso3)

    # ── ZLECAf cascade (DD replaced by ZLECAf preferential rate) ─────────────
    zlecaf_taxes = dict(taxes_for_cascade)
    if zlecaf_rate_pct is not None and zlecaf_rate_pct < dd_rate_pct:
        if zlecaf_rate_pct == 0:
            zlecaf_taxes.pop('DD', None)
        else:
            zlecaf_taxes['DD'] = zlecaf_rate_pct
    zlecaf_cascade = compute_tax_cascade(cif_value, zlecaf_taxes, country_iso3)

    savings_amount = round(npf_cascade['total_to_pay'] - zlecaf_cascade['total_to_pay'], 2)
    savings_pct = round(savings_amount / npf_cascade['total_to_pay'] * 100, 2) if npf_cascade['total_to_pay'] > 0 else 0

    all_sub_positions = get_sub_positions(country_iso3, hs6)
    desc_key = 'description_fr' if language == 'fr' else 'description_en'
    description = line.get(desc_key, line.get('description_fr', ''))

    # ── Build backward-compatible npf_calculation / zlecaf_calculation dicts ─
    def _steps_to_legacy(steps, cif):
        """Convert cascade steps to legacy {daps/dd/vat/other_taxes} dict."""
        out = {'total_to_pay': round(cif + sum(s['amount'] for s in steps), 2)}
        for s in steps:
            c = s['code']
            entry = {'base': s['base_value'], 'rate_pct': s['rate_pct'], 'amount': s['amount']}
            if c == 'DD':
                out['dd'] = entry
            elif c == 'DAPS':
                out['daps'] = entry
            elif c in ('TVA', 'T.V.A'):
                out['vat'] = entry
            else:
                # Accumulate other taxes
                ot = out.get('other_taxes', {'base': cif, 'rate_pct': 0, 'amount': 0})
                ot['amount'] = round(ot['amount'] + s['amount'], 2)
                ot['rate_pct'] = round(ot['rate_pct'] + s['rate_pct'], 4)
                out['other_taxes'] = ot
        return out

    npf_legacy   = _steps_to_legacy(npf_cascade['steps'],    cif_value)
    zlecaf_legacy = _steps_to_legacy(zlecaf_cascade['steps'], cif_value)

    return {
        'hs_code':        hs_code_clean,
        'hs6':            hs6,
        'description':    description,
        'description_fr': line.get('description_fr', ''),
        'description_en': line.get('description_en', ''),
        'country_iso3':   country_iso3,
        'cif_value':      cif_value,
        'generated_at':   country_data.get('generated_at', '') if country_data else '',
        'rates': {
            'daps_rate_pct':       daps_rate_pct,
            'dd_rate_pct':         dd_rate_pct,
            'zlecaf_rate_pct':     zlecaf_rate_pct,
            'vat_rate_pct':        vat_rate_pct,
            'other_taxes_pct':     other_taxes_pct,
            'prct_rate_pct':       prct_rate_pct,
            'tcs_rate_pct':        tcs_rate_pct,
            # effective_rate_pct = total_taxes / CIF × 100 (NOT a sum of rates)
            'effective_rate_pct':  npf_cascade['effective_rate_pct'],
            # Kept for legacy compatibility but labelled clearly
            'sum_of_rates_pct':    round(sum(taxes_for_cascade.values()), 2),
        },
        # Step-by-step cascade — ready for frontend display
        'calculation_steps':        npf_cascade['steps'],
        'calculation_steps_zlecaf': zlecaf_cascade['steps'],
        'cascade_legal_source':     npf_cascade['legal_source'],
        # Legacy keys kept for backward compatibility with existing frontend code
        'npf_calculation':    npf_legacy,
        'zlecaf_calculation': zlecaf_legacy,
        'savings': {
            'amount':     savings_amount,
            'percentage': savings_pct,
        },
        'taxes_detail':               taxes_detail,
        'individual_taxes':           individual_taxes,
        'fiscal_advantages':          line.get('fiscal_advantages', []),
        'administrative_formalities': line.get('administrative_formalities', []),
        'has_sub_positions':          len(all_sub_positions) > 0,
        'sub_position_count':         len(all_sub_positions),
        'sub_position':               sub_position_info,
        'data_source':                'authentic_tariff',
        'data_format':                'enhanced_v2',
    }


def get_available_countries():
    """Return list of countries that have tariff data files available (cached)."""
    global _available_countries_cache
    if _available_countries_cache is not None:
        return _available_countries_cache
    countries = []
    provider = _get_postgres_provider()
    if provider:
        try:
            pg_countries = provider.get_countries() or []
            if pg_countries:
                countries = [
                    {
                        'iso3': c.get('iso3', ''),
                        'name': _COUNTRY_NAMES.get(c.get('iso3', ''), c.get('name_fr', c.get('iso3', ''))),
                        'total_lines': int(c.get('total_positions', 0) or 0),
                        'total_positions': int(c.get('total_positions', 0) or 0),
                        'chapters_covered': c.get('chapters_covered', 0),
                        'has_nomenclature_map': False,
                    }
                    for c in pg_countries
                ]
                _available_countries_cache = countries
                return countries
            _log_etl_fallback('get_available_countries', 'ALL', reason='postgres-miss')
        except Exception as e:
            _log_etl_fallback('get_available_countries', 'ALL', reason=f'postgres-error: {e}')

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
