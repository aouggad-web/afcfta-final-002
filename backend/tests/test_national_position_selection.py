"""Selection contracts: test codes contain no tariff rates or production data."""

import pytest

from services import authentic_tariff_service
from services.national_position_selection import (
    NationalPositionRequired,
    select_calculation_position,
)


POSITIONS = [{"code": "00000010"}, {"code": "00000020"}]


def test_exact_position_retains_original_entry():
    assert select_calculation_position("00000020", POSITIONS) is POSITIONS[1]


@pytest.mark.parametrize("code", ["00000099", "0000001000", "0000001"])
def test_missing_national_code_never_selects_sibling_or_truncated_parent(code):
    with pytest.raises(NationalPositionRequired) as exc:
        select_calculation_position(code, POSITIONS)
    assert exc.value.detail["code"] == "NATIONAL_POSITION_NOT_FOUND"


def test_ambiguous_hs6_requires_selection_even_if_parent_is_listed():
    with pytest.raises(NationalPositionRequired) as exc:
        select_calculation_position("000000", [{"code": "000000"}] + POSITIONS)
    assert exc.value.detail["code"] == "NATIONAL_POSITION_SELECTION_REQUIRED"
    assert exc.value.detail["candidates"] == ["00000010", "00000020"]


def test_unambiguous_child_can_be_selected_without_fabricating_digits():
    assert select_calculation_position("000000", POSITIONS[:1]) is POSITIONS[0]


def test_formatted_crawled_code_matches_exactly():
    entry = {"code_raw": "0000.0020", "designation": "TEST"}
    assert select_calculation_position("00000020", [entry]) is entry


@pytest.mark.parametrize("code", ["00", "0000", "abcdef", "0000000000000"])
def test_browsing_prefixes_and_invalid_codes_cannot_be_calculated(code):
    with pytest.raises(NationalPositionRequired):
        select_calculation_position(code, POSITIONS)


def test_empty_enumeration_does_not_invent_a_national_position():
    assert select_calculation_position("000000", []) is None
    with pytest.raises(NationalPositionRequired):
        select_calculation_position("00000010", [])


@pytest.mark.parametrize("code", ["000000", "00000099"])
def test_authentic_service_stops_before_tax_fallback(monkeypatch, code):
    monkeypatch.setattr(authentic_tariff_service, "get_sub_positions", lambda *args: POSITIONS)

    def forbidden_fallback(*args):
        pytest.fail("A rejected position must not reach tariff fallback")

    monkeypatch.setattr(authentic_tariff_service, "load_country_tariffs", forbidden_fallback)
    result = authentic_tariff_service.calculate_import_taxes("ZZZ", code, 100)
    assert result["error_detail"]["candidate_count"] == 2
    assert "npf_calculation" not in result
