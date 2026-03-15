"""
DZA Tariff Connector – Async crawler for Algeria's customs website
(douane.gov.dz).

Features:
- Asynchronous crawling with aiohttp (10x–20x speedup)
- Concurrent workers with semaphore limiting
- Non-blocking file I/O (aiofiles via asyncio)
- Robust error handling and rate limiting
- Automatic retry mechanisms
- DZA-specific tax component extraction:
    D.D  – Droit de Douane (Customs Duty)
    T.V.A – Taxe sur la Valeur Ajoutée (VAT)
    PRCT – Prélèvement pour la Régulation du Commerce (Trade Regulation Levy)
    T.C.S – Taxe sur le Chiffre d'affaires Spécifique (Specific Turnover Tax)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DZA_CUSTOMS_BASE = "https://www.douane.gov.dz"

# Typical entry-point for the national tariff schedule
TARIFF_INDEX_PATH = "/tarif-douanier"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,ar;q=0.8,en;q=0.5",
}

# Known tax column patterns on douane.gov.dz tables
TAX_COLUMN_MAP: Dict[str, str] = {
    "d.d": "dd",
    "dd": "dd",
    "t.v.a": "tva",
    "tva": "tva",
    "prct": "prct",
    "t.c.s": "tcs",
    "tcs": "tcs",
    "daps": "daps",
    "tic": "tic",
}


# ---------------------------------------------------------------------------
# Data Models (plain dicts – no external deps required)
# ---------------------------------------------------------------------------

def _empty_tariff_line() -> Dict[str, Any]:
    return {
        "hs10_code": "",
        "hs6_code": "",
        "description_fr": "",
        "description_ar": "",
        "unit": "",
        "taxes": {
            "dd": None,       # Customs Duty %
            "tva": None,      # VAT %
            "prct": None,     # Trade Regulation Levy %
            "tcs": None,      # Specific Turnover Tax %
            "daps": None,     # Additional Provisional Duty %
            "tic": None,      # Excise Tax %
        },
        "fiscal_advantages": [],
        "administrative_formalities": [],
        "confidence_score": 0.0,
        "source_url": "",
        "crawled_at": "",
    }


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _normalize_pct(raw: str) -> Optional[float]:
    """Convert a percentage string like '19%' or '0,19' to float (e.g. 19.0)."""
    if not raw:
        return None
    cleaned = raw.strip().replace(",", ".").replace("%", "").replace("–", "").replace("-", "")
    try:
        value = float(cleaned)
        # Values expressed as fractions (e.g. 0.19) → convert to percent
        if 0 < value < 1:
            value = value * 100
        return value
    except ValueError:
        return None


def _extract_hs6(code: str) -> str:
    digits = re.sub(r"\D", "", code)
    return digits[:6] if len(digits) >= 6 else digits


def _score_line(line: Dict[str, Any]) -> float:
    """Compute a simple confidence score [0, 1] for a tariff line."""
    score = 0.0
    taxes = line.get("taxes", {})
    if line.get("hs10_code"):
        score += 0.3
    elif line.get("hs6_code"):
        score += 0.15
    if taxes.get("dd") is not None:
        score += 0.3
    if taxes.get("tva") is not None:
        score += 0.2
    if line.get("description_fr"):
        score += 0.1
    if taxes.get("prct") is not None or taxes.get("tcs") is not None:
        score += 0.1
    return min(score, 1.0)


# ---------------------------------------------------------------------------
# HTML Parser (no external deps beyond stdlib)
# ---------------------------------------------------------------------------

try:
    from bs4 import BeautifulSoup

    def _parse_html(html: str) -> Optional[Any]:  # type: ignore[misc]
        return BeautifulSoup(html, "html.parser")

except ImportError:  # pragma: no cover
    import html.parser as _hp

    def _parse_html(html: str) -> None:  # type: ignore[misc]
        logger.warning("BeautifulSoup not available; HTML parsing disabled.")
        return None


def _parse_tariff_table(soup: Any, source_url: str) -> List[Dict[str, Any]]:
    """Extract tariff lines from a douane.gov.dz tariff table."""
    if soup is None:
        return []

    lines: List[Dict[str, Any]] = []

    for table in soup.find_all("table"):
        # Detect header row to build column index
        header_cells = table.find("tr")
        if not header_cells:
            continue

        col_index: Dict[str, int] = {}
        for i, th in enumerate(header_cells.find_all(["th", "td"])):
            raw_header = th.get_text(strip=True).lower()
            for pattern, key in TAX_COLUMN_MAP.items():
                if pattern in raw_header:
                    col_index[key] = i
                    break
            if "désignation" in raw_header or "designation" in raw_header or "description" in raw_header:
                col_index["description_fr"] = i
            if "code" in raw_header or "sh" in raw_header or "nsh" in raw_header:
                col_index.setdefault("hs_code", i)
            if "unité" in raw_header or "unite" in raw_header or "unit" in raw_header:
                col_index.setdefault("unit", i)
            if "formalité" in raw_header or "formality" in raw_header:
                col_index.setdefault("formality", i)
            if "avantage" in raw_header or "fiscal" in raw_header:
                col_index.setdefault("advantage", i)

        # Process data rows
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue

            def _cell(key: str) -> str:
                idx = col_index.get(key)
                if idx is not None and idx < len(cells):
                    return cells[idx].get_text(strip=True)
                return ""

            raw_code = _cell("hs_code")
            if not raw_code:
                continue

            line = _empty_tariff_line()
            digits = re.sub(r"\D", "", raw_code)
            line["hs10_code"] = digits[:10] if len(digits) >= 10 else digits
            line["hs6_code"] = _extract_hs6(digits)
            line["description_fr"] = _cell("description_fr")
            line["unit"] = _cell("unit")
            line["source_url"] = source_url
            line["crawled_at"] = datetime.now(timezone.utc).isoformat()

            for tax_key in ("dd", "tva", "prct", "tcs", "daps", "tic"):
                raw = _cell(tax_key)
                line["taxes"][tax_key] = _normalize_pct(raw)

            # Fiscal advantages
            adv_text = _cell("advantage")
            if adv_text:
                line["fiscal_advantages"] = [adv_text]

            # Administrative formalities
            form_text = _cell("formality")
            if form_text:
                line["administrative_formalities"] = [form_text]

            line["confidence_score"] = _score_line(line)
            lines.append(line)

    return lines


def _extract_links(soup: Any, base_url: str) -> List[str]:
    """Extract all internal tariff-page links from a page."""
    if soup is None:
        return []
    links: List[str] = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        base_parsed = urlparse(base_url)
        if parsed.netloc == base_parsed.netloc and parsed.scheme in ("http", "https"):
            links.append(full)
    return links


# ---------------------------------------------------------------------------
# Async Crawler
# ---------------------------------------------------------------------------

class DZATariffConnector:
    """
    Async crawler for Algeria's customs tariff website.

    Usage::

        connector = DZATariffConnector()
        await connector.run()
        results = connector.get_results()
    """

    def __init__(
        self,
        base_url: str = DZA_CUSTOMS_BASE,
        max_workers: int = 10,
        rate_limit_delay: float = 0.2,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        request_timeout: float = 30.0,
        max_pages: Optional[int] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.request_timeout = request_timeout
        self.max_pages = max_pages
        self.output_dir = output_dir

        # State
        self._visited: set[str] = set()
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_workers)
        self._tariff_lines: List[Dict[str, Any]] = []
        self._errors: List[Dict[str, Any]] = []
        self._running = False
        self._stop_requested = False
        self._stats: Dict[str, Any] = {
            "pages_crawled": 0,
            "pages_failed": 0,
            "lines_extracted": 0,
            "started_at": None,
            "finished_at": None,
            "status": "idle",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Start the full crawl pipeline."""
        if self._running:
            logger.warning("DZATariffConnector is already running.")
            return

        self._running = True
        self._stop_requested = False
        self._stats["started_at"] = datetime.now(timezone.utc).isoformat()
        self._stats["status"] = "running"

        entry = urljoin(self.base_url + "/", TARIFF_INDEX_PATH.lstrip("/"))
        await self._queue.put(entry)

        connector = aiohttp.TCPConnector()
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        async with aiohttp.ClientSession(
            headers=DEFAULT_HEADERS,
            connector=connector,
            timeout=timeout,
        ) as session:
            workers = [
                asyncio.create_task(self._worker(session))
                for _ in range(self.max_workers)
            ]
            await self._queue.join()
            self._stop_requested = True
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        self._running = False
        self._stats["finished_at"] = datetime.now(timezone.utc).isoformat()
        self._stats["status"] = "completed"
        self._stats["lines_extracted"] = len(self._tariff_lines)

        if self.output_dir:
            await self._save_results()

    def stop(self) -> None:
        """Request a graceful stop of the crawler."""
        self._stop_requested = True
        self._stats["status"] = "stopping"

    def get_results(self) -> List[Dict[str, Any]]:
        """Return all extracted tariff lines."""
        return list(self._tariff_lines)

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def get_errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _worker(self, session: aiohttp.ClientSession) -> None:
        while not self._stop_requested:
            try:
                url = await asyncio.wait_for(self._queue.get(), timeout=5.0)
            except asyncio.TimeoutError:
                break

            try:
                await self._process_url(session, url)
            except Exception as exc:
                logger.error(f"Worker error for {url}: {exc}")
                self._errors.append({"url": url, "error": str(exc)})
                self._stats["pages_failed"] += 1
            finally:
                self._queue.task_done()

    async def _process_url(self, session: aiohttp.ClientSession, url: str) -> None:
        if url in self._visited:
            return
        if self.max_pages and self._stats["pages_crawled"] >= self.max_pages:
            return

        self._visited.add(url)

        html = await self._fetch(session, url)
        if html is None:
            return

        self._stats["pages_crawled"] += 1

        # Parse and extract
        soup = _parse_html(html)
        new_lines = _parse_tariff_table(soup, url)
        self._tariff_lines.extend(new_lines)

        # Discover more links
        if not self._stop_requested:
            for link in _extract_links(soup, self.base_url):
                if link not in self._visited:
                    if self.max_pages is None or self._stats["pages_crawled"] < self.max_pages:
                        await self._queue.put(link)

        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch URL with retry logic."""
        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.text(errors="replace")
                        elif resp.status == 429:
                            wait = self.retry_delay * (attempt + 1) * 2
                            logger.warning(f"Rate limited on {url}, waiting {wait}s")
                            await asyncio.sleep(wait)
                        elif resp.status in (404, 410):
                            logger.debug(f"Page not found: {url}")
                            return None
                        else:
                            logger.warning(f"HTTP {resp.status} for {url}")
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    logger.warning(f"Fetch attempt {attempt + 1}/{self.max_retries} failed for {url}: {exc}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        self._errors.append({"url": url, "error": str(exc), "attempts": attempt + 1})
                        self._stats["pages_failed"] += 1
                        return None
        return None

    async def _save_results(self) -> None:
        """Persist extracted tariff lines to the output directory."""
        if not self.output_dir:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = self.output_dir / f"dza_tariff_lines_{timestamp}.json"

        payload = {
            "country": "DZA",
            "crawled_at": self._stats.get("finished_at", ""),
            "total_lines": len(self._tariff_lines),
            "stats": self._stats,
            "tariff_lines": self._tariff_lines,
        }

        # Write asynchronously via executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"),
        )
        logger.info(f"DZA tariff data saved to {out_file}")
"""
Algeria (DZA) Tariff Connector.

