"""
Trade Data API Routes
Endpoints for accessing WTO and smart data source selection

Audit D2 (16/11/2026) : le client OMC est synchrone (30 s de délai, jusqu'à
5 essais avec attentes, `time.sleep`). Appelé depuis ces routes asynchrones,
il figeait la boucle d'événements jusqu'à environ trois minutes par requête,
sans compte. Les appels passent désormais par un thread, au plus deux à la
fois (au-delà : 503 immédiat, pour ne pas épuiser les threads qui servent
aussi les fichiers), et les codes reçus sont validés avant tout appel.
"""

import asyncio
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.concurrency import run_in_threadpool
from services.data_source_selector import data_source_selector
from services.wto_service import wto_service

router = APIRouter(tags=["Trade Data"])

_ISO3 = r"^[A-Za-z]{3}$"
_CODE_SH = r"^\d{2,10}$"
_MAX_PAYS_COMPARES = 10
_APPELS_OMC = asyncio.Semaphore(2)


async def _appel_omc(fonction, *args):
    """Exécute un appel au client OMC hors de la boucle, sans en dépasser deux."""
    if _APPELS_OMC.locked():
        raise HTTPException(
            status_code=503,
            detail="Service de données OMC occupé, réessayez dans un instant.",
        )
    async with _APPELS_OMC:
        return await run_in_threadpool(fonction, *args)


@router.get("/trade-data/latest")
async def get_latest_trade_data(
    reporter: str = Query(..., pattern=_ISO3, description="Reporter country ISO3 code"),
    partner: str = Query(..., pattern=_ISO3, description="Partner country ISO3 code"),
    hs_code: Optional[str] = Query(None, pattern=_CODE_SH, description="HS product code"),
):
    """
    Get the latest available trade data using smart source selection

    This endpoint automatically selects the best data source based on:
    - Data freshness
    - API availability
    - Coverage
    """
    result = await _appel_omc(data_source_selector.get_latest_trade_data, reporter, partner, hs_code)

    if not result.get("data"):
        raise HTTPException(status_code=404, detail="No trade data available from any source")

    return result


@router.get("/trade-data/compare-sources")
async def compare_data_sources(
    countries: List[str] = Query(
        ..., max_length=_MAX_PAYS_COMPARES, description="List of ISO3 country codes"
    )
):
    """
    Compare all data sources to determine which has the most recent data

    This is useful for understanding which data source to prioritize
    """
    if any(not re.match(_ISO3, code) for code in countries):
        raise HTTPException(status_code=422, detail="Codes pays ISO3 attendus (trois lettres).")
    comparison = await _appel_omc(data_source_selector.compare_data_sources, countries)
    return comparison


@router.get("/trade-data/wto/{reporter}/{partner}")
async def get_wto_data(
    reporter: str = Path(..., pattern=_ISO3),
    partner: str = Path(..., pattern=_ISO3),
    product_code: Optional[str] = Query(None, pattern=_CODE_SH),
):
    """
    Get WTO tariff and trade data directly
    """
    data = await _appel_omc(wto_service.get_tariff_data, reporter, partner, product_code)

    if not data:
        raise HTTPException(status_code=404, detail="No WTO data available")

    return data
