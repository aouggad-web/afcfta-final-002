"""
Scraper générique pour pays avec données limitées
"""
from typing import Dict, Any, List
import logging

from backend.crawlers.base_scraper import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)


class GenericScraper(BaseScraper):
    """
    Scraper pour pays utilisant tarifs régionaux
    (TEC CEDEAO, CET EAC, TDC CEMAC, SACU)
    """

    def __init__(self, country_code: str, config: Dict[str, Any] = None):
        """
        Initialize generic scraper.

        Args:
            country_code: ISO3 country code
            config: Optional configuration dictionary
        """
        super().__init__(country_code, config)
        self.regional_tariff = self.country_config.get("regional_tariff")
        self.vat_rate = self.country_config.get("vat_rate", 18.0) / 100

        logger.info(
            f"Initialized GenericScraper for {country_code} "
            f"(regional tariff: {self.regional_tariff}, VAT: {self.vat_rate * 100}%)"
        )

    async def scrape(self) -> ScraperResult:
        """
        Scrape customs data using regional tariff structure.

        Returns:
            ScraperResult with success status and data
        """
        start_time = self._get_current_time()

        try:
            logger.info(f"Starting scrape for {self.country_code} using generic scraper")

            # Get tariff data based on regional tariff
            tariffs = await self.scrape_tariffs()
            regulations = await self.scrape_regulations()

            data = {
                "country_code": self.country_code,
                "tariffs": tariffs,
                "regulations": regulations,
                "data_source": "generic_regional_tariff",
                "regional_tariff": self.regional_tariff,
                "scraped_at": start_time.isoformat(),
            }

            # Validate data
            is_valid, validation_errors = await self.validate(data)

            if not is_valid:
                logger.warning(f"Validation failed for {self.country_code}: {validation_errors}")

            # Save to database
            saved = await self.save_to_db(data)

            duration = (self._get_current_time() - start_time).total_seconds()

            return ScraperResult(
                country_code=self.country_code,
                success=True,
                data=data,
                duration_seconds=duration,
                records_scraped=len(tariffs.get("tariff_lines", [])),
                records_validated=len(tariffs.get("tariff_lines", [])) if is_valid else 0,
                records_saved=1 if saved else 0,
            )

        except Exception as e:
            error_msg = f"Error scraping {self.country_code}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            duration = (self._get_current_time() - start_time).total_seconds()

            return ScraperResult(
                country_code=self.country_code,
                success=False,
                error=error_msg,
                duration_seconds=duration,
            )

    async def scrape_tariffs(self) -> Dict[str, Any]:
        """Utilise les tarifs régionaux"""
        if self.regional_tariff == "TEC CEDEAO":
            return self._get_cedeao_tariff()
        elif self.regional_tariff == "CET EAC":
            return self._get_eac_tariff()
        elif self.regional_tariff == "TDC CEMAC":
            return self._get_cemac_tariff()
        elif self.regional_tariff == "SACU Common Tariff":
            return self._get_sacu_tariff()
        else:
            return self._get_generic_tariff()

    def _get_cedeao_tariff(self) -> Dict[str, Any]:
        """TEC CEDEAO (5 catégories: 0%, 5%, 10%, 20%, 35%)"""
        tariff_lines = []

        # Generate representative tariff lines for major chapters
        for chapter in range(1, 98):
            hs_code = f"{chapter:02d}0000"
            rate = self._get_tec_rate(chapter)

            tariff_lines.append({
                "hs_code": hs_code,
                "description": f"Chapter {chapter:02d} products",
                "customs_duty": f"{rate * 100:.1f}%",
                "vat": f"{self.vat_rate * 100:.1f}%",
                "unit": "KG",
                "source": "TEC CEDEAO"
            })

        return {
            "tariff_lines": tariff_lines,
            "note": "Using ECOWAS CET (Common External Tariff)",
            "tariff_structure": "TEC CEDEAO - 5 categories (0%, 5%, 10%, 20%, 35%)"
        }

    def _get_tec_rate(self, chapter: int) -> float:
        """Taux TEC par chapitre (simplified)"""
        # Basic necessities (food, raw materials)
        if chapter <= 24:
            return 0.05  # 5%
        # Semi-finished goods
        elif chapter <= 40:
            return 0.10  # 10%
        # Manufactured goods
        elif chapter <= 84:
            return 0.20  # 20%
        # Capital goods
        else:
            return 0.10  # 10%

    def _get_eac_tariff(self) -> Dict[str, Any]:
        """East African Community Common External Tariff"""
        tariff_lines = []

        for chapter in range(1, 98):
            hs_code = f"{chapter:02d}0000"

            # EAC has 3 tariff bands: 0%, 10%, 25%
            if chapter <= 15:
                rate = 0.0  # Raw materials
            elif chapter <= 84:
                rate = 0.10  # Intermediate goods
            else:
                rate = 0.25  # Final goods

            tariff_lines.append({
                "hs_code": hs_code,
                "description": f"Chapter {chapter:02d} products",
                "customs_duty": f"{rate * 100:.1f}%",
                "vat": f"{self.vat_rate * 100:.1f}%",
                "unit": "KG",
                "source": "EAC CET"
            })

        return {
            "tariff_lines": tariff_lines,
            "note": "Using EAC Common External Tariff",
            "tariff_structure": "EAC CET - 3 bands (0%, 10%, 25%)"
        }

    def _get_cemac_tariff(self) -> Dict[str, Any]:
        """CEMAC Common External Tariff"""
        tariff_lines = []

        for chapter in range(1, 98):
            hs_code = f"{chapter:02d}0000"

            # CEMAC has 4 tariff categories: 5%, 10%, 20%, 30%
            if chapter <= 24:
                rate = 0.05
            elif chapter <= 64:
                rate = 0.10
            elif chapter <= 84:
                rate = 0.20
            else:
                rate = 0.30

            tariff_lines.append({
                "hs_code": hs_code,
                "description": f"Chapter {chapter:02d} products",
                "customs_duty": f"{rate * 100:.1f}%",
                "vat": f"{self.vat_rate * 100:.1f}%",
                "unit": "KG",
                "source": "CEMAC TDC"
            })

        return {
            "tariff_lines": tariff_lines,
            "note": "Using CEMAC Common External Tariff (TDC)",
            "tariff_structure": "CEMAC TDC - 4 categories (5%, 10%, 20%, 30%)"
        }

    def _get_sacu_tariff(self) -> Dict[str, Any]:
        """Southern African Customs Union Tariff"""
        tariff_lines = []

        for chapter in range(1, 98):
            hs_code = f"{chapter:02d}0000"

            # SACU has variable rates, simplified here
            if chapter <= 24:
                rate = 0.0  # Agricultural products
            elif chapter <= 64:
                rate = 0.15  # Manufactured goods
            else:
                rate = 0.20  # Other goods

            tariff_lines.append({
                "hs_code": hs_code,
                "description": f"Chapter {chapter:02d} products",
                "customs_duty": f"{rate * 100:.1f}%",
                "vat": f"{self.vat_rate * 100:.1f}%",
                "unit": "KG",
                "source": "SACU Common Tariff"
            })

        return {
            "tariff_lines": tariff_lines,
            "note": "Using SACU Common Tariff Schedule",
            "tariff_structure": "SACU Common Tariff"
        }

    def _get_generic_tariff(self) -> Dict[str, Any]:
        """Generic fallback tariff structure"""
        tariff_lines = []

        for chapter in range(1, 98):
            hs_code = f"{chapter:02d}0000"

            # Generic simplified structure
            rate = 0.15  # 15% flat rate

            tariff_lines.append({
                "hs_code": hs_code,
                "description": f"Chapter {chapter:02d} products",
                "customs_duty": f"{rate * 100:.1f}%",
                "vat": f"{self.vat_rate * 100:.1f}%",
                "unit": "KG",
                "source": "Generic Tariff"
            })

        return {
            "tariff_lines": tariff_lines,
            "note": "Using generic tariff structure (15% flat rate)",
            "tariff_structure": "Generic simplified tariff"
        }

    async def scrape_regulations(self) -> Dict[str, Any]:
        """Get generic customs regulations"""
        return {
            "required_documents": [
                "Commercial Invoice",
                "Bill of Lading / Airway Bill",
                "Packing List",
                "Certificate of Origin",
                "Import Declaration",
                "Insurance Certificate"
            ],
            "prohibited_items": [
                "Narcotics and illegal drugs",
                "Counterfeit goods",
                "Weapons and ammunition (without license)"
            ],
            "restricted_items": [
                "Pharmaceuticals (requires health authorization)",
                "Food products (requires sanitary certificate)",
                "Plants and animals (requires phytosanitary certificate)"
            ],
            "customs_procedures": {
                "clearance_time": "3-7 days",
                "payment_methods": ["Bank transfer", "Cash", "Customs bond"],
                "inspection_rate": "Random or risk-based"
            }
        }

    async def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate scraped data.

        Args:
            data: Scraped data dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not data.get("country_code"):
            errors.append("Missing country_code")

        if not data.get("tariffs"):
            errors.append("Missing tariffs data")

        tariffs = data.get("tariffs", {})
        if not tariffs.get("tariff_lines"):
            errors.append("No tariff lines found")

        # Validate tariff lines have required fields
        for i, line in enumerate(tariffs.get("tariff_lines", [])[:10]):  # Check first 10
            if not line.get("hs_code"):
                errors.append(f"Tariff line {i} missing hs_code")
            if not line.get("customs_duty"):
                errors.append(f"Tariff line {i} missing customs_duty")

        is_valid = len(errors) == 0
        return is_valid, errors

    async def save_to_db(self, data: Dict[str, Any]) -> bool:
        """
        Save scraped data to MongoDB.

        Args:
            data: Data to save

        Returns:
            bool: True if saved successfully
        """
        if not self.db:
            logger.warning(f"Database not configured for {self.country_code}, skipping save")
            return False

        try:
            collection = self.db["customs_data"]

            # Add metadata
            document = {
                **data,
                "imported_at": self._get_current_time().isoformat(),
                "scraper_version": "1.0.0",
                "scraper_type": "generic",
            }

            # Insert into database
            result = await collection.insert_one(document)

            logger.info(f"Saved data for {self.country_code} with ID: {result.inserted_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving data for {self.country_code}: {str(e)}")
            return False
