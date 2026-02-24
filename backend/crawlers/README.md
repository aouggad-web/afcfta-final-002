# African Customs Data Crawler Infrastructure

Production-ready infrastructure for scraping customs data from all 54 African countries.

## 📋 Overview

This infrastructure provides:

- **Abstract base class** for all scrapers with common functionality
- **Factory pattern** for dynamic scraper creation
- **Complete registry** of all 54 African countries with metadata
- **Rate limiting** and retry logic for robust scraping
- **MongoDB integration** with motor (async)
- **Validation framework** for data quality
- **Async/await** implementation using httpx
- **Production-ready** error handling and logging

## 🏗️ Architecture

```
backend/crawlers/
├── __init__.py                      # Main package exports
├── base_scraper.py                  # Abstract base class
├── scraper_factory.py               # Factory pattern implementation
├── all_countries_registry.py        # 54 countries configuration
├── countries/                       # Country-specific scrapers
│   ├── __init__.py
│   ├── ghana_example.py             # Example implementation
│   └── [other country scrapers]
└── validators/                      # Data validators
    └── __init__.py
```

## 🚀 Quick Start

### Basic Usage

```python
from backend.crawlers import ScraperFactory

# Get scraper for a specific country
scraper = ScraperFactory.get_scraper("GHA")
result = await scraper.run()

print(f"Success: {result.success}")
print(f"Records scraped: {result.records_scraped}")
print(f"Duration: {result.duration_seconds}s")
```

### With MongoDB

```python
from motor.motor_asyncio import AsyncIOMotorClient
from backend.crawlers import ScraperFactory

# Connect to MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")

# Create scraper with database
scraper = ScraperFactory.get_scraper("GHA", db_client=client)

# Run the scraper
async with scraper:
    result = await scraper.run()
    print(f"Saved {result.records_saved} records")
```

### Custom Configuration

```python
from backend.crawlers import ScraperFactory, ScraperConfig

# Configure scraper behavior
config = ScraperConfig(
    country_code="NGA",
    max_retries=5,
    retry_delay=3.0,
    timeout=60.0,
    rate_limit_calls=10,
    rate_limit_period=60.0
)

scraper = ScraperFactory.get_scraper("NGA", config=config)
```

## 📦 Components

### 1. BaseScraper (Abstract Class)

All scrapers inherit from `BaseScraper` which provides:

**Abstract Methods** (must be implemented):
- `scrape()` - Fetch data from customs source
- `validate()` - Validate scraped data
- `save_to_db()` - Save to MongoDB

**Built-in Features**:
- HTTP client with rate limiting
- Retry logic with exponential backoff
- Error handling and logging
- Request statistics tracking
- URL utilities

**Properties**:
- `country_code` - ISO3 country code
- `country_name` - Country name (English)
- `source_url` - Customs website URL
- `region` - African region
- `vat_rate` - VAT rate percentage
- `regional_blocks` - Economic blocks (ECOWAS, EAC, etc.)
- `priority` - Crawling priority (1-3)

### 2. ScraperFactory

Factory for creating and managing scrapers.

**Methods**:

```python
# Get single scraper
scraper = ScraperFactory.get_scraper("GHA")

# Get by priority
high_priority = ScraperFactory.get_priority_scrapers("HIGH")

# Get by region
west_africa = ScraperFactory.get_region_scrapers("WEST_AFRICA")

# Get by economic block
ecowas = ScraperFactory.get_block_scrapers("ECOWAS")

# Get multiple countries
scrapers = ScraperFactory.get_multiple_scrapers(["GHA", "NGA", "KEN"])

# Get all 54 countries
all_scrapers = ScraperFactory.get_all_scrapers()

# Registry statistics
stats = ScraperFactory.get_registry_stats()
```

### 3. Countries Registry

Complete configuration for all 54 African countries.

**Data Included**:
- ISO2 and ISO3 codes
- Country names (English & French)
- Regions (North, West, Central, East, Southern Africa)
- Regional economic blocks (ECOWAS, CEMAC, EAC, SACU, SADC, etc.)
- VAT rates
- Customs website URLs
- Supported languages
- Priority levels
- Notes and metadata

**Utility Functions**:

```python
from backend.crawlers import (
    get_country_config,
    get_countries_by_region,
    get_countries_by_block,
    get_priority_countries,
    validate_registry,
    Region,
    RegionalBlock,
    Priority
)

# Get country config
config = get_country_config("GHA")

# Get countries by region
west = get_countries_by_region(Region.WEST_AFRICA)

# Get countries by block
ecowas = get_countries_by_block(RegionalBlock.ECOWAS)

# Get by priority
high = get_priority_countries(Priority.HIGH)

# Validate registry
report = validate_registry()
```

## 🔧 Creating Custom Scrapers

### Step 1: Create Scraper Class

Create a new file in `backend/crawlers/countries/`:

