"""
Ethiopia Tariff Scraper (customs.erca.gov.et)
=============================================
Extracts HS11 national tariff positions from the Ethiopian Customs Commission
Trade Portal (Webb Fontaine platform).

Source: customs.erca.gov.et (Ethiopian Customs Commission / ECC)
Official reference: Ethiopian Customs Proclamation, HS 2017

Ethiopia tariff structure:
- Customs Duty (DR): 0%, 5%, 10%, 20%, 30%, 35% on CIF value
- Excise Tax (ER): Variable rates on specific goods
- VAT: 15% standard rate
- Withholding Tax (WHR): 3% on CIF for commercial imports
- Surtax (SR): 10% on most imported goods
- COMESA Preferential Duty (D2R): Reduced rates for COMESA members

Key features:
- 97 chapters, ~5,500+ HS11 positions (11-digit national codes)
- Two schedules: 1st (raw materials) and 2nd (finished goods)
- English designations
- Multiple tax components per position

Output: ~5,500+ HS11 positions with full tax breakdown
"""

import requests
import json
import os
import re
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://customs.erca.gov.et/trade/customs-division/tariff"
SEARCH_URL = f"{BASE_URL}/search"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'eth_tariffs.json')

TAX_COLUMNS = ['DR', 'ER', 'VAT', 'WHR', 'SR', 'EXR', 'D2R', 'DSR', 'DAR']

TAX_NAMES = {
    'DR': 'Customs Duty',
    'ER': 'Excise Tax',
    'VAT': 'Value Added Tax',
    'WHR': 'Withholding Tax',
    'SR': 'Surtax',
    'EXR': 'Export Tax',
    'D2R': 'COMESA Preferential Duty',
    'DSR': 'Development Surcharge',
    'DAR': 'Additional Duty',
}


class EthiopiaCustomsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.positions = []
        self.stats = {
            "chapters_scraped": 0,
            "hs4_scraped": 0,
            "total_positions": 0,
            "errors": 0,
            "empty_chapters": 0,
        }

    def _init_session(self):
        try:
            resp = self.session.get(
                "https://customs.erca.gov.et/josso/signon/login.do",
                params={
                    "josso_cmd": "login_optional",
                    "josso_back_to": "https://customs.erca.gov.et/trade/josso_security_check"
                },
                timeout=30,
                allow_redirects=True
            )
            self.session.get(f"{BASE_URL}?lang=en", timeout=30)
            logger.info("Session initialized successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to initialize session: {e}")
            return False

    def _get_hs4_codes(self) -> List[str]:
        hs4_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'hs4_headings_en.json')
        if os.path.exists(hs4_file):
            with open(hs4_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            codes = sorted(data.keys())
            logger.info(f"Loaded {len(codes)} HS4 codes from database")
            return codes

        codes = []
        for ch in range(1, 98):
            ch_str = f"{ch:02d}"
            for sub in range(0, 100):
                codes.append(f"{ch_str}{sub:02d}")
        return codes

    def _parse_search_results(self, html: str) -> List[Dict]:
        results = []
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
        if len(tables) < 4:
            return results

        tariff_table = tables[3]
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tariff_table, re.DOTALL)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) < 10:
                continue

            cells_clean = []
            for c in cells:
                text = re.sub(r'<[^>]+>', '', c).strip()
                if text.startswith('×'):
                    text = ''
                cells_clean.append(text)

            non_empty = [c for c in cells_clean if c and c != '×']
            if len(non_empty) < 2:
                continue

            code_idx = None
            for idx, c in enumerate(cells_clean):
                if re.match(r'^\d{8,11}$', c):
                    code_idx = idx
                    break

            if code_idx is None:
                continue

            code = cells_clean[code_idx]
            desc = cells_clean[code_idx + 1] if code_idx + 1 < len(cells_clean) else ''
            unit = cells_clean[code_idx + 2] if code_idx + 2 < len(cells_clean) else ''

            tax_values = []
            for i in range(code_idx + 3, min(code_idx + 3 + len(TAX_COLUMNS), len(cells_clean))):
                val = cells_clean[i]
                try:
                    tax_values.append(float(val) if val else None)
                except ValueError:
                    tax_values.append(None)

            while len(tax_values) < len(TAX_COLUMNS):
                tax_values.append(None)

            taxes_detail = []
            taxes_dict = {}
            for i, col_name in enumerate(TAX_COLUMNS):
                if tax_values[i] is not None and tax_values[i] > 0:
                    taxes_detail.append({
                        'tax_code': col_name,
                        'tax_name': TAX_NAMES.get(col_name, col_name),
                        'rate': tax_values[i],
                        'rate_type': 'percentage'
                    })
                    taxes_dict[col_name] = tax_values[i]

            code_padded = code.ljust(11, '0')[:11]
            if len(code_padded) >= 8:
                formatted = f"{code_padded[:4]}.{code_padded[4:6]}.{code_padded[6:8]}"
                if len(code_padded) > 8:
                    formatted += f".{code_padded[8:]}"
            else:
                formatted = code

            position = {
                'code': formatted,
                'code_clean': code_padded,
                'designation': desc,
                'designation_en': desc,
                'unit': unit,
                'taxes': taxes_dict,
                'taxes_detail': taxes_detail,
                'total_taxes_pct': sum(t.get('rate', 0) for t in taxes_detail),
            }

            if tax_values[6] is not None:
                position['comesa_duty'] = tax_values[6]

            results.append(position)

        return results

    def _scrape_hs4(self, hs4_code: str) -> List[Dict]:
        try:
            resp = self.session.get(
                SEARCH_URL,
                params={
                    'tariff': hs4_code,
                    'searchMode': 'ALL',
                    '_action_searchByTariffKeywords': 'Search',
                    'pageSize': '50',
                    'lang': 'en'
                },
                timeout=30
            )
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} for HS4 {hs4_code}")
                return []

            positions = self._parse_search_results(resp.text)
            return positions

        except requests.RequestException as e:
            logger.warning(f"Error fetching HS4 {hs4_code}: {e}")
            self.stats['errors'] += 1
            return []

    def _save_progress(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        data = {
            'country_code': 'ETH',
            'country_name': 'Ethiopia',
            'country_name_am': 'ኢትዮጵያ',
            'source': 'customs.erca.gov.et',
            'source_url': 'https://customs.erca.gov.et/trade/customs-division/tariff',
            'source_organization': 'Ethiopian Customs Commission (ECC)',
            'regime_type': 'national',
            'tariff_system': 'Ethiopian National Tariff (HS 2017)',
            'nomenclature': 'HS 2017',
            'hs_level': 'HS11',
            'extraction_date': datetime.now().isoformat(),
            'total_positions': len(self.positions),
            'stats': self.stats,
            'tax_columns_info': {
                'DR': 'Customs Duty Rate (0-35%)',
                'ER': 'Excise Tax Rate',
                'VAT': 'Value Added Tax (15%)',
                'WHR': 'Withholding Tax Rate (3%)',
                'SR': 'Surtax Rate (10%)',
                'EXR': 'Export Tax Rate',
                'D2R': 'COMESA Preferential Duty Rate',
                'DSR': 'Development Surcharge Rate',
                'DAR': 'Additional Duty Rate',
            },
            'positions': self.positions
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(self.positions)} positions to {OUTPUT_FILE}")

    def scrape(self, max_chapters: int = None, delay: float = 1.0,
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

        if not self._init_session():
            logger.error("Failed to initialize session, aborting")
            return {'error': 'Session initialization failed'}

        hs4_codes = self._get_hs4_codes()

        if max_chapters:
            chapters_to_do = set()
            for code in hs4_codes:
                ch = code[:2]
                chapters_to_do.add(ch)
                if len(chapters_to_do) >= max_chapters:
                    break
            hs4_codes = [c for c in hs4_codes if c[:2] in chapters_to_do]

        scraped_hs4 = set()
        for p in self.positions:
            code = p.get('code_clean', '')
            if len(code) >= 4:
                scraped_hs4.add(code[:4])

        remaining = [c for c in hs4_codes if c not in scraped_hs4]
        logger.info(f"Scraping {len(remaining)} HS4 codes ({len(scraped_hs4)} already done)")

        current_chapter = None
        chapter_positions = 0

        for i, hs4_code in enumerate(remaining):
            ch = hs4_code[:2]
            if ch != current_chapter:
                if current_chapter is not None:
                    if chapter_positions == 0:
                        self.stats['empty_chapters'] += 1
                    self.stats['chapters_scraped'] += 1
                current_chapter = ch
                chapter_positions = 0
                logger.info(f"Starting Chapter {ch}")

            positions = self._scrape_hs4(hs4_code)
            new_positions = [p for p in positions if p['code_clean'] not in existing_codes]

            for p in new_positions:
                self.positions.append(p)
                existing_codes.add(p['code_clean'])
                chapter_positions += 1

            self.stats['hs4_scraped'] += 1
            self.stats['total_positions'] = len(self.positions)

            if (i + 1) % 50 == 0:
                logger.info(
                    f"Progress: {i+1}/{len(remaining)} HS4 codes "
                    f"({len(self.positions)} total positions, "
                    f"{self.stats['errors']} errors)"
                )
                self._save_progress()

            time.sleep(delay)

        if current_chapter is not None:
            self.stats['chapters_scraped'] += 1

        self._save_progress()

        logger.info(
            f"Scraping complete: {len(self.positions)} positions from "
            f"{self.stats['chapters_scraped']} chapters, "
            f"{self.stats['errors']} errors"
        )

        return {
            'country_code': 'ETH',
            'total_positions': len(self.positions),
            'stats': self.stats
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Ethiopia tariff data')
    parser.add_argument('--max-chapters', type=int, default=None,
                        help='Max chapters to scrape (default: all 97)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds')
    parser.add_argument('--no-resume', action='store_true',
                        help='Start fresh (ignore existing data)')
    args = parser.parse_args()

    scraper = EthiopiaCustomsScraper()
    result = scraper.scrape(
        max_chapters=args.max_chapters,
        delay=args.delay,
        resume=not args.no_resume
    )
    print(f"\nResult: {json.dumps(result, indent=2)}")


if __name__ == '__main__':
    main()
