"""
Scraper pour extraire les positions tarifaires nationales sud-africaines (SACU)
Source: sars.gov.za - Schedule 1 Part 1 (Customs & Excise Tariff)
Format: PDF unique (~700 pages), extraction via tables structurées
Données: codes HS8 + check digit, désignations exactes, 6 colonnes de taux
Couvre: ZAF (Afrique du Sud), BWA (Botswana), LSO (Lesotho), SWZ (Eswatini), NAM (Namibie)
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

import fitz
import httpx

logger = logging.getLogger(__name__)

PDF_URL = "https://www.sars.gov.za/wp-content/uploads/Legal/SCEA1964/Legal-LPrim-CE-Sch1P1Chpt1-to-99-Schedule-No-1-Part-1-Chapters-1-to-99.pdf"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")

SACU_COUNTRIES = [
    {"code": "ZAF", "name": "South Africa"},
    {"code": "BWA", "name": "Botswana"},
    {"code": "LSO", "name": "Lesotho"},
    {"code": "SWZ", "name": "Eswatini"},
    {"code": "NAM", "name": "Namibia"},
]

TAX_COLUMNS = [
    {"code": "GENERAL", "name": "General Customs Duty", "col_idx": 5},
    {"code": "EU_UK", "name": "EU / UK Preferential Rate", "col_idx": 6},
    {"code": "EFTA", "name": "EFTA Preferential Rate", "col_idx": 7},
    {"code": "SADC", "name": "SADC Preferential Rate", "col_idx": 8},
    {"code": "MERCOSUR", "name": "MERCOSUR Preferential Rate", "col_idx": 9},
    {"code": "AfCFTA", "name": "AfCFTA Preferential Rate", "col_idx": 10},
]

HS_CODE_PATTERN = re.compile(r'^(\d{4}\.\d{2}(?:\.\d{2})?)$')
HEADING_PATTERN = re.compile(r'^(\d{2}\.\d{2})$')
RATE_PCT_PATTERN = re.compile(r'(\d+(?:[.,]\d+)?)\s*%')
RATE_SPECIFIC_PATTERN = re.compile(r'(\d+(?:[.,]\d+)?)\s*c/(?:kg|li|la|unit|u)')


class SouthAfricaSARSScraper:
    def __init__(self):
        self.positions = []
        self.errors = []
        self.stats = {
            "pages_processed": 0,
            "positions_extracted": 0,
            "errors": 0,
            "started_at": None,
            "finished_at": None,
        }

    def _download_pdf(self) -> Optional[str]:
        os.makedirs(TEMP_DIR, exist_ok=True)
        filepath = os.path.join(TEMP_DIR, "sars_tariff.pdf")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 100000:
            logger.info(f"Using cached SARS PDF: {os.path.getsize(filepath)} bytes")
            return filepath

        try:
            logger.info("Downloading SARS tariff PDF...")
            resp = httpx.get(PDF_URL, timeout=120.0, follow_redirects=True,
                           headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 100000:
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded SARS PDF: {len(resp.content)} bytes")
                return filepath
            else:
                logger.error(f"Bad response: {resp.status_code}, {len(resp.content)} bytes")
        except Exception as e:
            logger.error(f"Failed to download SARS PDF: {e}")

        return None

    def _parse_rate(self, raw_value: str) -> Dict:
        if not raw_value:
            return {"rate_pct": None, "raw_value": ""}

        cleaned = raw_value.strip().lower()

        if cleaned in ("free", ""):
            return {"rate_pct": 0.0, "raw_value": "free"}

        pct_match = RATE_PCT_PATTERN.search(raw_value)
        specific_match = RATE_SPECIFIC_PATTERN.search(raw_value)

        if pct_match and specific_match:
            pct_val = float(pct_match.group(1).replace(",", "."))
            return {
                "rate_pct": pct_val,
                "raw_value": raw_value.strip(),
                "compound": True,
                "specific_component": specific_match.group(0),
            }
        elif pct_match:
            pct_val = float(pct_match.group(1).replace(",", "."))
            return {"rate_pct": pct_val, "raw_value": f"{pct_val}%"}
        elif specific_match:
            return {
                "rate_pct": None,
                "raw_value": raw_value.strip(),
                "specific_value": specific_match.group(0),
            }
        else:
            try:
                val = float(cleaned.replace("%", "").replace(",", "."))
                return {"rate_pct": val, "raw_value": f"{val}%"}
            except ValueError:
                return {"rate_pct": None, "raw_value": raw_value.strip()}

    def _get_chapter_from_code(self, code: str) -> str:
        digits = code.replace(".", "")
        if len(digits) >= 2:
            return digits[:2]
        return ""

    def scrape_all(self) -> Dict:
        self.stats["started_at"] = datetime.utcnow().isoformat()

        filepath = self._download_pdf()
        if not filepath:
            self.stats["errors"] = 1
            return self.stats

        try:
            doc = fitz.open(filepath)
            logger.info(f"Parsing SARS PDF: {doc.page_count} pages")

            current_heading = ""
            current_heading_desc = ""

            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                tables = page.find_tables()

                for tab in tables:
                    rows = tab.extract()
                    for row in rows:
                        if len(row) < 6:
                            continue

                        col0 = (row[0] or "").strip()
                        col1 = (row[1] or "").strip()
                        col2 = (row[2] or "").strip()
                        col3 = (row[3] or "").strip()
                        stat_unit = (row[4] or "").strip() if len(row) > 4 else ""

                        if col0 in ("Heading /", "Subheading", ""):
                            if col0 == "Heading /":
                                continue
                            if col0 == "Subheading":
                                continue

                        desc = f"{col2} {col3}".strip() if col3 else col2
                        desc = desc.replace("\n", " ").strip()

                        if HEADING_PATTERN.match(col0) and not col1:
                            current_heading = col0
                            current_heading_desc = desc
                            continue

                        if col0 and re.match(r'^\d{4}\.\d', col0):
                            if not stat_unit and not col1:
                                if not re.match(r'^\d{4}\.\d{2}\.\d{2}', col0):
                                    continue

                        code = col0
                        if not code:
                            continue

                        if not re.match(r'^\d{4}\.\d{2}', code):
                            continue

                        if not stat_unit and not col1:
                            if not re.match(r'^\d{4}\.\d{2}\.\d{2}', code):
                                current_heading = code[:5] if len(code) >= 5 else code
                                current_heading_desc = desc
                                continue

                        check_digit = col1

                        taxes = []
                        for tax_col in TAX_COLUMNS:
                            idx = tax_col["col_idx"]
                            raw = (row[idx] or "").strip() if len(row) > idx else ""
                            rate_info = self._parse_rate(raw)
                            taxes.append({
                                "code": tax_col["code"],
                                "name": tax_col["name"],
                                **rate_info,
                            })

                        chapter = self._get_chapter_from_code(code)

                        position = {
                            "code_raw": code,
                            "code_clean": code.replace(".", ""),
                            "check_digit": check_digit,
                            "designation": desc.strip(" -–"),
                            "chapter": chapter,
                            "heading": current_heading or code[:5],
                            "statistical_unit": stat_unit,
                            "taxes": taxes,
                            "fiscal_advantages": [],
                            "administrative_formalities": [],
                            "source": "sars.gov.za",
                            "country": "SACU",
                        }
                        self.positions.append(position)

                self.stats["pages_processed"] = page_idx + 1

                if (page_idx + 1) % 100 == 0:
                    logger.info(f"Page {page_idx+1}/{doc.page_count}: {len(self.positions)} positions")

            doc.close()

        except Exception as e:
            logger.error(f"Error parsing SARS PDF: {e}")
            self.errors.append({"error": str(e)})

        self.stats["positions_extracted"] = len(self.positions)
        self.stats["finished_at"] = datetime.utcnow().isoformat()

        self._save_all_countries()
        return self.stats

    def _save_all_countries(self):
        os.makedirs(DATA_DIR, exist_ok=True)

        for country in SACU_COUNTRIES:
            country_positions = []
            for p in self.positions:
                cp = dict(p)
                cp["country"] = country["code"]
                country_positions.append(cp)

            data = {
                "country": country["code"],
                "country_name": country["name"],
                "source": "sars.gov.za",
                "source_name": f"SARS Customs & Excise Tariff (SACU) - {country['name']}",
                "extraction_date": datetime.utcnow().isoformat(),
                "total_positions": len(country_positions),
                "sacu_note": "Southern African Customs Union - same tariff schedule for all 5 member states",
                "stats": self.stats,
                "positions": country_positions,
            }

            filepath = os.path.join(DATA_DIR, f"{country['code']}_tariffs.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {country['code']}: {len(country_positions)} positions")


def run_sars_scraper():
    logging.basicConfig(level=logging.INFO)
    scraper = SouthAfricaSARSScraper()
    stats = scraper.scrape_all()
    print(f"SARS/SACU extraction complete: {stats}")
    return stats


if __name__ == "__main__":
    run_sars_scraper()
