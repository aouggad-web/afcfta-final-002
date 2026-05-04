"""
Currency API endpoints.

GET /api/currencies/list           – All African currencies (one per country)
GET /api/currencies/unique         – Unique ISO 4217 currency codes
GET /api/currencies/{code}/info    – Currency details by code or country code
GET /api/currencies/union/{name}   – Currencies by monetary union
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from currencies import (
    CurrencyInfo,
    get_by_code,
    get_by_country,
    get_by_forex_regulation,
    get_by_monetary_union,
    get_unique_currencies,
    list_currencies,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/currencies")


@router.get("/list", response_model=List[CurrencyInfo])
def list_all_currencies(
    forex_regulation: Optional[str] = Query(
        None, description="Filter by regulation level: strict | moderate | liberal"
    ),
):
    """Return currency information for all 54 African countries."""
    if forex_regulation:
        return get_by_forex_regulation(forex_regulation)
    return list_currencies()


@router.get("/unique", response_model=List[CurrencyInfo])
def list_unique_currencies():
    """Return one record per unique ISO 4217 currency code."""
    return get_unique_currencies()


@router.get("/union/{union_name}", response_model=List[CurrencyInfo])
def list_by_union(union_name: str):
    """Return currencies belonging to a given monetary union (e.g. UEMOA, CEMAC, CMA)."""
    results = get_by_monetary_union(union_name)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No currencies found for monetary union '{union_name}'",
        )
    return results


@router.get("/{code}/info", response_model=CurrencyInfo)
def get_currency_info(code: str):
    """Return currency details by ISO 4217 currency code or ISO 3166-1 country code.

    The endpoint first tries to match a 3-letter ISO 4217 currency code
    (e.g. NGN), then falls back to a 2-letter ISO 3166-1 country code (e.g. NG).
    """
    code = code.upper()
    # Try by ISO 4217 currency code (3 chars)
    if len(code) == 3:
        info = get_by_code(code)
        if info:
            return info
    # Try by country code (2 chars)
    if len(code) == 2:
        info = get_by_country(code)
        if info:
            return info
    # Try country code fallback for 3-char codes (shouldn't happen but be safe)
    info = get_by_country(code)
    if info:
        return info
    raise HTTPException(
        status_code=404,
        detail=f"No currency found for code '{code}'",
    )
