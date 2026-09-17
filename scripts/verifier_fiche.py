#!/usr/bin/env python3
"""
Vérifier une fiche de collecte avant de l'intégrer au calculateur.

Une fiche établit une donnée fiscale sur source primaire (voir
``docs/COLLECTE_DONNEES_MANQUANTES.md``). Avant qu'elle n'entre dans le
calcul, ce script contrôle qu'elle tient ses promesses — pas que la donnée
est *vraie*, ce qu'aucun programme ne peut dire, mais qu'elle est
**vérifiable** : que la source est nommée, que le texte cité est bien celui
qui est archivé, et que rien d'essentiel ne manque.

Le contrôle d'empreinte est piloté par la donnée, pas par la forme du
fichier. Les fiches du dépôt ne se ressemblent pas : la règle vit tantôt dans
``regle``, tantôt dans ``determinations[]``, et le couple texte/empreinte
apparaît sous au moins six chemins de clés différents (``source.``,
``determinations[].``, ``instrument.``, ``pays.<ISO3>.<date>.``…). Une
première version reconnaissait les fiches à leur forme et laissait donc
passer, sans le moindre contrôle, huit fichiers sur douze — dont une fiche
kényane authentique. On parcourt désormais l'objet entier : partout où un
chemin de texte archivé côtoie une empreinte, le couple est vérifié.

Usage :
    python3 scripts/verifier_fiche.py <fiche.json> [...]
    python3 scripts/verifier_fiche.py --toutes

Sortie : un rapport par fichier, et un code de retour non nul si l'un échoue.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHES = os.path.join(REPO, "backend", "data", "legal_refs", "zlecaf_application")

#: Une fiche de taux porte un nombre ; une fiche d'assiette porte une formule
#: ou, quand la règle se lit en prose, sa portée. Les deux établissent une
#: donnée.
CLES_VALEUR = ("taux_standard_pct", "valeur", "assiette", "taux", "portee")
CLES_REFERENCE = ("article", "reference", "reference_legale", "instrument")
#: Une fiche qui établit plusieurs valeurs décline ses citations plutôt que de
#: les entasser sous une clé unique : `verbatim_taux_normal`,
#: `verbatim_exoneration_import`… Exiger le nom exact `verbatim` jugerait la
#: FORME de la fiche et non son contenu — c'est ainsi qu'une fiche algérienne
#: portant quatre citations sourcées a été refusée. Le préfixe est donc la règle.
PREFIXE_VERBATIM = "verbatim"
#: Les noms sous lesquels un texte archivé et son empreinte se présentent.
CLES_TEXTE = ("texte_archive", "texte_extrait", "fichier_archive")
CLES_EMPREINTE = ("sha256", "empreinte")


def _blocs(objet):
    """Tous les dictionnaires contenus dans la fiche, à n'importe quelle
    profondeur. C'est sur eux, et non sur une forme attendue, que portent les
    contrôles."""
    if isinstance(objet, dict):
        yield objet
        for valeur in objet.values():
            yield from _blocs(valeur)
    elif isinstance(objet, list):
        for valeur in objet:
            yield from _blocs(valeur)


def _premier(dico, cles):
    for cle in cles:
        if isinstance(dico, dict) and dico.get(cle) not in (None, "", [], {}):
            return cle, dico[cle]
    return None, None


def _porte_une_reference(texte):
    """La citation nomme-t-elle elle-même son article ?

    Ne cherche pas à extraire la référence, seulement à constater qu'elle est
    présente : le contrôle vaut « localisable », pas « bien formée »."""
    debut = texte.lstrip()[:200].lower()
    return any(
        marque in debut for marque in ("art.", "article", "règle ", "regle ", "section ", "§")
    )


def _verbatims(regle):
    """Les citations d'une règle, sous `verbatim` comme sous `verbatim_<quoi>`.

    Rendu trié pour que le rapport soit reproductible d'une exécution à
    l'autre."""
    if not isinstance(regle, dict):
        return []
    return [
        valeur
        for cle, valeur in sorted(regle.items())
        if isinstance(cle, str)
        and cle.startswith(PREFIXE_VERBATIM)
        and isinstance(valeur, str)
        and valeur.strip()
    ]


def _sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def _verifier_empreintes(fiche, dossier):
    """Contrôler chaque couple (texte archivé, empreinte) de la fiche.

    Rendu : (anomalies, réserves, nombre de textes réellement vérifiés)."""
    anomalies, reserves, verifies = [], [], 0
    for bloc in _blocs(fiche):
        _, chemin_relatif = _premier(bloc, CLES_TEXTE)
        if not chemin_relatif or not isinstance(chemin_relatif, str):
            continue
        chemin = os.path.join(dossier, chemin_relatif)
        nom = os.path.basename(chemin_relatif)
        if not os.path.exists(chemin):
            anomalies.append(f"texte archivé introuvable : {chemin_relatif}")
            continue
        _, declaree = _premier(bloc, CLES_EMPREINTE)
        if not declaree:
            reserves.append(f"{nom} : archivé sans empreinte, son contenu n'est pas contrôlable")
            continue
        reelle = _sha256(chemin)
        if reelle != declaree:
            anomalies.append(
                f"{nom} : empreinte différente "
                f"(déclarée {str(declaree)[:12]}, réelle {reelle[:12]})"
            )
        else:
            verifies += 1
    return anomalies, reserves, verifies


