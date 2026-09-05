"""
FastAPI Application Server — Montage et démarrage

Charge tous les modules de route, établit la connexion à MongoDB,
configure CORS, et lance le serveur uvicorn.

Démarrage :
  cd backend && python -m uvicorn server:app --reload --port 8000
"""

import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure repo root is importable (for top-level packages like `engine`)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charge les variables d'environnement depuis backend/.env
load_dotenv()

# Initialize database on startup, cleanup on shutdown
async def init_database():
    """Initialize MongoDB connection if available"""
    try:
        from pymongo import MongoClient
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
        # Test connection
        client.admin.command('ping')
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
    if db is not None:
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

# All other routers (auth, billing, tariffs, countries, banking, etc.) are
# wired centrally in routes.register_routes — mounting them under /api means
# they become /api/auth, /api/billing, /api/tariffs, etc.
from routes import register_routes

api_router = FastAPI()
register_routes(api_router)

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
