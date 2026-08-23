"""
ZLECAf Trade Calculator - Main Server
Refactored: Routes extracted to /routes/ modules

Version: 3.0.0
"""

import os
import sys
from pathlib import Path

# Ensure the backend directory is on sys.path so that subpackages
# (intelligence, performance, search, api, dashboard) can import each other.
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Ensure the repository root is on sys.path as well: backend services import the
# top-level ``engine`` package (legal overrides, customs calculation), which is a
# sibling of ``backend/`` and therefore invisible when the server is started with
# ``cd backend && uvicorn server:app`` (start.sh, scripts/start.sh, .replit).
#
# Appended rather than inserted, deliberately. Position is irrelevant to
# resolving ``engine``: neither ``engine/`` nor ``backend/engine/`` carries an
# ``__init__.py``, so both are PEP 420 namespace portions that merge into one
# ``engine.__path__`` whatever their order (and a regular ``engine`` package
# installed in site-packages would win over both from any position, so moving
# this entry earlier would not guard against that either). Appending does keep
# the repository root behind site-packages, which matters: the root exposes
# generically named directories (tests, data, docs, scripts, reports, ...) that
# would shadow installed packages if they came first.
_repo_root = _backend_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(1, str(_repo_root))

import logging
import logging.config

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

# ── Load .env BEFORE importing modules that read env vars at import time
# (auth.py reads SECRET_KEY in module scope to build the HMAC secret).
_ROOT_DIR_FOR_DOTENV = Path(__file__).parent
load_dotenv(_ROOT_DIR_FOR_DOTENV / ".env")

# Configure structured logging
logging.config.dictConfig(
    {
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
    }
)

logger = logging.getLogger(__name__)

import auth as _auth_module
from cors_config import resolve_cors_origin_regex, resolve_cors_origins

# Import routes module for modular endpoint registration
from routes import register_routes
from routes.admin_keys import router as admin_keys_router
from entitlement_guard import set_database as set_entitlement_guard_db
from routes.calculator import set_database as set_calculator_db
from routes.contact import set_database as set_contact_db
from routes.substitution import register_routes as register_substitution_routes
from routes.user_auth import set_database as set_user_auth_db

# Billing en défaut mou UNIQUEMENT quand la dépendance externe `stripe` manque
# à l'installation. Une régression interne à billing.py (import cassé, cycle,
# `cannot import name ...`) doit remonter — sinon le paiement resterait
# silencieusement désactivé malgré un environnement correct.
try:
    from routes.billing import set_database as set_billing_db
except ModuleNotFoundError as e:
    if e.name != "stripe":
        raise
    set_billing_db = None
from services.crawled_data_service import crawled_service
from services.tariff_data_service import tariff_service
from services.user_auth_service import hash_password, verify_password

try:
    from notifications import NotificationManager
except ImportError:
    NotificationManager = None

# =============================================================================
# CONFIGURATION
# =============================================================================

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB Connection
mongo_url = os.environ.get("MONGO_URL", "")
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
        db = client[os.environ.get("DB_NAME", "afcfta")]
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
        logger.info(
            f"Notification manager initialized with channels: {notification_manager.get_enabled_channels()}"
        )
    except Exception as e:
        logger.warning(f"Notification manager initialization failed: {e}")

# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

_app_env = os.environ.get("APP_ENV", "development")
_docs_url = None if _app_env == "production" else "/docs"
_redoc_url = None if _app_env == "production" else "/redoc"
_openapi_url = None if _app_env == "production" else "/openapi.json"

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
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
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

# CORS middleware — origins controlled via ALLOWED_ORIGINS env variable, plus
# a regex covering Emergent preview subdomains (see cors_config.py for why).
_cors_origins = resolve_cors_origins(os.environ)
_allow_origin_regex = resolve_cors_origin_regex(os.environ)

