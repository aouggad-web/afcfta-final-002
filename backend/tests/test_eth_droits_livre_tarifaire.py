"""Éthiopie : droit de douane absent du portail, repris du livre tarifaire 2021 du
ministère des Finances. Fiche : ETH_droits_livre_tarifaire_2021-10-07.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "ETH.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _dd(position):
    return next(d for d in position["droits"] if d["code"] == "DD")


def test_reproducteurs_droit_du_livre(positions):
    """0101.2100 : absent du portail, « Free » au livre (page 1)."""
    dd = _dd(positions["01012100000"])
    assert dd["taux"] == 0.0 and dd["source"].startswith("Livre tarifaire")
    assert calculer(positions["01012100000"], 1000, devise_position="ETB")["npf"]["etat"] == COMPLET


def test_le_portail_prime_sur_le_livre(positions):
    """07.13 : 15 % au livre de 2021, 5 % au portail — le portail est conservé."""
    dd = _dd(positions[next(k for k in positions if k.startswith("07131000"))])
    assert dd["taux"] == 5.0 and "Livre" not in dd["source"]


def test_sous_position_modifiee_en_sh2022_non_comblee(positions):
    """1211.90 figure à la table I de l'OMD : le code de 2017 peut désigner un
    autre produit, le droit reste indisponible plutôt que repris du livre."""
    assert _dd(positions["12119000000"])["taux"] is None
