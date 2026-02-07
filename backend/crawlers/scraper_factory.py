"""
Factory pattern for creating country-specific scrapers.

This module provides a factory for instantiating the appropriate scraper
for each African country. It includes:
- Scraper registry system
- Generic fallback scraper for countries without specific implementations
- Scraper discovery and registration
- Bulk scraper creation utilities

Usage:
    from backend.crawlers import ScraperFactory
    
    # Get scraper for a specific country
    scraper = ScraperFactory.get_scraper("GHA", db_client=mongo_client)
    result = await scraper.run()
    
    # Get all scrapers for high-priority countries
    scrapers = ScraperFactory.get_priority_scrapers(priority="HIGH")
"""

import logging
from typing import Dict, Type, Optional, List, Union, Any
from motor.motor_asyncio import AsyncIOMotorClient

from .base_scraper import BaseScraper, ScraperConfig
from .all_countries_registry import (
    AFRICAN_COUNTRIES_REGISTRY,
    get_country_config,
    get_priority_countries,
    get_countries_by_region,
    get_countries_by_block,
    Priority,
    Region,
    RegionalBlock,
)


logger = logging.getLogger(__name__)


class GenericScraper(BaseScraper):
    """
    Generic scraper for countries without specific implementations.
    
    This scraper provides basic functionality for countries that don't have
    custom scraping logic yet. It can be used as a placeholder or starting point.
    """
    
    async def scrape(self) -> Dict[str, Any]:
        """
        Generic scrape implementation using the tariff data collector.
        
        Consolidates existing ETL data (chapter tariffs, HS6 detailed rates,
        VAT, other taxes) into structured tariff line records.
        """
        logger.info(f"Collecting tariff data for {self.country_name} ({self.country_code})")
        
        try:
            from services.tariff_data_collector import get_collector
            collector = get_collector()
            tariff_data = collector.collect_country_tariffs(self.country_code)
            collector.save_country_tariffs(self.country_code, tariff_data)
            
            return {
                "country_code": self.country_code,
                "country_name": self.country_name,
                "source_url": self.source_url,
                "vat_rate": self.vat_rate,
                "region": self.region,
                "regional_blocks": self.regional_blocks,
                "scrape_type": "tariff_collection",
                "data": {
                    "tariff_lines": len(tariff_data.get("tariff_lines", [])),
                    "lines_with_sub_positions": tariff_data.get("summary", {}).get("lines_with_sub_positions", 0),
                    "summary": tariff_data.get("summary", {}),
                }
            }
        except Exception as e:
            logger.error(f"Tariff collection failed for {self.country_code}: {e}")
            return {
                "country_code": self.country_code,
                "country_name": self.country_name,
                "source_url": self.source_url,
                "vat_rate": self.vat_rate,
                "region": self.region,
                "regional_blocks": self.regional_blocks,
                "scrape_type": "generic_fallback",
                "error": str(e),
                "data": {"tariffs": [], "hs_codes": [], "regulations": []}
            }
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Generic validation implementation.
        
        Performs basic validation checks.
        Override this method for more specific validation.
        """
        if not data:
            logger.error(f"No data to validate for {self.country_code}")
            return False
        
        # Check required fields
        required_fields = ["country_code", "country_name", "source_url"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Verify country code matches
        if data["country_code"] != self.country_code:
            logger.error(
                f"Country code mismatch: expected {self.country_code}, "
                f"got {data['country_code']}"
            )
            return False
        
        logger.info(f"Generic validation passed for {self.country_code}")
        return True
    
    async def save_to_db(self, data: Dict[str, Any]) -> int:
        """
        Generic save implementation.
        
        Saves data to a generic collection.
        Override this method for specific database schemas.
        """
        if not self.database:
            logger.warning("No database client available")
            return 0
        
        try:
            collection = self.database.customs_data_raw
            
            # Add metadata
            doc = {
                **data,
                "scraped_at": data.get("timestamp"),
                "scraper_version": "1.0.0",
                "scraper_type": "generic",
            }
            
            # Upsert by country code
            result = await collection.update_one(
                {"country_code": self.country_code},
                {"$set": doc},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new document for {self.country_code}")
                return 1
            elif result.modified_count > 0:
                logger.info(f"Updated existing document for {self.country_code}")
                return 1
            else:
                logger.info(f"No changes for {self.country_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to save data for {self.country_code}: {e}")
            raise


class ScraperFactory:
    """
    Factory for creating country-specific scrapers.
    
    This class manages the registry of scrapers and provides methods
    for creating scraper instances.
    """
    
    # Registry of country-specific scraper classes
    _registry: Dict[str, Type[BaseScraper]] = {}
    
    # Default scraper for countries without specific implementations
    _default_scraper: Type[BaseScraper] = GenericScraper
    
    @classmethod
    def register(cls, country_code: str, scraper_class: Type[BaseScraper]):
        """
        Register a scraper class for a specific country.
        
        Args:
            country_code: ISO3 country code
            scraper_class: Scraper class (must inherit from BaseScraper)
            
        Raises:
            ValueError: If scraper_class doesn't inherit from BaseScraper
        """
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError(
                f"{scraper_class.__name__} must inherit from BaseScraper"
            )
        
        country_code = country_code.upper()
        if country_code not in AFRICAN_COUNTRIES_REGISTRY:
            logger.warning(
                f"Registering scraper for unknown country code: {country_code}"
            )
        
        cls._registry[country_code] = scraper_class
        logger.info(
            f"Registered {scraper_class.__name__} for {country_code}"
        )
    
    @classmethod
    def unregister(cls, country_code: str):
        """
        Unregister a scraper for a specific country.
        
        Args:
            country_code: ISO3 country code
        """
        country_code = country_code.upper()
        if country_code in cls._registry:
            del cls._registry[country_code]
            logger.info(f"Unregistered scraper for {country_code}")
    
    @classmethod
    def get_scraper(
        cls,
        country_code: str,
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None,
        force_generic: bool = False,
    ) -> BaseScraper:
        """
        Get a scraper instance for a specific country.
        
        Args:
            country_code: ISO3 country code
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional)
            force_generic: Force use of generic scraper even if specific one exists
            
        Returns:
            Scraper instance for the country
            
        Raises:
            ValueError: If country code is invalid
        """
        country_code = country_code.upper()
        
        # Validate country code
        if country_code not in AFRICAN_COUNTRIES_REGISTRY:
            raise ValueError(
                f"Invalid country code: {country_code}. "
                f"Must be one of the 54 African countries."
            )
        
        # Get scraper class
        if force_generic:
            scraper_class = cls._default_scraper
        else:
            scraper_class = cls._registry.get(country_code, cls._default_scraper)
        
        # Create instance
        if scraper_class == cls._default_scraper:
            logger.info(
                f"No specific scraper for {country_code}, using generic scraper"
            )
        
        return scraper_class(
            country_code=country_code,
            db_client=db_client,
            config=config
        )
    
    @classmethod
    def get_multiple_scrapers(
        cls,
        country_codes: List[str],
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None,
    ) -> List[BaseScraper]:
        """
        Get multiple scraper instances.
        
        Args:
            country_codes: List of ISO3 country codes
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional)
            
        Returns:
            List of scraper instances
        """
        scrapers = []
        for code in country_codes:
            try:
                scraper = cls.get_scraper(code, db_client, config)
                scrapers.append(scraper)
            except ValueError as e:
                logger.error(f"Skipping invalid country code {code}: {e}")
        
        return scrapers
    
    @classmethod
    def get_priority_scrapers(
        cls,
        priority: Union[Priority, str],
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None,
    ) -> List[BaseScraper]:
        """
        Get scrapers for all countries with a specific priority level.
        
        Args:
            priority: Priority level (HIGH, MEDIUM, LOW)
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional)
            
        Returns:
            List of scraper instances
        """
        if isinstance(priority, str):
            priority = Priority[priority.upper()]
        
        country_codes = get_priority_countries(priority)
        return cls.get_multiple_scrapers(country_codes, db_client, config)
    
    @classmethod
    def get_region_scrapers(
        cls,
        region: Union[Region, str],
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None,
    ) -> List[BaseScraper]:
        """
        Get scrapers for all countries in a specific region.
        
        Args:
            region: Region (NORTH_AFRICA, WEST_AFRICA, etc.)
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional)
            
        Returns:
            List of scraper instances
        """
        if isinstance(region, str):
            region = Region[region.upper().replace(" ", "_")]
        
        country_codes = get_countries_by_region(region)
        return cls.get_multiple_scrapers(country_codes, db_client, config)
    
    @classmethod
    def get_block_scrapers(
        cls,
        block: Union[RegionalBlock, str],
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None,
    ) -> List[BaseScraper]:
        """
        Get scrapers for all countries in a regional economic block.
        
        Args:
            block: Regional block (ECOWAS, CEMAC, EAC, SACU, etc.)
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional)
            
        Returns:
            List of scraper instances
        """
        if isinstance(block, str):
            block = RegionalBlock[block.upper()]
        
        country_codes = get_countries_by_block(block)
        return cls.get_multiple_scrapers(country_codes, db_client, config)
    
    @classmethod
    def get_all_scrapers(
        cls,
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None,
    ) -> List[BaseScraper]:
        """
        Get scrapers for all 54 African countries.
        
        Args:
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional)
            
        Returns:
            List of all scraper instances
        """
        country_codes = list(AFRICAN_COUNTRIES_REGISTRY.keys())
        return cls.get_multiple_scrapers(country_codes, db_client, config)
    
    @classmethod
    def list_registered_scrapers(cls) -> Dict[str, str]:
        """
        List all registered country-specific scrapers.
        
        Returns:
            Dict mapping country codes to scraper class names
        """
        return {
            code: scraper_class.__name__
            for code, scraper_class in cls._registry.items()
        }
    
    @classmethod
    def get_registry_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about the scraper registry.
        
        Returns:
            Dict with registry statistics
        """
        total_countries = len(AFRICAN_COUNTRIES_REGISTRY)
        registered = len(cls._registry)
        using_generic = total_countries - registered
        
        return {
            "total_countries": total_countries,
            "specific_scrapers": registered,
            "using_generic": using_generic,
            "coverage_percentage": (registered / total_countries * 100) if total_countries > 0 else 0,
            "registered_countries": list(cls._registry.keys()),
        }


