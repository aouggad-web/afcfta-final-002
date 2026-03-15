"""
Egypt (EGY) Tariff Crawler.

Wraps the existing EgyptTariffsScraper into the NorthAfricaCrawlerBase
(BaseScraper-compatible) interface for integration with the crawl orchestrator.

Sources:
  Primary: egyptariffs.com (based on Egyptian Customs Authority data)
  Official: customs.gov.eg
Tax structure: CD, VAT (14%), SD, DT, ST
Special features: QIZ rates, Investment law incentives, COMESA, Suez Canal zone.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from .base_north_africa_crawler import NorthAfricaCrawlerBase
from config.crawler_configs.egy_config import EGY_CONFIG

logger = logging.getLogger(__name__)


class EGYTariffCrawler(NorthAfricaCrawlerBase):
    """
    Egypt tariff crawler using egyptariffs.com as the data source.

    Integrates with EgyptTariffsScraper to provide:
    - Sync crawling (converted to async via run_in_executor)
    - ~8,816 HS10 positions from Egyptian Customs Authority data
    - Tax structure: CD (Customs Duty), VAT (14%), SD, DT, ST
    - Special rates: QIZ (US market access), Investment law 72/2017,
                     COMESA preferential rates, Suez Canal Economic Zone
    """

    _country_code = "EGY"

    def __init__(self, *args, max_positions: Optional[int] = None,
                 delay: float = 1.5, resume: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_positions = max_positions
        self.delay = delay
        self.resume = resume
        self.config = EGY_CONFIG

    async def scrape(self) -> Dict[str, Any]:
        """
        Run the Egypt tariff scraper and return structured data.

        EgyptTariffsScraper is sync-based; runs in executor to avoid blocking.
        """
        from crawlers.countries.egypt_tariffs_scraper import EgyptTariffsScraper

        logger.info("EGY: Starting Egypt tariff crawl via egyptariffs.com")
        scraper = EgyptTariffsScraper()

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: scraper.scrape(
                max_positions=self.max_positions,
                delay=self.delay,
                resume=self.resume,
            ),
        )

        positions = scraper.positions

        records = []
        for pos in positions:
            raw_taxes = {}
            for td in pos.get("taxes_detail", []):
                raw_taxes[td.get("tax_code", "?")] = td.get("rate")

            if not raw_taxes:
                raw_taxes = {k: v for k, v in pos.get("taxes", {}).items()}

            records.append(
                self.build_canonical_record(
                    hs_code=pos.get("code_clean", pos.get("code", "")),
                    designation=pos.get("designation", ""),
                    taxes=raw_taxes,
                    source=self.config["primary_source"],
                    designation_en=pos.get("designation_en", ""),
                    administrative_formalities=pos.get("administrative_formalities", []),
                )
            )

        return {
            "country_code": self._country_code,
            "country_name": self.config["country_name"],
            "source": self.config["primary_source"],
            "official_source": self.config["official_source"],
            "nomenclature": self.config["nomenclature"],
            "legal_reference": self.config["legal_reference"],
            "tax_structure": list(self.config["tax_structure"].keys()),
            "preferential_agreements": self.config["preferential_agreements"],
            "special_zones": self.config["special_zones"],
            "total_records": len(records),
            "records": records,
            "stats": result.get("stats", {}),
        }

    async def parse_taxes(self, html: str, country_config: Dict) -> List[Dict]:
        """Parse Egypt-specific tax structure from HTML using JSON-LD."""
        import re
        import json as json_mod

        taxes = {}
        json_blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )

        for jb in json_blocks:
            try:
                d = json_mod.loads(jb)
                if d.get("@type") == "Product":
                    for prop in d.get("additionalProperty", []):
                        name = prop.get("name", "")
                        value = prop.get("value", "")
                        unit = prop.get("unitText", "")
                        if name == "Import Duty Rate" and unit == "PERCENT":
                            taxes["CD"] = self.normalize_rate(value)
                        elif name == "VAT Rate" and unit == "PERCENT":
                            taxes["VAT"] = self.normalize_rate(value)
                    break
            except Exception:
                continue

        return [{"taxes": taxes}]

    async def validate_data(self, tariff_lines: List[Dict]) -> bool:
        """Validate Egypt tariff data quality."""
        if not tariff_lines:
            logger.error("EGY: No tariff lines to validate")
            return False

        valid_count = sum(
            1 for line in tariff_lines
            if line.get("hs_code") and line.get("designation")
        )
        coverage = valid_count / len(tariff_lines) if tariff_lines else 0
        logger.info(f"EGY: Validation coverage {coverage:.1%} ({valid_count}/{len(tariff_lines)})")
        return coverage >= 0.5
