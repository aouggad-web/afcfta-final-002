"""Prélèvement OHADA selon le règlement n° 002/2003/CM : nul sur les produits
pharmaceutiques et le matériel médical, non dû par les originaires de la CEEAC.
Fiche : OHADA_reglement_002_2003_2026-10-31.json."""

import json
import os

import pytest

from services import exoneration_origine

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")


def _positions(iso):
    chemin = os.path.join(SOCLE, f"{iso}.json")
    if not os.path.exists(chemin):
        pytest.skip("socle absent (gitignoré)")
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _ohada(position):
    return next(d for d in position["droits"] if d["code"] == "OHADA")


@pytest.mark.parametrize("iso", ["GAB", "CAF", "TCD", "CMR", "COG", "GNQ"])
def test_produits_pharmaceutiques_et_materiel_medical_exoneres(iso):
    positions = _positions(iso)
    for code in ("30049000", "90189000", "94021010", "94029000"):
        assert _ohada(positions[code])["taux"] == 0.0, (iso, code)
    assert _ohada(positions["01011010"])["taux"] == 0.05
    assert _ohada(positions["94021020"])["taux"] == 0.05  # fauteuils de coiffeur


@pytest.mark.parametrize("iso", ["GAB", "CAF", "TCD", "CMR", "COG", "GNQ"])
def test_les_originaires_de_la_ceeac_hors_ohada_ne_le_paient_pas(iso):
    positions = _positions(iso)
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], "AGO")
    assert "OHADA" in {e["code"] for e in exonerations}
    _, exonerations = exoneration_origine.appliquer(positions["01011010"], "NGA")
    assert "OHADA" not in {e["code"] for e in exonerations}
