"""
AfCFTA Platform - Regional Analytics API Routes
================================================
Comparative analysis dashboard endpoints for all African regional blocs.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regional-analytics", tags=["Regional Analytics Dashboard"])


def _analytics():
    from intelligence.analytics.regional_analytics import get_regional_analytics
    return get_regional_analytics()


@router.get("/blocs")
async def list_regional_blocs():
    """List all supported regional blocs with member countries."""
    from intelligence.analytics.regional_analytics import REGIONAL_BLOCS
    return {
        "blocs": [
            {
                "code": code,
                "full_name": info["full_name"],
                "member_count": len(info["countries"]),
                "headquarters": info["headquarters"],
                "established": info["established"],
            }
            for code, info in REGIONAL_BLOCS.items()
        ]
    }


@router.get("/blocs/{bloc}")
async def get_bloc_summary(bloc: str):
    """Get detailed summary for a specific regional bloc."""
    try:
        return _analytics().get_bloc_summary(bloc.upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/compare")
async def compare_regions(
    blocs: Optional[str] = Query(None, description="Comma-separated bloc codes (default: all)"),
    metrics: Optional[str] = Query(None, description="Comma-separated metrics"),
):
    """
    Compare multiple regional blocs across selected metrics.
    Returns ranked comparisons and best performer per metric.
    """
    try:
        bloc_list = [b.strip().upper() for b in blocs.split(",")] if blocs else None
        metric_list = [m.strip() for m in metrics.split(",")] if metrics else None
        return _analytics().compare_regions(blocs=bloc_list, metrics=metric_list)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/heatmap")
async def get_investment_heatmap():
    """
    Get investment opportunity heatmap data for all regional blocs.
    Returns tier-classified opportunities for choropleth visualization.
    """
    try:
        return {"heatmap": _analytics().get_investment_heatmap()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/corridors")
async def get_trade_corridors(
    origin_bloc: Optional[str] = Query(None, description="Filter by origin bloc"),
):
    """Get intra-African trade corridor analysis with growth rates and key products."""
    try:
        return {
            "corridors": _analytics().get_trade_corridor_analysis(
                origin_bloc=origin_bloc.upper() if origin_bloc else None
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/visualization/{chart_type}")
async def get_visualization_data(
    chart_type: str,
    countries: Optional[str] = Query(None, description="Comma-separated country codes (for radar chart)"),
    blocs: Optional[str] = Query(None, description="Comma-separated bloc codes (for bar chart)"),
    metric: str = Query("investment_score", description="Metric for bar chart"),
    sector: str = Query("general"),
    country: Optional[str] = Query(None, description="Country code (for line chart)"),
):
    """
    Get chart-ready visualization data.

    Supported chart types:
    - radar: Country multi-factor comparison
    - bar: Regional bloc metric comparison
    - heatmap: Country investment score heatmap
    - sankey: Trade corridor flow diagram
    - line: Country trend analysis
    """
    from dashboard.visualization_engine import get_visualization_engine
    viz = get_visualization_engine()

    try:
        if chart_type == "radar":
            country_list = [c.strip().upper() for c in (countries or "MAR,EGY,KEN").split(",")]
            return viz.radar_chart_data(country_list, sector=sector)
        elif chart_type == "bar":
            bloc_list = [b.strip().upper() for b in blocs.split(",")] if blocs else None
            return viz.bar_chart_data(blocs=bloc_list, metric=metric)
        elif chart_type == "heatmap":
            return viz.heatmap_data()
        elif chart_type == "sankey":
            return viz.sankey_data()
        elif chart_type == "line":
            return viz.line_chart_trend(
                country=(country or "MAR").upper(), metric=metric
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Visualization error for {chart_type}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/export")
async def export_analysis(
    format: str = Query("excel", description="Output format: excel | pdf | json"),
    blocs: Optional[str] = Query(None),
    sector: str = Query("general"),
):
    """
    Export regional analysis report.
    Returns file download for Excel/PDF or JSON data.
    """
    from fastapi.responses import Response
    from search.enhanced_search import get_search_engine
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine, COUNTRY_INDICATORS

    engine = get_intelligence_engine()
    countries = list(COUNTRY_INDICATORS.keys())

    opportunities = []
    for country in countries:
        score = engine.calculate_investment_score(country, sector)
        opportunities.append({
            "country": country,
            "sector": sector,
            "investment_score": score.overall_score,
            "grade": score.grade,
            "recommendation": score.recommendation_strength,
        })

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
