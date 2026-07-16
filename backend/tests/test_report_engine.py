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


def test_fx_reserves_and_import_cover_degrade_gracefully_without_dataset(monkeypatch):
    # When wb_reserves.json is absent, the accessors flag unavailable and never
    # invent a number (deterministic: force the dataset empty).
    monkeypatch.setattr(macro, "_WB_RESERVES", None)
    monkeypatch.setattr(macro, "_wb_reserves", lambda: None)
    fx = macro.get_fx_reserves("NGA")
    cover = macro.get_import_cover("NGA")
    assert fx["available"] is False and fx["value_busd"] is None
    assert cover["available"] is False and cover["months"] is None
    assert fx["indicator"] == macro.WB_FX_RESERVES_INDICATOR
    assert cover["indicator"] == macro.WB_IMPORT_COVER_INDICATOR


def test_fx_reserves_and_import_cover_available_from_committed_dataset():
    # data/json/wb_reserves.json is now committed (real WB data via the workflow):
    # FX reserves and import cover must be available for a covered country.
    fx = macro.get_fx_reserves("DZA")
    cover = macro.get_import_cover("DZA")
    assert fx["available"] is True and fx["value_busd"] > 0
    assert cover["available"] is True and cover["months"] > 0


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
def test_landed_cost_sums_fob_freight_and_insurance():
    res = report_engine._landed_cost(100000.0, 995.0)
    assert res["available"] is True
    assert res["breakdown"]["best_operational_freight_usd"] == 995.0
    # Assurance cargo estimée : 0,5 % × 110 % × (FOB + fret), toujours flaggée.
    insurance = res["components"]["insurance"]
    assert insurance["is_estimation"] is True
    assert insurance["premium_usd"] == round(100995.0 * 1.1 * 0.005, 2)
    # Sans trade finance fourni, les frais bancaires sont exclus (pas inventés).
    assert res["components"]["trade_finance"]["available"] is False
    assert res["breakdown"]["trade_finance_fee_usd"] is None
    assert res["value_usd"] == round(100995.0 + insurance["premium_usd"], 2)


def test_landed_cost_adds_recommended_instrument_fee():
    trade_finance = {
        "available": True,
        "instruments": [
            {"code": "LC_IRREVOCABLE", "name_fr": "Crédit Documentaire", "typical_cost_pct": 1.5},
            {"code": "DOC_COLLECTION_DP", "name_fr": "Remise D/P", "typical_cost_pct": 0.5},
        ],
    }
    res = report_engine._landed_cost(100000.0, 995.0, trade_finance=trade_finance)
    tf = res["components"]["trade_finance"]
    # Le PREMIER instrument recommandé (le mieux adapté) est facturé, en % du FOB.
    assert tf["available"] is True and tf["instrument_code"] == "LC_IRREVOCABLE"
    assert tf["fee_usd"] == 1500.0
    assert res["breakdown"]["trade_finance_fee_usd"] == 1500.0
    insurance_usd = res["components"]["insurance"]["premium_usd"]
    assert res["value_usd"] == round(100995.0 + insurance_usd + 1500.0, 2)


def test_landed_cost_surfaces_container_port_fees_without_double_count():
    shipment = {"available": True, "containers_needed": 3, "container_type": "teu"}
    cheapest = {
        "mode": "sea",
        "port_fees": {
            "origin_thc_usd": 150,
            "destination_thc_usd": 200,
            "total_usd": 350,
            "basis": "per_container",
            "included_in_freight": True,
        },
    }
    res = report_engine._landed_cost(100000.0, 1000.0, shipment, cheapest)
    pf = res["components"]["port_fees"]
    # THC × nombre de conteneurs, décomposés chargement / déchargement…
    assert pf["available"] is True and pf["total_usd"] == 1050.0
    assert pf["loading_usd"] == 450.0 and pf["discharge_usd"] == 600.0
    assert pf["included_in_freight"] is True
    bd = res["breakdown"]
    assert bd["port_fees_loading_usd"] == 450.0
    assert bd["port_fees_discharge_usd"] == 600.0
    # …le fret est aussi exposé HORS frais portuaires (lignes additives)…
    assert bd["freight_excl_port_fees_usd"] == round(3000.0 - 1050.0, 2)
    # …et JAMAIS ré-additionnés : total = FOB + fret(×3) + assurance seulement.
    insurance_usd = res["components"]["insurance"]["premium_usd"]
    assert res["value_usd"] == round(100000.0 + 3000.0 + insurance_usd, 2)


