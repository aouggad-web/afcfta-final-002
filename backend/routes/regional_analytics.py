"""
AfCFTA Platform - Regional Analytics API Routes
================================================
Comparative analysis dashboard endpoints for all African regional blocs.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from auth import require_auth
from entitlement_guard import check_export_format, get_optional_subscriber
from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regional-analytics", tags=["Regional Analytics Dashboard"])


# Les vues du tableau de bord (blocs, comparaison, carte de chaleur, corridors,
# graphiques) n'avaient aucun appelant : retirées le 17/11/2026 (audit D8). Seul
# l'export reste servi.


async def _format_d_export(
    format: str = Query("excel", description="Output format: excel | pdf | json"),
    user: Optional[dict] = Depends(get_optional_subscriber),
    key_doc: dict = Depends(require_auth),
) -> str:
    """Format demandé, contrôlé contre la formule (audit E1) : le pdf est
    accordé à toutes les formules, l'excel au seul compte admin (décision du
    06/11/2026), json reste libre. Le handler reçoit le format d'ici, sans
    second paramètre dont le défaut pourrait diverger."""
    if format in ("excel", "pdf"):
        check_export_format(format, user, key_doc)
    return format


@router.get("/export")
async def export_analysis(
    format: str = Depends(_format_d_export),
    blocs: Optional[str] = Query(None),
    sector: str = Query("general"),
):
    """
    Export regional analysis report.
    Returns file download for Excel/PDF or JSON data.
    """
    from fastapi.responses import Response
    from intelligence.ai_engine.investment_scoring import (
        COUNTRY_INDICATORS,
        SECTOR_MULTIPLIERS,
        get_intelligence_engine,
    )
    from search.enhanced_search import get_search_engine

    # Le secteur est recopié dans chaque ligne du fichier : une valeur libre y
    # glisserait une formule de tableur (audit M5).
    secteurs = ["general", *SECTOR_MULTIPLIERS]
    if sector not in secteurs:
        raise HTTPException(
            status_code=422,
            detail=f"Secteur inconnu. Valeurs admises : {', '.join(secteurs)}.",
        )

    engine = get_intelligence_engine()
    countries = list(COUNTRY_INDICATORS.keys())

    opportunities = []
    for country in countries:
        score = engine.calculate_investment_score(country, sector)
        opportunities.append(
            {
                "country": country,
                "sector": sector,
                "investment_score": score.overall_score,
                "grade": score.grade,
                "recommendation": score.recommendation_strength,
            }
        )

    analysis_data = {
        "opportunities": sorted(opportunities, key=lambda x: x["investment_score"], reverse=True),
        "total_count": len(opportunities),
        "sector": sector,
    }

    from dashboard.export_services import get_export_service

    exporter = get_export_service()

    if format == "excel":
        data = exporter.export_investment_analysis_excel(analysis_data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    elif format == "pdf":
        data = exporter.export_investment_analysis_pdf(analysis_data)
        media_type = "application/pdf"
        ext = "pdf"
    else:
        import json as _json

        data = _json.dumps(analysis_data, default=str, indent=2).encode()
        media_type = "application/json"
        ext = "json"

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=afcfta_analysis.{ext}"},
    )
