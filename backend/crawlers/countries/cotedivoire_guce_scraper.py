"""
Côte d'Ivoire Tariff Scraper (guce.gouv.ci)
=============================================
Extracts national tariff positions from the GUCE (Guichet Unique du Commerce
Extérieur) official tariff database.

Source: https://guce.gouv.ci/customs/tariff/download
Official reference: ECOWAS CET with national sub-positions (CEDEAO TEC)

Côte d'Ivoire tariff structure:
- DD (Droit de Douane): 0%, 5%, 10%, 20%, 35% (ECOWAS CET bands)
- TVA (Taxe sur la Valeur Ajoutée): 0%, 9%, 18%
- DUS (Droit Unique de Sortie): Export tax on specific goods
- TUB (Taxe Unique sur les Boissons): Petroleum products, beverages
- TSB_PT (Taxe Spéciale Boissons / Prélèvement Transformation): Alcohol, beverages
- PSV (Prélèvement Spécial de Viabilité): Special viability levy on meat
- TUF (Taxe Unique sur les Fuels): Fuel tax
- PCS (Prélèvement Communautaire de Solidarité): 0.8% community levy
- PUA (Prélèvement Union Africaine): 0.2% AU import tax
- RS (Redevance Statistique): 1% statistical duty

Method: Downloads official Excel tariff file from GUCE portal and parses it.
This is the most reliable source as it contains the complete national nomenclature
with all tax components.

Output: ~6,100+ positions (HS8/HS10 national sub-positions)
"""

import requests
import json
import os
import re
import logging
import time
import xlrd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOAD_URL = "https://guce.gouv.ci/customs/tariff/download"
SEARCH_URL = "https://guce.gouv.ci/customs/tariff/search"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'CIV_tariffs.json')

TAX_COLUMN_MAP = {
    'TAR_T01': {'code': 'DD', 'name': 'Droit de Douane', 'type': 'ad_valorem'},
    'TAR_T02': {'code': 'TUB', 'name': 'Taxe Unique sur les Boissons', 'type': 'ad_valorem'},
    'TAR_T03': {'code': 'TVA', 'name': 'Taxe sur la Valeur Ajoutée', 'type': 'ad_valorem'},
    'TAR_T04': {'code': 'DUS', 'name': 'Droit Unique de Sortie', 'type': 'ad_valorem'},
    'TAR_T05': {'code': 'TSB_PT', 'name': 'Taxe Spéciale Boissons / Prélèvement Transformation', 'type': 'ad_valorem'},
    'TAR_T06': {'code': 'PSV', 'name': 'Prélèvement Spécial de Viabilité', 'type': 'specific'},
    'TAR_T07': {'code': 'TUF', 'name': 'Taxe Unique sur les Fuels', 'type': 'ad_valorem'},
    'TAR_T11': {'code': 'SPEC', 'name': 'Montant Spécifique (FCFA/unité)', 'type': 'specific'},
}


def download_tariff_excel(output_path: str = '/tmp/guce_tariff.xls') -> str:
    logger.info("Downloading official tariff Excel from GUCE portal...")
    resp = requests.get(DOWNLOAD_URL, params={'lang': 'fr'}, timeout=120,
                       headers={'User-Agent': 'Mozilla/5.0'})
    resp.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(resp.content)

    size_mb = len(resp.content) / (1024 * 1024)
    logger.info(f"Downloaded {size_mb:.1f} MB to {output_path}")
    return output_path


def parse_hs_code(raw_code: str) -> Tuple[str, str, bool]:
    if not raw_code:
        return '', '', False
    raw = str(raw_code).strip()
    has_wildcard = '*' in raw
    clean = re.sub(r'[^0-9]', '', raw)
    if len(clean) < 6:
        return '', '', False

    parts = [clean[:4]]
    if len(clean) > 4:
        parts.append(clean[4:6])
    if len(clean) > 6:
        parts.append(clean[6:8])
    if len(clean) > 8:
        parts.append(clean[8:])
    dotted = '.'.join(parts)

    return clean, dotted, has_wildcard


def extract_taxes(row_data: dict, headers: list, ws, row_idx: int) -> Tuple[dict, list]:
    taxes = {}
    taxes_detail = []

    for col_idx in range(28, min(43, len(headers))):
        col_name = headers[col_idx]
        if col_name not in TAX_COLUMN_MAP:
            continue

        val = ws.cell_value(row_idx, col_idx)
        if val is None or str(val).strip() == '' or str(val).strip().upper() == 'CALCULEZ':
            continue

        try:
            rate = float(val)
        except (ValueError, TypeError):
            continue

        tax_info = TAX_COLUMN_MAP[col_name]
        taxes[tax_info['code']] = rate

        taxes_detail.append({
            'tax_code': tax_info['code'],
            'tax_name': tax_info['name'],
            'rate': rate,
            'rate_type': tax_info['type'],
            'base': 'CIF' if tax_info['code'] in ('DD', 'TVA', 'TUB', 'TSB_PT', 'TUF') else 'variable'
        })

    return taxes, taxes_detail


