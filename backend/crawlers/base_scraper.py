"""
Base scraper abstract class for African customs data crawling.

This module provides the abstract base class that all country-specific scrapers
must inherit from. It includes:
- Async HTTP client using httpx
- Rate limiting and retry logic
- Error handling and logging
- MongoDB integration
- Data validation hooks
- Common scraping utilities

All country-specific scrapers should inherit from BaseScraper and implement
the abstract methods: scrape(), validate(), and save_to_db().
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

import httpx
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from .all_countries_registry import get_country_config


# Configure logging
logger = logging.getLogger(__name__)


class ScraperConfig(BaseModel):
    """Configuration for a scraper instance"""
    
    country_code: str = Field(..., description="ISO3 country code")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_delay: float = Field(default=2.0, description="Delay between retries in seconds")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    rate_limit_calls: int = Field(default=10, description="Max calls per rate limit period")
    rate_limit_period: float = Field(default=60.0, description="Rate limit period in seconds")
    user_agent: str = Field(
        default="AfCFTA Customs Scraper/1.0 (+https://afcfta-api.com)",
        description="User agent string for requests"
    )
    follow_redirects: bool = Field(default=True, description="Follow HTTP redirects")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class ScraperResult(BaseModel):
    """Result model for scraper operations"""
    
    country_code: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None
    records_scraped: int = 0
    records_validated: int = 0
    records_saved: int = 0


class RateLimiter:
    """Simple rate limiter using sliding window"""
    
    def __init__(self, calls: int, period: float):
        """
        Initialize rate limiter.
        
        Args:
            calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps: List[datetime] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        async with self._lock:
            now = datetime.utcnow()
            # Remove timestamps outside the current window
            cutoff = now - timedelta(seconds=self.period)
            self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
            
            # If at limit, wait until oldest timestamp expires
            if len(self.timestamps) >= self.calls:
                sleep_time = (self.timestamps[0] - cutoff).total_seconds()
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    # Retry acquire after sleeping
                    return await self.acquire()
            
            # Record this call
            self.timestamps.append(now)


