"""Nigéria : accise de la Fifth Schedule (Annex IV) de la Customs, Excise Tariff,
Etc. (Variation) Order 2026, en vigueur au 1er juillet 2026. Fiche :
NGA_accises_fifth_schedule_2026-10-26.json."""

import json
import os

import pytest

from services import socle
from services.calcul import calculer

SOCLE_NGA = os.path.join(socle.SOCLE_DIR, "NGA.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE_NGA), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE_NGA, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _accise(positions, code, quantite):
    lignes = calculer(positions[code], 100000.0, quantite=quantite, taux_de_change=1.0)["npf"]["lignes"]
    return next(l for l in lignes if l["code"] == "EXC")


@pytest.mark.parametrize("code,quantite,montant", [
    ("2203001000", 100, 7200.0),  # bière : NILL, ₦72 par litre
    ("2204210000", 10, 25700.0),  # vin : 25 % + ₦70 par litre
    ("2208300000", 10, 30750.0),  # whisky : 30 % + ₦75 par litre
    ("2402200000", 200, 31200.0),  # cigarettes : 30 % + ₦6 par cigarette
    ("2201102000", 100, 1000.0),  # eaux gazéifiées : ₦10 par litre
])
def test_les_taux_2026_de_l_annexe_iv(positions, code, quantite, montant):
    accise = _accise(positions, code, quantite)
    assert accise["statut"] == "CALCULE" and accise["montant"] == montant


@pytest.mark.parametrize("code", ["2202100000", "2009121000", "2403190000", "2404110000"])
def test_sucre_ou_deux_unites_restent_non_liquidables(positions, code):
    assert _accise(positions, code, 10)["montant"] is None


@pytest.mark.parametrize("code", ["2905110000", "0709930000", "2523100000", "2106909900", "2207101000"])
def test_hors_de_la_liste_pas_d_accise(positions, code):
    accise = _accise(positions, code, 10)
    assert accise["statut"] == "CALCULE" and accise["montant"] == 0.0
