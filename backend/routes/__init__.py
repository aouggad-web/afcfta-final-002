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

from fastapi import APIRouter, Depends
import logging

from auth import require_auth

_auth = [Depends(require_auth)]

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
from .rules_of_origin import router as rules_router, init_data as init_rules_data
from .hs6_database import router as hs6_db_router
from .authentic_tariffs import router as authentic_tariffs_router
from .tariffs_calculation import router as tariffs_calc_router

try:
    from .dismantlement import router as dismantlement_router
    DISMANTLEMENT_AVAILABLE = True
except ImportError as e:
    dismantlement_router = None
    DISMANTLEMENT_AVAILABLE = False
    _logger.warning(f"Dismantlement schedule route unavailable: {e}")

# Load Rules of Origin data
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from etl.afcfta_rules_of_origin import CHAPTER_RULES, ORIGIN_TYPES
    RULES_OF_ORIGIN_DATA_LOADED = True
    _logger.info(f"Loaded {len(CHAPTER_RULES)} chapter rules of origin")
except Exception as e:
    CHAPTER_RULES = {}
    ORIGIN_TYPES = {}
    RULES_OF_ORIGIN_DATA_LOADED = False
    _logger.warning(f"Failed to load rules of origin data: {e}")

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

try:
    from .admin_projects import router as admin_projects_router
    ADMIN_PROJECTS_AVAILABLE = True
except ImportError:
    admin_projects_router = None
    ADMIN_PROJECTS_AVAILABLE = False


