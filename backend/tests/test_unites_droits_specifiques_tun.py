"""Tunisie : un droit spécifique se liquide dans l'unité que nomme son assiette.

« PN (KG) » : le poids net en kilos (718 droits). « QCS » : l'unité statistique
de la position, publiée avec elle (« NOMBRE », « LITRE »…). « QCI » n'a pas
d'unité publiée (champ vide sur les 17 542 positions) et « PN(KG)/100 EXCES »
renvoie à un seuil non publié : ces 1 158 droits restent non liquidables au
lieu d'être multipliés par une quantité d'unité inconnue.
"""

import json
import os

import pytest

from services.calcul import MANQUE_ASSIETTE, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "TUN.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(scope="module")
def positions():
    with open(os.path.join(SOCLE, "TUN.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _ligne(r, code):
    return next(l for l in r["npf"]["lignes"] if l["code"] == code)


def test_l_unite_statistique_de_la_position_porte_le_droit_qcs(positions):
    """Chevaux 0101.21 : D.S.V. « 0.1 dinars », assiette QCS, unité NOMBRE."""
    r = calculer(positions["0101210001"], 1000, quantite=2, devise_cif="TND")
    dsv = _ligne(r, "DSV")
    assert dsv["unite_quantite"] == "nombre" and dsv["montant"] == 0.2


def test_le_poids_net_porte_le_droit_pn_kg(positions):
    r = calculer(positions["0201100001"], 1000, quantite=2, devise_cif="TND")
    assert _ligne(r, "TMABATT")["unite_quantite"] == "kg"


def test_un_seuil_d_exces_non_publie_ne_se_liquide_pas(positions):
    """Viande 0201.10 : D.S.V. « 0.05 dinars », assiette « PN(KG)/100 EXCES »."""
    r = calculer(positions["0201100001"], 1000, quantite=2, devise_cif="TND")
    assert _ligne(r, "DSV")["statut"] == MANQUE_ASSIETTE
    assert r["npf"]["etat"] != "COMPLET"


def test_aucun_droit_specifique_ne_se_liquide_sans_unite(positions):
    sans_unite = [
        d
        for p in positions.values()
        for d in p["droits"]
        if isinstance(d.get("specifique"), dict)
        and d.get("assiette") == "xQTE"
        and not d["specifique"].get("unite_quantite")
    ]
    assert sans_unite == []
