"""
Regression tests for CrawledDataService.lookup().

Guards against two bugs found in the authentic-data path:

1. A 6-digit HS6 query must resolve to a real national position for every
   country that has authentic crawled data. National lines are stored at
   8-12 digits, so an exact match never occurs; lookup() must fall back to
   the HS6 index instead of returning None (which made the calculator serve
   estimated chapter rates labelled as "verified").

2. EGY positions must actually be indexed (the parser previously read the
   wrong field names and silently dropped all 8,746 Egyptian positions).
"""

import pytest
from services.crawled_data_service import crawled_service

# Countries with genuine national crawled tariff data.
AUTHENTIC_COUNTRIES = ["DZA", "EGY", "MAR", "TUN"]


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    crawled_service.load()
    for iso in AUTHENTIC_COUNTRIES:
        crawled_service._ensure_country_loaded(iso)


@pytest.mark.parametrize("iso", AUTHENTIC_COUNTRIES)
def test_country_has_indexed_positions(iso):
    idx = crawled_service._code_index.get(iso, {})
    assert len(idx) > 0, f"{iso} has no indexed national positions"


@pytest.mark.parametrize("iso", AUTHENTIC_COUNTRIES)
def test_six_digit_hs6_resolves_to_national_position(iso):
    hs6_index = crawled_service._hs6_index.get(iso, {})
    assert hs6_index, f"{iso} HS6 index is empty"

    # Use a real HS6 present in this country's data.
    sample_hs6 = next(iter(hs6_index.keys()))

    result = crawled_service.lookup(iso, sample_hs6)
    assert result is not None, (
        f"{iso}: 6-digit HS6 {sample_hs6} did not resolve to a national "
        f"position (calculator would fall back to estimated data)"
    )
    assert result["code_clean"].startswith(sample_hs6)


@pytest.mark.parametrize("iso", AUTHENTIC_COUNTRIES)
def test_overlong_code_still_truncates(iso):
    hs6_index = crawled_service._hs6_index.get(iso, {})
    sample = next(iter(hs6_index.values()))[0]["code_clean"]
    # Append extra digits beyond the stored national code length.
    assert crawled_service.lookup(iso, sample + "99") is not None


def test_egy_taxes_are_parsed():
    """EGY positions must carry parsed DD/TVA rates, not empty taxes."""
    hs6_index = crawled_service._hs6_index.get("EGY", {})
    sample_hs6 = next(iter(hs6_index.keys()))
    result = crawled_service.lookup("EGY", sample_hs6)
    assert result["taxes"], "EGY position has no taxes parsed"
    assert any(
        t["code"] == "DD" for t in result["taxes"]
    ), "EGY position is missing the Droit de Douane (DD) line"
