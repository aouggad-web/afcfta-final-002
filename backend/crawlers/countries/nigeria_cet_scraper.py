"""
Scraper pour extraire les positions tarifaires nationales nigérianes
Source: customs.gov.ng - ECOWAS Common External Tariff (CET)
Format: PDF par chapitre (97 chapitres), extraction via tables structurées
Données: codes HS10, désignations exactes, ID (Import Duty), VAT, IAT, EXC
"""

import json
import logging
import os
import re
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import fitz
import httpx

logger = logging.getLogger(__name__)

PDF_BASE_URL = "https://customs.gov.ng/wp-content/uploads/2022/05"
ALT_PDF_BASE_URL = "https://trade.gov.ng/trade-server/wp-content/uploads/2022/05"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/pdf,*/*",
}

CHAPTERS = list(range(1, 98))
CHAPTER_27_ALT = "https://customs.gov.ng/wp-content/uploads/2021/10/Chapter_27.pdf"

TAX_FULL_NAMES = {
    "ID": "Import Duty (Customs Duty)",
    "VAT": "Value Added Tax",
    "IAT": "Import Adjustment Tax",
    "EXC": "Excise Duty",
}

HS_CODE_PATTERN = re.compile(r'(\d{4}\.\d{2}\.\d{2}\.\d{2})')


class NigeriaCETScraper:
    def __init__(self):
        self.positions = []
        self.errors = []
        self.stats = {
            "chapters_processed": 0,
            "chapters_failed": 0,
            "positions_extracted": 0,
            "errors": 0,
            "started_at": None,
            "finished_at": None,
        }

    def _download_chapter_pdf(self, chapter: int) -> Optional[str]:
        os.makedirs(TEMP_DIR, exist_ok=True)
        filepath = os.path.join(TEMP_DIR, f"nigeria_ch{chapter}.pdf")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return filepath

        if chapter == 27:
            urls = [CHAPTER_27_ALT, f"{PDF_BASE_URL}/Chapter-{chapter}.pdf"]
        else:
            urls = [
                f"{PDF_BASE_URL}/Chapter-{chapter}.pdf",
                f"{ALT_PDF_BASE_URL}/Chapter-{chapter}.pdf",
            ]

        for url in urls:
            try:
                time.sleep(0.5)
                resp = httpx.get(url, headers=HEADERS, timeout=30.0, follow_redirects=True)
                if resp.status_code == 200 and len(resp.content) > 500:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"Downloaded chapter {chapter}: {len(resp.content)} bytes")
                    return filepath
            except Exception as e:
                logger.warning(f"Failed to download chapter {chapter} from {url}: {e}")

        self.errors.append({"chapter": chapter, "error": "Download failed"})
        return None

    def _parse_chapter_pdf(self, filepath: str, chapter: int) -> List[Dict]:
        positions = []
        try:
            doc = fitz.open(filepath)
            current_heading = ""
            current_heading_desc = ""
            ch_num = str(chapter).zfill(2)

            for page in doc:
                tables = page.find_tables()
                for tab in tables:
                    rows = tab.extract()
                    for row in rows:
                        if len(row) < 6:
                            continue

                        heading = (row[0] or "").strip()
                        tsn = (row[1] or "").strip()
                        desc = (row[2] or "").strip().replace("\n", " ")
                        su = (row[3] or "").strip() if len(row) > 3 else ""
                        id_rate = (row[4] or "").strip() if len(row) > 4 else ""
                        vat_rate = (row[5] or "").strip() if len(row) > 5 else ""
                        iat_rate = (row[6] or "").strip() if len(row) > 6 else ""
                        exc_rate = (row[7] or "").strip() if len(row) > 7 else ""

                        if heading == "Heading" or tsn == "TSN":
                            continue

                        if heading and not tsn:
                            current_heading = heading
                            current_heading_desc = desc
                            continue

                        if not tsn:
                            continue

                        if not HS_CODE_PATTERN.match(tsn):
                            continue

                        clean_desc = desc.strip(" -–")
                        if not clean_desc and current_heading_desc:
                            clean_desc = current_heading_desc

                        taxes = self._build_taxes(id_rate, vat_rate, iat_rate, exc_rate)

                        position = {
                            "code_raw": tsn,
                            "code_clean": tsn.replace(".", ""),
                            "designation": clean_desc,
                            "chapter": ch_num,
                            "heading": current_heading or tsn[:5],
                            "statistical_unit": su,
                            "taxes": taxes,
                            "fiscal_advantages": [],
                            "administrative_formalities": [],
                            "source": "customs.gov.ng",
                            "country": "NGA",
                        }
                        positions.append(position)

            doc.close()

        except Exception as e:
            logger.error(f"Error parsing chapter {chapter}: {e}")
            self.errors.append({"chapter": chapter, "error": str(e)})

        return positions

    def _build_taxes(self, id_rate: str, vat_rate: str, iat_rate: str, exc_rate: str) -> List[Dict]:
        taxes = []
        rate_map = [
            ("ID", id_rate),
            ("VAT", vat_rate),
            ("IAT", iat_rate),
            ("EXC", exc_rate),
        ]

        for code, raw_val in rate_map:
            tax_entry = {
                "code": code,
                "name": TAX_FULL_NAMES.get(code, code),
            }

            cleaned = raw_val.strip().replace("%", "").replace(",", ".").strip()

            if not cleaned or cleaned in ("-", "–", ""):
                tax_entry["rate_pct"] = None
                tax_entry["raw_value"] = ""
            elif cleaned.lower() in ("free", "0"):
                tax_entry["rate_pct"] = 0.0
                tax_entry["raw_value"] = "free" if cleaned.lower() == "free" else "0%"
            else:
                try:
                    val = float(cleaned)
                    tax_entry["rate_pct"] = val
                    tax_entry["raw_value"] = f"{val}%"
                except ValueError:
                    tax_entry["rate_pct"] = None
                    tax_entry["raw_value"] = raw_val
                    if "/" in raw_val or "c/" in raw_val.lower():
                        tax_entry["specific_value"] = raw_val

            taxes.append(tax_entry)

        return taxes

    def scrape_all(self, chapters: List[int] = None, save_progress: bool = True) -> Dict:
        self.stats["started_at"] = datetime.utcnow().isoformat()
        chapters_to_process = chapters or CHAPTERS

        logger.info(f"Starting Nigeria CET extraction for {len(chapters_to_process)} chapters")

        for ch in chapters_to_process:
            try:
                filepath = self._download_chapter_pdf(ch)
                if not filepath:
                    self.stats["chapters_failed"] += 1
                    continue

                positions = self._parse_chapter_pdf(filepath, ch)
                self.positions.extend(positions)
                self.stats["chapters_processed"] += 1
                self.stats["positions_extracted"] = len(self.positions)

                logger.info(f"Chapter {ch}: {len(positions)} positions (total: {len(self.positions)})")

                if save_progress and self.stats["chapters_processed"] % 10 == 0:
                    self._save_progress()

            except Exception as e:
                logger.error(f"Error processing chapter {ch}: {e}")
                self.errors.append({"chapter": ch, "error": str(e)})
                self.stats["chapters_failed"] += 1

        self.stats["finished_at"] = datetime.utcnow().isoformat()
        self._save_final()

        return self.stats

    def _save_progress(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        progress_pct = int(self.stats["chapters_processed"] / len(CHAPTERS) * 100)
        filepath = os.path.join(DATA_DIR, f"NGA_progress_{progress_pct}.json")
        self._write_json(filepath)
        logger.info(f"Progress saved: {progress_pct}% ({len(self.positions)} positions)")

    def _save_final(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, "NGA_tariffs.json")
        self._write_json(filepath)
        logger.info(f"Final save: {len(self.positions)} positions to {filepath}")

    def _write_json(self, filepath: str):
        data = {
            "country": "NGA",
            "country_name": "Nigeria",
            "source": "customs.gov.ng",
            "source_name": "Nigeria Customs Service - ECOWAS Common External Tariff",
            "extraction_date": datetime.utcnow().isoformat(),
            "total_positions": len(self.positions),
            "stats": self.stats,
            "positions": self.positions,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def run_nigeria_scraper(chapters: List[int] = None):
    logging.basicConfig(level=logging.INFO)
    scraper = NigeriaCETScraper()
    stats = scraper.scrape_all(chapters=chapters)
    print(f"Nigeria CET extraction complete: {stats}")
    return stats


if __name__ == "__main__":
    run_nigeria_scraper()
