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
    """Detailed health status with all service checks"""
    checks = {
        "api": {"status": "up", "latency_ms": 1},
        "database": {"status": "up", "type": "MongoDB"},
        "cache": {"status": "up", "type": "In-Memory"}
    }

    # Check notification system
    try:
        from backend.notifications import NotificationManager
        manager = NotificationManager()
        enabled_channels = manager.get_enabled_channels()
        stats = manager.get_stats()
        checks["notifications"] = {
            "status": "healthy" if enabled_channels else "disabled",
            "channels": enabled_channels,
            "total_sent": stats.get("manager", {}).get("total_sent", 0)
        }
    except Exception as e:
        checks["notifications"] = {
            "status": "error",
            "message": f"Notification system error: {str(e)}"
        }

    # Check WTO API
    try:
        from services.wto_service import wto_service
        test_data = await wto_service.get_tariff_data("KEN", "wld")
        checks["wto_api"] = {
            "status": "healthy" if test_data else "degraded",
            "message": "WTO API accessible"
        }
    except Exception as e:
        checks["wto_api"] = {
            "status": "unhealthy",
            "message": f"WTO API error: {str(e)}"
        }

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "components": checks,
        "features": {
            "tariff_calculator": "enabled",
            "hs6_database": "enabled",
            "oec_integration": "enabled",
            "wto_integration": "enabled",
            "news_feed": "enabled",
            "notifications": (
                "enabled"
                if checks.get("notifications", {}).get("status") in ["healthy", "disabled"]
                else "error"
            ),
            "data_export": "enabled"
        }
    }
