"""
Fusion de publication par code SH — permet le crawl PAR TRANCHES des gros pays.

L'étape « Publier » du workflow écrasait le dataset existant (cp). Pour MAR
(~13k positions) ou TUN (~17,5k), un crawl complet dépasse la durée d'un run :
on crawle par tranches de chapitres, et chaque tranche doit FUSIONNER dans le
fichier existant, pas le remplacer.

Règle de fusion (même esprit que AlgeriaConformeproScraper.save_final) :
  - index des positions existantes par (hs_code | code | raw_code) ;
  - les positions nouvellement crawlées REMPLACENT les anciennes à même code ;
  - les autres sont conservées telles quelles (y compris les entrées au format
    hérité — elles convergent vers le contrat v2 au fil des tranches) ;
  - les métadonnées de tête (source, extracted_at, calculation_rules, stats)
    viennent du crawl NEUF ; `merged_from_existing` trace la fusion.

CLI (workflow) :
    python -m crawlers.scrapling_engine.merge_publish \
        --new /tmp/MAR_tariffs.json \
        --existing backend/data/crawled/MAR_tariffs.json \
        --out backend/data/crawled/MAR_tariffs.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict


def _key(position: Dict) -> str:
    return str(
        position.get("hs_code") or position.get("code") or position.get("raw_code") or ""
    ).strip()


def merge(new_data: Dict, existing_data: Dict) -> Dict:
    merged: Dict[str, Dict] = {}
    kept_existing = 0
    for pos in existing_data.get("sub_positions", []):
        k = _key(pos)
        if k:
            merged[k] = pos
            kept_existing += 1
    replaced = 0
    added = 0
    for pos in new_data.get("sub_positions", []):
        k = _key(pos)
        if not k:
            continue
        if k in merged:
            replaced += 1
        else:
            added += 1
        merged[k] = pos

    out = dict(new_data)  # métadonnées du crawl neuf (source, extracted_at, …)
    out["sub_positions"] = list(merged.values())
    stats = dict(out.get("stats") or {})
    stats["sub_positions"] = len(out["sub_positions"])
    out["stats"] = stats
    out["merged_from_existing"] = {
        "existing_positions": kept_existing,
        "replaced_by_new_crawl": replaced,
        "added_by_new_crawl": added,
        "total_after_merge": len(out["sub_positions"]),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Fusion par code SH d'un crawl dans le dataset")
    ap.add_argument("--new", required=True, type=Path, help="JSON du crawl neuf (tranche)")
    ap.add_argument("--existing", type=Path, default=None, help="Dataset existant (optionnel)")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    new_data = json.load(open(args.new, encoding="utf-8"))
    if args.existing and args.existing.exists():
        try:
            existing_data = json.load(open(args.existing, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing_data = {}
    else:
        existing_data = {}

    out = merge(new_data, existing_data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    info = out["merged_from_existing"]
    print(
        f"Fusion : {info['existing_positions']} existantes, "
        f"{info['replaced_by_new_crawl']} remplacées, {info['added_by_new_crawl']} ajoutées "
        f"-> {info['total_after_merge']} au total"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
