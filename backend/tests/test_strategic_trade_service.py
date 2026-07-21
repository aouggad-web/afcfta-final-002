"""
Tests for the strategic trade intelligence engine.

Hermetic: the two OEC-backed calls (base export opportunities and the African
import index) are mocked, so the test exercises the *enrichment & fusion* logic
— capacity-driven flows, emerging megaproject flows, tariff edge, rules of
origin, aggregation — without any network.
"""

import asyncio

import pytest
from services import strategic_trade_service as mod


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def mock_oec(monkeypatch):
    """Base export opportunities + African import index, both hermetic."""

    async def fake_find_export_opportunities(iso3, year=2022, min_market_size=0, lang="fr"):
        # Algeria's real top export is a hydrocarbon (not in the curated KB).
        return {
            "exporter": {"iso3": "DZA", "name": "Algérie"},
            "data_source": "TEST",
            "opportunities": [
                {
                    "export_product": {"hs_code": "270900", "name": "Crude Petroleum"},
                    "market_match_level": "hs6",
                    "potential_markets": [
                        {
                            "country_iso3": "EGY",
                            "country_name": "Égypte",
                            "market_size": 1_000_000_000,
                            "capture_potential": 0.2,
                            "price_positioning": None,
                        }
                    ],
                    "afcfta_advantage": "ZLECAf",
                    "binding_constraint": "capacité",
                }
            ],
        }

    async def fake_import_index(year, hs_level="HS6", limit=100):
        # African demand for refined sugar (Cevital champion) and iron ore
        # (Gara Djebilet future capacity) — neither is in Algeria's top exports.
        # 720851 (hot-rolled steel) is NOT curated but falls under Algeria's real
        # UNIDO basic-metals capacity (ISIC 24) -> must be DISCOVERED. 260111
        # (iron ore) is extractive -> must never be discovered.
        return {
            "170199": [
                {"iso3": "SEN", "value": 120_000_000, "quantity": 0},
                {"iso3": "CMR", "value": 90_000_000, "quantity": 0},
                {"iso3": "DZA", "value": 5_000_000, "quantity": 0},  # self, must be skipped
            ],
            "260111": [
                {"iso3": "EGY", "value": 400_000_000, "quantity": 0},
            ],
            "720851": [
                {"iso3": "EGY", "value": 300_000_000, "quantity": 0},
            ],
        }

    monkeypatch.setattr(
        mod.real_substitution_service,
        "find_export_opportunities",
        fake_find_export_opportunities,
    )
    monkeypatch.setattr(
        mod.real_substitution_service,
        "_build_african_import_index",
        fake_import_index,
    )
    # Lead time is corridor logistics — keep the test offline.
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 12)


def test_base_and_capacity_and_emerging_flows_all_present():
    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    by_hs = {f["hs_code"]: f for f in res["flows"]}

    # 1) Base OEC flow (crude) survives.
    assert "270900" in by_hs
    assert by_hs["270900"]["is_emerging"] is False

    # 2) Capacity-driven champion flow (refined sugar / Cevital) — NOT in the
    #    base exports, surfaced purely from proven industrial capacity vs demand.
    assert "170199" in by_hs
    sugar = by_hs["170199"]
    assert sugar["signal"] == "High Growth"
    assert sugar["is_emerging"] is False  # operational champion, not a future mine
    assert sugar["transformation"]["champion"].lower().startswith("raffinage de sucre")
    assert sugar["transformation"]["input_target"] is not None  # raw sugar input volume

    # 3) Emerging megaproject flow (iron ore / Gara Djebilet).
    assert "260111" in by_hs
    iron = by_hs["260111"]
    assert iron["signal"] == "High Growth"
    assert iron["is_emerging"] is True