def _etablit_une_valeur(fiche):
    """La fiche porte-t-elle une règle ? Rendu : (blocs de règle, verbatim vu).

    Une règle vit dans `regle`, ou dans chaque entrée de `determinations[]` —
    les deux formes existent au dépôt et établissent également une donnée."""
    regles = []
    if isinstance(fiche.get("regle"), dict):
        regles.append(fiche["regle"])
    determinations = fiche.get("determinations")
    if isinstance(determinations, list):
        regles.extend(d for d in determinations if isinstance(d, dict))
    return regles


def verifier(chemin):
    """Rendre (anomalies, réserves, statut) pour un fichier.

    `statut` vaut 'fiche' quand le fichier établit une donnée et a été jugé
    comme tel, 'ignore' quand il n'en établit aucune, 'non_etabli' quand il
    conclut explicitement à l'absence de source."""
    try:
        with open(chemin, encoding="utf-8") as f:
            fiche = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"illisible : {exc}"], [], "fiche"
    if not isinstance(fiche, dict):
        return ["la fiche n'est pas un objet JSON"], [], "fiche"

    dossier = os.path.dirname(os.path.abspath(chemin))
    # L'empreinte se vérifie d'abord, et quelle que soit la nature du fichier :
    # un document de travail qui cite un texte archivé doit le citer
    # fidèlement, lui aussi.
    anomalies, reserves, verifies = _verifier_empreintes(fiche, dossier)

    if fiche.get("etabli") is False:
        if not fiche.get("doutes"):
            anomalies.append("fiche non établie sans explication : 'doutes' attendu")
        return anomalies, reserves + ["non établie — aucune donnée à intégrer"], "non_etabli"

    regles = _etablit_une_valeur(fiche)
    if not regles:
        # Relevé d'application ZLECAf, plan de collecte, tableau d'état : ces
        # documents citent parfois une source mais n'établissent pas de valeur.
        # Leurs empreintes ont tout de même été contrôlées ci-dessus.
        reserves.append(
            f"n'établit aucune valeur — {verifies} empreinte(s) vérifiée(s) tout de même"
        )
        return anomalies, reserves, "ignore"

    for i, regle in enumerate(regles):
        ou = "regle" if len(regles) == 1 and "regle" in fiche else f"détermination {i + 1}"
        if _premier(regle, CLES_VALEUR)[0] is None:
            anomalies.append(f"{ou} : aucune valeur retenue")
        citations = _verbatims(regle)
        if not citations:
            anomalies.append(
                f"{ou} : verbatim absent — une fiche cite le texte, elle ne le résume pas"
            )
        # La référence peut vivre dans une clé dédiée, ou être portée par la
        # citation elle-même — « Art. 21 - La taxe sur la valeur ajoutée… » est
        # localisable sans qu'un champ `article` le répète.
        if _premier(regle, CLES_REFERENCE)[0] is None and not any(
            _porte_une_reference(texte) for texte in citations
        ):
            reserves.append(f"{ou} : aucune référence d'article, la citation n'est pas localisable")

    if verifies == 0:
        reserves.append("aucun texte archivé vérifié : la citation n'est pas contrôlable")
    if not fiche.get("verified_at"):
        reserves.append("date de vérification absente")
    if not (fiche.get("ne_tranche_pas") or fiche.get("ce_que_cela_ne_tranche_pas")):
        reserves.append("la fiche ne dit pas ce qu'elle laisse ouvert")
    if fiche.get("conflits"):
        reserves.append(f"conflit de sources signalé : {fiche['conflits']}")

    return anomalies, reserves, "fiche"


def main(argv):
    options = [a for a in argv[1:] if a.startswith("-")]
    args = [a for a in argv[1:] if not a.startswith("-")]
    inconnues = [o for o in options if o not in ("--toutes", "-h", "--help")]
    if inconnues:
        print(f"option inconnue : {' '.join(inconnues)}", file=sys.stderr)
        return 2
    if "-h" in options or "--help" in options:
        print(__doc__.strip())
        return 0
    if "--toutes" in options:
        if args:
            print("--toutes ne se combine pas avec des chemins explicites", file=sys.stderr)
            return 2
        args = sorted(glob.glob(os.path.join(FICHES, "*.json")))
    if not args:
        print("aucun fichier à vérifier (préciser des chemins, ou --toutes)", file=sys.stderr)
        return 2

    en_echec = fiches = ignores = 0
    for chemin in args:
        anomalies, reserves, statut = verifier(chemin)
        marque = {"fiche": "✓", "ignore": "–", "non_etabli": "○"}[statut]
        if anomalies:
            en_echec += 1
            marque = "✗"
        if statut == "fiche":
            fiches += 1
        else:
            ignores += 1
        print(f"{marque} {os.path.basename(chemin)}")
        for a in anomalies:
            print(f"    ANOMALIE  {a}")
        for r in reserves:
            print(f"    réserve   {r}")

    print()
    print(
        f"{fiches} fiche(s) établissant une valeur, {ignores} autre(s) document(s), "
        f"{en_echec} en anomalie"
    )
    return 1 if en_echec else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
