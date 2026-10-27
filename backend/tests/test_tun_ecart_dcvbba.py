"""Tunisie : le DCVBBA de la bière et du vin, servi au double du taux légal.

Le Tarif Web sert 4,8 D/l là où le tableau annexé à la loi n° 88-62 porte
2,4 D/l (loi n° 2020-46, art. 20), 15 D/hl pour 7,5 D/hl, 7,5 D pour 3,75 D
par unité. Les montants sont conservés ; chaque droit le dit par une note.
"""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "TUN.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(scope="module")
def positions():
    with open(os.path.join(SOCLE, "TUN.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _dcvbba(positions):
    return [
        d
        for code, p in positions.items()
        if code.startswith(("2203", "2204"))
        for d in p["droits"]
        if d.get("code_source") == "DCVBBA" and d.get("assiette") == "xQTE"
    ]


def test_chaque_dcvbba_specifique_porte_la_note(positions):
    droits = _dcvbba(positions)
    assert len(droits) == 364
    assert all(d.get("note", "").startswith("Montant du Tarif Web conservé.") for d in droits)


def test_le_montant_reste_celui_du_tarif_web(positions):
    """Bière ≤ 0,320 l : 4,8 D/l servis, note visible dans la liquidation."""
    r = calculer(positions["2203000101"], 1000, quantite=10, devise_cif="TND")
    ligne = next(l for l in r["npf"]["lignes"] if l["code"] == "DCVBBA")
    assert ligne["montant"] == pytest.approx(48.0)
    assert "2,4 D/litre" in ligne["note"] and "le double" in ligne["note"]


def test_l_unite_au_decilitre_est_signalee_a_part(positions):
    notes = {d["note"] for d in _dcvbba(positions) if d["specifique"]["unite_quantite"] == "deciltre"}
    assert any("vingt fois" in n for n in notes)
