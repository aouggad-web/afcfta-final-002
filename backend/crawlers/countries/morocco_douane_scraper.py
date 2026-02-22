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

RATE_LIMIT_DELAY = 2.0

BASE_URL = "https://www.douane.gov.ma"
INFO_0_URL = f"{BASE_URL}/adil/info_0.asp"
SEARCH_URL = f"{BASE_URL}/adil/rsearch1.asp"
FORM_URL = f"{BASE_URL}/adil/envoi_position.asp"

CHAPTERS = [f"{i:02d}" for i in range(1, 98) if i != 77]


class MoroccoDouaneScraper:
    def __init__(self):
        self.country_code = "MAR"
        self.source = "douane.gov.ma/adil"

    def _new_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=60.0,
            verify=False,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9",
            }
        )

    def _decode(self, content: bytes) -> str:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("utf-8", errors="replace")

    async def get_chapter_positions(self, chapter: str) -> list:
        client = self._new_client()
        try:
            url = f"{INFO_0_URL}?pos={chapter}0100"
            resp = await client.get(url)
            if resp.status_code != 200:
                return []

            html = self._decode(resp.content)
            soup = BeautifulSoup(html, "html.parser")

            positions = []
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                match = re.search(r"info_x\.asp\?position=(\d{10})", href)
                if match:
                    code = match.group(1)
                    if code[:2] == chapter and code not in seen:
                        seen.add(code)
                        designation = a.get_text(strip=True)
                        designation = re.sub(r"^-+\s*", "", designation)
                        positions.append({
                            "code": code,
                            "designation": designation,
                            "chapter": chapter,
                        })
            return positions
        finally:
            await client.aclose()

    async def get_position_taxes(self, client: httpx.AsyncClient, code: str) -> dict:
        url = f"{BASE_URL}/adil/info_2.asp?pos={code}"
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return {}

            html = self._decode(resp.content)
            soup = BeautifulSoup(html, "html.parser")

            taxes = {}
            for td in soup.find_all("td"):
                text = td.get_text(strip=True)

                di_match = re.search(r"Droit\s+d['\u2019]Importation.*?\(\s*DI\s*\)\s*:\s*([\d,\.]+)\s*%", text)
                if di_match:
                    taxes["Droit d'Importation (DI)"] = di_match.group(1).replace(",", ".") + " %"

                tpi_match = re.search(r"Taxe\s+Parafiscale.*?\(\s*TPI\s*\)\s*:\s*([\d,\.]+)\s*%", text)
                if tpi_match:
                    taxes["Taxe Parafiscale à l'Importation (TPI)"] = tpi_match.group(1).replace(",", ".") + " %"

                tva_match = re.search(r"Taxe\s+sur\s+la\s+Valeur\s+Ajout.*?\(\s*TVA\s*\)\s*:\s*([\d,\.]+)\s*%", text)
                if tva_match:
                    taxes["Taxe sur la Valeur Ajoutée (TVA)"] = tva_match.group(1).replace(",", ".") + " %"

                tic_match = re.search(r"Taxe\s+Int.*?rieure.*?Consommation.*?\(\s*TIC\s*\)\s*:\s*([\d,\.]+)", text)
                if tic_match:
                    val = tic_match.group(1).replace(",", ".")
                    if "%" in text[text.find("TIC"):]:
                        taxes["Taxe Intérieure de Consommation (TIC)"] = val + " %"
                    else:
                        taxes["Taxe Intérieure de Consommation (TIC)"] = val + " DH"

            return taxes
        except Exception as e:
            logger.warning(f"Error getting taxes for {code}: {e}")
            return {}

    async def get_position_formalities(self, client: httpx.AsyncClient, code: str) -> list:
        url = f"{BASE_URL}/adil/info_4.asp?pos={code}"
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []

            html = self._decode(resp.content)
            soup = BeautifulSoup(html, "html.parser")

            formalities = []
            for td in soup.find_all("td"):
                text = td.get_text(strip=True)
                if len(text) > 10 and any(k in text.lower() for k in [
                    "contrôle", "certificat", "autorisation", "licence",
                    "visa", "norme", "phytosanitaire", "vétérinaire",
                    "sanitaire", "conformité", "agrément", "homologation",
                ]):
                    if text not in formalities:
                        formalities.append(text)

            return formalities
        except Exception as e:
            logger.warning(f"Error getting formalities for {code}: {e}")
            return []

    async def get_position_preferences(self, client: httpx.AsyncClient, code: str) -> list:
        url = f"{BASE_URL}/adil/info_3.asp?pos={code}"
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []

            html = self._decode(resp.content)
            soup = BeautifulSoup(html, "html.parser")

            preferences = []
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        text = " | ".join(c.get_text(strip=True) for c in cells if c.get_text(strip=True))
                        if text and "%" in text:
                            preferences.append(text)

            return preferences
        except Exception as e:
            logger.warning(f"Error getting preferences for {code}: {e}")
            return []

    async def scrape_position_details(self, code: str) -> dict:
        client = self._new_client()
        try:
            await client.get(f"{BASE_URL}/adil/")
            await client.get(FORM_URL)

            resp = await client.post(
                SEARCH_URL,
                data={"lposition": code},
                headers={
                    "Referer": FORM_URL,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            taxes = await self.get_position_taxes(client, code)
            formalities = await self.get_position_formalities(client, code)

            return {
                "taxes": taxes,
                "formalities": formalities,
            }
        finally:
            await client.aclose()

    async def scrape_chapter_with_taxes(self, chapter: str, progress_callback=None) -> list:
        logger.info(f"Morocco: Scraping chapter {chapter} positions...")

        positions = await self.get_chapter_positions(chapter)
        if not positions:
            logger.warning(f"Morocco: No positions found for chapter {chapter}")
            return []

        logger.info(f"Morocco: Chapter {chapter} has {len(positions)} positions, fetching taxes...")

        client = self._new_client()
        try:
            await client.get(f"{BASE_URL}/adil/")
            await client.get(FORM_URL)

            for i, pos in enumerate(positions):
                code = pos["code"]

                resp = await client.post(
                    SEARCH_URL,
                    data={"lposition": code},
                    headers={
                        "Referer": FORM_URL,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                taxes = await self.get_position_taxes(client, code)
                formalities = await self.get_position_formalities(client, code)

                pos["taxes"] = taxes
                pos["formalities"] = formalities

                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(chapter, i + 1, len(positions))

                await asyncio.sleep(RATE_LIMIT_DELAY)

            return positions
        finally:
            await client.aclose()

    async def scrape_sample(self, chapters: list = None, max_per_chapter: int = 5) -> list:
        if chapters is None:
            chapters = ["01", "04", "10", "17", "27", "30", "39", "72", "84", "87"]

        all_results = []
        for ch in chapters:
            await asyncio.sleep(RATE_LIMIT_DELAY)
            positions = await self.get_chapter_positions(ch)
            if not positions:
                continue

            sample = positions[:max_per_chapter]

            client = self._new_client()
            try:
                await client.get(f"{BASE_URL}/adil/")
                await client.get(FORM_URL)

                for pos in sample:
                    code = pos["code"]
                    await client.post(
                        SEARCH_URL,
                        data={"lposition": code},
                        headers={
                            "Referer": FORM_URL,
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                    )
                    pos["taxes"] = await self.get_position_taxes(client, code)
                    pos["formalities"] = await self.get_position_formalities(client, code)
                    await asyncio.sleep(RATE_LIMIT_DELAY)
            finally:
                await client.aclose()

            all_results.extend(sample)
            logger.info(f"Chapter {ch}: {len(positions)} positions, sampled {len(sample)}")

        return all_results

    async def scrape_all_positions(self, save_progress: bool = True) -> list:
        data_dir = Path(__file__).parent.parent.parent / "data" / "crawled"
        data_dir.mkdir(parents=True, exist_ok=True)

        all_positions = []
        for ch in CHAPTERS:
            chapter_data = await self.scrape_chapter_with_taxes(ch)
            all_positions.extend(chapter_data)

            if save_progress and chapter_data:
                progress_path = data_dir / f"MAR_chapter_{ch}.json"
                with open(progress_path, "w", encoding="utf-8") as f:
                    json.dump(chapter_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Chapter {ch}: {len(chapter_data)} positions (total: {len(all_positions)})")

        final_path = data_dir / "MAR_crawled.json"
        with open(final_path, "w", encoding="utf-8") as f:
            json.dump({
                "country_code": "MAR",
                "country_name": "Maroc",
                "source": self.source,
                "total_positions": len(all_positions),
                "positions": all_positions,
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Morocco: {len(all_positions)} total positions saved")
        return all_positions

    def save_csv(self, results: list, output_path: str):
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "Chapitre",
                "Code_Position_10_chiffres",
                "Designation",
                "Droit_Importation_DI",
                "Taxe_Parafiscale_Importation_TPI",
                "Taxe_Valeur_Ajoutee_TVA",
                "Taxe_Interieure_Consommation_TIC",
                "Formalites_particulieres",
                "Source"
            ])

            for r in results:
                taxes = r.get("taxes", {})
                formalities = r.get("formalities", [])

                writer.writerow([
                    r.get("chapter", r.get("code", "")[:2]),
                    r.get("code", ""),
                    r.get("designation", ""),
                    taxes.get("Droit d'Importation (DI)", ""),
                    taxes.get("Taxe Parafiscale à l'Importation (TPI)", ""),
                    taxes.get("Taxe sur la Valeur Ajoutée (TVA)", ""),
                    taxes.get("Taxe Intérieure de Consommation (TIC)", ""),
                    " | ".join(formalities) if formalities else "",
                    self.source,
                ])
