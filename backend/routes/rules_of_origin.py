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
import re
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


def _rule_explanation(code: Optional[str], lang: str) -> str:
    """Plain-language explanation of what satisfying this rule code requires.

    Distinct from `name`, which is just the rule's short label (e.g. "Changement
    de Position Tarifaire") - this spells out the actual compliance test, since
    the rule code/name alone doesn't tell a non-specialist what they need to do.
    """
    if not code:
        return ""
    return ORIGIN_TYPES.get(code, {}).get("explanation", {}).get(lang, "")


def _build_rule_obj(code: Optional[str], lang: str) -> Optional[dict]:
    if not code:
        return None
    return {
        "code": code,
        "name": _rule_name(code, lang),
        "explanation": _rule_explanation(code, lang),
    }


def _regional_content(primary_code: Optional[str], threshold: Optional[int]) -> Optional[int]:
    """Regional-content percentage implied by a PSR entry.

    WO ("wholly obtained") is 100% by definition even though the dataset
    leaves its `threshold` field null (there's no max-non-originating %
    for a wholly-obtained product). CTH/CTSH/CC/SP entries genuinely have
    no percentage threshold (they're tariff-classification-change or
    specific-process rules, not value-content rules), so None there means
    "not applicable", not a missing value to default/guess at.
    """
    if primary_code == "WO":
        return 100
    if threshold is not None:
        return 100 - threshold
    return None


def _threshold_for_display(entry: dict, status: str, notes: list) -> tuple:
    # A dated source note qualifies the printed threshold. Expose it separately
    # until the applicable tariff-line version and effective rate are validated.
    threshold_note = next(
        (note for note in notes if note.startswith("Note 2.5 de l'Appendice IV:")),
        None,
    )
    threshold = None if status == "YTB" or threshold_note else entry.get("threshold")
    return threshold, threshold_note


# Annexe 2 article founding each rule code's criterion, as already cited in
# that code's origin_types explanation (a test keeps the two in step).
# HYBRID and NONE have no explanation, hence no article here. Nor has CC:
# art. 6(1) sets no chapter-level criterion, so a change of chapter rests on
# the Appendix IV rule itself (art. 6(2), already cited for every row).
_CRITERION_ARTICLES = {
    "WO": "art. 4(a) et art. 5",
    "CTH": "article 6(1)(c)",
    "CTSH": "article 6(1)(d)",
    "VA": "article 6(1)(b)",
    "VA15": "article 6(1)(b)",
    "VA40": "article 6(1)(b)",
    "VA50": "article 6(1)(b)",
    "VA60": "article 6(1)(b)",
    "VA65": "article 6(1)(b)",
    "RVC": "article 6(1)(a)",
    "SP": "article 6(1)(e)",
    "YARN": "art. 6(1)(e)",
}


# A rule code (WO, CTH, VA60...) only describes a row whose own Appendix IV
# text states that criterion and nothing more. Many rows do not: a "WO" row may
# only require the materials of chapters 17 and 18 to be wholly obtained, a CTH
# row may add a proviso on certain materials. For those rows the code's name, explanation,
# article and implied regional content would contradict or truncate the rule
# text, so only the text (which alone is authoritative) is shown.
_REVIEW_CLAUSE = (
    r"(?:[,.]?\s*(?:sous réserve d'(?:un réexamen|une révision)"
    r"|règle devant faire l'objet d'un réexamen"
    r"|cette règle fera l'objet d'un réexamen)[^.]*)?"
)
_VALUE_TEXT = (
    r"fabrication (?:à partir de matières )?dans laquelle la valeur (?:de toutes les |des )matières "
    r"(?:non originaires )?utilisées (?:n'excède pas|ne doit pas excéder) "
    r"\[?{pct}\]? ?% du prix départ usine du produit"
)
_CRITERION_TEXT = {
    # "sans laquelle": typo of the official 68.03 row (Appendix IV p. 76).
    "WO": r"fabrication [ds]ans laquelle (?:toutes )?les matières (?:utilisées )?"
    r"doivent être entièrement obtenues",
    "CTH": r"fabrication à partir de matières de toute position autres? que celle du produit",
    "CTSH": r"fabrication à partir de matières de toute sous-position autres? que celle du produit",
    "CC": r"fabrication à partir de matières de tout chapitre autre que celui du produit",
    "YARN": r"fabrication à partir de fils",
    "NONE": r"pas de règle",
}


