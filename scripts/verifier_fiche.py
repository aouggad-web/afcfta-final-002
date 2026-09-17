#!/usr/bin/env python3
"""
Vérifier une fiche de collecte avant de l'intégrer au calculateur.

Une fiche établit une donnée fiscale sur source primaire (voir
``docs/COLLECTE_DONNEES_MANQUANTES.md``). Avant qu'elle n'entre dans le
calcul, ce script contrôle qu'elle tient ses promesses — pas que la donnée
est *vraie*, ce qu'aucun programme ne peut dire, mais qu'elle est
**vérifiable** : que la source est nommée et atteignable, que le texte cité
est bien celui qui est archivé, et que rien d'essentiel ne manque.

Usage :
    python3 scripts/verifier_fiche.py backend/data/legal_refs/zlecaf_application/*.json
    python3 scripts/verifier_fiche.py --toutes

Sortie : un rapport par fiche, et un code de retour non nul si l'une échoue.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHES = os.path.join(REPO, "backend", "data", "legal_refs", "zlecaf_application")

#: Les fiches du dépôt ne partagent pas toutes le même vocabulaire — elles se
#: sont ajoutées au fil des collectes. On accepte les synonymes plutôt que
#: d'imposer une réécriture des fiches déjà validées.
#: Une fiche de taux porte un nombre ; une fiche d'assiette porte une formule
#: ou, quand la règle se lit en prose (« la valeur en douane majorée de tous
#: les droits perçus à l'entrée »), sa portée. Les deux établissent une donnée.
CLES_VALEUR = ("taux_standard_pct", "valeur", "assiette", "taux", "portee")
CLES_REFERENCE = ("article", "reference", "reference_legale")


def _premier(dico, cles):
    for cle in cles:
        if isinstance(dico, dict) and dico.get(cle) not in (None, "", [], {}):
            return cle, dico[cle]
    return None, None


def verifier(chemin):
    """Rendre (anomalies, avertissements) pour une fiche."""
    anomalies, avertissements = [], []
    nom = os.path.basename(chemin)

    try:
        with open(chemin, encoding="utf-8") as f:
            fiche = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"illisible : {exc}"], []
    if not isinstance(fiche, dict):
        return ["la fiche n'est pas un objet JSON"], []

    # Le dossier contient aussi des documents de travail — plans de collecte,
    # tableaux d'état — qui n'établissent aucune donnée et n'ont donc pas à
    # porter de source ni de verbatim. Les juger comme des fiches produirait
    # un rapport d'anomalies qui n'apprend rien.
    # Une fiche de source établit une VALEUR : elle porte donc un bloc `regle`
    # (ou se déclare non établie). Un relevé d'application ZLECAf, un plan de
    # collecte ou un tableau d'état peuvent citer une source sans rien établir
    # de tel — ce sont d'autres documents, jugés selon d'autres critères.
    if "regle" not in fiche and fiche.get("etabli") is None:
        return [], ["ignoré : n'établit aucune valeur, ce n'est pas une fiche de source"]

    # Une fiche peut conclure « NON ÉTABLI » : c'est une réponse valable, et
    # elle n'a alors pas à porter de valeur. Elle doit dire ce qui a été
    # cherché, sinon elle n'est qu'un silence.
    if fiche.get("etabli") is False:
        if not fiche.get("doutes"):
            anomalies.append("fiche non établie sans explication : 'doutes' attendu")
        return anomalies, ["non établie — aucune donnée à intégrer"]

    source = fiche.get("source")
    if not isinstance(source, dict):
        anomalies.append("bloc 'source' absent")
        source = {}
    if not source.get("url"):
        anomalies.append("source sans URL : la donnée n'est pas retrouvable")
    if not (source.get("institution") or source.get("document")):
        anomalies.append("source sans institution ni document nommé")

    # Le texte archivé est le cœur de la vérifiabilité : sans lui, la fiche
    # affirme sans montrer. Son empreinte doit correspondre, sinon le texte
    # a changé depuis la lecture — ou n'est pas celui qui a été lu.
    archive = source.get("texte_archive")
    if archive:
        chemin_archive = os.path.join(os.path.dirname(chemin), archive)
        if not os.path.exists(chemin_archive):
            anomalies.append(f"texte archivé introuvable : {archive}")
        elif source.get("sha256"):
            reelle = hashlib.sha256(open(chemin_archive, "rb").read()).hexdigest()
            if reelle != source["sha256"]:
                anomalies.append(
                    f"empreinte du texte archivé différente "
                    f"(déclarée {source['sha256'][:12]}, réelle {reelle[:12]})"
                )
        else:
            avertissements.append("texte archivé sans empreinte sha256")
    else:
        avertissements.append("aucun texte archivé : la citation n'est pas contrôlable")

    regle = fiche.get("regle")
    if not isinstance(regle, dict):
        anomalies.append("bloc 'regle' absent")
        regle = {}
    cle_valeur, valeur = _premier(regle, CLES_VALEUR)
    if cle_valeur is None:
        anomalies.append(f"aucune valeur retenue (attendu l'une de {', '.join(CLES_VALEUR)})")
    if not regle.get("verbatim"):
        anomalies.append("verbatim absent : une fiche cite le texte, elle ne le résume pas")
    cle_ref, _ = _premier(regle, CLES_REFERENCE)
    if cle_ref is None and not source.get("reference"):
        avertissements.append("aucune référence d'article : la citation n'est pas localisable")

    if not fiche.get("verified_at"):
        avertissements.append("date de vérification absente")
    if not (fiche.get("ne_tranche_pas") or fiche.get("ce_que_cela_ne_tranche_pas")):
        avertissements.append("la fiche ne dit pas ce qu'elle laisse ouvert")
    if fiche.get("conflits"):
        avertissements.append(f"conflit de sources signalé : {fiche['conflits']}")

    return anomalies, avertissements


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("-")]
    if "--toutes" in argv[1:] or not args:
        args = sorted(glob.glob(os.path.join(FICHES, "*.json")))
    if not args:
        print("aucune fiche à vérifier")
        return 0

    en_echec = 0
    for chemin in args:
        anomalies, avertissements = verifier(chemin)
        nom = os.path.basename(chemin)
        if anomalies:
            en_echec += 1
            print(f"✗ {nom}")
            for a in anomalies:
                print(f"    ANOMALIE  {a}")
        else:
            print(f"✓ {nom}")
        for a in avertissements:
            print(f"    réserve   {a}")

    print()
    print(f"{len(args)} fiche(s) vérifiée(s), {en_echec} en anomalie")
    return 1 if en_echec else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
