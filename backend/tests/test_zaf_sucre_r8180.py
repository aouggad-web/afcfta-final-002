"""Afrique du Sud, sucre : l'avis R.8180 (GG 55738, 13 novembre 2026) ramène le droit
spécifique à 516,35 c/kg dans toutes les colonnes des sous-positions 1701.12, .13, .14, .91
et .99. Fiche : ZAF_amendement_sucre_2026-11-13.json."""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)

SUCRES = ("170112", "170113", "170114", "170191", "170199")
COLONNES = ("EU_UK", "EFTA", "SADC", "MERCOSUR", "AFCFTA")


def _dd(position):
    return next(d for d in position["droits"] if d["code"] == "DD")


@besoin_socle
@pytest.mark.parametrize("code", SUCRES)
def test_le_socle_porte_le_droit_de_r8180_sur_la_ligne_et_les_cinq_colonnes(code):
    position, _ = socle.position("ZAF", code)
    dd = _dd(position)
    assert dd["specifique"]["montant"] == pytest.approx(5.1635)
    assert dd["specifique"]["brut"] == "516,35c/kg"
    assert (dd["specifique"]["unite_quantite"], dd["specifique"]["sous_unite_source"]) == ("kg", "c")
    assert dd.get("taux") is None and "R.8180" in dd["source"]
    assert set(position["preferentiels"]) >= set(COLONNES)
    for colonne in COLONNES:
        pref = position["preferentiels"][colonne]
        assert pref["taux"] is None and pref["specifique"]["brut"] == "516,35c/kg", colonne


@besoin_socle
def test_les_autres_sucres_et_le_reste_du_chapitre_ne_bougent_pas():
    """R.8180 ne vise que cinq sous-positions : 1701.12 à 1701.99 sont les seules de la position 17.01."""
    positions = socle.charger("ZAF")["positions"]
    assert {c for c in positions if c.startswith("1701")} == set(SUCRES)
    autre, _ = socle.position("ZAF", "170310")
    assert "R.8180" not in (_dd(autre).get("source") or "")


@besoin_socle
def test_le_calcul_liquide_516_35_c_par_kg_et_aucun_avantage_zlecaf():
    from routes import calcul as route

    app = FastAPI()
    app.include_router(route.router)
    client = TestClient(app)
    corps = {"destination": "ZAF", "code_sh": "17019900", "valeur_cif": 10000, "quantites": {"kg": 1000}}
    sans = client.post("/calcul", json=dict(corps, origine="BRA")).json()
    zlecaf = client.post("/calcul", json=dict(corps, origine="KEN")).json()

    ligne = next(ligne for ligne in sans["npf"]["lignes"] if ligne["code"] == "DD")
    assert ligne["montant"] == pytest.approx(5163.5)
    # La colonne AfCFTA égale la colonne générale : la préférence ne change pas le droit.
    pref = next(ligne for ligne in zlecaf["preference"]["lignes"] if ligne["code"] == "DD")
    assert pref["montant"] == pytest.approx(5163.5)
