"""
FastAPI Application Server — Montage et démarrage

Charge tous les modules de route, établit la connexion à MongoDB,
configure CORS, et lance le serveur uvicorn.

Démarrage :
  cd backend && python -m uvicorn server:app --reload --port 8000
"""

import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Charge les variables d'environnement depuis backend/.env
load_dotenv()

# Initialize database on startup, cleanup on shutdown
async def init_database():
    """Initialize MongoDB connection if available.

    The route handlers (user_auth, billing, contact) call `await db.<coll>...`,
    so the injected database must be an async Motor database, not a synchronous
    pymongo one.
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
        # Test connection (Motor's command is awaitable)
        await client.admin.command("ping")
        db = client.get_database(os.getenv("MONGO_DB", "afcfta"))
        return db, client
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        return None, None

async def shutdown_database(client):
    """Close MongoDB connection"""
    if client:
        try:
            client.close()
        except Exception as e:
            print(f"Error closing MongoDB: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    db, mongo_client = await init_database()

    # Inject database into routers that need it
    if db:
        from routes import user_auth, billing, contact
        user_auth.set_database(db)
        billing.set_database(db)
        contact.set_database(db)
        print("✅ Database initialized and injected into routers")
    else:
        print("⚠️  Database not available; auth/billing/contact endpoints will return 503")

    yield

    # Shutdown: Close database
    await shutdown_database(mongo_client)

# Crée l'app FastAPI avec lifespan
app = FastAPI(
    title="AFCFTA Trade & Production Platform",
    description="API pour la plateforme commerciale africaine et les statistiques de production",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS — accès depuis le frontend (localhost:5000 en dev)
cors_config = {
    "allow_origins": [
        "http://localhost:5000",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# Check pour APP_ENV (utilisé par le système de déploiement)
if os.getenv("APP_ENV") == "production":
    # En production, limiter à l'origine du domaine
    cors_config["allow_origins"] = [os.getenv("FRONTEND_URL", "https://example.com")]

app.add_middleware(CORSMiddleware, **cors_config)

# Production router (auto-contained, no dependencies)
from routes import production
app.include_router(production.router)

# Legacy routers mounted under /api prefix
# These routers declare prefixes like /auth, /billing, etc.
# Mounting them under /api means they become /api/auth, /api/billing, etc.
from routes import (
    billing,
    contact,
    insurance,
    regulatory_compliance,
    regulatory_master_registry,
    regulatory_qa,
    reports,
    strategic_intelligence,
    user_auth,
    banking_enhancements,
)

api_router = FastAPI()
api_router.include_router(user_auth.router)
api_router.include_router(billing.router)
api_router.include_router(contact.router)
api_router.include_router(insurance.router)
api_router.include_router(regulatory_compliance.router)
api_router.include_router(regulatory_master_registry.router)
api_router.include_router(regulatory_qa.router)
api_router.include_router(reports.router)
api_router.include_router(strategic_intelligence.router)
api_router.include_router(banking_enhancements.router)

app.mount("/api", api_router)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint de vérification de l'état du serveur"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Endpoint racine — docs disponibles sur /docs"""
    return {
        "name": "AFCFTA Trade & Production API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
