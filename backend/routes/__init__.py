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
from .rules_of_origin import router as rules_router
from .hs6_database import router as hs6_db_router
from .authentic_tariffs import router as authentic_tariffs_router
from .tariffs_calculation import router as tariffs_calc_router
from .faostat import router as faostat_router
from .calculator import router as calculator_router
try:
    from .gemini_analysis import router as gemini_router
    GEMINI_AVAILABLE = True
except ImportError:
    gemini_router = None
    GEMINI_AVAILABLE = False
GEMINI_AVAILABLE = True  # already imported above

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

try:
    from .regulatory_engine import router as regulatory_engine_router
    REGULATORY_ENGINE_AVAILABLE = True
except ImportError:
    REGULATORY_ENGINE_AVAILABLE = False

try:
    from .search import router as search_router
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

try:
    from .cache import router as cache_router
    CACHE_ROUTER_AVAILABLE = True
except ImportError:
    CACHE_ROUTER_AVAILABLE = False

try:
    from .dza_crawler import router as dza_crawler_router
    DZA_CRAWLER_AVAILABLE = True
except ImportError:
    DZA_CRAWLER_AVAILABLE = False

try:
    from .enhanced_calculator import router as enhanced_calculator_router
    ENHANCED_CALCULATOR_AVAILABLE = True
except ImportError:
    ENHANCED_CALCULATOR_AVAILABLE = False
    from .north_africa_crawlers import router as north_africa_crawlers_router
    NORTH_AFRICA_CRAWLERS_AVAILABLE = True
except ImportError:
    NORTH_AFRICA_CRAWLERS_AVAILABLE = False

try:
    from .cemac_crawlers import router as cemac_crawlers_router
    CEMAC_CRAWLERS_AVAILABLE = True
except ImportError:
    CEMAC_CRAWLERS_AVAILABLE = False

try:
    from .regional_data import router as regional_data_router
    REGIONAL_DATA_AVAILABLE = True
except ImportError:
    REGIONAL_DATA_AVAILABLE = False

try:
    from .regional_calculator import router as regional_calculator_router
    REGIONAL_CALCULATOR_AVAILABLE = True
except ImportError:
    REGIONAL_CALCULATOR_AVAILABLE = False

try:
    from .investment_intelligence import router as investment_intelligence_router
    INVESTMENT_INTELLIGENCE_AVAILABLE = True
except ImportError:
    INVESTMENT_INTELLIGENCE_AVAILABLE = False

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
    API_V2_AVAILABLE = False
    from .sadc_intelligence import router as sadc_intelligence_router
    SADC_INTELLIGENCE_AVAILABLE = True
except ImportError:
    SADC_INTELLIGENCE_AVAILABLE = False
    from .ai_intelligence import router as ai_intelligence_router
    AI_INTELLIGENCE_AVAILABLE = True
except ImportError:
    AI_INTELLIGENCE_AVAILABLE = False

try:
    from .regional_analytics import router as regional_analytics_router
    REGIONAL_ANALYTICS_AVAILABLE = True
except ImportError:
    REGIONAL_ANALYTICS_AVAILABLE = False

try:
    from .enhanced_search import router as enhanced_search_router
    ENHANCED_SEARCH_AVAILABLE = True
except ImportError:
    ENHANCED_SEARCH_AVAILABLE = False

try:
    from .performance import router as performance_router
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False

try:
    from api.graphql.schema import router as graphql_router
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False

try:
    from api.websocket.handlers import router as websocket_router
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

try:
    from api.mobile.lightweight_endpoints import router as mobile_router
    MOBILE_AVAILABLE = True
except ImportError:
    MOBILE_AVAILABLE = False


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
    if GEMINI_AVAILABLE:
        api_router.include_router(gemini_router, tags=["AI Analysis"])
    api_router.include_router(rules_router, tags=["Rules of Origin"])
    api_router.include_router(hs6_db_router, tags=["HS6 Database"])
    api_router.include_router(authentic_tariffs_router, tags=["Authentic Tariffs"])
    api_router.include_router(tariffs_calc_router, tags=["Tariff Calculations"])
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
    if API_V2_AVAILABLE:
        api_router.include_router(api_v2_router, tags=["API v2"])
    if AI_INTELLIGENCE_AVAILABLE:
        api_router.include_router(ai_intelligence_router, tags=["AI Intelligence"])
    if ENHANCED_SEARCH_AVAILABLE:
        api_router.include_router(enhanced_search_router, tags=["Enhanced Search"])
    if SADC_INTELLIGENCE_AVAILABLE:
        api_router.include_router(sadc_intelligence_router, tags=["SADC Intelligence"])
    if AI_INTELLIGENCE_AVAILABLE:
        api_router.include_router(ai_intelligence_router, tags=["AI Investment Intelligence"])
    if REGIONAL_ANALYTICS_AVAILABLE:
        api_router.include_router(regional_analytics_router, tags=["Regional Analytics Dashboard"])
    if ENHANCED_SEARCH_AVAILABLE:
        api_router.include_router(enhanced_search_router, tags=["Enhanced Search & Filtering"])
    if PERFORMANCE_AVAILABLE:
        api_router.include_router(performance_router, tags=["Performance Monitoring"])
    if GRAPHQL_AVAILABLE:
        api_router.include_router(graphql_router, tags=["GraphQL"])
    if WEBSOCKET_AVAILABLE:
        api_router.include_router(websocket_router, tags=["WebSocket Real-time"])
    if MOBILE_AVAILABLE:
        api_router.include_router(mobile_router, tags=["Mobile API"])
