"""
Tests du garde-fou de couverture de données (coverage_caveat).

Bug signalé : Maurice ressortait comme "producteur principal" / leader
continental des produits pharmaceutiques — pas une hallucination de LLM
cette fois, mais un vrai trou de données : le fichier ingéré
(data/json/production_africaine.json) ne contient qu'UN SEUL pays (Maurice)
pour "Produits pharmaceutiques" (UNIDO), alors que l'Égypte, le Maroc,
l'Afrique du Sud et la Tunisie ont des industries pharmaceutiques réelles non
encore ingérées. Un rang #1 / 100% de part calculé sur 1 pays ne doit jamais
être présenté comme un leadership réel — d'où ce garde-fou.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import production_capacity_service as pcs  # noqa: E402


def test_coverage_caveat_none_when_enough_countries():
    assert pcs._coverage_caveat("agri", "Cocoa beans", 10) is None
    assert pcs._coverage_caveat("agri", "Cocoa beans", pcs._MIN_RELIABLE_COVERAGE_COUNTRIES) is None


def test_coverage_caveat_present_below_threshold():
    for n in (0, 1, 2, pcs._MIN_RELIABLE_COVERAGE_COUNTRIES - 1):
        note = pcs._coverage_caveat("manufacturing", "Produits pharmaceutiques", n)
        assert note is not None
        assert "Produits pharmaceutiques" in note
        assert str(n) in note
        assert "UNIDO" in note


def test_mauritius_pharma_flagged_as_low_coverage_not_leadership():
    # Reproduit exactement le bug signalé : SH 30 (médicaments) -> Maurice
    # seule dans le jeu de données -> DOIT porter un garde-fou explicite,
    # et AUCUNE part africaine (le « 100 % » était un artefact d'ingestion).
    r = pcs.get_continental_producers("30")
    assert r["available"] is True
    assert r["coverage_caveat"] is not None
    assert len(r["top_producers"]) == 1
    assert r["top_producers"][0]["country_iso3"] == "MUS"
    assert r["top_producers"][0]["share_pct"] is None


def test_get_capacity_propagates_coverage_caveat_in_continental_block():
    r = pcs.get_capacity("MUS", "30")
    assert r["available"] is True
    assert r["continental"]["coverage_caveat"] is not None
    assert r["continental"]["total_countries"] == 1


def test_get_capacity_emits_no_rank_share_leader_under_threshold():
    # Le cœur du bug « Maurice producteur africain 100 % de médicaments » :
    # sous le seuil de couverture, rang/part/leader/total sont des artefacts
    # et ne doivent PAS être émis — seule la valeur réelle du pays subsiste.
    r = pcs.get_capacity("MUS", "30")
    cont = r["continental"]
    assert cont["rank"] is None
    assert cont["country_share_pct"] is None
    assert cont["leader"] is None
    assert cont["continental_total"] is None
    assert all(p["share_pct"] is None for p in cont["top_producers"])
    # La valeur mesurée réelle du pays, elle, reste servie.
    assert r["latest_value"] is not None
    # Et aucun scénario « rattrapage du leader » n'est bâti sur un faux leader.
    assert "potentiel_rattrapage" not in r["integration_scenarios"]


def test_get_country_profile_nulls_rank_share_under_threshold(monkeypatch):
    # get_country_profile ne liste que les produits de la liste explicite
    # HS_TO_COMMODITY (la pharma n'y arrive que par repli chapitre) : on force
    # le garde-fou pour vérifier le mécanisme — sous couverture partielle,
    # rang et part ne sont JAMAIS émis vers les prompts.
    monkeypatch.setattr(pcs, "_coverage_caveat", lambda *a, **k: "couverture partielle (test)")
    profile = pcs.get_country_profile("CIV", top_n=10)
    assert profile["available"] is True
    assert profile["products"]
    for p in profile["products"]:
        assert p["coverage_caveat"]
        assert p["rank"] is None
        assert p["share_pct"] is None


def test_capacity_is_reliable_gates_thin_coverage():
    # Porte du proxy d'exportations : un bloc mesuré mince (caveat) n'est PAS
    # fiable seul -> le proxy doit s'y adjoindre ; un bloc bien couvert l'est.
    assert pcs.capacity_is_reliable(None) is False
    assert pcs.capacity_is_reliable({"available": False}) is False
    assert pcs.capacity_is_reliable(pcs.get_capacity("MUS", "30")) is False  # 1 pays
    assert pcs.capacity_is_reliable(pcs.get_capacity("CIV", "1801")) is True  # cacao
    # Un proxy déjà attaché est terminal (pas de re-proxy).
    assert pcs.capacity_is_reliable({"available": True, "is_proxy": True}) is True


def test_well_covered_commodity_has_no_caveat():
    # Cacao (ICE-benchmark-covered agri commodity) a une couverture large —
    # aucun garde-fou ne doit apparaître.
    r = pcs.get_continental_producers("1801")
    assert r["available"] is True
    assert r["coverage_caveat"] is None
    assert len(r["top_producers"]) >= pcs._MIN_RELIABLE_COVERAGE_COUNTRIES


def test_report_engine_supply_side_surfaces_coverage_caveat():
    from services import report_engine

    supply = report_engine._supply_side("30")
    assert supply["available"] is True
    assert supply["coverage_caveat"] is not None
