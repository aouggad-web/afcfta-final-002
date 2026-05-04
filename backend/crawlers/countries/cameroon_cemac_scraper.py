"""
Cameroon Tariff Scraper (CEMAC TEC PDF)
=======================================
Extracts national tariff positions for Cameroon from the official CEMAC
(Communauté Économique et Monétaire de l'Afrique Centrale) customs tariff PDF.

Source: Official CEMAC Tarif des Douanes PDF
  - cameroontradeportal.cm (Cameroon Trade Portal)
  - douanes.ga (Gabon Customs - same CEMAC document)

Cameroon tariff structure:
- DD (Droit de Douane): 5%, 10%, 20%, 30% (CEMAC CET bands)
- TCI (Taxe Communautaire d'Intégration): 1% on CIF value
- TVA: 19.25% (17.5% base + 10% CAC) - "TN" in PDF, "EXO" = exempt
- DA (Droit d'Accise): 5-50% on specific products (marked ** in PDF)
- CAC (Centimes Additionnels Communaux): included in TVA rate
- RI (Redevance Informatique): 0.45% on CIF (capped at 15,000 XAF)

Method: Downloads official CEMAC tariff PDF and extracts HS8 codes, product
designations, and tax rates using PyMuPDF text position analysis.

Output: ~5,400+ positions (HS8 codes)
"""

import requests
import json
import os
import re
import logging
import time
import fitz
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_URLS = [
    "https://douanes.ga/med/pdf/tarif-des-douanes-de-la-cemac-version-originale-pdf-210608020644.pdf",
    "https://www.cameroontradeportal.cm/tradeportal/templates/Tip_accueil/docs/R%C3%A9formes%20nationales/tarif_des_douanes%20nomenclature.pdf",
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'CMR_tariffs.json')

HS8_PATTERN = re.compile(r'^\d{4}\.\d{2}\.\d{2}\.?$')
HS6_PATTERN = re.compile(r'^\d{2}\.\d{2}$')

TVA_RATE = 19.25
TCI_RATE = 1.0
RI_RATE = 0.45

CAMEROON_FIXED_TAXES = {
    'TCI': {'code': 'TCI', 'name': "Taxe Communautaire d'Intégration (CEMAC)", 'rate': TCI_RATE, 'type': 'ad_valorem', 'base': 'CIF'},
    'RI': {'code': 'RI', 'name': 'Redevance Informatique', 'rate': RI_RATE, 'type': 'ad_valorem', 'base': 'CIF (plafond 15 000 XAF)'},
}


def download_cemac_pdf(output_path: str = '/tmp/cemac_tariff.pdf') -> str:
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        if size > 1_000_000:
            logger.info(f"Using cached CEMAC PDF: {output_path} ({size/1024/1024:.1f} MB)")
            return output_path

    for url in PDF_URLS:
        try:
            logger.info(f"Downloading CEMAC tariff PDF from {url}...")
            resp = requests.get(url, timeout=120, headers={'User-Agent': 'Mozilla/5.0'})
            resp.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(resp.content)

            size_mb = len(resp.content) / (1024 * 1024)
            logger.info(f"Downloaded {size_mb:.1f} MB to {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")

    raise RuntimeError("Could not download CEMAC tariff PDF from any source")


