"""
ECOWAS Member States Tariff Scraper
====================================
Generates tariff files for ECOWAS member states using the official ECOWAS
Common External Tariff (TEC CEDEAO) nomenclature with country-specific
national taxes verified from official government sources.

Source nomenclature: ECOWAS TEC (Règlement C/REG.16/12/21)
  - Same HS codes and DD rates for all 15 ECOWAS member states
  - Downloaded from GUCE CIV portal (official CEDEAO nomenclature)

Country-specific taxes verified from:
  - Benin: douanes.gouv.bj, impots.finances.gouv.bj (TVA 18%)
  - Burkina Faso: dgi.bf, servicepublic.gov.bf (TVA 18%)
  - Mali: douanes.gouv.ml, DGI Mali (TVA 18%)
  - Niger: impots.gouv.ne, service-public.ne (TVA 19%)
  - Togo: otr.tg (TVA 18%)
  - Guinea: dgd.gov.gn, dgi.gov.gn (TVA 18%)

Note: Mali, Burkina Faso, and Niger left ECOWAS (Jan 2025) to form AES
(Alliance des États du Sahel). They still use the same TEC nomenclature
but replaced PCC CEDEAO with PC-AES at the same 0.5% rate.
"""

import requests
import json
import os
import re
import logging
import time
import xlrd
from typing import Dict, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GUCE_DOWNLOAD_URL = "https://guce.gouv.ci/customs/tariff/download"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')

