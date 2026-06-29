"""
AI Trade Analysis Routes — powered by Anthropic Claude
API endpoints for AI-powered trade analysis (replaces Google Gemini)
WITH HYBRID CACHING (Redis → JSON file fallback)
"""

import logging
from typing import Annotated, Optional

from auth import check_ai_quota, require_admin
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from services.claude_trade_service import claude_trade_service
from services.real_comparison_service import real_comparison_service
from services.real_product_service import real_product_service
from services.real_summary_service import real_summary_service
from services.real_trade_data_service import AFRICAN_COUNTRIES, has_trade_data
from services.redis_cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Trade Analysis"])

# These endpoints call the Anthropic Claude API and have real per-request
# cost, so they're metered against the caller's monthly quota (see auth.py)
# in addition to the router-wide require_auth dependency applied at
# registration in routes/__init__.py.
_ai_quota = [Depends(check_ai_quota)]

# Countries without trade data (occupied territories, etc.)
NO_DATA_COUNTRIES = {
    "ESH": "RASD (Sahara Occidental)",
    "RASD": "RASD (Sahara Occidental)",
    "Sahara": "RASD (Sahara Occidental)",
    "Western Sahara": "RASD (Sahara Occidental)",
    "Sahara Occidental": "RASD (Sahara Occidental)",
}


def check_country_has_data(country_name: str) -> tuple:
    """
    Check if a country has trade data available
    Returns (has_data, country_info) tuple
    """
    name_lower = country_name.lower().strip()

    # Check direct match in NO_DATA_COUNTRIES
    for key, value in NO_DATA_COUNTRIES.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return False, {
                "name": value,
                "iso3": "ESH",
                "reason": "Territoire occupé - aucune statistique commerciale disponible dans les bases de données internationales (OEC, WITS)",
            }

    # Check by ISO3
    for iso3, info in AFRICAN_COUNTRIES.items():
        if (
            info.get("name_fr", "").lower() == name_lower
            or info.get("name_en", "").lower() == name_lower
        ):
            if not info.get("has_trade_data", True):
                return False, {
                    "name": info.get("name_fr", country_name),
                    "iso3": iso3,
                    "reason": info.get("note", "Données non disponibles"),
                }

    return True, None


