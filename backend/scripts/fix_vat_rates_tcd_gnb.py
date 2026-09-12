"""Corrige deux taux de TVA erronés dans les fichiers tarifaires.

TCD (Tchad) — le fichier porte 19,25 % avec l'observation « TVA + Centimes
Additionnels (17,5 % + 10 % CAC) », qui décrit la structure **camerounaise**
et non tchadienne : la valeur a été héritée du gabarit CEMAC du Cameroun.
Le taux normal tchadien est de 18 %.
Source : PwC Worldwide Tax Summaries — Chad, Other taxes (« The VAT rate
applicable in Chad is 18% on all taxable operations »).

GNB (Guinée-Bissau) — le fichier porte 15 %, l'ancien régime antérieur à la
TVA. La TVA (IVA) instituée par la loi n°4/2022 est entrée en vigueur le
1er janvier 2025 au taux normal de 19 %.

Dans les deux cas ``total_taxes_pct`` est recalculé comme la somme des
``taxes_detail``, conformément à la convention du schéma.

Usage : python backend/scripts/fix_vat_rates_tcd_gnb.py [--apply]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

CORRECTIONS = {
    "TCD": {
        "old": 19.25,
        "new": 18.0,
        "observation": "TVA (taux normal)",
        "source": "PwC Worldwide Tax Summaries — Chad (taux normal 18 %)",
    },
    "GNB": {
        "old": 15.0,
        "new": 19.0,
        "observation": "Taxe sur la Valeur Ajoutée (IVA, loi n°4/2022, en vigueur 01/01/2025)",
        "source": "Loi n°4/2022 — IVA en vigueur au 01/01/2025, taux normal 19 %",
    },
}


def fix(iso: str, spec: dict, apply: bool) -> dict:
    path = DATA / f"{iso}_tariffs.json"
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)

    old, new = spec["old"], spec["new"]
    changed_lines = 0

    for line in doc.get("tariff_lines", []):
        if line.get("vat_rate") == old:
            line["vat_rate"] = new
            changed_lines += 1
        for tax in line.get("taxes_detail") or []:
            if tax.get("tax") == "TVA" and tax.get("rate") == old:
                tax["rate"] = new
                tax["observation"] = spec["observation"]
        if line.get("taxes_detail"):
            line["total_taxes_pct"] = round(
                sum(t.get("rate") or 0 for t in line["taxes_detail"]), 4
            )

    summary = doc.setdefault("summary", {})
    if summary.get("vat_rate_pct") == old:
        summary["vat_rate_pct"] = new
    summary["vat_source"] = spec["source"]

    # indent=2 : format déjà en place dans ces deux fichiers, préservé pour
    # que le diff ne porte que sur les valeurs corrigées.
    if apply:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return {"iso": iso, "lines_changed": changed_lines, f"{old}->{new}": True, "applied": apply}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon simulation)")
    args = parser.parse_args()
    for iso, spec in CORRECTIONS.items():
        print(json.dumps(fix(iso, spec, args.apply), ensure_ascii=False))
