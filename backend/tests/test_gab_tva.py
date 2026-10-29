"""Gabon : TVA à l'importation, exonérations (CGI art. 210) et taux réduits
(art. 221) de la loi de finances 2026 et de la LFR 2026. Fiche : GAB_tva_2026-10-29.json."""

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


def _tva(position):
    return next(d for d in position["droits"] if d["famille"] == "tva")


@pytest.mark.parametrize(
    "code, taux",
    [
        ("10063010", 0.0),  # riz
        ("04021000", 0.0),  # lait en poudre
        ("30049000", 0.0),  # médicaments
        ("25232900", 0.0),  # ciment, exonéré bien qu'à 10 % dans la LF 2026
        ("20089110", 0.0),  # cœurs de palmier : conserves de légumes
        ("85023100", 0.0),  # aérogénérateurs : énergies renouvelables
        ("84714900", 10.0),  # ordinateurs
        ("87089900", 10.0),  # pièces détachées automobiles (LFR 2026)
        ("20089910", 10.0),  # conserves de fruits
        ("11010010", 5.0),  # farine
        ("04070090", 5.0),  # œufs
        ("19024000", 18.0),  # couscous, hors des pâtes alimentaires
        ("25231000", 18.0),  # clinkers, hors du ciment
        ("20081100", 18.0),  # arachides, hors des conserves de fruits
        ("02061000", 18.0),  # abats, hors des viandes
        ("01011010", 18.0),
    ],
)
def test_taux_de_tva_par_position(positions, code, taux):
    assert _tva(positions[code])["taux"] == taux


@pytest.mark.parametrize("code", ["72104100", "87119000", "27111300", "22011000"])
def test_taux_indetermine_depuis_la_position(positions, code):
    tva = _tva(positions[code])
    assert tva["taux"] is None and tva["note"]
    r = calculer(positions[code], 1000, devise_position="XAF", devise_cif="XAF")
    assert r["npf"]["etat"] == PARTIEL


def test_le_riz_ne_paie_pas_de_tva(positions):
    r = calculer(positions["10063010"], 1000, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert lignes["TVA"]["montant"] == 0.0 and r["npf"]["etat"] == COMPLET


def test_un_ordinateur_paie_10_pct_sur_l_assiette_de_l_art_216(positions):
    r = calculer(positions["84714900"], 1000, devise_position="XAF", devise_cif="XAF")
    tva = next(l for l in r["npf"]["lignes"] if l["code"] == "TVA")
    assert tva["montant"] == pytest.approx(tva["base"] * 0.10)
