"""Cap-Vert : taxe spécifique sur l'alcool importé en CVE par litre (Lei n.º 45/X/2024,
OE 2025, art. 77 et annexe I). Fiche : CPV_taxe_alcool_2026-11-02.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CPV.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _tea(position):
    return next(d for d in position["droits"] if d["code"] == "TEA")


@pytest.mark.parametrize(
    "code, montant",
    [("2203001000", 60.0), ("2204210010", 90.0), ("2204300000", 90.0), ("2205900000", 90.0),
     ("2206001000", 90.0), ("2207109000", 90.0), ("2207200000", 90.0), ("2208201000", 300.0),
     ("2208300000", 300.0), ("2208900000", 300.0)],
)
def test_bareme_par_litre(positions, code, montant):
    tea = _tea(positions[code])
    assert tea["specifique"]["montant"] == montant and tea["specifique"]["unite_quantite"] == "litre"


def test_alcool_ethylique_de_l_article_2207_10_10_non_vise(positions):
    assert not any(d["code"] == "TEA" for d in positions["2207101000"]["droits"])


def test_biere_complete_avec_les_litres(positions):
    """100 000 CVE, 100 l : DI 50 % = 50 000 ; TC 500 ; TEA 6 000 ; ICE 50 % sur 156 500 ;
    IVA sur la valeur et tous les droits et taxes."""
    r = calculer(positions["2203001000"], 100_000, quantites={"litre": 100}, devise_position="CVE",
                 devise_cif="CVE")["npf"]
    lignes = {l["code"]: l for l in r["lignes"]}
    assert lignes["TEA"]["montant"] == 6_000
    assert lignes["ICE"]["base"] == 156_500
    assert lignes["TVA"]["base"] == 156_500 + lignes["ICE"]["montant"]
    assert r["etat"] == "COMPLET"
