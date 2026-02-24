import asyncio
import httpx
import json
import csv
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 1.5

BASE_URL = "https://www.douane.gov.tn"
TARIF_API = f"{BASE_URL}/tarifwebnew/getresultat.php"
REGLEMENTATION_API = f"{BASE_URL}/tarifwebnew/help.php"

CHAPTERS = [f"{i:02d}" for i in range(1, 98) if i != 77]


class TunisiaDouaneScraper:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.sections = {}
        self.chapters = {}
        self.positions = []
        self.country_code = "TUN"
        self.source = "douane.gov.tn/tarifweb2025"

    async def _ensure_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                verify=False,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                    "Referer": f"{BASE_URL}/tarifweb2025/",
                }
            )

    async def _close_client(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        await self._ensure_client()
        for attempt in range(max_retries):
            try:
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    return resp.text
                logger.warning(f"HTTP {resp.status_code} for {url}")
            except Exception as e:
                logger.warning(f"Error fetching {url}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 * (attempt + 1))
        return None

    async def get_chapter_positions(self, chapter: str) -> list:
        url = f"{TARIF_API}?choix=1&chap={chapter}"
        html = await self._fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        positions = []
        seen = set()
        for cell in soup.find_all(["td", "th"], onclick=True):
            oc = cell.get("onclick", "")
            match = re.search(r"submit_frm_resultat\('(\d+)','(\d+)','(\d+)'\)", oc)
            if not match:
                continue
            choix, chap, code = match.groups()
            if len(code) < 8 or code in seen:
                continue

            text = cell.get_text(strip=True)
            if re.match(r"^\d+$", text):
                next_td = cell.find_next_sibling("td")
                designation = next_td.get_text(strip=True) if next_td else ""
            else:
                designation = text

            seen.add(code)
            positions.append({
                "code": code,
                "designation": designation,
                "choix": choix,
                "chapter": chap,
            })

        return positions

    async def get_position_detail(self, choix: str, chapter: str, code: str) -> dict:
        url = f"{TARIF_API}?choix={choix}&chap={chapter}&sel={code}"
        html = await self._fetch_page(url)

        result = {
            "hs_code": code,
            "chapter": chapter,
            "taxes_import": [],
            "taxes_export": [],
            "preferences": [],
            "reglementation_import": [],
            "reglementation_export": [],
            "qcs": "",
            "qci": "",
            "groupe_utilisation": "",
            "mode_paiement": "",
            "import_status": "",
            "export_status": "",
        }

        if not html:
            return result

        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 1:
                continue

            header_row = rows[0]
            header_cells = header_row.find_all(["td", "th"])
            header_text = " ".join(c.get_text(strip=True) for c in header_cells).upper()

            if "QCS" in header_text and "QCI" in header_text:
                if len(rows) > 1:
                    data_cells = rows[1].find_all(["td", "th"])
                    texts = [c.get_text(strip=True) for c in data_cells]
                    if len(texts) >= 4:
                        result["qcs"] = texts[0]
                        result["qci"] = texts[1]
                        result["groupe_utilisation"] = texts[2]
                        result["mode_paiement"] = texts[3]

            elif "IMPORT" in header_text and "EXPORT" in header_text and "DROITS" not in header_text:
                if len(rows) > 1:
                    data_cells = rows[1].find_all(["td", "th"])
                    texts = [c.get_text(strip=True) for c in data_cells]
                    if len(texts) >= 2:
                        result["import_status"] = texts[0]
                        result["export_status"] = texts[1]

            elif "DROITS" in header_text and "TAXES" in header_text:
                is_export = False
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    texts = [c.get_text(strip=True) for c in cells]
                    if len(texts) >= 2:
                        tax_raw = texts[0]
                        value_raw = texts[1]
                        assiette = texts[2] if len(texts) > 2 else ""

                        code_match = re.match(r"^([A-Z/_]+)", tax_raw)
                        tax_code = code_match.group(1) if code_match else tax_raw[:10]
                        tax_name = tax_raw[len(tax_code):].strip() if code_match else tax_raw

                        rate_match = re.search(r"([\d.,]+)\s*%", value_raw)
                        rate = float(rate_match.group(1).replace(",", ".")) if rate_match else None

                        is_specific = "DT/" in value_raw.upper() or "DINARS" in value_raw.upper()
                        specific_value = value_raw if is_specific and rate is None else ""

                        tax_entry = {
                            "code": tax_code.strip(),
                            "name": tax_name.strip(),
                            "raw_value": value_raw,
                            "rate_pct": rate,
                            "specific_value": specific_value,
                            "assiette": assiette,
                        }

                        if "EXP" in tax_code.upper():
                            result["taxes_export"].append(tax_entry)
                            is_export = True
                        elif is_export:
                            result["taxes_export"].append(tax_entry)
                        else:
                            result["taxes_import"].append(tax_entry)

            elif "CODE PAYS" in header_text or "TAUX" in header_text and "PR" in header_text:
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    texts = [c.get_text(strip=True) for c in cells]
                    if len(texts) >= 3:
                        result["preferences"].append({
                            "country_code": texts[0],
                            "country_name": texts[1],
                            "rate": texts[2],
                        })

            elif "CODE" in header_text and "DESCRIPTION" in header_text:
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    texts = [c.get_text(strip=True) for c in cells]
                    if len(texts) >= 2:
                        reg_entry = {
                            "code": texts[0],
                            "description": texts[1],
                        }
                        if "EXP" in texts[1].upper():
                            result["reglementation_export"].append(reg_entry)
                        else:
                            result["reglementation_import"].append(reg_entry)

        return result

    async def scrape_chapter(self, chapter: str, max_positions: int = None) -> list:
        logger.info(f"Scraping Tunisia chapter {chapter}...")
        positions = await self.get_chapter_positions(chapter)
        if not positions:
            logger.warning(f"No positions found for chapter {chapter}")
            return []

        logger.info(f"Found {len(positions)} positions in chapter {chapter}")
        if max_positions:
            positions = positions[:max_positions]

        results = []
        for i, pos in enumerate(positions):
            await asyncio.sleep(RATE_LIMIT_DELAY)
            detail = await self.get_position_detail(pos["choix"], pos["chapter"], pos["code"])
            detail["designation"] = pos["designation"]
            results.append(detail)

            if (i + 1) % 50 == 0:
                logger.info(f"Chapter {chapter}: {i+1}/{len(positions)} positions scraped")

        logger.info(f"Chapter {chapter}: {len(results)} positions with details")
        return results

    async def scrape_sample(self, chapters: list = None, max_per_chapter: int = 3) -> list:
        if chapters is None:
            chapters = ["01", "04", "10", "17", "27", "30", "39", "72", "84", "87"]

        all_results = []
        for ch in chapters:
            positions = await self.get_chapter_positions(ch)
            if not positions:
                continue

            sample = positions[:max_per_chapter]
            for pos in sample:
                await asyncio.sleep(RATE_LIMIT_DELAY)
                detail = await self.get_position_detail(pos["choix"], pos["chapter"], pos["code"])
                detail["designation"] = pos["designation"]
                all_results.append(detail)

            logger.info(f"Chapter {ch}: {len(sample)} sample positions scraped")

        return all_results

    async def scrape_all(self, save_progress: bool = True):
        data_dir = Path(__file__).parent.parent.parent / "data" / "crawled"
        data_dir.mkdir(parents=True, exist_ok=True)

        all_results = []
        for ch in CHAPTERS:
            results = await self.scrape_chapter(ch)
            all_results.extend(results)

            if save_progress and results:
                progress_path = data_dir / f"TUN_chapter_{ch}.json"
                with open(progress_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

        final_path = data_dir / "TUN_crawled.json"
        with open(final_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        logger.info(f"Tunisia: {len(all_results)} total positions saved to {final_path}")
        return all_results

    def save_csv(self, results: list, output_path: str):
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "Chapitre", "Code_NDP_11_chiffres", "Designation",
                "Regime_Import", "Regime_Export",
                "Droits_Taxes_Import", "Droits_Taxes_Export",
                "Preferences_Tarifaires", "Reglementation",
                "Groupe_Utilisation", "Mode_Paiement", "Source"
            ])

            for r in results:
                import_taxes = []
                for t in r.get("taxes_import", []):
                    rate = t.get("raw_value", "")
                    name = t.get("name", t.get("code", ""))
                    import_taxes.append(f"{name}: {rate}")

                export_taxes = []
                for t in r.get("taxes_export", []):
                    rate = t.get("raw_value", "")
                    name = t.get("name", t.get("code", ""))
                    export_taxes.append(f"{name}: {rate}")

                prefs = []
                for p in r.get("preferences", []):
                    prefs.append(f"{p['country_name']}: {p['rate']}")

                regs = []
                for reg in r.get("reglementation_import", []) + r.get("reglementation_export", []):
                    regs.append(reg.get("description", ""))

                writer.writerow([
                    r.get("chapter", ""),
                    r.get("hs_code", ""),
                    r.get("designation", ""),
                    r.get("import_status", ""),
                    r.get("export_status", ""),
                    " | ".join(import_taxes),
                    " | ".join(export_taxes),
                    " | ".join(prefs),
                    " | ".join(regs),
                    r.get("groupe_utilisation", ""),
                    r.get("mode_paiement", ""),
                    self.source,
                ])
