"""
Crawler pour extraire les positions tarifaires nationales algériennes
Source: conformepro.dz (données issues de douane.gov.dz)
Structure: Section → Chapitre → Rangée (HS4) → Sous-position (HS8/HS10)
Données extraites: code SH, désignation exacte, DD, TVA, TCS, PRCT, DAPS, formalités
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://conformepro.dz/resources/tarif-douanier"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
}

RATE_LIMIT_DELAY = 1.5


class AlgeriaConformeproScraper:
    def __init__(self):
        self.client = None
        self.sections = []
        self.chapters = []
        self.headings = []
        self.sub_positions = []
        self.errors = []
        self.stats = {
            "sections": 0,
            "chapters": 0,
            "headings": 0,
            "sub_positions": 0,
            "errors": 0,
            "started_at": None,
            "finished_at": None,
        }

    async def _init_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(
                headers=HEADERS,
                timeout=30.0,
                follow_redirects=True,
                verify=False,
            )

    async def _close_client(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        await self._init_client()
        for attempt in range(retries):
            try:
                await asyncio.sleep(RATE_LIMIT_DELAY)
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    return resp.text
                logger.warning(f"HTTP {resp.status_code} for {url}")
                if resp.status_code == 429:
                    await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Fetch error (attempt {attempt+1}) for {url}: {e}")
                await asyncio.sleep(3)
        self.errors.append({"url": url, "error": "Max retries exceeded"})
        self.stats["errors"] += 1
        return None

    def _extract_links(self, html: str, pattern: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if pattern in href:
                text = a.get_text(strip=True)
                if text:
                    bold = a.find("strong")
                    title = bold.get_text(strip=True) if bold else ""
                    links.append({
                        "url": href,
                        "text": text,
                        "title": title,
                    })
        return links

    async def scrape_sections(self) -> List[Dict]:
        logger.info("Scraping sections...")
        html = await self._fetch_page(BASE_URL)
        if not html:
            return []

        sections = []
        links = self._extract_links(html, "/resources/tarif-douanier/section/")
        for link in links:
            url = link["url"]
            if not url.startswith("http"):
                url = f"https://conformepro.dz{url}"
            m = re.search(r"/section/(\d+)/", url)
            if m:
                sections.append({
                    "code": m.group(1),
                    "name": link["title"] or link["text"],
                    "url": url,
                })

        seen = set()
        unique = []
        for s in sections:
            if s["code"] not in seen:
                seen.add(s["code"])
                unique.append(s)
        self.sections = unique
        self.stats["sections"] = len(unique)
        logger.info(f"Found {len(unique)} sections")
        return unique

    async def scrape_chapters(self) -> List[Dict]:
        logger.info("Scraping chapters from all sections...")
        chapters = []

        for section in self.sections:
            html = await self._fetch_page(section["url"])
            if not html:
                continue

            links = self._extract_links(html, "/resources/tarif-douanier/chapitre/")
            for link in links:
                url = link["url"]
                if not url.startswith("http"):
                    url = f"https://conformepro.dz{url}"
                m = re.search(r"/chapitre/(\d+)/", url)
                if m:
                    chapters.append({
                        "code": m.group(1),
                        "name": link["title"] or link["text"],
                        "url": url,
                        "section": section["code"],
                    })

        seen = set()
        unique = []
        for c in chapters:
            if c["code"] not in seen:
                seen.add(c["code"])
                unique.append(c)
        self.chapters = unique
        self.stats["chapters"] = len(unique)
        logger.info(f"Found {len(unique)} chapters")
        return unique

    async def scrape_headings(self) -> List[Dict]:
        logger.info("Scraping headings (rangées) from all chapters...")
        headings = []

        for i, chapter in enumerate(self.chapters):
            logger.info(f"  Chapter {chapter['code']} ({i+1}/{len(self.chapters)})")
            html = await self._fetch_page(chapter["url"])
            if not html:
                continue

            links = self._extract_links(html, "/resources/tarif-douanier/rangee/")
            for link in links:
                url = link["url"]
                if not url.startswith("http"):
                    url = f"https://conformepro.dz{url}"
                m = re.search(r"/rangee/([\d.]+)/", url)
                if m:
                    headings.append({
                        "code": m.group(1),
                        "name": link["title"] or link["text"],
                        "url": url,
                        "chapter": chapter["code"],
                        "section": chapter["section"],
                    })

        seen = set()
        unique = []
        for h in headings:
            if h["code"] not in seen:
                seen.add(h["code"])
                unique.append(h)
        self.headings = unique
        self.stats["headings"] = len(unique)
        logger.info(f"Found {len(unique)} headings")
        return unique

    async def scrape_sub_positions_for_heading(self, heading: Dict) -> List[Dict]:
        html = await self._fetch_page(heading["url"])
        if not html:
            return []

        subs = []
        links = self._extract_links(html, "/resources/tarif-douanier/sous-position/")
        for link in links:
            url = link["url"]
            if not url.startswith("http"):
                url = f"https://conformepro.dz{url}"
            m = re.search(r"/sous-position/([\d.]+)/", url)
            if m:
                raw_code = m.group(1)
                subs.append({
                    "raw_code": raw_code,
                    "name": link["title"] or link["text"],
                    "url": url,
                    "heading": heading["code"],
                    "chapter": heading["chapter"],
                    "section": heading["section"],
                })
        return subs

    async def scrape_sub_position_detail(self, sub: Dict) -> Dict:
        html = await self._fetch_page(sub["url"])
        if not html:
            return sub

        soup = BeautifulSoup(html, "html.parser")

        result = {
            "raw_code": sub["raw_code"],
            "heading": sub["heading"],
            "chapter": sub["chapter"],
            "section": sub["section"],
            "name": sub["name"],
            "taxes": {},
            "advantages": [],
            "formalities": [],
            "source": "conformepro.dz",
            "source_url": sub["url"],
        }

        result["hs_code"] = sub["raw_code"].replace(".", "")

        h1 = soup.find("h1")
        if h1:
            h1_text = h1.get_text(strip=True)
            prefix = "Le tarif douanier algérien pour"
            if prefix in h1_text:
                result["designation"] = h1_text.replace(prefix, "").strip()
            else:
                result["designation"] = h1_text

        designation_h2 = soup.find("h2", string=re.compile(r"[Dd]ésignation", re.I))
        if designation_h2:
            texts = []
            for sibling in designation_h2.next_siblings:
                if sibling.name == "h2":
                    break
                if hasattr(sibling, "get_text"):
                    t = sibling.get_text(strip=True)
                    if t:
                        texts.append(t)
                elif isinstance(sibling, str) and sibling.strip():
                    texts.append(sibling.strip())
            if texts:
                result["designation_full"] = " > ".join(texts)

        tax_names = {
            "Droit de douane": "DD",
            "TVA": "TVA",
            "TCS": "TCS",
            "PRCT": "PRCT",
            "DAPS": "DAPS",
            "TIC": "TIC",
        }

        for label, key in tax_names.items():
            h2 = soup.find("h2", string=re.compile(rf"^{re.escape(label)}$", re.I))
            if not h2:
                h2 = soup.find("h2", string=re.compile(rf"{re.escape(label)}", re.I))
            if h2:
                next_el = h2.find_next(["p", "div"])
                if next_el:
                    val_text = next_el.get_text(strip=True)
                    rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%?", val_text)
                    if rate_match:
                        rate = float(rate_match.group(1).replace(",", "."))
                        result["taxes"][key] = {
                            "name": label,
                            "rate": rate,
                            "raw": val_text,
                        }

        advantages_h2 = soup.find("h2", string=re.compile(r"[Aa]vantages?", re.I))
        if advantages_h2:
            ul = advantages_h2.find_next("ul")
            if ul:
                for li in ul.find_all("li"):
                    text = li.get_text(strip=True)
                    if text and "copies licence invalides" not in text.lower():
                        result["advantages"].append(text)

        formalities_h2 = soup.find("h2", string=re.compile(r"[Ff]ormalit", re.I))
        if formalities_h2:
            ul = formalities_h2.find_next("ul")
            if ul:
                for li in ul.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        result["formalities"].append(text)
            else:
                texts = []
                for sib in formalities_h2.next_siblings:
                    if sib.name == "h2":
                        break
                    if hasattr(sib, "get_text"):
                        t = sib.get_text(strip=True)
                        if t:
                            for part in re.split(r"(?<=[a-zé\)])(?=[A-Z])", t):
                                part = part.strip()
                                if part:
                                    texts.append(part)
                result["formalities"] = texts

        return result

    async def scrape_all_sub_positions(self, start_heading_idx: int = 0, max_headings: int = None):
        logger.info(f"Scraping sub-positions from {len(self.headings)} headings...")
        all_subs = []
        end_idx = len(self.headings) if max_headings is None else min(start_heading_idx + max_headings, len(self.headings))

        for i in range(start_heading_idx, end_idx):
            heading = self.headings[i]
            logger.info(f"  Heading {heading['code']} ({i+1}/{len(self.headings)})")

            subs = await self.scrape_sub_positions_for_heading(heading)
            logger.info(f"    Found {len(subs)} sub-positions, fetching details...")

            for j, sub in enumerate(subs):
                detail = await self.scrape_sub_position_detail(sub)
                all_subs.append(detail)

                if (j + 1) % 50 == 0:
                    logger.info(f"    Progress: {j+1}/{len(subs)} sub-positions")

            if (i + 1) % 5 == 0:
                self._save_progress(all_subs, f"DZA_progress_{i+1}")
                logger.info(f"  Progress saved: {len(all_subs)} sub-positions so far")

        self.sub_positions.extend(all_subs)
        self.stats["sub_positions"] = len(self.sub_positions)
        return all_subs

    def _save_progress(self, data: List[Dict], filename: str):
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, f"{filename}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "country": "DZA",
                "source": "conformepro.dz",
                "extracted_at": datetime.utcnow().isoformat(),
                "count": len(data),
                "data": data,
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} records to {filepath}")

    def save_final(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.stats["finished_at"] = datetime.utcnow().isoformat()

        structure = {
            "country": "DZA",
            "country_name": "Algérie",
            "source": "conformepro.dz (données douane.gov.dz)",
            "extracted_at": datetime.utcnow().isoformat(),
            "stats": self.stats,
            "sections": self.sections,
            "chapters": self.chapters,
        }
        with open(os.path.join(DATA_DIR, "DZA_structure.json"), "w", encoding="utf-8") as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        tariff_data = {
            "country": "DZA",
            "country_name": "Algérie",
            "source": "conformepro.dz (données douane.gov.dz)",
            "extracted_at": datetime.utcnow().isoformat(),
            "stats": self.stats,
            "sub_positions": self.sub_positions,
        }
        with open(os.path.join(DATA_DIR, "DZA_tariffs.json"), "w", encoding="utf-8") as f:
            json.dump(tariff_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Final data saved: {len(self.sub_positions)} sub-positions")
        logger.info(f"Stats: {json.dumps(self.stats, indent=2)}")

    async def run(self, max_headings: int = None):
        self.stats["started_at"] = datetime.utcnow().isoformat()
        logger.info("=== Algeria Tariff Scraper (conformepro.dz) ===")

        try:
            await self.scrape_sections()
            await self.scrape_chapters()
            await self.scrape_headings()
            await self.scrape_all_sub_positions(max_headings=max_headings)
            self.save_final()
        finally:
            await self._close_client()

        return {
            "success": True,
            "stats": self.stats,
            "sub_positions_count": len(self.sub_positions),
        }


async def run_algeria_scraper(max_headings: int = None):
    scraper = AlgeriaConformeproScraper()
    return await scraper.run(max_headings=max_headings)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_algeria_scraper(max_headings=5))
    print(json.dumps(result, indent=2, ensure_ascii=False))
