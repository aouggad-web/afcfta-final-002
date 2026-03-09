"""
Enhanced HS Code Search API Routes.

Provides multi-strategy HS code search with exact, fuzzy, and semantic matching.

Endpoints:
  GET /api/enhanced-search/hs-codes?q=coffee  # Enhanced HS code search
"""

import logging
import unicodedata
from typing import Dict, List

from fastapi import APIRouter, Query

from etl.hs6_database import HS6_DATABASE
from etl.hs_codes_data import get_hs_chapters

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-search", tags=["Enhanced Search"])


# ==================== Normalisation helpers ====================

def _normalize(text: str) -> str:
    """Lower-case and strip Unicode combining marks (accents)."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


# ==================== Synonym / semantic keyword map ====================

# Maps search terms to semantically related keywords so that a query such as
# "coffee" also matches entries containing "cafe", "cafea", "coffea", etc.
_SEMANTIC_SYNONYMS: Dict[str, List[str]] = {
    "coffee": ["cafe", "cafea", "coffea", "arabica", "robusta", "espresso"],
    "cafe": ["coffee", "coffea", "arabica", "robusta"],
    "tea": ["the", "camellia", "herbal"],
    "the": ["tea", "camellia"],
    "cocoa": ["cacao", "chocolate", "theobroma"],
    "cacao": ["cocoa", "chocolate", "theobroma"],
    "chocolate": ["cacao", "cocoa"],
    "sugar": ["sucre", "saccharum", "glucose", "fructose"],
    "sucre": ["sugar", "saccharum"],
    "cotton": ["coton", "gossypium"],
    "coton": ["cotton", "gossypium"],
    "oil": ["huile", "petroleum", "crude"],
    "huile": ["oil", "vegetable"],
    "wood": ["bois", "timber", "lumber"],
    "bois": ["wood", "timber"],
    "fish": ["poisson", "seafood", "aquatic"],
    "poisson": ["fish", "seafood"],
    "meat": ["viande", "beef", "pork", "poultry"],
    "viande": ["meat", "beef"],
    "wheat": ["ble", "triticum", "flour"],
    "ble": ["wheat", "triticum"],
    "rice": ["riz", "paddy", "oryza"],
    "riz": ["rice", "paddy"],
    "maize": ["mais", "corn", "zea"],
    "mais": ["maize", "corn"],
    "corn": ["mais", "maize", "zea"],
    "cement": ["ciment", "clinker"],
    "ciment": ["cement", "clinker"],
    "iron": ["fer", "acier", "steel"],
    "steel": ["acier", "fer", "iron"],
    "acier": ["steel", "iron", "fer"],
    "gold": ["or", "aurum"],
    "or": ["gold", "aurum"],
    "copper": ["cuivre"],
    "cuivre": ["copper"],
    "aluminum": ["aluminium", "bauxite"],
    "aluminium": ["aluminum", "bauxite"],
    "leather": ["cuir", "hide", "skin"],
    "cuir": ["leather", "hide"],
    "tobacco": ["tabac", "nicotiana"],
    "tabac": ["tobacco", "nicotiana"],
    "rubber": ["caoutchouc", "hevea"],
    "caoutchouc": ["rubber", "hevea"],
    "plastic": ["plastique", "polymer"],
    "plastique": ["plastic", "polymer"],
    "chemical": ["chimique", "reagent"],
    "medicament": ["medicine", "pharmaceutical", "drug"],
    "medicine": ["medicament", "pharmaceutical", "drug"],
    "pharmaceutical": ["medicament", "medicine"],
    "vehicle": ["vehicule", "automobile", "car", "truck"],
    "vehicule": ["vehicle", "automobile"],
    "automobile": ["vehicle", "vehicule", "car"],
    "electric": ["electrique", "electronics"],
    "electrique": ["electric", "electronics"],
    "fertilizer": ["engrais", "fertilisant"],
    "engrais": ["fertilizer", "fertilisant"],
    "seed": ["graine", "semence"],
    "graine": ["seed", "semence"],
    "mineral": ["minerai", "ore"],
    "minerai": ["mineral", "ore"],
}


def _get_synonyms(query_norm: str) -> List[str]:
    """Return semantic synonyms for the normalised query term."""
    return [_normalize(s) for s in _SEMANTIC_SYNONYMS.get(query_norm, [])]


# ==================== Search strategies ====================

def _build_entry(code: str, data: dict, language: str, chapters: dict, match_type: str) -> dict:
    desc_key = f"description_{language}"
    chapter = code[:2]
    return {
        "code": code,
        "label": data.get(desc_key, data.get("description_fr", "")),
        "chapter": chapter,
        "chapter_name": chapters.get(chapter, {}).get(language, ""),
        "category": data.get("category", ""),
        "sensitivity": data.get("sensitivity", "normal"),
        "match_type": match_type,
    }


def _exact_matches(query_norm: str, language: str, chapters: dict, limit: int) -> List[dict]:
    """Entries whose description or code starts with / is equal to the query."""
    results = []
    for code, data in HS6_DATABASE.items():
        if len(results) >= limit:
            break
        desc_fr = _normalize(data.get("description_fr", ""))
        desc_en = _normalize(data.get("description_en", ""))
        # Exact code match or description starts with query
        if code == query_norm or desc_fr.startswith(query_norm) or desc_en.startswith(query_norm):
            results.append(_build_entry(code, data, language, chapters, "exact"))
    return results


def _fuzzy_matches(query_norm: str, language: str, chapters: dict, limit: int, exact_codes: set) -> List[dict]:
    """Entries whose description contains the query as a substring (not already exact)."""
    results = []
    for code, data in HS6_DATABASE.items():
        if len(results) >= limit:
            break
        if code in exact_codes:
            continue
        desc_fr = _normalize(data.get("description_fr", ""))
        desc_en = _normalize(data.get("description_en", ""))
        category = _normalize(data.get("category", ""))
        if query_norm in desc_fr or query_norm in desc_en or query_norm in category:
            results.append(_build_entry(code, data, language, chapters, "fuzzy"))
    return results


def _semantic_matches(
    query_norm: str,
    language: str,
    chapters: dict,
    limit: int,
    seen_codes: set,
) -> List[dict]:
    """Entries that match any semantic synonym of the query."""
    synonyms = _get_synonyms(query_norm)
    if not synonyms:
        return []

    results = []
    for code, data in HS6_DATABASE.items():
        if len(results) >= limit:
            break
        if code in seen_codes:
            continue
        desc_fr = _normalize(data.get("description_fr", ""))
        desc_en = _normalize(data.get("description_en", ""))
        category = _normalize(data.get("category", ""))
        combined = f"{desc_fr} {desc_en} {category}"
        if any(syn in combined for syn in synonyms):
            results.append(_build_entry(code, data, language, chapters, "semantic"))
    return results


# ==================== Endpoints ====================

@router.get("/hs-codes")
async def enhanced_hs_code_search(
    q: str = Query(..., min_length=2, description="Search query (product name or HS code)"),
    language: str = Query("en", description="Language for labels: en or fr"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per match type"),
):
    """
    Enhanced HS code search combining three complementary strategies:

    - **exact_matches**: Codes or descriptions that start with / equal the query.
    - **fuzzy_matches**: Descriptions containing the query as a substring.
    - **semantic_matches**: Entries matching semantic synonyms of the query
      (e.g. "coffee" → also finds "cafe", "arabica", "coffea").

    All searches are accent-insensitive and case-insensitive.

    Parameters:
    - q: Search query (e.g. "coffee", "090111", "wheat")
    - language: en (default) or fr
    - limit: Maximum results per category (1–100, default 20)
    """
    query_norm = _normalize(q.strip())
    chapters = get_hs_chapters()

    exact = _exact_matches(query_norm, language, chapters, limit)
    exact_codes = {e["code"] for e in exact}

    fuzzy = _fuzzy_matches(query_norm, language, chapters, limit, exact_codes)
    fuzzy_codes = exact_codes | {f["code"] for f in fuzzy}

    semantic = _semantic_matches(query_norm, language, chapters, limit, fuzzy_codes)

    return {
        "query": q,
        "language": language,
        "exact_matches": exact,
        "fuzzy_matches": fuzzy,
        "semantic_matches": semantic,
        "total_results": len(exact) + len(fuzzy) + len(semantic),
AfCFTA Platform - Enhanced Search API Routes
Intelligent HS code search and advanced investment opportunity filtering.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-search", tags=["Enhanced Search & Filtering"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class InvestmentSearchRequest(BaseModel):
    countries: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    investment_size: str = Field(default="medium")
    risk_tolerance: str = Field(default="medium")
    required_incentives: Optional[List[str]] = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search_engine():
    from search.enhanced_search import get_search_engine
    return get_search_engine()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/hs-codes")
async def search_hs_codes(
    q: str = Query(..., min_length=2, description="Search query (code or description)"),
    lang: str = Query("en", description="Response language: en | fr"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Intelligent HS code search with exact, fuzzy, and semantic matching.
    Supports numeric codes (e.g. '0901') and natural language ('coffee').
    Results are cached in L1 for 1 hour.
    """
    try:
        engine = _search_engine()
        results = engine.intelligent_hs_search(q, lang=lang)

        # Apply limit to each category
        results["exact_matches"] = results["exact_matches"][:limit]
        results["fuzzy_matches"] = results["fuzzy_matches"][:limit]
        results["semantic_matches"] = results["semantic_matches"][:limit]

        return results
    except Exception as exc:
        logger.error(f"HS search error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/investment-opportunities")
