"""
Tunisia (TUN) Tariff Crawler.

Wraps the existing TunisiaDouaneScraper into the NorthAfricaCrawlerBase
(BaseScraper-compatible) interface for integration with the crawl orchestrator.

Sources:
  Primary: douane.finances.tn (tarifweb2025)
  Secondary: customs.gov.tn
Tax structure: DD, TVA (19%), FODEC, TCL, Consumption taxes
Special features: EU Association Agreement (most advanced in region),
                  DCFTA preparation, offshore regime, textile/automotive.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_north_africa_crawler import NorthAfricaCrawlerBase
from config.crawler_configs.tun_config import TUN_CONFIG

logger = logging.getLogger(__name__)


class TUNTariffCrawler(NorthAfricaCrawlerBase):
    """
    Tunisia tariff crawler using douane.finances.tn/tarifweb2025.

    Integrates with TunisiaDouaneScraper to provide:
    - Async crawling with httpx
    - Tax structure: DD, TVA (19%), FODEC (1%), TCL, Consumption taxes
    - EU Association Agreement rates (most advanced in North Africa)
    - DCFTA (Deep and Comprehensive Free Trade Area) preparation rates
    - Offshore enterprise regime benefits
    - Textile and automotive industry-specific arrangements
    """

    _country_code = "TUN"

    def __init__(self, *args, chapters: Optional[List[str]] = None,
                 max_per_chapter: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.chapters = chapters
        self.max_per_chapter = max_per_chapter
        self.config = TUN_CONFIG

    async def scrape(self) -> Dict[str, Any]:
        """
        Run the Tunisia tariff scraper and return structured data.

        Uses TunisiaDouaneScraper for the actual crawling logic.
        Full crawl covers all 96 chapters; use chapters for a sample.
        """
        from crawlers.countries.tunisia_douane_scraper import TunisiaDouaneScraper

        logger.info("TUN: Starting Tunisia tariff crawl via douane.finances.tn")
        scraper = TunisiaDouaneScraper()

        try:
            await scraper._ensure_client()

            if self.chapters is not None or self.max_per_chapter is not None:
                positions = await scraper.scrape_sample(
                    chapters=self.chapters,
                    max_per_chapter=self.max_per_chapter or 3,
                )
            else:
                positions = await scraper.scrape_all(save_progress=True)

            records = []
            for pos in positions:
                import_taxes = {}
                for t in pos.get("taxes_import", []):
                    code = t.get("code", "").strip()
                    rate = t.get("rate_pct")
                    if code and rate is not None:
                        import_taxes[code] = rate

                records.append(
                    self.build_canonical_record(
                        hs_code=pos.get("hs_code", pos.get("code", "")),
                        designation=pos.get("designation", ""),
                        taxes=import_taxes,
                        source=self.config["primary_source"],
                        chapter=pos.get("chapter", ""),
                        taxes_export=[
                            t for t in pos.get("taxes_export", [])
                        ],
                        preferences=pos.get("preferences", []),
                        import_status=pos.get("import_status", ""),
                        export_status=pos.get("export_status", ""),
                    )
                )

            return {
                "country_code": self._country_code,
                "country_name": self.config["country_name"],
                "source": self.config["primary_source"],
                "nomenclature": self.config["nomenclature"],
                "tax_structure": list(self.config["tax_structure"].keys()),
                "preferential_agreements": self.config["preferential_agreements"],
                "special_regimes": self.config["special_regimes"],
                "total_records": len(records),
                "records": records,
            }
        finally:
            await scraper._close_client()

    async def parse_taxes(self, html: str, country_config: Dict) -> List[Dict]:
        """Parse Tunisia-specific tax structure from HTML."""
        import re
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        taxes = {}
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue
            header_text = " ".join(
                c.get_text(strip=True) for c in rows[0].find_all(["td", "th"])
            ).upper()

            if "DROITS" in header_text and "TAXES" in header_text:
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    texts = [c.get_text(strip=True) for c in cells]
                    if len(texts) >= 2:
                        tax_code = re.match(r"^([A-Z/_]+)", texts[0])
                        rate_match = re.search(r"([\d.,]+)\s*%", texts[1])
                        if tax_code and rate_match:
                            taxes[tax_code.group(1).strip()] = self.normalize_rate(
                                rate_match.group(1)
                            )

        return [{"taxes": taxes}]

    async def validate_data(self, tariff_lines: List[Dict]) -> bool:
        """Validate Tunisia tariff data quality."""
        if not tariff_lines:
            logger.error("TUN: No tariff lines to validate")
            return False

        valid_count = sum(
            1 for line in tariff_lines
            if line.get("hs_code") and line.get("designation")
        )
        coverage = valid_count / len(tariff_lines) if tariff_lines else 0
        logger.info(f"TUN: Validation coverage {coverage:.1%} ({valid_count}/{len(tariff_lines)})")
        return coverage >= 0.5