@router.get("/opportunities/{country_name}", dependencies=_ai_quota)
async def get_ai_trade_opportunities(
    country_name: str,
    mode: str = Query(default="export", description="Analysis mode: export, import, or industrial"),
    lang: str = Query(default="fr", description="Language for response (fr/en)"),
):
    """
    Get AI-analyzed trade opportunities for a country

    Uses Google Gemini to analyze trade opportunities based on official data sources.

    Args:
        country_name: Name of the African country (e.g., "Algeria", "Nigeria", "Kenya")
        mode: Analysis mode
            - export: Find export opportunities
            - import: Find import substitution opportunities
            - industrial: Analyze value chain transformation opportunities
        lang: Language for the response

    Returns:
        AI-generated trade opportunities with sources and reliability indicators
    """
    valid_modes = ["export", "import", "industrial"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")

    # Check if country has trade data
    has_data, no_data_info = check_country_has_data(country_name)
    if not has_data:
        return {
            "country": no_data_info["name"],
            "iso3": no_data_info["iso3"],
            "mode": mode,
            "no_data": True,
            "message": f"Aucune donnée commerciale disponible pour {no_data_info['name']}",
            "reason": no_data_info["reason"],
            "note": "Ce pays est membre de l'Union Africaine et signataire de la ZLECAf, mais n'a pas de statistiques commerciales disponibles dans les bases de données internationales.",
            "opportunities": [],
            "summary": {
                "total_opportunities": 0,
                "total_potential_value": 0,
                "status": "NO_DATA_AVAILABLE",
            },
            "sources": ["OEC", "WITS - Aucune donnée trouvée"],
        }

    try:
        result = await claude_trade_service.analyze_trade_opportunities(
            country_name=country_name, mode=mode, lang=lang
        )

        if "error" in result and not result.get("opportunities"):
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI trade analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile/{country_name}", dependencies=_ai_quota)
async def get_ai_country_profile(
    country_name: str, lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-generated comprehensive economic profile for a country

    Includes:
    - Economic indicators (GDP, inflation, unemployment, debt)
    - Development indices (HDI, GAI)
    - Trade summary with top partners and products
    - AfCFTA potential and opportunities

    Args:
        country_name: Name of the African country
        lang: Language for the response

    Returns:
        Comprehensive country profile with economic and trade data
    """
    try:
        result = await claude_trade_service.get_country_economic_profile(
            country_name=country_name, lang=lang
        )

        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating country profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/product/{hs_code}")
async def get_ai_product_analysis(
    hs_code: str, lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Trade flows for a specific product (HS code), from REAL data.

    Provides (all sourced, no LLM-generated figures):
    - Product information and classification (WCO HS nomenclature)
    - African trade flows summary (OEC BACI / UN Comtrade)
    - Top African exporters and importers (OEC)
    - Production capacities (FAO / USGS / UNIDO)

    Args:
        hs_code: HS code (2, 4 or 6 digits)
        lang: Language for the response

    Returns:
        Comprehensive product trade analysis for Africa
    """
    # Validate HS code format
    if not hs_code.isdigit() or len(hs_code) not in [2, 4, 6]:
        raise HTTPException(status_code=400, detail="HS code must be 2, 4, or 6 digits")

    try:
        result = await real_product_service.analyze_product_by_hs_code(hs_code=hs_code, lang=lang)

        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing product: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/balance/{country_name}", dependencies=_ai_quota)
async def get_ai_trade_balance(
    country_name: str, lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AI-analyzed trade balance history for a country

    Returns trade balance data (exports, imports, balance) for 2020-2024
    with trend analysis and outlook.

    Args:
        country_name: Name of the African country
        lang: Language for the response

    Returns:
        Trade balance history with analysis
    """
    try:
        result = await claude_trade_service.get_trade_balance_analysis(
            country_name=country_name, lang=lang
        )

        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade balance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def check_ai_service_health():
    """Check if the AI service (Claude) is properly configured and operational."""
    import os

    from dotenv import load_dotenv

    load_dotenv()

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    try:
        import anthropic

        sdk_available = True
    except ImportError:
        sdk_available = False

    return {
        "status": "operational" if (has_key and sdk_available) else "not_configured",
        "model": "claude-sonnet-4-6",
        "provider": "Anthropic Claude",
        "sdk_available": sdk_available,
        "api_key_set": has_key,
    }


@router.get("/compare")
async def compare_two_countries(
    country_a: str = Query(..., description="First African country name"),
    country_b: str = Query(..., description="Second African country name"),
    lang: str = Query(default="fr", description="Language (fr/en)"),
):
    """
    Compare two African countries as AfCFTA trade partners, from REAL data.

    Economic indicators come from country_data (IMF/World Bank/UNDP), bilateral
    trade and complementarity from OEC (BACI/UN Comtrade). No LLM-generated
    figures.
    """
    if not country_a or not country_b:
        raise HTTPException(status_code=400, detail="Both country_a and country_b are required")
    if country_a.lower() == country_b.lower():
        raise HTTPException(status_code=400, detail="The two countries must be different")

    try:
        result = await real_comparison_service.compare_countries(
            country_a=country_a,
            country_b=country_b,
            lang=lang,
        )
        if "error" in result and len(result) <= 2:
            # Unknown/invalid country is a client input error, not a server fault
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing countries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary")
async def get_ai_trade_summary(
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Comprehensive African trade summary, from REAL data.

    Used for the "Vue d'ensemble" (Overview) tab. Aggregates come from the
    curated 2024 trade dataset (OEC/World Bank/IMF) and country_data — no
    LLM-generated figures.

    Args:
        lang: Language for the response

    Returns:
        Trade summary with real continental aggregates and top trading countries
    """
    try:
        result = await real_summary_service.get_trade_summary(lang=lang)

        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating trade summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/value-chains", dependencies=_ai_quota)
async def get_ai_value_chains(
    sector: str = Query(
        default=None,
        description="Specific sector to analyze (coffee, cocoa, cotton, petroleum, minerals, automotive)",
    ),
    lang: str = Query(default="fr", description="Language for response (fr/en)"),
):
    """
    Get AI-analyzed African value chains

    Used for the "Chaînes de Valeur" (Value Chains) tab.
    Analyzes production, transformation, and export opportunities.

    Args:
        sector: Optional specific sector (coffee, cocoa, cotton, petroleum, minerals, automotive)
        lang: Language for the response

    Returns:
        Value chains analysis with stages, top producers, and AfCFTA opportunities
    """
    valid_sectors = ["coffee", "cocoa", "cotton", "petroleum", "minerals", "automotive", None]
    if sector and sector not in valid_sectors:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sector. Must be one of: {[s for s in valid_sectors if s]}",
        )

    try:
        result = await claude_trade_service.get_value_chains_analysis(sector=sector, lang=lang)

        if "error" in result and len(result) <= 2:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating value chains: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cache/stats")
async def get_cache_statistics(key_doc: Annotated[dict, Depends(require_admin)] = None):
    """
    Get cache statistics (Redis + JSON file fallback) — admin only,
    consistent with the other /ai/cache/* management endpoints.

    Returns:
        Cache status, active backend, hit rate, and entry count
    """
    return cache_service.get_stats()


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(
        default=None,
        description="Cache type pattern to invalidate (e.g., 'gemini_summary', 'gemini_value_chains'). Leave empty to invalidate all.",
    ),
    country: str = Query(
        default=None, description="Country name to invalidate specific country cache entries."
    ),
    lang: str = Query(default=None, description="Language filter for invalidation (fr/en)."),
    key_doc: Annotated[dict, Depends(require_admin)] = None,
):
    """
    Invalidate cache entries (admin endpoint)

    Allows targeted invalidation by:
    - pattern: cache type prefix (e.g., gemini_summary, gemini_value_chains, gemini_analysis)
    - country + optional lang: invalidate specific country-mode combinations
    - No parameters: invalidate all AI cache entries

    Returns:
        Number of invalidated entries and details
    """
    invalidated = 0
    details = []

    if country:
        # Stamp de version des données de production (modes enrichis export/industrial)
        try:
            from production_data import get_production_data_version

            pdv = get_production_data_version()
        except Exception:
            pdv = None
        for mode in ["export", "import", "industrial"]:
            for l in ([lang] if lang else ["fr", "en"]):
                params = {"country": country, "mode": mode, "lang": l}
                if pdv and mode in ("export", "industrial"):
                    params["pdv"] = pdv
                if cache_service.invalidate("claude_analysis", params):
                    invalidated += 1
                    details.append(f"claude_analysis:{country}:{mode}:{l}")
        for l in ([lang] if lang else ["fr", "en"]):
            for profile_params in [
                {"country": country, "lang": l, "type": "profile"},
            ]:
                if cache_service.invalidate("claude_profile", profile_params):
                    invalidated += 1
                    details.append(f"claude_profile:{country}:{l}")
    elif pattern:
        invalidated = cache_service.invalidate_pattern(pattern)
        details.append(f"pattern:{pattern}")
    else:
        invalidated = cache_service.clear_all()
        details.append("all")

    return {
        "status": "ok",
        "invalidated_entries": invalidated,
        "details": details,
        "message": f"{invalidated} entrée(s) de cache invalidée(s)",
    }


@router.delete("/cache/clear")
async def clear_cache(
    pattern: str = Query(
        default=None,
        description="Pattern to clear (e.g., 'gemini_analysis'). Leave empty to clear all.",
    ),
    key_doc: Annotated[dict, Depends(require_admin)] = None,
):
    """
    Clear cache entries (admin endpoint)

    Args:
        pattern: Optional pattern to match (gemini_analysis, gemini_profile, etc.)

    Returns:
        Number of cleared entries
    """
    if pattern:
        cleared = cache_service.invalidate_pattern(pattern)
    else:
        cleared = cache_service.clear_all()

    return {"cleared_entries": cleared, "pattern": pattern or "all"}


def register_routes(app_router):
    """Register AI analysis routes with the main API router"""
    app_router.include_router(router)