def _rule_branches(raw_fr: str) -> list:
    text = re.sub(r"\s+", " ", (raw_fr or "").replace("’", "'")).strip()
    text = re.sub(r"^Ex-[\d.]+:.*? — ", "", text)  # designation glued before the rule
    # "Ou" separates alternatives; the source text sometimes glues it to a
    # neighbouring word ("produitOu Fabrication", "OuFabrication").
    return [
        b.strip().rstrip(".")
        for b in re.split(r"\s*\bOu\s*(?=[A-ZÉ])|(?<=[a-zé])Ou\s*(?=[A-ZÉ])", text)
    ]


def _states_criterion(code: Optional[str], branch: str) -> bool:
    if code == "SP":
        # Specific-process rows are worded case by case; only exclude those
        # whose text is in fact a change of heading or the rule for sets.
        return not re.match(_CRITERION_TEXT["CTH"], branch, re.I) and "assortiment" not in branch
    if code and code.startswith("VA") and code[2:].isdigit():
        pattern = _VALUE_TEXT.format(pct=code[2:])
    else:
        pattern = _CRITERION_TEXT.get(code)
    return bool(pattern) and bool(re.fullmatch(pattern + _REVIEW_CLAUSE, branch, re.I))


def _criterion_fits(entry: dict, alternative: bool = False) -> bool:
    """True when one "Ou" branch of the row's text states the criterion of its
    code (or of its alternative code)."""
    code = entry.get("alt_code" if alternative else "code")
    return any(_states_criterion(code, b) for b in _rule_branches(entry.get("raw_fr")))


# Label of a row whose text states no single criterion of its code.
_ROW_SPECIFIC_RULE = {
    "fr": "Règle propre à cette ligne de l'Appendice IV",
    "en": "Rule specific to this Appendix IV row",
}

# Label of a row whose Appendix IV text is "Pas de règle" (63.09, 63.10), as
# the rules tab already words it; NONE has no origin type of its own.
_NO_RULE = {"fr": "Pas de règle d'origine", "en": "No rule of origin"}


def _displayed_name(entry: dict, status: str, threshold_note, lang: str) -> str:
    """Rule name shown: a pending rule is named as such, a Note 2.5 rule by its
    criterion only (never the disputed "60 %"), a row whose text does not state
    its code's criterion by the neutral row-specific label, a "Pas de règle"
    row as having no rule of origin."""
    if status == "YTB":
        return _rule_name("YTB", lang)
    if not _criterion_fits(entry):
        return _ROW_SPECIFIC_RULE.get(lang, _ROW_SPECIFIC_RULE["fr"])
    if entry.get("code") == "NONE":
        return _NO_RULE.get(lang, _NO_RULE["fr"])
    if threshold_note:
        return _rule_name("VA", lang)
    return _rule_name(entry.get("code"), lang)


def _criterion_articles(entry: dict) -> list:
    """Annexe 2 articles behind the rule. Every Appendix IV row rests on
    art. 6(2); the criterion's own article is added only when the row's text
    states that criterion. A rule not yet adopted is not adopted per Appendix IV
    note 2.4 (cited in notes_fr); Annex 2 art. 42 (pending provisions, among them
    the elaboration of hybrid Appendix IV rules, 42(1)(c)) and its interim clause
    42(3) are cited as such, without asserting that they cover this row."""
    if entry.get("status") == "YTB":
        return ["Annexe 2, article 42, alinéas 1(c) et 3 (dispositions en suspens)"]
    articles = ["Annexe 2, article 6(2) (règles de l'Appendice IV)"]
    threshold_note = any(
        note.startswith("Note 2.5 de l'Appendice IV:") for note in entry.get("notes") or []
    )
    for code, alternative in ((entry.get("code"), False), (entry.get("alt_code"), True)):
        article = _CRITERION_ARTICLES.get(code)
        if article and _criterion_fits(entry, alternative):
            name = _rule_name("VA" if threshold_note and not alternative else code, "fr")
            articles.append(f"Annexe 2, {article} ({name})")
    return articles


