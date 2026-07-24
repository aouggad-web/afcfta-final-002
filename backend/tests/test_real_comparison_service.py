"""
Tests for RealComparisonService (the "Comparaison" tab).

Economic indicators must come from country_data (real), bilateral trade and
complementarity from OEC (real) — never LLM-generated or randomised. OEC is
mocked so the tests are hermetic (no network).
"""

import asyncio

import pytest
from services import real_comparison_service as mod


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _clear_cache():
    mod._CACHE.clear()
    yield
    mod._CACHE.clear()


def _patch(monkeypatch, *, bilateral, exports, imports):
    async def fake_bilateral(exporter, importer, year=2022, limit=10):
        return bilateral.get(
            (exporter, importer), {"total_value": 0, "top_products": [], "year": year}
        )

    async def fake_exports(iso3, year=2022, limit=100):
        return exports.get(iso3, [])

    async def fake_imports(iso3, year=2022, limit=100):
        return imports.get(iso3, [])

    monkeypatch.setattr(mod.real_trade_service, "get_bilateral_trade", fake_bilateral)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_exports)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_imports", fake_imports)


def test_resolve_iso3_by_name_and_code():
    assert mod._resolve_iso3("DZA") == "DZA"
    assert mod._resolve_iso3("Nigeria") == "NGA"
    assert mod._resolve_iso3("Algérie") == "DZA"
    assert mod._resolve_iso3("Atlantis") is None


def test_parse_pct():
    assert mod._parse_pct("3.5%") == 3.5
    assert mod._parse_pct(4) == 4.0
    assert mod._parse_pct(None) is None
    assert mod._parse_pct("n/a") is None


def test_compare_uses_real_country_data_and_oec(monkeypatch):
    # CIV exports cocoa (ch.18); DZA imports cocoa (ch.18) -> complementarity
    bilateral = {
        ("CIV", "DZA"): {
            "total_value": 500_000_000,
            "top_products": [{"product_name": "Cocoa"}],
            "year": 2022,
        },
        ("DZA", "CIV"): {
            "total_value": 200_000_000,
            "top_products": [{"product_name": "Refined petroleum"}],
            "year": 2022,
        },
    }
    exports = {
        "CIV": [{"hs_code": "1801", "product_name": "Cocoa beans", "trade_value": 4_000_000_000}],
        "DZA": [
            {"hs_code": "2710", "product_name": "Refined petroleum", "trade_value": 3_000_000_000}
        ],
    }
    imports = {
        "DZA": [
            {"hs_code": "1806", "product_name": "Chocolate", "trade_value": 1_000_000_000}
        ],  # ch.18
        "CIV": [
            {"hs_code": "2710", "product_name": "Refined petroleum", "trade_value": 2_000_000_000}
        ],  # ch.27
    }
    _patch(monkeypatch, bilateral=bilateral, exports=exports, imports=imports)

    result = run(mod.compare_countries("Côte d'Ivoire", "Algérie", lang="fr"))

    assert result["is_estimation"] is False
    assert "OEC" in result["data_source"]

    # Economic indicators come from REAL_COUNTRY_DATA
    econ = result["economic_comparison"]
    assert econ["gdp_a_billion"] == mod.REAL_COUNTRY_DATA["CIV"]["gdp_usd_2024"]
    assert econ["gdp_b_billion"] == mod.REAL_COUNTRY_DATA["DZA"]["gdp_usd_2024"]
    assert econ["hdi_b"] == mod.REAL_COUNTRY_DATA["DZA"]["development_index"]
    assert econ["inflation_a"] is None  # not fabricated

    # Bilateral from real OEC directional flows
    bt = result["bilateral_trade"]
    assert bt["exports_a_to_b_musd"] == 500.0
    assert bt["exports_b_to_a_musd"] == 200.0
    assert bt["balance_musd"] == 300.0

    # Complementarity: CIV (cocoa ch.18) -> DZA (imports chocolate ch.18); bounded by min
    comp = result["trade_complementarity"]
    civ_flow = comp["a_can_supply_to_b"]
    assert civ_flow and civ_flow[0]["hs6Code"] == "18"
    assert civ_flow[0]["potential_musd"] == 1000.0  # min(4000M, 1000M)
    assert 0 <= comp["score"] <= 10

    # DZA (petroleum ch.27) -> CIV (imports petroleum ch.27)
    assert result["trade_complementarity"]["b_can_supply_to_a"][0]["hs6Code"] == "27"


def test_compare_is_reproducible(monkeypatch):
    bilateral = {("CIV", "DZA"): {"total_value": 500_000_000, "top_products": [], "year": 2022}}
    _patch(monkeypatch, bilateral=bilateral, exports={}, imports={})
    r1 = run(mod.compare_countries("CIV", "DZA", lang="fr"))
    mod._CACHE.clear()
    r2 = run(mod.compare_countries("CIV", "DZA", lang="fr"))
    assert r1 == r2


def test_compare_unknown_country_errors(monkeypatch):
    _patch(monkeypatch, bilateral={}, exports={}, imports={})
    result = run(mod.compare_countries("Atlantis", "DZA", lang="fr"))
    assert result.get("error")