def test_landed_cost_port_fees_unavailable_for_other_modes():
    res = report_engine._landed_cost(100000.0, 995.0, None, {"mode": "road"})
    assert res["components"]["port_fees"]["available"] is False
    assert res["breakdown"]["port_fees_included_usd"] is None


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


def test_market_component_normalisation():
    # 100 M$ imports -> subscore 1.0 ; unavailable stays excluded (no fabrication).
    full = report_engine._market_component({"available": True, "import_value_usd": 100_000_000})
    assert full["available"] is True and full["subscore"] == 1.0
    half = report_engine._market_component({"available": True, "import_value_usd": 50_000_000})
    assert half["subscore"] == 0.5
    assert report_engine._market_component(None)["available"] is False


def test_market_potential_counts_in_score_when_provided(_no_network_fx):
    # With OEC market imports injected, market_potential is counted in the E2E score.
    rep = report_engine.get_opportunity_report(
        "1801",
        "CIV",
        "NGA",
        goods_value_usd=50000.0,
        market_imports={"available": True, "import_value_usd": 80_000_000},
    )
    e2e = rep["composite_indicators"]["end_to_end_score"]
    mp = next(b for b in e2e["breakdown"] if b["component"] == "market_potential")
    assert mp["counted"] is True
    assert mp["subscore"] == 0.8
    assert rep["market_potential"]["available"] is True


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
    # Sans importations observées du marché cible, aucun tonnage n'est inventé.
    assert "MT/mois" not in result["recommendation"]


def _quick_win_report(hs_code, annual_import_usd):
    return {
        "composite_indicators": {"end_to_end_score": {"available": True, "score": 0.8}},
        "inputs": {"hs_code": hs_code},
        "national_need": {
            "available": True,
            "observed_imports": {"import_value_usd": annual_import_usd, "source": "OEC"},
        },
    }


def test_narrative_phase1_volume_scales_with_product_value():
    # L'ancienne recommandation codait en dur « 200–500 MT/mois » quel que soit
    # le produit : 500 MT/mois de médicaments (~60 USD/kg) = 30 M$/mois, absurde
    # pour un corridor bilatéral (cas signalé : SH 300490 Algérie → Sénégal).
    from services import narrative_analysis_service as narrative

    pharma = narrative.summarize_opportunity(_quick_win_report("300490", 400_000_000))
    potatoes = narrative.summarize_opportunity(_quick_win_report("070190", 400_000_000))

    assert "200–500 MT/mois" not in pharma["recommendation"]
    assert "Estimation de dimensionnement" in pharma["recommendation"]

    def _mt_upper(reco):
        import re

        m = re.search(r"([\d.]+)–([\d.]+) MT/mois", reco)
        assert m, reco
        return float(m.group(2))

    # À valeur d'importation égale, le tonnage cible des médicaments doit être
    # ~60× plus faible que celui des pommes de terre (ratio USD/kg 60 vs 1).
    assert _mt_upper(pharma["recommendation"]) < _mt_upper(potatoes["recommendation"]) / 10


def test_narrative_phase1_volume_derived_from_observed_demand():
    from services import narrative_analysis_service as narrative

    result = narrative.summarize_opportunity(_quick_win_report("300490", 400_000_000))
    reco = result["recommendation"]
    # 10 % de 400 M$/an = 3,3 M$/mois ; à ~60 USD/kg → ~56 MT/mois maximum.
    assert "MT/mois" in reco
    assert "5–10 %" in reco
    assert "importations annuelles observées" in reco


def test_narrative_phase1_no_tonnage_without_demand_data():
    from services import narrative_analysis_service as narrative

    report = {
        "composite_indicators": {"end_to_end_score": {"available": True, "score": 0.9}},
        "inputs": {"hs_code": "300490"},
    }
    result = narrative.summarize_opportunity(report)
    assert result["priority_tier"] == "QUICK_WIN"
    assert "MT/mois" not in result["recommendation"]
    assert "demande réelle" in result["recommendation"]


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


