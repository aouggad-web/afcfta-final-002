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


# ── Troisième défaut du même genre : les règles NOMMÉES ───────────────────────
def test_une_regle_qui_nomme_ses_sous_regles_est_acceptee(tmp_path):
    """Une fiche qui établit plusieurs règles distinctes les nomme.

    Défaut constaté le 2026-09-18 : une fiche mauritanienne portant deux
    règles entièrement sourcées — déclaration en détail et prohibitions, avec
    leurs articles et leurs citations — a été refusée parce que le bloc qui
    les CONTIENT ne citait rien lui-même. L'outil jugeait de nouveau la forme.
    """
    chemin = _ecrire(
        tmp_path,
        {
            "declaration_en_detail": {
                "article": "Art. 111-114",
                "verbatim": "Toutes les marchandises importées doivent faire l'objet "
                "d'une déclaration en détail leur assignant un régime douanier.",
                "portee": "Générale — toutes positions.",
            },
            "prohibitions": {
                "article": "Art. 33-36",
                "verbatim": "Sont considérées comme prohibées toutes marchandises dont "
                "l'importation est interdite à quelque titre que ce soit.",
                "portee": "Huit motifs, levée sur titre régulier.",
            },
            "licences_economiques": "Aucune restriction quantitative.",
        },
    )
    anomalies, _, statut = verifier_fiche.verifier(chemin)
    assert anomalies == []
    assert statut == "fiche"


def test_une_sous_regle_sans_citation_ne_sauve_pas_les_autres(tmp_path):
    """Contrôle négatif : le conteneur ne dilue pas l'exigence.

    Une sous-règle qui ne cite rien n'est pas retenue comme règle — elle ne
    peut donc pas servir de caution à un bloc qui, lui, résume au lieu de citer.
    """
    chemin = _ecrire(
        tmp_path,
        {
            "premiere": {"article": "Art. 1", "portee": "résumé sans citation"},
            "seconde": {"article": "Art. 2", "portee": "résumé sans citation"},
        },
    )
    anomalies, _, _ = verifier_fiche.verifier(chemin)
    assert any("verbatim absent" in a for a in anomalies)


def test_une_regle_plate_reste_jugee_comme_avant(tmp_path):
    """Non-régression : la forme historique n'est pas dégradée par la nouvelle."""
    chemin = _ecrire(
        tmp_path,
        {
            "article": "Art. 21",
            "verbatim": "La taxe sur la valeur ajoutée est assise sur la valeur en douane.",
            "assiette": "CIF",
        },
    )
    anomalies, _, statut = verifier_fiche.verifier(chemin)
    assert anomalies == []
    assert statut == "fiche"


def test_un_conteneur_dont_aucune_sous_regle_ne_porte_de_valeur_est_signale(tmp_path):
    """Une sous-règle qui cite mais ne retient rien reste une anomalie."""
    chemin = _ecrire(
        tmp_path,
        {
            "une_regle": {
                "article": "Art. 7",
                "verbatim": "Le présent article est cité fidèlement mais n'est pas exploité.",
            }
        },
    )
    anomalies, _, _ = verifier_fiche.verifier(chemin)
    assert any("aucune valeur retenue" in a for a in anomalies)
