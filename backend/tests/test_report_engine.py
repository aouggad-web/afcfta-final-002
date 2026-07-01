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


# ── Narrative Analysis ──────────────────────────────────────────────────────
def test_narrative_supply_real_producer():
    from services import narrative_analysis_service as narrative

    supply_profile = {
        "available": True,
        "subscore": 0.91,
        "continental_share_pct": 18.2,
        "rank": 1,
        "commodity": "Cocoa beans",
        "source": "FAO PRODSTAT",
        "detail": {"year": 2023, "trend": {"growth_pct_annual": 2.1, "period": "2019–2023"}},
    }
    result = narrative.analyze_supply("CIV", "1801", supply_profile)
    assert result["available"] is True
    assert "1er producteur" in result["narrative"].lower()
    assert "18.2" in result["narrative"]
    assert "2023" in result["narrative"]


def test_narrative_summarize_opportunity():
    from services import narrative_analysis_service as narrative

    report = {
        "composite_indicators": {
            "end_to_end_score": {"available": True, "score": 0.78},
        },
        "supply": {
            "available": True,
            "continental_share_pct": 18.2,
            "rank": 1,
        },
        "demand": {
            "available": True,
            "total_import_value_usd": 840_000_000,
        },
    }
    result = narrative.summarize_opportunity(report)
    assert result["priority_tier"] == "QUICK_WIN"
    assert len(result["key_findings"]) > 0
    assert "Déployer" in result["recommendation"]


# ── Benchmarking Service ─────────────────────────────────────────────────────
def test_benchmark_top_producers(monkeypatch):
    from services import benchmarking_service as benchmark

    # Stub production_capacity_service
    def _mock_continental(hs_code):
        return {
            "available": True,
            "commodity": "Cocoa beans",
            "unit": "tonnes",
            "year": 2023,
            "source": "FAO PRODSTAT",
            "top_producers": [
                {"country_iso3": "CIV", "country_name": "Côte d'Ivoire", "country_share_pct": 18.2},
                {"country_iso3": "GHA", "country_name": "Ghana", "country_share_pct": 16.8},
            ],
        }

    monkeypatch.setattr(
        "services.production_capacity_service.get_continental_producers", _mock_continental
    )
    result = benchmark.get_top_producers("1801", n=2)
    assert result["available"] is True
    assert len(result["producers"]) == 2
    assert result["producers"][0]["country_iso3"] == "CIV"


def test_tariff_benefit_real_rates():
    from services import benchmarking_service as benchmark

    # NGA imports cocoa (180100): national duty 5% -> ZLECAf 0% => real 5% advantage.
    res = benchmark.tariff_benefit_analysis("CIV", "NGA", "180100")
    assert res["available"] is True
    assert res["national_rate_pct"] == 5.0
    assert res["zlecaf_rate_pct"] == 0.0
    assert res["tariff_advantage_pct"] == 5.0
    # Must NOT be the old hardcoded 8.5%
    assert res["tariff_advantage_pct"] != 8.5


def test_tariff_benefit_zero_when_no_duty():
    from services import benchmarking_service as benchmark

    # EGY rice (100630): national duty already 0% => no ZLECAf advantage.
    res = benchmark.tariff_benefit_analysis("SEN", "EGY", "100630")
    assert res["available"] is True
    assert res["tariff_advantage_pct"] == 0.0


def test_segmentation_no_fabricated_tariff_when_unavailable():
    from services import segmentation_service as segmentation

    # No tariff_benefit in report -> tariff factor must be absent (not a fake 8.5%).
    report = {
        "supply": {"available": True, "continental_share_pct": 18.2, "subscore": 0.91},
    }
    factors = segmentation.factor_breakdown(report)
    assert not any(f["factor"] == "tariff_advantage" for f in factors)


def test_benchmark_cost_competitive():
    from services import benchmarking_service as benchmark

    result = benchmark.benchmark_cost("CIV", "1801", "NGA", landed_cost_usd=100000)
    assert result["available"] is True
    assert result["position"] == "best"
    assert "leader" in result["narrative"].lower()


# ── Segmentation Service ─────────────────────────────────────────────────────
def test_effort_impact_matrix_quick_win():
    from services import segmentation_service as segmentation

    report = {
        "inputs": {"goods_value_usd": 100000},
        "composite_indicators": {
            "landed_cost": {"breakdown": {"best_operational_freight_usd": 1200}}
        },
        "demand": {"available": True, "total_import_value_usd": 500_000_000},
    }
    result = segmentation.effort_impact_matrix(report)
    assert result["effort_score"] < 0.4
    assert result["impact_score"] > 0.6
    assert result["quadrant"] == "quick_win"


def test_risk_reward_matrix_ideal_corridor():
    from services import segmentation_service as segmentation

    report = {
        "composite_indicators": {
            "financing_feasibility_index": {"available": True, "index": 0.75},
            "end_to_end_score": {"available": True, "score": 0.78},
        },
        "finance": {"country_risk": {"available": True, "risk_score": 3.5, "alert_level": "green"}},
        "supply": {"available": True, "subscore": 0.9},
        "demand": {"available": True, "total_import_value_usd": 500_000_000},
    }
    result = segmentation.risk_reward_matrix(report)
    assert result["risk_score"] < 0.4
    assert result["reward_score"] > 0.7
    assert result["quadrant"] == "ideal_corridor"


