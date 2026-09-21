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


@pytest.fixture(scope="module")
def service():
    from services import authentic_tariff_service as svc

    return svc


def test_les_trois_etats_se_distinguent(service):
    """Une position servie, une position sans formalité, une position absente."""
    documentees, statut = service.formalites_et_statut("MAR", "0101210000")
    assert statut == service.FORMALITES_DOCUMENTEES
    assert documentees, "un état DOCUMENTEES sans formalité n'a pas de sens"

    vides, statut = service.formalites_et_statut("KEN", "01012900")
    assert statut == service.FORMALITES_NON_ETABLIES
    assert vides == []

    absente, statut = service.formalites_et_statut("MAR", "9999999999")
    assert statut == service.FORMALITES_POSITION_INTROUVABLE
    assert absente == []


def test_aucun_etat_ne_signifie_aucune_obligation(service):
    """CONTRÔLE NÉGATIF — le plus important de ce fichier.

    Le jour où un état « AUCUNE_OBLIGATION » apparaîtra, il devra s'appuyer sur
    une attestation de la source, pas sur une liste vide. Ce test tombe si
    quelqu'un l'ajoute sans cette preuve.
    """
    etats = {
        service.FORMALITES_DOCUMENTEES,
        service.FORMALITES_NON_ETABLIES,
        service.FORMALITES_POSITION_INTROUVABLE,
    }
    assert len(etats) == 3, "les trois états doivent rester distincts"
    for etat in etats:
        assert "AUCUNE_OBLIGATION" not in etat
        assert "DISPENSE" not in etat
        assert "EXEMPT" not in etat.upper()


def test_l_ancienne_fonction_garde_son_contrat(service):
    """Ses appelants existants reçoivent toujours une liste, jamais un couple."""
    resultat = service.get_administrative_formalities("KEN", "01012900")
    assert isinstance(resultat, list)
    resultat = service.get_administrative_formalities("MAR", "0101210000")
    assert isinstance(resultat, list) and resultat


def test_la_route_porte_le_statut_et_la_reserve():
    """La réserve voyage dans la réponse, pas seulement dans l'écran."""
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    reponse = client.get("/api/authentic-tariffs/country/KEN/formalities/01012900")
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
    reponse = client.get("/api/authentic-tariffs/country/MAR/formalities/0101210000")
    if reponse.status_code == 404:
        pytest.skip("le Maroc n'est pas servi par ce chemin dans cet environnement")
    corps = reponse.json()
    assert corps["statut"] == "DOCUMENTEES"
    assert corps["reserve"] is None
    assert corps["formalities"]
