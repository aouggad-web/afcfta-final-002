"""
FastAPI Application Server — Montage et démarrage

Charge tous les modules de route, établit la connexion à MongoDB,
configure CORS, et lance le serveur uvicorn.

Démarrage :
  cd backend && python -m uvicorn server:app --reload --port 8000
"""

import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Charge les variables d'environnement depuis backend/.env
load_dotenv()

# Crée l'app FastAPI
app = FastAPI(
    title="AFCFTA Trade & Production Platform",
    description="API pour la plateforme commerciale africaine et les statistiques de production",
    version="1.0.0",
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
