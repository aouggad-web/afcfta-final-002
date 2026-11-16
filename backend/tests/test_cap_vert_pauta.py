"""Cap-Vert : Pauta Aduaneira 2022 modifiée par la Lei 51/X/2025 et la Lei
69/X/2025 (OE 2026) ; DI et taxa comunitária CEDEAO (0,5 %) sur la valeur en
douane ; ICE sur la valeur et tous droits et taxes sauf lui-même (Regulamento do
ICE, art. 13) ; IVA sur la valeur et tous droits et taxes sauf elle-même
(Regulamento do IVA, art. 16). Fiche : CPV_pauta_IVA_ICE_2026-10-12.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CPV.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position, quantite=None):
    r = calculer(position, 1_000_000, devise_cif="CVE", quantite=quantite)["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_pauta_sans_redevance_statistique(positions):
    """6 135 positions de la Pauta 2022, 110 supprimées et 554 créées par la Lei 51."""
    assert len(positions) == 6579
    assert not any(d["code"] == "RS" for p in positions.values() for d in p["droits"])


def test_iva_sur_la_valeur_et_tous_les_droits(positions):
    """0106.11 (primates vivants) : DI 5 %, TC 0,5 %, IVA 15 % sur 1 055 000."""
    etat, lignes = _calcul(positions["0106110000"])
    assert etat == "COMPLET"
    assert (lignes["DD"]["montant"], lignes["PCC"]["montant"]) == (50_000.0, 5_000.0)
    assert lignes["TVA"]["base"] == 1_055_000.0


def test_iva_exoneree_is(positions):
    etat, lignes = _calcul(positions["0101210000"])
    assert etat == "COMPLET" and lignes["TVA"]["montant"] == 0.0


def test_ice_puis_iva(positions):
    """2202.10 (eaux sucrées) : DI 55 %, ICE 10 % sur 1 555 000, IVA sur la somme."""
    etat, lignes = _calcul(positions["2202100000"])
    assert lignes["ICE"]["base"] == 1_555_000.0 and lignes["ICE"]["montant"] == 155_500.0
    assert lignes["TVA"]["base"] == pytest.approx(1_710_500.0)


def test_taxe_tabac_dans_l_assiette_de_l_ice(positions):
    """Cigarettes : 180$00 par paquet (art. 90), comptés dans l'assiette de l'ICE."""
    etat, _ = _calcul(positions["2402200000"])
    assert etat != "COMPLET"
    etat, lignes = _calcul(positions["2402200000"], quantite=100)
    assert etat == "COMPLET" and lignes["TET"]["montant"] == 18_000.0
    assert lignes["ICE"]["base"] == 1_273_000.0
    assert lignes["TVA"]["base"] == pytest.approx(1_273_000.0 + 636_500.0)


def test_ice_specifique_des_vehicules(positions):
    """Annexe II de l'OE 2026 : 100 000 CVE par véhicule, dans l'assiette de l'IVA."""
    etat, lignes = _calcul(positions["8703900000"], quantite=1)
    assert etat == "COMPLET" and lignes["ICES"]["montant"] == 100_000.0
    assert lignes["TVA"]["base"] == 1_605_000.0


def test_di_reduit_par_l_oe_2026(positions):
    """Annexe III de la Lei 69/X/2025 : poissons d'ornement d'eau douce à 10 %."""
    assert next(d for d in positions["0301110000"]["droits"] if d["code"] == "DD")["taux"] == 10.0


def test_vehicules_electriques_exoneres(positions):
    etat, lignes = _calcul(positions["8703802019"])
    assert etat == "COMPLET" and "ICE" not in lignes
    assert lignes["DD"]["montant"] == 0.0 and lignes["TVA"]["montant"] == 0.0


def test_alcool_declare_incomplet(positions):
    """Taxe par litre (Lei 45/X/2024, art. 77) : sans quantité en litres, total incomplet."""
    etat, _ = _calcul(positions["2208300000"])
    assert etat != "COMPLET"


def test_tc_retiree_pour_une_origine_cedeao(positions):
    _, retires = exoneration_origine.appliquer(positions["0106110000"], "SEN")
    assert {r["code"] for r in retires} == {"PCC"}
    _, retires_hors = exoneration_origine.appliquer(positions["0106110000"], "CHN")
    assert not retires_hors
