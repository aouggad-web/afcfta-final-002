"""CEMAC : la TCI ne frappe que les produits originaires des pays tiers (acte
additionnel n° 03/00-CEMAC-046-CM-05, art. 2). Fiche : CEMAC_TCI_origine_2026-10-30.json."""

import json
import os

import pytest

from services import exoneration_origine
from services.calcul import COMPLET, calculer

SOCLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")
CEMAC = ("CMR", "CAF", "COG", "GAB", "GNQ", "TCD")


def _position(iso, code="01011010"):
    chemin = os.path.join(SOCLES, f"{iso}.json")
    if not os.path.exists(chemin):
        pytest.skip("socle absent (gitignoré)")
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)["positions"][code]


@pytest.mark.parametrize("destination", CEMAC)
def test_un_originaire_de_la_cemac_ne_paie_pas_la_tci(destination):
    origine = "GAB" if destination != "GAB" else "CMR"
    _, retires = exoneration_origine.appliquer(_position(destination), origine)
    assert "TCI" in {e["code"] for e in retires}


@pytest.mark.parametrize("destination", CEMAC)
@pytest.mark.parametrize("origine", ["FRA", "NGA", "AGO", None])
def test_hors_cemac_ou_sans_origine_la_tci_reste_due(destination, origine):
    _, retires = exoneration_origine.appliquer(_position(destination), origine)
    assert "TCI" not in {e["code"] for e in retires}


def test_la_tva_du_tchad_ne_compte_plus_la_tci_retiree():
    """TVA tchadienne sur CIF + DD + TCI + DA : la TCI non due ne grossit pas la base."""
    position, _ = exoneration_origine.appliquer(_position("TCD"), "CMR")
    r = calculer(position, 1000, devise_position="XAF", devise_cif="XAF")
    lignes = {l["code"]: l for l in r["npf"]["lignes"]}
    assert "TCI" not in lignes and lignes["TVA"]["base"] == 1050.0 and r["npf"]["etat"] == COMPLET


def test_la_taxe_conjoncturelle_de_l_uemoa_n_est_pas_touchee():
    chemin = os.path.join(SOCLES, "MLI.json")
    if not os.path.exists(chemin):
        pytest.skip("socle absent (gitignoré)")
    with open(chemin, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    tci = [d for p in positions.values() for d in p["droits"] if d["code"] == "TCI"]
    assert tci and not any(d.get("exoneration_origine") for d in tci)
