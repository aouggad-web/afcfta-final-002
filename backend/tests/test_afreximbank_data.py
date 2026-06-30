"""
Tests for the Afreximbank ATR 2026 sourced-data accessor.

Validates the extracted dataset is loaded correctly and consistently
(the data file is real/committed, so no mocking is needed).
"""

from services import afreximbank_data as a


def test_continental_indicators_present():
    ind = a.get_continental_indicators()
    assert ind["real_gdp_growth_pct"] == 4.5
    assert ind["inflation_pct"] == 13.1
    assert ind["intra_african_trade_busd"] == 213.8


def test_intra_african_total():
    assert a.get_intra_african_total_busd() == 213.83


def test_intra_african_by_country_covers_54():
    by_country = a.get_intra_african_by_country()
    assert len(by_country) == 54
    # Sum of per-country 2025 values is consistent with the reported total
    total = sum(r["intra_african_2025_busd"] for r in by_country.values())
    assert abs(total - 213.83) < 0.5


def test_country_lookup_and_top():
    zaf = a.get_country_intra_african("zaf")  # case-insensitive
    assert zaf["intra_african_2025_busd"] == 41.15
    top = a.get_top_intra_african(3)
    assert [r["iso3"] for r in top] == ["ZAF", "COD", "CIV"]
    assert a.get_country_intra_african("XXX") is None


def test_merchandise_exports():
    by_country = a.get_merchandise_exports_by_country()
    assert len(by_country) == 54
    assert a.get_merchandise_exports_total_busd() == 685.2
    zaf = a.get_country_merchandise_exports("ZAF")
    assert zaf["value_2025_busd"] == 116.39
    # Per-country 2025 sum reconciles with the reported total
    total = sum(r["value_2025_busd"] for r in by_country.values())
    assert abs(total - 685.2) < 0.5


def test_dataset_exposes_source():
    ds = a.get_dataset()
    assert "Afreximbank" in ds["source"]
    assert "merchandise_exports_by_country" in ds
    assert "intra_african_trade_by_country" in ds