def parse_excel_tariff(xls_path: str) -> List[dict]:
    logger.info(f"Parsing tariff Excel file: {xls_path}")
    wb = xlrd.open_workbook(xls_path)
    ws = wb.sheet_by_name('Sheet 1')
    headers = [ws.cell_value(0, j) for j in range(ws.ncols)]

    positions = []
    seen_codes = set()
    stats = {
        'total_rows': 0,
        'skipped_no_code': 0,
        'skipped_duplicate': 0,
        'skipped_no_tax': 0,
        'skipped_header_only': 0,
        'parsed': 0,
        'chapters': set(),
    }

    for r in range(1, ws.nrows):
        stats['total_rows'] += 1
        raw_code = str(ws.cell_value(r, 11)).strip()

        if not raw_code or raw_code == '0000011111':
            stats['skipped_no_code'] += 1
            continue

        code_clean, code_dotted, has_wildcard = parse_hs_code(raw_code)

        if has_wildcard or len(code_clean) < 10:
            stats['skipped_header_only'] += 1
            continue

        if code_clean in seen_codes:
            stats['skipped_duplicate'] += 1
            continue

        desc = ws.cell_value(r, 12)
        if not desc or not str(desc).strip():
            desc = ws.cell_value(r, 21)
        if not desc or not str(desc).strip():
            desc = ws.cell_value(r, 13)
        if not desc or not str(desc).strip():
            desc = ws.cell_value(r, 10)

        desc = str(desc).strip() if desc else ''
        desc = desc.lstrip('- ')

        taxes, taxes_detail = extract_taxes({}, headers, ws, r)

        if not taxes:
            stats['skipped_no_tax'] += 1
            continue

        chapter = code_clean[:2]
        stats['chapters'].add(chapter)

        hs6_code = ws.cell_value(r, 9) or ''
        hs6_desc = ws.cell_value(r, 10) or ''
        hs4_code = ws.cell_value(r, 6) or ''
        hs4_desc = ws.cell_value(r, 7) or ''
        hs2_code = ws.cell_value(r, 3) or ''
        hs2_desc = ws.cell_value(r, 4) or ''

        unit_raw = ws.cell_value(r, 22) or ''
        unit = str(unit_raw).strip() if unit_raw else ''

        position = {
            'code': code_dotted,
            'code_clean': code_clean,
            'code_length': len(code_clean),
            'designation': desc,
            'chapter': chapter,
            'hs2': str(hs2_code).strip(),
            'hs2_desc': str(hs2_desc).strip(),
            'hs4': str(hs4_code).strip(),
            'hs4_desc': str(hs4_desc).strip(),
            'hs6': str(hs6_code).strip().replace('.0', ''),
            'hs6_desc': str(hs6_desc).strip(),
            'unit': unit,
            'taxes': taxes,
            'taxes_detail': taxes_detail,
            'source': 'guce.gouv.ci',
            'data_type': 'national',
        }

        positions.append(position)
        seen_codes.add(code_clean)
        stats['parsed'] += 1

    stats['chapters'] = len(stats['chapters'])
    logger.info(f"Parsed {stats['parsed']} positions from {stats['chapters']} chapters")
    logger.info(f"Stats: {stats}")
    return positions


def save_results(positions: List[dict], output_file: str = OUTPUT_FILE):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    result = {
        'country': 'CIV',
        'country_name': "Côte d'Ivoire",
        'source': 'guce.gouv.ci',
        'source_url': 'https://guce.gouv.ci/customs/tariff',
        'method': 'excel_download',
        'hs_level': 'national_sub_positions',
        'nomenclature': 'ECOWAS CET + National Sub-positions',
        'data_type': 'national',
        'currency': 'XOF (FCFA)',
        'extracted_at': datetime.now().isoformat(),
        'total_positions': len(positions),
        'positions': positions,
        'tax_legend': {
            'DD': 'Droit de Douane (ECOWAS CET: 0%, 5%, 10%, 20%, 35%)',
            'TVA': 'Taxe sur la Valeur Ajoutée (0%, 9%, 18%)',
            'DUS': 'Droit Unique de Sortie (export)',
            'TUB': 'Taxe Unique sur les Boissons',
            'TSB_PT': 'Taxe Spéciale Boissons / Prélèvement Transformation',
            'PSV': 'Prélèvement Spécial de Viabilité (FCFA/kg)',
            'TUF': 'Taxe Unique sur les Fuels',
            'SPEC': 'Montant Spécifique (FCFA/unité)',
            'PCS': 'Prélèvement Communautaire de Solidarité (0.8%)',
            'PUA': "Prélèvement Union Africaine (0.2%)",
            'RS': 'Redevance Statistique (1%)',
        },
        'notes': [
            "Données extraites du fichier Excel officiel du portail GUCE",
            "Les taxes PCS (0.8%), PUA (0.2%) et RS (1%) s'appliquent à toutes les importations",
            "La Côte d'Ivoire applique le TEC CEDEAO (5 bandes tarifaires)",
            "TVA à taux réduit (9%) sur certains produits de première nécessité",
        ]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(positions)} positions to {output_file}")
    return output_file


def run_scraper():
    logger.info("=" * 60)
    logger.info("Côte d'Ivoire GUCE Tariff Extraction")
    logger.info("=" * 60)

    start_time = time.time()

    xls_path = '/tmp/guce_tariff.xls'
    if not os.path.exists(xls_path):
        download_tariff_excel(xls_path)
    else:
        logger.info(f"Using cached Excel file: {xls_path}")

    positions = parse_excel_tariff(xls_path)

    output_file = save_results(positions)

    elapsed = time.time() - start_time
    logger.info(f"\nExtraction complete in {elapsed:.1f}s")
    logger.info(f"Total positions: {len(positions)}")
    logger.info(f"Output: {output_file}")

    dd_dist = {}
    for p in positions:
        dd = p['taxes'].get('DD', 'N/A')
        dd_dist[dd] = dd_dist.get(dd, 0) + 1
    logger.info(f"DD distribution: {dict(sorted(dd_dist.items()))}")

    tva_dist = {}
    for p in positions:
        tva = p['taxes'].get('TVA', 'N/A')
        tva_dist[str(tva)] = tva_dist.get(str(tva), 0) + 1
    logger.info(f"TVA distribution: {dict(sorted(tva_dist.items()))}")

    return positions


if __name__ == '__main__':
    run_scraper()
