"""
Rules of Origin Routes
API endpoints for AfCFTA Rules of Origin (ZLECAf)

Data source: backend/data/zlecaf_rules_of_origin.json, derived from the
authentic AfCFTA Annexe 2 / Appendice IV (Product Specific Rules) table as
approved by the 12th meeting of the Council of Ministers (December 2023).

Matching priority: 6-digit subheading -> 4-digit heading -> 2-digit chapter.
No fabricated/placeholder data: any rule the source leaves bracketed /
"À déterminer" is tagged status="YTB" and never assigned a numeric threshold.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules-of-origin", tags=["Rules of Origin"])

# Populated via init_data() during app startup (see routes/__init__.py)
RULES_DATA: dict = {}
ORIGIN_TYPES: dict = {}

DEFAULT_SOURCE = "AfCFTA Appendix IV (PSR) - Décembre 2023, 12e réunion du Conseil des Ministres"


def init_data(rules_data: dict, origin_types: dict = None):
    """Initialize module-level data with the loaded JSON dataset."""
    global RULES_DATA, ORIGIN_TYPES
    RULES_DATA = rules_data or {}
    if origin_types:
        ORIGIN_TYPES = origin_types
    elif RULES_DATA.get("origin_types"):
        ORIGIN_TYPES = RULES_DATA["origin_types"]


def _rule_name(code: Optional[str], lang: str) -> str:
    if not code:
        return ""
    return ORIGIN_TYPES.get(code, {}).get(lang, code)


def _build_rule_obj(code: Optional[str], lang: str) -> Optional[dict]:
    if not code:
        return None
    return {
        "code": code,
        "name": _rule_name(code, lang),
    }


def _entry_to_response(
    hs_code: str, entry: dict, match_type: str, matched_code: str, chapter: str, lang: str
) -> dict:
    primary_code = entry.get("code")
    alt_code = entry.get("alt_code")

    primary_rule = _build_rule_obj(primary_code, lang) or {"code": "UNKNOWN", "name": ""}
    # Attach the raw rule text to the primary rule object for richer detail
    primary_rule["description"] = entry.get(f"description_{lang}") or entry.get("raw_fr") or ""

    alternative_rule = _build_rule_obj(alt_code, lang)

    threshold = entry.get("threshold")
    regional_content = 100 - threshold if threshold is not None else None
    is_wholly_obtained = primary_code == "WO"
    rule_text = entry.get(f"description_{lang}") or entry.get("raw_fr") or ""

    return {
        "hs_code": hs_code,
        "chapter": chapter,
        "status": entry.get("status", "AGREED"),
        "rules": {
            "primary_rule": primary_rule,
            "alternative_rule": alternative_rule,
            "regional_content": regional_content,
            "threshold_pct": threshold,
            "time_phase": entry.get("time_phase"),
            "applicable_notes": entry.get("notes", []),
            "rule_text_fr": entry.get("raw_fr", ""),
            "rule_text_en": entry.get("description_en") or entry.get("name_en", ""),
        },
        # Legacy shape kept for frontend/src/components/rules/RulesTab.jsx,
        # which reads rule.psr / rule.value_added_threshold directly.
        "rule": {
            "psr": rule_text,
            "wholly_obtained": is_wholly_obtained,
            "value_added_threshold": (
                regional_content if regional_content is not None else (threshold or 60)
            ),
            "category": primary_rule.get("name", ""),
            "primary_rule": primary_code,
            "alternative_rule": alt_code,
            "max_non_originating": threshold,
            "notes": rule_text,
            "status": entry.get("status", "AGREED"),
        },
        "match_type": match_type,
        "matched_code": matched_code,
        "source": entry.get("source", DEFAULT_SOURCE),
    }


@router.get("/stats")
async def get_rules_of_origin_statistics():
    """Get statistics about the rules of origin database."""
    chapters = RULES_DATA.get("chapters", {})
    headings = RULES_DATA.get("headings", {})

    if not chapters and not headings:
        return {
            "total_chapters": 0,
            "agreed_chapters": 0,
            "partial_chapters": 0,
            "ytb_chapters": 0,
            "heading_rules": 0,
            "ytb_headings": 0,
            "source": DEFAULT_SOURCE,
        }

    agreed_chapters = sum(1 for r in chapters.values() if r.get("status") == "AGREED")
    partial_chapters = sum(1 for r in chapters.values() if r.get("status") == "PARTIAL")
    ytb_chapters = sum(1 for r in chapters.values() if r.get("status") == "YTB")
    ytb_headings = sum(1 for r in headings.values() if r.get("status") == "YTB")

    return {
        "total_chapters": len(chapters),
        "agreed_chapters": agreed_chapters,
        "partial_chapters": partial_chapters,
        "ytb_chapters": ytb_chapters,
        "heading_rules": len(headings),
        "ytb_headings": ytb_headings,
        "source": RULES_DATA.get("source", DEFAULT_SOURCE),
    }


@router.get("/{hs_code}")
async def get_rules_of_origin(
    hs_code: str, lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AfCFTA Rules of Origin for a specific HS code.

    Matching priority: 6-digit subheading, then 4-digit heading, then
    2-digit chapter (most specific match first), as laid out in the
    Appendice IV Product-Specific-Rules table. Some headings carry a
    chapter-level default rule that is overridden for specific
    subheadings only (e.g. 62.03 defaults to chapter 62's YARN rule, but
    subheadings 6203.11/6203.31/6203.41 - wool/fine-hair suits - have
    their own explicit CTH rule).
    """
    lang = lang if lang in ("fr", "en") else "fr"

    hs_clean = hs_code.replace(".", "").replace(" ", "")
    chapter = hs_clean[:2].zfill(2) if len(hs_clean) >= 2 else hs_clean.zfill(2)

    chapters = RULES_DATA.get("chapters", {})
    headings = RULES_DATA.get("headings", {})
    subheadings = RULES_DATA.get("subheadings", {})

    # 1) Most-specific match: 6-digit subheading
    if len(hs_clean) >= 6:
        subheading6 = hs_clean[:6]
        if subheading6 in subheadings:
            return _entry_to_response(
                hs_code, subheadings[subheading6], "subheading", subheading6, chapter, lang
            )

    # 2) Heading-level match (4-digit)
    if len(hs_clean) >= 4:
        heading4 = hs_clean[:4]
        if heading4 in headings:
            return _entry_to_response(
                hs_code, headings[heading4], "heading", heading4, chapter, lang
            )

    # 3) Chapter-level match
    if chapter in chapters:
        return _entry_to_response(hs_code, chapters[chapter], "chapter", chapter, chapter, lang)

    # 4) No data available for this code
    return {
        "hs_code": hs_code,
        "chapter": chapter,
        "status": "UNKNOWN",
        "rules": {
            "primary_rule": {"code": "UNKNOWN", "name": ""},
            "alternative_rule": None,
            "regional_content": None,
            "threshold_pct": None,
            "time_phase": None,
            "applicable_notes": [],
            "rule_text_fr": "",
            "rule_text_en": "",
        },
        # No fabricated default here (that was the original P0 bug): leave
        # "rule" absent so RulesTab.jsx's `rulesOfOrigin.rule &&` guard simply
        # renders nothing instead of showing an invented generic rule.
        "rule": None,
        "match_type": "none",
        "matched_code": None,
        "source": DEFAULT_SOURCE,
    }


def register_routes(app_router, rules_data: dict = None, origin_types: dict = None):
    """Register rules of origin routes with the main API router."""
    if rules_data:
        init_data(rules_data, origin_types)
    app_router.include_router(router)
