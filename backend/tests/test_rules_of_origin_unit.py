"""
Unit tests for the rules-of-origin single source of truth.

Covers routes.rules_of_origin.get_rule_of_origin(), the function shared by
routes/calculator.py and etl/hs6_database.py since the Phase 1 consolidation
that retired the separate, drifting etl.afcfta_rules_of_origin dataset.

Regression target: HS6 codes under heading 62.03 (men's suits) that don't
have their own explicit subheading rule (e.g. 620319) must resolve via the
heading-level CTH rule, not silently fall back to chapter 62's YARN default
— that exact fallback was the bug in the now-retired dataset.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import routes.rules_of_origin as roo


def _load_rules_data():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "zlecaf_rules_of_origin.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def setup_module(module):
    data = _load_rules_data()
    roo.init_data(data, data.get("origin_types"))


def test_heading_6203_fallback_no_longer_uses_chapter_yarn_rule():
    result = roo.get_rule_of_origin("620319", "fr")
    assert result["primary_rule"]["code"] == "CTH"
    assert result["source"] == "HEADING"
    # CTH has no percentage threshold in the dataset (it's a tariff-
    # classification-change rule, not a value-content rule) - None is the
    # correct, intentional value here, not a missing default to fabricate.
    # See routes/rules_of_origin.py::_regional_content.
    assert result["regional_content"] is None


def test_explicit_subheading_6203_still_resolves_via_subheading():
    result = roo.get_rule_of_origin("620311", "fr")
    assert result["primary_rule"]["code"] == "CTH"
    assert result["source"] == "SUBHEADING"


def test_wholly_obtained_products():
    for hs6 in ("100110", "090111"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["primary_rule"]["code"] == "WO"
        # WO is 100% regional content by definition, even though the
        # dataset's own `threshold` field is null for WO entries.
        assert result["regional_content"] == 100


def test_unknown_chapter_returns_ytb_shaped_fallback_without_crashing():
    result = roo.get_rule_of_origin("999999", "fr")
    assert result["status"] == "UNKNOWN"
    assert result["primary_rule"]["code"] == "YTB"
    assert result["source"] == "NONE"


def test_short_and_long_hs_codes_are_normalized():
    heading_only = roo.get_rule_of_origin("6203", "fr")
    assert heading_only["primary_rule"]["code"] == "CTH"

    eight_digit = roo.get_rule_of_origin("62031900", "fr")
    assert eight_digit["primary_rule"]["code"] == "CTH"
    assert eight_digit["source"] == "HEADING"


def test_shape_matches_legacy_etl_consumers():
    result = roo.get_rule_of_origin("850440", "fr")
    for key in (
        "hs6_code",
        "heading",
        "chapter",
        "chapter_description",
        "status",
        "primary_rule",
        "alternative_rule",
        "regional_content",
        "notes",
        "source",
        "source_detail",
    ):
        assert key in result
    assert "code" in result["primary_rule"]
    assert "name" in result["primary_rule"]
    assert "description" in result["primary_rule"]
    assert "explanation" in result["primary_rule"]


# --- Phase 2: HS6 granularity expansion regression tests -------------------
#
# These cover entries added by parsing the official AfCFTA Appendice IV PSR
# document (user-provided source, December 2023 / 12th Council of Ministers)
# directly, expanding heading/subheading coverage from 101/15 to 239/49.
# Every assertion below is grounded in that document's literal text - no
# threshold or rule code here was invented.


def test_phase2_heading_coverage_expanded_well_beyond_phase1():
    headings = roo.RULES_DATA.get("headings", {})
    subheadings = roo.RULES_DATA.get("subheadings", {})
    assert len(headings) >= 240
    assert len(subheadings) >= 45


def test_phase2_bracketed_source_code_maps_to_ytb_not_a_guessed_rule():
    # Source document lists "[52.04]" (brackets = not yet adopted) for
    # cotton sewing thread - must resolve to YTB, never a fabricated CTH/VA.
    result = roo.get_rule_of_origin("520400", "fr")
    assert result["primary_rule"]["code"] == "YTB"
    assert result["regional_content"] is None


def test_phase2_new_heading_cth_rule_grounded_in_source_text():
    # 85.19 (sound recording/reproducing apparatus): "Fabrication à partir
    # de matières de toute position autre que celle du produit" -> CTH.
    result = roo.get_rule_of_origin("851900", "fr")
    assert result["primary_rule"]["code"] == "CTH"
    assert result["source"] == "HEADING"


def test_phase2_new_heading_va_threshold_matches_source_percentage():
    # 84.01 (nuclear reactors): "...n'excède pas 60 %..." -> VA60,
    # implied regional content 40 (100 - 60), not an invented figure.
    result = roo.get_rule_of_origin("840100", "fr")
    assert result["primary_rule"]["code"] == "VA60"
    assert result["regional_content"] == 40


def test_phase2_existing_phase1_subheading_entries_untouched():
    # The Phase 1 6203.11/31/41 entries must survive Phase 2 merge unchanged
    # (merge policy: never overwrite an existing chapter/heading/subheading).
    for hs6 in ("620311", "620331", "620341"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["primary_rule"]["code"] == "CTH"
        assert result["source"] == "SUBHEADING"


# --- Copilot review follow-up: extraction-artifact regressions -------------


def test_no_glued_words_around_ou_alternative_marker():
    # Heading 50.01's source rule splits two "Ou"-joined alternatives with
    # no delimiter ("...produitOuImpression...") - the raw text stored in
    # the dataset must have the word boundary restored, not the glued
    # artifact.
    raw = roo.RULES_DATA["headings"]["5001"]["raw_fr"]
    assert "produitOu" not in raw
    assert "nonimprimé" not in raw


def test_no_leaked_rule_sentence_in_description():
    # Heading 84.56's source table has a malformed column boundary that
    # bleeds a "Fabrication dans laquelle..." rule fragment into the
    # product description cell - that duplicate fragment must not surface
    # in description_fr.
    result = roo.get_rule_of_origin("845600", "fr")
    assert "Fabrication dans laquelle" not in result["primary_rule"]["description"]


def test_empty_source_row_is_omitted_not_fabricated():
    # Subheading 6212.90 has a genuinely empty description and rule cell
    # in the source document - rather than fabricate placeholder content,
    # it must be absent so HS 621290 falls back to heading 62.12's rule.
    assert "621290" not in roo.RULES_DATA.get("subheadings", {})
    result = roo.get_rule_of_origin("621290", "fr")
    assert result["source"] in ("HEADING", "CHAPTER")


def test_empty_ytb_rule_text_normalized_to_a_determiner():
    # Subheading 6207.19 is YTB with an empty rule cell in the source -
    # raw_fr must show the dataset's existing "not yet agreed" placeholder
    # rather than an empty string.
    assert roo.RULES_DATA["subheadings"]["620719"]["raw_fr"] == "À déterminer"
    result = roo.get_rule_of_origin("620719", "fr")
    assert result["primary_rule"]["code"] == "YTB"


# --- Phase 3: plain-language rule explanations ------------------------------


def test_every_origin_type_has_an_explanation_in_both_languages():
    for code, entry in roo.ORIGIN_TYPES.items():
        explanation = entry.get("explanation")
        assert explanation, f"{code} is missing an explanation"
        assert explanation.get("fr"), f"{code} is missing a French explanation"
        assert explanation.get("en"), f"{code} is missing an English explanation"


def test_get_rule_of_origin_includes_explanation_for_each_language():
    result_fr = roo.get_rule_of_origin("620319", "fr")
    assert result_fr["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["CTH"]["explanation"]["fr"]

    result_en = roo.get_rule_of_origin("620319", "en")
    assert result_en["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["CTH"]["explanation"]["en"]


def test_explanation_absent_for_unknown_code_path():
    result = roo.get_rule_of_origin("999999", "fr")
    assert result["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["YTB"]["explanation"]["fr"]


def test_explanations_are_grounded_in_annexe_2_articles():
    # Explanations cite the actual AfCFTA Annexe 2 sur les Règles d'Origine
    # articles each rule code implements (art. 4-6), not generic textbook
    # ROO phrasing, so the wording is traceable to the authoritative source.
    grounding = {
        "WO": "5",
        "CTH": "6(1)(c)",
        "CTSH": "6(1)(d)",
        "VA": "6(1)(a)-(b)",
        "VA60": "6(1)(a)-(b)",
        "SP": "6(1)(e)",
    }
    for code, article_ref in grounding.items():
        explanation = roo.ORIGIN_TYPES[code]["explanation"]["fr"]
        assert article_ref in explanation, f"{code} explanation doesn't cite art. {article_ref}"
        assert "Annexe 2" in explanation


def test_va_threshold_explanation_states_the_specific_percentage():
    result = roo.get_rule_of_origin("840100", "fr")
    assert result["primary_rule"]["code"] == "VA60"
    assert "60" in result["primary_rule"]["explanation"]