def test_tariff_hs4_resolves_to_hs6():
    from services import benchmarking_service as benchmark

    # HS4 "1801" must resolve to a real HS6 sub-heading and return the real tariff.
    hs6, resolved = benchmark._resolve_hs6("NGA", "1801")
    assert hs6 == "180100" and resolved is True
    res = benchmark.tariff_benefit_analysis("CIV", "NGA", "1801")
    assert res["available"] is True
    assert res["hs6_used"] == "180100"
    assert res["hs6_resolved"] is True
    assert res["tariff_advantage_pct"] == 5.0


def test_tariff_dza_no_zlecaf_for_non_active_partner():
    from services import benchmarking_service as benchmark

    # L'Algérie n'accorde les taux ZLECAf qu'à ses 9 partenaires actifs
    # (réciprocité, circulaire DGD 482/2024). GNB n'en fait pas partie :
    # cajou 080131 -> taux NPF 30 %, avantage NUL (régression corrigée :
    # le rapport affichait 30 % -> 0 %).
    res = benchmark.tariff_benefit_analysis("GNB", "DZA", "080131")
    assert res["available"] is True
    assert res["national_rate_pct"] == 30.0
    assert res["zlecaf_rate_pct"] == 30.0
    assert res["tariff_advantage_pct"] == 0.0
    assert res["tariff_advantage_index"] == 0.0
    assert res["trade_regime"] == "NPF"
    assert "non encore activé" in (res["trade_regime_note"] or "")


def test_tariff_dza_zlecaf_for_active_partner():
    from services import benchmarking_service as benchmark

    # EGY est un partenaire actif de l'Algérie : le calendrier de
    # démantèlement DZA s'applique (liste A, calendrier standard -> 0 % dès
    # 2025), exactement comme dans le calculateur.
    res = benchmark.tariff_benefit_analysis("EGY", "DZA", "080131")
    assert res["available"] is True
    assert res["trade_regime"] == "ZLECAF"
    assert res["national_rate_pct"] == 30.0
    assert res["zlecaf_rate_pct"] == 0.0
    assert res["tariff_advantage_pct"] == 30.0


def test_tariff_customs_union_pair():
    from services import benchmarking_service as benchmark

    # BFA et CIV sont tous deux UEMOA : libre circulation (0 %), régime
    # prioritaire sur la ZLECAf.
    res = benchmark.tariff_benefit_analysis("BFA", "CIV", "180100")
    assert res["available"] is True
    assert res["trade_regime"] == "CUSTOMS_UNION"
    assert res["zlecaf_rate_pct"] == 0.0
    assert res["tariff_advantage_pct"] == res["national_rate_pct"]


def test_segmentation_tariff_factor_gives_real_reason_when_no_advantage():
    from services import segmentation_service as segmentation

    report = {
        "tariff_benefit": {
            "available": True,
            "tariff_advantage_pct": 0.0,
            "tariff_advantage_index": 0.0,
            "national_rate_pct": 30.0,
            "zlecaf_rate_pct": 30.0,
            "trade_regime": "NPF",
            "trade_regime_note": (
                "ZLECAf non encore activé pour GNB à l'import en Algérie "
                "(circulaire DGD 482/2024) — taux NPF appliqué"
            ),
        }
    }
    factors = segmentation.factor_breakdown(report)
    tf = next(f for f in factors if f["factor"] == "tariff_advantage")
    assert tf["category"] == "neutral"
    assert "non encore activé" in tf["rationale"]


def test_gdp_per_capita_falls_back_to_country_profiles(monkeypatch):
    """Sans dataset ETL wb_gdp_pc.json, le PIB/hab vient du module Profils
    Pays (country_data.REAL_COUNTRY_DATA, déjà embarqué) — L3 marche sans réseau."""
    from services import demand_estimation_service as d

    # Simule l'absence du dataset ETL -> repli sur les Profils Pays.
    monkeypatch.setattr(d, "_load_gdp", lambda: {})
    res = d.get_gdp_per_capita("DZA")
    assert res["available"] is True
    assert res["value_usd"] > 0
    assert "Profils Pays" in res["source"]


def test_gdp_per_capita_prefers_etl_when_present(monkeypatch):
    """Le dataset ETL, s'il est présent, prime sur le repli Profils Pays."""
    from services import demand_estimation_service as d

    monkeypatch.setattr(d, "_load_gdp", lambda: {"DZA": {"value": 9999.0, "year": 2025}})
    res = d.get_gdp_per_capita("DZA")
    assert res["value_usd"] == 9999.0
    assert "WDI NY.GDP.PCAP.CD" in res["source"]


