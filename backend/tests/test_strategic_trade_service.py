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

    async def fake_get_oec_exports(iso3, year=2022, limit=100, hs_level="HS4"):
        # Facteur 4 (historique d'export réel, voir _export_history_hs4) et
        # position nette (facteur 5, voir _national_net_position) : par défaut
        # aucun flux, pour rester hermétique. get_strategic_flows peut les
        # appeler selon le flux d'exécution (dès qu'un candidat tiers 2/3
        # existe) — un test qui ne les stub pas atteindrait sinon le service
        # OEC réel (jusqu'à son délai d'attente HTTP) même hors-réseau.
        return []

    async def fake_get_oec_imports(iso3, year=2022, limit=100, hs_level="HS4"):
        # Facteur 5 (position nette, voir _national_net_position) : aucun
        # import par défaut -> le garde-fou « besoin national » ne bloque rien
        # tant qu'un test ne simule pas explicitement un déficit.
        return []

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
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_get_oec_exports)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_imports", fake_get_oec_imports)
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
    sugar = next(f for f in res["flows"] if f["hs_code"] == "170199")
    sugar_markets = [m["iso3"] for m in sugar["markets"]]
    assert "DZA" not in sugar_markets  # exporter must never be its own market


def test_enrichment_fields_populated():
    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    sugar = next(f for f in res["flows"] if f["hs_code"] == "170199")
    adv = sugar["advantage"]
    # Tariff edge = chapter-17 MFN proxy (15%) minus AfCFTA preferential (0).
    assert adv["afcfta_tariff_edge"]["edge_pct"] == 15.0
    assert adv["rules_of_origin"] is not None  # RoO resolved (lazy-loaded)
    # Un flux = un produit, avec ses marchés importateurs listés (lead time par
    # marché) — plus de carte dupliquée par destination, ni de graphe de demande.
    assert sugar["markets"], "le produit doit lister ses marchés importateurs"
    assert all(m["lead_time_days"] == 12 for m in sugar["markets"])
    assert all(m["import_usd"] > 0 for m in sugar["markets"])
    assert "growth_trajectory" not in sugar


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
    de l'index de capacité d'un pays sans intrant laitier corroboré (facteur 2,
    ``unido_discovery_service._input_corroborated``) ; (2) même sans
    corroboration d'intrant, le plafond de plausibilité VA gradué (facteur 3
    x facteur 4) empêcherait tout produit découvert jamais exporté de dépasser
    10 % de la VA de sa division.
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


def test_national_demand_excludes_dza_milk_powder_despite_real_capacity(monkeypatch):
    """
    Régression du cas signalé : l'Algérie ressortait comme exportatrice de
    lait en poudre (SH 040210) alors qu'elle en IMPORTE plus d'1 Md$/an. Sa
    production laitière est réelle (le facteur 2 « intrant corroboré » est
    satisfait — même avec le projet Baladna, ~300 000 vaches) : le bug n'est
    donc PAS un défaut de capacité de production, mais l'absence de contrôle
    du besoin national. Le garde-fou « position nette » (facteur 5) doit
    écarter ce flux même quand la capacité de production est authentique.
    """

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Algérie"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        return {"040210": [{"iso3": "EGY", "value": 60_000_000, "quantity": 0}]}

    async def fake_imports(iso3, year=2022, limit=100, hs_level="HS4"):
        # Position nette DZA sur 040210 : grosse demande d'import réelle,
        # aucun export en face -> importateur net flagrant.
        return [{"hs_code": "040210", "product_name": "Milk powder", "trade_value": 1_050_000_000}]

    async def fake_exports(iso3, year=2022, limit=100, hs_level="HS4"):
        return []

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_imports", fake_imports)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_exports)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 15)
    # Force la corroboration d'intrant laitier (facteur 2) à passer, pour
    # isoler le garde-fou testé (facteur 5) — sans ce force, le SH4 laitier
    # serait déjà exclu en amont par le facteur 2, et le test ne prouverait
    # rien sur le nouveau garde-fou.
    from services import unido_discovery_service as disco

    monkeypatch.setattr(disco, "_input_corroborated", lambda iso3, hs4: True)

    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    assert not any(
        f["hs_code"] == "040210" for f in res["flows"]
    ), "l'Algérie ne doit jamais ressortir exportatrice d'un produit qu'elle importe massivement"


