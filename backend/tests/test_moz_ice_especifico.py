"""Mozambique : taux spécifiques de l'ICE (« ICE_VAL_MIN » de la Pauta), lus
dans la tabela anexa du Código do ICE (Lei n.º 19/2022, prorogée par la Lei
n.º 7/2025). Fiche : MOZ_ice_especifico_2026-10-26.json."""

import importlib.util
import json
import os
import re

import pytest

from services import socle
from services.calcul import calculer

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RACINE = os.path.dirname(BACKEND)


def _constructeur():
    spec = importlib.util.spec_from_file_location(
        "build_socle_moz_test", os.path.join(RACINE, "scripts", "build_socle.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _minimums_de_la_pauta():
    with open(os.path.join(BACKEND, "data", "crawled", "MOZ_tariffs.json"), encoding="utf-8") as f:
        donnees = json.load(f)
    return {
        p["national_code"]: float(re.match(r"[\d.]+", t["raw_value"]).group())
        for p in donnees["sub_positions"]
        for t in p["taxes"]
        if t["code"] == "ICE_VAL_MIN"
    }


def test_chaque_minimum_de_la_pauta_a_son_montant_dans_la_tabela():
    bs = _constructeur()
    for code, montant in _minimums_de_la_pauta().items():
        if code in bs.ICE_ESPECIFICO_MOZ:
            assert bs.ICE_ESPECIFICO_MOZ[code][0] == montant, code
        else:
            _, brut, _ = next(r for r in bs.ICE_NON_LIQUIDABLE_MOZ if code.startswith(r[0]))
            assert float(brut.split("/")[0].replace(",", ".")) == montant, code


SOCLE_MOZ = os.path.join(socle.SOCLE_DIR, "MOZ.json")
avec_socle = pytest.mark.skipif(not os.path.exists(SOCLE_MOZ), reason="socle absent (gitignoré)")


def _position(code):
    with open(SOCLE_MOZ, encoding="utf-8") as f:
        return json.load(f)["positions"][code]


def _lignes(code, cif, quantite):
    lignes = calculer(_position(code), cif, quantite=quantite, taux_de_change=1.0)["npf"]["lignes"]
    return {ligne["code"]: ligne for ligne in lignes}


@avec_socle
def test_plus_aucune_ligne_ice_val_min():
    with open(SOCLE_MOZ, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    assert not [c for c, p in positions.items() for d in p["droits"] if d["code"] == "ICEVALMIN"]


@avec_socle
def test_le_tabac_paie_le_plus_eleve_de_l_ad_valorem_et_du_specifique():
    # 75 % de (CIF + DD) = 9 000 MT ; 550 MT/kg × 10 kg = 5 500 MT.
    ice = _lignes("24021000", 10000.0, 10.0)["ICE"]
    assert ice["statut"] == "CALCULE" and ice["montant"] == 9000.0
    assert ice["composante_retenue"] == "ad_valorem"
    # 550 MT/kg × 100 kg = 55 000 MT l'emporte.
    ice = _lignes("24021000", 10000.0, 100.0)["ICE"]
    assert ice["montant"] == 55000.0 and ice["composante_retenue"] == "specifique"


@avec_socle
def test_le_vehicule_d_occasion_paie_son_montant_par_unite():
    lignes = _lignes("87032120", 100000.0, 1.0)
    # 5 % de 120 000 MT = 6 000 MT < 12 000 MT/unid.
    assert lignes["ICE"]["montant"] == 12000.0
    assert lignes["TVA"]["statut"] == "CALCULE"


@avec_socle
def test_le_carburant_se_taxe_au_litre_de_la_tabela():
    ice = _lignes("27101239", 10000.0, 1000.0)["ICE"]
    assert ice["montant"] == 7710.0
    assert _position("27101239")["droits"][1]["specifique"]["unite_quantite"] == "litre"


@avec_socle
@pytest.mark.parametrize("code", ["22083000", "20091200", "22071090"])
def test_sucre_et_alcool_pur_restent_non_liquidables(code):
    lignes = _lignes(code, 10000.0, 10.0)
    assert lignes["ICE"]["montant"] is None
    assert lignes["TVA"]["montant"] is None
