"""
Convertisseur EAC CET 2022 (Markdown/HTML) → CSV
=================================================

Parse le document officiel « EAC Common External Tariff 2022 Version »
(Annexe 1 au Protocole d'Union Douanière, EAC Gazette, en vigueur au
1er juillet 2022) converti en Markdown avec tables HTML, et produit un
CSV canonique pour ``eac_cet_adapter.py``.

Structure source :
  - Schedule 1 : tarif complet 4 bandes (0/10/25/35 %) — les lignes
    marquées « SI » renvoient au Schedule 2.
  - Schedule 2 : produits sensibles (35-100 %, taux mixtes
    « 75% or $345/MT whichever is higher ») — REMPLACE le taux du
    Schedule 1 pour les codes concernés.

Colonnes produites :
    Code_SH ; Designation ; Unite ; DD ; DD_specifique ;
    DD_unite_specifique ; Sensible ; Taux_brut

Usage :
    python engine/scripts/eac_cet_md_to_csv.py \\
        engine/sources/eac_cet_2022_30juin.md \\
        engine/sources/eac_cet_2022.csv
"""

import argparse
import csv
import re
from pathlib import Path

_CODE_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")
_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
# « 75% or $345/MT whichever is higher » / « 35% or USD 0.40/kg … »
_MIXED_RE = re.compile(r"([\d.]+)\s*%\s*or\s*(?:\$|USD?)\s*([\d.]+)\s*/\s*(\w+)", re.IGNORECASE)
_PCT_RE = re.compile(r"([\d.]+)\s*%")

SCHEDULE2_MARKER = "SENSITIVE ITEMS"

# Unités statistiques rencontrées dans le document
_KNOWN_UNITS = {
    "u",
    "kg",
    "mt",
    "carat",
    "m2",
    "m3",
    "l",
    "m",
    "pa",
    "2u",
    "1000u",
    "g",
    "ct",
    "no",
}


def _strip(cell: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cell)).strip()


def parse_rate(raw: str) -> dict:
    """Décompose un taux brut en composantes ad valorem / spécifique."""
    raw = raw.strip()
    out = {"pct": "", "specific": "", "specific_unit": "", "raw": raw}
    m = _MIXED_RE.search(raw)
    if m:
        out["pct"] = m.group(1)
        out["specific"] = m.group(2)
        out["specific_unit"] = f"USD/{m.group(3)}"
        return out
    m = _PCT_RE.search(raw)  # gère aussi « kg 25% » et « 25%25% »
    if m:
        out["pct"] = m.group(1)
    return out


def _parse_row(cells: list[str], in_schedule2: bool) -> dict | None:
    """Extrait (code, description, unité, taux) d'une ligne <tr>, ou None."""
    code_idx = next((i for i, c in enumerate(cells) if _CODE_RE.match(c)), None)
    if code_idx is None or code_idx + 1 >= len(cells):
        return None

    code = cells[code_idx].replace(".", "")
    description = cells[code_idx + 1]
    rest = cells[code_idx + 2 :]

    unit, rate_raw = "", ""
    for c in rest:
        if not c:
            continue
        if "%" in c or "$" in c or c.upper() == "SI":
            rate_raw = c
            # cellule fusionnée « kg 25% » : récupérer l'unité en tête
            lead = c.split()[0].lower() if c.split() else ""
            if lead in _KNOWN_UNITS:
                unit = unit or c.split()[0]
        elif not unit and c.lower() in _KNOWN_UNITS:
            unit = c

    if not rate_raw:
        return None

    rate = parse_rate(rate_raw)
    return {
        "Code_SH": code,
        "Designation": description,
        "Unite": unit,
        "DD": rate["pct"],
        "DD_specifique": rate["specific"],
        "DD_unite_specifique": rate["specific_unit"],
        "Sensible": "1" if (in_schedule2 or rate_raw.upper() == "SI") else "0",
        "Taux_brut": rate["raw"],
        "_is_si_ref": rate_raw.upper() == "SI",
    }


def parse(md_path: Path) -> tuple[list[dict], dict]:
    """Parse le document ; le Schedule 2 écrase les taux « SI » du Schedule 1."""
    rows: dict[str, dict] = {}
    stats = {"schedule1": 0, "schedule2_overrides": 0, "si_unresolved": 0}
    in_schedule2 = False

    with md_path.open(encoding="utf-8") as f:
        for line in f:
            if SCHEDULE2_MARKER in line:
                in_schedule2 = True
            for tr in _TR_RE.finditer(line):
                cells = [_strip(c) for c in _TD_RE.findall(tr.group(1))]
                row = _parse_row(cells, in_schedule2)
                if row is None:
                    continue
                code = row["Code_SH"]
                if in_schedule2:
                    if code in rows:
                        stats["schedule2_overrides"] += 1
                    rows[code] = row
                elif code not in rows:
                    rows[code] = row
                    stats["schedule1"] += 1

    # Lignes « SI » jamais résolues par le Schedule 2 → exclues (pas de taux)
    final = []
    for row in rows.values():
        if row.pop("_is_si_ref") and not row["DD"]:
            stats["si_unresolved"] += 1
            continue
        final.append(row)
    return final, stats


FIELDNAMES = [
    "Code_SH",
    "Designation",
    "Unite",
    "DD",
    "DD_specifique",
    "DD_unite_specifique",
    "Sensible",
    "Taux_brut",
]


def write_csv(rows: list[dict], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def run(md_path: str, csv_path: str) -> dict:
    rows, stats = parse(Path(md_path))
    write_csv(rows, Path(csv_path))
    return {"lines": len(rows), "out": csv_path, **stats}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convertit l'EAC CET 2022 (Markdown) en CSV")
    ap.add_argument("md_path", help="Fichier Markdown source (EAC Gazette)")
    ap.add_argument("csv_path", help="Fichier CSV de sortie")
    args = ap.parse_args()
    r = run(args.md_path, args.csv_path)
    print(
        f"{r['lines']} lignes → {r['out']} "
        f"(Schedule 1: {r['schedule1']}, écrasées par Schedule 2: "
        f"{r['schedule2_overrides']}, SI non résolues: {r['si_unresolved']})"
    )
