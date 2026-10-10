"""Guinée équatoriale : pas de redevance informatique. La ligne était recopiée du
tarif camerounais ; aucune loi équato-guinéenne lue ne l'institue. Fiche :
GNQ_redevance_informatique_2026-10-10.json."""

import json
import os

import pytest
from services.calcul import COMPLET, calculer

SOCLE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GNQ.json"
)
besoin_socle = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


@besoin_socle
def test_aucune_redevance_informatique(positions):
    assert not [c for c, p in positions.items() if any(d["code"] == "RI" for d in p["droits"])]


@besoin_socle
def test_une_position_ordinaire_se_calcule_sans_taux_de_change(positions):
    r = calculer(positions["01011010"], 10000, devise_position="XAF")
    assert r["npf"]["etat"] == COMPLET
    assert [l["code"] for l in r["npf"]["lignes"]] == ["DD", "TCI", "TVA"]
