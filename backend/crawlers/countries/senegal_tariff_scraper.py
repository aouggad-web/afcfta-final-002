"""
Senegal Tariff Scraper (douanes.sn / ECOWAS TEC)
=================================================
Extracts national tariff positions for Senegal from the ECOWAS Common External
Tariff (TEC CEDEAO) nomenclature with Senegal-specific national taxes.

Source: ECOWAS TEC nomenclature (official CEDEAO regulation C/REG.16/12/21)
Tax rates: douanes.sn (official Senegal customs authority)

Senegal tariff structure (per douanes.sn/ndn722/):
- DD (Droit de Douane): 0%, 5%, 10%, 20%, 35% (ECOWAS CET bands)
- RS (Redevance Statistique): 1% on CIF value
- PCS (Prélèvement Communautaire de Solidarité UEMOA): 1% (was 0.8%, updated)
- PCC (Prélèvement Communautaire CEDEAO): 0.5% on CIF value
- PUA (Prélèvement Union Africaine): 0.2% on CIF value
- TVA: 18% standard rate (0% on exempt goods)

Method: Uses the official ECOWAS TEC nomenclature (from GUCE CIV Excel which is
the same ECOWAS nomenclature for all 15 member states) and applies Senegal-specific
national taxes as published by douanes.sn.

Output: ~6,100+ positions (HS10 national sub-positions)
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

GUCE_DOWNLOAD_URL = "https://guce.gouv.ci/customs/tariff/download"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'SEN_tariffs.json')

SENEGAL_TAXES = {
    'RS': {'code': 'RS', 'name': 'Redevance Statistique', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
    'PCS': {'code': 'PCS', 'name': 'Prélèvement Communautaire de Solidarité (UEMOA)', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
    'PCC': {'code': 'PCC', 'name': 'Prélèvement Communautaire CEDEAO', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
    'PUA': {'code': 'PUA', 'name': "Prélèvement Union Africaine", 'rate': 0.2, 'type': 'ad_valorem', 'base': 'CIF'},
}

TVA_RATE = 18.0

TVA_EXEMPT_HS4 = set()


def download_ecowas_nomenclature(output_path: str = '/tmp/guce_tariff.xls') -> str:
    if os.path.exists(output_path):
        logger.info(f"Using cached ECOWAS nomenclature file: {output_path}")
        return output_path

    logger.info("Downloading ECOWAS TEC nomenclature from GUCE portal...")
    resp = requests.get(GUCE_DOWNLOAD_URL, params={'lang': 'fr'}, timeout=120,
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


def build_senegal_taxes(dd_rate: float, tva_rate: float) -> Tuple[dict, list]:
    taxes = {'DD': dd_rate}
    taxes_detail = [{
        'tax_code': 'DD',
        'tax_name': 'Droit de Douane (TEC CEDEAO)',
        'rate': dd_rate,
        'rate_type': 'ad_valorem',
        'base': 'CIF',
    }]

    for key, tax_info in SENEGAL_TAXES.items():
        taxes[tax_info['code']] = tax_info['rate']
        taxes_detail.append({
            'tax_code': tax_info['code'],
            'tax_name': tax_info['name'],
            'rate': tax_info['rate'],
            'rate_type': tax_info['type'],
            'base': tax_info['base'],
        })

    if tva_rate > 0:
        taxes['TVA'] = tva_rate
        taxes_detail.append({
            'tax_code': 'TVA',
            'tax_name': 'Taxe sur la Valeur Ajoutée',
            'rate': tva_rate,
            'rate_type': 'ad_valorem',
            'base': 'CIF + DD + RS + PCS',
        })

    return taxes, taxes_detail


def parse_ecowas_nomenclature(xls_path: str) -> List[dict]:
    logger.info(f"Parsing ECOWAS nomenclature for Senegal: {xls_path}")
    wb = xlrd.open_workbook(xls_path)
    ws = wb.sheet_by_name('Sheet 1')
    headers = [ws.cell_value(0, j) for j in range(ws.ncols)]

    positions = []
    seen_codes = set()
    stats = {
        'total_rows': 0,
        'skipped_no_code': 0,
        'skipped_header_only': 0,
        'skipped_duplicate': 0,
        'parsed': 0,
        'tva_exempt': 0,
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

        dd_val = ws.cell_value(r, 28)
        try:
            dd_rate = float(dd_val)
        except (ValueError, TypeError):
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

        hs4 = code_clean[:4]
        is_tva_exempt = hs4 in TVA_EXEMPT_HS4
        tva_rate = 0.0 if is_tva_exempt else TVA_RATE
        if is_tva_exempt:
            stats['tva_exempt'] += 1

        taxes, taxes_detail = build_senegal_taxes(dd_rate, tva_rate)

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
            'source': 'douanes.sn + TEC CEDEAO',
            'data_type': 'regional_cet_with_national_taxes',
        }

        positions.append(position)
        seen_codes.add(code_clean)
        stats['parsed'] += 1

    stats['chapters'] = len(stats['chapters'])
    logger.info(f"Parsed {stats['parsed']} positions from {stats['chapters']} chapters")
    logger.info(f"TVA exempt positions: {stats['tva_exempt']}")
    logger.info(f"Stats: {stats}")
    return positions


def save_results(positions: List[dict], output_file: str = OUTPUT_FILE):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    result = {
        'country': 'SEN',
        'country_name': 'Sénégal',
        'source': 'douanes.sn + TEC CEDEAO',
        'source_url': 'https://www.douanes.sn/ndn722/',
        'method': 'ecowas_tec_with_national_taxes',
        'hs_level': 'national_sub_positions',
        'nomenclature': 'ECOWAS CET (TEC CEDEAO) + Senegal National Taxes',
        'data_type': 'regional_cet_with_national_taxes',
        'currency': 'XOF (FCFA)',
        'extracted_at': datetime.now().isoformat(),
        'total_positions': len(positions),
        'positions': positions,
        'tax_legend': {
            'DD': 'Droit de Douane (TEC CEDEAO: 0%, 5%, 10%, 20%, 35%)',
            'RS': 'Redevance Statistique (1% sur valeur CAF)',
            'PCS': 'Prélèvement Communautaire de Solidarité UEMOA (1%)',
            'PCC': 'Prélèvement Communautaire CEDEAO (0.5%)',
            'PUA': "Prélèvement Union Africaine (0.2%)",
            'TVA': 'Taxe sur la Valeur Ajoutée (18% taux unique)',
        },
        'notes': [
            "Nomenclature: TEC CEDEAO (Règlement C/REG.16/12/21) - identique pour les 15 États membres",
            "Droits de douane: identiques au TEC CEDEAO (5 bandes: 0%, 5%, 10%, 20%, 35%)",
            "Taxes nationales: RS (1%), PCS UEMOA (1%), PCC CEDEAO (0.5%), PUA (0.2%) - source douanes.sn",
            "TVA: 18% taux unique appliqué par défaut - les exemptions spécifiques nécessitent vérification auprès de douanes.sn",
            "Les codes HS et désignations proviennent de la nomenclature officielle CEDEAO",
        ]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(positions)} positions to {output_file}")
    return output_file


def run_scraper():
    logger.info("=" * 60)
    logger.info("Senegal Tariff Extraction (ECOWAS TEC + National Taxes)")
    logger.info("=" * 60)

    start_time = time.time()

    xls_path = download_ecowas_nomenclature('/tmp/guce_tariff.xls')
    positions = parse_ecowas_nomenclature(xls_path)
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
