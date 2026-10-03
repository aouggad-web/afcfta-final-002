#!/usr/bin/env python3
"""Droit de base 2019 des positions tunisiennes SH 2022 absentes de l'e-Tariff.

L'e-Tariff tunisien est en SH 2017 ; le Tarif Web 2026 en SH 2022. Une ligne
nationale dont les 9 premiers chiffres ne figurent pas dans l'e-Tariff n'a pas
de droit de base. On le retrouve par la table I de l'OMD (« Correlating the
2022 version to the 2017 version », novembre 2020), au niveau SH6 :

* si le SH6 de la ligne figure à la table I, ses sources sont les SH6 2017
  qu'elle énumère (« ex » compris) ; une entrée sans source énumérée
  (« Applicable subheadings ») ne se résout pas ;
* sinon le SH6 n'a pas changé de portée : sa source est lui-même.

Le droit de base n'est retenu que si TOUTES les lignes e-Tariff des SH6
sources portent le même taux : la ligne nationale en relevait en 2019, son
taux ne peut être que celui-là. Plusieurs taux, ou aucune ligne source : rien.

    python3 backend/scripts/extraire_concordance_tun.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import pymupdf

RACINE = Path(__file__).resolve().parents[1]
TABLE_I = RACINE / "data" / "legal_refs" / "zlecaf_application" / "sources" / "OMD_correlation_SH2022_SH2017_table_I.pdf"
ETARIFF = RACINE / "data" / "official_preferential" / "TUN_afcfta_etariff_2026-10-03.json.gz"
COEFFICIENTS = RACINE / "data" / "zlecaf_tun" / "coefficients_tarifweb_2026.json"
SORTIE = RACINE / "data" / "zlecaf_tun" / "concordance_sh2022_sh2017.json"

_CODE = re.compile(r"^\d{4}\.\d{2}$")
_SOURCE = re.compile(r"^(?:ex)?(\d{4}\.\d{2})[,;]?$")


def lire_table_i() -> dict:
    """SH6 2022 -> SH6 2017 sources. Colonnes : 2022 (x < 150), 2017 (150-230)."""
    table: dict[str, list] = {}
    derniere = None  # entrée 2022 en cours : elle peut se poursuivre page suivante
    for page in pymupdf.open(TABLE_I):
        mots = [m for m in page.get_text("words") if m[1] < 715]  # pied de page ôté
        gauche = sorted((m for m in mots if m[0] < 150 and _CODE.match(m[4])), key=lambda m: m[1])
        milieu = sorted((m for m in mots if 150 <= m[0] < 230), key=lambda m: (m[1], m[0]))
        # Sources en haut de page, avant la première entrée 2022 : suite de la
        # dernière entrée de la page précédente (ex. 8462.61, 8806.10).
        premiere = gauche[0][1] - 2 if gauche else 715
        if derniere is not None:
            for m in milieu:
                trouve = _SOURCE.match(m[4]) if m[1] < premiere else None
                if trouve:
                    table[derniere].append(trouve.group(1).replace(".", ""))
        for i, mot in enumerate(gauche):
            haut = mot[1] - 2
            bas = gauche[i + 1][1] - 2 if i + 1 < len(gauche) else 715
            sources = table.setdefault(mot[4].replace(".", ""), [])
            for m in milieu:
                trouve = _SOURCE.match(m[4]) if haut <= m[1] < bas else None
                if trouve:
                    sources.append(trouve.group(1).replace(".", ""))
            derniere = mot[4].replace(".", "")
    return table


def main() -> None:
    table = lire_table_i()
    with gzip.open(ETARIFF, "rt", encoding="utf-8") as f:
        etariff = json.load(f)
    base = {ligne["hs_code"]: float(ligne["mfn_rate_expression"]) for ligne in etariff["schedules"]["1"]}
    par_sh6 = defaultdict(set)
    for code, taux in base.items():
        par_sh6[code[:6]].add(taux)
    positions = json.loads(COEFFICIENTS.read_text(encoding="utf-8"))["positions"]

    resolues, non_resolues, ecartees = {}, {}, defaultdict(int)
    for code in sorted(positions):
        if code[:9] in base:
            continue
        sources = table.get(code[:6], [code[:6]])
        taux = set().union(*(par_sh6.get(s, set()) for s in sources)) if sources else set()
        if len(taux) == 1:
            resolues[code] = {"base": taux.pop(), "sources_sh2017": sorted(set(sources))}
        else:
            if not sources:
                motif = "sources non énumérées par l'OMD"
            elif not taux:
                motif = "SH6 inconnu de l'e-Tariff et de la table I de l'OMD"
            else:
                motif = "taux multiples"
            ecartees[motif] += 1
            non_resolues[code] = {
                "motif": motif,
                "sources_sh2017": sorted(set(sources)),
                "taux_trouves": sorted(taux),
            }

    resultat = {
        "_objet": (
            "Droit de base 2019 des positions tunisiennes SH 2022 sans ligne e-Tariff, "
            "par la table I de l'OMD au niveau SH6 ; retenu seulement si toutes les "
            "lignes e-Tariff des SH6 sources portent le même taux."
        ),
        "_table_i": "backend/data/legal_refs/zlecaf_application/sources/OMD_correlation_SH2022_SH2017_table_I.pdf",
        "_table_i_sha256": hashlib.sha256(TABLE_I.read_bytes()).hexdigest(),
        "_etariff_sha256": hashlib.sha256(ETARIFF.read_bytes()).hexdigest(),
        "_ecartees": dict(ecartees),
        "positions": resolues,
        "non_resolues": non_resolues,
    }
    SORTIE.write_text(json.dumps(resultat, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(resolues)} positions résolues, écartées {dict(ecartees)} -> {SORTIE}")


if __name__ == "__main__":
    main()
