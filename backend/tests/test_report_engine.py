"""
Tests for the premium Opportunités report engine and its adapters.

Discipline under test (mirrors the rest of the platform):
  - Real, sourced values only; unavailable data -> None / available: False,
    never fabricated.
  - Composite indicators are deterministic and their weighting is transparent
    (the end-to-end score renormalises over *available* components only).

Hermetic: the FX provider (network) is stubbed; all other inputs are local
datasets, so no test touches the network.
"""

import asyncio

import pytest
from services import finance_opportunity_adapter as finance
from services import logistics_opportunity_adapter as logistics
from services import macro_indicators_service as macro
from services import report_engine


# ── Macro indicators ─────────────────────────────────────────────────────────
def test_gai_is_real_for_known_country():
    gai = macro.get_gai("MUS")  # Mauritius ranks #1 in Africa on GAI 2025
    assert gai is not None
    assert gai["rank_africa"] == 1
    assert isinstance(gai["score"], (int, float))
    assert "Mo Ibrahim" in gai["source"]


def test_gai_none_for_unknown_country():
    assert macro.get_gai("ZZZ") is None


def test_fx_reserves_and_import_cover_degrade_gracefully_without_dataset():
    # data/json/wb_reserves.json is not shipped (World Bank API blocked here);
    # the accessors must flag unavailable and never invent a number.
    fx = macro.get_fx_reserves("NGA")
    cover = macro.get_import_cover("NGA")
    assert fx["available"] is False and fx["value_busd"] is None
    assert cover["available"] is False and cover["months"] is None
    assert fx["indicator"] == macro.WB_FX_RESERVES_INDICATOR
    assert cover["indicator"] == macro.WB_IMPORT_COVER_INDICATOR


# ── Financing-feasibility index (pure, deterministic) ────────────────────────
def test_financing_feasibility_full_score():
    profile = {
        "trade_finance": {"available": True, "instruments": [{"code": "LC_IRREVOCABLE"}]},
        "payment_coverage": {"available": True, "papss_covered": True, "shared_systems": [{}]},
        "country_risk": {"available": True, "alert_level": "green"},
        "destination_macro": {"import_cover": {"available": True, "months": 6}},
    }
    res = finance.summarize_financing_feasibility(profile)
    assert res["available"] is True
    assert res["index"] == 1.0  # all four components maxed


def test_financing_feasibility_partial_and_renormalised():
    # Only payment coverage available -> index computed over that single weight.
    profile = {
        "trade_finance": {"available": False},
        "payment_coverage": {"available": True, "papss_covered": False, "shared_systems": []},
        "country_risk": {"available": False},
        "destination_macro": {"import_cover": {"available": False}},
    }
    res = finance.summarize_financing_feasibility(profile)
    assert res["available"] is True
    assert res["index"] == 0.0  # no PAPSS, no shared systems


def test_financing_feasibility_unavailable_when_no_components():
    profile = {
        "trade_finance": {"available": False},
        "payment_coverage": {"available": False},
        "country_risk": {"available": False},
        "destination_macro": {"import_cover": {"available": False}},
    }
    res = finance.summarize_financing_feasibility(profile)
    assert res["available"] is False and res["index"] is None


# ── Logistics-accessibility index (pure, deterministic) ──────────────────────
def test_logistics_accessibility_index():
    profile = {
        "freight": {"available": True, "operational_count": 3},
        "cheapest_operational_option": {"feasibility": "high"},
    }
    res = logistics.summarize_logistics_accessibility(profile)
    assert res["available"] is True
    assert res["index"] == 1.0  # 3 modes (cap) + high feasibility


def test_logistics_accessibility_unavailable():
    res = logistics.summarize_logistics_accessibility({"freight": {"available": False}})
    assert res["available"] is False and res["index"] is None


# ── End-to-end score renormalisation (pure, deterministic) ───────────────────
def test_end_to_end_score_renormalises_over_available():
    components = {
        "market_potential": {"available": False, "subscore": None},
        "supply_capacity": {"available": True, "subscore": 1.0},
        "logistics_accessibility": {"available": True, "subscore": 0.5},
        "financing_feasibility": {"available": False, "subscore": None},
        "country_risk": {"available": False, "subscore": None},
    }
    weights = {
        "market_potential": 0.25,
        "supply_capacity": 0.25,
        "logistics_accessibility": 0.25,
        "financing_feasibility": 0.15,
        "country_risk": 0.10,
    }
    res = report_engine._end_to_end_score(components, weights)
    # (0.25*1.0 + 0.25*0.5) / (0.25 + 0.25) = 0.75
    assert res["available"] is True
    assert res["score"] == 0.75
    assert res["weight_coverage"] == 0.5


def test_end_to_end_score_unavailable_when_nothing_counts():
    components = {"supply_capacity": {"available": False, "subscore": None}}
    res = report_engine._end_to_end_score(components, {"supply_capacity": 0.25})
    assert res["available"] is False and res["score"] is None


# ── Landed cost (pure, deterministic) ────────────────────────────────────────
def test_landed_cost_sums_fob_and_freight():
    res = report_engine._landed_cost(100000.0, 995.0)
    assert res["available"] is True
    assert res["value_usd"] == 100995.0
    assert res["breakdown"]["best_operational_freight_usd"] == 995.0


