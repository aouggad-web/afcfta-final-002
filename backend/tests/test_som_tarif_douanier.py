"""Somalie : droit de douane du tarif national (Somali Customs Tariff 2022,
ministère des Finances), à la place du TEC de l'EAC 2022.
Fiche : SOM_tarif_douanier_2022_2026-11-01.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "SOM.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def socle():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)


def _dd(position):
    return next(d for d in position["droits"] if d["code"] == "DD")


def test_source_est_le_tarif_national(socle):
    assert socle["source"]["fichier"].endswith("crawled/SOM_tariffs.json")
    assert len(socle["positions"]) == 5472


def test_droits_du_tarif_2022(socle):
    """Reproducteurs 0101.21 : 5 % (0 % au TEC de l'EAC) ; gazole 2710.19.31 : 10 % ;
    ordinateurs portables 8471.30 : 5 % ; cigarettes 2402.20.10 : 35 %."""
    p = socle["positions"]
    taux = {c: _dd(p[c])["taux"] for c in ("01012100", "27101931", "84713000", "24022010")}
    assert taux == {"01012100": 5.0, "27101931": 10.0, "84713000": 5.0, "24022010": 35.0}


def test_droit_ad_valorem_sur_la_valeur_en_douane(socle):
    r = calculer(socle["positions"]["01012900"], 1000, devise_cif="USD")["npf"]
    lignes = {l["code"]: l for l in r["lignes"]}
    assert lignes["DD"]["montant"] == 250.0


@pytest.mark.parametrize("code", ["02031100", "22030000", "12099100", "03023900"])
def test_sans_taux_publie_le_droit_n_est_pas_nul(socle, code):
    """« – » sans FREE, « TBD % », « (y) » : pas de taux, et surtout pas 0 %."""
    assert "taux" not in _dd(socle["positions"][code])
