"""
African Customs Data Crawlers

This module provides a comprehensive infrastructure for scraping customs data
from 54 African countries. It includes base classes, factory patterns, and
country-specific configurations.

Main Components:
- BaseScraper: Abstract base class for all scrapers
- ScraperFactory: Factory for creating country-specific scrapers
- AllCountriesRegistry: Configuration for all 54 African countries

Usage:
    from backend.crawlers import ScraperFactory

    scraper = ScraperFactory.get_scraper("GHA")
    data = await scraper.scrape()
"""

from .all_countries_registry import (
    AFRICAN_COUNTRIES_REGISTRY,
    REGIONAL_BLOCKS,
    Priority,
    Region,
    RegionalBlock,
    get_countries_by_block,
    get_countries_by_region,
    get_country_config,
    get_priority_countries,
    validate_registry,
)

__all__ = [
    "AFRICAN_COUNTRIES_REGISTRY",
    "REGIONAL_BLOCKS",
    "Region",
    "RegionalBlock",
    "Priority",
    "get_country_config",
    "get_countries_by_region",
    "get_countries_by_block",
    "get_priority_countries",
    "validate_registry",
]

# BaseScraper/ScraperFactory dépendent de `motor` (MongoDB) — présent dans le
# backend complet, mais ABSENT de l'environnement crawl minimal des runners
# GitHub (requirements-crawl.txt). Import tolérant : le moteur Scrapling
# (crawlers.scrapling_engine) et le scraper conformepro (httpx+bs4) n'en ont
# pas besoin ; le backend complet garde le comportement historique.
try:  # pragma: no cover - dépend de l'environnement d'exécution
    from .base_scraper import BaseScraper, ScraperConfig, ScraperResult
    from .scraper_factory import GenericScraper, ScraperFactory

    __all__ += [
        "BaseScraper",
        "ScraperConfig",
        "ScraperResult",
        "ScraperFactory",
        "GenericScraper",
    ]
except ImportError:  # environnement crawl minimal (sans motor/pydantic)
    BaseScraper = ScraperConfig = ScraperResult = None  # type: ignore
    GenericScraper = ScraperFactory = None  # type: ignore

__version__ = "1.0.0"
