"""
Morocco (MAR) Tariff Crawler.

Wraps the existing MoroccoDouaneScraper into the NorthAfricaCrawlerBase
(BaseScraper-compatible) interface for integration with the crawl orchestrator.

Sources:
  Primary: douane.gov.ma (ADIL portal)
  Secondary: portail.adii.gov.ma
Tax structure: DD, TVA (20%), PI, TIC, TPCE
Special features: EU/EFTA/Agadir/Turkey preferential rates,
                  agricultural seasonal variations, industrial zones.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_north_africa_crawler import NorthAfricaCrawlerBase
from config.crawler_configs.mar_config import MAR_CONFIG

logger = logging.getLogger(__name__)


class MARTariffCrawler(NorthAfricaCrawlerBase):
    """
    Morocco tariff crawler using douane.gov.ma/ADIL portal.

    Integrates with MoroccoDouaneScraper to provide:
    - Async crawling with httpx for 10x-20x performance improvement
    - Tax structure: DD, TVA (20%), PI (Parafiscal Import), TIC, TPCE
    - Preferential rates: EU Association, Agadir, EFTA, Turkey
    - Seasonal agricultural rate handling
    - Industrial zone (Tanger-Med, Casablanca Finance City) rates
    """

    _country_code = "MAR"

    def __init__(self, *args, chapters: Optional[List[str]] = None,
                 max_per_chapter: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.chapters = chapters
        self.max_per_chapter = max_per_chapter
        self.config = MAR_CONFIG

    async def scrape(self) -> Dict[str, Any]:
        """
        Run the Morocco tariff scraper and return structured data.

        Uses MoroccoDouaneScraper for the actual crawling logic.
        Full crawl covers all 96 chapters; use chapters parameter for a sample.
        """
        from crawlers.countries.morocco_douane_scraper import MoroccoDouaneScraper

        logger.info("MAR: Starting Morocco tariff crawl via douane.gov.ma/ADIL")
        scraper = MoroccoDouaneScraper()

        try:
            if self.chapters is not None or self.max_per_chapter is not None:
                # Sample crawl
                positions = await scraper.scrape_sample(
                    chapters=self.chapters,
                    max_per_chapter=self.max_per_chapter or 5,
                )
            else:
                # Full crawl
                positions = await scraper.scrape_all_positions(save_progress=True)

            records = [
                self.build_canonical_record(
                    hs_code=pos.get("code", ""),
                    designation=pos.get("designation", ""),
                    taxes=pos.get("taxes", {}),
                    source=self.config["primary_source"],
                    chapter=pos.get("chapter", pos.get("code", "")[:2] if pos.get("code") else ""),
                    formalities=pos.get("formalities", []),
                    preferences=pos.get("preferences", []),
                )
                for pos in positions
            ]

            return {
                "country_code": self._country_code,
                "country_name": self.config["country_name"],
                "source": self.config["primary_source"],
                "nomenclature": self.config["nomenclature"],
                "tax_structure": list(self.config["tax_structure"].keys()),
                "preferential_agreements": self.config["preferential_agreements"],
                "total_records": len(records),
                "records": records,
            }
        finally:
            pass  # MoroccoDouaneScraper manages its own clients per operation

    async def parse_taxes(self, html: str, country_config: Dict) -> List[Dict]:
        """Parse Morocco-specific tax structure from HTML."""
        import re
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        taxes = {}

        for td in soup.find_all("td"):
            text = td.get_text(strip=True)

            di_match = re.search(
                r"Droit\s+d['\u2019]Importation.*?\(\s*DI\s*\)\s*:\s*([\d,\.]+)\s*%", text
            )
            if di_match:
                taxes["DD"] = self.normalize_rate(di_match.group(1))

            tva_match = re.search(
                r"Taxe\s+sur\s+la\s+Valeur\s+Ajout.*?\(\s*TVA\s*\)\s*:\s*([\d,\.]+)\s*%", text
            )
            if tva_match:
                taxes["TVA"] = self.normalize_rate(tva_match.group(1))

            tpi_match = re.search(
                r"Taxe\s+Parafiscale.*?\(\s*TPI\s*\)\s*:\s*([\d,\.]+)\s*%", text
            )
            if tpi_match:
                taxes["PI"] = self.normalize_rate(tpi_match.group(1))

            tic_match = re.search(
                r"Taxe\s+Int.*?rieure.*?Consommation.*?\(\s*TIC\s*\)\s*:\s*([\d,\.]+)", text
            )
            if tic_match:
                taxes["TIC"] = self.normalize_rate(tic_match.group(1))

        return [{"taxes": taxes}]

    async def validate_data(self, tariff_lines: List[Dict]) -> bool:
        """Validate Morocco tariff data quality."""
        if not tariff_lines:
            logger.error("MAR: No tariff lines to validate")
            return False

        valid_count = sum(
            1 for line in tariff_lines
            if line.get("hs_code") and line.get("designation")
        )
        coverage = valid_count / len(tariff_lines) if tariff_lines else 0
        logger.info(f"MAR: Validation coverage {coverage:.1%} ({valid_count}/{len(tariff_lines)})")
        return coverage >= 0.5
