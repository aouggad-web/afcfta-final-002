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

from .base_scraper import BaseScraper, ScraperConfig, ScraperResult
from .scraper_factory import ScraperFactory, GenericScraper
from .all_countries_registry import (
    AFRICAN_COUNTRIES_REGISTRY,
    REGIONAL_BLOCKS,
    Region,
    RegionalBlock,
    Priority,
    get_country_config,
    get_countries_by_region,
    get_countries_by_block,
    get_priority_countries,
    validate_registry,
)

__all__ = [
    "BaseScraper",
    "ScraperConfig",
    "ScraperResult",
    "ScraperFactory",
    "GenericScraper",
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

__version__ = "1.0.0"
