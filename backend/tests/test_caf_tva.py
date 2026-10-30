"""Centrafrique : TVA à l'importation, exonérations (CGI art. 249, loi de
finances 2025) et taux réduit de 5 % (art. 257, loi de finances 2024).
Fiche : CAF_tva_2026-10-30.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CAF.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _tva(position):
    return next(d for d in position["droits"] if d["code"] == "TVA")["taux"]


@pytest.mark.parametrize("code", ["29371200", "29411000", "30049000", "37011000", "37021000", "40141000",
                                  "40151100", "87131000", "90049010", "90181100", "90221400", "94029000"])
def test_produits_pharmaceutiques_et_medicaux_exoneres(positions, code):
    assert _tva(positions[code]) == 0.0


@pytest.mark.parametrize("code", ["04011000", "07019000", "38089110", "38089290", "94021010"])
def test_taux_reduit_de_cinq_pour_cent(positions, code):
    assert _tva(positions[code]) == 5.0


@pytest.mark.parametrize("code", ["02013000", "03053020", "08011100", "38089410", "94021020", "90049020",
                                  "10063010"])
def test_taux_general(positions, code):
    """Viandes, poisson de 03.05 et fruits : le taux réduit ne vise que les produits locaux ;
    désinfectants, fauteuils de coiffeur, lunettes protectrices : non listés."""
    assert _tva(positions[code]) == 19.0


def test_la_base_reste_valeur_droit_de_douane_et_accise(positions):
    r = calculer(positions["07019000"], 1000, devise_position="XAF", devise_cif="XAF")
    tva = next(l for l in r["npf"]["lignes"] if l["code"] == "TVA")
    assert tva["base"] == 1000.0 + next(l for l in r["npf"]["lignes"] if l["code"] == "DD")["montant"]
    assert tva["montant"] == round(tva["base"] * 0.05, 2)
