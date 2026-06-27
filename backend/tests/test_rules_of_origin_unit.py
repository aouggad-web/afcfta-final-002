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
