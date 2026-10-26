"""Tchad : droit d'accises et taxe spécifique de l'art. 36 de la LF 2021, dans
sa rédaction issue de la LF 2026 (art. 44). Fiche :
TCD_droit_accises_2026-10-26.json."""

import json
import os

import pytest

from services import socle
from services.calcul import calculer

SOCLE_TCD = os.path.join(socle.SOCLE_DIR, "TCD.json")
pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE_TCD), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE_TCD, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _droits(positions, code, code_droit):
    return [d for d in positions[code]["droits"] if d["code"] == code_droit]


@pytest.mark.parametrize("code,taux", [
    ("22021000", 10.0), ("22030010", 25.0), ("22042110", 25.0), ("22083000", 25.0),
    ("24022000", 30.0), ("24039910", 30.0), ("33030000", 20.0), ("33041000", 20.0),
    ("87113000", 12.5), ("87032410", 25.0), ("87033390", 25.0),
])
def test_le_droit_d_accises_suit_l_article_36(positions, code, taux):
    (da,) = _droits(positions, code, "DA")
    assert da["taux"] == taux and da["assiette"] == "CIF+DD"


@pytest.mark.parametrize("code", ["24039920", "87111000", "87032310", "52051100", "30049000"])
def test_hors_du_tableau_pas_de_droit_d_accises(positions, code):
    assert not _droits(positions, code, "DA")


def test_la_tva_s_assoit_sur_le_droit_d_accises(positions):
    lignes = {x["code"]: x for x in calculer(positions["22030010"], 100000.0)["npf"]["lignes"]}
    # DA : 25 % de (100 000 + 30 000) ; TVA : 18 % de (100 000 + 30 000 + 1 000 + 32 500).
    assert lignes["DA"]["montant"] == 32500.0
    assert lignes["TVA"]["montant"] == 29430.0


def test_la_taxe_specifique_par_paquet_se_liquide_sur_la_quantite(positions):
    lignes = {x["code"]: x for x in calculer(positions["24022000"], 100000.0, quantite=10)["npf"]["lignes"]}
    assert lignes["SPEC"]["montant"] == 500.0


def test_la_taxe_specifique_en_pourcentage_reste_sans_assiette(positions):
    (spec,) = _droits(positions, "22030010", "SPEC")
    assert spec["taux"] == 10.0 and spec["assiette"] is None
    assert not _droits(positions, "24039920", "SPEC")