class BaseScraper(ABC):
    """
    Abstract base class for all African customs data scrapers.
    
    This class provides:
    - HTTP client management
    - Rate limiting
    - Retry logic with exponential backoff
    - Error handling and logging
    - MongoDB integration
    - Common scraping utilities
    
    Subclasses must implement:
    - scrape(): Fetch data from customs source
    - validate(): Validate scraped data
    - save_to_db(): Save validated data to MongoDB
    """
    
    def __init__(
        self,
        country_code: str,
        db_client: Optional[AsyncIOMotorClient] = None,
        config: Optional[ScraperConfig] = None
    ):
        """
        Initialize base scraper.
        
        Args:
            country_code: ISO3 country code (e.g., 'GHA', 'NGA')
            db_client: MongoDB async client (optional)
            config: Scraper configuration (optional, uses defaults if not provided)
        """
        self.country_code = country_code.upper()
        self._db_client = db_client
        self._config = config or ScraperConfig(country_code=self.country_code)
        
        # Get country configuration
        self._country_config = get_country_config(self.country_code)
        if not self._country_config:
            raise ValueError(f"Country code '{self.country_code}' not found in registry")
        
        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            calls=self._config.rate_limit_calls,
            period=self._config.rate_limit_period
        )
        
        # HTTP client (lazy initialization)
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Statistics
        self._stats = {
            "requests_made": 0,
            "requests_failed": 0,
            "retries_attempted": 0,
            "rate_limits_hit": 0,
        }
        
        logger.info(
            f"Initialized {self.__class__.__name__} for {self.country_name} ({self.country_code})"
        )
    
    # ==================== Properties ====================
    
    @property
    def country_name(self) -> str:
        """Get country name in English"""
        return self._country_config["name_en"]
    
    @property
    def country_name_fr(self) -> str:
        """Get country name in French"""
        return self._country_config["name_fr"]
    
    @property
    def source_url(self) -> str:
        """Get primary customs data source URL"""
        return self._country_config["customs_url"]
    
    @property
    def region(self) -> str:
        """Get country region"""
        return self._country_config["region"]
    
    @property
    def vat_rate(self) -> float:
        """Get country VAT rate"""
        return self._country_config["vat_rate"]
    
    @property
    def regional_blocks(self) -> List[str]:
        """Get regional economic blocks country belongs to"""
        return [block.value for block in self._country_config["blocks"]]
    
    @property
    def priority(self) -> int:
        """Get crawling priority level"""
        return self._country_config["priority"].value
    
    @property
    def database(self) -> Optional[AsyncIOMotorDatabase]:
        """Get MongoDB database instance"""
        if self._db_client:
            return self._db_client.zlecaf_customs
        return None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            headers = {
                "User-Agent": self._config.user_agent,
                "Accept": "text/html,application/json,application/xml",
                "Accept-Language": "en,fr",
            }
            self._http_client = httpx.AsyncClient(
                headers=headers,
                timeout=self._config.timeout,
                follow_redirects=self._config.follow_redirects,
                verify=self._config.verify_ssl,
            )
        return self._http_client
    
    # ==================== Abstract Methods ====================
    
    @abstractmethod
    async def scrape(self) -> Dict[str, Any]:
        """
        Scrape customs data from source.
        
        This method should:
        1. Fetch data from customs website/API
        2. Parse the data into a structured format
        3. Return raw scraped data
        
        Returns:
            Dictionary containing scraped data
            
        Raises:
            Exception: If scraping fails
        """
        pass
    
    @abstractmethod
    async def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped data.
        
        This method should:
        1. Check data completeness
        2. Verify data types and formats
        3. Validate against business rules
        4. Log validation errors
        
        Args:
            data: Raw scraped data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def save_to_db(self, data: Dict[str, Any]) -> int:
        """
        Save validated data to MongoDB.
        
        This method should:
        1. Transform data to database schema
        2. Handle upserts (update or insert)
        3. Maintain data versioning if needed
        4. Log save operations
        
        Args:
            data: Validated data to save
            
        Returns:
            Number of records saved
            
        Raises:
            Exception: If database save fails
        """
        pass
    
    # ==================== HTTP Methods ====================
    
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """
        Fetch URL with rate limiting and retry logic.
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            params: URL parameters
            data: Form data
            json: JSON data
            headers: Additional headers
            timeout: Request timeout (overrides default)
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPError: If all retries fail
        """
        await self._rate_limiter.acquire()
        
        retry_count = 0
        last_exception = None
        
        while retry_count <= self._config.max_retries:
            try:
                self._stats["requests_made"] += 1
                
                response = await self.http_client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=headers,
                    timeout=timeout or self._config.timeout,
                )
                
                response.raise_for_status()
                
                logger.debug(f"Successfully fetched {url} (attempt {retry_count + 1})")
                return response
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                self._stats["requests_failed"] += 1
                
                # Don't retry client errors (4xx) except 429 (rate limit)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    logger.error(f"Client error fetching {url}: {e}")
                    raise
                
                if e.response.status_code == 429:
                    self._stats["rate_limits_hit"] += 1
                    logger.warning(f"Rate limited by server: {url}")
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                self._stats["requests_failed"] += 1
                logger.warning(f"Request error fetching {url}: {e}")
            
            # Retry with exponential backoff
            if retry_count < self._config.max_retries:
                self._stats["retries_attempted"] += 1
                delay = self._config.retry_delay * (2 ** retry_count)
                logger.info(f"Retrying in {delay}s (attempt {retry_count + 1}/{self._config.max_retries})")
                await asyncio.sleep(delay)
                retry_count += 1
            else:
                break
        
        # All retries exhausted
        logger.error(f"Failed to fetch {url} after {self._config.max_retries} retries")
        if last_exception:
            raise last_exception
        raise httpx.RequestError(f"Failed to fetch {url}")
    
    async def fetch_json(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch JSON data from URL.
        
        Args:
            url: URL to fetch
            method: HTTP method
            **kwargs: Additional arguments for fetch()
            
        Returns:
            Parsed JSON response
        """
        response = await self.fetch(url, method=method, **kwargs)
        return response.json()
    
    async def fetch_text(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> str:
        """
        Fetch text content from URL.
        
        Args:
            url: URL to fetch
            method: HTTP method
            **kwargs: Additional arguments for fetch()
            
        Returns:
            Text response
        """
        response = await self.fetch(url, method=method, **kwargs)
        return response.text
    
    # ==================== Public Methods ====================
    
    async def run(self) -> ScraperResult:
        """
        Run the complete scraping pipeline.
        
        This method:
        1. Scrapes data from source
        2. Validates the data
        3. Saves to database
        4. Returns result summary
        
        Returns:
            ScraperResult with operation details
        """
        start_time = datetime.utcnow()
        result = ScraperResult(
            country_code=self.country_code,
            success=False
        )
        
        try:
            logger.info(f"Starting scrape for {self.country_name} ({self.country_code})")
            
            # Step 1: Scrape
            data = await self.scrape()
            if not data:
                raise ValueError("Scrape returned empty data")
            
            result.records_scraped = self._count_records(data)
            logger.info(f"Scraped {result.records_scraped} records")
            
            # Step 2: Validate
            is_valid = await self.validate(data)
            if not is_valid:
                raise ValueError("Data validation failed")
            
            result.records_validated = result.records_scraped
            logger.info(f"Validated {result.records_validated} records")
            
            # Step 3: Save to DB (if client available)
            if self.database:
                records_saved = await self.save_to_db(data)
                result.records_saved = records_saved
                logger.info(f"Saved {records_saved} records to database")
            else:
                logger.warning("No database client, skipping save")
                result.records_saved = 0
            
            # Success
            result.success = True
            result.data = data
            
        except Exception as e:
            logger.error(f"Scraper failed for {self.country_code}: {e}", exc_info=True)
            result.error = str(e)
        
        finally:
            # Calculate duration
            end_time = datetime.utcnow()
            result.duration_seconds = (end_time - start_time).total_seconds()
            
            # Log statistics
            logger.info(
                f"Scraper completed for {self.country_code} - "
                f"Success: {result.success}, "
                f"Duration: {result.duration_seconds:.2f}s, "
                f"Requests: {self._stats['requests_made']}, "
                f"Retries: {self._stats['retries_attempted']}"
            )
        
        return result
    
    async def close(self):
        """Close HTTP client and cleanup resources"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            logger.debug(f"Closed HTTP client for {self.country_code}")
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    # ==================== Helper Methods ====================
    
    def _count_records(self, data: Dict[str, Any]) -> int:
        """
        Count records in scraped data.
        
        Override this method if data structure is non-standard.
        
        Args:
            data: Scraped data
            
        Returns:
            Number of records
        """
        if isinstance(data, dict):
            # Look for common list fields
            for key in ["records", "items", "data", "results"]:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
            # Count all list values
            return sum(len(v) for v in data.values() if isinstance(v, list))
        elif isinstance(data, list):
            return len(data)
        return 1
    
    def make_absolute_url(self, url: str, base: Optional[str] = None) -> str:
        """
        Convert relative URL to absolute.
        
        Args:
            url: URL to convert
            base: Base URL (uses source_url if not provided)
            
        Returns:
            Absolute URL
        """
        if url.startswith(("http://", "https://")):
            return url
        return urljoin(base or self.source_url, url)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraper statistics.
        
        Returns:
            Dictionary with scraper statistics
        """
        return {
            **self._stats,
            "country_code": self.country_code,
            "country_name": self.country_name,
        }
