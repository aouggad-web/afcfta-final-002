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
from datetime import datetime
from typing import Dict, List, Optional

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

HS_CODE_PATTERN = re.compile(r"^(\d{4}\.\d{2}(?:\.\d{2})?)$")
HEADING_PATTERN = re.compile(r"^(\d{2}\.\d{2})$")
RATE_PCT_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
RATE_SPECIFIC_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*c/(?:\d+\s*)?(?:kg|li|la|unit|u)\b", re.IGNORECASE
)


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
            resp = httpx.get(
                PDF_URL, timeout=120.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}
            )
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
        # le texte brut publié est conservé quand il existe ; une cellule
        # vide est normalisée au libellé SARS canonique « free ».
        raw_kept = " ".join(raw_value.split())

        if cleaned in ("free", ""):
            return {"rate_pct": 0.0, "raw_value": raw_kept if raw_kept else "free"}

        pct_match = RATE_PCT_PATTERN.search(raw_value)
        specific_match = RATE_SPECIFIC_PATTERN.search(raw_value)

        if pct_match and specific_match:
            pct_val = float(pct_match.group(1).replace(",", "."))
            return {
                "rate_pct": pct_val,
                "raw_value": raw_kept,
                "compound": True,
                "specific_component": specific_match.group(0),
            }
        elif pct_match:
            pct_val = float(pct_match.group(1).replace(",", "."))
            return {"rate_pct": pct_val, "raw_value": raw_kept}
        elif specific_match:
            return {
                "rate_pct": None,
                "raw_value": raw_kept,
                "specific_value": specific_match.group(0),
            }
        else:
            try:
                val = float(cleaned.replace("%", "").replace(",", "."))
                return {"rate_pct": val, "raw_value": raw_kept}
            except ValueError:
                return {"rate_pct": None, "raw_value": raw_kept}

    def _get_chapter_from_code(self, code: str) -> str:
        digits = code.replace(".", "")
        if len(digits) >= 2:
            return digits[:2]
        return ""

    # Patterns pour extraction texte (fallback quand find_tables manque des lignes)
    TEXT_CODE_PATTERN = re.compile(r"(\d{4}\.\d{2}(?:\.\d{2}){1,2})")
    TEXT_HEADING_PATTERN = re.compile(r"^(\d{4}\.\d{2})\s*$")
    TEXT_RATE_PATTERN = re.compile(
        r"(free|\d+(?:[.,]\d+)?\s*%|\d+(?:[.,]\d+)?\s*c/\d*\s*(?:kg|li|u|unit))",
        re.IGNORECASE,
    )

    def _extract_page_text(self, page, current_heading, current_heading_desc):
        """
        Extraction texte — capture TOUTES les positions 8/10-digit que
        find_tables manque. Le PDF SARS met chaque élément sur une ligne
        séparée: code, check_digit, désignation, unité, taux×6.
        """
        text = page.get_text("text")
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        found = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Heading 6-digit seul → heading courant
            m6 = re.match(r"^(\d{4}\.\d{2})$", line)
            if m6:
                current_heading = m6.group(1)
                i += 1
                continue

            # Code 8-digit ou 10-digit au début d'un bloc
            m_code = re.match(r"^(\d{4}\.\d{2}\.\d{2}(?:\.\d{2})?)$", line)
            if not m_code:
                i += 1
                continue

            code = m_code.group(1)
            i += 1

            # Check digit: ligne suivante si c'est un seul chiffre
            check_digit = ""
            if i < len(lines) and re.match(r"^\d$", lines[i]):
                check_digit = lines[i]
                i += 1

            # Collecter les lignes de description + unité + taux
            block_lines = []
            while i < len(lines):
                next_line = lines[i]
                # Si on atteint le prochain code tariff, stop
                if re.match(r"^\d{4}\.\d{2}(\.\d{2}){0,2}$", next_line):
                    break
                block_lines.append(next_line)
                i += 1
                # Limite de sécurité: 25 lignes max par bloc
                if len(block_lines) >= 25:
                    break

            if not block_lines:
                continue

            # Identifier l'unité statistique (kg, u, l, m², etc.)
            stat_unit = ""
            unit_idx = -1
            for idx, bl in enumerate(block_lines):
                if re.match(r"^(kg|u|l|m2|m²|m|kg/l|li|la|10kg|100kg|t|g|ml)$", bl, re.IGNORECASE):
                    stat_unit = bl
                    unit_idx = idx
                    break

            # Extraire les taux: free, X%, Xc/kg
            rate_values = []
            for bl in block_lines:
                if bl.lower() in ("free", "f"):
                    rate_values.append("free")
                elif re.match(r"^\d+(?:[.,]\d+)?\s*%$", bl):
                    rate_values.append(bl)
                elif re.match(r"^\d+(?:[.,]\d+)?\s*c/", bl, re.IGNORECASE):
                    rate_values.append(bl)
                elif re.match(r"^\d+(?:[.,]\d+)?\s*%?\s*or\s*", bl, re.IGNORECASE):
                    rate_values.append(bl)

            # La désignation = lignes avant l'unité et avant les taux
            desc_end = unit_idx if unit_idx >= 0 else len(block_lines)
            # Trouver le premier taux pour couper la désignation
            for idx, bl in enumerate(block_lines):
                if bl.lower() in ("free", "f") or re.match(r"^\d+(?:[.,]\d+)?\s*%", bl):
                    desc_end = min(desc_end, idx)
                    break

            desc_parts = block_lines[:desc_end]
            desc = " ".join(desc_parts).strip().strip("-– ").strip()
            desc = re.sub(r"\s+", " ", desc)

            # Construire les taxes (6 colonnes SARS)
            # Grouper les taux composés (ex: "40% or 240c/kg" = 2 valeurs → 1 taxe)
            taxes = []
            rate_idx = 0
            for tax_col in TAX_COLUMNS:
                if rate_idx < len(rate_values):
                    raw_val = rate_values[rate_idx]
                    # Gérer les taux composés: "40% or 240c/kg" → 1 taxe
                    rate_info = self._parse_rate(raw_val)
                    rate_idx += 1
                else:
                    rate_info = {"rate_pct": None, "raw_value": ""}
                taxes.append(
                    {
                        "code": tax_col["code"],
                        "name": tax_col["name"],
                        **rate_info,
                    }
                )

            chapter = self._get_chapter_from_code(code)

            position = {
                "code_raw": code,
                "code_clean": code.replace(".", ""),
                "check_digit": check_digit,
                "designation": desc,
                "chapter": chapter,
                "heading": current_heading or code[:5],
                "statistical_unit": stat_unit,
                "taxes": taxes,
                "fiscal_advantages": [],
                "administrative_formalities": [],
                "source": "sars.gov.za",
                "country": "SACU",
                "_extraction_method": "text",
            }
            found.append(position)

        return found, current_heading, current_heading_desc

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
            table_positions = {}

            # ── PASS 1: Extraction par tables (find_tables) ──
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

                        if col0 and re.match(r"^\d{4}\.\d", col0):
                            if not stat_unit and not col1:
                                if not re.match(r"^\d{4}\.\d{2}\.\d{2}", col0):
                                    continue

                        code = col0
                        if not code:
                            continue

                        if not re.match(r"^\d{4}\.\d{2}", code):
                            continue

                        if not stat_unit and not col1:
                            if not re.match(r"^\d{4}\.\d{2}\.\d{2}", code):
                                current_heading = code[:5] if len(code) >= 5 else code
                                current_heading_desc = desc
                                continue

                        check_digit = col1

                        taxes = []
                        for tax_col in TAX_COLUMNS:
                            idx = tax_col["col_idx"]
                            raw = (row[idx] or "").strip() if len(row) > idx else ""
                            rate_info = self._parse_rate(raw)
                            taxes.append(
                                {
                                    "code": tax_col["code"],
                                    "name": tax_col["name"],
                                    **rate_info,
                                }
                            )

                        chapter = self._get_chapter_from_code(code)
                        code_clean = code.replace(".", "")

                        position = {
                            "code_raw": code,
                            "code_clean": code_clean,
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
                            "_extraction_method": "table",
                        }
                        table_positions[code_clean] = position

                self.stats["pages_processed"] = page_idx + 1

                if (page_idx + 1) % 100 == 0:
                    logger.info(
                        f"[table] Page {page_idx+1}/{doc.page_count}: "
                        f"{len(table_positions)} positions"
                    )

            logger.info(
                f"Pass 1 (tables): {len(table_positions)} positions extracted"
            )

            # ── PASS 2: Extraction texte (catch-all) ──
            current_heading = ""
            current_heading_desc = ""
            text_positions = {}

            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                found, current_heading, current_heading_desc = (
                    self._extract_page_text(
                        page, current_heading, current_heading_desc
                    )
                )
                for pos in found:
                    text_positions[pos["code_clean"]] = pos

                if (page_idx + 1) % 100 == 0:
                    logger.info(
                        f"[text] Page {page_idx+1}/{doc.page_count}: "
                        f"{len(text_positions)} positions"
                    )

            logger.info(
                f"Pass 2 (text): {len(text_positions)} positions extracted"
            )

            # ── MERGE: table positions prioritaires, text comble les trous ──
            merged = dict(text_positions)
            merged.update(table_positions)

            for pos in merged.values():
                pos.pop("_extraction_method", None)

            # ── NORMALISATION 8-digit: SARS utilise 8 chiffres pour toute
            # marchandise. Les codes 6-digit qui ont des taux mais PAS
            # d'enfants 8-digit sont des lignes tarifaires à part entière
            # (subdivision nationale = "00"). On les normalise en 8-digit. ──
            code_to_pos = {p["code_clean"]: p for p in merged.values()}
            eight_prefixes = {
                c[:6] for c in code_to_pos if len(c) == 8
            }
            normalized = {}
            for code, pos in code_to_pos.items():
                if len(code) == 6:
                    taxes = pos.get("taxes", [])
                    general = next(
                        (t for t in taxes if t.get("code") == "GENERAL"), None
                    )
                    has_rate = general and general.get("rate_pct") is not None
                    has_children = code in eight_prefixes
                    if has_rate and not has_children:
                        pos["code_raw"] = pos["code_raw"] + ".00"
                        pos["code_clean"] = code + "00"
                        normalized[code + "00"] = pos
                    elif not has_rate:
                        continue
                    elif has_children:
                        continue
                else:
                    normalized[code] = pos

            self.positions = list(normalized.values())
            self.positions.sort(key=lambda p: p["code_clean"])

            doc.close()

        except Exception as e:
            logger.error(f"Error parsing SARS PDF: {e}")
            self.errors.append({"error": str(e)})

        self.stats["positions_extracted"] = len(self.positions)
        self.stats["extraction_method"] = {
            "table_pass": len(table_positions),
            "text_pass": len(text_positions),
            "merged_total": len(merged),
            "normalized_8digit": len(self.positions),
        }
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
