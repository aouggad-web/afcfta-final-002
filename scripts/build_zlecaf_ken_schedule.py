#!/usr/bin/env python3
"""Extrait le barème ZLECAf kényan du texte gazetté, et rien d'autre.

Source : EAC Provisional Schedule of Tariff Concessions for the AfCFTA,
Category A Products — Legal Notice EAC/321/2022, Journal officiel de l'EAC
du 6 septembre 2022, publié par la Kenya Revenue Authority.

Le barème publie, pour chaque position, un taux de base et DIX colonnes
annuelles, 2021 à 2030. **Ce script lit ces colonnes ; il n'en calcule
aucune.** Qu'elles vaillent exactement `base x (1 - n/10)` sur les 53 420
colonnes du document est un CONTRÔLE, pas une règle de production : le jour
où une colonne s'en écarterait, c'est la colonne publiée qui ferait foi.

Deux pièges du document, traités explicitement :

1. **Onze lignes d'aciers portent un taux composite** (« 25% or $200/MT
   whichever is higher ») que la grammaire du moteur ne sait pas liquider.
   Elles sont ÉCARTÉES et listées à part, jamais ramenées à leur volet ad
   valorem — ce serait servir un droit inférieur à celui qui est dû. L'une
   d'elles, 7228.40.00, est de surcroît incohérente dans le document même :
   base composite, mais colonnes annuelles de la série 35 %.

2. **Le pourcentage d'une DÉSIGNATION n'est pas un taux.** « containing 85%
   or more by weight… », « 99.99% pure » : une extraction qui prend le
   premier « % » du segment ramasse ces valeurs et fabrique des bases de
   0,25 %, 85 % ou 99,99 %. L'ancrage se fait donc sur la STRUCTURE du
   tableau — base, horizon, puis les dix annuités — et non sur le premier
   pourcentage rencontré.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "backend" / "data" / "zlecaf_ken"

URL = (
    "https://www.kra.go.ke/images/publications/"
    "EAC-PROVISIONAL-SCHEDULE-OF-TARIFF-CONCESSIONS-FOR-THE-AFRICAN-"
    "CONTINENTAL-FREE-TRADE-AREA-AfCFTA-CATEGORY-A-PRODUCTS.pdf"
)
#: Empreinte du PDF dont ce barème est tiré, relevée le 23/09/2026.
SHA256_ATTENDU = "7a92fb35c5bba0e637deecb6d7d5eb309ecbbdefa84fecae67a56aa75f0ecaeb"

PREMIERE_ANNEE = 2021
CODE = re.compile(r"\b(\d{4}\.\d{2}\.\d{2})\b")
DIX_ANNUITES = r"((?:\d+(?:\.\d+)?\s*%\s*){10})"
AVEC_HORIZON = re.compile(r"(\d+(?:\.\d+)?)\s*%\s+(\d+)\s+" + DIX_ANNUITES)
SANS_HORIZON = re.compile(r"(\d+(?:\.\d+)?)\s*%\s+" + DIX_ANNUITES)
#: Marqueurs d'un taux composite : la ligne est écartée dès qu'ils paraissent.
COMPOSITE = ("whichever", "/MT", "USD")


def texte_du_pdf(chemin):
    import pypdf

    lecteur = pypdf.PdfReader(str(chemin))
    return "\n".join((page.extract_text() or "") for page in lecteur.pages)


def extraire(flux):
    bornes = [(m.start(), m.group(1)) for m in CODE.finditer(flux)]
    lignes, composites, sans_horizon, illisibles = {}, [], [], []
    for i, (debut, code) in enumerate(bornes):
        fin = bornes[i + 1][0] if i + 1 < len(bornes) else len(flux)
        segment = flux[debut:fin]
        if any(marqueur in segment for marqueur in COMPOSITE):
            if code not in composites:
                composites.append(code)
            continue
        if code in lignes:
            continue
        trouve = AVEC_HORIZON.search(segment)
        horizon = int(trouve.group(2)) if trouve else None
        if not trouve:
            trouve = SANS_HORIZON.search(segment)
            if not trouve:
                illisibles.append(code)
                continue
            sans_horizon.append(code)
        bloc = trouve.group(3) if horizon is not None else trouve.group(2)
        annuites = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", bloc)]
        lignes[code] = {
            "base_pct": float(trouve.group(1)),
            "horizon_ans": horizon,
            "annuites_pct": annuites,
            "designation": segment[len(code) : trouve.start()].strip(),
        }
    return lignes, composites, sans_horizon, illisibles


def controler(lignes):
    """Le contrôle qui compte : chaque annuité est-elle bien base x (1 - n/10) ?

    Un écart n'est pas une erreur d'extraction à corriger en silence : ce
    serait une ligne que le barème traite autrement, et il faudrait la lire.
    """
    ecarts = []
    for code, ligne in lignes.items():
        if len(ligne["annuites_pct"]) != 10:
            ecarts.append((code, "nombre de colonnes"))
            continue
        for n, valeur in enumerate(ligne["annuites_pct"], start=1):
            if abs(valeur - ligne["base_pct"] * (1 - n / 10.0)) > 0.051:
                ecarts.append((code, f"annuite {n}", valeur, ligne["base_pct"]))
                break
    return ecarts


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("pdf", help="chemin du PDF gazetté (ou de son extraction texte .txt)")
    options = a.parse_args(argv)
    chemin = Path(options.pdf)

    if chemin.suffix.lower() == ".txt":
        flux = chemin.read_text(encoding="utf-8")
        empreinte = None
    else:
        empreinte = hashlib.sha256(chemin.read_bytes()).hexdigest()
        if empreinte != SHA256_ATTENDU:
            print(
                f"ATTENTION : empreinte {empreinte[:16]}… au lieu de "
                f"{SHA256_ATTENDU[:16]}… — document différent de celui vérifié",
                file=sys.stderr,
            )
        flux = texte_du_pdf(chemin)
    flux = re.sub(r"\s+", " ", flux)

    lignes, composites, sans_horizon, illisibles = extraire(flux)
    ecarts = controler(lignes)

    print(f"  positions exploitables      : {len(lignes)}")
    print(f"  taux composites écartés     : {len(composites)} {composites}")
    print(f"  horizon absent du document  : {sans_horizon}")
    print(f"  segments illisibles         : {illisibles}")
    print(f"  colonnes contrôlées         : {sum(len(v['annuites_pct']) for v in lignes.values())}")
    print(f"  écarts à base x (1 - n/10)  : {len(ecarts)} {ecarts[:3]}")
    print(
        f"  bases rencontrées           : {dict(sorted(Counter(v['base_pct'] for v in lignes.values()).items()))}"
    )

    SORTIE.mkdir(parents=True, exist_ok=True)
    document = {
        "_objet": (
            "Barème ZLECAf applicable à l'importation au Kenya, catégorie A. "
            "Taux LUS dans les colonnes publiées, jamais calculés."
        ),
        "_instrument": (
            "EAC Provisional Schedule of Tariff Concessions for the AfCFTA: "
            "Category A Products — Legal Notice EAC/321/2022, Journal officiel "
            "de l'EAC du 06/09/2022"
        ),
        "_url": URL,
        "_document_sha256": empreinte or SHA256_ATTENDU,
        "_premiere_annee": PREMIERE_ANNEE,
        "_derniere_annee": PREMIERE_ANNEE + 9,
        "_perimetre": (
            "Droit de douane (CET Import Duty) SEULEMENT. L'IDF et le RDL sont "
            "des prélèvements de la loi kényanne (Miscellaneous Fees and Levies "
            "Act 2016), dont les listes d'exonération ne visent que l'origine "
            "EAC ; aucune détermination publiée ne les rattache à la concession "
            "ZLECAf. Ils restent dus au taux plein."
        ),
        "_lignes_ecartees": {
            "taux_composite": composites,
            "motif": (
                "Taux « X% or $Y/MT whichever is higher » : la grammaire du "
                "moteur ne liquide pas un composite. Les ramener à leur volet "
                "ad valorem servirait un droit inférieur à celui qui est dû. "
                "7228.40.00 est de plus incohérente dans le document : base "
                "composite, annuités de la série 35 %."
            ),
        },
        "_horizon_absent": {
            "codes": sans_horizon,
            "note": (
                "Le document omet la cellule « Time Frame » ; les dix annuités "
                "sont publiées et lues telles quelles. Rien n'est déduit."
            ),
        },
        "positions": {
            c: {k: v for k, v in d.items() if k != "designation"} for c, d in sorted(lignes.items())
        },
    }
    cible = SORTIE / "bareme_categorie_a.json"
    cible.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  écrit : {cible} ({cible.stat().st_size / 1024:.0f} Ko)")
    return 1 if (ecarts or illisibles) else 0


if __name__ == "__main__":
    raise SystemExit(main())