async def search_investment_opportunities(request: InvestmentSearchRequest):
    """
    Advanced investment opportunity search with multi-criteria filtering.

    Supports geographic, sector, investment size, and risk-level filtering.
    Returns scored and ranked opportunities with facets for the UI filter panel.
    """
    try:
        engine = _search_engine()
        criteria: Dict[str, Any] = {
            "countries": request.countries or [],
            "regions": request.regions or [],
            "sectors": request.sectors or ["general"],
            "investment_size": request.investment_size,
            "risk_tolerance": request.risk_tolerance,
            "required_incentives": request.required_incentives or [],
            "min_score": request.min_score,
        }
        result = engine.investment_opportunity_search(criteria)

        # Paginate
        all_opps = result.get("opportunities", [])
        start = (request.page - 1) * request.per_page
        end = start + request.per_page
        result["opportunities"] = all_opps[start:end]
        result["pagination"] = {
            "page": request.page,
            "per_page": request.per_page,
            "total_count": result["total_count"],
            "total_pages": -(-result["total_count"] // request.per_page),
        }
        return result
    except Exception as exc:
        logger.error(f"Investment search error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    type: str = Query("all", description="all | hs_code | country | sector"),
    limit: int = Query(8, ge=1, le=20),
):
    """
    Fast autocomplete for search inputs.
    Combines HS code suggestions with country and sector lookups.
    """
    suggestions = []

    if type in ("all", "hs_code") and len(q) >= 2:
        engine = _search_engine()
        hs_results = engine.intelligent_hs_search(q)
        for match in (
            hs_results.get("exact_matches", [])[:3]
            + hs_results.get("semantic_matches", [])[:3]
        ):
            suggestions.append({
                "type": "hs_code",
                "value": match.get("hs_code", ""),
                "label": match.get("description") or match.get("description_en", ""),
            })

    if type in ("all", "sector"):
        sectors = [
            "agriculture", "manufacturing", "ict", "energy",
            "finance", "tourism", "logistics", "mining", "textiles", "automotive",
        ]
        q_lower = q.lower()
        suggestions += [
            {"type": "sector", "value": s, "label": s.title()}
            for s in sectors if q_lower in s
        ]

    return {"query": q, "suggestions": suggestions[:limit]}


@router.get("/filters/options")
async def get_filter_options():
    """Return all available filter options for the search UI."""
    from intelligence.analytics.regional_analytics import REGIONAL_BLOCS
    from intelligence.ai_engine.investment_scoring import COUNTRY_INDICATORS

    return {
        "geographic_filters": {
            "countries": list(COUNTRY_INDICATORS.keys()),
            "regional_blocs": list(REGIONAL_BLOCS.keys()),
        },
        "investment_filters": {
            "investment_sizes": ["sme", "medium", "large"],
            "risk_tolerances": ["low", "medium", "high"],
            "sectors": [
                "agriculture", "manufacturing", "ict", "energy",
                "finance", "tourism", "logistics", "mining", "textiles", "automotive",
            ],
        },
        "score_range": {"min": 0.0, "max": 1.0, "step": 0.05},
    }
