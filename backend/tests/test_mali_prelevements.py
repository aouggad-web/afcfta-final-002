"""Mali : tarif de la DGD (TEC CEDEAO, édition du Mali, 28/12/2023) ; ISCP sur la
valeur en douane majorée des droits et taxes dus à l'entrée (CGI art. 243) ;
TVA sur la valeur CAF et tous les droits et taxes autres que la TVA (CGI
art. 198 et 199). Fiche : MLI_prelevements_TVA_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "MLI.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_prelevements_du_tarif_et_tva(positions):
    """0101.21 : DD 5 % : 50 ; RS 10 ; PC-AES 5 ; PCS 0,8 % : 8 ; TVA 18 % sur 1 073."""
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET"
    assert [lignes[c]["montant"] for c in ("DD", "RS", "PC-AES", "PCS")] == [50.0, 10.0, 5.0, 8.0]
    assert lignes["TVA"]["base"] == 1073.0


def test_iscp_sur_valeur_et_droits_d_entree(positions):
    """Bière 2203.00.10 : ISCP 50 % sur 1 000 + 200 + 10 + 5 + 8 ; TVA sur cette base + ISCP."""
    etat, lignes = _calcul(positions["2203001000"])
    assert lignes["ISCP"]["base"] == 1223.0 and lignes["ISCP"]["montant"] == 611.5
    assert lignes["TVA"]["base"] == 1834.5


def test_tai_droit_d_entree(positions):
    """0101.29 : TAI 5 % sur la valeur CAF, comprise dans la base de la TVA."""
    etat, lignes = _calcul(positions["0101290000"])
    assert lignes["TAI"]["montant"] == 50.0
    assert lignes["TVA"]["base"] == 1173.0


def test_tci_sans_assiette_rend_la_tva_indisponible(positions):
    etat, lignes = _calcul(positions["1701120000"])
    assert lignes["TCI"]["montant"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"


def test_tva_du_tarif_officiel(positions):
    taux = {d["code"]: d["taux"] for d in positions["0101210000"]["droits"]}
    assert taux["PCS"] == 0.8 and "PCC" not in taux