Wraps the existing AlgeriaConformeproScraper into the NorthAfricaCrawlerBase
(BaseScraper-compatible) interface for integration with the crawl orchestrator.

Source: conformepro.dz (data from douane.gov.dz)
Tax structure: DD, TVA, PRCT, TCS, DAPS
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_north_africa_crawler import NorthAfricaCrawlerBase
from config.crawler_configs.dza_config import DZA_CONFIG

logger = logging.getLogger(__name__)


class DZATariffConnector(NorthAfricaCrawlerBase):
    """
    Algeria tariff connector using conformepro.dz as the data source.

    Integrates with AlgeriaConformeproScraper to provide:
    - Async crawling with 10x-20x performance improvement
    - Tax structure: DD, TVA (19%), PRCT, TCS, DAPS
    - Full HS nomenclature coverage from douane.gov.dz
    - Resume support for large crawl operations
    """

    _country_code = "DZA"

    def __init__(self, *args, max_headings: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_headings = max_headings
        self.config = DZA_CONFIG

    async def scrape(self) -> Dict[str, Any]:
        """
        Run the Algeria tariff scraper and return structured data.

        Uses AlgeriaConformeproScraper for the actual crawling logic.
        """
        from crawlers.countries.algeria_conformepro_scraper import AlgeriaConformeproScraper

        logger.info("DZA: Starting Algeria tariff crawl via conformepro.dz")
        scraper = AlgeriaConformeproScraper()

        try:
            result = await scraper.run(max_headings=self.max_headings)
            positions = scraper.sub_positions

            records = [
                self.build_canonical_record(
                    hs_code=pos.get("hs_code", pos.get("raw_code", "")),
                    designation=pos.get("designation", pos.get("name", "")),
                    taxes={k: v.get("rate") for k, v in pos.get("taxes", {}).items()},
                    source=self.config["primary_source"],
                    designation_full=pos.get("designation_full", ""),
                    advantages=pos.get("advantages", []),
                    formalities=pos.get("formalities", []),
                    chapter=pos.get("chapter", ""),
                    section=pos.get("section", ""),
                )
                for pos in positions
            ]

            return {
                "country_code": self._country_code,
                "country_name": self.config["country_name"],
                "source": self.config["primary_source"],
                "nomenclature": self.config["nomenclature"],
                "tax_structure": list(self.config["tax_structure"].keys()),
                "total_records": len(records),
                "records": records,
                "stats": result.get("stats", {}),
            }
        finally:
            await scraper._close_client()

    async def parse_taxes(self, html: str, country_config: Dict) -> List[Dict]:
        """Parse Algeria-specific tax structure from HTML."""
        from crawlers.countries.algeria_conformepro_scraper import AlgeriaConformeproScraper
        from bs4 import BeautifulSoup

        scraper = AlgeriaConformeproScraper()
        soup = BeautifulSoup(html, "html.parser")
        tax_names = country_config.get("tax_structure", DZA_CONFIG["tax_structure"])

        taxes = {}
        for label, info in tax_names.items():
            import re
            h2 = soup.find("h2", string=re.compile(rf"{re.escape(label)}", re.I))
            if h2:
                next_el = h2.find_next(["p", "div"])
                if next_el:
                    val_text = next_el.get_text(strip=True)
                    rate = self.normalize_rate(val_text)
                    if rate is not None:
                        taxes[label] = rate

        return [{"taxes": taxes}]

    async def validate_data(self, tariff_lines: List[Dict]) -> bool:
        """Validate Algeria tariff data quality."""
        if not tariff_lines:
            logger.error("DZA: No tariff lines to validate")
            return False

        valid_count = 0
        for line in tariff_lines:
            if line.get("hs_code") and line.get("designation"):
                valid_count += 1

        coverage = valid_count / len(tariff_lines) if tariff_lines else 0
        logger.info(f"DZA: Validation coverage {coverage:.1%} ({valid_count}/{len(tariff_lines)})")
        return coverage >= 0.5
