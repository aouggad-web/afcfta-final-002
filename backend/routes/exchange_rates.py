"""
Exchange rate API endpoints.

POST /api/exchange-rates/refresh             – Force refresh rates from providers (admin)

Les routes publiques de ce préfixe (taux du jour, paires, historique, alertes,
conversion) n'avaient aucun appelant : retirées le 17/11/2026 (audit D8, D3).
L'interface lit les taux par /api/banking/forex/*.
"""

from typing import Annotated

from auth import require_admin
from exchange_rates import get_service
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/exchange-rates")


@router.post("/refresh")
def refresh_rates(
    base: str = Query("USD", description="Base currency code (ISO 4217)"),
    key_doc: Annotated[dict, Depends(require_admin)] = None,
):
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
