"""
Crawler Configuration System
Centralized configuration for DZA tariff crawler and related services.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


@dataclass
class CrawlerConfig:
    """Configuration for the DZA async tariff crawler."""

    # Concurrency settings
    max_workers: int = 10
    semaphore_limit: int = 10

    # Rate limiting
    rate_limit_delay: float = 0.2  # seconds between requests

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 2.0

    # Timeout
    request_timeout: float = 30.0

    # Page limits (None = no limit)
    max_pages: Optional[int] = None

    # Target site
    base_url: str = "https://www.douane.gov.dz"

    # Data directories
    raw_dir: Path = DATA_DIR / "raw" / "DZA"
    parsed_dir: Path = DATA_DIR / "parsed" / "DZA"
    published_dir: Path = DATA_DIR / "published" / "DZA"

    # HTTP headers
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __post_init__(self):
        # Ensure directories exist
        for d in (self.raw_dir, self.parsed_dir, self.published_dir):
            d.mkdir(parents=True, exist_ok=True)


@dataclass
class DataRetentionConfig:
    """Data retention policies."""

    # Maximum age of cached data before refresh is triggered (hours)
    max_data_age_hours: int = 24

    # Maximum number of raw HTML files to keep per session
    max_raw_files: int = 10_000

    # Whether to keep old parsed files when refreshing
    keep_old_parsed: bool = True


@dataclass
class QualityConfig:
    """Quality thresholds for data validation."""

    # Minimum confidence score to accept a tariff line
    min_confidence_score: float = 0.5

    # Minimum fraction of tariff lines that must have VAT to accept a dataset
    min_vat_coverage: float = 0.5

    # Minimum fraction of tariff lines that must have national HS10 codes
    min_hs10_coverage: float = 0.3

    # Whether to reject entire dataset on critical errors
    strict_mode: bool = False


@dataclass
class IntegrationConfig:
    """Integration priority settings for the enhanced calculator."""

    # Data source priority order (highest priority first)
    source_priority: list = field(
        default_factory=lambda: ["dza_authentic", "crawled", "tariff_service", "etl_fallback"]
    )

    # Confidence scores per data source
    confidence_scores: dict = field(
        default_factory=lambda: {
            "dza_authentic": 0.98,
            "crawled": 0.85,
            "tariff_service": 0.75,
            "etl_fallback": 0.60,
        }
    )


# ---------------------------------------------------------------------------
# Module-level singletons (override via environment variables if needed)
# ---------------------------------------------------------------------------

def get_crawler_config() -> CrawlerConfig:
    """Return a CrawlerConfig populated from environment variables."""
    return CrawlerConfig(
        max_workers=int(os.environ.get("DZA_CRAWLER_MAX_WORKERS", 10)),
        semaphore_limit=int(os.environ.get("DZA_CRAWLER_SEMAPHORE", 10)),
        rate_limit_delay=float(os.environ.get("DZA_CRAWLER_RATE_LIMIT", 0.2)),
        max_retries=int(os.environ.get("DZA_CRAWLER_MAX_RETRIES", 3)),
        retry_delay=float(os.environ.get("DZA_CRAWLER_RETRY_DELAY", 2.0)),
        request_timeout=float(os.environ.get("DZA_CRAWLER_TIMEOUT", 30.0)),
        max_pages=(
            int(os.environ["DZA_CRAWLER_MAX_PAGES"])
            if os.environ.get("DZA_CRAWLER_MAX_PAGES")
            else None
        ),
        base_url=os.environ.get("DZA_CUSTOMS_URL", "https://www.douane.gov.dz"),
    )


def get_quality_config() -> QualityConfig:
    return QualityConfig(
        min_confidence_score=float(os.environ.get("DZA_QUALITY_MIN_CONFIDENCE", 0.5)),
        min_vat_coverage=float(os.environ.get("DZA_QUALITY_MIN_VAT", 0.5)),
        min_hs10_coverage=float(os.environ.get("DZA_QUALITY_MIN_HS10", 0.3)),
        strict_mode=os.environ.get("DZA_QUALITY_STRICT", "false").lower() == "true",
    )


def get_integration_config() -> IntegrationConfig:
    return IntegrationConfig()
