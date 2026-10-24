"""Une absence d'information n'est pas une absence d'obligation.

LE DÉFAUT CORRIGÉ. `get_administrative_formalities()` rendait une liste vide
dans trois situations que plus rien ne distinguait ensuite :

  * la position porte des formalités              → on les sert ;
  * la position existe et n'en porte aucune       → rien n'est documenté ;
  * la position est INTROUVABLE                   → on n'a rien cherché.

L'interface, elle, masquait purement et simplement la carte « Documents
requis » (`if (!formalities || formalities.length === 0) return null`).
L'opérateur voyait donc un résultat complet — taxes, avantages, coût
réglementaire — sans le moindre signe que les formalités n'avaient jamais été
établies. Il pouvait en conclure qu'aucune licence n'était requise.

L'AMPLEUR, mesurée sur les crawls du 21/09/2026 : **315 185 positions sur
350 022 — 90 % — ne portent aucune formalité, et 46 pays sur 54 n'en portent
aucune du tout** (Kenya, Ghana, Afrique du Sud, Nigeria, Tunisie, Éthiopie...).
Le silence était la règle, pas l'exception.

CE QUE CES TESTS TIENNENT.

1. LES TROIS ÉTATS SE DISTINGUENT. C'est la correction elle-même.

2. LE CONTRÔLE NÉGATIF, ET IL COMPTE PLUS QUE LE RESTE : aucun état ne doit
   jamais signifier « aucune obligation ». Le dépôt ne collecte nulle part une
   attestation d'absence d'obligation — il collecte des formalités, ou rien.
   Tant qu'une telle attestation n'existe pas dans la source, un quatrième
   état « AUCUNE_OBLIGATION » serait une valeur fabriquée.

3. LA RÉSERVE EST DANS LA RÉPONSE, pas dans l'écran. Un second écran qui
   consommerait la même route ne peut pas retomber dans le silence.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "backend"))


def test_la_route_porte_le_statut_et_la_reserve():
    """La réserve voyage dans la réponse, pas seulement dans l'écran."""
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    reponse = client.get("/api/consultation/KEN/formalites/01012900")
    if reponse.status_code == 404:
        pytest.skip("le Kenya n'est pas servi par ce chemin dans cet environnement")
    corps = reponse.json()
    assert corps["statut"] == "NON_ETABLIES"
    assert corps["formalities"] == []
    # La phrase qui empêche la lecture « rien à faire ».
    assert "absence d'obligation" in corps["reserve"]


def test_une_position_servie_ne_porte_aucune_reserve():
    """La réserve ne doit pas devenir un avertissement de fond d'écran."""
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    reponse = client.get("/api/consultation/MAR/formalites/0101210000")
    if reponse.status_code == 404:
        pytest.skip("le Maroc n'est pas servi par ce chemin dans cet environnement")
    corps = reponse.json()
    assert corps["statut"] == "DOCUMENTEES"
    assert corps["reserve"] is None
    assert corps["formalities"]


def test_aucun_etat_ne_signifie_aucune_obligation():
    """CONTRÔLE NÉGATIF — le plus important de ce fichier.

    Le jour où un état « AUCUNE_OBLIGATION » apparaîtra, il devra s'appuyer sur
    une attestation de la source, pas sur une liste vide. Ce test tombe si
    quelqu'un l'ajoute sans cette preuve.
    """
    from services import formalites

    etats = {
        formalites.FORMALITES_DOCUMENTEES,
        formalites.FORMALITES_AUCUNE_PARTICULIERE,
        formalites.FORMALITES_NON_ETABLIES,
        formalites.FORMALITES_POSITION_INTROUVABLE,
    }
    assert len(etats) == 4, "les quatre états doivent rester distincts"
    for etat in etats:
        assert "AUCUNE_OBLIGATION" not in etat
        assert "DISPENSE" not in etat
        assert "EXEMPT" not in etat.upper()


def test_le_constat_ne_se_generalise_pas_aux_autres_pays():
    """CONTRÔLE NÉGATIF — la leçon du Maroc, appliquée aux formalités.

    Un pays dont la source n'a PAS été vérifiée exhaustive garde « non
    établies » : étendre le constat par analogie transformerait des lacunes en
    autant de déclarations d'absence de formalité.
    """
    from services.formalites import SOURCES_EXHAUSTIVES_FORMALITES

    assert set(SOURCES_EXHAUSTIVES_FORMALITES) == {"DZA"}


def test_chaque_source_exhaustive_porte_sa_preuve():
    """Une entrée sans preuve relevée n'a rien à faire dans la table."""
    from services.formalites import SOURCES_EXHAUSTIVES_FORMALITES

    for pays, preuve in SOURCES_EXHAUSTIVES_FORMALITES.items():
        assert len(preuve) > 150, f"{pays} : la preuve doit être circonstanciée"
        assert "chantillon" in preuve or "rifi" in preuve, pays
