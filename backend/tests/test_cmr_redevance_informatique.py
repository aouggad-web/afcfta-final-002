"""Cameroun : redevance informatique à 1 % de la valeur imposable, sans plafond à
l'importation (loi de finances 2023, art. 9 a), maintenu en 2026). Fiche :
CMR_redevance_informatique_2026-10-09.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CMR.json")
besoin_socle = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


@besoin_socle
def test_la_redevance_est_a_un_pour_cent_sans_plafond(positions):
    ri = [d for p in positions.values() for d in p["droits"] if d["code"] == "RI"]
    assert ri, "aucune redevance informatique au socle camerounais"
    assert {(d["taux"], d.get("plafond"), d["assiette"]) for d in ri} == {(1.0, None, "CIF")}
    assert all("Loi de finances 2023, art. 9 a)" in d["note"] for d in ri)


@besoin_socle
def test_une_position_ordinaire_se_calcule_sans_taux_de_change(positions):
    r = calculer(positions["01011010"], 10000, devise_position="XAF")
    assert r["npf"]["etat"] == COMPLET
    assert next(l for l in r["npf"]["lignes"] if l["code"] == "RI")["montant"] == pytest.approx(100.0)
