"""
Exchange rate API endpoints.

GET  /api/exchange-rates/latest              – Current rates (USD base)
GET  /api/exchange-rates/african             – African currency rates only
GET  /api/exchange-rates/{base}/{target}     – Specific currency pair
GET  /api/exchange-rates/historical/{date}   – Historical rates for a date
GET  /api/exchange-rates/alerts              – Rate change alerts
POST /api/exchange-rates/convert             – Currency conversion
POST /api/exchange-rates/refresh             – Force refresh rates from providers
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from exchange_rates import ConversionRequest, ConversionResult, RateBundle, get_service
from exchange_rates.models import RateAlert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/exchange-rates")


def _bundle_to_dict(bundle: RateBundle) -> dict:
    return {
        "base": bundle.base,
        "timestamp": bundle.timestamp.isoformat(),
        "source": bundle.source,
        "rates": bundle.rates,
    }


@router.get("/latest")
def get_latest_rates(base: str = Query("USD", description="Base currency code (ISO 4217)")):
    """Return the latest exchange rates for a given base currency."""
    svc = get_service()
    bundle = svc.get_latest(base)
    if bundle is None:
        raise HTTPException(
            status_code=503,
            detail="Exchange rate data is currently unavailable. Please try again later.",
        )
    return _bundle_to_dict(bundle)


@router.get("/african")
def get_african_rates(base: str = Query("USD", description="Base currency code (ISO 4217)")):
    """Return only African currency exchange rates."""
    svc = get_service()
    rates = svc.get_african_rates(base)
    if not rates:
        raise HTTPException(
            status_code=503,
            detail="African exchange rate data is currently unavailable.",
        )
    bundle = svc.get_latest(base)
    return {
        "base": base.upper(),
        "timestamp": bundle.timestamp.isoformat() if bundle else datetime.now(timezone.utc).isoformat(),
        "source": bundle.source if bundle else "cache",
        "rates": rates,
    }


@router.get("/historical/{date}")
def get_historical_rates(
    date: str,
    base: str = Query("USD", description="Base currency code (ISO 4217)"),
):
    """Return historical exchange rates for a specific date (YYYY-MM-DD)."""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{date}'. Use YYYY-MM-DD.",
        )
    svc = get_service()
    bundle = svc.get_historical(date, base)
    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Historical rates for {date} (base={base.upper()}) not available.",
        )
    return _bundle_to_dict(bundle)


@router.get("/alerts")
def get_rate_alerts():
    """Return rate change alerts for movements above 5%."""
    svc = get_service()
    alerts = svc.get_alerts()
    return {
        "count": len(alerts),
        "threshold_percent": 5.0,
        "alerts": [a.model_dump() for a in alerts],
    }


@router.post("/convert", response_model=ConversionResult)
def convert_currency(request: ConversionRequest):
    """Convert an amount from one currency to another."""
    svc = get_service()
    result = svc.convert(request.from_currency, request.to_currency, request.amount)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Cannot convert {request.from_currency} → {request.to_currency}. "
                "Currency pair may not be supported or rates unavailable."
            ),
        )
    return result


@router.post("/refresh")
def refresh_rates(base: str = Query("USD", description="Base currency code (ISO 4217)")):
    """Manually trigger a rate refresh from the provider chain."""
    svc = get_service()
    bundle = svc.update_rates(base)
    if bundle is None:
        raise HTTPException(
            status_code=503,
            detail="Failed to refresh rates. All providers are currently unavailable.",
        )
    return {
        "status": "updated",
        "base": bundle.base,
        "timestamp": bundle.timestamp.isoformat(),
        "source": bundle.source,
        "pairs_fetched": len(bundle.rates),
    }


@router.get("/{base}/{target}")
def get_pair_rate(base: str, target: str):
    """Return the exchange rate for a specific currency pair."""
    svc = get_service()
    rate = svc.get_rate(base, target)
    if rate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange rate for {base.upper()}/{target.upper()} not available.",
        )
    return rate.model_dump()
