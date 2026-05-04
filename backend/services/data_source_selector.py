"""
Smart Data Source Selector
Automatically chooses the best available data source based on:
- Data freshness (most recent)
- API availability (rate limits, errors)
- Data coverage (completeness)

Priority order:
1. OEC - Good coverage, historical data
2. WTO - Tariff-focused, annual updates
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging

from .wto_service import wto_service

logger = logging.getLogger(__name__)

# Try to import OEC service if available
try:
    from .oec_trade_service import OECTradeService
    oec_service = OECTradeService()
    HAS_OEC = True
except ImportError:
    HAS_OEC = False
    oec_service = None
    logger.warning("OEC service not available")


class DataSourceSelector:
    """
    Smart data source selector that chooses the best available source
    based on data freshness, availability, and API limits
    """

    def __init__(self):
        self.wto = wto_service
        self.oec = oec_service if HAS_OEC else None
        self._source_status = {
            "OEC": {"available": HAS_OEC, "last_check": None, "error_count": 0},
            "WTO": {"available": True, "last_check": None, "error_count": 0}
        }

    def get_latest_trade_data(
        self,
        reporter: str,
        partner: str,
        hs_code: Optional[str] = None
    ) -> Dict:
        """
        Get the latest available trade data from the best source

        Priority order:
        1. OEC (good coverage, needs Pro for latest)
        2. WTO (tariff-focused, annual)

        Args:
            reporter: ISO3 reporter country code
            partner: ISO3 partner country code
            hs_code: Optional HS product code

        Returns:
            Dictionary with trade data and source information
        """
        results = {
            "reporter": reporter,
            "partner": partner,
            "hs_code": hs_code,
            "sources_checked": [],
            "data": None,
            "source_used": None,
            "data_period": None,
            "timestamp": datetime.now().isoformat()
        }

        # Try OEC first if available
        if self.oec and self._source_status["OEC"]["available"]:
            try:
                oec_data = self._get_oec_data(reporter, partner, hs_code)

                results["sources_checked"].append({
                    "source": "OEC",
                    "status": "success" if oec_data else "no_data"
                })

                if oec_data:
                    results["data"] = oec_data
                    results["source_used"] = "OEC"
                    results["data_period"] = str(datetime.now().year - 1)
                    self._update_source_status("OEC", success=True)
                    return results

            except Exception as e:
                logger.error(f"OEC error: {str(e)}")
                self._update_source_status("OEC", success=False)
                results["sources_checked"].append({
                    "source": "OEC",
                    "status": "error",
                    "error": str(e)
                })

        # Fallback to WTO (mainly for tariff data)
        if self._source_status["WTO"]["available"]:
            try:
                wto_data = self.wto.get_tariff_data(reporter, partner, hs_code)

                results["sources_checked"].append({
                    "source": "WTO",
                    "status": "success" if wto_data else "no_data",
                    "period": wto_data.get("latest_period") if wto_data else None
                })

                if wto_data and wto_data.get("data"):
                    results["data"] = wto_data["data"]
                    results["source_used"] = "WTO"
                    results["data_period"] = wto_data.get("latest_period")
                    self._update_source_status("WTO", success=True)
                    return results

            except Exception as e:
                logger.error(f"WTO error: {str(e)}")
                self._update_source_status("WTO", success=False)
                results["sources_checked"].append({
                    "source": "WTO",
                    "status": "error",
                    "error": str(e)
                })

        return results

    def get_trade_with_source_info(
        self,
        reporter: str,
        partner: str = None,
        hs_code: Optional[str] = None
    ) -> Dict:
        """
        Get trade data with detailed source information
        Useful for transparency about data provenance
        """
        result = self.get_latest_trade_data(reporter, partner, hs_code)

        # Add source quality information
        result["data_quality"] = {
            "source": result.get("source_used"),
            "freshness": self._get_freshness_label(result.get("data_period")),
            "reliability": self._get_source_reliability(result.get("source_used")),
            "coverage": "partial" if hs_code else "comprehensive"
        }

        return result

    def get_best_source_for_country(self, country_code: str) -> str:
        """
        Determine the best data source for a specific country

        Args:
            country_code: ISO3 country code

        Returns:
            Best source name (OEC or WTO)
        """
        if self.oec and self._source_status["OEC"]["available"]:
            return "OEC"
        return "WTO"

    def get_source_status(self) -> Dict:
        """Get current status of all data sources"""
        return {
            "sources": self._source_status,
            "recommended": self._get_recommended_source(),
            "timestamp": datetime.now().isoformat()
        }

    def compare_data_sources(
        self,
        country_codes: List[str]
    ) -> Dict:
        """
        Compare all data sources to determine which has the latest data

        Returns:
            Comparison report with latest available periods
        """
        comparison = {
            "timestamp": datetime.utcnow().isoformat(),
            "countries_checked": country_codes,
            "sources": {}
        }

        for country in country_codes[:5]:  # Check first 5 to avoid rate limits
            # Check WTO
            try:
                wto_period = self.wto.get_latest_available_year(country)
                if "WTO" not in comparison["sources"]:
                    comparison["sources"]["WTO"] = []
                comparison["sources"]["WTO"].append({
                    "country": country,
                    "latest_period": wto_period
                })
            except Exception as e:
                logger.error(f"Error checking WTO for {country}: {str(e)}")

        # Determine overall winner
        avg_periods = {}
        for source, data in comparison["sources"].items():
            periods = [int(d["latest_period"]) for d in data if d["latest_period"]]
            if periods:
                avg_periods[source] = sum(periods) / len(periods)

        if avg_periods:
            comparison["recommended_source"] = max(avg_periods, key=avg_periods.get)
            comparison["average_latest_year"] = avg_periods

        return comparison

    def _get_oec_data(self, reporter: str, partner: str, hs_code: str) -> Optional[Dict]:
        """Helper to get OEC data with proper format"""
        if not self.oec:
            return None

        try:
            exports = self.oec.get_country_exports(reporter, 2022, limit=50)
            if exports:
                return {
                    "type": "exports",
                    "data": exports,
                    "source": "OEC"
                }
        except Exception as e:
            logger.warning(f"OEC data fetch failed: {e}")

        return None

    def _update_source_status(self, source: str, success: bool):
        """Update source availability status"""
        if source in self._source_status:
            self._source_status[source]["last_check"] = datetime.now().isoformat()
            if success:
                self._source_status[source]["error_count"] = 0
            else:
                self._source_status[source]["error_count"] += 1
                # Disable source after 5 consecutive errors
                if self._source_status[source]["error_count"] >= 5:
                    self._source_status[source]["available"] = False

    def _get_freshness_label(self, period: str) -> str:
        """Get human-readable freshness label"""
        if not period:
            return "unknown"

        try:
            year = int(period)
            current_year = datetime.now().year
            diff = current_year - year

            if diff <= 1:
                return "recent"
            elif diff <= 2:
                return "moderate"
            else:
                return "outdated"
        except ValueError:
            return "unknown"

    def _get_source_reliability(self, source: str) -> str:
        """Get reliability rating for a source"""
        reliability = {
            "OEC": "high",
            "WTO": "high"
        }
        return reliability.get(source, "unknown")

    def _get_recommended_source(self) -> str:
        """Get currently recommended source"""
        for source in ["OEC", "WTO"]:
            if self._source_status.get(source, {}).get("available", False):
                return source
        return "WTO"


# Global selector instance
data_source_selector = DataSourceSelector()

