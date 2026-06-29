"""
Tests for RealSummaryService (the "Vue d'ensemble" tab).

Continental aggregates must come from real sourced datasets (curated 2024 trade
figures + country_data), never LLM-generated or randomised. These datasets are
static, so no network/mocking is required.
"""

import asyncio

from services import real_summary_service as mod


def run(coro):
    return asyncio.run(coro)


def test_summary_aggregates_are_real_and_positive():
    result = run(mod.get_trade_summary(lang="fr"))

    assert result["is_estimation"] is False
    assert "OEC" in result["data_source"]

    ov = result["overview"]
    assert ov["total_african_trade_billion_usd"] > 0
    assert ov["total_gdp_trillion_usd"] > 0
    assert ov["afcfta_countries"] == 54
    # Not fabricated when no continental source exists
    assert ov["intra_african_trade_billion_usd"] is None
    assert result["top_sectors"] == []


def test_top_trading_countries_ranked_with_real_iso3():
    result = run(mod.get_trade_summary(lang="fr"))
    top = result["top_trading_countries"]

    assert len(top) > 0
    # Ranked by descending trade volume
    volumes = [c["trade_volume_billion"] for c in top]
    assert volumes == sorted(volumes, reverse=True)
    # South Africa is the largest trader in the dataset and maps ZA -> ZAF
    assert top[0]["iso3"] == "ZAF"
    assert top[0]["rank"] == 1
    # Field shape consumed by the frontend
    assert {"name", "trade_volume_billion", "iso3"} <= set(top[0])


def test_summary_is_reproducible():
    r1 = run(mod.get_trade_summary(lang="fr"))
    r2 = run(mod.get_trade_summary(lang="fr"))
    assert r1 == r2


def test_total_trade_matches_dataset_sum():
    from routes.statistics import TRADE_PERFORMANCE_GLOBAL_2024 as rows

    expected = round(sum((r["exports_2024"] + r["imports_2024"]) for r in rows), 1)
    result = run(mod.get_trade_summary(lang="fr"))
    assert result["overview"]["total_african_trade_billion_usd"] == expected
