"""
Une préférence qui ne réduit rien n'est pas annoncée comme appliquée.

Audit du 2026-10-09, point 4 : DZA/8703101100 depuis la Tunisie répondait
« APPLIED » avec un droit de 30 % — le NPF lui-même, la position étant sur la
liste (A) gelée. L'écran affichait « ZLECAf appliqué » et une économie nulle.
"""

from __future__ import annotations

import os

import pytest

from services import socle
from services.preference import taux_preferentiels

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

besoin_socle = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "DZA.json")),
    reason="socle absent (gitignoré) : reconstruire avec scripts/build_socle.py",
)


@besoin_socle
def test_une_position_gelee_n_est_pas_dite_appliquee():
    position, _ = socle.position("DZA", "8703101100")
    decision = taux_preferentiels(position, "DZA", "TUN", "8703101100")

    assert decision["applique"] is False
    assert decision["statut"] == "PREFERENCE_SANS_EFFET"
    assert decision["taux"] == {}
    assert decision["motif"].startswith("Liste (A) gelée")
    assert "droit commun" in decision["motif"]
    assert "taux NPF appliqué" in decision["note"]


@besoin_socle
def test_une_preference_qui_reduit_reste_appliquee():
    # Café robusta, liste (A) : DD démantelé et DAPS exonéré.
    position, _ = socle.position("DZA", "0901111000")
    decision = taux_preferentiels(position, "DZA", "TUN", "0901111000")

    assert decision["applique"] is True
    assert decision["statut"] == "APPLIED"


def test_un_seul_prelevement_reduit_suffit():
    """Le DAPS exonéré donne un effet à la préférence, même si le DD reste au NPF."""
    from services.preference import _sans_effet

    position = {"droits": [{"code": "DD", "taux": 30.0}, {"code": "DAPS", "taux": 70.0}]}
    assert _sans_effet({"DD": {"taux": 30.0}}, position) is True
    assert _sans_effet({"DD": {"taux": 30.0}, "DAPS": {"taux": 0.0}}, position) is False
    # Un NPF déjà nul n'a rien à démanteler : rien n'y est fictif.
    assert _sans_effet({"DD": {"taux": 0.0}}, {"droits": [{"code": "DD", "taux": 0.0}]}) is False
