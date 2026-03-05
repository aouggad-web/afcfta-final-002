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
