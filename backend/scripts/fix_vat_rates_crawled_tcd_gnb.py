#!/usr/bin/env python3
"""Corrige la TVA du Tchad et de la Guinée-Bissau dans les sources consommées.

Une première correction avait visé ``backend/data/{TCD,GNB}_tariffs.json``.
Ce n'est pas ce que lit le pipeline : ``normalize_crawled.py`` part de
``backend/data/crawled/``, et c'est cette copie que le manifeste épingle. Les
taux faux y sont donc restés servis.

Tchad — le fichier portait 19,25 %, présenté comme « 17,5 % base + 10 %
centimes additionnels — Loi de Finances 2024 ». C'est le taux camerounais :
le Cameroun applique 17,5 % majorés de 10 % de centimes additionnels
communaux, pas le Tchad. Le gabarit CEMAC a été recopié d'un État membre à
l'autre. Le détail le prouve : le taux réduit du fichier vaut 9,90 %, soit
9 % × 1,10, appliqué à une liste de produits (sucre, huile, savon, textile)
qui est bien celle du Tchad. La liste est tchadienne, la majoration est
camerounaise.

Taux réels : 18 % standard, 9 % réduit sur les produits locaux (ciment, sucre,
huile, savon, textiles, béton, fer), 0 % à l'exportation.
Source : PwC Worldwide Tax Summaries — Chad, Other taxes.

Guinée-Bissau — le fichier portait 17 %, qui ne correspond à aucun régime :
ni l'IGV abrogé (19 % à taux unique), ni l'IVA qui l'a remplacé. L'IVA, institué
par la Lei nº 4/2022 et entré en vigueur le 1er janvier 2025, fixe à son
article 18º-1 : 10 % pour les importations de l'annexe I, 19 % pour les autres,
0 % à l'exportation.
Source : Alfândegas da Guiné-Bissau (alfandegas.mef.gw), citant le Código do IVA.

Ce que le script ne fait pas : il n'introduit pas les taux réduits. Les deux
pays en ont un, mais aucune des deux listes de produits concernés n'est
disponible ici au niveau de la position tarifaire — l'annexe I du Code bissau-
guinéen n'est pas dépouillée, et la liste tchadienne est énoncée en langage
naturel. Appliquer le taux normal à toutes les lignes reste le modèle en
place ; la limite est désormais inscrite dans les notes du fichier plutôt que
passée sous silence.

Usage :
    python backend/scripts/fix_vat_rates_crawled_tcd_gnb.py [--check]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CRAWLED = REPO_ROOT / "backend" / "data" / "crawled"

CORRECTIONS = {
    "TCD": {
        "wrong": 19.25,
        "right": 18.0,
        "tax_name": "Taxe sur la Valeur Ajoutée",
        "legend": "TVA (taux normal 18%)",
        "notes": {
            "TVA: 19.25% (17.5% base + 10% centimes additionnels) - Loi de Finances 2024":
                "TVA: 18% (taux normal). Source : PwC Worldwide Tax Summaries — Chad. "
                "La valeur 19,25% précédemment portée ici était le taux camerounais "
                "(17,5% + 10% de centimes additionnels), hérité du gabarit CEMAC.",
            "Taux réduit TVA: 9.90% pour produits locaux (sucre, huile, savon, textile)":
                "Taux réduit TVA: 9% sur les produits locaux (ciment, sucre, huile, "
                "savon, textiles, béton, fer) — NON modélisé ici : la liste n'est pas "
                "disponible au niveau de la position tarifaire. Toutes les lignes "
                "portent le taux normal.",
        },
    },
    "GNB": {
        "wrong": 17.0,
        "right": 19.0,
        "tax_name": "Imposto sobre o Valor Acrescentado (IVA)",
        "legend": None,
        "notes": {},
        "header_replacements": {
            "TVA = taux national 17%.":
                "IVA = taux national 19% (Lei nº 4/2022, art. 18º-1, en vigueur depuis "
                "le 01/01/2025). Taux réduit de 10% sur les importations de l'annexe I "
                "du Code de l'IVA, NON modélisé ici : l'annexe n'est pas dépouillée au "
                "niveau de la position. Source : alfandegas.mef.gw.",
        },
    },
}


def detect_indent(path: pathlib.Path, default: int = 2) -> int:
    """Indentation déjà sur disque, relue sur la deuxième ligne du fichier."""
    with open(path, encoding="utf-8") as handle:
        handle.readline()
        second = handle.readline()
    stripped = second.lstrip(" ")
    width = len(second) - len(stripped)
    return width if stripped.startswith('"') and width > 0 else default


def fix_country(iso: str, spec: dict, check_only: bool) -> int:
    path = CRAWLED / f"{iso}_tariffs.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    wrong, right = spec["wrong"], spec["right"]
    changed = 0

    for position in doc.get("positions", []):
        taxes = position.get("taxes") or {}
        if taxes.get("TVA") == wrong:
            taxes["TVA"] = right
            changed += 1
        for detail in position.get("taxes_detail") or []:
            if detail.get("tax_code") == "TVA" and detail.get("rate") == wrong:
                detail["rate"] = right
                detail["tax_name"] = spec["tax_name"]

    # Tout total agrégé doit suivre, sinon il contredit son propre détail.
    for position in doc.get("positions", []):
        for key in ("total_taxes_pct", "total_taxes"):
            if key in position:
                position[key] = round(
                    sum(d.get("rate", 0.0) for d in position.get("taxes_detail") or []), 4
                )

    legend = doc.get("tax_legend")
    if isinstance(legend, dict) and "TVA" in legend and spec["legend"]:
        legend["TVA"] = spec["legend"]

    notes = doc.get("notes")
    if isinstance(notes, list):
        doc["notes"] = [spec["notes"].get(n, n) for n in notes]

    for field in ("source", "note"):
        value = doc.get(field)
        if isinstance(value, str):
            for old, new in spec.get("header_replacements", {}).items():
                value = value.replace(old, new)
            doc[field] = value

    # Le contenu change : le sceau devient faux et doit être refait en aval.
    doc.pop("_integrity_seal", None)

    remaining = sum(
        1 for p in doc.get("positions", []) if (p.get("taxes") or {}).get("TVA") == wrong
    )
    print(f"{iso} : {changed} positions corrigées {wrong} → {right} ; "
          f"{remaining} restantes au taux erroné")
    if remaining:
        return 1

    if not check_only:
        path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=detect_indent(path)),
            encoding="utf-8",
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="ne rien écrire, seulement rapporter")
    args = parser.parse_args()
    return max(fix_country(iso, spec, args.check) for iso, spec in CORRECTIONS.items())


if __name__ == "__main__":
    sys.exit(main())
