"""
WTO (World Trade Organization) API Service
Provides tariff data and trade policy information
API Documentation: https://apiportal.wto.org/
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import httpx
WTO Data Portal API Service
Free access to tariff and trade data
API Documentation: https://data.wto.org/
"""

import requests
import time
from typing import Dict, Optional
from datetime import datetime
from requests.exceptions import HTTPError
import logging

logger = logging.getLogger(__name__)


class WTOService:
    """
    WTO API Service for tariff and trade policy data
    Free public access available
def make_wto_request_with_retry(url, params=None, max_retries=5):
    """
    Make WTO API request with exponential backoff for rate limits
    
    Args:
        url: API endpoint URL
        params: Optional query parameters
        max_retries: Maximum number of retry attempts (default: 5)
    
    Returns:
        Response object or None if all retries failed
    """
    def calculate_backoff(attempt):
        """
        Calculate exponential backoff wait time formula: (2^attempt) * 2 seconds.
        
        Note: This is a pure calculation function. Calling code is responsible for
        not invoking it on the final failed attempt (when attempt >= max_retries - 1).
        For max_retries=5, this should only be called for attempts 0-3, yielding
        wait times of 2, 4, 8, 16 seconds.
        """
        return (2 ** attempt) * 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    wait_time = calculate_backoff(attempt)
                    logger.warning(f"⚠️ Rate limit hit (429), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Rate limit exceeded after {max_retries} attempts")
                    return None
            elif e.response.status_code == 400:
                logger.warning(f"⚠️ Bad request (400) for URL: {url}. Skipping...")
                return None
            elif e.response.status_code == 401:
                logger.warning(f"⚠️ Unauthorized (401) for URL: {url}. Check API credentials. Skipping...")
                return None
            else:
                logger.error(f"❌ HTTP error {e.response.status_code}: {e}")
                return None
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = calculate_backoff(attempt)
                logger.warning(f"⚠️ Request timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Request timed out after {max_retries} attempts")
                return None
        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            return None
    
    # All paths in the loop should return, but include this as a safety fallback
    raise RuntimeError(f"Unexpected: retry loop completed without returning (max_retries={max_retries})")


class WTOService:
    """
    WTO Data Portal API Service
    Free access to tariff and trade data
    """
    
    BASE_URL = "https://api.wto.org/timeseries/v1"
    
    def __init__(self):
        self.api_key = os.getenv("WTO_API_KEY", "")
        self._cache = {}
        self._cache_ttl = 7200  # 2 hours cache (tariffs don't change often)
        
    def _get_cache_key(self, *args) -> str:
        return "-".join(str(a) for a in args)
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        entry = self._cache[key]
        return (datetime.utcnow() - entry["timestamp"]).seconds < self._cache_ttl
    
    async def get_tariff_data(
        self,
        reporter: str,
        partner: str = None,
        hs_code: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get tariff data for a country
        
        Args:
            reporter: ISO3 country code
            partner: Optional ISO3 partner country code
            hs_code: Optional HS product code
            
        Returns:
            Tariff data dictionary
        """
        cache_key = self._get_cache_key("tariff", reporter, partner or "all", hs_code or "all")
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]
        
        # Build indicator code for MFN tariffs
        indicator = "HS_M_0010"  # MFN Applied Duties
        
        params = {
            "i": indicator,
            "r": reporter,
            "ps": "last",  # Latest available
            "max": 500
        }
        
        if partner:
            params["p"] = partner
        if hs_code:
            params["pc"] = hs_code
        
        headers = {}
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/data",
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = {
                        "source": "WTO",
                        "data": data.get("Dataset", []),
                        "metadata": {
                            "reporter": reporter,
                            "partner": partner,
                            "hs_code": hs_code,
                            "indicator": indicator
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                        "latest_period": self._extract_latest_period(data.get("Dataset", []))
                    }
                    
                    self._cache[cache_key] = {
                        "data": result,
                        "timestamp": datetime.utcnow()
                    }
                    
                    return result
                    
                elif response.status_code == 401:
                    logger.warning("WTO API: Unauthorized - API key may be required")
                    return None
                else:
                    logger.error(f"WTO API error: {response.status_code}")
                    return None
                    
        pass
    
    def get_tariff_data(
        self,
        reporter_code: str,
        partner_code: str,
        product_code: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get tariff data from WTO
        
        Args:
            reporter_code: ISO3 country code
            partner_code: ISO3 partner code
            product_code: HS code
            
        Returns:
            Tariff data dictionary or None if error
        """
        endpoint = f"{self.BASE_URL}/data"
        
        params = {
            "i": "IDB_MFN_SMPL",  # Indicator: MFN Simple Average
            "r": reporter_code,
            "p": partner_code,
            "fmt": "json"
        }
        
        if product_code:
            params["pc"] = product_code
            
        try:
            response = make_wto_request_with_retry(endpoint, params=params, max_retries=5)
            
            if response is None:
                return None
            
            data = response.json()
            
            # Extract latest year
            dataset = data.get("Dataset", {})
            series = dataset.get("Series", [])
            
            latest_year = None
            if series:
                observations = series[0].get("Obs", [])
                if observations:
                    latest_year = observations[-1].get("Time")
            
            return {
                "source": "WTO",
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "latest_period": latest_year
            }
        except Exception as e:
            logger.error(f"WTO API error: {str(e)}")
            return None
    
    async def get_mfn_average(
        self,
        country_code: str,
        product_group: str = None
    ) -> Optional[Dict]:
        """
        Get MFN (Most Favored Nation) average tariff for a country
        
        Args:
            country_code: ISO3 country code
            product_group: Optional product group (AG=Agriculture, NAMA=Non-Agricultural)
            
        Returns:
            Average tariff information
        """
        cache_key = self._get_cache_key("mfn_avg", country_code, product_group or "all")
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]
        
        # Use simple average indicator
        indicator = "HS_M_0020"  # Simple Average MFN
    def get_trade_indicators(
        self,
        country_code: str,
        indicator: str = "TRADE_VALUE"
    ) -> Optional[Dict]:
        """
        Get trade indicators from WTO
        
        Args:
            country_code: ISO3 country code
            indicator: Trade indicator type
            
        Returns:
            Trade indicator data or None if error
        """
        endpoint = f"{self.BASE_URL}/data"
        
        params = {
            "i": indicator,
            "r": country_code,
            "ps": "last",
            "max": 100
        }
        
        if product_group:
            params["pc"] = product_group
            
        headers = {}
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/data",
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    dataset = data.get("Dataset", [])
                    
                    # Extract average from dataset
                    avg_tariff = None
                    year = None
                    
                    for record in dataset:
                        if record.get("Value"):
                            avg_tariff = float(record["Value"])
                            year = record.get("Year")
                            break
                    
                    result = {
                        "source": "WTO",
                        "country": country_code,
                        "mfn_average_percent": avg_tariff,
                        "product_group": product_group or "all",
                        "year": year,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    self._cache[cache_key] = {
                        "data": result,
                        "timestamp": datetime.utcnow()
                    }
                    
                    return result
                    
        except Exception as e:
            logger.error(f"WTO MFN average error: {str(e)}")
            return None
    
    async def get_afcfta_tariff_comparison(
        self,
        country_code: str,
        hs_code: str
    ) -> Optional[Dict]:
        """
        Compare MFN tariff vs AfCFTA tariff (typically 0%)
        
        Args:
            country_code: ISO3 country code
            hs_code: HS product code
            
        Returns:
            Comparison showing tariff reduction potential
        """
        mfn_data = await self.get_tariff_data(country_code, hs_code=hs_code)
        
        if not mfn_data or not mfn_data.get("data"):
            return None
            
        # Extract MFN rate
        mfn_rate = None
        for record in mfn_data["data"]:
            if record.get("Value"):
                mfn_rate = float(record["Value"])
                break
        
        if mfn_rate is None:
            return None
            
        # AfCFTA rate is typically 0% for most products (after full implementation)
        afcfta_rate = 0.0
        
        return {
            "country": country_code,
            "hs_code": hs_code,
            "mfn_rate_percent": mfn_rate,
            "afcfta_rate_percent": afcfta_rate,
            "tariff_reduction_percent": mfn_rate - afcfta_rate,
            "savings_description": f"Économie de {mfn_rate:.1f}% sous la ZLECAf",
            "source": "WTO + AfCFTA TRS",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_latest_available_year(self, country_code: str) -> Optional[str]:
        """
        Get the latest year with available tariff data
        
        Args:
            country_code: ISO3 country code
            
        Returns:
            Latest year as string (e.g., "2023")
        """
        data = await self.get_tariff_data(country_code)
            "fmt": "json"
        }
        
        try:
            response = make_wto_request_with_retry(endpoint, params=params, max_retries=5)
            
            if response is None:
                return None
            
            data = response.json()
            return {
                "source": "WTO",
                "indicator": indicator,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"WTO API error: {str(e)}")
            return None
    
    def get_latest_available_year(self, country_code: str) -> Optional[str]:
        """
        Get the latest available year for a country in WTO database
        
        Returns:
            Latest year as string or None
        """
        data = self.get_tariff_data(country_code, "wld")
        
        if data and data.get("latest_period"):
            return data["latest_period"]
            
        return None
    
    def _extract_latest_period(self, dataset: List[Dict]) -> Optional[str]:
        """Extract the latest year from dataset records"""
        years = [r.get("Year") for r in dataset if r.get("Year")]
        if years:
            return str(max(int(y) for y in years if y.isdigit()))
        return None


# Global service instance
wto_service = WTOService()
