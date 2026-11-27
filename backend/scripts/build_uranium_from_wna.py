#!/usr/bin/env python3
"""
Uranium africain — DÉRIVÉ du tableau de la WNA, plus saisi à la main
=====================================================================
Écrit ``backend/etl/uranium_wna.py`` à partir du tableau « Production from
mines (tonnes U) » de la page *World Uranium Mining Production* de la World
Nuclear Association :
https://world-nuclear.org/information-library/nuclear-fuel-cycle/mining-of-uranium/world-uranium-mining-production

Le tableau publie, par pays, la production des mines en tonnes d'uranium
(tU). Le script en retient les pays africains, années 2022 à 2024.

CE QUE CE SCRIPT REFUSE DE FAIRE
----------------------------------
- **Garder un pays absent du tableau.** Un pays que la WNA ne liste pas n'a
  pas de chiffre : il n'est pas émis.

Usage :
    python3 backend/scripts/build_uranium_from_wna.py            # écrit
    python3 backend/scripts/build_uranium_from_wna.py --dry-run  # affiche
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
OUT_FILE = BACKEND_DIR / "etl" / "uranium_wna.py"

PAGE_URL = (
    "https://world-nuclear.org/information-library/nuclear-fuel-cycle/"
    "mining-of-uranium/world-uranium-mining-production"
)
ANNEES = (2022, 2023, 2024)

#: Noms de pays africains tels que la WNA les écrit -> ISO3.
WNA_AFRICA = {
    "Namibia": "NAM", "Niger": "NER", "South Africa": "ZAF", "Malawi": "MWI",
    "Tanzania": "TZA", "Zambia": "ZMB", "Botswana": "BWA",
}


def _cellules(rangee: str) -> list:
    return [
        html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
        for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", rangee, re.S)
    ]


def lire_tableau(page: str) -> tuple:
    """Rend ({iso3: {année: tU}}, HTML du tableau) pour le tableau par pays."""
    for tableau in re.findall(r"<table.*?</table>", page, re.S):
        rangees = [_cellules(r) for r in re.findall(r"<tr.*?</tr>", tableau, re.S)]
        if not rangees or rangees[0][:1] != ["Country"]:
            continue
        colonnes = {int(c): k for k, c in enumerate(rangees[0]) if c.isdigit()}
        out = {}
        for cellules in rangees[1:]:
            iso3 = WNA_AFRICA.get(cellules[0] if cellules else "")
            if not iso3:
                continue
            for annee in ANNEES:
                k = colonnes.get(annee)
                brut = cellules[k].replace(",", "") if k is not None and k < len(cellules) else ""
                if re.fullmatch(r"\d+(?:\.\d+)?", brut) and float(brut) > 0:
                    out.setdefault(iso3, {})[annee] = float(brut)
        return out, tableau
    raise ValueError("tableau « Country / années » introuvable sur la page WNA")


def telecharger() -> str:
    requete = urllib.request.Request(PAGE_URL, headers={"User-Agent": "afcfta-production-etl/1.0"})
    with urllib.request.urlopen(requete, timeout=120) as resp:
        return resp.read().decode("utf-8")


def render(par_pays: dict, sha256: str) -> str:
    pays = ",\n".join(
        f"    {iso3!r}: {{" + ", ".join(f"{a}: {v!r}" for a, v in sorted(ans.items())) + "}"
        for iso3, ans in sorted(par_pays.items())
    )
    return f'''"""
Uranium africain dérivé de la WNA — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===================================================================
Produit par ``backend/scripts/build_uranium_from_wna.py`` depuis le tableau
de production par pays de la World Nuclear Association :
{PAGE_URL}

Production des mines, en tonnes d'uranium (tU), années {ANNEES[0]}-{ANNEES[-1]}.

Régénérer :
    python3 backend/scripts/build_uranium_from_wna.py
"""

from __future__ import annotations

from typing import Dict

WNA_DATASET = "World Nuclear Association — World Uranium Mining Production"
WNA_SOURCE_URL = {PAGE_URL!r}
WNA_MEASURE = "Production from mines, tonnes U"
#: Empreinte SHA-256 du tableau HTML dont ces chiffres sont issus.
WNA_SHA256 = {sha256!r}

#: iso3 -> {{année: tonnes d'uranium}}
WNA_URANIUM: Dict[str, Dict[int, float]] = {{
{pays},
}}
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    args = ap.parse_args()

    par_pays, tableau = lire_tableau(telecharger())
    sha256 = hashlib.sha256(tableau.encode("utf-8")).hexdigest()
    for iso3, ans in sorted(par_pays.items()):
        print(f"   {iso3}  {ans}")
    if args.dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return
    OUT_FILE.write_text(render(par_pays, sha256), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(BACKEND_DIR.parent)}")


if __name__ == "__main__":
    sys.exit(main())
