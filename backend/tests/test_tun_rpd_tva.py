"""Tunisie : TVA sur la valeur augmentée de tous les droits et taxes sauf elle-même
(Code de la TVA art. 6) ; RPD 3 % de la somme des droits et taxes liquidés, TVA
comprise, minimum 10 dinars par article (loi n° 2012-27, art. 57). Fiche :
TUN_RPD_2026-10-07.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "TUN.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position, valeur):
    r = calculer(position, valeur, quantite=1.0, devise_position="TND")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def _voiture(positions):
    return positions[next(k for k in positions if k.startswith("8703401011"))]


def test_la_tva_porte_aussi_sur_le_droit_de_consommation(positions):
    """Voiture 8703.40 : DD 0 %, DC 10 %, TVA 19 % sur 1 000 + 100."""
    etat, lignes = _lignes(_voiture(positions), 10000.0)
    assert lignes["TVAAUTO"]["base"] == 11000.0 and lignes["TVAAUTO"]["famille"] == "tva"
    assert etat == COMPLET


def test_la_rpd_porte_sur_tous_les_droits_et_taxes_tva_comprise(positions):
    etat, lignes = _lignes(_voiture(positions), 10000.0)
    # 3 % de (1 000 de DC + 2 090 de TVA).
    assert (lignes["RPD"]["base"], lignes["RPD"]["montant"]) == (3090.0, 92.7)


def test_la_rpd_ne_descend_pas_sous_dix_dinars(positions):
    etat, lignes = _lignes(_voiture(positions), 100.0)
    assert lignes["RPD"]["montant"] == 10.0 and lignes["RPD"]["minimum_applique"]