def test_unido_discovered_flow_from_capacity():
    """
    Tiers 3 : un produit non curé (acier plat 720851) mais couvert par la
    capacité UNIDO réelle du pays (métallurgie de base, ISIC 24) émerge comme
    flux DÉCOUVERT, tandis qu'un minerai extractif (260111) n'émerge jamais.
    """
    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    by_hs = {f["hs_code"]: f for f in res["flows"]}

    assert "720851" in by_hs, "L'acier plat devrait être découvert via la capacité UNIDO"
    steel = by_hs["720851"]
    assert steel["discovery_tier"] == "unido"
    assert steel["signal"] == "High Growth"
    ev = steel["capacity_evidence"]
    assert ev["isic_code"] == "24"
    assert ev["value_added_usd"] > 0
    assert ev["source"] == "UNIDO INDSTAT4"
    # La transformation est narrée depuis l'évidence de division (pas de champion).
    assert steel["transformation"]["sector"]

    # Le minerai de fer brut reste porté par la capacité FUTURE (projet), jamais
    # par la découverte manufacturière UNIDO.
    assert by_hs["260111"].get("discovery_tier") != "unido"


def test_self_market_is_excluded():
    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    sugar_markets = [f["to"]["iso3"] for f in res["flows"] if f["hs_code"] == "170199"]
    assert "DZA" not in sugar_markets  # exporter must never be its own market


def test_enrichment_fields_populated():
    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    sugar = next(f for f in res["flows"] if f["hs_code"] == "170199")
    adv = sugar["advantage"]
    # Tariff edge = chapter-17 MFN proxy (15%) minus AfCFTA preferential (0).
    assert adv["afcfta_tariff_edge"]["edge_pct"] == 15.0
    assert adv["rules_of_origin"] is not None  # RoO resolved (lazy-loaded)
    assert adv["lead_time_days"] == 12
    # 5-year demand trajectory has 5 points.
    assert len(sugar["growth_trajectory"]["points"]) == 5


def test_summary_aggregation():
    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    summary = res["summary"]
    assert summary["identified_flows"] == len(res["flows"])
    assert summary["total_potential_usd"] > 0
    assert summary["top_partners"]
    assert summary["priority_commodities"]
    # Partners are sorted by potential descending.
    pots = [p["potential_usd"] for p in summary["top_partners"]]
    assert pots == sorted(pots, reverse=True)


def test_no_fictitious_dairy_flow_for_burundi(monkeypatch):
    """
    Régression du bug réel constaté : Burundi -> Algérie, lait en poudre
    (SH 040210), 246,6 M$ de potentiel — soit PLUS que la totalité de la
    valeur ajoutée du secteur alimentaire burundais (191,6 M$, UNIDO), pour un
    pays dont la collecte de lait cru réelle plafonne à ~40 500 t/an (FAOSTAT
    2024). Deux garde-fous corrigent ce cas : (1) les SH4 laitiers sont exclus
    de l'index de capacité d'un pays sans intrant laitier corroboré
    (``unido_discovery_service._has_dairy_input``) ; (2) même sans corroboration
    d'intrant, le plafond de plausibilité VA (``_DISCOVERY_VA_CAP_FRACTION``)
    empêcherait tout produit découvert de dépasser 30 % de la VA de sa division.
    """

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Burundi"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        # Reproduit exactement la demande algérienne réelle en lait en poudre
        # qui avait généré le flux fictif.
        return {"040210": [{"iso3": "DZA", "value": 986_400_000, "quantity": 0}]}

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 20)

    res = run(mod.get_strategic_flows("BDI", year=2024, lang="fr", limit=50))
    assert not any(f["hs_code"] == "040210" for f in res["flows"])


def test_discovered_flow_potential_capped_by_sector_value_added(monkeypatch):
    """Garde-fou général : un flux découvert ne peut jamais dépasser 30 % de la
    valeur ajoutée réelle de sa division ISIC, quel que soit le produit."""

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Burundi"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        # Coton (textiles, division 13) : demande massive simulée pour
        # vérifier que le plafond s'applique hors du cas laitier.
        return {"520512": [{"iso3": "EGY", "value": 500_000_000, "quantity": 0}]}

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 15)

    res = run(mod.get_strategic_flows("BDI", year=2024, lang="fr", limit=50))
    cotton = next(f for f in res["flows"] if f["hs_code"] == "520512")
    va = cotton["capacity_evidence"]["value_added_usd"]
    assert cotton["potential_usd"] <= va * mod._DISCOVERY_VA_CAP_FRACTION + 1  # arrondi
