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
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if pattern not in href or href in seen:
                continue
            seen.add(href)
            text = a.get_text(" ", strip=True)
            if text:
                links.append({"url": href, "text": text})
        return links

    def _parse_rangee_cards(self, html: str, heading: Dict) -> List[Dict]:
        """
        Parse sous-position cards from a rangee listing page.

        Real card DOM (confirmed from conformepro.dz):
          <a href=".../sous-position/01.01.211100/slug">
            <small class="datagrid-title">Sous-position 2111.00</small>
            <h3 class="fw-bold mb-1 text-primary">Short title</h3>
            <p class="text-muted m-0 fs-4">Extended description</p>
          </a>
        """
        soup = BeautifulSoup(html, "html.parser")
        subs = []
        seen = set()

        for card in soup.find_all("a", href=lambda h: h and "/sous-position/" in h):
            href = card.get("href", "")
            if href in seen:
                continue
            seen.add(href)

            url = href if href.startswith("http") else f"https://conformepro.dz{href}"
            m = re.search(r"/sous-position/([\d.]+)/", url)
            if not m:
                continue
            raw_code = m.group(1)

            small = card.find("small", class_="datagrid-title")
            h3 = card.find("h3")
            p = card.find("p")

            display_code = small.get_text(strip=True) if small else ""
            title = h3.get_text(strip=True) if h3 else ""
            description = p.get_text(strip=True) if p else title

            subs.append({
                "raw_code": raw_code,
                "display_code": display_code,
                "name": title,
                "description": description,
                "url": url,
                "heading": heading["code"],
                "chapter": heading["chapter"],
                "section": heading["section"],
            })

        return subs

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
                    "name": link["text"],
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
                        "name": link["text"],
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
                        "name": link["text"],
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
        return self._parse_rangee_cards(html, heading)

    def _parse_vstack(self, soup: BeautifulSoup, label: str) -> str:
        """
        Extract the value from a div.vstack block whose h2 text matches `label`.

        Real detail page DOM (confirmed from conformepro.dz):
          <div class="vstack ...">
            <h2>Droit de douane</h2>
            <p class="fw-bold display-5 m-0">5%</p>
          </div>
          <div class="vstack ...">
            <h2>Désignation complète</h2>
            <div class="fs-3">Animaux vivants > ...</div>
          </div>
          <div class="vstack ...">
            <h2>Avantages</h2>
            <div class="fs-3"><ul><li>...</li></ul></div>
          </div>
        """
        for div in soup.find_all("div", class_="vstack"):
            h2 = div.find("h2")
            if not h2 or h2.get_text(strip=True) != label:
                continue
            p = div.find("p", class_=lambda c: c and "fw-bold" in c)
            if p:
                return p.get_text(strip=True)
            div_fs = div.find("div", class_="fs-3")
            if div_fs:
                items = div_fs.find_all("li")
                if items:
                    return "; ".join(li.get_text(strip=True) for li in items if li.get_text(strip=True))
                return div_fs.get_text(strip=True)
        return ""

    async def scrape_sub_position_detail(self, sub: Dict) -> Dict:
        html = await self._fetch_page(sub["url"])
        if not html:
            return sub

        soup = BeautifulSoup(html, "html.parser")

        result = {
            "raw_code": sub["raw_code"],
            "hs_code": sub["raw_code"].replace(".", ""),
            "display_code": sub.get("display_code", ""),
            "heading": sub["heading"],
            "chapter": sub["chapter"],
            "section": sub["section"],
            "name": sub.get("name", ""),
            "description": sub.get("description", sub.get("name", "")),
            "taxes": {},
            "advantages": [],
            "formalities": [],
            "source": "conformepro.dz",
            "source_url": sub["url"],
        }

        # "Désignation complète" is the authoritative full description
        designation_full = self._parse_vstack(soup, "Désignation complète")
        if designation_full:
            result["designation_full"] = designation_full

        # Tax rates — each lives in its own div.vstack block
        tax_labels = {
            "Droit de douane": "DD",
            "TVA": "TVA",
            "TCS": "TCS",
            "PRCT": "PRCT",
            "DAPS": "DAPS",
            "TIC": "TIC",
        }
        for label, key in tax_labels.items():
            raw = self._parse_vstack(soup, label)
            if raw:
                rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%?", raw)
                if rate_match:
                    result["taxes"][key] = {
                        "name": label,
                        "rate": float(rate_match.group(1).replace(",", ".")),
                        "raw": raw,
                    }

        # Advantages and formalities are in div.vstack with <ul> lists
        advantages_raw = self._parse_vstack(soup, "Avantages")
        if advantages_raw:
            result["advantages"] = [s.strip() for s in advantages_raw.split(";") if s.strip()]

        formalities_raw = self._parse_vstack(soup, "Formalités")
        if formalities_raw:
            result["formalities"] = [s.strip() for s in formalities_raw.split(";") if s.strip()]

        return result

    def _load_last_progress(self):
        import glob as globmod
        progress_files = sorted(
            globmod.glob(os.path.join(DATA_DIR, "DZA_progress_*.json")),
            key=lambda p: int(os.path.basename(p).replace("DZA_progress_", "").replace(".json", ""))
        )
        if progress_files:
            last_file = progress_files[-1]
            try:
                with open(last_file, "r", encoding="utf-8") as f:
                    prev = json.load(f)
                data = prev.get("data", [])
                heading_idx = int(os.path.basename(last_file).replace("DZA_progress_", "").replace(".json", ""))
                logger.info(f"Resume: loaded {len(data)} sub-positions from {os.path.basename(last_file)}, resuming from heading {heading_idx}")
                return data, heading_idx
            except Exception as e:
                logger.warning(f"Could not load progress: {e}")
        return [], 0

    async def scrape_all_sub_positions(self, start_heading_idx: int = 0, max_headings: int = None, resume: bool = True):
        logger.info(f"Scraping sub-positions from {len(self.headings)} headings...")
        all_subs = []
        actual_start = start_heading_idx

        if resume and start_heading_idx == 0:
            prev_data, prev_idx = self._load_last_progress()
            if prev_data:
                all_subs = prev_data
                actual_start = prev_idx
                logger.info(f"Resuming from heading {actual_start} with {len(all_subs)} sub-positions already collected")

        end_idx = len(self.headings) if max_headings is None else min(actual_start + max_headings, len(self.headings))

        for i in range(actual_start, end_idx):
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

    def save_final(self, chapters: set = None):
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

        if chapters:
            # Partial scrape: merge new positions into existing DZA_tariffs.json
            # Keep existing positions for chapters NOT in the requested set
            existing_path = os.path.join(DATA_DIR, "DZA_tariffs.json")
            existing_positions = []
            if os.path.exists(existing_path):
                try:
                    with open(existing_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    existing_positions = [
                        p for p in existing.get("sub_positions", [])
                        if int(p.get("chapter", "0")) not in chapters
                    ]
                    logger.info(f"Kept {len(existing_positions)} existing positions from chapters outside filter")
                except Exception as e:
                    logger.warning(f"Could not load existing DZA_tariffs.json for merge: {e}")

            merged = existing_positions + self.sub_positions
            merged.sort(key=lambda p: p.get("hs_code", ""))
            logger.info(f"Merged total: {len(merged)} positions ({len(existing_positions)} existing + {len(self.sub_positions)} new)")

            tariff_data = {
                "country": "DZA",
                "country_name": "Algérie",
                "source": "conformepro.dz (données douane.gov.dz)",
                "extracted_at": datetime.utcnow().isoformat(),
                "stats": {
                    **self.stats,
                    "total_positions": len(merged),
                    "new_positions": len(self.sub_positions),
                    "chapters_scraped": sorted(chapters),
                },
                "sub_positions": merged,
            }
        else:
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

        logger.info(f"Final data saved: {len(tariff_data['sub_positions'])} sub-positions total")
        logger.info(f"Stats: {json.dumps(self.stats, indent=2)}")

    async def run(self, max_headings: int = None, chapters: set = None):
        self.stats["started_at"] = datetime.utcnow().isoformat()
        logger.info("=== Algeria Tariff Scraper (conformepro.dz) ===")
        if chapters:
            logger.info(f"Chapter filter: {sorted(chapters)}")

        try:
            await self.scrape_sections()
            await self.scrape_chapters()

            if chapters:
                before = len(self.chapters)
                self.chapters = [
                    c for c in self.chapters
                    if int(c["code"]) in chapters
                ]
                logger.info(f"Filtered chapters: {before} → {len(self.chapters)} (requested: {sorted(chapters)})")

            await self.scrape_headings()
            await self.scrape_all_sub_positions(max_headings=max_headings)
            self.save_final(chapters=chapters)
        finally:
            await self._close_client()

        return {
            "success": True,
            "stats": self.stats,
            "sub_positions_count": len(self.sub_positions),
        }


def parse_chapters_arg(chapters_str: str) -> set:
    """
    Parse a chapters argument like '29-76,78-98' into a set of int chapter numbers.
    Supports individual numbers ('29'), ranges ('29-76'), and comma-separated combos.
    """
    result = set()
    for part in chapters_str.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            result.update(range(int(lo), int(hi) + 1))
        elif part.isdigit():
            result.add(int(part))
    return result


async def run_algeria_scraper(max_headings: int = None, chapters: set = None):
    scraper = AlgeriaConformeproScraper()
    return await scraper.run(max_headings=max_headings, chapters=chapters)


async def run_algeria_scraper_fast():
    """
    Fast mode: collect only national tariff positions with card-level descriptions.
    Skips detail page requests (no taxes/formalities). ~15x faster than full mode.
    Output: DZA_tariffs_fast.json
    """
    scraper = AlgeriaConformeproScraper()
    scraper.stats["started_at"] = datetime.utcnow().isoformat()
    logger.info("=== Algeria Tariff Scraper — FAST MODE (positions + descriptions only) ===")

    try:
        await scraper.scrape_sections()
        await scraper.scrape_chapters()
        await scraper.scrape_headings()

        all_subs = []
        for i, heading in enumerate(scraper.headings):
            logger.info(f"  Heading {heading['code']} ({i+1}/{len(scraper.headings)})")
            subs = await scraper.scrape_sub_positions_for_heading(heading)
            for sub in subs:
                all_subs.append({
                    "raw_code": sub["raw_code"],
                    "hs_code": sub["raw_code"].replace(".", ""),
                    "display_code": sub.get("display_code", ""),
                    "heading": sub["heading"],
                    "chapter": sub["chapter"],
                    "section": sub["section"],
                    "name": sub.get("name", ""),
                    "description": sub.get("description", ""),
                    "source": "conformepro.dz",
                    "source_url": sub["url"],
                })
            logger.info(f"    {len(subs)} positions collected (total: {len(all_subs)})")

        scraper.stats["finished_at"] = datetime.utcnow().isoformat()
        scraper.stats["sub_positions"] = len(all_subs)

        output = {
            "country": "DZA",
            "country_name": "Algérie",
            "source": "conformepro.dz (données douane.gov.dz)",
            "mode": "fast — positions and descriptions only",
            "extracted_at": datetime.utcnow().isoformat(),
            "stats": scraper.stats,
            "sub_positions": all_subs,
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        out_path = os.path.join(DATA_DIR, "DZA_tariffs_fast.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(all_subs)} positions to {out_path}")

    finally:
        await scraper._close_client()

    return {"success": True, "count": len(all_subs)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Scraper Algeria conformepro.dz — positions tarifaires nationales (DD, TVA, TCS, PRCT, DAPS)"
    )
    parser.add_argument("--fast", action="store_true",
                        help="Mode rapide : positions + descriptions seulement, sans pages de détail")
    parser.add_argument("--max-headings", type=int, default=None,
                        help="Limiter le nombre de rangées traitées (debug)")
    parser.add_argument("--chapters", type=str, default=None,
                        help="Chapitres à scraper, ex: '29-76,78-98'. Si omis, scrape tous les chapitres.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    chapters_set = None
    if args.chapters:
        chapters_set = parse_chapters_arg(args.chapters)
        print(f"Chapitres demandés: {sorted(chapters_set)} ({len(chapters_set)} chapitres)")

    if args.fast:
        result = asyncio.run(run_algeria_scraper_fast())
    else:
        result = asyncio.run(run_algeria_scraper(max_headings=args.max_headings, chapters=chapters_set))
    print(json.dumps(result, indent=2, ensure_ascii=False))
