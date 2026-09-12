"""Retire de backend/data/DZA_tariffs.json les taux ZLECAf fabriqués.

Les 5 193 lignes concernées portent ``zlecaf_rate = 0.0`` avec
``zlecaf_source = "ZLECAf"`` — un marqueur déjà répertorié comme fabriqué
dans ``TariffDataService._FABRICATED_ZLECAF_SOURCES`` et neutralisé au
runtime, mais resté physiquement dans le fichier.

Confrontées à la circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024 et à
ses listes de concessions, 818 de ces valeurs sont fausses :

  - 402 positions gelées (règles d'origine non arrêtées) → droit commun ;
  - 282 positions de la liste (B) → 80 % du taux de base 2019 en 2026 ;
  - 134 positions de la liste (C), exclues du démantèlement → droit commun.

Les 4 375 restantes (liste A, exonérée depuis le 1.1.2025) sont justes
aujourd'hui, mais un champ scalaire par ligne ne peut de toute façon pas
représenter un taux qui dépend du partenaire, de la liste et de l'année :
seuls 22 des 54 États membres ont activé l'accord avec l'Algérie, et les
autres restent au droit commun. La source de vérité est donc
``services.zlecaf_schedule_dza.compute_dza_zlecaf_rate``.

Usage : python backend/scripts/purge_dza_fabricated_zlecaf_rates.py [--apply]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "data" / "DZA_tariffs.json"
FABRICATED_SOURCES = {"ZLECAf", "ZLECAf (produit normal)", "ZLECAf (produit sensible)"}


def purge(path: Path, apply: bool) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)

    removed = kept = 0
    for line in doc.get("tariff_lines", []):
        if line.get("zlecaf_source") in FABRICATED_SOURCES:
            line.pop("zlecaf_rate", None)
            line.pop("zlecaf_source", None)
            removed += 1
        elif "zlecaf_rate" in line or "zlecaf_source" in line:
            kept += 1

    # indent=1 : format déjà en place dans le fichier, préservé pour que le
    # diff ne porte que sur les champs retirés.
    if apply and removed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
            f.write("\n")

    return {"removed": removed, "kept": kept, "applied": apply}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="écrit le fichier (sinon simulation)")
    args = parser.parse_args()
    print(json.dumps(purge(TARGET, args.apply), indent=2))