def test_intra_african_context_real_afreximbank():
    """Le contexte commerce intra-africain (Afreximbank ATR 2026) est branché
    dans le rapport bilatéral pour origine + destination — données réelles."""
    from services import report_engine

    ctx = report_engine.get_intra_african_context("CIV", "NGA")
    assert ctx["available"] is True
    assert "Afreximbank" in ctx["source"]
    # Origine et destination couvertes, avec valeurs réelles et tendance calculée.
    for side in (ctx["origin"], ctx["destination"]):
        assert side["available"] is True
        iat = side["intra_african_trade"]
        assert iat["value_2025_busd"] > 0
        assert iat["share_2025_pct"] > 0
        assert iat["growth_2021_2025_pct"] is not None  # calculée depuis la série 5 ans
    # Contexte continental réel exposé.
    assert ctx["continental_2025"]["intra_african_trade_busd"] > 0


def test_intra_african_context_degrades_for_uncovered_country():
    from services import report_engine

    ctx = report_engine.get_intra_african_context("CIV", "ZZZ")
    assert ctx["origin"]["available"] is True
    assert ctx["destination"]["available"] is False  # jamais fabriqué


def test_african_importers_use_free_stats_channel(monkeypatch):
    """Le fan-out 54 pays est remplacé par UNE requête sur le canal OEC
    gratuit du module Statistiques (aucun token requis)."""
    from services.real_trade_data_service import real_trade_service

    async def fake_importers(hs_code, year, limit=54):
        assert hs_code == "180100"
        return {
            "data": [
                {
                    "country_iso3": "NGA",
                    "country_name": "Nigéria",
                    "hs_code": "180100",
                    "import_value": 9_000_000.0,
                },
                {
                    "country_iso3": "EGY",
                    "country_name": "Égypte",
                    "hs_code": "180100",
                    "import_value": 4_000_000.0,
                },
            ],
            "source": "OEC/BACI (canal gratuit du module Statistiques)",
        }

    monkeypatch.setattr(
        "services.oec_trade_service.oec_service.get_top_african_importers", fake_importers
    )
    rows = asyncio.run(real_trade_service.get_african_importers_for_product("180100"))
    assert [r["country_iso3"] for r in rows] == ["NGA", "EGY"]
    assert rows[0]["import_value"] == 9_000_000.0


def test_african_importers_fall_back_to_fanout(monkeypatch):
    """Canal gratuit indisponible -> repli sur le fan-out historique."""
    from services import real_trade_data_service as rt

    async def broken(hs_code, year, limit=54):
        raise RuntimeError("free channel down")

    monkeypatch.setattr("services.oec_trade_service.oec_service.get_top_african_importers", broken)

    class _Resp:
        status_code = 200

        def json(self):
            return {"data": [{"HS6 ID": "1180100", "Trade Value": 777.0}]}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(rt.httpx, "AsyncClient", _Client)
    rows = asyncio.run(rt.real_trade_service.get_african_importers_for_product("180100"))
    assert rows and all(r["import_value"] == 777.0 for r in rows)


def test_list_tracked_products_deduped_with_data():
    from services import production_capacity_service as pcs

    products = pcs.list_tracked_products()
    assert len(products) >= 20
    # Dédupliqué par commodity/dataset (le cacao a 6 préfixes HS -> 1 entrée).
    keys = [(p["dataset"], p["commodity"]) for p in products]
    assert len(keys) == len(set(keys))
    # Chaque entrée a des données réelles derrière (producteurs continentaux).
    sample = products[0]
    assert pcs.get_continental_producers(sample["hs_code"])["available"] is True