```python
# backend/crawlers/countries/ghana.py
from typing import Dict, Any
from ..base_scraper import BaseScraper

class GhanaScraper(BaseScraper):
    """Ghana customs scraper"""
    
    # Required: tells factory which country
    _country_code = "GHA"
    
    async def scrape(self) -> Dict[str, Any]:
        """Fetch Ghana customs data"""
        # Use self.fetch() for HTTP requests
        response = await self.fetch(f"{self.source_url}/tariffs")
        
        # Parse and return data
        return {
            "country_code": self.country_code,
            "tariffs": parse_tariffs(response.text),
            "timestamp": datetime.utcnow(),
        }
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate scraped data"""
        if not data or "tariffs" not in data:
            return False
        return True
    
    async def save_to_db(self, data: Dict[str, Any]) -> int:
        """Save to MongoDB"""
        collection = self.database.customs_ghana
        result = await collection.update_one(
            {"country_code": "GHA"},
            {"$set": data},
            upsert=True
        )
        return 1 if result.upserted_id or result.modified_count > 0 else 0
```

### Step 2: Auto-Registration

The scraper is automatically registered when the module is imported, thanks to the `_country_code` attribute.

### Step 3: Use Your Scraper

```python
# Your custom scraper is now available
scraper = ScraperFactory.get_scraper("GHA")
# Returns GhanaScraper instance instead of GenericScraper
```

## 🌍 Country Registry

### Regions

- **North Africa** (6 countries): Algeria, Egypt, Libya, Morocco, Sudan, Tunisia
- **West Africa** (16 countries): Benin, Burkina Faso, Cape Verde, Côte d'Ivoire, Gambia, Ghana, Guinea, Guinea-Bissau, Liberia, Mali, Mauritania, Niger, Nigeria, Senegal, Sierra Leone, Togo
- **Central Africa** (8 countries): Cameroon, Central African Republic, Chad, Congo, DR Congo, Equatorial Guinea, Gabon, São Tomé and Príncipe
- **East Africa** (14 countries): Burundi, Comoros, Djibouti, Eritrea, Ethiopia, Kenya, Madagascar, Malawi, Mauritius, Rwanda, Seychelles, Somalia, South Sudan, Uganda
- **Southern Africa** (10 countries): Angola, Botswana, Eswatini, Lesotho, Mozambique, Namibia, South Africa, Tanzania, Zambia, Zimbabwe

### Regional Economic Blocks

- **ECOWAS/CEDEAO** (15 members): Economic Community of West African States
- **UEMOA** (8 members): West African Economic and Monetary Union
- **CEMAC** (6 members): Economic and Monetary Community of Central Africa
- **EAC** (6 members): East African Community
- **SACU** (5 members): Southern African Customs Union
- **SADC** (16 members): Southern African Development Community
- **COMESA** (19 members): Common Market for Eastern and Southern Africa
- **AMU** (5 members): Arab Maghreb Union
- **ECCAS** (11 members): Economic Community of Central African States
- **IGAD** (8 members): Intergovernmental Authority on Development

### Priority Levels

- **HIGH** (19 countries): Major economies, good data availability
- **MEDIUM** (18 countries): Medium economies, partial data
- **LOW** (17 countries): Small economies, limited data

## 🔒 Features

### Rate Limiting

Built-in rate limiter using sliding window algorithm:

```python
config = ScraperConfig(
    country_code="GHA",
    rate_limit_calls=10,    # Max 10 calls
    rate_limit_period=60.0   # Per 60 seconds
)
```

### Retry Logic

Automatic retry with exponential backoff:

```python
config = ScraperConfig(
    country_code="GHA",
    max_retries=3,           # Retry up to 3 times
    retry_delay=2.0          # Initial delay 2s (doubles each retry)
)
```

### Error Handling

- HTTP errors with status code handling
- Network timeouts and connection errors
- Rate limit detection (429 responses)
- Comprehensive logging

### Statistics Tracking

```python
scraper = ScraperFactory.get_scraper("GHA")
await scraper.run()

stats = scraper.get_stats()
# {
#   "requests_made": 10,
#   "requests_failed": 2,
#   "retries_attempted": 2,
#   "rate_limits_hit": 0,
#   "country_code": "GHA",
#   "country_name": "Ghana"
# }
```

## 📊 Data Models

### ScraperConfig

Configuration model:

```python
ScraperConfig(
    country_code: str           # ISO3 code
    max_retries: int = 3        # Max retry attempts
    retry_delay: float = 2.0    # Retry delay (seconds)
    timeout: float = 30.0       # Request timeout
    rate_limit_calls: int = 10  # Max calls per period
    rate_limit_period: float = 60.0  # Period in seconds
    user_agent: str = "..."     # User agent string
    follow_redirects: bool = True
    verify_ssl: bool = True
)
```

### ScraperResult

Result model:

