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


@besoin_socle
def test_un_taux_zlecaf_au_dessus_du_npf_n_est_pas_dit_applique():
    # Viande bovine, liste (B) : 24 % au calendrier pour un DD NPF de 5 %,
    # que le moteur sert (plancher NPF) ; le DAPS, NPF 0 %, n'a rien à réduire.
    position, _ = socle.position("DZA", "0201101100")
    decision = taux_preferentiels(position, "DZA", "TUN", "0201101100")

    assert decision["applique"] is False
    assert decision["statut"] == "PREFERENCE_SANS_EFFET"
    assert decision["taux"] == {}


def test_un_seul_prelevement_reduit_suffit():
    """Le DAPS exonéré donne un effet à la préférence, même si le DD reste au NPF."""
    from services.preference import _sans_effet

    position = {"droits": [{"code": "DD", "taux": 30.0}, {"code": "DAPS", "taux": 70.0}]}
    assert _sans_effet({"DD": {"taux": 30.0}}, position) is True
    assert _sans_effet({"DD": {"taux": 30.0}, "DAPS": {"taux": 0.0}}, position) is False
    # Un NPF déjà nul n'a rien à démanteler : rien n'y est fictif.
    assert _sans_effet({"DD": {"taux": 0.0}}, {"droits": [{"code": "DD", "taux": 0.0}]}) is False
    # Un prélèvement à NPF nul est ignoré quand un autre se compare.
    position = {"droits": [{"code": "DD", "taux": 5.0}, {"code": "DAPS", "taux": 0.0}]}
    assert _sans_effet({"DD": {"taux": 24.0}, "DAPS": {"taux": 0.0}}, position) is True
    assert _sans_effet({"DD": {"taux": 5.0}, "DAPS": {"taux": 0.0}}, position) is True
    assert _sans_effet({"DD": {"taux": 2.0}, "DAPS": {"taux": 0.0}}, position) is False
    # Un NPF inconnu ne se compare pas : la préférence reste servie.
    assert _sans_effet({"DD": {"taux": 5.0}}, {"droits": []}) is False


# ── La règle d'origine accompagne la préférence (audit, point 11) ─────────────
@besoin_socle
def test_la_preference_appliquee_porte_sa_regle_d_origine():
    from routes.calcul import DemandeCalcul, calcul

    reponse = calcul(
        DemandeCalcul(destination="DZA", origine="TUN", code_sh="0901111000", valeur_cif=10000)
    )
    regle = reponse["regle_origine"]
    assert regle["hs6"] == "090111"
    assert regle["regle"]["code"] == "WO"
    assert regle["regle"]["nom"] == {"fr": "Entièrement Obtenu", "en": "Wholly Obtained"}
    assert "certificat d'origine ZLECAf" in regle["reserve"]


@besoin_socle
def test_sans_preference_aucune_regle_d_origine_n_est_jointe():
    from routes.calcul import DemandeCalcul, calcul

    reponse = calcul(
        DemandeCalcul(destination="DZA", origine="TUN", code_sh="8703101100", valeur_cif=10000)
    )
    assert "regle_origine" not in reponse
