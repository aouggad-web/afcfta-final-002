"""
Example: Ghana-specific customs scraper

This file demonstrates how to create a country-specific scraper by
inheriting from BaseScraper and implementing the required methods.

To register this scraper:
1. Ensure the file is in backend/crawlers/countries/
2. Add _country_code class attribute
3. The scraper will be auto-registered by the factory

Usage:
    from backend.crawlers import ScraperFactory
    
    scraper = ScraperFactory.get_scraper("GHA")
    result = await scraper.run()
"""

from typing import Dict, Any
import logging
from datetime import datetime

from ..base_scraper import BaseScraper


logger = logging.getLogger(__name__)


class GhanaScraper(BaseScraper):
    """
    Ghana-specific customs data scraper.
    
    Data sources:
    - Ghana Revenue Authority (GRA): https://www.gra.gov.gh
    - Ghana Customs Division
    - Import Duty Calculator
    - Tariff schedules
    """
    
    # This attribute tells the factory which country this scraper is for
    _country_code = "GHA"
    
    async def scrape(self) -> Dict[str, Any]:
        """
        Scrape customs data for Ghana.
        
        This implementation shows how to:
        1. Fetch multiple data sources
        2. Parse HTML/JSON responses
        3. Combine data from different endpoints
        """
        logger.info(f"Starting Ghana customs data scrape from {self.source_url}")
        
        data = {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "scraped_at": datetime.utcnow().isoformat(),
            "source_url": self.source_url,
            "scraper_version": "1.0.0",
        }
        
        try:
            # Example: Fetch tariff data
            # In a real implementation, you would:
            # 1. Navigate to the tariff page
            # 2. Parse the HTML/JSON
            # 3. Extract tariff rates
            
            # For now, placeholder data structure
            data["tariffs"] = {
                "base_url": self.source_url,
                "vat_rate": self.vat_rate,
                "import_duty_calculator": f"{self.source_url}/import-duty-calculator",
                "tariff_schedule": [],
                "special_rates": {},
            }
            
            # Example: Fetch HS code mappings
            data["hs_codes"] = {
                "source": "GRA Customs Division",
                "mappings": [],
                "last_updated": None,
            }
            
            # Example: Fetch regulations
            data["regulations"] = {
                "import_restrictions": [],
                "prohibited_goods": [],
                "required_permits": [],
            }
            
            logger.info(f"Successfully scraped Ghana customs data")
            
        except Exception as e:
            logger.error(f"Error scraping Ghana data: {e}")
            raise
        
        return data
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped Ghana customs data.
        
        Checks:
        1. Required fields present
        2. Data types correct
        3. VAT rate matches expected value
        4. Data structures are valid
        """
        if not data:
            logger.error("No data to validate")
            return False
        
        # Check required top-level fields
        required_fields = [
            "country_code", "country_name", "scraped_at",
            "tariffs", "hs_codes", "regulations"
        ]
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate country code
        if data["country_code"] != "GHA":
            logger.error(f"Invalid country code: {data['country_code']}")
            return False
        
        # Validate VAT rate
        if "tariffs" in data and "vat_rate" in data["tariffs"]:
            expected_vat = 15.0
            actual_vat = data["tariffs"]["vat_rate"]
            if abs(actual_vat - expected_vat) > 0.01:
                logger.warning(
                    f"VAT rate mismatch: expected {expected_vat}%, got {actual_vat}%"
                )
        
        # Validate data structures
        if not isinstance(data["tariffs"], dict):
            logger.error("Tariffs must be a dictionary")
            return False
        
        if not isinstance(data["hs_codes"], dict):
            logger.error("HS codes must be a dictionary")
            return False
        
        logger.info("Ghana data validation passed")
        return True
    
    async def save_to_db(self, data: Dict[str, Any]) -> int:
        """
        Save validated Ghana customs data to MongoDB.
        
        Collections used:
        - customs_ghana_raw: Raw scraped data
        - customs_ghana_tariffs: Processed tariff data
        - customs_ghana_hs_codes: HS code mappings
        """
        if not self.database:
            logger.warning("No database client available")
            return 0
        
        try:
            records_saved = 0
            
            # Save raw data
            raw_collection = self.database.customs_ghana_raw
            raw_doc = {
                **data,
                "saved_at": datetime.utcnow(),
            }
            
            result = await raw_collection.update_one(
                {"country_code": "GHA"},
                {"$set": raw_doc},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                records_saved += 1
                logger.info("Saved raw Ghana data")
            
            # Save tariff data if available
            if "tariffs" in data and data["tariffs"].get("tariff_schedule"):
                tariff_collection = self.database.customs_ghana_tariffs
                
                for tariff in data["tariffs"]["tariff_schedule"]:
                    tariff_doc = {
                        **tariff,
                        "country_code": "GHA",
                        "updated_at": datetime.utcnow(),
                    }
                    
                    result = await tariff_collection.update_one(
                        {
                            "country_code": "GHA",
                            "hs_code": tariff.get("hs_code")
                        },
                        {"$set": tariff_doc},
                        upsert=True
                    )
                    
                    if result.upserted_id or result.modified_count > 0:
                        records_saved += 1
                
                logger.info(f"Saved {len(data['tariffs']['tariff_schedule'])} tariff records")
            
            # Save HS code mappings if available
            if "hs_codes" in data and data["hs_codes"].get("mappings"):
                hs_collection = self.database.customs_ghana_hs_codes
                
                for mapping in data["hs_codes"]["mappings"]:
                    hs_doc = {
                        **mapping,
                        "country_code": "GHA",
                        "updated_at": datetime.utcnow(),
                    }
                    
                    result = await hs_collection.update_one(
                        {
                            "country_code": "GHA",
                            "hs_code": mapping.get("hs_code")
                        },
                        {"$set": hs_doc},
                        upsert=True
                    )
                    
                    if result.upserted_id or result.modified_count > 0:
                        records_saved += 1
                
                logger.info(f"Saved {len(data['hs_codes']['mappings'])} HS code mappings")
            
            logger.info(f"Total records saved for Ghana: {records_saved}")
            return records_saved
            
        except Exception as e:
            logger.error(f"Failed to save Ghana data: {e}")
            raise


# Note: This scraper will be auto-registered by the factory when the module is imported
# because it has the _country_code attribute and inherits from BaseScraper
