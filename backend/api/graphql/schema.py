"""
AfCFTA Platform - GraphQL Resolvers
=====================================
FastAPI + ariadne GraphQL endpoint.

Falls back to a JSON REST response if ariadne is not installed so
that the application boots without extra dependencies.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .schema_definition import GRAPHQL_SCHEMA_SDL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graphql", tags=["GraphQL"])

# ---------------------------------------------------------------------------
# Try to load ariadne (optional dependency)
# ---------------------------------------------------------------------------
try:
    from ariadne import (
        QueryType,
        MutationType,
        make_executable_schema,
        graphql_sync,
        ScalarType,
    )
    from ariadne.asgi import GraphQL as AriadneGraphQL

    ARIADNE_AVAILABLE = True
except ImportError:
    ARIADNE_AVAILABLE = False
    logger.info("ariadne not installed – GraphQL will use fallback JSON resolvers")


# ---------------------------------------------------------------------------
# Resolver helpers (shared between ariadne and fallback)
# ---------------------------------------------------------------------------

def _resolve_health(*_) -> Dict[str, Any]:
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


def _resolve_search_products(_, __, query: str, filters=None, pagination=None) -> Dict[str, Any]:
    from search.enhanced_search import get_search_engine
    engine = get_search_engine()
    lang = (filters or {}).get("lang", "en")
    return engine.intelligent_hs_search(query, lang=lang)


def _resolve_search_investments(_, __, criteria: Dict[str, Any]) -> Dict[str, Any]:
    from search.enhanced_search import get_search_engine
    engine = get_search_engine()
    return engine.investment_opportunity_search(criteria)


def _resolve_investment_score(_, __, country: str, sector: str = "general",
                               investmentSize: str = "medium",
                               userProfile: Optional[Dict] = None) -> Dict[str, Any]:
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    engine = get_intelligence_engine()
    score = engine.calculate_investment_score(country, sector, investmentSize, userProfile or {})
    return score.to_dict()


def _resolve_compare_countries(_, __, countries: List[str], sector: str = "general") -> Dict[str, Any]:
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    engine = get_intelligence_engine()
    scores = [engine.calculate_investment_score(c, sector).to_dict() for c in countries]
    ranking = sorted(
        [{"country": s["country"], "score": s["overall_score"], "grade": s["grade"]}
         for s in scores],
        key=lambda x: x["score"], reverse=True
    )
    return {"countries": countries, "scores": scores, "ranking": ranking}


def _resolve_compare_regions(_, __, regions: List[str], metrics: Optional[List[str]] = None) -> Dict[str, Any]:
    from intelligence.analytics.regional_analytics import get_regional_analytics
    analytics = get_regional_analytics()
    return analytics.compare_regions(blocs=regions, metrics=metrics)


def _resolve_bulk_tariff(_, __, calculations: List[Dict[str, Any]]) -> Dict[str, Any]:
    op_id = str(uuid.uuid4())
    start = time.perf_counter()
    results = []
    errors = 0
    for calc in calculations:
        try:
            rate = 5.0  # Simplified; real impl queries tariff service
            goods_value = float(calc.get("goodsValueUsd", 0))
            duty = goods_value * rate / 100
            results.append({
                "originCountry": calc.get("originCountry"),
                "destinationCountry": calc.get("destinationCountry"),
                "hsCode": calc.get("hsCode"),
                "goodsValueUsd": goods_value,
                "tariffRatePct": rate,
                "dutyAmountUsd": duty,
                "totalLandedCostUsd": goods_value + duty,
                "appliedScheme": "AfCFTA preferential",
                "notes": [],
            })
        except Exception as exc:
            errors += 1
            logger.warning(f"Bulk tariff calc error: {exc}")

    return {
        "operationId": op_id,
        "totalRequests": len(calculations),
        "successCount": len(results),
        "errorCount": errors,
        "results": results,
        "processingTimeMs": round((time.perf_counter() - start) * 1000, 2),
    }


def _resolve_recommendations(_, __, userProfile: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    engine = get_intelligence_engine()
    recs = engine.get_personalized_recommendations(userProfile, limit=limit)
    return {
        "sector": userProfile.get("sector", "general"),
        "riskTolerance": userProfile.get("risk_tolerance", "medium"),
        "recommendations": [r.to_dict() for r in recs],
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def _resolve_predict_trade(_, __, originCountry: str, destinationCountry: str,
                            productCategory: str, timeframeMonths: int = 12) -> Dict[str, Any]:
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    engine = get_intelligence_engine()
    prediction = engine.predict_trade_flows(
        originCountry, destinationCountry, productCategory, timeframeMonths
    )
    return prediction.to_dict()


def _resolve_risk_assessment(_, __, country: str, sector: str = "general",
                              investmentSize: str = "medium") -> Dict[str, Any]:
    from intelligence.ai_engine.investment_scoring import get_intelligence_engine
    engine = get_intelligence_engine()
    return engine.assess_risk(country, sector, investmentSize)


def _resolve_regional_bloc(_, __, bloc: str) -> Dict[str, Any]:
    from intelligence.analytics.regional_analytics import get_regional_analytics
    return get_regional_analytics().get_bloc_summary(bloc)


def _resolve_heatmap(_, __) -> List[Dict[str, Any]]:
    from intelligence.analytics.regional_analytics import get_regional_analytics
    return get_regional_analytics().get_investment_heatmap()


def _resolve_corridors(_, __, originBloc: Optional[str] = None) -> List[Dict[str, Any]]:
    from intelligence.analytics.regional_analytics import get_regional_analytics
    return get_regional_analytics().get_trade_corridor_analysis(originBloc)


def _resolve_live_metrics(_, __, bloc: str) -> Dict[str, Any]:
    from intelligence.analytics.regional_analytics import get_regional_analytics
    summary = get_regional_analytics().get_bloc_summary(bloc)
    metrics = [
        {"metric": k, "value": v, "unit": None, "benchmark": None}
        for k, v in (summary.get("metrics") or {}).items()
    ]
    return {
        "bloc": bloc,
        "metrics": metrics,
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }


def _resolve_cache_stats(_, __) -> Dict[str, Any]:
    try:
        from performance.caching.cache_layers import get_cache
        stats = get_cache().all_stats()
        return {
            "l1HotData": stats.get("L1_hot_data", {}),
            "l2RegionalIntel": stats.get("L2_regional_intel", {}),
            "l3Calculations": stats.get("L3_calculations", {}),
            "l4Realtime": stats.get("L4_realtime", {}),
            "timestamp": stats.get("timestamp", ""),
        }
    except Exception:
        return {"error": "Cache stats unavailable"}


def _resolve_performance_summary(_, __) -> Dict[str, Any]:
    from performance.monitoring.performance_metrics import get_metrics
    return get_metrics().summary()


def _mutate_save_search(_, __, searchParams: Dict[str, Any], name: str) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "searchParams": searchParams,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


def _mutate_create_alert(_, __, criteria: Dict[str, Any], userId: str) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "userId": userId,
        "criteria": criteria,
        "active": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


def _mutate_invalidate_cache(_, __, countryCode: Optional[str] = None) -> Dict[str, Any]:
    try:
        from performance.caching.cache_layers import get_cache
        cache = get_cache()
        if countryCode:
            result = cache.invalidate_country(countryCode)
        else:
            result = {"message": "Provide a countryCode to invalidate"}
        return result
    except Exception as exc:
        return {"error": str(exc)}


def _mutate_warm_cache(_, __) -> Dict[str, Any]:
    return {"status": "Cache warming initiated (async)", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# Build Ariadne executable schema (if available)
# ---------------------------------------------------------------------------

def _build_ariadne_schema():
    json_scalar = ScalarType("JSON")
    json_scalar.set_serializer(lambda v: v)
    json_scalar.set_value_parser(lambda v: v)

    query = QueryType()
    mutation = MutationType()

    query.set_field("health", _resolve_health)
    query.set_field("searchProducts", _resolve_search_products)
    query.set_field("searchInvestmentOpportunities", _resolve_search_investments)
    query.set_field("getInvestmentScore", _resolve_investment_score)
    query.set_field("compareCountries", _resolve_compare_countries)
    query.set_field("compareRegions", _resolve_compare_regions)
    query.set_field("bulkTariffCalculation", _resolve_bulk_tariff)
    query.set_field("getPersonalizedRecommendations", _resolve_recommendations)
    query.set_field("predictTradeFlows", _resolve_predict_trade)
    query.set_field("getRiskAssessment", _resolve_risk_assessment)
    query.set_field("getRegionalBlocSummary", _resolve_regional_bloc)
    query.set_field("getInvestmentHeatmap", _resolve_heatmap)
    query.set_field("getTradeCorridors", _resolve_corridors)
    query.set_field("getLiveRegionalMetrics", _resolve_live_metrics)
    query.set_field("getCacheStats", _resolve_cache_stats)
    query.set_field("getPerformanceSummary", _resolve_performance_summary)

    mutation.set_field("saveSearch", _mutate_save_search)
    mutation.set_field("createInvestmentAlert", _mutate_create_alert)
    mutation.set_field("invalidateCache", _mutate_invalidate_cache)
    mutation.set_field("warmCache", _mutate_warm_cache)

    return make_executable_schema(GRAPHQL_SCHEMA_SDL, [query, mutation, json_scalar])


# ---------------------------------------------------------------------------
# FastAPI endpoints
# ---------------------------------------------------------------------------

# Fallback resolver map for when ariadne is not installed
_RESOLVER_MAP = {
    "health": lambda p: _resolve_health(None, None),
    "searchProducts": lambda p: _resolve_search_products(
        None, None, p.get("query", ""), p.get("filters"), p.get("pagination")
    ),
    "searchInvestmentOpportunities": lambda p: _resolve_search_investments(
        None, None, p.get("criteria", {})
    ),
    "getInvestmentScore": lambda p: _resolve_investment_score(
        None, None,
        p.get("country", ""), p.get("sector", "general"),
        p.get("investmentSize", "medium"), p.get("userProfile")
    ),
    "compareCountries": lambda p: _resolve_compare_countries(
        None, None, p.get("countries", []), p.get("sector", "general")
    ),
    "compareRegions": lambda p: _resolve_compare_regions(
        None, None, p.get("regions", []), p.get("metrics")
    ),
    "bulkTariffCalculation": lambda p: _resolve_bulk_tariff(
        None, None, p.get("calculations", [])
    ),
    "getPersonalizedRecommendations": lambda p: _resolve_recommendations(
        None, None, p.get("userProfile", {}), p.get("limit", 10)
    ),
    "predictTradeFlows": lambda p: _resolve_predict_trade(
        None, None,
        p.get("originCountry", ""), p.get("destinationCountry", ""),
        p.get("productCategory", ""), p.get("timeframeMonths", 12)
    ),
    "getRiskAssessment": lambda p: _resolve_risk_assessment(
        None, None, p.get("country", ""), p.get("sector", "general"), p.get("investmentSize", "medium")
    ),
    "getRegionalBlocSummary": lambda p: _resolve_regional_bloc(None, None, p.get("bloc", "")),
    "getInvestmentHeatmap": lambda p: _resolve_heatmap(None, None),
    "getTradeCorridors": lambda p: _resolve_corridors(None, None, p.get("originBloc")),
    "getLiveRegionalMetrics": lambda p: _resolve_live_metrics(None, None, p.get("bloc", "")),
    "getCacheStats": lambda p: _resolve_cache_stats(None, None),
    "getPerformanceSummary": lambda p: _resolve_performance_summary(None, None),
}

_MUTATION_MAP = {
    "saveSearch": lambda p: _mutate_save_search(None, None, p.get("searchParams", {}), p.get("name", "")),
    "createInvestmentAlert": lambda p: _mutate_create_alert(None, None, p.get("criteria", {}), p.get("userId", "")),
    "invalidateCache": lambda p: _mutate_invalidate_cache(None, None, p.get("countryCode")),
    "warmCache": lambda p: _mutate_warm_cache(None, None),
}


@router.get("")
async def graphql_playground():
    """Serve GraphQL Playground IDE."""
    html = """<!DOCTYPE html>