def test_import_opportunities_scenario_dza():
    """S4 — miroir de S2 côté import : produits classés pour un pays, avec le
    fournisseur choisi par régime préférentiel RÉEL (réciprocité algérienne)."""
    from services import report_engine

    rep = report_engine.get_import_opportunities_scenario("DZA", top_k=3)
    assert rep["scenario"] == "S4_best_imports_for_country"
    assert rep["products_scanned"] >= 20
    opps = rep["ranked_opportunities"]
    assert len(opps) == 3

    for o in opps:
        # Jamais le pays lui-même en fournisseur.
        assert all(s["country_iso3"] != "DZA" for s in o["suppliers_considered"])
        # Le besoin est une estimation étiquetée, jamais fabriquée.
        assert o["market_need"]["available"] is True
        # Production locale absente du référentiel = étiquetée, pas un zéro mesuré.
        if not o["local_production"]["recorded"]:
            assert o["unmet_need_note"] is not None
        # Le régime tarifaire du fournisseur vient du moteur du calculateur.
        assert o["best_supplier"]["trade_regime"] in (
            "ZLECAF",
            "CUSTOMS_UNION",
            "NPF",
            "FTA_CONDITIONAL",
            None,
        )

    # Classement final par score (desc) comme S2.
    scores = [o["end_to_end_score"] or 0 for o in opps]
    assert scores == sorted(scores, reverse=True)


def test_import_opportunities_supplier_prefers_real_tariff_regime():
    """Pour l'Algérie, un fournisseur partenaire ZLECAf actif (avantage réel)
    doit être préféré à un producteur plus gros au taux NPF, à produit égal."""
    from services import report_engine

    rep = report_engine.get_import_opportunities_scenario("DZA", top_k=8)
    by_hs = {o["hs_code"]: o for o in rep["ranked_opportunities"]}
    tea = by_hs.get("0902")
    if tea is None:  # le thé peut sortir du top_k si les données évoluent
        return
    advs = {
        s["country_iso3"]: (s["tariff_advantage_pct"] or 0) for s in tea["suppliers_considered"]
    }
    best = tea["best_supplier"]["country_iso3"]
    assert advs[best] == max(advs.values())


def test_country_product_imports_uses_stats_channel(monkeypatch):
    """Le module Opportunités lit les imports OEC via le MÊME canal que la
    recherche SH2/4/6 du module Statistiques (cache persistant partagé)."""
    import asyncio

    from services.real_trade_data_service import real_trade_service

    async def fake_history(**kwargs):
        assert kwargs["country_iso3"] == "DZA"
        assert kwargs["level"] == "hs6"
        return {
            "chart_rows": [
                {"year": 2022, "exports": 0, "imports": 500000.0},
                {"year": 2024, "exports": 0, "imports": 750000.0},
                {"year": 2023, "exports": 0, "imports": 0},
            ],
            "source": "OEC / BACI (HS Rev. 2017)",
        }

    monkeypatch.setattr(
        "services.oec_trade_service.oec_service.get_country_hs6_history", fake_history
    )
    res = asyncio.run(real_trade_service.get_country_product_imports("DZA", "080131"))
    assert res["available"] is True
    # Dernière année avec des imports observés (2023 = 0 est sautée).
    assert res["import_value_usd"] == 750000.0
    assert res["year"] == 2024
    assert "Statistiques" in res["channel"]


def test_country_product_imports_falls_back_to_direct(monkeypatch):
    """Si le canal Statistiques est indisponible, repli sur la requête OEC
    directe historique — jamais de valeur fabriquée."""
    import asyncio

    from services import real_trade_data_service as rt

    async def broken_history(**kwargs):
        raise RuntimeError("stats channel down")

    monkeypatch.setattr(
        "services.oec_trade_service.oec_service.get_country_hs6_history", broken_history
    )

    class _Resp:
        status_code = 200

        def json(self):
            return {"data": [{"HS6 ID": "1080131", "Trade Value": 1234.0}]}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            return _Resp()

    monkeypatch.setattr(rt.httpx, "AsyncClient", _Client)
    res = asyncio.run(rt.real_trade_service.get_country_product_imports("DZA", "080131"))
    assert res["available"] is True
    assert res["import_value_usd"] == 1234.0


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


def test_national_need_level2_population_proxy(monkeypatch):
    from services import demand_estimation_service as demand

    # Force GDP unavailable (no ETL dataset, no profiles) -> L2 population proxy.
    monkeypatch.setattr(demand, "_load_gdp", lambda: {})
    monkeypatch.setattr(demand, "_gdp_from_country_profiles", lambda iso: None)
    monkeypatch.setattr(demand, "_gdp_values_map", lambda: {})
    res = demand.estimate_national_need("180100", "NGA")  # cocoa
    assert res["available"] is True
    assert res["is_estimation"] is True
    assert res["estimation_level"] == 2  # GDP unavailable -> stays L2
    assert res["value"] > 0
    assert res["unit"] == "tonnes"
    # Transparency: formula + inputs + sources are exposed
    assert "Population ×" in res["method"]
    assert res["inputs"]["population"] > 0
    assert res["inputs"]["continental_production"] > 0
    assert res["inputs"]["per_capita_reference"] > 0
    assert len(res["sources"]) >= 2