def test_national_net_position_does_not_block_genuine_surplus_export(monkeypatch):
    """
    Contre-épreuve : un pays qui EXPORTE déjà largement plus qu'il n'importe
    un produit (excédent réel) ne doit pas être bloqué par le garde-fou —
    celui-ci cible spécifiquement le déficit nettement en faveur des imports.
    """

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Algérie"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        return {"170199": [{"iso3": "SEN", "value": 120_000_000, "quantity": 0}]}

    async def fake_imports(iso3, year=2022, limit=100, hs_level="HS4"):
        return [{"hs_code": "170199", "product_name": "Refined sugar", "trade_value": 2_000_000}]

    async def fake_exports(iso3, year=2022, limit=100, hs_level="HS4"):
        return [{"hs_code": "170199", "product_name": "Refined sugar", "trade_value": 80_000_000}]

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_imports", fake_imports)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_exports)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 12)

    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    assert any(f["hs_code"] == "170199" for f in res["flows"])


def test_discovered_flow_potential_capped_by_sector_value_added(monkeypatch):
    """Garde-fou général (facteur 3) : un flux découvert ne peut jamais dépasser
    le plafond gradué (facteur 4) de la valeur ajoutée réelle de sa division
    ISIC, quel que soit le produit — ici sans aucun historique d'export réel,
    donc au plafond le plus prudent (nascent)."""

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

    async def fake_exports(iso3, year=2022, limit=100, hs_level="HS4"):
        return []  # aucun historique d'export réel -> plafond « nascent »

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_exports)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 15)

    res = run(mod.get_strategic_flows("BDI", year=2024, lang="fr", limit=50))
    cotton = next(f for f in res["flows"] if f["hs_code"] == "520512")
    va = cotton["capacity_evidence"]["value_added_usd"]
    assert cotton["capacity_evidence"]["has_export_history"] is False
    assert cotton["potential_usd"] <= va * mod._DISCOVERY_VA_CAP_FRACTION_NASCENT + 1  # arrondi


def test_discovered_flow_gets_corroborated_cap_when_export_history_exists(monkeypatch):
    """Facteur 4 : un produit déjà exporté (même faiblement) par le pays obtient
    le plafond standard (30 %), pas le plafond « nascent » (10 %)."""

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Burundi"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        return {"520512": [{"iso3": "EGY", "value": 500_000_000, "quantity": 0}]}

    async def fake_exports(iso3, year=2022, limit=100, hs_level="HS4"):
        # Historique réel, même modeste, sur le SH4 du coton (5205).
        return [{"hs_code": "5205", "product_name": "Cotton yarn", "trade_value": 500_000}]

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod.real_trade_service, "get_oec_exports", fake_exports)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 15)

    res = run(mod.get_strategic_flows("BDI", year=2024, lang="fr", limit=50))
    cotton = next(f for f in res["flows"] if f["hs_code"] == "520512")
    va = cotton["capacity_evidence"]["value_added_usd"]
    assert cotton["capacity_evidence"]["has_export_history"] is True
    assert cotton["potential_usd"] <= va * mod._DISCOVERY_VA_CAP_FRACTION_CORROBORATED + 1


def test_no_duplicate_product_titles_in_discovered_tier(monkeypatch):
    """
    Régression signalée en production : le panneau « Commodités prioritaires »
    affichait deux lignes « Gaz de pétrole (GPL) & hydrocarbures gazeux »,
    deux « Huile de palme » et deux « Lait concentré / en poudre » — parce que
    le libellé du tiers 3 (découverte UNIDO) ne varie qu'au niveau SH4, alors
    que la demande d'import est indexée au SH6 : deux sous-positions SH6 du
    même SH4 (ex. 271111 et 271121, toutes deux « GPL ») produisaient chacune
    leur propre carte avec un titre identique. Une seule sous-position par SH4
    doit désormais survivre (la plus demandée).
    """

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Algérie"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        # Deux sous-positions SH6 du MÊME SH4 2711 (GPL), toutes deux au-dessus
        # du seuil de marché minimal -> avant le correctif, deux cartes « GPL ».
        return {
            "271111": [{"iso3": "EGY", "value": 300_000_000, "quantity": 0}],
            "271121": [{"iso3": "MAR", "value": 200_000_000, "quantity": 0}],
        }

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 10)

    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    gpl_flows = [
        f for f in res["flows"] if f["product"] == "Gaz de pétrole (GPL) & hydrocarbures gazeux"
    ]
    gpl_hs_codes = {f["hs_code"] for f in gpl_flows}
    assert len(gpl_hs_codes) == 1, f"un seul code SH devrait survivre, trouvé {gpl_hs_codes}"
    # La sous-position gagnante est celle à la demande la plus forte (271111, 300M).
    assert "271111" in gpl_hs_codes