def test_landed_cost_unavailable_without_freight():
    res = report_engine._landed_cost(100000.0, None)
    assert res["available"] is False and res["value_usd"] is None


# ── Supply component from real production data ────────────────────────────────
def test_supply_component_real_producer():
    # Côte d'Ivoire is the #1 African cocoa producer — deterministic local data.
    comp = report_engine._supply_component("CIV", "1801")
    assert comp["available"] is True
    assert comp["rank"] == 1
    assert comp["subscore"] == 1.0  # dominant continental share


# ── Integration: full report (FX stubbed to stay hermetic) ───────────────────
@pytest.fixture
def _no_network_fx(monkeypatch):
    monkeypatch.setattr(
        finance,
        "get_fx",
        lambda o, d: {
            "available": False,
            "note": "stubbed",
            "origin_currency": None,
            "destination_currency": None,
        },
    )


def test_opportunity_report_structure(_no_network_fx):
    rep = report_engine.get_opportunity_report("1801", "CIV", "NGA", goods_value_usd=50000.0)
    assert rep["report_type"] == "bilateral_product_opportunity"
    ci = rep["composite_indicators"]
    # market potential requires OEC (paid) -> must be excluded, not fabricated
    e2e = ci["end_to_end_score"]
    mp = next(b for b in e2e["breakdown"] if b["component"] == "market_potential")
    assert mp["counted"] is False
    # supply is real and should be counted
    assert rep["supply"]["available"] is True
    assert rep["data_quality"]["is_estimation"] is False


# ── Market-seeking report (demand + supply) ──────────────────────────────────
def test_demand_side_computes_shares():
    importers = [
        {"country_iso3": "NGA", "country_name": "Nigeria", "import_value": 300},
        {"country_iso3": "ZAF", "country_name": "South Africa", "import_value": 100},
    ]
    d = report_engine._demand_side(importers)
    assert d["available"] is True
    assert d["total_import_value_usd"] == 400
    assert d["markets"][0]["share_pct"] == 75.0


def test_demand_side_unavailable_without_oec():
    d = report_engine._demand_side([])
    assert d["available"] is False and d["markets"] == []
    assert "OEC" in d["note"]


def test_supply_side_real_producers():
    s = report_engine._supply_side("1801")  # cocoa
    assert s["available"] is True
    assert any(p["country_iso3"] == "CIV" for p in s["producers"])


def test_oec_token_injected_into_params(monkeypatch):
    from services import real_trade_data_service as rt

    # No token -> params unchanged
    monkeypatch.setattr(rt, "OEC_API_TOKEN", None)
    base = {"cube": "trade_i_baci_a_17", "limit": "1"}
    assert rt._oec_params(base) == base
    assert "token" not in rt._oec_params(base)

    # Token set -> injected as query param, original dict untouched
    monkeypatch.setattr(rt, "OEC_API_TOKEN", "secret-xyz")
    out = rt._oec_params(base)
    assert out["token"] == "secret-xyz"
    assert "token" not in base  # non-mutating


def test_importers_for_product_exact_hs6_all_countries(monkeypatch):
    """Exact HS6 match, aggregation across all countries, non-match excluded."""
    from services import real_trade_data_service as rt

    nga_oec = rt.AFRICAN_COUNTRIES["NGA"]["oec"]
    zaf_oec = rt.AFRICAN_COUNTRIES["ZAF"]["oec"]

    class _Resp:
        status_code = 200

        def __init__(self, data):
            self._data = data

        def json(self):
            return {"data": self._data}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, params=None):
            imp = params.get("Importer Country")
            if imp == nga_oec:
                # one matching HS6 line (prefixed id) + one non-matching line
                return _Resp(
                    [
                        {"HS6 ID": "52180100", "Trade Value": 1000},
                        {"HS6 ID": "180200", "Trade Value": 999},
                    ]
                )
            if imp == zaf_oec:
                return _Resp([{"HS6 ID": "180100", "Trade Value": 500}])
            return _Resp([])

    monkeypatch.setattr(rt.httpx, "AsyncClient", _Client)
    res = asyncio.run(rt.real_trade_service.get_african_importers_for_product("180100"))
    assert [(r["country_iso3"], r["import_value"]) for r in res] == [
        ("NGA", 1000.0),
        ("ZAF", 500.0),
    ]  # sorted desc; non-matching 180200 excluded


def test_market_seeking_report_demand_degrades_supply_real(monkeypatch):
    # Stub the OEC call (network) so demand is deterministically unavailable.
    from services import real_trade_data_service as rt

    async def _empty(hs_code, year=2022):
        return []

    monkeypatch.setattr(rt.real_trade_service, "get_african_importers_for_product", _empty)
    rep = asyncio.run(report_engine.get_market_seeking_report("1801", lang="fr"))
    assert rep["report_type"] == "market_seeking"
    assert rep["demand"]["available"] is False  # OEC blocked -> graceful
    assert rep["supply"]["available"] is True  # local production data
    assert rep["data_quality"]["is_estimation"] is False