# Security middlewares (optional)
try:
    from middlewares import CSRFMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CSRFMiddleware,
        exempt_paths=[
            "/api/docs",
            "/api/openapi.json",
            "/api/redoc",
            "/api/health",
            "/api/",
            "/api/tariff-data/collect",
            "/api/crawl",
            "/api/crawl/start",
            # Webhooks paiement : appels serveur-à-serveur signés, sans cookie
            # ni jeton CSRF — authentifiés par leur propre signature.
            "/api/billing/webhook",
            "/api/billing/chargily/webhook",
        ],
    )
    # Quotas et liste d'exemptions : voir backend/middlewares/rate_limiter.py.
    # Pilotables par RATE_LIMIT_* (dont RATE_LIMIT_ENABLED pour couper vite).
    app.add_middleware(RateLimitMiddleware)
    logger.info("Security middlewares loaded: CSP headers, CSRF protection, Rate limiting")
except ImportError as e:
    logger.warning(f"Security middlewares not loaded: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Requested-With"],
    expose_headers=["X-CSRF-Token"],
)

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
        await customs_data.create_indexes(
            [
                IndexModel([("country_code", ASCENDING)]),
                IndexModel([("imported_at", DESCENDING)]),
                IndexModel([("country_code", ASCENDING), ("imported_at", DESCENDING)]),
            ]
        )
        # tariff_lines indexes (if collection exists)
        tariff_lines = db["tariff_lines"]
        await tariff_lines.create_indexes(
            [
                IndexModel([("country_code", ASCENDING)]),
                IndexModel([("hs_code", ASCENDING)]),
                IndexModel([("country_code", ASCENDING), ("hs_code", ASCENDING)]),
            ]
        )
        # api_keys indexes (auth system)
        api_keys = db["api_keys"]
        await api_keys.create_indexes(
            [
                IndexModel([("key_hash", ASCENDING)], unique=True),
                IndexModel([("active", ASCENDING), ("tier", ASCENDING)]),
            ]
        )
        # SaaS user accounts + login brute-force tracking
        await db["users"].create_indexes([IndexModel([("email", ASCENDING)], unique=True)])
        await db["login_attempts"].create_indexes(
            [IndexModel([("identifier", ASCENDING)], unique=True)]
        )
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"MongoDB index creation skipped: {e}")


