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


def get_tariff_line(country: str, hs6: str) -> Optional[dict]:
    """Return basic tariff line data for a 6-digit HS code and country.

    Returns a dict with at least ``hs6`` or ``None`` when not found.
    """
    try:
        engine = get_search_engine()
        results = engine.search(query=hs6, country=country, limit=1)
        if results:
            r = results[0]
            return {"hs6": hs6, "description": r.get("description", ""), "country": country}
    except Exception:
        pass
    return None


def get_sub_positions(country: str, hs6: str) -> list:
    """Return sub-positions (8- or 10-digit codes) for a 6-digit HS code and country."""
    try:
        engine = get_search_engine()
        results = engine.search(query=hs6, country=country, limit=200)
        sub = []
        for r in results:
            code = str(r.get("hs_code", ""))
            if len(code) > 6 and code.startswith(hs6):
                sub.append(
                    {
                        "code": code,
                        "digits": len(code),
                        "dd_rate": r.get("duty_rate_pct", 0.0),
                        "description_fr": r.get("description", ""),
                        "description_en": r.get("description", ""),
                        "source": "search_engine",
                    }
                )
        return sub
    except Exception:
        return []


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

    Accepts ``q`` or ``query`` (alias) as the search term.  Returns results
    enriched with ``chapter_name``, ``full_position``, ``from_authentic`` and
    optionally ``sub_positions``.
    """
    effective_q = q or query
    if not effective_q:
        raise HTTPException(status_code=422, detail="Query parameter 'q' or 'query' is required")
    if len(effective_q) < 2:
        raise HTTPException(status_code=422, detail="Query must be at least 2 characters")

    try:
        # Special case for long numeric codes (potentially Algeria extended sub-positions)
        # Check Algeria nomenclature if query is a long numeric code (8+ digits)
        if effective_q.isdigit() and len(effective_q) >= 8:
            dza_nomenclature = load_algeria_nomenclature()
            if dza_nomenclature and effective_q in dza_nomenclature:
                logger.info(f"Found {effective_q} in Algeria nomenclature_map")
                chapter = effective_q[:2]
                chapter_name = CHAPTER_NAMES.get(language, CHAPTER_NAMES.get("fr", {})).get(
                    chapter, ""
                )
                return {
                    "query": effective_q,
                    "count": 1,
                    "results": [
                        {
                            "code": effective_q,
                            "description": dza_nomenclature[effective_q],
                            "country": "DZA",
                            "duty_rate_pct": 0.0,
                            "unit": "",
                            "chapter": chapter,
                            "chapter_name": chapter_name,
                            "full_position": (
                                f"{chapter} - {chapter_name}" if chapter_name else chapter
                            ),
                            "from_authentic": True,
                            "match_type": "exact_nomenclature",
                            "source": "algeria_nomenclature_map",
                        }
                    ],
                    "total": 1,
                    "source": "algeria_nomenclature_map",
                }

        engine = get_search_engine()
        raw_results = engine.search(query=effective_q, country=country_code, limit=limit)

        # Separate 6-digit tariff lines from sub-positions (longer codes)
        top_level = []
        embedded_sub: dict = {}
        for r in raw_results:
            code = str(r.get("hs_code", ""))
            if len(code) <= 6:
                top_level.append(r)
            else:
                hs6 = code[:6]
                embedded_sub.setdefault(hs6, []).append(r)

        results = []
        for r in top_level:
            code = str(r.get("hs_code", ""))
            chapter = code[:2]
            chapter_name = CHAPTER_NAMES.get(language, CHAPTER_NAMES.get("fr", {})).get(chapter, "")
            full_position = f"{chapter} - {chapter_name}" if chapter_name else chapter
            entry = {
                "code": code,
                "description": r.get("description", ""),
                "country": r.get("country", ""),
                "duty_rate_pct": r.get("duty_rate_pct"),
                "unit": r.get("unit", ""),
                "chapter": chapter,
                "chapter_name": chapter_name,
                "full_position": full_position,
                "from_authentic": True,
                "match_type": "hybrid",
            }
            if include_sub_positions:
                raw_subs = get_sub_positions(country_code or r.get("country", ""), code) or [
                    {
                        "code": s.get("hs_code", ""),
                        "digits": len(str(s.get("hs_code", ""))),
                        "dd_rate": s.get("duty_rate_pct", 0.0),
                        "description_fr": s.get("description", ""),
                        "description_en": s.get("description", ""),
                        "source": "search_engine",
                    }
                    for s in embedded_sub.get(code, [])
                ]
                entry["sub_positions"] = [
                    {
                        "code": sp.get("code", ""),
                        "digits": sp.get("digits", 0),
                        "dd": sp.get("dd_rate", 0.0),
                        "description": sp.get("description_fr") or sp.get("description_en", ""),
                        "source": sp.get("source", ""),
                    }
                    for sp in raw_subs
                ]
            results.append(entry)

        return {
            "query": effective_q,
            "count": len(results),
            "results": results,
            "total": len(results),
            "source": "optimized_tariff_engine",
        }
    except HTTPException:
        raise
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
