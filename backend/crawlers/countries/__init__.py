"""
Country-specific scrapers

This module contains country-specific scraper implementations.
Each scraper inherits from BaseScraper and implements custom logic
for its country's customs data sources.

Example:
    from backend.crawlers.countries.ghana import GhanaScraper
    
    scraper = GhanaScraper(country_code="GHA", db_client=client)
    result = await scraper.run()
"""

__all__ = []
