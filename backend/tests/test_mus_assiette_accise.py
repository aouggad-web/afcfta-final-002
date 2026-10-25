"""Maurice : assiette de l'accise ad valorem à l'importation = « value at
importation » (Excise Act s.2), valeur au sens du Customs Act ; véhicules
d'occasion exclus. Fiche : MUS_assiette_accise_2026-10-06.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "MUS.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position):
    r = calculer(position, 1000)
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_une_voiture_neuve_paie_l_accise_sur_la_valeur_et_la_tva_dessus(positions):
    """8703.21.19 neuve : accise 45 % sur 1 000 ; TVA sur valeur + DD + accise."""
    etat, lignes = _lignes(positions["87032119"])
    assert (lignes["EXC"]["base"], lignes["EXC"]["montant"]) == (1000.0, 450.0)
    assert lignes["TVA"]["base"] == 1450.0 and etat == COMPLET


def test_une_voiture_d_occasion_reste_sans_assiette(positions):
    etat, lignes = _lignes(positions["87032199"])
    assert lignes["EXC"]["statut"] == "ASSIETTE_INDISPONIBLE" and etat != COMPLET


def test_un_taux_nul_ne_bloque_plus_la_tva(positions):
    etat, lignes = _lignes(positions["04029990"])
    assert lignes["EXC"]["montant"] == 0.0 and etat == COMPLET
