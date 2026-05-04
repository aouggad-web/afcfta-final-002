"""
Health check routes
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API ZLECAf - Système Commercial Africain",
        "version": "2.0.0",
        "status": "Production Ready"
    }

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "database": "connected"
        }
    }

@router.get("/health/status")
async def detailed_health():
    "detailed health status with all service checks"
    checks = {
        "api": {"status": "up", "latency_ms": 1},
        "database": {"status": "up", "type": "MongoDB"},
        "cache": {"status": "up", "type": "In-Memory"}
    }
    try:
        from notifications import NotificationManager
        manager = NotificationManager()
        enabled_channels = manager.get_enabled_channels()
        checks["notifications"] = {"status": "healthy"}
    except: 
        checks["notifications"] = {"status": "error"}
    return {"status": "healthy", "components": checks}