# Auto-discover and register scrapers from countries/ directory
def _auto_register_scrapers():
    """
    Automatically discover and register country-specific scrapers.
    
    This function imports scraper modules from the countries/ subdirectory
    and registers any scrapers that have been defined.
    """
    import importlib
    import pkgutil
    from pathlib import Path
    
    # Get the countries directory
    countries_dir = Path(__file__).parent / "countries"
    if not countries_dir.exists():
        logger.info("No countries/ directory found, skipping auto-registration")
        return
    
    # Import all modules in countries/
    try:
        import backend.crawlers.countries as countries_package
        
        for importer, modname, ispkg in pkgutil.iter_modules(
            countries_package.__path__,
            prefix="backend.crawlers.countries."
        ):
            try:
                module = importlib.import_module(modname)
                
                # Look for scraper classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a scraper class (not BaseScraper itself)
                    if (
                        isinstance(attr, type) and
                        issubclass(attr, BaseScraper) and
                        attr not in (BaseScraper, GenericScraper) and
                        hasattr(attr, '_country_code')
                    ):
                        # Register the scraper
                        country_code = attr._country_code
                        ScraperFactory.register(country_code, attr)
                        
            except Exception as e:
                logger.warning(f"Failed to import {modname}: {e}")
                
    except ImportError:
        logger.info("Countries package not found, skipping auto-registration")


# Run auto-registration on import
_auto_register_scrapers()

# Log registry stats
_stats = ScraperFactory.get_registry_stats()
logger.info(
    f"Scraper registry initialized: {_stats['specific_scrapers']}/{_stats['total_countries']} "
    f"countries have specific scrapers ({_stats['coverage_percentage']:.1f}% coverage)"
)
