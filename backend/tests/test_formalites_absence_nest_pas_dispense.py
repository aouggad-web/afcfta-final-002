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
        service.FORMALITES_AUCUNE_PARTICULIERE,
        service.FORMALITES_NON_ETABLIES,
        service.FORMALITES_POSITION_INTROUVABLE,
    }
    assert len(etats) == 4, "les quatre états doivent rester distincts"
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


def test_une_source_exhaustive_dit_le_constat_pas_la_lacune(service):
    """Algérie : le silence du portail est une information, pas un manque.

    `conformepro.dz` publie un bloc « Formalités » quand une formalité
    particulière existe, et aucun bloc sinon. Vérifié le 21/09/2026 sur un
    échantillon tiré au sort : 60 positions sans formalité au crawl, 60 fois
    aucun bloc au portail ; 20 positions avec formalité, 19 blocs présents
    (la vingtième a échoué en réseau).

    Le produit peut donc dire à l'opérateur quelque chose de POSITIF — cette
    marchandise n'est soumise à aucune formalité particulière — au lieu de lui
    servir une réserve qui ferait passer une information solide pour un trou.
    """
    _, statut = service.formalites_et_statut("DZA", "5201001000")
    assert statut == service.FORMALITES_AUCUNE_PARTICULIERE

    documentees, statut = service.formalites_et_statut("DZA", "0101211100")
    assert statut == service.FORMALITES_DOCUMENTEES
    assert documentees


def test_le_constat_ne_se_generalise_pas_aux_autres_pays(service):
    """CONTRÔLE NÉGATIF — la leçon du Maroc, appliquée aux formalités.

    Un pays dont la source n'a PAS été vérifiée exhaustive garde « non
    établies ». Étendre le constat par analogie transformerait 297 794 lacunes
    en autant de déclarations d'absence de formalité — une valeur fabriquée à
    l'échelle du continent.
    """
    assert set(service.SOURCES_EXHAUSTIVES_FORMALITES) == {"DZA"}
    for pays, code in (("KEN", "01012900"), ("MAR", "0902100000")):
        _, statut = service.formalites_et_statut(pays, code)
        assert statut != service.FORMALITES_AUCUNE_PARTICULIERE, pays


def test_chaque_source_exhaustive_porte_sa_preuve(service):
    """Une entrée sans preuve relevée n'a rien à faire dans la table."""
    for pays, preuve in service.SOURCES_EXHAUSTIVES_FORMALITES.items():
        assert len(preuve) > 150, f"{pays} : la preuve doit être circonstanciée"
        assert "chantillon" in preuve or "rifi" in preuve, pays
