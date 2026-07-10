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
    # seule dans le jeu de données -> DOIT porter un garde-fou explicite.
    r = pcs.get_continental_producers("30")
    assert r["available"] is True
    assert r["coverage_caveat"] is not None
    assert len(r["top_producers"]) == 1
    assert r["top_producers"][0]["country_iso3"] == "MUS"


def test_get_capacity_propagates_coverage_caveat_in_continental_block():
    r = pcs.get_capacity("MUS", "30")
    assert r["available"] is True
    assert r["continental"]["coverage_caveat"] is not None
    assert r["continental"]["total_countries"] == 1


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