def test_national_need_level3_from_country_profiles(monkeypatch):
    from services import demand_estimation_service as demand

    # No ETL dataset, but the Country Profiles module supplies GDP/capita for all
    # 54 countries -> L3 standard-of-living adjustment activates without network.
    monkeypatch.setattr(demand, "_load_gdp", lambda: {})
    res = demand.estimate_national_need("180100", "NGA")
    assert res["available"] is True
    assert res["estimation_level"] == 3
    assert "PIB/hab_pays" in res["method"]
    assert any("Profils Pays" in s for s in res["sources"])


def test_national_need_suggests_supplier():
    from services import demand_estimation_service as demand

    # NGA cocoa -> suggested supplier is the #1 African producer (CIV), not NGA.
    res = demand.estimate_national_need("180100", "NGA")
    assert res["suggested_supplier"]["iso3"] == "CIV"


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


# ── Méthode affinée (cas signalé : ETH ~3,7 Md$ « niveau 3 » sans garde-fous) ──


def test_national_need_gdp_average_is_population_weighted():
    from services import demand_estimation_service as demand

    idx = {
        "BIG": {"population": 100_000_000},  # grand pays pauvre
        "RICH": {"population": 1_000_000},  # petit pays riche
    }
    gdp_map = {"BIG": 1_000.0, "RICH": 20_000.0}
    weighted = demand._weighted_continental_gdp_avg(gdp_map, idx)
    simple = (1_000.0 + 20_000.0) / 2  # ancien calcul
    # Pondérée population ≈ 1 188 $ ; la moyenne simple (10 500 $) écrasait le
    # facteur des grands pays peuplés à faible revenu.
    assert weighted < 1_500
    assert weighted < simple / 5


def test_national_need_elasticity_resolved_by_product_class():
    from services import demand_estimation_service as demand

    assert demand.income_elasticity_for_hs("100510")["value"] == 0.3  # maïs (base)
    assert demand.income_elasticity_for_hs("300490")["value"] == 0.9  # pharma
    assert demand.income_elasticity_for_hs("852872")["value"] == 1.2  # TV (durable)
    assert demand.income_elasticity_for_hs("610910")["value"] == 0.8  # habillement
    # Chapitre non mappé -> défaut, classe explicitée
    fallback = demand.income_elasticity_for_hs("990000")
    assert fallback["value"] == demand.DEFAULT_INCOME_ELASTICITY
    # Surcharge explicite de l'appelant respectée
    res = demand.estimate_national_need("300490", "ETH", income_elasticity=0.5)
    if res.get("available") and res["estimation_level"] == 3:
        assert res["inputs"]["income_elasticity"] == 0.5


def test_national_need_sector_scope_is_explicit():
    from services import demand_estimation_service as demand

    # SH 340111 (savon) ne matche qu'au chapitre -> le besoin estimé couvre tout
    # le secteur « chimie », ce qui doit être dit, pas laissé passer pour le
    # besoin du seul produit.
    res = demand.estimate_national_need("340111", "ETH")
    assert res["available"] is True
    assert res["reference_scope"] == "secteur (chapitre SH2)"
    assert "secteur" in res["note"]


def test_national_need_propagates_partial_coverage_caveat():
    from services import demand_estimation_service as demand

    # Pharma HS 30 : référence UNIDO couvrant 1 pays africain seulement — le
    # caveat de la donnée de référence doit remonter dans l'estimation.
    res = demand.estimate_national_need("300490", "ETH")
    assert res["available"] is True
    assert res["reference_coverage_caveat"]
    assert "COUVERTURE PARTIELLE" in res["note"]