def _legal_reference(entry: dict, match_type: str, matched_code: str) -> dict:
    """Cite the actual Appendix IV row selected by the resolver."""
    labels = {"chapter": "chapitre", "heading": "position", "subheading": "sous-position"}
    code = str(matched_code)
    display_code = code[:4] + "." + code[4:] if len(code) == 6 else code
    if len(code) == 4:
        display_code = code[:2] + "." + code[2:]
    scope = "ex " if entry.get("ex") else ""
    notes = []
    if entry.get("status") == "YTB":
        notes.append(
            "Appendice IV, note 2.4 (règle pas encore adoptée par les institutions "
            "de négociation de la ZLECAf)"
        )
    if any(note.startswith("Note 2.5 de l'Appendice IV:") for note in entry.get("notes") or []):
        notes.append("Appendice IV, note 2.5 (clause transitoire)")
    return {
        "instrument_fr": (
            "Accord portant création de la ZLECAf — Protocole sur le commerce des marchandises, "
            "Annexe 2 sur les règles d'origine, Appendice IV"
        ),
        "location_fr": f"{scope}{labels[match_type]} {display_code}",
        "ex": bool(entry.get("ex")),
        "articles_fr": _criterion_articles(entry),
        "matched_code": matched_code,
        "match_type": match_type,
        "source_version": entry.get("source") or DEFAULT_SOURCE,
        "notes_fr": notes,
    }


def _displayed_explanation(entry: dict, status: str, threshold_note, lang: str) -> str:
    """Explanation shown for a rule. A pending rule gets the YTB explanation
    (Appendix IV note 2.4); a row whose text does not state its
    code's criterion gets none (its text alone is authoritative); a rule whose
    printed threshold is qualified by Note 2.5 gets the generic value-content
    explanation, which names no percentage."""
    if status == "YTB":
        return _rule_explanation("YTB", lang)
    if not _criterion_fits(entry):
        return ""
    if threshold_note:
        return _rule_explanation("VA", lang)
    return _rule_explanation(entry.get("code"), lang)


def _displayed_alternative(entry: dict, lang: str) -> Optional[dict]:
    rule = _build_rule_obj(entry.get("alt_code"), lang)
    if rule and not _criterion_fits(entry, alternative=True):
        rule["explanation"] = ""
    return rule


def _entry_to_response(
    hs_code: str, entry: dict, match_type: str, matched_code: str, chapter: str, lang: str
) -> dict:
    primary_code = entry.get("code")
    alt_code = entry.get("alt_code")

    primary_rule = _build_rule_obj(primary_code, lang) or {"code": "UNKNOWN", "name": ""}
    # The Appendice IV rule text is raw_fr (description_fr is the product
    # designation). It exists in French only: no translation, whatever lang.
    rule_text = entry.get("raw_fr") or ""
    status = entry.get("status", "AGREED")
    requirement = "" if status == "YTB" else rule_text
    primary_rule["description"] = requirement

    alternative_rule = _displayed_alternative(entry, lang)

    notes = entry.get("notes") or []
    threshold, threshold_note = _threshold_for_display(entry, status, notes)
    fits = status != "YTB" and _criterion_fits(entry)
    primary_rule["name"] = _displayed_name(entry, status, threshold_note, lang)
    primary_rule["matches_text"] = fits
    primary_rule["explanation"] = _displayed_explanation(entry, status, threshold_note, lang)
    regional_content = _regional_content(primary_code, threshold) if fits else None
    is_wholly_obtained = fits and primary_code == "WO"

    return {
        "hs_code": hs_code,
        "chapter": chapter,
        "status": status,
        "product_description_fr": entry.get("product_description_fr")
        or entry.get("description_fr")
        or "",
        "rules": {
            "primary_rule": primary_rule,
            "alternative_rule": alternative_rule,
            "regional_content": regional_content,
            "threshold_pct": threshold,
            "time_phase": entry.get("time_phase"),
            "applicable_notes": notes,
            "threshold_note_fr": threshold_note,
            "rule_text_fr": entry.get("raw_fr", ""),
            "rule_text_en": "",  # no English version of the rule in the dataset
        },
        # Legacy shape kept for frontend/src/components/rules/RulesTab.jsx,
        # which reads rule.psr / rule.value_added_threshold directly.
        "rule": {
            "psr": requirement,
            "wholly_obtained": is_wholly_obtained,
            # Only value-content rules (VA*) carry a threshold; CTH, WO, SP,
            # YTB... get None, never a defaulted percentage.
            "value_added_threshold": regional_content if threshold is not None else None,
            "category": primary_rule.get("name", ""),
            "primary_rule": primary_code,
            "alternative_rule": alt_code,
            "max_non_originating": threshold,
            "status": entry.get("status", "AGREED"),
        },
        "match_type": match_type,
        "matched_code": matched_code,
        "legal_reference": _legal_reference(entry, match_type, matched_code),
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
        "legal_reference": None,
        "source": DEFAULT_SOURCE,
    }