```python
ScraperResult(
    country_code: str
    success: bool
    data: Optional[Dict]        # Scraped data
    error: Optional[str]        # Error message if failed
    timestamp: datetime
    duration_seconds: float
    records_scraped: int
    records_validated: int
    records_saved: int
)
```

## 🧪 Testing

Run the test suite:

```bash
python test_scraper_infrastructure.py
```

Tests cover:
- Registry completeness (54 countries)
- Scraper creation and configuration
- Bulk operations (priority, region, block)
- Generic scraper functionality
- Factory registry system
- Properties and utilities

## 📝 Examples

### Example 1: Scrape High Priority Countries

```python
import asyncio
from backend.crawlers import ScraperFactory

async def scrape_high_priority():
    scrapers = ScraperFactory.get_priority_scrapers("HIGH")
    
    for scraper in scrapers:
        print(f"Scraping {scraper.country_name}...")
        async with scraper:
            result = await scraper.run()
            if result.success:
                print(f"  ✓ Success: {result.records_scraped} records")
            else:
                print(f"  ✗ Failed: {result.error}")

asyncio.run(scrape_high_priority())
```

### Example 2: Scrape ECOWAS Countries

```python
import asyncio
from backend.crawlers import ScraperFactory, RegionalBlock
from motor.motor_asyncio import AsyncIOMotorClient

async def scrape_ecowas():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    scrapers = ScraperFactory.get_block_scrapers(
        RegionalBlock.ECOWAS,
        db_client=client
    )
    
    results = []
    for scraper in scrapers:
        async with scraper:
            result = await scraper.run()
            results.append(result)
    
    # Summary
    successful = sum(1 for r in results if r.success)
    print(f"Scraped {successful}/{len(results)} ECOWAS countries")

asyncio.run(scrape_ecowas())
```

### Example 3: Parallel Scraping

```python
import asyncio
from backend.crawlers import ScraperFactory

async def scrape_country(country_code):
    scraper = ScraperFactory.get_scraper(country_code)
    async with scraper:
        return await scraper.run()

async def scrape_parallel():
    countries = ["GHA", "NGA", "KEN", "ZAF", "EGY"]
    
    # Scrape in parallel
    results = await asyncio.gather(
        *[scrape_country(code) for code in countries]
    )
    
    for result in results:
        status = "✓" if result.success else "✗"
        print(f"{status} {result.country_code}: {result.duration_seconds:.2f}s")

asyncio.run(scrape_parallel())
```

## 🛠️ Advanced Usage

### Custom HTTP Headers

```python
scraper = ScraperFactory.get_scraper("GHA")

# Add custom headers for specific request
response = await scraper.fetch(
    url="https://example.com/api",
    headers={"Authorization": "Bearer token123"}
)
```

### Form Submissions

```python
scraper = ScraperFactory.get_scraper("GHA")

# POST form data
response = await scraper.fetch(
    url="https://example.com/search",
    method="POST",
    data={"hs_code": "080300", "year": "2025"}
)
```

### JSON APIs

```python
scraper = ScraperFactory.get_scraper("GHA")

# Fetch JSON directly
data = await scraper.fetch_json("https://api.example.com/tariffs")
```

## 📚 Dependencies

Required packages (from `backend/requirements.txt`):

- `httpx>=0.28.1` - Async HTTP client
- `motor>=3.3.1` - Async MongoDB driver
- `pydantic>=2.12.0` - Data validation
- `python-dotenv>=1.1.1` - Environment configuration

## 🔐 Security

- SSL verification enabled by default
- Configurable user agent
- Rate limiting to respect server policies
- No credentials stored in code
- MongoDB connection string from environment

## 📖 API Reference

See the docstrings in each module for detailed API documentation:

- `base_scraper.py` - BaseScraper class and utilities
- `scraper_factory.py` - ScraperFactory and GenericScraper
- `all_countries_registry.py` - Country configurations and utilities

## 🤝 Contributing

To add a new country scraper:

1. Create `backend/crawlers/countries/{country_name}.py`
2. Inherit from `BaseScraper`
3. Set `_country_code` class attribute
4. Implement `scrape()`, `validate()`, and `save_to_db()`
5. Test with `ScraperFactory.get_scraper(country_code)`

The scraper will be automatically registered!

## 📄 License

Part of the AfCFTA API project.

## 🆘 Support

For issues or questions:
1. Check the test suite for examples
2. Review the example scraper (`ghana_example.py`)
3. Check the docstrings for detailed API info
4. Review existing country scrapers for patterns

## 🎯 Roadmap

- [ ] Add more country-specific scrapers
- [ ] Implement advanced validators
- [ ] Add proxy support
- [ ] Add selenium/playwright for JavaScript sites
- [ ] Add data normalization layer
- [ ] Add caching layer
- [ ] Add scheduling system
- [ ] Add monitoring and alerting
- [ ] Add data quality metrics
- [ ] Add API endpoints for scraper management

---

**Version:** 1.0.0  
**Last Updated:** February 2025  
**Status:** Production Ready ✅