def test_national_need_floored_by_observed_imports():
    from services import demand_estimation_service as demand

    base = demand.estimate_national_need("300490", "ETH")
    assert base["available"] is True
    huge_imports = float(base["value"]) * 10
    res = demand.estimate_national_need(
        "300490",
        "ETH",
        observed_imports={"import_value_usd": huge_imports, "year": 2023, "source": "OEC"},
    )
    # Le proxy en dessous d'un flux réel mesuré est démenti par lui -> plancher.
    assert res["calibration"] and res["calibration"]["applied"] is True
    assert res["value"] == demand._round_sig(huge_imports, 3)
    assert "recalé au plancher" in res["method"]


def test_national_need_observed_imports_below_estimate_no_floor():
    from services import demand_estimation_service as demand

    res = demand.estimate_national_need(
        "340111",
        "ETH",
        observed_imports={"import_value_usd": 1_000.0, "year": 2023, "source": "OEC"},
    )
    # Importations observées inférieures à l'estimation : pas de recalage
    # (plancher seulement, jamais plafond), signal conservé à part.
    assert res["available"] is True
    assert not res.get("calibration")
    assert res["observed_imports"]["import_value_usd"] == 1_000.0


def test_national_need_value_honest_rounding():
    from services import demand_estimation_service as demand

    assert demand._round_sig(3_694_915_962.13, 3) == 3_690_000_000.0
    assert demand._round_sig(0.0, 3) == 0.0
    res = demand.estimate_national_need("340111", "ETH")
    # Jamais plus de 3 chiffres significatifs sur une valeur modélisée.
    assert res["value"] == demand._round_sig(res["value"], 3)


def test_narrative_national_need_relays_sector_scope_and_caveat():
    from services import demand_estimation_service as demand
    from services import narrative_analysis_service as narrative

    need = demand.estimate_national_need("300490", "ETH")
    out = narrative.analyze_national_need("ETH", need)
    assert out["available"] is True
    assert "secteur" in out["narrative"]
    assert "couverture partielle" in out["narrative"]


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

    # An unknown country (no ETL dataset entry, no Country-Profiles entry) ->
    # unavailable, never fabricated.
    gdp = demand.get_gdp_per_capita("ZZZ")
    assert gdp["available"] is False and gdp["value_usd"] is None


# ── Scenario S1: import inputs → production → export ─────────────────────────
# ── Copilot review fixes (anti-regression) ──────────────────────────────────
def test_financing_narrative_available_without_top_level_flag():
    from services import narrative_analysis_service as narrative

    # get_finance_profile has no top-level 'available' — narrative must still work.
    profile = {
        "trade_finance": {"available": True, "instruments": [{"code": "LC"}]},
        "payment_coverage": {"available": True, "papss_covered": True},
        "country_risk": {"available": False},
        "fx": {"available": False},
    }
    res = narrative.analyze_financing("NGA", profile)
    assert res["available"] is True
    assert "Trade finance" in res["narrative"]


def test_logistics_narrative_uses_transit_days():
    from services import narrative_analysis_service as narrative

    profile = {
        "freight": {"available": True, "options": [{"available": True}, {"available": True}]},
        "cheapest_operational_option": {
            "mode": "sea",
            "total_cost_usd": 1200,
            "transit_days_min": 5,
            "transit_days_max": 7,
        },
        "free_zones": {"zones": []},
    }
    res = narrative.analyze_logistics("CIV", "NGA", profile)
    assert "5–7 jours" in res["narrative"]


def test_effort_impact_matrix_handles_none_goods_value():
    from services import segmentation_service as segmentation

    # goods_value_usd present but None must not raise (TypeError guard).
    report = {"inputs": {"goods_value_usd": None}, "composite_indicators": {}}
    res = segmentation.effort_impact_matrix(report)
    assert res["effort_score"] == 0.5  # neutral fallback, no crash


def test_factor_breakdown_no_fabricated_fx_spread():
    from services import segmentation_service as segmentation

    # fx available but no spread -> fx_volatility factor must be ABSENT (no default 2%).
    report = {"finance": {"profile": {"fx": {"available": True, "rate": 1600}}}}
    factors = segmentation.factor_breakdown(report)
    assert not any(f["factor"] == "fx_volatility" for f in factors)


def test_benchmark_cost_non_leader_unavailable():
    from services import benchmarking_service as benchmark

    # Ghana is not the #1 cocoa producer (CIV is) -> numeric gap must be unavailable,
    # not a fabricated heuristic.
    res = benchmark.benchmark_cost("GHA", "1801", "NGA", landed_cost_usd=100000)
    assert res["available"] is False
    assert res.get("gap_pct") is None


