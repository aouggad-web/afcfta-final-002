"""Cameroun et Gabon : droit d'accises à l'importation selon le CGI (annexe II, art. 138
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


@pytest.mark.parametrize("code", ["34022000", "94033000", "55141100", "48181000", "95049000"])
def test_les_produits_importes_de_l_annexe_ii_paient_le_taux_general(positions, code):
    """Annexe II, p. 107-108 : savons et préparations de nettoyage, meubles en
    bois, tissus 5514 à 5516, papier hygiénique, jeux 9504 — 25 % (art. 142 (5))."""
    etat, lignes = _lignes(positions[code])
    assert lignes["DA"]["montant"] == lignes["DA"]["base"] * 0.25 and etat == COMPLET


def test_aucun_reste_du_marquage_du_crawl(positions):
    accises = [d for p in positions.values() for d in p["droits"] if d["code"] == "DA"]
    assert len(accises) == 477
    assert all(d["source"].startswith("Code général des impôts du Cameroun") for d in accises)


GAB = os.path.join(os.path.dirname(SOCLE), "GAB.json")


@pytest.mark.skipif(not os.path.exists(GAB), reason="socle absent (gitignoré)")
def test_gabon_cosmetique_au_taux_du_cgi_et_tissu_sans_accise():
    """CGI du Gabon, art. 250 et 216 : 25 % sur valeur + droits et taxes
    d'entrée hors TVA ; TVA sur valeur + DD + accise."""
    with open(GAB, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    etat, lignes = _lignes(positions["33049900"])
    assert (lignes["DA"]["base"], lignes["DA"]["montant"]) == (1312.0, 328.0)
    assert lignes["TVA"]["base"] == 1628.0 and etat == COMPLET
    etat, lignes = _lignes(positions["52081100"])
    assert "DA" not in lignes and etat == COMPLET


COG = os.path.join(os.path.dirname(SOCLE), "COG.json")


@pytest.mark.skipif(not os.path.exists(COG), reason="socle absent (gitignoré)")
def test_congo_taux_de_la_loi_de_finances_2026():
    """Loi sur le droit d'accises du Congo, art. 2 et 8 nouveaux (LF 2026) : tabac
    30 %, véhicule de plus de 3 000 cm3 25 %, champagne 50 %, perruques 10 %, sur
    valeur + DD ; TVA sur valeur + DD + accise. Cosmétiques et motocycles, visés
    par l'art. 8 : 25 %. Alcool éthylique : sans taux. Fiche : COG_droit_accises_2026-10-09.json."""
    with open(COG, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    etat, lignes = _lignes(positions["24022000"])
    assert (lignes["DA"]["base"], lignes["DA"]["montant"]) == (1300.0, 390.0)
    assert lignes["TVA"]["base"] == 1690.0 and etat == COMPLET
    assert _lignes(positions["87032410"])[1]["DA"]["montant"] == 325.0
    assert _lignes(positions["22041010"])[1]["DA"]["taux_pct"] == 50.0
    assert _lignes(positions["22041090"])[1]["DA"]["taux_pct"] == 25.0
    assert _lignes(positions["67041100"])[1]["DA"]["taux_pct"] == 10.0
    assert _lignes(positions["71132000"])[1]["DA"]["taux_pct"] == 5.0
    assert "DA" not in _lignes(positions["95044000"])[1]
    assert _lignes(positions["33049900"])[1]["DA"]["taux_pct"] == 25.0
    assert _lignes(positions["87113000"])[1]["DA"]["taux_pct"] == 25.0
    assert _lignes(positions["96140000"])[1]["DA"]["taux_pct"] == 30.0
    assert _lignes(positions["29072200"])[1]["DA"]["taux_pct"] == 50.0
    for code in ("22071010", "22021000", "95042000"):
        etat, lignes = _lignes(positions[code])
        assert lignes["DA"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET
    etat, lignes = _lignes(positions["52081100"])
    assert "DA" not in lignes and etat == COMPLET


CAF = os.path.join(os.path.dirname(SOCLE), "CAF.json")


@pytest.mark.skipif(not os.path.exists(CAF), reason="socle absent (gitignoré)")
def test_centrafrique_cosmetique_et_motocycle_au_taux_du_cgi_voiture_sans_taux():
    """CGI de Centrafrique, art. 289 bis, 291, 292 et annexe : 25 % et 12,5 %
    sur valeur + DD ; TVA sur valeur + DD + accise (art. 253). Véhicules :
    taux selon l'âge. Fiche : CAF_droit_accises_2026-10-05.json."""
    with open(CAF, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    etat, lignes = _lignes(positions["33049900"])
    assert (lignes["DA"]["base"], lignes["DA"]["montant"]) == (1300.0, 325.0)
    assert lignes["TVA"]["base"] == 1625.0 and etat == COMPLET
    _, lignes = _lignes(positions["87113000"])
    assert lignes["DA"]["montant"] == 162.5
    etat, lignes = _lignes(positions["87032410"])
    assert lignes["DA"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET
    etat, lignes = _lignes(positions["52081100"])
    assert "DA" not in lignes and etat == COMPLET


GNQ = os.path.join(os.path.dirname(SOCLE), "GNQ.json")


@pytest.mark.skipif(not os.path.exists(GNQ), reason="socle absent (gitignoré)")
def test_guinee_equatoriale_droits_specifiques_sans_taux_et_tissu_sans_accise():
    """Loi de budget 2020 : boissons et tabacs taxés par litre, degré ou unité,
    portés sans taux. Fiche : GNQ_droit_accises_2026-10-05.json."""
    with open(GNQ, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    etat, lignes = _lignes(positions["22030010"])
    assert lignes["DA"]["statut"] == "TAUX_INDISPONIBLE" and etat != COMPLET
    etat, lignes = _lignes(positions["52081100"])
    assert "DA" not in lignes and etat == COMPLET
