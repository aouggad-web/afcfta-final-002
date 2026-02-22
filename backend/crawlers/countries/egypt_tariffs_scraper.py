"""
Egypt Tariff Scraper (egyptariffs.com)
======================================
Extracts HS10 national tariff positions from egyptariffs.com,
an educational database based on official Egyptian customs data.

Source: egyptariffs.com (based on Egyptian Customs Authority data)
Official reference: Presidential Decree 419/2018, updated through 218/2025

Egypt tariff structure:
- Import Duty (ضريبة الوارد): 0-60% on CIF value (up to 3000% for alcohol)
- VAT (ضريبة القيمة المضافة): Standard 14%
- Customs duties calculated on CIF (Cost + Insurance + Freight)

Key features:
- 8,816 HS10 positions from sitemap
- Structured JSON-LD data with import duty and VAT rates
- Arabic designations with English descriptions
- Trade agreement references (EFTA, Turkey, etc.)

Output: ~8,800 HS10 positions with import duty and VAT rates
"""

import requests
import json
import os
import re
import logging
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SITEMAP_URL = "https://www.egyptariffs.com/sitemap.xml"
BASE_URL = "https://www.egyptariffs.com/tariff/"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'egy_tariffs.json')


class EgyptTariffsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar,en;q=0.5',
        })
        self.positions = []
        self.hs_codes = []
        self.stats = {
            "pages_scraped": 0,
            "total_positions": 0,
            "errors": 0,
            "skipped": 0,
        }

    def _fetch_sitemap(self) -> List[str]:
        logger.info(f"Fetching sitemap from {SITEMAP_URL}")
        resp = self.session.get(SITEMAP_URL, timeout=30)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//ns:loc', ns)

        hs_codes = []
        for url_elem in urls:
            url = url_elem.text
            if '/tariff/' in url:
                code = url.split('/tariff/')[-1].replace('/', '')
                if code and code.isdigit() and len(code) == 10:
                    hs_codes.append(code)

        logger.info(f"Found {len(hs_codes)} HS10 codes in sitemap")
        return hs_codes

    def _parse_json_ld(self, html: str) -> Optional[Dict]:
        json_blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )

        for jb in json_blocks:
            try:
                d = json.loads(jb)
                if d.get('@type') == 'Product':
                    return d
            except json.JSONDecodeError:
                continue
        return None

    def _extract_taxes_from_properties(self, product: Dict) -> Dict:
        taxes = {}
        properties = product.get('additionalProperty', [])

        for prop in properties:
            name = prop.get('name', '')
            value = prop.get('value', '')
            unit = prop.get('unitText', '')

            if name == 'Import Duty Rate' and unit == 'PERCENT':
                try:
                    taxes['import_duty'] = float(value)
                except (ValueError, TypeError):
                    pass
            elif name == 'VAT Rate' and unit == 'PERCENT':
                try:
                    taxes['vat'] = float(value)
                except (ValueError, TypeError):
                    pass
            elif name == 'Import Restrictions':
                taxes['restrictions'] = value

        return taxes

    def _extract_designation(self, product: Dict) -> tuple:
        description = product.get('description', '')
        name = product.get('name', '')

        ar_designation = name.split('\n')[0].strip().strip('"').strip()
        if len(ar_designation) > 200:
            ar_designation = ar_designation[:200]

        en_designation = ''
        desc_match = re.search(r'HS code [\d/]+\.\s*(.*?)(?:\.|$)', description)
        if desc_match:
            en_designation = desc_match.group(1).strip()

        return ar_designation, en_designation, description

    def _scrape_position(self, hs_code: str) -> Optional[Dict]:
        url = f"{BASE_URL}{hs_code}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 404:
                self.stats['skipped'] += 1
                return None
            resp.raise_for_status()

            product = self._parse_json_ld(resp.text)
            if not product:
                self.stats['skipped'] += 1
                return None

            taxes = self._extract_taxes_from_properties(product)
            ar_designation, en_designation, description = self._extract_designation(product)

            hs_formatted = f"{hs_code[:4]}.{hs_code[4:6]}.{hs_code[6:8]}.{hs_code[8:10]}"

            taxes_detail = []
            if 'import_duty' in taxes:
                taxes_detail.append({
                    'tax_code': 'ID',
                    'tax_name': 'Import Duty (ضريبة الوارد)',
                    'rate': taxes['import_duty'],
                    'rate_type': 'percentage'
                })
            if 'vat' in taxes:
                taxes_detail.append({
                    'tax_code': 'VAT',
                    'tax_name': 'VAT (ضريبة القيمة المضافة)',
                    'rate': taxes['vat'],
                    'rate_type': 'percentage'
                })

            position = {
                'code': hs_formatted,
                'code_clean': hs_code,
                'designation': ar_designation,
                'designation_en': en_designation,
                'taxes': {
                    td['tax_code']: td['rate'] for td in taxes_detail
                },
                'taxes_detail': taxes_detail,
                'total_taxes_pct': sum(t.get('rate', 0) for t in taxes_detail),
            }

            if taxes.get('restrictions'):
                position['administrative_formalities'] = [taxes['restrictions']]

            self.stats['pages_scraped'] += 1
            return position

        except requests.RequestException as e:
            logger.warning(f"Error fetching {hs_code}: {e}")
            self.stats['errors'] += 1
            return None

    def _save_progress(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        data = {
            'country_code': 'EGY',
            'country_name': 'Egypt',
            'country_name_ar': 'مصر',
            'source': 'egyptariffs.com',
            'source_url': 'https://www.egyptariffs.com',
            'source_organization': 'Based on Egyptian Customs Authority data',
            'regime_type': 'national',
            'tariff_system': 'Egyptian National Tariff (Presidential Decree 419/2018)',
            'nomenclature': 'HS 2022',
            'hs_level': 'HS10',
            'extraction_date': datetime.now().isoformat(),
            'total_positions': len(self.positions),
            'stats': self.stats,
            'positions': self.positions
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(self.positions)} positions to {OUTPUT_FILE}")

    def scrape(self, max_positions: int = None, delay: float = 1.5,
               resume: bool = True) -> Dict:
        if resume and os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                self.positions = existing.get('positions', [])
                self.stats = existing.get('stats', self.stats)
                logger.info(f"Resuming from {len(self.positions)} existing positions")
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")

        existing_codes = {p['code_clean'] for p in self.positions}

        self.hs_codes = self._fetch_sitemap()

        remaining = [c for c in self.hs_codes if c not in existing_codes]
        if max_positions:
            remaining = remaining[:max_positions]

        logger.info(f"Scraping {len(remaining)} new positions ({len(existing_codes)} already done)")

        batch_count = 0
        for i, hs_code in enumerate(remaining):
            position = self._scrape_position(hs_code)
            if position:
                self.positions.append(position)
                self.stats['total_positions'] = len(self.positions)
                batch_count += 1

            if (i + 1) % 50 == 0:
                logger.info(
                    f"Progress: {i+1}/{len(remaining)} "
                    f"({len(self.positions)} total, "
                    f"{self.stats['errors']} errors, "
                    f"{self.stats['skipped']} skipped)"
                )
                self._save_progress()

            time.sleep(delay)

        self._save_progress()

        logger.info(
            f"Scraping complete: {len(self.positions)} positions, "
            f"{self.stats['errors']} errors, {self.stats['skipped']} skipped"
        )

        return {
            'country_code': 'EGY',
            'total_positions': len(self.positions),
            'stats': self.stats
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Egypt tariff data')
    parser.add_argument('--max', type=int, default=None,
                        help='Max positions to scrape (default: all)')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='Delay between requests in seconds')
    parser.add_argument('--no-resume', action='store_true',
                        help='Start fresh (ignore existing data)')
    args = parser.parse_args()

    scraper = EgyptTariffsScraper()
    result = scraper.scrape(
        max_positions=args.max,
        delay=args.delay,
        resume=not args.no_resume
    )
    print(f"\nResult: {json.dumps(result, indent=2)}")


if __name__ == '__main__':
    main()
