"""Cameroun : droit d'accises à l'importation selon le CGI (annexe II, art. 138
et 142). Fiche : CMR_droit_accises_2026-10-05.json."""

import json
import os

import pytest

from services.calcul import COMPLET, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CMR.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position):
    r = calculer(position, 1000, devise_cif="XAF")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_un_produit_de_beaute_paie_l_accise_et_la_tva_sur_l_accise(positions):
    """33.04 : DA 25 % sur CIF + DD = 325 ; TVA 19,25 % sur CIF + DD + DA = 1 625."""
    etat, lignes = _lignes(positions["33049900"])
    assert (lignes["DA"]["base"], lignes["DA"]["montant"]) == (1300.0, 325.0)
    assert lignes["TVA"]["base"] == 1625.0 and etat == COMPLET


def test_un_tissu_de_coton_n_est_pas_soumis_a_l_accise(positions):
    """Le crawl le marquait « variable » ; l'annexe II ne le vise pas."""
    etat, lignes = _lignes(positions["52081100"])
    assert "DA" not in lignes and etat == COMPLET


def test_une_voiture_porte_l_accise_sans_taux_faute_d_age(positions):
    etat, lignes = _lignes(positions["87032310"])
    assert lignes["DA"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET


def test_aucun_reste_du_marquage_du_crawl(positions):
    accises = [d for p in positions.values() for d in p["droits"] if d["code"] == "DA"]
    assert len(accises) == 252
    assert all(d["source"].startswith("Code général des impôts du Cameroun") for d in accises)
