#!/usr/bin/env python3
"""
Extraction des comptes économiques de l'ONS 2021-2024 (Algérie), par branche
============================================================================
Source : ONS, « Les comptes économiques de 2021 à 2024 », n° 1067 (août 2025).
Entrée : data/sources/DZA/ons/comptes_economiques_2021_2024.txt (texte du PDF).
Sortie : data/sources/DZA/ons/comptes_economiques_2021_2024.json.

Les nombres du PDF sont groupés par espaces (« 1 418 362 »), ce qui rend le
découpage ambigu. On le lève par les identités comptables :
  compte de production : PB - CI = VA et VA - RS - AINSP = EBE ;
  partage volume-prix  : VA(n, prix n-1) = VA(n-1) x (1 + volume) et
                         VA(n) = VA(n, prix n-1) x (1 + prix).
Une ligne qui ne vérifie pas son identité est signalée, jamais devinée. Contrôles
finaux : public + privé = total, VA du partage volume-prix = VA du compte, et
somme des branches hors hydrocarbures = total « Industrie » publié.

Usage:
    python3 scripts/extract_ons_comptes_dza.py            # écrit le JSON
    python3 scripts/extract_ons_comptes_dza.py --dry-run  # contrôles seulement
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "data", "sources", "DZA", "ons")
TEXTE = os.path.join(DOSSIER, "comptes_economiques_2021_2024.txt")
SORTIE = os.path.join(DOSSIER, "comptes_economiques_2021_2024.json")

BRANCHES = [
    "Autres industries extractives",
    "Industries alimentaires et du tabac",
    "Industrie textile, de l'habillement et des fourrures",
    "Industrie du cuir et de la chaussure",
    "Fabrication d'articles en bois et en papier, imprimerie et reproduction",
    "Raffinage et cokéfaction",
    "Industrie chimique, du caoutchouc et des plastiques",
    "Fabrication d'autres produits minéraux non métalliques",
    "Métallurgie, travail des métaux",
    "Fabrication de machines et équipements",
    "Fabrication de machines de bureau et matériel informatique",
    "Fabrication de machines et appareils électriques",
    "Fabrication d'équipements de communication et d'instruments médicaux",
    "Autres industries manufacturières",
    "Production et distribution d'électricité, de gaz",
    "Extraction d'hydrocarbures et services annexes",
]
HORS_INDUSTRIE = {
    "Extraction d'hydrocarbures et services annexes",
    "Raffinage et cokéfaction",
    "Production et distribution d'électricité, de gaz",
}
# Total « Industrie » (hors hydrocarbures) publié, tableau du partage volume-prix par grands secteurs
INDUSTRIE_PUBLIEE = {2021: 1084574, 2022: 1333188, 2023: 1467653, 2024: 1674431}
SECTEURS = ["SNF publiques", "Entreprises privées", "Administration publique", "TOTAL"]

META = {
    "publication": "ONS, Les comptes économiques de 2021 à 2024, n° 1067",
    "date_publication": "2025-08",
    "editeur": "Office national des statistiques (Algérie), Direction technique chargée de la comptabilité nationale",
    "systeme": "SCN 2008",
    "statut": {
        "2021": "définitif",
        "2022": "définitif",
        "2023": "semi-définitif",
        "2024": "provisoire",
    },
    "unite": "millions de DA courants",
    "champs": {
        "PB": "production brute (prix de base)",
        "CI": "consommation intermédiaire",
        "VA": "valeur ajoutée brute",
        "RS": "rémunération des salariés",
        "AINSP": "autres impôts nets de subventions sur la production",
        "EBE": "excédent brut d'exploitation / revenu mixte",
        "va_prix_prec": "VA de l'année aux prix de l'année précédente",
        "volume_pct": "croissance en volume (%)",
        "prix_pct": "variation du prix de la VA (%)",
        "va_courante": "VA aux prix courants",
    },
    "extraction": (
        "Texte du PDF (comptes_economiques_2021_2024.txt) découpé par "
        "backend/scripts/extract_ons_comptes_dza.py ; chaque ligne vérifie PB - CI = VA et "
        "VA - RS - AINSP = EBE, les chaînes volume-prix, public + privé = total, et la somme "
        "des branches hors hydrocarbures = total « Industrie » publié (2021-2024)."
    ),
}


def norm(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u00a0", " ")


def decoupages(jetons, n):
    """Tous les découpages de `jetons` en n nombres groupés par milliers."""
    if n == 0:
        if not jetons:
            yield []
        return
    if not jetons:
        return
    premier = jetons[0]
    chiffres = premier.lstrip("-")
    if len(chiffres) > 3:  # « 1090 » : nombre écrit sans espace, complet
        for reste in decoupages(jetons[1:], n - 1):
            yield [int(premier)] + reste
        return
    negatif = premier.startswith("-")
    val, i = int(chiffres), 1
    while True:
        for reste in decoupages(jetons[i:], n - 1):
            yield [-val if negatif else val] + reste
        if i < len(jetons) and len(jetons[i]) == 3 and not jetons[i].startswith("-"):
            val = val * 1000 + int(jetons[i])
            i += 1
        else:
            return


def compte(texte):
    sols = []
    for s in decoupages(re.findall(r"-?\d+", texte), 6):
        pb, ci, va, rs, ainsp, ebe = s
        if abs(pb - ci - va) <= 2 and abs(va - rs - ainsp - ebe) <= 2:
            sols.append(s)
    return sols


def extraire(lignes):
    alertes = []
    tetes = [
        (i, int(m.group(1)))
        for i, l in enumerate(lignes)
        for m in [re.search(r"Compte de production et compte d'exploitation.*-(\d{4})-", l)]
        if m
    ]
    fin_comptes = next(
        j
        for j, l in enumerate(lignes)
        if "Produit Intérieur Brut et valeurs ajoutées sectorielles" in l
    )
    sections = defaultdict(list)
    for k, (i, an) in enumerate(tetes):
        fin = tetes[k + 1][0] if k + 1 < len(tetes) else fin_comptes
        sections[an].append(norm(" ".join(lignes[i:fin])))

    comptes = []
    for an, parties in sorted(sections.items()):
        corps = " ".join(parties)
        pos = sorted((corps.find(norm(b)), b) for b in BRANCHES if corps.find(norm(b)) >= 0)
        for k, (j, b) in enumerate(pos):
            fin = pos[k + 1][0] if k + 1 < len(pos) else len(corps)
            seg = corps[j + len(norm(b)) : fin]
            for arret in ("Construction", "Commerce", "Ensemble", "Compte de production"):
                q = seg.find(arret)
                if q >= 0:
                    seg = seg[:q]
            marques = sorted(
                (m.start(), lib) for lib in SECTEURS for m in re.finditer(re.escape(lib), seg)
            )
            for q, (p, lib) in enumerate(marques):
                f = marques[q + 1][0] if q + 1 < len(marques) else len(seg)
                nombres = seg[p + len(lib) : f]
                sols = compte(nombres)
                if not sols:  # numéro de page collé en fin de section
                    sols = compte(" ".join(re.findall(r"-?\d+", nombres)[:-1]))
                if len(sols) == 1:
                    pb, ci, va, rs, ainsp, ebe = sols[0]
                    comptes.append(
                        dict(
                            annee=an,
                            branche=b,
                            secteur=lib,
                            PB=pb,
                            CI=ci,
                            VA=va,
                            RS=rs,
                            AINSP=ainsp,
                            EBE=ebe,
                        )
                    )
                else:
                    alertes.append(("compte", an, b, lib, len(sols)))

    def section(titre):
        i = next(k for k, l in enumerate(lignes) if titre in l)
        j = next(k for k in range(i + 1, len(lignes)) if lignes[k].startswith("Partage volume"))
        return norm(" ".join(lignes[i:j]))

    def un(jetons):
        s = list(decoupages(jetons, 1))
        return s[0][0] if len(s) == 1 else None

    volume = []
    for titre, (a1, a2) in (
        ("optique production 2021-2022", (2021, 2022)),
        ("optique production 2023-2024", (2023, 2024)),
    ):
        corps = section(titre)
        pos = sorted((corps.find(norm(b)), b) for b in BRANCHES if corps.find(norm(b)) >= 0)
        for k, (j, b) in enumerate(pos):
            fin = pos[k + 1][0] if k + 1 < len(pos) else len(corps)
            seg = re.split(r"[A-Za-zÉé]", corps[j + len(norm(b)) : fin])[0]
            jetons = re.findall(r"-?\d+,\d+|-?\d+", seg)
            dec = [i for i, t in enumerate(jetons) if "," in t]
            if len(dec) != 4:
                alertes.append(("volume", a1, b, len(dec)))
                continue
            d = [float(jetons[i].replace(",", ".")) for i in dec]
            v1, v4 = un(jetons[: dec[0]]), un(jetons[dec[3] + 1 :])
            retenu = None
            for va1, vp2 in decoupages(jetons[dec[1] + 1 : dec[2]], 2):
                if (
                    v1
                    and abs(v1 * (1 + d[1] / 100) / va1 - 1) < 0.003
                    and abs(va1 * (1 + d[2] / 100) / vp2 - 1) < 0.003
                    and v4
                    and abs(vp2 * (1 + d[3] / 100) / v4 - 1) < 0.003
                ):
                    retenu = (va1, vp2)
            if retenu is None:
                alertes.append(("volume identité", a1, b))
                continue
            volume.append(
                dict(
                    branche=b,
                    annee=a1,
                    va_prix_prec=v1,
                    volume_pct=d[0],
                    prix_pct=d[1],
                    va_courante=retenu[0],
                )
            )
            volume.append(
                dict(
                    branche=b,
                    annee=a2,
                    va_prix_prec=retenu[1],
                    volume_pct=d[2],
                    prix_pct=d[3],
                    va_courante=v4,
                )
            )
    return comptes, volume, alertes


def controler(comptes, volume):
    alertes = []
    par = defaultdict(dict)
    for r in comptes:
        par[(r["annee"], r["branche"])][r["secteur"]] = r
    for cle, s in par.items():
        for champ in ("PB", "CI", "VA", "RS", "AINSP", "EBE"):
            somme = sum(s[x][champ] for x in s if x != "TOTAL")
            if abs(somme - s["TOTAL"][champ]) > 3:
                alertes.append(("public+privé≠total", cle, champ))
    for r in volume:
        if abs(r["va_courante"] - par[(r["annee"], r["branche"])]["TOTAL"]["VA"]) > 1:
            alertes.append(("VA volume≠compte", r["annee"], r["branche"]))
    for an, publie in INDUSTRIE_PUBLIEE.items():
        somme = sum(
            s["TOTAL"]["VA"] for (a, b), s in par.items() if a == an and b not in HORS_INDUSTRIE
        )
        if somme != publie:
            alertes.append(("Industrie", an, somme, publie))
    if len(par) != 64 or len(volume) != 64:
        alertes.append(("couverture", len(par), len(volume)))
    return alertes


def main():
    lignes = open(TEXTE, encoding="utf-8").read().split("\n")
    comptes, volume, alertes = extraire(lignes)
    alertes += controler(comptes, volume)
    print(
        f"{len(comptes)} lignes de comptes, {len(volume)} lignes volume-prix, {len(alertes)} alerte(s)"
    )
    for a in alertes:
        print("  ", a)
    if alertes:
        sys.exit(1)
    if "--dry-run" not in sys.argv:
        with open(SORTIE, "w", encoding="utf-8") as f:
            json.dump(
                {"meta": META, "comptes": comptes, "volume": volume},
                f,
                ensure_ascii=False,
                indent=1,
            )
        print("écrit :", os.path.relpath(SORTIE, RACINE))


if __name__ == "__main__":
    main()
