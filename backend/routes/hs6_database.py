"""
HS6 Database Routes - Optimized for Data-Driven Search.
Uses the TariffSearchEngine to provide complete and accurate tariff data.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from search.hs_code_search import get_search_engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

try:
    from etl.hs_codes_data import HS_CHAPTERS as _HS_CHAPTERS

    CHAPTER_NAMES: Dict[str, Dict[str, str]] = {
        "fr": {ch: names["fr"] for ch, names in _HS_CHAPTERS.items()},
        "en": {ch: names["en"] for ch, names in _HS_CHAPTERS.items()},
    }
except ImportError:
    CHAPTER_NAMES = {"fr": {}, "en": {}}

# ---------------------------------------------------------------------------
# Search scoring helpers
# ---------------------------------------------------------------------------

# Maximum base score awarded for a code prefix match (one point per
# character remaining keeps shorter prefixes higher-ranked).
_MAX_CODE_SCORE = 10

# Scores for text-match quality tiers.
_EXACT_WORD_MATCH_SCORE = 50  # query word matches a full word in description
_PARTIAL_MATCH_SCORE = 10  # query word appears as a substring


def _score_code_match(code: str, query: str) -> int:
    """Score a numeric code match by prefix overlap.

    Returns a positive integer when *code* starts with *query*, scaled so
    that shorter prefixes yield higher scores (broader match has priority).
    Returns 0 when there is no prefix match.
    """
    if not code or not query:
        return 0
    if code.startswith(query):
        return max(1, _MAX_CODE_SCORE - len(query))
    return 0


def _score_text_match(description: str, query: str) -> int:
    """Score text relevance between *description* and *query*.

    Returns >= 50 for exact word matches, > 0 for partial/substring matches,
    and 0 when there is no overlap at all. Case-insensitive.
    """
    if not description or not query:
        return 0
    desc_lower = description.lower()
    query_words = query.lower().split()
    desc_words = desc_lower.split()
    total = 0
    for word in query_words:
        if word in desc_words:
            total += _EXACT_WORD_MATCH_SCORE
        elif word in desc_lower:
            total += _PARTIAL_MATCH_SCORE
    return total


def _build_search_result(code: str, data: dict, language: str, score: int) -> dict:
    """Build a standardised search result dictionary.

    Args:
        code: 6-digit HS code string.
        data: Code entry dict with ``description_fr`` and/or ``description_en``.
        language: Requested language (``'fr'`` or ``'en'``).
        score: Pre-computed relevance score.

    Returns:
        A dict with keys: code, description, chapter, chapter_name,
        full_position, position_4, score.
    """
    chapter = code[:2]
    position_4 = code[:4]
    desc_key = f"description_{language}" if language in ("fr", "en") else "description_fr"
    description = data.get(desc_key) or data.get("description_fr", "")
    chapter_name = CHAPTER_NAMES.get(language, CHAPTER_NAMES.get("fr", {})).get(chapter, "")
    full_position = f"{chapter} - {chapter_name}" if chapter_name else chapter
    return {
        "code": code,
        "description": description,
        "chapter": chapter,
        "chapter_name": chapter_name,
        "full_position": full_position,
        "position_4": position_4,
        "score": score,
    }


router = APIRouter(prefix="/hs6")


def load_algeria_nomenclature():
    """Load Algeria nomenclature map for extended sub-position search"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        file_path = os.path.join(data_dir, "DZA_nomenclature_map.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading Algeria nomenclature: {e}")
    return None


@router.get("/smart-search")
async def smart_search_hs6(
    q: Optional[str] = Query(default=None, min_length=2),
    query: Optional[str] = Query(default=None, min_length=2),
    language: str = Query(default="fr"),
    country_code: Optional[str] = Query(default=None),
    include_sub_positions: bool = Query(default=False),
    limit: int = Query(default=20),
):
    """
    Smart HS6 search powered by the optimized TariffSearchEngine.
    Provides complete denominations (buffered) and real-time data loading.
    Special handling for DZA (Algeria) with nomenclature_map lookup for extended codes.
    """
    try:
        # Special case for long numeric codes (potentially Algeria extended sub-positions)
        # Check Algeria nomenclature if query is a long numeric code (8+ digits)
        if q.isdigit() and len(q) >= 8:
            dza_nomenclature = load_algeria_nomenclature()
            if dza_nomenclature and q in dza_nomenclature:
                # Found exact match in Algeria nomenclature
                logger.info(f"Found {q} in Algeria nomenclature_map")
                return {
                    "query": q,
                    "results": [
                        {
                            "code": q,
                            "description": dza_nomenclature[q],
                            "country": "DZA",
                            "duty_rate_pct": 0.0,
                            "unit": "",
                            "chapter": q[:2],
                            "match_type": "exact_nomenclature",
                            "source": "algeria_nomenclature_map",
                        }
                    ],
                    "total": 1,
                    "source": "algeria_nomenclature_map",
                }

        engine = get_search_engine()
        # The new engine provides a unified search method
        raw_results = engine.search(query=q, country=country_code, limit=limit)

        # Map results to the format expected by the frontend
        results = []
        for r in raw_results:
            results.append(
                {
                    "code": str(r.get("hs_code", "")),
                    "description": r.get("description", ""),
                    "country": r.get("country", ""),
                    "duty_rate_pct": r.get("duty_rate_pct"),
                    "unit": r.get("unit", ""),
                    "chapter": str(r.get("hs_code", ""))[:2],
                    "match_type": "hybrid",
                }
            )

        return {
            "query": q,
            "results": results,
            "total": len(results),
            "source": "optimized_tariff_engine",
        }
    except Exception as e:
        logger.error(f"Smart search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/info/{hs_code}")
async def get_hs6_info(hs_code: str, language: str = Query(default="fr")):
    """Get detailed info for a specific HS code using the optimized engine."""
    engine = get_search_engine()
    # Search for exact code
    res = engine.search(query=hs_code, limit=1)
    if res:
        r = res[0]
        return {"code": str(r.get("hs_code")), "description": r.get("description"), "found": True}
    return {"code": hs_code, "found": False, "description": f"HS {hs_code} not found"}
