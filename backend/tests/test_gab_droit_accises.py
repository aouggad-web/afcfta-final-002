"""Gabon : droit d'accises de l'art. 250 du CGI réécrit par la loi de finances
2026 (n° 041/2025) et la loi de finances rectificative 2026 (n° 002/2026).
Fiche : GAB_droit_accises_2026-10-29.json."""

import json
import os

import pytest

from services.calcul import COMPLET, PARTIEL, calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "GAB.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position, quantites=None):
    r = calculer(position, 1000, quantites=quantites, devise_position="XAF", devise_cif="XAF")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_une_biere_importee_paie_25_pour_cent_et_200_fcfa_par_litre(positions):
    """CIF 1 000, 100 litres : DA = 25 % de 1 312 (CIF + DD 300 + TCI 10 + CIA 2)
    + 200 × 100 = 20 328 ; TVA 18 % sur CIF + DD + DA = 21 628."""
    etat, lignes = _lignes(positions["22030010"], {"litre": 100})
    assert (lignes["DA"]["base"], lignes["DA"]["montant"]) == (1312.0, 20328.0)
    assert lignes["TVA"]["base"] == 21628.0 and etat == COMPLET


def test_sans_le_volume_l_accise_n_est_pas_reduite_a_sa_part_ad_valorem(positions):
    etat, lignes = _lignes(positions["22030010"])
    assert lignes["DA"]["montant"] is None and etat == PARTIEL


@pytest.mark.parametrize(
    "code, specifique",
    [("22041010", 2250), ("22041090", 1750), ("22042110", 1750), ("22051000", 1750), ("22082000", 500)],
)
def test_vins_champagnes_et_spiritueux(positions, code, specifique):
    """LFR 2026 : champagnes 32 % + 2 250 FCFA/l, vins 32 % + 1 750 FCFA/l ;
    LF 2026 : boissons de plus de 12 % vol. 30 % + 500 FCFA/l."""
    taux = 30.0 if code.startswith("2208") else 32.0
    etat, lignes = _lignes(positions[code], {"litre": 1})
    assert lignes["DA"]["montant"] == round(1312.0 * taux / 100 + specifique, 4)
    assert etat == COMPLET


def test_les_cigarettes_paient_32_pour_cent_et_250_fcfa_par_paquet(positions):
    etat, lignes = _lignes(positions["24022000"], {"paquet": 10})
    assert lignes["DA"]["montant"] == 1312.0 * 0.32 + 2500 and etat == COMPLET


@pytest.mark.parametrize(
    "code, taux",
    [("87032310", 5.0), ("87033310", 5.0), ("87111000", 1.0), ("87042100", 1.0), ("87051000", 1.0), ("93020000", 10.0), ("20091100", 5.0)],
)
def test_taux_ad_valorem_de_la_loi_de_finances_2026(positions, code, taux):
    etat, lignes = _lignes(positions[code])
    assert lignes["DA"]["montant"] == round(lignes["DA"]["base"] * taux / 100, 4) and etat == COMPLET


def test_les_tracteurs_agricoles_ne_portent_pas_l_accise(positions):
    etat, lignes = _lignes(positions["87019011"])
    assert "DA" not in lignes and etat == COMPLET


def test_une_petite_cylindree_reste_sans_taux_faute_de_savoir_si_elle_est_neuve(positions):
    etat, lignes = _lignes(positions["87032210"])
    assert lignes["DA"]["statut"] == "TAUX_INDISPONIBLE" and etat == PARTIEL


def test_huit_accises_seulement_restent_sans_taux(positions):
    accises = [d for p in positions.values() for d in p["droits"] if d["code"] == "DA"]
    sans_taux = [d for d in accises if d["taux"] is None]
    assert len(accises) == 126 and len(sans_taux) == 8
    assert all(d["note"] for d in sans_taux)
    assert all(d["source"].startswith("Code général des impôts du Gabon, art. 250") for d in accises)
