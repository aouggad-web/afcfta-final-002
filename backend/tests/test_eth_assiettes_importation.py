"""Éthiopie : accise sur CIF + DD (Proclamation 1186/2020 art. 9) ; TVA sur CIF +
droits et accise (Proclamation 1341/2024 art. 27) ; surtaxe sur CIF + DD +
accise + TVA (Règlement 133/2007) ; WHR 3 % du CIF (Proclamation 979/2016
art. 85). Fiche : ETH_assiettes_importation_2026-10-07.json."""

import json
import os

import pytest
from services.calcul import COMPLET, calculer

SOCLE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "ETH.json"
)
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(position):
    r = calculer(position, 1000, devise_position="ETB")
    return r["npf"]["etat"], {l["code"]: l for l in r["npf"]["lignes"]}


def test_biere_accise_sur_cif_et_droit_puis_tva_et_whr(positions):
    """2203 : DD 35 %, accise le plus élevé de 40 % sur 1 350 et de 28 Birr par
    litre (directive 1007/2024), TVA sur 4 150, surtaxe 10 % de CIF + DD +
    accise + TVA (Règlement 133/2007), WHR 3 % de 1 000 ; pas de taxe sociale,
    la bière étant soumise à la surtaxe (Règlement 519/2022, art. 6(2))."""
    r = calculer(positions["22030000000"], 1000, quantite=100, devise_position="ETB")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert (lignes["EXC"]["base"], lignes["EXC"]["montant"]) == (1350.0, 2800.0)
    assert lignes["TVA"]["base"] == 1000.0 + 350.0 + 2800.0
    assert lignes["SUR"]["base"] == 4150.0 + 622.5
    assert (lignes["WHR"]["base"], lignes["WHR"]["montant"]) == (1000.0, 30.0)
    assert "SWL" not in lignes
    assert r["npf"]["etat"] == COMPLET


def test_surtaxe_ou_taxe_sociale_jamais_les_deux(positions):
    """Règlement 519/2022, art. 6(2) : la taxe sociale exempte les marchandises
    soumises à la surtaxe ; elle ne vise que les exemptées de l'art. 5 du
    Règlement 133/2007 (engrais, pétrole, véhicules, aéronefs)."""
    for position in positions.values():
        codes = [d["code"] for d in position["droits"]]
        assert ("SUR" in codes) != ("SWL" in codes)
    for code in ("31021000000", "27101220000", "87032313000", "88024000000"):
        etat, lignes = _lignes(positions[code])
        assert "SUR" not in lignes and (lignes["SWL"]["base"], lignes["SWL"]["montant"]) == (1000.0, 30.0)


def test_surtaxe_a_trancher_sans_taux(positions):
    """Pommes de terre : exclues de la surtaxe par une directive non lue ; la
    surtaxe reste à compléter, le total est partiel."""
    sur = next(d for d in positions["07019000000"]["droits"] if d["code"] == "SUR")
    assert sur["taux"] is None
    assert _lignes(positions["07019000000"])[0] != COMPLET


def test_accise_bornee_aux_sous_positions_de_l_annexe(positions):
    """Sacs de caisse : 103 Birr/kg (directive 1007/2024) ; les autres sacs et
    le talc pour bébé, hors annexe, restent sans accise, comme au portail."""
    r = calculer(positions["39232110000"], 1000, quantite=10, devise_position="ETB")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert lignes["EXC"]["montant"] == 1030.0
    for code in ("39232190000", "33049120000", "18010000000", "68118100000"):
        assert not any(d["code"] == "EXC" for d in positions[code]["droits"])
    rtd = next(d for d in positions["22089010000"]["droits"] if d["code"] == "EXC")
    assert rtd["regle_composee"] == "LE_PLUS_ELEVE" and rtd["specifique"]["montant"] == 28.0


def test_la_surtaxe_s_assoit_sur_la_tva(positions):
    etat, lignes = _lignes(positions["40159090000"])
    assert lignes["TVA"]["base"] == 1350.0 and lignes["SUR"]["base"] == 1552.5
    assert "SWL" not in lignes