def register_routes(api_router: APIRouter):
    """Register all route modules to the main API router"""
    # Initialize Rules of Origin with official data
    if RULES_OF_ORIGIN_DATA_LOADED:
        init_rules_data(CHAPTER_RULES, ORIGIN_TYPES)
        _logger.info("Rules of Origin data initialized successfully")

    # Health endpoints remain public (no auth required)
    api_router.include_router(health_router, tags=["Health"])

    # All other routers require a valid API key
    if NEWS_AVAILABLE:
        api_router.include_router(news_router, tags=["News"], dependencies=_auth)
    api_router.include_router(oec_router, tags=["OEC Trade"], dependencies=_auth)
    api_router.include_router(hs_codes_router, tags=["HS Codes"], dependencies=_auth)
    api_router.include_router(production_router, tags=["Production"], dependencies=_auth)
    api_router.include_router(logistics_router, tags=["Logistics"], dependencies=_auth)
    api_router.include_router(countries_router, tags=["Countries"], dependencies=_auth)
    api_router.include_router(tariffs_router, tags=["Tariffs"], dependencies=_auth)
    api_router.include_router(statistics_router, tags=["Statistics"], dependencies=_auth)
    api_router.include_router(etl_router, tags=["ETL Administration"], dependencies=_auth)
    api_router.include_router(substitution_router, tags=["Trade Substitution"], dependencies=_auth)
    if GEMINI_AVAILABLE:
        api_router.include_router(gemini_router, tags=["AI Analysis"], dependencies=_auth)
    api_router.include_router(rules_router, tags=["Rules of Origin"], dependencies=_auth)
    api_router.include_router(hs6_db_router, tags=["HS6 Database"], dependencies=_auth)
    api_router.include_router(authentic_tariffs_router, tags=["Authentic Tariffs"], dependencies=_auth)
    api_router.include_router(tariffs_calc_router, tags=["Tariff Calculations"], dependencies=_auth)
    if FAOSTAT_AVAILABLE:
        api_router.include_router(faostat_router, tags=["FAOSTAT Production 2024"], dependencies=_auth)
    api_router.include_router(calculator_router, tags=["Calculator"], dependencies=_auth)
    if TRADE_DATA_AVAILABLE:
        api_router.include_router(trade_data_router, tags=["Trade Data Sources"], dependencies=_auth)
    if EXPORT_ROUTER_AVAILABLE:
        api_router.include_router(export_router, tags=["Export"], dependencies=_auth)
    if CRAWL_AVAILABLE:
        api_router.include_router(crawl_router, tags=["Crawl Orchestration"], dependencies=_auth)
    if TARIFF_DATA_AVAILABLE:
        api_router.include_router(tariff_data_router, tags=["Tariff Data Collection"], dependencies=_auth)
    if REGULATORY_ENGINE_AVAILABLE:
        api_router.include_router(regulatory_engine_router, tags=["Regulatory Engine v3"], dependencies=_auth)
    if SEARCH_AVAILABLE:
        api_router.include_router(search_router, tags=["Text Search"], dependencies=_auth)
    if CACHE_ROUTER_AVAILABLE:
        api_router.include_router(cache_router, tags=["Cache Management"], dependencies=_auth)
    if DZA_CRAWLER_AVAILABLE:
        api_router.include_router(dza_crawler_router, tags=["DZA Crawler"], dependencies=_auth)
    if ENHANCED_CALCULATOR_AVAILABLE:
        api_router.include_router(enhanced_calculator_router, tags=["Enhanced Calculator v2"], dependencies=_auth)
    if NORTH_AFRICA_CRAWLERS_AVAILABLE:
        api_router.include_router(north_africa_crawlers_router, tags=["North Africa Crawlers"], dependencies=_auth)
    if CEMAC_CRAWLERS_AVAILABLE:
        api_router.include_router(cemac_crawlers_router, tags=["CEMAC Crawlers"], dependencies=_auth)
    if REGIONAL_DATA_AVAILABLE:
        api_router.include_router(regional_data_router, tags=["Regional Data Inventory"], dependencies=_auth)
    if REGIONAL_CALCULATOR_AVAILABLE:
        api_router.include_router(regional_calculator_router, tags=["Regional Calculator"], dependencies=_auth)
    if INVESTMENT_INTELLIGENCE_AVAILABLE:
        api_router.include_router(investment_intelligence_router, tags=["Investment Intelligence"], dependencies=_auth)
    if UMA_REGIONS_AVAILABLE:
        api_router.include_router(uma_regions_router, tags=["UMA North Africa Regions"], dependencies=_auth)
    if API_V2_AVAILABLE:
        api_router.include_router(api_v2_router, tags=["API v2"], dependencies=_auth)
    if AI_INTELLIGENCE_AVAILABLE:
        api_router.include_router(ai_intelligence_router, tags=["AI Intelligence"], dependencies=_auth)
    if ENHANCED_SEARCH_AVAILABLE:
        api_router.include_router(enhanced_search_router, tags=["Enhanced Search"], dependencies=_auth)
    if SADC_INTELLIGENCE_AVAILABLE:
        api_router.include_router(sadc_intelligence_router, tags=["SADC Intelligence"], dependencies=_auth)
    if REGIONAL_ANALYTICS_AVAILABLE:
        api_router.include_router(regional_analytics_router, tags=["Regional Analytics Dashboard"], dependencies=_auth)
    if PERFORMANCE_AVAILABLE:
        api_router.include_router(performance_router, tags=["Performance Monitoring"], dependencies=_auth)
    if BANKING_AVAILABLE:
        api_router.include_router(banking_router, tags=["Banking System"], dependencies=_auth)
    if POSTGRES_TARIFFS_AVAILABLE:
        api_router.include_router(postgres_tariffs_router, tags=["PostgreSQL Tariffs"], dependencies=_auth)
    if GRAPHQL_AVAILABLE:
        api_router.include_router(graphql_router, tags=["GraphQL"], dependencies=_auth)
    if WEBSOCKET_AVAILABLE:
        api_router.include_router(websocket_router, tags=["WebSocket Real-time"], dependencies=_auth)
    if MOBILE_AVAILABLE:
        api_router.include_router(mobile_router, tags=["Mobile API"], dependencies=_auth)
    if CURRENCIES_AVAILABLE:
        api_router.include_router(currencies_router, tags=["Currencies"], dependencies=_auth)
    if EXCHANGE_RATES_AVAILABLE:
        api_router.include_router(exchange_rates_router, tags=["Exchange Rates"], dependencies=_auth)
<<<<<<< Updated upstream
    # Admin endpoints — uses its own require_admin dependency at route level
    if ADMIN_PROJECTS_AVAILABLE:
        api_router.include_router(admin_projects_router, tags=["Admin - Structuring Projects"])
=======
    if DISMANTLEMENT_AVAILABLE:
        api_router.include_router(dismantlement_router, tags=["ZLECAf Dismantlement Schedule"], dependencies=_auth)
>>>>>>> Stashed changes