def test_direct_export_scenario_ranks_markets(_no_network_fx):
    # CIV produces cocoa (1801) -> rank candidate export markets.
    rep = report_engine.get_direct_export_scenario(
        "1801",
        "CIV",
        candidate_destinations=["NGA", "EGY", "ZAF"],
        top_k=3,
        goods_value_usd=50000.0,
    )
    assert rep["report_type"] == "value_chain_direct_export"
    assert rep["scenario"] == "S2_produce_export_direct"
    assert rep["producer_supply"]["available"] is True  # CIV is a real cocoa producer
    opps = rep["ranked_opportunities"]
    assert len(opps) == 3
    # Producer must never appear as its own destination
    assert all(o["destination_iso3"] != "CIV" for o in opps)
    # Each opportunity carries a real bilateral landed cost + tariff block
    assert all("landed_cost" in o and "tariff_benefit" in o for o in opps)
    # Ranking is by export score desc (None treated as 0)
    scores = [o["end_to_end_score"] or 0 for o in opps]
    assert scores == sorted(scores, reverse=True)


def test_direct_export_empty_candidates_stays_empty():
    # Explicit empty list must NOT fall back to the full 54-market set.
    rep = report_engine.get_direct_export_scenario("1801", "CIV", candidate_destinations=[])
    assert rep["candidates_considered"] == 0
    assert rep["deep_dived"] == 0


def test_direct_export_default_candidates_exclude_producer():
    rep = report_engine.get_direct_export_scenario("1801", "CIV", top_k=1)
    assert rep["candidates_considered"] > 40  # ~54 African markets minus CIV
    assert rep["deep_dived"] == 1


def test_transformation_scenario_structure(_no_network_fx):
    # Import cocoa beans (1801), produce cocoa paste (1803) in CIV, export to NGA.
    rep = report_engine.get_transformation_scenario(
        input_hs_code="1801",
        input_origin_iso3="GHA",
        producer_iso3="CIV",
        finished_hs_code="1803",
        destination_iso3="NGA",
        input_value_usd=40000.0,
        finished_value_usd=70000.0,
    )
    assert rep["report_type"] == "value_chain_transformation"
    assert rep["scenario"] == "S1_import_inputs_produce_export"
    # Three legs present
    assert "leg1_input_import" in rep
    assert "leg2_production" in rep
    assert rep["leg3_export"]["report_type"] == "bilateral_product_opportunity"
    # Real input tariff computed at the producer (CIV) for the input HS
    assert rep["leg1_input_import"]["tariff"]["available"] in (True, False)
    # Gross value-added = finished - input, flagged partial (not net profit)
    va = rep["value_added"]
    assert va["available"] is True
    assert va["gross_value_added_usd"] == 30000.0  # 70000 - 40000
    assert va["is_estimation"] is False
    assert "BRUTE" in va["note"]


def test_transformation_value_added_unavailable_without_values():
    rep = report_engine.get_transformation_scenario("1801", "GHA", "CIV", "1803", "NGA")
    assert rep["value_added"]["available"] is False


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


def test_get_product_name_resolves_exact_hs6_not_wrong_chapter():
    # Bug signalé : « 180400 » (beurre de cacao) était étiqueté « Produits
    # laitiers, œufs » — l'ancien code gardait les 4 DERNIERS chiffres
    # (« 0400 ») et rattachait la sous-position au chapitre de ses chiffres
    # 3-4. Tout SH6 en « xx01xx » devenait « Animaux vivants ».
    from services.real_trade_data_service import get_product_name

    assert get_product_name("180400", "fr") == "Beurre de cacao"
    assert get_product_name("180400", "en") == "Cocoa butter"
    assert "laitier" not in get_product_name("180400", "fr").lower()
    assert get_product_name("090111", "fr") == "Café non torréfié"
    assert get_product_name("180100", "fr") == "Cacao en fèves"
    # Les niveaux moins spécifiques restent corrects.
    assert get_product_name("1804", "fr") == "Cacao et préparations"
    assert get_product_name("09", "fr")  # chapitre — ne lève pas
    assert get_product_name("", "fr") == "Produit inconnu"
