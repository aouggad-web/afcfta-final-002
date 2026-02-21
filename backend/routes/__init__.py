"""
Routes module for ZLECAf API
Organized by domain for better maintainability

MIGRATION STATUS:
- health.py: COMPLETE
- news.py: COMPLETE  
- oec.py: COMPLETE
- hs_codes.py: COMPLETE
- production.py: COMPLETE
- logistics.py: COMPLETE
- countries.py: COMPLETE
- tariffs.py: COMPLETE
- statistics.py: COMPLETE
- etl.py: COMPLETE
- substitution.py: COMPLETE
- gemini_analysis.py: COMPLETE (NOW WITH CACHE)
- comtrade.py: COMPLETE (UN COMTRADE integration)
- rules_of_origin.py: COMPLETE (NEW - Extracted from server.py)
- hs6_database.py: COMPLETE (UPDATED - Full HS6 search routes)
- authentic_tariffs.py: COMPLETE (54 countries tariff data)
- tariffs_calculation.py: COMPLETE (NEW - Tariff calculation utilities)
- gemini_analysis.py: COMPLETE
- trade_data.py: COMPLETE (UN COMTRADE & WTO integration)
"""

from fastapi import APIRouter

# Import all route modules
from .health import router as health_router
from .news import router as news_router
from .oec import router as oec_router
from .hs_codes import router as hs_codes_router
from .production import router as production_router
from .logistics import router as logistics_router
from .countries import router as countries_router
from .tariffs import router as tariffs_router
from .statistics import router as statistics_router
from .etl import router as etl_router
from .substitution import router as substitution_router
from .gemini_analysis import router as gemini_router
from .comtrade import router as comtrade_router
from .rules_of_origin import router as rules_router
from .hs6_database import router as hs6_db_router
from .authentic_tariffs import router as authentic_tariffs_router
from .tariffs_calculation import router as tariffs_calc_router
try:
    from .gemini_analysis import router as gemini_router
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from .trade_data import router as trade_data_router
    TRADE_DATA_AVAILABLE = True
except ImportError:
    TRADE_DATA_AVAILABLE = False

try:
    from routers.export_router import router as export_router
    EXPORT_ROUTER_AVAILABLE = True
except ImportError:
    EXPORT_ROUTER_AVAILABLE = False

try:
    from .crawl import router as crawl_router
    CRAWL_AVAILABLE = True
except ImportError:
    CRAWL_AVAILABLE = False

try:
    from .tariff_data import router as tariff_data_router
    TARIFF_DATA_AVAILABLE = True
except ImportError:
    TARIFF_DATA_AVAILABLE = False

def register_routes(api_router: APIRouter):
    """Register all route modules to the main API router"""
    api_router.include_router(health_router, tags=["Health"])
    api_router.include_router(news_router, tags=["News"])
    api_router.include_router(oec_router, tags=["OEC Trade"])
    api_router.include_router(hs_codes_router, tags=["HS Codes"])
    api_router.include_router(production_router, tags=["Production"])
    api_router.include_router(logistics_router, tags=["Logistics"])
    api_router.include_router(countries_router, tags=["Countries"])
    api_router.include_router(tariffs_router, tags=["Tariffs"])
    api_router.include_router(statistics_router, tags=["Statistics"])
    api_router.include_router(etl_router, tags=["ETL Administration"])
    api_router.include_router(substitution_router, tags=["Trade Substitution"])
    api_router.include_router(gemini_router, tags=["AI Analysis"])
    api_router.include_router(comtrade_router, tags=["COMTRADE Data"])
    api_router.include_router(rules_router, tags=["Rules of Origin"])
    api_router.include_router(hs6_db_router, tags=["HS6 Database"])
    api_router.include_router(authentic_tariffs_router, tags=["Authentic Tariffs"])
    api_router.include_router(tariffs_calc_router, tags=["Tariff Calculations"])
    if GEMINI_AVAILABLE:
        api_router.include_router(gemini_router, tags=["AI Analysis"])
    if TRADE_DATA_AVAILABLE:
        api_router.include_router(trade_data_router, tags=["Trade Data Sources"])
    
    if EXPORT_ROUTER_AVAILABLE:
        api_router.include_router(export_router, tags=["Export"])
    if CRAWL_AVAILABLE:
        api_router.include_router(crawl_router, tags=["Crawl Orchestration"])
    if TARIFF_DATA_AVAILABLE:
        api_router.include_router(tariff_data_router, tags=["Tariff Data Collection"])