def get_rule_of_origin(hs_code: str, lang: str = "fr") -> dict:
    """Single source of truth for the rules-of-origin verdict on an HS code.

    Used by backend code that needs this lookup outside an HTTP request
    (e.g. etl/hs6_database.py), as a direct function
    call. The module's own /{hs_code} endpoint does not call this function —
    it has its own matching loop that builds its (richer) response via
    _entry_to_response. Both implement the same subheading -> heading ->
    chapter priority against the same RULES_DATA, so keep them in sync if
    that priority ever changes. Returned shape matches the one historically
    produced by etl.afcfta_rules_of_origin.get_rule_of_origin, which this
    supersedes — that module duplicated RULES_DATA in a separate,
    independently maintained Python dict and had drifted out of sync with
    it (e.g. it was missing a heading-level rule for 62.03, see
    headings['6203'] above).

    Matching priority: 6-digit subheading -> 4-digit heading -> 2-digit chapter.
    """
    lang = lang if lang in ("fr", "en") else "fr"
    hs_clean = hs_code.replace(".", "").replace(" ", "")
    hs6 = hs_clean[:6].ljust(6, "0") if hs_clean else "000000"
    heading = hs_clean[:4] if len(hs_clean) >= 4 else hs_clean
    chapter = hs_clean[:2].zfill(2) if len(hs_clean) >= 2 else hs_clean.zfill(2)

    chapters = RULES_DATA.get("chapters", {})
    headings = RULES_DATA.get("headings", {})
    subheadings = RULES_DATA.get("subheadings", {})

    entry = None
    match_type = "none"
    if hs6 in subheadings:
        entry, match_type = subheadings[hs6], "subheading"
    elif heading in headings:
        entry, match_type = headings[heading], "heading"
    elif chapter in chapters:
        entry, match_type = chapters[chapter], "chapter"

    chapter_entry = chapters.get(chapter, {})
    chapter_description = chapter_entry.get(f"description_{lang}") or chapter_entry.get(
        "raw_fr", ""
    )

    if entry is None:
        return {
            "hs6_code": hs6,
            "heading": heading,
            "chapter": chapter,
            "chapter_description": chapter_description,
            "status": "UNKNOWN",
            "primary_rule": {
                "code": "YTB",
                "type": "YTB",
                "name": ORIGIN_TYPES.get("YTB", {}).get(lang)
                or ("En cours de négociation" if lang == "fr" else "Yet to be agreed"),
                "description": (
                    "Les règles pour ce produit sont encore en négociation"
                    if lang == "fr"
                    else "Rules for this product are still under negotiation"
                ),
                "explanation": _rule_explanation("YTB", lang),
            },
            "alternative_rule": None,
            "regional_content": None,
            "notes": "",
            "source": "NONE",
            "source_detail": f"No PSR entry found for {hs_code}",
        }

    primary_code = entry.get("code")
    alt_code = entry.get("alt_code")
    status = entry.get("status", "AGREED")
    notes = entry.get("notes") or []
    threshold, threshold_note = _threshold_for_display(entry, status, notes)
    fits = status != "YTB" and _criterion_fits(entry)
    regional_content = _regional_content(primary_code, threshold) if fits else None

    return {
        "hs6_code": hs6,
        "heading": heading,
        "chapter": chapter,
        "chapter_description": chapter_description,
        "status": entry.get("status", "AGREED"),
        "primary_rule": {
            "code": primary_code,
            "type": primary_code,
            "name": _displayed_name(entry, status, threshold_note, lang),
            "description": entry.get(f"description_{lang}") or entry.get("raw_fr", ""),
            "explanation": _displayed_explanation(entry, status, threshold_note, lang),
            # A row-specific name refers to the row text: give that text
            # (French only), except for a rule not yet adopted.
            "matches_text": fits,
            "rule_text_fr": "" if status == "YTB" else entry.get("raw_fr") or "",
        },
        "alternative_rule": (
            {
                "code": alt_code,
                "type": alt_code,
                "name": _rule_name(alt_code, lang),
                "description": _rule_name(alt_code, lang),
                "explanation": (
                    _rule_explanation(alt_code, lang)
                    if _criterion_fits(entry, alternative=True)
                    else ""
                ),
            }
            if alt_code
            else None
        ),
        "regional_content": regional_content,
        "notes": "; ".join(notes) if notes else "",
        "source": match_type.upper(),
        "source_detail": f"AfCFTA Appendix IV (PSR) - {match_type} match for {hs_code}",
    }


def register_routes(app_router, rules_data: dict = None, origin_types: dict = None):
    """Register rules of origin routes with the main API router."""
    if rules_data:
        init_data(rules_data, origin_types)
    app_router.include_router(router)