async def _seed_admin_account():
    """Create (or refresh) the SaaS admin account from .env credentials."""
    if db is None:
        return
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    # /api/auth/login always lowercases the submitted email before querying;
    # normalize the same way here so a stray uppercase letter or surrounding
    # whitespace in ADMIN_EMAIL doesn't seed an account login can never find.
    admin_email = admin_email.strip().lower()
    try:
        from datetime import datetime, timezone

        existing = await db["users"].find_one({"email": admin_email})
        if existing is None:
            await db["users"].insert_one(
                {
                    "name": "Admin",
                    "email": admin_email,
                    "password_hash": hash_password(admin_password),
                    "role": "admin",
                    "created_at": datetime.now(timezone.utc),
                }
            )
            logger.info(f"Seeded admin account: {admin_email}")
        elif not verify_password(admin_password, existing.get("password_hash", "")):
            await db["users"].update_one(
                {"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}}
            )
            logger.info(f"Admin password re-synced from .env: {admin_email}")
    except Exception as e:
        logger.warning(f"Admin account seeding skipped: {e}")


@app.on_event("startup")
async def startup_load_tariff_data():
    """Load collected tariff data on startup for the calculator"""

    # Set up database indexes for performance
    await _setup_database_indexes()

    # Wire database into auth and calculator
    _auth_module.set_database(db)
    set_user_auth_db(db)
    set_contact_db(db)
    set_entitlement_guard_db(db)
    if set_billing_db is not None:
        set_billing_db(db)
    await _seed_admin_account()
    set_calculator_db(db)

    # Idempotence des webhooks Stripe : un event rejoué ne doit être traité
    # qu'une fois (Stripe garantit une livraison at-least-once).
    if db is not None:
        try:
            from pymongo import ASCENDING as _ASCENDING

            await db.usage_counters.create_index(
                [
                    ("user_id", _ASCENDING),
                    ("counter_id", _ASCENDING),
                    ("period_key", _ASCENDING),
                ],
                unique=True,
            )
        except Exception as e:
            logger.error(
                "Index unique usage_counters non créé (%s) — les quotas d'entitlement "
                "risquent d'être comptés en double sous forte concurrence.",
                e,
            )
        try:
            await db.payment_events.create_index("event_id", unique=True)
        except Exception as e:
            # Sans cet index, la déduplication des webhooks ne tient plus : les
            # rejeux Stripe/Chargily (livraison at-least-once) seraient traités
            # plusieurs fois — emails en double, états d'abonnement incohérents.
            # On ne bloque pas le démarrage, mais ceci doit remonter en alerte.
            logger.error(
                "CRITIQUE: index unique payment_events.event_id non créé (%s) — "
                "l'idempotence des webhooks de paiement n'est PLUS garantie. "
                "Créez l'index manuellement avant d'encaisser des paiements.",
                e,
            )

    # Load crawled data
    try:
        crawled_service.load()
        crawled_stats = crawled_service.get_stats()
        if crawled_stats["total_positions"] > 0:
            logger.info(
                f"Crawled data service ready: {crawled_stats['countries']} countries, "
                f"{crawled_stats['total_positions']:,} authentic positions"
            )
        else:
            logger.info("No crawled data found yet.")
    except Exception as e:
        logger.warning(f"Crawled data service startup: {e}")

    # Load tariff data
    try:
        tariff_service.load()
        stats = tariff_service.get_stats()
        if stats["countries"] > 0:
            logger.info(
                f"Tariff data service ready: {stats['countries']} countries, "
                f"{stats['total_positions']:,} positions loaded"
            )
        else:
            logger.info("No pre-collected tariff data found. Running initial collection...")
            from services.tariff_data_collector import TariffDataCollector

            collector = TariffDataCollector()
            result = collector.collect_all_countries()
            logger.info(
                f"Initial collection complete: {result['total_tariff_lines']} lines for {result['countries_processed']} countries"
            )
            tariff_service.load(force=True)
            stats = tariff_service.get_stats()
            logger.info(
                f"Tariff data service ready after collection: {stats['countries']} countries"
            )
    except Exception as e:
        logger.warning(f"Tariff data service startup: {e}. Calculator will use ETL fallback.")

    # Start the exchange rate scheduler (updates every 4 hours, first run immediate)
    try:
        from tasks.scheduler import start_scheduler

        start_scheduler(interval_hours=4)
        logger.info("Exchange rate scheduler started (interval=4h)")
    except Exception as e:
        logger.warning(f"Exchange rate scheduler startup failed: {e}")


# =============================================================================
# REGISTER ALL ROUTES
# =============================================================================

register_routes(api_router)
register_substitution_routes(api_router)
api_router.include_router(admin_keys_router, tags=["Admin: API Keys"])

# Include the router in the main app
app.include_router(api_router)

# =============================================================================
# STATIC FILES (Frontend)
# =============================================================================

from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

build_dir = Path(__file__).parent.parent / "frontend" / "build"
if build_dir.exists() and (build_dir / "index.html").exists():
    # Supporte les deux layouts de build : CRA (build/static) et Vite
    # (build/assets) — l'app est buildée par Vite (frontend/vite.config.js,
    # outDir "build"), le mode mono-processus (Replit, petit VPS) sert le
    # frontend directement depuis FastAPI.
    for _sub in ("static", "assets"):
        _subdir = build_dir / _sub
        if _subdir.exists():
            app.mount(f"/{_sub}", StaticFiles(directory=str(_subdir)), name=_sub)

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        file_path = (build_dir / full_path).resolve()
        if not str(file_path).startswith(str(build_dir.resolve())):
            return FileResponse(str(build_dir / "index.html"))
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(build_dir / "index.html"))