def extract_page_data(page) -> List[dict]:
    blocks = page.get_text("dict")
    items = []

    for block in blocks["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                txt = span["text"].strip()
                if not txt:
                    continue
                x0 = span["bbox"][0]
                y0 = span["bbox"][1]
                items.append({'text': txt, 'x': x0, 'y': y0})

    return items


def parse_page_tariffs(items: List[dict]) -> tuple:
    codes = []
    designations = []
    dd_rates = []
    tva_values = []
    accise_flags = []

    HEADER_TEXTS = {'NUMERO', 'DU', 'TARIF', 'DESIGNATION DES PRODUITS',
                    'DROIT', 'DE', 'DOUANE', 'DISPOSI-', 'TIONS', 'SPECIALES',
                    'TVA', "D'ACCISE"}

    for item in items:
        txt = item['text']
        x = item['x']
        y = item['y']

        if x < 75:
            cleaned = txt.rstrip('.')
            if HS8_PATTERN.match(cleaned):
                codes.append({'code': cleaned, 'y': y})

        elif 75 <= x < 340:
            if (txt not in HEADER_TEXTS
                    and not txt.startswith('Commission de la CEMAC')
                    and not re.match(r'^\d+$', txt)):
                cleaned = txt.rstrip('.')
                if not HS8_PATTERN.match(cleaned) and not HS6_PATTERN.match(cleaned):
                    designations.append({'text': txt, 'y': y})

        elif 340 <= x < 420:
            if '%' in txt:
                rate_str = txt.replace('%', '').replace(' ', '').strip()
                try:
                    rate = float(rate_str)
                    dd_rates.append({'rate': rate, 'y': y})
                except ValueError:
                    pass

        elif 450 <= x < 510:
            if txt in ('TN', 'EXO', 'TX', 'EX'):
                tva_values.append({'value': txt, 'y': y})

        elif x >= 510:
            if txt == '**':
                accise_flags.append({'y': y})

    return codes, designations, dd_rates, tva_values, accise_flags


def _find_nearest(items, y, tolerance=15, key='rate'):
    best = None
    best_dist = tolerance + 1
    for item in items:
        dist = abs(item['y'] - y)
        if dist < best_dist:
            best_dist = dist
            best = item.get(key, item.get('value'))
    return best if best_dist <= tolerance else None


def match_data_to_codes(codes, designations, dd_rates, tva_values, accise_flags):
    results = []

    sorted_codes = sorted(codes, key=lambda c: c['y'])
    sorted_dd = sorted(dd_rates, key=lambda d: d['y'])
    used_dd = set()

    for i, code_item in enumerate(sorted_codes):
        code = code_item['code']
        y = code_item['y']

        y_next = sorted_codes[i + 1]['y'] if i + 1 < len(sorted_codes) else y + 50

        desc_parts = []
        for d in designations:
            if abs(d['y'] - y) < 3 or (d['y'] > y and d['y'] < y_next - 2):
                desc_parts.append(d['text'])

        dd = None
        best_dist = 16
        best_dd_idx = -1
        for j, r in enumerate(sorted_dd):
            if j in used_dd:
                continue
            dist = abs(r['y'] - y)
            if dist < best_dist:
                best_dist = dist
                dd = r['rate']
                best_dd_idx = j
        if best_dd_idx >= 0:
            used_dd.add(best_dd_idx)

        if dd is None and sorted_dd:
            closest = min((r for j, r in enumerate(sorted_dd) if j not in used_dd),
                         key=lambda r: abs(r['y'] - y), default=None)
            if closest and abs(closest['y'] - y) < 30:
                dd = closest['rate']

        tva_status = _find_nearest(tva_values, y, tolerance=15, key='value')

        has_accise = any(abs(a['y'] - y) < 15 for a in accise_flags)

        desc = ' '.join(desc_parts).strip()
        desc = re.sub(r'\.{2,}', '', desc).strip()
        desc = re.sub(r'\s+', ' ', desc).strip()

        if dd is not None:
            results.append({
                'code': code,
                'designation': desc,
                'dd_rate': dd,
                'tva_status': tva_status or 'TN',
                'has_accise': has_accise,
            })

    return results


def build_cameroon_taxes(dd_rate: float, tva_status: str, has_accise: bool) -> Tuple[dict, list]:
    taxes = {'DD': dd_rate}
    taxes_detail = [{
        'tax_code': 'DD',
        'tax_name': 'Droit de Douane (TEC CEMAC)',
        'rate': dd_rate,
        'rate_type': 'ad_valorem',
        'base': 'CIF',
    }]

    for key, tax_info in CAMEROON_FIXED_TAXES.items():
        taxes[tax_info['code']] = tax_info['rate']
        taxes_detail.append({
            'tax_code': tax_info['code'],
            'tax_name': tax_info['name'],
            'rate': tax_info['rate'],
            'rate_type': tax_info['type'],
            'base': tax_info['base'],
        })

    if tva_status in ('TN', 'TX'):
        taxes['TVA'] = TVA_RATE
        taxes_detail.append({
            'tax_code': 'TVA',
            'tax_name': 'Taxe sur la Valeur Ajoutée (incl. 10% CAC)',
            'rate': TVA_RATE,
            'rate_type': 'ad_valorem',
            'base': 'CIF + DD + TCI',
        })

    if has_accise:
        taxes['DA'] = -1
        taxes_detail.append({
            'tax_code': 'DA',
            'tax_name': "Droit d'Accise",
            'rate': -1,
            'rate_type': 'ad_valorem',
            'base': 'CIF',
            'note': 'Taux variable selon le produit (5% à 50%)',
        })

    return taxes, taxes_detail


def _process_page_positions(
    results: List[dict],
    seen_codes: set,
    stats: dict,
) -> List[dict]:
    """Extract and deduplicate tariff positions from a single page's matched rows.

    Args:
        results: Matched rows returned by :func:`match_data_to_codes`.
        seen_codes: Set of already-processed code strings (mutated in place).
        stats: Running extraction statistics dict (mutated in place).

    Returns:
        List of new position dicts extracted from this page.
    """
    positions: List[dict] = []
    for r in results:
        stats['raw_extractions'] += 1

        code_str = r['code'].rstrip('.')
        code_clean = code_str.replace('.', '')

        if code_clean in seen_codes:
            stats['duplicates'] += 1
            continue

        chapter = code_clean[:2]
        stats['chapters'].add(chapter)

        taxes, taxes_detail = build_cameroon_taxes(r['dd_rate'], r['tva_status'], r['has_accise'])

        positions.append({
            'code': code_str,
            'code_clean': code_clean,
            'code_length': len(code_clean),
            'designation': r['designation'],
            'chapter': chapter,
            'hs6': f"{code_clean[:4]}.{code_clean[4:6]}",
            'taxes': taxes,
            'taxes_detail': taxes_detail,
            'source': 'CEMAC Tarif des Douanes (PDF officiel)',
            'data_type': 'regional_cet',
        })
        seen_codes.add(code_clean)
        stats['final_positions'] += 1

    return positions


def parse_pdf(pdf_path: str) -> List[dict]:
    """Parse the official CEMAC customs tariff PDF and return tariff positions.

    Each position dict contains:
    - ``code`` / ``code_clean``: national tariff code
    - ``designation``: French product description
    - ``chapter``: 2-digit HS chapter
    - ``hs6``: dotted HS6 prefix
    - ``taxes`` / ``taxes_detail``: duty and tax breakdown

    Args:
        pdf_path: Filesystem path to the CEMAC tariff PDF.

    Returns:
        List of tariff position dicts. An empty list is returned when the
        file cannot be opened or no usable data is found.
    """
    logger.info("Parsing CEMAC tariff PDF: %s", pdf_path)
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        logger.error("Cannot open PDF %s: %s", pdf_path, exc)
        return []

    all_positions: List[dict] = []
    seen_codes: set = set()
    stats = {
        'total_pages': doc.page_count,
        'pages_with_data': 0,
        'raw_extractions': 0,
        'duplicates': 0,
        'no_dd': 0,
        'final_positions': 0,
        'chapters': set(),
    }

    try:
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                items = extract_page_data(page)
            except Exception as exc:
                logger.warning("Error reading page %d: %s", page_num, exc)
                continue

            if not items:
                continue

            codes, designations, dd_rates, tva_values, accise_flags = parse_page_tariffs(items)
            if not codes:
                continue

            stats['pages_with_data'] += 1
            results = match_data_to_codes(codes, designations, dd_rates, tva_values, accise_flags)
            page_positions = _process_page_positions(results, seen_codes, stats)
            all_positions.extend(page_positions)
    finally:
        doc.close()

    chapters_count = len(stats['chapters'])
    stats['chapters'] = chapters_count
    logger.info(
        "Extracted %d positions from %d pages (chapters: %d, duplicates skipped: %d)",
        stats['final_positions'],
        stats['pages_with_data'],
        chapters_count,
        stats['duplicates'],
    )
    return all_positions


def save_results(positions: List[dict], output_file: str = OUTPUT_FILE):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    result = {
        'country': 'CMR',
        'country_name': 'Cameroun',
        'source': 'CEMAC Tarif des Douanes',
        'source_url': 'https://www.cameroontradeportal.cm',
        'method': 'pdf_extraction',
        'hs_level': 'hs8',
        'nomenclature': 'CEMAC CET (Tarif Extérieur Commun)',
        'data_type': 'regional_cet',
        'currency': 'XAF (FCFA)',
        'extracted_at': datetime.now().isoformat(),
        'total_positions': len(positions),
        'positions': positions,
        'tax_legend': {
            'DD': 'Droit de Douane (TEC CEMAC: 5%, 10%, 20%, 30%)',
            'TCI': "Taxe Communautaire d'Intégration (1%)",
            'TVA': 'Taxe sur la Valeur Ajoutée (19.25% = 17.5% + 10% CAC)',
            'DA': "Droit d'Accise (variable: 5% à 50%)",
            'RI': 'Redevance Informatique (0.45%, plafond 15 000 XAF)',
        },
        'cemac_members': [
            'Cameroun', 'République Centrafricaine', 'République du Congo',
            'Gabon', 'Guinée Équatoriale', 'Tchad'
        ],
        'notes': [
            "Données extraites du PDF officiel du Tarif des Douanes CEMAC",
            "DD: 4 bandes tarifaires CEMAC (5%, 10%, 20%, 30%)",
            "TVA: 19.25% incluant CAC 10% (TN=Taux Normal, EXO=Exonéré)",
            "Droit d'Accise: produits spécifiques marqués ** (alcool, tabac, cosmétiques, véhicules)",
            "Le même tarif CEMAC s'applique aux 6 États membres",
            "Taxes nationales Cameroun: RI (0.45%), TCI (1%)",
        ]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(positions)} positions to {output_file}")
    return output_file


def run_scraper():
    logger.info("=" * 60)
    logger.info("Cameroon CEMAC Tariff Extraction")
    logger.info("=" * 60)

    start_time = time.time()

    pdf_path = download_cemac_pdf('/tmp/cemac_tariff.pdf')
    positions = parse_pdf(pdf_path)
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
