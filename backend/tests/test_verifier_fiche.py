"""Le vérificateur de fiches doit juger le CONTENU, jamais la forme.

Deux défauts l'ont déjà prouvé nécessaire, tous deux du même genre :

- il reconnaissait une fiche à la présence d'un bloc ``regle`` et laissait donc
  passer, sans aucun contrôle d'empreinte, huit fichiers sur douze ;
- il exigeait une clé nommée exactement ``verbatim`` et refusait donc une fiche
  algérienne portant quatre citations sourcées sous ``verbatim_taux_normal``,
  ``verbatim_exoneration_import``…

Les deux fois, l'outil censé garantir la traçabilité se trompait sur une fiche
authentique — le pire défaut possible pour un garde-fou, puisqu'il pousse à
contourner l'outil plutôt qu'à corriger la donnée. Ces tests verrouillent le
contrat : ce qui est cité passe, ce qui est résumé échoue, quelle que soit la
façon dont c'est nommé.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "verifier_fiche", os.path.join(_RACINE, "scripts", "verifier_fiche.py")
)
verifier_fiche = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verifier_fiche)


def _ecrire(tmp_path, regle):
    fiche = {
        "schema_version": 1,
        "objet": "fiche de test",
        "verified_at": "2026-09-17",
        "regle": regle,
        "ce_que_cela_ne_tranche_pas": "rien",
    }
    chemin = tmp_path / "fiche.json"
    chemin.write_text(json.dumps(fiche, ensure_ascii=False), encoding="utf-8")
    return str(chemin)


@pytest.mark.parametrize(
    "cle",
    ["verbatim", "verbatim_taux_normal", "verbatim_exoneration_import"],
    ids=["nom_nu", "decline_taux", "decline_exoneration"],
)
def test_une_citation_compte_quel_que_soit_le_nom_de_sa_cle(tmp_path, cle):
    """Une fiche qui établit plusieurs valeurs décline ses citations.

    Les refuser jugerait la forme : c'est le défaut qui a fait échouer
    ``DZA_taux_TVA``, dont les quatre citations portaient chacune son article.
    """
    chemin = _ecrire(
        tmp_path,
        {"taux": 19.0, cle: "Art. 21 - La taxe sur la valeur ajoutée est perçue au taux de 19 %."},
    )
    anomalies, reserves, _ = verifier_fiche.verifier(chemin)

    assert not [a for a in anomalies if "verbatim" in a], anomalies
    assert not [r for r in reserves if "référence d'article" in r], reserves


def test_une_regle_sans_aucune_citation_reste_une_anomalie(tmp_path):
    """L'assouplissement ne doit pas désarmer le contrôle.

    Sans cette borne, élargir la reconnaissance des citations finirait par
    accepter une fiche qui résume sa source au lieu de la citer — exactement ce
    que l'outil existe pour refuser.
    """
    chemin = _ecrire(tmp_path, {"taux": 19.0, "portee": "TVA à 19 %"})
    anomalies, _, _ = verifier_fiche.verifier(chemin)

    assert any("verbatim absent" in a for a in anomalies), anomalies


def test_une_citation_qui_ne_nomme_pas_son_article_laisse_la_reserve(tmp_path):
    """« Localisable » est une exigence distincte de « cité ».

    Une citation exacte mais sans référence reste vérifiable contre le texte
    archivé, et invérifiable contre le journal officiel : c'est une réserve,
    pas une anomalie.
    """
    chemin = _ecrire(
        tmp_path,
        {"taux": 19.0, "verbatim_resume": "La taxe est perçue au taux normal de 19 pour cent."},
    )
    anomalies, reserves, _ = verifier_fiche.verifier(chemin)

    assert not [a for a in anomalies if "verbatim" in a], anomalies
    assert any("référence d'article" in r for r in reserves), reserves


def test_les_fiches_du_depot_passent_toutes():
    """Le contrat vaut sur les fiches réelles, pas sur des exemples choisis.

    Une anomalie ici signale soit une fiche à corriger, soit — comme deux fois
    déjà — un vérificateur qui se trompe sur une fiche authentique.
    """
    dossier = verifier_fiche.FICHES
    fichiers = sorted(
        os.path.join(dossier, nom) for nom in os.listdir(dossier) if nom.endswith(".json")
    )
    assert fichiers, "aucune fiche trouvée : le test perdrait son sens"

    en_anomalie = {
        os.path.basename(chemin): verifier_fiche.verifier(chemin)[0]
        for chemin in fichiers
        if verifier_fiche.verifier(chemin)[0]
    }

    assert not en_anomalie, f"fiches en anomalie : {en_anomalie}"