def test_factor_breakdown_opportunities_and_risks():
    from services import segmentation_service as segmentation

    report = {
        "supply": {"available": True, "continental_share_pct": 18.2, "subscore": 0.91},
        "demand": {"available": True, "total_import_value_usd": 500_000_000},
        "composite_indicators": {
            "logistics_accessibility_index": {"available": True, "index": 0.82},
            "financing_feasibility_index": {"available": True, "index": 0.73},
        },
        "finance": {
            "country_risk": {"available": True, "alert_level": "orange", "risk_score": 6.2}
        },
    }
    factors = segmentation.factor_breakdown(report)
    opps = [f for f in factors if f["category"] == "opportunity"]
    risks = [f for f in factors if f["category"] == "risk"]
    assert len(opps) > 0
    assert len(risks) > 0


def test_opportunity_report_ultra_fine(_no_network_fx):
    """Ultra-fine report includes narrative, benchmarking, segmentation."""
    rep = report_engine.get_opportunity_report_ultra_fine(
        "1801", "CIV", "NGA", goods_value_usd=50000.0
    )

    # Base report fields
    assert rep["report_type"] == "bilateral_product_opportunity"
    assert rep["report_tier"] == "ultra_fine"

    # Executive summary
    assert "executive_summary" in rep
    assert rep["executive_summary"]["priority_tier"] is not None

    # Narrative analysis
    assert "narrative_analysis" in rep
    assert rep["narrative_analysis"].get("supply", {}).get("available") is not None

    # Benchmarking
    assert "benchmarking" in rep
    assert "top_producers" in rep["benchmarking"]

    # Segmentation
    assert "segmentation" in rep
    assert "effort_impact_matrix" in rep["segmentation"]
    assert "risk_reward_matrix" in rep["segmentation"]
    assert "factor_breakdown" in rep["segmentation"]
    assert len(rep["segmentation"]["factor_breakdown"]) > 0

    # National need (S3) wired into the report + narrative + exec finding
    assert "national_need" in rep
    nn = rep["national_need"]
    assert nn["available"] is True  # NGA cocoa -> L2 estimate from real data
    assert nn["is_estimation"] is True
    assert rep["narrative_analysis"]["national_need"]["available"] is True
    assert any("Besoin du marché" in f for f in rep["executive_summary"]["key_findings"])


# ── National-need estimation (S3, transparent cascade) ───────────────────────
def test_population_is_real_from_constants():
    from services import demand_estimation_service as demand

    pop = demand.get_population("NGA")
    assert pop["available"] is True
    assert pop["value"] > 100_000_000  # Nigeria
    assert pop["region"]


def test_national_need_level2_population_proxy():
    from services import demand_estimation_service as demand

    # No apparent consumption -> L2 estimate from real FAO production + population.
    res = demand.estimate_national_need("180100", "NGA")  # cocoa
    assert res["available"] is True
    assert res["is_estimation"] is True
    assert res["estimation_level"] == 2  # GDP dataset absent here -> stays L2
    assert res["value"] > 0
    assert res["unit"] == "tonnes"
    # Transparency: formula + inputs + sources are exposed
    assert "Population ×" in res["method"]
    assert res["inputs"]["population"] > 0
    assert res["inputs"]["continental_production"] > 0
    assert res["inputs"]["per_capita_reference"] > 0
    assert len(res["sources"]) >= 2


def test_national_need_level1_measured_when_apparent_given():
    from services import demand_estimation_service as demand

    res = demand.estimate_national_need(
        "180100",
        "NGA",
        apparent={"production": 720000, "imports": 50000, "exports": 600000, "unit": "tonnes"},
    )
    assert res["is_estimation"] is False  # measured, not modelled
    assert res["estimation_level"] == 1
    assert res["value"] == 170000.0  # 720000 + 50000 - 600000


def test_national_need_reference_includes_imports():
    from services import demand_estimation_service as demand

    # Same product, with vs without continental imports in the per-capita reference.
    base = demand.estimate_national_need("180100", "NGA")
    enriched = demand.estimate_national_need("180100", "NGA", continental_imports_tonnes=1_000_000)
    assert base["reference_basis"] == "production_only"
    assert enriched["reference_basis"] == "production_plus_imports"
    # Adding imports raises the per-capita availability -> higher estimated need.
    assert enriched["value"] > base["value"]
    assert "importations" in enriched["method"]


def test_national_need_attaches_observed_imports():
    from services import demand_estimation_service as demand

    signal = {"import_value_usd": 840_000_000, "source": "OEC / UN Comtrade (BACI)"}
    res = demand.estimate_national_need("180100", "NGA", observed_imports=signal)
    assert res["observed_imports"] == signal  # direct demand signal surfaced


def test_national_need_unavailable_without_production():
    from services import demand_estimation_service as demand

    # Unknown HS -> no continental production -> estimate unavailable, never invented.
    res = demand.estimate_national_need("999999", "NGA")
    assert res["available"] is False
    assert res["value"] is None


def test_gdp_per_capita_degrades_gracefully():
    from services import demand_estimation_service as demand

    # wb_gdp_pc.json not shipped (WB API blocked here) -> unavailable, no fabrication.
    gdp = demand.get_gdp_per_capita("NGA")
    assert gdp["available"] is False and gdp["value_usd"] is None


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