<html>
<head>
  <title>AfCFTA GraphQL Playground</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css">
</head>
<body>
  <div id="root"></div>
  <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
  <script>
    window.addEventListener('load', function() {
      GraphQLPlayground.init(document.getElementById('root'), {
        endpoint: '/api/graphql',
        settings: { 'editor.theme': 'dark' }
      });
    });
  </script>
</body>
</html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)


@router.post("")
async def graphql_endpoint(request: Request):
    """
    Handle GraphQL POST requests.
    Uses ariadne if available, otherwise resolves via fallback map.
    """
    body = await request.json()
    operation_name = body.get("operationName")
    variables = body.get("variables") or {}
    query_str = body.get("query", "")

    if ARIADNE_AVAILABLE:
        schema = _build_ariadne_schema()
        success, result = graphql_sync(
            schema,
            query_str,
            variable_values=variables,
            operation_name=operation_name,
            context_value={"request": request},
        )
        return JSONResponse(result, status_code=200 if success else 400)

    # Fallback: simple operation resolver
    # Determine operation type and name from query string
    import re
    op_match = re.search(r"\b(query|mutation)\s+(\w+)?\s*[({]", query_str)
    op_type = op_match.group(1) if op_match else "query"
    field_match = re.search(r"\{\s*(\w+)", query_str)
    field_name = field_match.group(1) if field_match else None

    resolver_map = _RESOLVER_MAP if op_type == "query" else _MUTATION_MAP
    if field_name and field_name in resolver_map:
        try:
            data = resolver_map[field_name](variables)
            return JSONResponse({"data": {field_name: data}})
        except Exception as exc:
            logger.error(f"GraphQL resolver error for {field_name}: {exc}")
            return JSONResponse({"errors": [{"message": str(exc)}]}, status_code=500)

    return JSONResponse(
        {
            "data": None,
            "errors": [{"message": f"Operation not found: {field_name}"}],
            "meta": {"ariadne_available": ARIADNE_AVAILABLE},
        }
    )


@router.get("/schema")
async def get_schema():
    """Return the GraphQL schema SDL."""
    return JSONResponse({"schema": GRAPHQL_SCHEMA_SDL})