def test_no_duplicate_product_titles_across_champion_sh6_basket(monkeypatch):
    """
    Même défaut côté tiers 2 (champions curés) : un champion listant plusieurs
    SH6 sous un seul libellé d'extrant (ex. Cevital « Huile de table raffinée &
    margarine » couvre 6 SH6) ne doit produire qu'UNE carte par libellé, même
    si plusieurs de ses SH6 ont chacun une vraie demande africaine.
    """

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Algérie"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        # 150790 et 151190 appartiennent tous deux au panier SH6 du champion
        # "Raffinage d'huiles (Cevital & filière)" (label unique).
        return {
            "150790": [{"iso3": "TUN", "value": 60_000_000, "quantity": 0}],
            "151190": [{"iso3": "MAR", "value": 40_000_000, "quantity": 0}],
        }

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 10)

    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    all_hs = {f["hs_code"] for f in res["flows"]}
    assert "150790" in all_hs  # demande la plus forte (60M > 40M) -> survit, tiers 2
    # 151190 (sous-position perdante du MÊME panier champion) ne doit fuiter
    # NULLE PART ailleurs — ni comme doublon tiers 2, ni redécouvert par le
    # tiers 3 sous un titre générique différent ("Huile de palme").
    assert "151190" not in all_hs


def test_discovered_flow_lists_markets_in_one_card_not_duplicated(monkeypatch):
    """
    Méthode retenue : au lieu d'une carte par (produit × marché), UN flux par
    produit qui LISTE ses marchés importateurs avec leur volume d'import réel.
    Deux marchés du même produit (acier plat 720851) ne produisent donc plus
    deux cartes, mais une seule carte à deux entrées de marché. La rationale
    reste spécifique (premier marché + demande totale), jamais un modèle copié.
    """

    async def fake_find(iso3, year=2022, min_market_size=0, lang="fr"):
        return {
            "exporter": {"iso3": iso3, "name": "Algérie"},
            "data_source": "TEST",
            "opportunities": [],
        }

    async def fake_idx(year, hs_level="HS6", limit=100):
        return {
            "720851": [
                {"iso3": "EGY", "value": 300_000_000, "quantity": 0},
                {"iso3": "TUN", "value": 50_000_000, "quantity": 0},
            ]
        }

    monkeypatch.setattr(mod.real_substitution_service, "find_export_opportunities", fake_find)
    monkeypatch.setattr(mod.real_substitution_service, "_build_african_import_index", fake_idx)
    monkeypatch.setattr(mod, "_lead_time_days", lambda *a, **k: 10)

    res = run(mod.get_strategic_flows("DZA", year=2024, lang="fr", limit=50))
    steel = [f for f in res["flows"] if f["hs_code"] == "720851"]
    assert len(steel) == 1, "un seul flux (carte) par produit, marchés listés dedans"
    flow = steel[0]
    markets = {m["iso3"]: m for m in flow["markets"]}
    assert set(markets) == {"EGY", "TUN"}
    assert markets["EGY"]["import_usd"] == 300_000_000
    assert markets["TUN"]["import_usd"] == 50_000_000
    # Marchés triés par volume d'import décroissant.
    assert flow["markets"][0]["iso3"] == "EGY"
    # Rationale spécifique : premier marché nommé + cadrage multi-marchés + volume.
    rat = flow["strategic_rationale"]
    assert "Égypte" in rat
    assert "2 marchés" in rat
    assert "300 M$" in rat
