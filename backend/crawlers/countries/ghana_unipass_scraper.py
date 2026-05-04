"""
Ghana UNIPASS (ICUMS) Tariff Scraper
======================================
Extracts HS10 national tariff positions from Ghana's Integrated Customs
Management System (UNIPASS/ICUMS).
Source: external.unipassghana.com

Ghana follows the ECOWAS Common External Tariff (CET) with 5 tariff bands:
- Band 0: 0% (essential social goods)
- Band 1: 5% (raw materials, capital goods)
- Band 2: 10% (intermediate goods)
- Band 3: 20% (consumer goods)
- Band 4: 35% (protected goods)

Additional taxes extracted per position:
- Import Duty (ID): 0-35% (ECOWAS CET bands)
- Import Duty VAT: 0% or 15% (standard VAT)
- Import Excise: varies by product
- Export Duty: 0% for most products
- NHIL Rate: National Health Insurance Levy (2.5%)

Output: ~6,400 HS10 positions with 5 tax columns
"""

import requests
import json
import os
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://external.unipassghana.com/co/code/popup/selectHsCode.do"



class GhanaUnipassScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://external.unipassghana.com/',
        })
        self.positions = []
        self.stats = {
            "pages_scraped": 0,
            "total_positions": 0,
            "errors": 0,
            "rate_distribution": {},
        }

    def _fetch_page(self, page_no: int, page_size: int = 100) -> Optional[List[Dict]]:
        start = (page_no - 1) * page_size
        listop = json.dumps({
            "miv_end_index": str(start + page_size),
            "miv_pageNo": str(page_no),
            "searchHSCodeOrName": None,
            "miv_start_index": str(start),
            "miv_sort": "",
            "miv_pageSize": str(page_size)
        })

        data = {
            "decorator": "popup",
            "MENU_ID": "IIM01S02V01",
            "LISTOP": listop,
            "searchHSCodeOrName": "",
            "miv_pageNo": str(page_no),
            "miv_pageSize": str(page_size)
        }

        try:
            resp = self.session.post(BASE_URL, data=data, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Page {page_no}: Request failed: {e}")
            self.stats["errors"] += 1
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')

        if not table or "No data found" in table.get_text():
            return []

        rows = table.find_all('tr')
        page_positions = []

        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 10:
                continue

            cell_texts = [c.get_text(strip=True) for c in cells]

            try:
                hs_code = cell_texts[1]
                description = cell_texts[2]
                hs_head = cell_texts[3]
                unit = cell_texts[4]
                import_duty = self._parse_rate(cell_texts[5])
                import_vat = self._parse_rate(cell_texts[6])
                import_excise = self._parse_rate(cell_texts[7])
                export_duty = self._parse_rate(cell_texts[8])
                nhil_rate = self._parse_rate(cell_texts[9])
            except (IndexError, ValueError) as e:
                logger.warning(f"Page {page_no}: Parse error: {e}")
                continue

            if not hs_code or len(hs_code) < 8:
                continue

            taxes_detail = []
            total_taxes_pct = 0.0

            if import_duty is not None and import_duty > 0:
                taxes_detail.append({
                    "tax_name": "Import Duty (ECOWAS CET)",
                    "rate": import_duty,
                    "base": "CIF"
                })
                total_taxes_pct += import_duty

            if import_vat is not None and import_vat > 0:
                taxes_detail.append({
                    "tax_name": "Value Added Tax (VAT)",
                    "rate": import_vat,
                    "base": "CIF+Duty"
                })
                total_taxes_pct += import_vat

            if import_excise is not None and import_excise > 0:
                taxes_detail.append({
                    "tax_name": "Import Excise Duty",
                    "rate": import_excise,
                    "base": "CIF+Duty"
                })
                total_taxes_pct += import_excise

            if export_duty is not None and export_duty > 0:
                taxes_detail.append({
                    "tax_name": "Export Duty",
                    "rate": export_duty,
                    "base": "FOB"
                })

            if nhil_rate is not None and nhil_rate > 0:
                taxes_detail.append({
                    "tax_name": "National Health Insurance Levy (NHIL)",
                    "rate": nhil_rate,
                    "base": "CIF+Duty"
                })
                total_taxes_pct += nhil_rate

            chapter = hs_code[:2]
            duty_key = f"{import_duty}%" if import_duty is not None else "N/A"
            self.stats["rate_distribution"][duty_key] = self.stats["rate_distribution"].get(duty_key, 0) + 1

            position = {
                "hs_code": hs_code,
                "hs_code_display": f"{hs_code[:4]}.{hs_code[4:6]}.{hs_code[6:8]}.{hs_code[8:]}" if len(hs_code) == 10 else hs_code,
                "designation": description,
                "chapter": chapter,
                "heading": hs_head,
                "unit": unit,
                "import_duty": import_duty,
                "import_vat": import_vat,
                "import_excise": import_excise,
                "export_duty": export_duty,
                "nhil_rate": nhil_rate,
                "taxes_detail": taxes_detail,
                "total_taxes_pct": round(total_taxes_pct, 2),
                "fiscal_advantages": [],
                "administrative_formalities": [],
                "source": "Ghana UNIPASS/ICUMS (unipassghana.com)",
                "data_format": "crawled_authentic"
            }

            page_positions.append(position)

        return page_positions

    def _parse_rate(self, rate_str: str) -> Optional[float]:
        rate_str = rate_str.strip()
        if not rate_str or rate_str == '-' or rate_str == 'N/A':
            return None
        try:
            return float(rate_str)
        except ValueError:
            return None

    def run(self, output_dir: str = None, delay: float = 2.0, start_page: int = 1) -> Dict:
        logger.info("=" * 60)
        logger.info("Ghana UNIPASS Tariff Scraper - Starting")
        logger.info("=" * 60)

        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "crawled")

        existing_file = os.path.join(output_dir, "gha_tariffs.json")
        if start_page == 1 and os.path.exists(existing_file):
            try:
                with open(existing_file, 'r') as f:
                    existing = json.load(f)
                if existing.get("positions") and existing.get("scrape_complete") is not True:
                    self.positions = existing["positions"]
                    last_page = existing.get("last_page_scraped", 0)
                    start_page = last_page + 1
                    logger.info(f"Resuming from page {start_page} ({len(self.positions)} existing positions)")
            except Exception:
                pass

        max_pages = 70
        empty_streak = 0
        consecutive_errors = 0

        for page_no in range(start_page, max_pages + 1):
            logger.info(f"Fetching page {page_no}...")

            page_positions = None
            for attempt in range(3):
                page_positions = self._fetch_page(page_no)
                if page_positions is not None:
                    consecutive_errors = 0
                    break
                wait = (attempt + 1) * 5
                logger.warning(f"Page {page_no}: attempt {attempt+1} failed, waiting {wait}s...")
                time.sleep(wait)
                consecutive_errors += 1

            if page_positions is None:
                if consecutive_errors >= 6:
                    logger.error(f"Too many consecutive errors, stopping at page {page_no}")
                    break
                continue

            if not page_positions:
                empty_streak += 1
                if empty_streak >= 2:
                    logger.info(f"No more data after page {page_no - 1}")
                    break
                continue

            empty_streak = 0
            self.positions.extend(page_positions)
            self.stats["pages_scraped"] += 1
            self.stats["total_positions"] = len(self.positions)

            if page_no % 10 == 0:
                logger.info(f"  Progress: {len(self.positions)} positions from {page_no} pages")
                self._save(output_dir, last_page=page_no)

            time.sleep(delay)

        logger.info(f"\nExtraction complete:")
        logger.info(f"  Total positions: {len(self.positions)}")
        logger.info(f"  Pages scraped: {self.stats['pages_scraped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info(f"  Rate distribution (top 10):")
        for rate, count in sorted(self.stats["rate_distribution"].items(), key=lambda x: -x[1])[:10]:
            logger.info(f"    {rate}: {count}")

        filepath = self._save(output_dir, last_page=self.stats["pages_scraped"] + start_page - 1, complete=True)

        return {
            "status": "success",
            "country_code": "GHA",
            "country_name": "Ghana",
            "total_positions": len(self.positions),
            "pages_scraped": self.stats["pages_scraped"],
            "errors": self.stats["errors"],
            "file": filepath,
            "rate_distribution": dict(sorted(
                self.stats["rate_distribution"].items(), key=lambda x: -x[1]
            ))
        }

    def _save(self, output_dir: str = None, last_page: int = 0, complete: bool = False) -> str:
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "crawled")
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, "gha_tariffs.json")

        data = {
            "country_code": "GHA",
            "country_name": "Ghana",
            "source": "Ghana UNIPASS/ICUMS",
            "source_url": "https://external.unipassghana.com",
            "source_organization": "Ghana Revenue Authority (GRA)",
            "extraction_date": datetime.now().isoformat(),
            "total_positions": len(self.positions),
            "last_page_scraped": last_page,
            "scrape_complete": complete,
            "hs_version": "HS 2022",
            "tariff_system": "ECOWAS CET 5-band (0%, 5%, 10%, 20%, 35%) + national levies",
            "economic_community": "ECOWAS",
            "taxes_extracted": [
                "Import Duty (ECOWAS CET)",
                "Import Duty VAT (15%)",
                "Import Excise Duty",
                "Export Duty",
                "National Health Insurance Levy (NHIL)"
            ],
            "positions": self.positions
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(self.positions)} positions to {filepath}")
        return filepath


if __name__ == "__main__":
    scraper = GhanaUnipassScraper()
    result = scraper.run()
    print(json.dumps({k: v for k, v in result.items() if k != 'rate_distribution'}, indent=2))
    print(f"\nRate distribution: {json.dumps(result['rate_distribution'], indent=2)}")
