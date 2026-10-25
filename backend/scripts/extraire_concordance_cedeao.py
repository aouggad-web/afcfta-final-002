#!/usr/bin/env python3
"""Concordance TEC CEDEAO 2022 → offre e-Tariff CEDEAO (TEC 2017).

L'offre CEDEAO de l'e-Tariff est rédigée sur le TEC 2017 ; un tarif national
passé au TEC 2022 (Nigeria) a des positions sans ligne d'offre. Deux voies,
dans cet ordre :

1. **Table du Mali** (« tableau de concordance des NTS supprimées », TEC 2017
   → TEC 2022, à 10 chiffres) : la position 2022 reçoit l'offre de ses
   positions 2017 sources — seulement si chaque source est confirmée par la
   table I de l'OMD (document sans autorité émettrice identifiée).
2. **Table I de l'OMD**, au SH6, pour un SH6 absent de l'offre : sources =
   SH6 2017 énumérés (ou le SH6 lui-même).

Dans les deux cas, l'offre n'est retenue que si TOUTES les lignes sources
portent exactement la même offre (catégorie, taux de base, calendrier) ; on
garde alors l'une d'elles comme ligne représentative. Sinon : rien.

    python3 backend/scripts/extraire_concordance_cedeao.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extraire_concordance_tun import TABLE_I, lire_table_i  # noqa: E402

TABLE_MALI = (
    RACINE / "data" / "legal_refs" / "zlecaf_application" / "sources" / "MLI_concordance_TEC2017_TEC2022_NTS_supprimees.pdf"
)
ETARIFF = RACINE / "data" / "official_preferential" / "ECOWAS_afcfta_etariff_2026-10-03.json.gz"
SORTIE = RACINE / "data" / "zlecaf_cedeao" / "concordance_tec2022_tec2017.json"

def lire_table_mali() -> dict:
    """TEC 2022 -> TEC 2017 sources, lues cellule par cellule.

    Les codes 2022 sont centrés verticalement dans leur cellule : une lecture
    par bandes de hauteur les attribuait à la ligne voisine (98 paires
    contredisaient la table de l'OMD). Les cellules du tableau font foi :
    colonnes 0 à 2 pour le TEC 2017, 6 à 8 pour le TEC 2022. Une ligne sans
    code 2017 en haut de page poursuit la dernière ligne de la page précédente.
    """
    lignes: list = []
    for page in pymupdf.open(TABLE_MALI):
        for table in page.find_tables().tables:
            for cellules in table.extract():
                textes = [c or "" for c in cellules]
                tec2017 = [code for c in textes[0:3] for code in re.findall(r"\b\d{10}\b", c)]
                tec2022 = [code for c in textes[6:9] for code in re.findall(r"\b\d{10}\b", c)]
                if tec2017:
                    lignes.append((tec2017[0], tec2022))
                elif tec2022 and lignes:
                    lignes[-1][1].extend(tec2022)
    inverse = defaultdict(set)
    for tec2017, cibles in lignes:
        for tec2022 in cibles:
            inverse[tec2022].add(tec2017)
    return inverse


def _offre(ligne: dict) -> str:
    return json.dumps(
        {k: ligne[k] for k in ("category", "mfn_rate_expression", "annual_rate_expressions")}, sort_keys=True
    )


def _representative(codes, offre) -> str | None:
    lignes = [offre.get(c) for c in codes]
    if not lignes or any(ligne is None for ligne in lignes):
        return None
    return sorted(codes)[0] if len({_offre(ligne) for ligne in lignes}) == 1 else None


def main() -> None:
    with gzip.open(ETARIFF, "rt", encoding="utf-8") as f:
        etariff = json.load(f)
    offre = {ligne["hs_code"]: ligne for ligne in etariff["schedules"]["1"]}
    par_sh6 = defaultdict(list)
    for code in offre:
        par_sh6[code[:6]].append(code)

    table_i = lire_table_i()
    mali, ecartees = {}, defaultdict(int)
    for tec2022, sources in sorted(lire_table_mali().items()):
        if tec2022 in offre:
            continue
        # La table du Mali n'est retenue que confirmée par la table I de l'OMD :
        # chaque source 2017 doit relever d'un SH6 que l'OMD donne pour origine.
        attendus = set(table_i.get(tec2022[:6], [tec2022[:6]]))
        if any(source[:6] not in attendus for source in sources):
            ecartees["Mali : contredit par la table I de l'OMD"] += 1
            continue
        rep = _representative(sources, offre)
        if rep:
            mali[tec2022] = {"ligne_e_tariff": rep, "sources_tec2017": sorted(sources)}
        else:
            ecartees["Mali : offres divergentes ou source absente"] += 1

    omd = {}
    for sh6, sources in sorted(table_i.items()):
        if sh6 in par_sh6:
            continue
        codes = [c for s in (sources or []) for c in par_sh6.get(s, [])]
        rep = _representative(codes, offre) if codes else None
        if rep:
            omd[sh6] = {"ligne_e_tariff": rep, "sources_sh2017": sorted(set(sources))}
        else:
            ecartees["OMD : offres divergentes ou aucune ligne source"] += 1

    resultat = {
        "_objet": (
            "Rattachement des positions TEC CEDEAO 2022 sans ligne dans l'offre e-Tariff "
            "CEDEAO (TEC 2017) : par la table du Mali (10 chiffres), puis par la table I "
            "de l'OMD (SH6), seulement quand toutes les lignes sources portent la même offre."
        ),
        "_table_mali_sha256": hashlib.sha256(TABLE_MALI.read_bytes()).hexdigest(),
        "_table_i_omd_sha256": hashlib.sha256(TABLE_I.read_bytes()).hexdigest(),
        "_etariff_sha256": hashlib.sha256(ETARIFF.read_bytes()).hexdigest(),
        "_ecartees": dict(ecartees),
        "par_position_mali": mali,
        "par_sh6_omd": omd,
    }
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps(resultat, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Mali {len(mali)} positions, OMD {len(omd)} SH6, écartées {dict(ecartees)} -> {SORTIE}")


if __name__ == "__main__":
    main()
