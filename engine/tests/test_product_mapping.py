import pytest

from engine.product_mapping import (
    ExistingTariffIndexMapper,
    GazetteProductMapping,
    automatic_overlay_hs6,
    normalize_term,
)


def mapping(**updates):
    values = {
        "mapping_id": "map-1", "measure_id": "measure-1",
        "gazette_product_text": "Wheat", "normalized_product_name": "wheat",
        "gazette_reference": "Official gazette row 1", "index_terms_used": ["wheat"],
        "wco_index_matches": [{"hs6": "100199", "description_en": "Other wheat"}],
        "hs_version": "HS2022", "hs4_candidates": ["1001"], "hs6_candidates": ["100199"],
        "selected_hs6": "100199", "classification_status": "VALIDATED_HS6",
        "confidence_score": 95, "classification_reasoning": "Unique candidate confirmed by heading.",
        "section_notes_checked": ["Section II"], "chapter_notes_checked": ["Chapter 10"],
        "legal_conditions": [], "requires_human_review": False,
        "source_id": "source-1", "effective_from": "2026-07-01", "effective_to": "2027-06-30",
    }
    values.update(updates)
    return GazetteProductMapping(**values)


def fake_search(country, term, language, limit):
    rows = {
        "wheat": [{"hs6": "100199", "description_en": "Other wheat"}],
        "grain": [{"hs6": "100199", "description_en": "Other wheat"}],
        "steel pipe": [
            {"hs6": "730630", "description_en": "Other welded tubes"},
            {"hs6": "730661", "description_en": "Square hollow profiles"},
        ],
    }
    return rows.get(term, [])


def test_exact_index_product_and_synonym_use_existing_search():
    mapper = ExistingTariffIndexMapper(fake_search)
    assert mapper.candidates(["wheat"])[0]["hs6"] == "100199"
    assert mapper.candidates(["grain"])[0]["hs6"] == "100199"


def test_description_with_material_is_normalized_without_losing_material():
    assert normalize_term("Steel pipes") == "steel pipe"


@pytest.mark.parametrize(
    "status",
    ["END_USE_MEASURE", "CONTEXT_DEPENDENT", "MULTIPLE_HS_CANDIDATES", "HUMAN_REVIEW_REQUIRED"],
)
def test_uncertain_or_end_use_mapping_never_applies(status):
    candidate = mapping(classification_status=status, requires_human_review=True)
    assert automatic_overlay_hs6(candidate) is None


def test_expression_covering_multiple_products_is_blocked():
    candidate = mapping(
        gazette_product_text="Various raw materials for animal feed",
        hs6_candidates=["100590", "230990"], selected_hs6=None,
        classification_status="END_USE_MEASURE", confidence_score=20,
        requires_human_review=True,
    )
    assert automatic_overlay_hs6(candidate) is None


def test_multiple_index_candidates_are_preserved():
    rows = ExistingTariffIndexMapper(fake_search).candidates(["steel pipe"])
    assert {row["hs6"] for row in rows} == {"730630", "730661"}


def test_hs_version_change_blocks_overlay():
    assert automatic_overlay_hs6(mapping(), target_hs_version="HS2017") is None


def test_expiry_is_kept_for_temporal_engine():
    candidate = mapping(effective_to="2026-06-30")
    assert candidate.effective_to == "2026-06-30"


def test_validated_code_still_does_not_waive_beneficiary_condition():
    candidate = mapping(legal_conditions=["beneficiary=MANUFACTURER"])
    assert automatic_overlay_hs6(candidate) == "100199"
    assert candidate.legal_conditions == ["beneficiary=MANUFACTURER"]


def test_overlay_can_list_multiple_hs6_but_is_not_automatic_as_single_mapping():
    candidate = mapping(hs6_candidates=["842511", "842519", "843139"], selected_hs6=None)
    assert automatic_overlay_hs6(candidate) is None