COUNTRY_CONFIGS = {
    'BEN': {
        'country': 'BEN',
        'country_name': 'Bénin',
        'source': 'douanes.gouv.bj + TEC CEDEAO',
        'source_url': 'https://douanes.gouv.bj/tarif-douane/',
        'currency': 'XOF (FCFA)',
        'tva_rate': 18.0,
        'tva_name': 'Taxe sur la Valeur Ajoutée',
        'tva_base': 'CIF + DD + RS + PCS',
        'is_uemoa': True,
        'is_aes': False,
        'national_taxes': {
            'RS': {'code': 'RS', 'name': 'Redevance Statistique', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCS': {'code': 'PCS', 'name': 'Prélèvement Communautaire de Solidarité (UEMOA)', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCC': {'code': 'PCC', 'name': 'Prélèvement Communautaire CEDEAO', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
            'PUA': {'code': 'PUA', 'name': "Prélèvement Union Africaine", 'rate': 0.2, 'type': 'ad_valorem', 'base': 'CIF'},
        },
        'notes': [
            "Nomenclature: TEC CEDEAO (Règlement C/REG.16/12/21) - identique pour les 15 États membres",
            "Droits de douane: TEC CEDEAO (5 bandes: 0%, 5%, 10%, 20%, 35%)",
            "Taxes nationales: RS (1%), PCS UEMOA (1%), PCC CEDEAO (0.5%), PUA (0.2%) - source douanes.gouv.bj",
            "TVA: 18% taux standard - exemptions spécifiques selon Code Général des Impôts (Loi n°2021-15)",
            "Source officielle: douanes.gouv.bj + impots.finances.gouv.bj",
        ],
    },
    'BFA': {
        'country': 'BFA',
        'country_name': 'Burkina Faso',
        'source': 'dgi.bf + TEC CEDEAO',
        'source_url': 'https://dgi.bf/',
        'currency': 'XOF (FCFA)',
        'tva_rate': 18.0,
        'tva_name': 'Taxe sur la Valeur Ajoutée',
        'tva_base': 'CIF + DD + RS + PCS',
        'is_uemoa': True,
        'is_aes': True,
        'national_taxes': {
            'RS': {'code': 'RS', 'name': 'Redevance Statistique', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCS': {'code': 'PCS', 'name': 'Prélèvement Communautaire de Solidarité (UEMOA)', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PC_AES': {'code': 'PC-AES', 'name': 'Prélèvement Confédéral AES', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
        },
        'notes': [
            "Nomenclature: basée sur le TEC CEDEAO - le Burkina Faso utilise toujours cette nomenclature",
            "Droits de douane: TEC CEDEAO (5 bandes: 0%, 5%, 10%, 20%, 35%)",
            "Le Burkina Faso a quitté la CEDEAO (janv. 2025) pour l'Alliance des États du Sahel (AES)",
            "Taxes nationales: RS (1%), PCS UEMOA (1%), PC-AES (0.5% remplace PCC CEDEAO) - source dgi.bf",
            "TVA: 18% taux standard (taux réduits 10% et 2% pour certains secteurs) - source servicepublic.gov.bf",
            "Source officielle: dgi.bf + servicepublic.gov.bf",
        ],
    },
    'MLI': {
        'country': 'MLI',
        'country_name': 'Mali',
        'source': 'douanes.gouv.ml + TEC CEDEAO',
        'source_url': 'https://douanes.gouv.ml/',
        'currency': 'XOF (FCFA)',
        'tva_rate': 18.0,
        'tva_name': 'Taxe sur la Valeur Ajoutée',
        'tva_base': 'CIF + DD + RS + PCS',
        'is_uemoa': True,
        'is_aes': True,
        'national_taxes': {
            'RS': {'code': 'RS', 'name': 'Redevance Statistique', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCS': {'code': 'PCS', 'name': 'Prélèvement Communautaire de Solidarité (UEMOA)', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PC_AES': {'code': 'PC-AES', 'name': 'Prélèvement Confédéral AES', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
        },
        'notes': [
            "Nomenclature: basée sur le TEC CEDEAO - le Mali utilise toujours cette nomenclature",
            "Droits de douane: TEC CEDEAO (5 bandes: 0%, 5%, 10%, 20%, 35%)",
            "Le Mali a quitté la CEDEAO (janv. 2025) pour l'Alliance des États du Sahel (AES)",
            "Taxes nationales: RS (1%), PCS UEMOA (1%), PC-AES (0.5% remplace PCC CEDEAO) - source douanes.gouv.ml",
            "TVA: 18% taux standard - source Direction Générale des Impôts du Mali",
            "Source officielle: douanes.gouv.ml + DGI Mali",
        ],
    },
    'NER': {
        'country': 'NER',
        'country_name': 'Niger',
        'source': 'impots.gouv.ne + TEC CEDEAO',
        'source_url': 'https://www.impots.gouv.ne/',
        'currency': 'XOF (FCFA)',
        'tva_rate': 19.0,
        'tva_name': 'Taxe sur la Valeur Ajoutée',
        'tva_base': 'CIF + DD + RS + PCS',
        'is_uemoa': True,
        'is_aes': True,
        'national_taxes': {
            'RS': {'code': 'RS', 'name': 'Redevance Statistique', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCS': {'code': 'PCS', 'name': 'Prélèvement Communautaire de Solidarité (UEMOA)', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PC_AES': {'code': 'PC-AES', 'name': 'Prélèvement Confédéral AES', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
        },
        'notes': [
            "Nomenclature: basée sur le TEC CEDEAO - le Niger utilise toujours cette nomenclature",
            "Droits de douane: TEC CEDEAO (5 bandes: 0%, 5%, 10%, 20%, 35%)",
            "Le Niger a quitté la CEDEAO (janv. 2025) pour l'Alliance des États du Sahel (AES)",
            "Taxes nationales: RS (1%), PCS UEMOA (1%), PC-AES (0.5% remplace PCC CEDEAO) - source impots.gouv.ne",
            "TVA: 19% taux standard (taxe numérique 19% depuis janv. 2025) - source service-public.ne",
            "Source officielle: impots.gouv.ne + service-public.ne",
        ],
    },
    'TGO': {
        'country': 'TGO',
        'country_name': 'Togo',
        'source': 'otr.tg + TEC CEDEAO',
        'source_url': 'https://www.otr.tg/',
        'currency': 'XOF (FCFA)',
        'tva_rate': 18.0,
        'tva_name': 'Taxe sur la Valeur Ajoutée',
        'tva_base': 'CIF + DD + RS + PCS',
        'is_uemoa': True,
        'is_aes': False,
        'national_taxes': {
            'RS': {'code': 'RS', 'name': 'Redevance Statistique', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCS': {'code': 'PCS', 'name': 'Prélèvement Communautaire de Solidarité (UEMOA)', 'rate': 1.0, 'type': 'ad_valorem', 'base': 'CIF'},
            'PCC': {'code': 'PCC', 'name': 'Prélèvement Communautaire CEDEAO', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
            'PUA': {'code': 'PUA', 'name': "Prélèvement Union Africaine", 'rate': 0.2, 'type': 'ad_valorem', 'base': 'CIF'},
        },
        'notes': [
            "Nomenclature: TEC CEDEAO (Règlement C/REG.16/12/21) - identique pour les 15 États membres",
            "Droits de douane: TEC CEDEAO (5 bandes: 0%, 5%, 10%, 20%, 35%)",
            "Taxes nationales: RS (1%), PCS UEMOA (1%), PCC CEDEAO (0.5%), PUA (0.2%) - source otr.tg",
            "TVA: 18% taux unique - source Office Togolais des Recettes (OTR)",
            "Source officielle: otr.tg",
        ],
    },
    'GIN': {
        'country': 'GIN',
        'country_name': 'Guinée',
        'source': 'dgd.gov.gn + TEC CEDEAO',
        'source_url': 'https://dgd.gov.gn/',
        'currency': 'GNF (Franc Guinéen)',
        'tva_rate': 18.0,
        'tva_name': 'Taxe sur la Valeur Ajoutée',
        'tva_base': 'CIF + DD',
        'is_uemoa': False,
        'is_aes': False,
        'national_taxes': {
            'PCC': {'code': 'PCC', 'name': 'Prélèvement Communautaire CEDEAO', 'rate': 0.5, 'type': 'ad_valorem', 'base': 'CIF'},
        },
        'notes': [
            "Nomenclature: TEC CEDEAO (Règlement C/REG.16/12/21) - identique pour les 15 États membres",
            "Droits de douane: TEC CEDEAO (DFI - Droit Fiscal d'Importation: 0%, 5%, 10%, 20%)",
            "La Guinée n'est PAS membre de l'UEMOA - pas de PCS ni RS UEMOA",
            "Taxes nationales: PCC CEDEAO (0.5%) - source dgd.gov.gn",
            "TVA: 18% taux standard - source dgi.gov.gn",
            "Source officielle: dgd.gov.gn + dgi.gov.gn",
        ],
    },
}


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


def build_country_taxes(dd_rate: float, tva_rate: float, config: dict) -> Tuple[dict, list]:
    taxes = {'DD': dd_rate}
    is_aes = config.get('is_aes', False)
    if is_aes:
        dd_label = 'Droit de Douane (ex-TEC CEDEAO, nomenclature maintenue par AES)'
    else:
        dd_label = 'Droit de Douane (TEC CEDEAO)'

    taxes_detail = [{
        'tax_code': 'DD',
        'tax_name': dd_label,
        'rate': dd_rate,
        'rate_type': 'ad_valorem',
        'base': 'CIF',
    }]

    for key, tax_info in config['national_taxes'].items():
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
            'tax_name': config['tva_name'],
            'rate': tva_rate,
            'rate_type': 'ad_valorem',
            'base': config['tva_base'],
        })

    return taxes, taxes_detail


def generate_country_tariffs(country_code: str, xls_path: str) -> List[dict]:
    config = COUNTRY_CONFIGS[country_code]
    logger.info(f"Generating tariffs for {config['country_name']} ({country_code})")

    wb = xlrd.open_workbook(xls_path)
    ws = wb.sheet_by_name('Sheet 1')

    positions = []
    seen_codes = set()
    stats = {
        'total_rows': 0,
        'skipped_no_code': 0,
        'skipped_header_only': 0,
        'skipped_duplicate': 0,
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

        tva_rate = config['tva_rate']
        taxes, taxes_detail = build_country_taxes(dd_rate, tva_rate, config)

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

        trade_bloc = 'AES' if config.get('is_aes') else 'ECOWAS/CEDEAO'
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
            'source': config['source'],
            'data_type': 'regional_cet_with_national_taxes',
            'trade_bloc': trade_bloc,
            'source_verified': config['source_url'],
        }

        positions.append(position)
        seen_codes.add(code_clean)
        stats['parsed'] += 1

    stats['chapters'] = len(stats['chapters'])
    logger.info(f"  {config['country_name']}: {stats['parsed']} positions, {stats['chapters']} chapters")
    return positions


def save_country_results(country_code: str, positions: List[dict]):
    config = COUNTRY_CONFIGS[country_code]
    output_file = os.path.join(OUTPUT_DIR, f'{country_code}_tariffs.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    tax_legend = {'DD': 'Droit de Douane (TEC CEDEAO: 0%, 5%, 10%, 20%, 35%)'}
    for key, tax_info in config['national_taxes'].items():
        tax_legend[tax_info['code']] = f"{tax_info['name']} ({tax_info['rate']}%)"
    tax_legend['TVA'] = f"{config['tva_name']} ({config['tva_rate']}%)"

    result = {
        'country': country_code,
        'country_name': config['country_name'],
        'source': config['source'],
        'source_url': config['source_url'],
        'method': 'ecowas_tec_with_national_taxes',
        'hs_level': 'national_sub_positions',
        'nomenclature': 'ECOWAS CET (TEC CEDEAO) + National Taxes',
        'data_type': 'regional_cet_with_national_taxes',
        'currency': config['currency'],
        'extracted_at': datetime.now().isoformat(),
        'total_positions': len(positions),
        'positions': positions,
        'tax_legend': tax_legend,
        'notes': config['notes'],
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"  Saved {len(positions)} positions to {output_file}")
    return output_file


def run_scraper(countries: List[str] = None):
    if countries is None:
        countries = list(COUNTRY_CONFIGS.keys())

    logger.info("=" * 60)
    logger.info("ECOWAS Member States Tariff Generation")
    logger.info(f"Countries: {', '.join(countries)}")
    logger.info("=" * 60)

    start_time = time.time()
    xls_path = download_ecowas_nomenclature('/tmp/guce_tariff.xls')

    results = {}
    for cc in countries:
        if cc not in COUNTRY_CONFIGS:
            logger.warning(f"Unknown country code: {cc}")
            continue

        positions = generate_country_tariffs(cc, xls_path)
        save_country_results(cc, positions)

        dd_dist = {}
        for p in positions:
            dd = p['taxes'].get('DD', 'N/A')
            dd_dist[dd] = dd_dist.get(dd, 0) + 1

        results[cc] = {
            'positions': len(positions),
            'dd_distribution': dict(sorted(dd_dist.items())),
            'tva_rate': COUNTRY_CONFIGS[cc]['tva_rate'],
        }

    elapsed = time.time() - start_time
    logger.info(f"\nAll countries generated in {elapsed:.1f}s")
    for cc, info in results.items():
        logger.info(f"  {cc}: {info['positions']} positions, TVA {info['tva_rate']}%")
        logger.info(f"    DD distribution: {info['dd_distribution']}")

    return results


if __name__ == '__main__':
    run_scraper()
