"""
ZLECAf Trade Calculator - Main Server
Refactored: Routes extracted to /routes/ modules

Version: 3.0.0
"""

import sys
import os
from pathlib import Path

# Ensure the backend directory is on sys.path so that subpackages
# (intelligence, performance, search, api, dashboard) can import each other.
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import logging.config

# Configure structured logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": os.environ.get("LOG_LEVEL", "INFO"),
        "handlers": ["console"],
    },
})

logger = logging.getLogger(__name__)

# Import routes module for modular endpoint registration
from routes import register_routes
from routes.substitution import register_routes as register_substitution_routes
from routes.calculator import set_database as set_calculator_db

from services.tariff_data_service import tariff_service
from services.crawled_data_service import crawled_service

try:
    from notifications import NotificationManager
except ImportError:
    NotificationManager = None

# =============================================================================
# CONFIGURATION
# =============================================================================

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Connection
mongo_url = os.environ.get('MONGO_URL', '')
db = None
client = None
if mongo_url:
    try:
        client = AsyncIOMotorClient(
            mongo_url,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=30000,
            connectTimeoutMS=20000,
            serverSelectionTimeoutMS=5000,
        )
        db = client[os.environ.get('DB_NAME', 'afcfta')]
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Running without database.")
        db = None
else:
    logger.warning("MONGO_URL not set. Running without database.")

# Notification Manager
notification_manager = None
if NotificationManager:
    try:
        notification_manager = NotificationManager()
        logger.info(f"Notification manager initialized with channels: {notification_manager.get_enabled_channels()}")
    except Exception as e:
        logger.warning(f"Notification manager initialization failed: {e}")

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(
    title="Système Commercial ZLECAf - API Complète",
    version="3.0.0",
    description=(
        "API complète pour le calculateur tarifaire ZLECAf avec données de 54 pays africains. "
        "Includes tariff calculation, HS code lookup, rules of origin, logistics data, "
        "and trade intelligence for the African Continental Free Trade Area."
    ),
    contact={
        "name": "AfCFTA Trade Calculator Support",
        "url": "https://afcfta.trade",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {"name": "Health", "description": "Health check and status endpoints"},
        {"name": "Calculator", "description": "Tariff calculation endpoints"},
        {"name": "HS Codes", "description": "Harmonized System code search and lookup"},
        {"name": "Countries", "description": "Country profiles and economic data"},
        {"name": "Tariffs", "description": "Tariff data for African countries"},
        {"name": "Rules of Origin", "description": "AfCFTA rules of origin"},
        {"name": "Logistics", "description": "Maritime, aviation, and land logistics"},
        {"name": "Statistics", "description": "Trade statistics and analytics"},
        {"name": "News", "description": "African trade news feed"},
    ],
)

# CORS middleware
_cors_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://afcfta.trade",
    "https://www.afcfta.trade",
]
_frontend_url = os.environ.get("FRONTEND_URL", "")
if _frontend_url:
    _cors_origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security middlewares (optional)
try:
    from middlewares import SecurityHeadersMiddleware, CSRFMiddleware, RateLimitMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFMiddleware, exempt_paths=[
        "/api/docs", "/api/openapi.json", "/api/redoc",
        "/api/health", "/api/",
        "/api/tariff-data/collect",
        "/api/crawl",
        "/api/crawl/start",
    ])
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120, burst_limit=20)
    logger.info("Security middlewares loaded: CSP headers, CSRF protection, Rate limiting")
except ImportError as e:
    logger.warning(f"Security middlewares not loaded: {e}")

# API Router with /api prefix
api_router = APIRouter(prefix="/api")

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Système Commercial ZLECAf API - Version 3.0"}

# =============================================================================
# EXTERNAL SERVICE INITIALIZATION
# =============================================================================

# Initialize export router DB
try:
    from routers.export_router import init_db as init_export_db
    init_export_db(db)
except ImportError:
    pass

# Initialize crawl orchestrator
try:
    from services.crawl_orchestrator import init_orchestrator
    init_orchestrator(
        db_client=client,
        notification_manager=notification_manager,
        max_concurrency=5,
    )
    logger.info("Crawl orchestrator initialized")
except Exception as e:
    logger.warning(f"Crawl orchestrator initialization failed: {e}")

# =============================================================================
# STARTUP EVENTS
# =============================================================================

async def _setup_database_indexes():
    """Create MongoDB indexes for optimal query performance."""
    if db is None:
        return
    try:
        from pymongo import ASCENDING, DESCENDING, IndexModel
        # customs_data collection indexes
        customs_data = db["customs_data"]
        await customs_data.create_indexes([
            IndexModel([("country_code", ASCENDING)]),
            IndexModel([("imported_at", DESCENDING)]),
            IndexModel([("country_code", ASCENDING), ("imported_at", DESCENDING)]),
        ])
        # tariff_lines indexes (if collection exists)
        tariff_lines = db["tariff_lines"]
        await tariff_lines.create_indexes([
            IndexModel([("country_code", ASCENDING)]),
            IndexModel([("hs_code", ASCENDING)]),
            IndexModel([("country_code", ASCENDING), ("hs_code", ASCENDING)]),
        ])
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"MongoDB index creation skipped: {e}")

@app.on_event("startup")
async def startup_load_tariff_data():
    """Load collected tariff data on startup for the calculator"""

    # Set up database indexes for performance
    await _setup_database_indexes()

    # Set database for calculator routes
    set_calculator_db(db)
    
    # Load crawled data
    try:
        crawled_service.load()
        crawled_stats = crawled_service.get_stats()
        if crawled_stats["total_positions"] > 0:
            logger.info(f"Crawled data service ready: {crawled_stats['countries']} countries, "
                        f"{crawled_stats['total_positions']:,} authentic positions")
        else:
            logger.info("No crawled data found yet.")
    except Exception as e:
        logger.warning(f"Crawled data service startup: {e}")

    # Load tariff data
    try:
        tariff_service.load()
        stats = tariff_service.get_stats()
        if stats["countries"] > 0:
            logger.info(f"Tariff data service ready: {stats['countries']} countries, "
                        f"{stats['total_positions']:,} positions loaded")
        else:
            logger.info("No pre-collected tariff data found. Running initial collection...")
            from services.tariff_data_collector import TariffDataCollector
            collector = TariffDataCollector()
            result = collector.collect_all_countries()
            logger.info(f"Initial collection complete: {result['total_tariff_lines']} lines for {result['countries_processed']} countries")
            tariff_service.load(force=True)
            stats = tariff_service.get_stats()
            logger.info(f"Tariff data service ready after collection: {stats['countries']} countries")
    except Exception as e:
        logger.warning(f"Tariff data service startup: {e}. Calculator will use ETL fallback.")

# =============================================================================
# REGISTER ALL ROUTES
# =============================================================================

register_routes(api_router)
register_substitution_routes(api_router)

# Include the router in the main app
app.include_router(api_router)

# =============================================================================
# STATIC FILES (Frontend)
# =============================================================================

from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

build_dir = Path(__file__).parent.parent / "frontend" / "build"
if build_dir.exists() and (build_dir / "static").exists():
    app.mount("/static", StaticFiles(directory=str(build_dir / "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        file_path = build_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(build_dir / "index.html"))
