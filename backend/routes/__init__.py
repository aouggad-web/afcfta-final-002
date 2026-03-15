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
- rules_of_origin.py: COMPLETE (Extracted from server.py)
- hs6_database.py: COMPLETE (Full HS6 search routes)
- authentic_tariffs.py: COMPLETE (54 countries tariff data)
- tariffs_calculation.py: COMPLETE (Tariff calculation utilities)
- trade_data.py: COMPLETE (WTO integration)
- calculator.py: COMPLETE (Main tariff calculator - extracted from server.py)
"""

from fastapi import APIRouter
import logging

_logger = logging.getLogger(__name__)

# Import all route modules
from .health import router as health_router

try:
    from .news import router as news_router
    NEWS_AVAILABLE = True
except ImportError:
    news_router = None
    NEWS_AVAILABLE = False

from .oec import router as oec_router
from .hs_codes import router as hs_codes_router
from .production import router as production_router
from .logistics import router as logistics_router
from .countries import router as countries_router
from .tariffs import router as tariffs_router
from .statistics import router as statistics_router
from .etl import router as etl_router
from .substitution import router as substitution_router
from .rules_of_origin import router as rules_router
from .hs6_database import router as hs6_db_router
from .authentic_tariffs import router as authentic_tariffs_router
from .tariffs_calculation import router as tariffs_calc_router

try:
    from .faostat import router as faostat_router
    FAOSTAT_AVAILABLE = True
except ImportError:
    faostat_router = None
    FAOSTAT_AVAILABLE = False

    _logger.warning("faostat package not installed; FAOSTAT routes will be unavailable")
    faostat_router = None
    FAOSTAT_AVAILABLE = False
from .calculator import router as calculator_router

try:
    from .gemini_analysis import router as gemini_router
    GEMINI_AVAILABLE = True
except ImportError:
    gemini_router = None
    GEMINI_AVAILABLE = False

try:
    from .trade_data import router as trade_data_router
    TRADE_DATA_AVAILABLE = True
except ImportError:
    trade_data_router = None
    TRADE_DATA_AVAILABLE = False

try:
    from routers.export_router import router as export_router
    EXPORT_ROUTER_AVAILABLE = True
except ImportError:
    export_router = None
    EXPORT_ROUTER_AVAILABLE = False

try:
    from .crawl import router as crawl_router
    CRAWL_AVAILABLE = True
except ImportError:
    crawl_router = None
    CRAWL_AVAILABLE = False

try:
    from .tariff_data import router as tariff_data_router
    TARIFF_DATA_AVAILABLE = True
except ImportError:
    tariff_data_router = None
    TARIFF_DATA_AVAILABLE = False

try:
    from .regulatory_engine import router as regulatory_engine_router
    REGULATORY_ENGINE_AVAILABLE = True
except ImportError:
    regulatory_engine_router = None
    REGULATORY_ENGINE_AVAILABLE = False

try:
    from .search import router as search_router
    SEARCH_AVAILABLE = True
except ImportError:
    search_router = None
    SEARCH_AVAILABLE = False

try:
    from .cache import router as cache_router
    CACHE_ROUTER_AVAILABLE = True
except ImportError:
    cache_router = None
    CACHE_ROUTER_AVAILABLE = False

try:
    from .dza_crawler import router as dza_crawler_router
    DZA_CRAWLER_AVAILABLE = True
except ImportError:
    dza_crawler_router = None
    DZA_CRAWLER_AVAILABLE = False

try:
    from .enhanced_calculator import router as enhanced_calculator_router
    ENHANCED_CALCULATOR_AVAILABLE = True
except ImportError:
    enhanced_calculator_router = None
    ENHANCED_CALCULATOR_AVAILABLE = False

try:
    from .north_africa_crawlers import router as north_africa_crawlers_router
    NORTH_AFRICA_CRAWLERS_AVAILABLE = True
except ImportError:
    north_africa_crawlers_router = None
    NORTH_AFRICA_CRAWLERS_AVAILABLE = False

try:
    from .cemac_crawlers import router as cemac_crawlers_router
    CEMAC_CRAWLERS_AVAILABLE = True
except ImportError:
    cemac_crawlers_router = None
    CEMAC_CRAWLERS_AVAILABLE = False

try:
    from .regional_data import router as regional_data_router
    REGIONAL_DATA_AVAILABLE = True
except ImportError:
    regional_data_router = None
    REGIONAL_DATA_AVAILABLE = False

try:
    from .regional_calculator import router as regional_calculator_router
    REGIONAL_CALCULATOR_AVAILABLE = True
except ImportError:
    regional_calculator_router = None
    REGIONAL_CALCULATOR_AVAILABLE = False

try:
    from .investment_intelligence import router as investment_intelligence_router
    INVESTMENT_INTELLIGENCE_AVAILABLE = True
except ImportError:
    investment_intelligence_router = None
    INVESTMENT_INTELLIGENCE_AVAILABLE = False

try:
    from .uma_regions import router as uma_regions_router
    UMA_REGIONS_AVAILABLE = True
except ImportError:
    uma_regions_router = None
    UMA_REGIONS_AVAILABLE = False

try:
    import importlib.util as _ilu
    import os as _os
    _ep_path = _os.path.join(_os.path.dirname(__file__), "..", "api", "v2", "endpoints.py")
    _spec = _ilu.spec_from_file_location("api_v2_endpoints", _ep_path)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    api_v2_router = _mod.router
    API_V2_AVAILABLE = True
except Exception:
    api_v2_router = None
    API_V2_AVAILABLE = False

try:
    from .sadc_intelligence import router as sadc_intelligence_router
    SADC_INTELLIGENCE_AVAILABLE = True
except ImportError:
    sadc_intelligence_router = None
    SADC_INTELLIGENCE_AVAILABLE = False

try:
    from .ai_intelligence import router as ai_intelligence_router
    AI_INTELLIGENCE_AVAILABLE = True
except ImportError:
    ai_intelligence_router = None
    AI_INTELLIGENCE_AVAILABLE = False

try:
    from .regional_analytics import router as regional_analytics_router
    REGIONAL_ANALYTICS_AVAILABLE = True
except ImportError:
    regional_analytics_router = None
    REGIONAL_ANALYTICS_AVAILABLE = False

try:
    from .enhanced_search import router as enhanced_search_router
    ENHANCED_SEARCH_AVAILABLE = True
except ImportError:
    enhanced_search_router = None
    ENHANCED_SEARCH_AVAILABLE = False

try:
    from .performance import router as performance_router
    PERFORMANCE_AVAILABLE = True
except ImportError:
    performance_router = None
    PERFORMANCE_AVAILABLE = False

try:
    from .banking import router as banking_router
    BANKING_AVAILABLE = True
except ImportError:
    banking_router = None
    BANKING_AVAILABLE = False

try:
    from .postgres_tariffs import router as postgres_tariffs_router
    POSTGRES_TARIFFS_AVAILABLE = True
except ImportError:
    postgres_tariffs_router = None
    POSTGRES_TARIFFS_AVAILABLE = False

try:
    from api.graphql.schema import router as graphql_router
    GRAPHQL_AVAILABLE = True
except ImportError:
    graphql_router = None
    GRAPHQL_AVAILABLE = False

try:
    from api.websocket.handlers import router as websocket_router
    WEBSOCKET_AVAILABLE = True
except ImportError:
    websocket_router = None
    WEBSOCKET_AVAILABLE = False

try:
    from api.mobile.lightweight_endpoints import router as mobile_router
    MOBILE_AVAILABLE = True
except ImportError:
    mobile_router = None
    MOBILE_AVAILABLE = False

try:
    from .currencies import router as currencies_router
    CURRENCIES_AVAILABLE = True
except ImportError:
    currencies_router = None
    CURRENCIES_AVAILABLE = False

try:
    from .exchange_rates import router as exchange_rates_router
    EXCHANGE_RATES_AVAILABLE = True
except ImportError:
    exchange_rates_router = None
    EXCHANGE_RATES_AVAILABLE = False


def register_routes(api_router: APIRouter):
    """Register all route modules to the main API router"""
    api_router.include_router(health_router, tags=["Health"])
    if NEWS_AVAILABLE:
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
    if GEMINI_AVAILABLE:
        api_router.include_router(gemini_router, tags=["AI Analysis"])
    api_router.include_router(rules_router, tags=["Rules of Origin"])
    api_router.include_router(hs6_db_router, tags=["HS6 Database"])
    api_router.include_router(authentic_tariffs_router, tags=["Authentic Tariffs"])
    api_router.include_router(tariffs_calc_router, tags=["Tariff Calculations"])
    if FAOSTAT_AVAILABLE:
        api_router.include_router(faostat_router, tags=["FAOSTAT Production 2024"])
    api_router.include_router(calculator_router, tags=["Calculator"])
    if TRADE_DATA_AVAILABLE:
        api_router.include_router(trade_data_router, tags=["Trade Data Sources"])
    if EXPORT_ROUTER_AVAILABLE:
        api_router.include_router(export_router, tags=["Export"])
    if CRAWL_AVAILABLE:
        api_router.include_router(crawl_router, tags=["Crawl Orchestration"])
    if TARIFF_DATA_AVAILABLE:
        api_router.include_router(tariff_data_router, tags=["Tariff Data Collection"])
    if REGULATORY_ENGINE_AVAILABLE:
        api_router.include_router(regulatory_engine_router, tags=["Regulatory Engine v3"])
    if SEARCH_AVAILABLE:
        api_router.include_router(search_router, tags=["Text Search"])
    if CACHE_ROUTER_AVAILABLE:
        api_router.include_router(cache_router, tags=["Cache Management"])
    if DZA_CRAWLER_AVAILABLE:
        api_router.include_router(dza_crawler_router, tags=["DZA Crawler"])
    if ENHANCED_CALCULATOR_AVAILABLE:
        api_router.include_router(enhanced_calculator_router, tags=["Enhanced Calculator v2"])
    if NORTH_AFRICA_CRAWLERS_AVAILABLE:
        api_router.include_router(north_africa_crawlers_router, tags=["North Africa Crawlers"])
    if CEMAC_CRAWLERS_AVAILABLE:
        api_router.include_router(cemac_crawlers_router, tags=["CEMAC Crawlers"])
    if REGIONAL_DATA_AVAILABLE:
        api_router.include_router(regional_data_router, tags=["Regional Data Inventory"])
    if REGIONAL_CALCULATOR_AVAILABLE:
        api_router.include_router(regional_calculator_router, tags=["Regional Calculator"])
    if INVESTMENT_INTELLIGENCE_AVAILABLE:
        api_router.include_router(investment_intelligence_router, tags=["Investment Intelligence"])
    if UMA_REGIONS_AVAILABLE:
        api_router.include_router(uma_regions_router, tags=["UMA North Africa Regions"])
    if API_V2_AVAILABLE:
        api_router.include_router(api_v2_router, tags=["API v2"])
    if AI_INTELLIGENCE_AVAILABLE:
        api_router.include_router(ai_intelligence_router, tags=["AI Intelligence"])
    if ENHANCED_SEARCH_AVAILABLE:
        api_router.include_router(enhanced_search_router, tags=["Enhanced Search"])
    if SADC_INTELLIGENCE_AVAILABLE:
        api_router.include_router(sadc_intelligence_router, tags=["SADC Intelligence"])
    if REGIONAL_ANALYTICS_AVAILABLE:
        api_router.include_router(regional_analytics_router, tags=["Regional Analytics Dashboard"])
    if PERFORMANCE_AVAILABLE:
        api_router.include_router(performance_router, tags=["Performance Monitoring"])
    if BANKING_AVAILABLE:
        api_router.include_router(banking_router, tags=["Banking System"])
    if POSTGRES_TARIFFS_AVAILABLE:
        api_router.include_router(postgres_tariffs_router, tags=["PostgreSQL Tariffs"])
    if GRAPHQL_AVAILABLE:
        api_router.include_router(graphql_router, tags=["GraphQL"])
    if WEBSOCKET_AVAILABLE:
        api_router.include_router(websocket_router, tags=["WebSocket Real-time"])
    if MOBILE_AVAILABLE:
        api_router.include_router(mobile_router, tags=["Mobile API"])
    if CURRENCIES_AVAILABLE:
        api_router.include_router(currencies_router, tags=["Currencies"])
    if EXCHANGE_RATES_AVAILABLE:
        api_router.include_router(exchange_rates_router, tags=["Exchange Rates"])
