"""
Base North Africa Crawler Framework.

Provides a common abstract base class for all North African country crawlers,
extending the existing BaseScraper with regional-specific utilities.

Supports async operations for 10x-20x performance improvement.
"""

import asyncio
import json
import logging
import os
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from crawlers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

DATA_BASE_DIR = Path(__file__).parent.parent.parent / "data"


class NorthAfricaCrawlerBase(BaseScraper):
    """
    Abstract base class for North African country tariff crawlers.

    Extends BaseScraper with:
    - Country-specific configuration loading
    - Structured data export (JSON/CSV)
    - Progress tracking and resumable crawls
    - Canonical data normalization
    - Cross-country validation hooks
    """

    # Subclasses must set this to the ISO3 country code
    _country_code: str = ""

    # ==================== Abstract North Africa Methods ====================

    @abstractmethod
    async def parse_taxes(self, html: str, country_config: Dict) -> List[Dict]:
        """
        Parse tax information from HTML content.

        Args:
            html: Raw HTML content from customs website
            country_config: Country-specific configuration dict

        Returns:
            List of parsed tariff line dictionaries
        """

    @abstractmethod
    async def validate_data(self, tariff_lines: List[Dict]) -> bool:
        """
        Validate parsed tariff lines for data quality.

        Args:
            tariff_lines: List of tariff line dictionaries

        Returns:
            True if data passes validation, False otherwise
        """

    # ==================== Shared Utility Methods ====================

    def get_country_data_dir(self, subdir: str = "raw") -> Path:
        """Get the data directory for this country."""
        path = DATA_BASE_DIR / subdir / self._country_code
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_published_dir(self) -> Path:
        """Get the published data directory for this country."""
        return self.get_country_data_dir("published")

    def get_parsed_dir(self) -> Path:
        """Get the parsed data directory for this country."""
        return self.get_country_data_dir("parsed")

    async def export_canonical(
        self,
        data: List[Dict],
        format: str = "json",
        filename: Optional[str] = None,
    ) -> str:
        """
        Export tariff data in canonical format.

        Args:
            data: List of tariff line dicts
            format: Output format - 'json' or 'csv'
            filename: Optional output filename

        Returns:
            Path to the exported file
        """
        if not filename:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self._country_code}_tariffs_{ts}.{format}"

        out_dir = self.get_published_dir()
        out_path = out_dir / filename

        if format == "json":
            payload = {
                "country_code": self._country_code,
                "exported_at": datetime.utcnow().isoformat(),
                "total_records": len(data),
                "records": data,
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv

            if not data:
                return str(out_path)
            fieldnames = list(data[0].keys())
            with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                writer.writerows(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported {len(data)} records to {out_path}")
        return str(out_path)

    def normalize_hs_code(self, raw_code: str, target_digits: int = 10) -> str:
        """
        Normalize an HS code to the target number of digits.

        Args:
            raw_code: Raw HS code string (may include dots, spaces)
            target_digits: Target number of digits (default 10)

        Returns:
            Normalized HS code string
        """
        clean = "".join(c for c in raw_code if c.isdigit())
        if len(clean) < target_digits:
            clean = clean.ljust(target_digits, "0")
        return clean[:target_digits]

    def normalize_rate(self, raw_value: Any) -> Optional[float]:
        """
        Normalize a tax rate value to a float percentage.

        Args:
            raw_value: Raw rate value (string, int, float, or None)

        Returns:
            Float percentage or None if not parseable
        """
        if raw_value is None:
            return None
        if isinstance(raw_value, (int, float)):
            return float(raw_value)
        if isinstance(raw_value, str):
            import re

            m = re.search(r"([\d]+(?:[.,]\d+)?)", raw_value)
            if m:
                return float(m.group(1).replace(",", "."))
        return None

    def build_canonical_record(
        self,
        hs_code: str,
        designation: str,
        taxes: Dict[str, Any],
        source: str,
        **extra,
    ) -> Dict:
        """
        Build a canonical tariff record in the standard format.

        Args:
            hs_code: HS code (string of digits)
            designation: Product designation / description
            taxes: Dict of {tax_code: rate_value}
            source: Data source identifier
            **extra: Additional fields

        Returns:
            Canonical tariff record dict
        """
        normalized_taxes = {
            k: self.normalize_rate(v) for k, v in taxes.items()
        }
        total = sum(v for v in normalized_taxes.values() if v is not None)

        record = {
            "country_code": self._country_code,
            "hs_code": hs_code,
            "designation": designation,
            "taxes": normalized_taxes,
            "total_taxes_pct": round(total, 4),
            "source": source,
            "scraped_at": datetime.utcnow().isoformat(),
        }
        record.update(extra)
        return record

    # ==================== BaseScraper Required Implementations ====================

    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate scraped data dictionary."""
        if not data:
            return False
        records = data.get("records", data.get("positions", data.get("data", [])))
        if not isinstance(records, list):
            return False
        return await self.validate_data(records)

    async def save_to_db(self, data: Dict[str, Any]) -> int:
        """Save data to MongoDB if available."""
        if not self.database:
            logger.warning(f"No database client for {self._country_code}, skipping DB save")
            return 0

        records = data.get("records", data.get("positions", data.get("data", [])))
        if not records:
            return 0

        try:
            collection = self.database[f"tariffs_{self._country_code.lower()}"]
            doc = {
                "country_code": self._country_code,
                "scraped_at": datetime.utcnow(),
                "total_records": len(records),
                "records": records,
            }
            result = await collection.replace_one(
                {"country_code": self._country_code},
                doc,
                upsert=True,
            )
            saved = result.upserted_id is not None or result.modified_count > 0
            return len(records) if saved else 0
        except Exception as e:
            logger.error(f"DB save failed for {self._country_code}: {e}")
            raise
