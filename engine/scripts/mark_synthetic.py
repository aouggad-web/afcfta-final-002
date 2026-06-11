"""
Marquage des données synthétiques — Migration v4
=================================================

Stamps tous les fichiers *_canonical.jsonl existants avec
provenance SYNTHETIC/D quand aucune provenance n'est présente
ou quand data_status n'est pas VERIFIED/PARTIAL.

Idempotent : ne touche jamais une ligne déjà VERIFIED ou PARTIAL.

Usage:
    python engine/scripts/mark_synthetic.py [--dry-run]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"

SYNTHETIC_PROVENANCE = {
    "data_status": "SYNTHETIC",
    "reliability": "D",
    "source_name": "Données synthétiques générées par template",
    "source_url": None,
    "source_document": None,
    "version_date": None,
    "retrieved_at": datetime.now().isoformat(),
    "notes": (
        "Ces données sont générées par template à partir de la nomenclature "
        "SH6 mondiale. Les taux, formalités et codes nationaux ne correspondent "
        "pas à des sources officielles vérifiées. Ne pas utiliser pour des "
        "décisions commerciales réelles."
    ),
}

DISCLAIMER = (
    "Ces données sont synthétiques et non vérifiées. "
    "Consultez les tarifs douaniers officiels avant toute opération commerciale."
)

PROTECTED = {"VERIFIED", "PARTIAL"}


def _mark_file(path: Path, dry_run: bool) -> dict:
    lines_total = 0
    lines_marked = 0
    lines_skipped = 0

    out_lines = []
    with path.open(encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            lines_total += 1
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                out_lines.append(raw)
                continue

            prov = obj.get("provenance") or {}
            status = prov.get("data_status", "")
            if status in PROTECTED:
                lines_skipped += 1
                out_lines.append(raw)
                continue

            obj["provenance"] = SYNTHETIC_PROVENANCE.copy()
            obj["provenance"]["retrieved_at"] = datetime.now().isoformat()
            obj["schema_version"] = "4.0"
            out_lines.append(json.dumps(obj, ensure_ascii=False))
            lines_marked += 1

    if not dry_run and lines_marked > 0:
        with path.open("w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")

    return {"total": lines_total, "marked": lines_marked, "skipped": lines_skipped}


def run(dry_run: bool = False) -> dict:
    jsonl_files = sorted(OUTPUT_DIR.glob("*_canonical.jsonl"))
    registry = {}
    grand_total = grand_marked = grand_skipped = 0

    for path in jsonl_files:
        country = path.stem.replace("_canonical", "")
        stats = _mark_file(path, dry_run)
        registry[country] = {
            "data_status": "SYNTHETIC",
            "reliability": "D",
            "lines_total": stats["total"],
            "lines_marked": stats["marked"],
            "lines_skipped_protected": stats["skipped"],
            "disclaimer": DISCLAIMER,
        }
        grand_total += stats["total"]
        grand_marked += stats["marked"]
        grand_skipped += stats["skipped"]
        print(
            f"  {country}: {stats['total']} lignes → "
            f"{stats['marked']} marquées, {stats['skipped']} protégées"
        )

    status_doc = {
        "generated_at": datetime.now().isoformat(),
        "schema_version": "4.0",
        "dry_run": dry_run,
        "summary": {
            "countries": len(registry),
            "lines_total": grand_total,
            "lines_marked": grand_marked,
            "lines_skipped_protected": grand_skipped,
        },
        "countries": registry,
    }

    out_path = OUTPUT_DIR / "DATA_STATUS.json"
    if not dry_run:
        out_path.write_text(json.dumps(status_doc, ensure_ascii=False, indent=2))
        print(f"\nRegistre écrit → {out_path}")

    return status_doc


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Marque les données synthétiques v4")
    ap.add_argument("--dry-run", action="store_true", help="Simulation sans écriture")
    args = ap.parse_args()

    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"{prefix}Marquage des données synthétiques...")
    result = run(dry_run=args.dry_run)
    s = result["summary"]
    print(
        f"\n{prefix}Total : {s['lines_total']} lignes | "
        f"{s['lines_marked']} marquées | "
        f"{s['lines_skipped_protected']} protégées | "
        f"{s['countries']} pays"
    )
