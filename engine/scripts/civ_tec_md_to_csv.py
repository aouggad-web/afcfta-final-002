"""
Convertisseur TEC CEDEAO (Markdown CIV) → CSV
==============================================

Parse le fichier Markdown exporté par SYDAM WORLD (douanes.ci) — enrichi
des droits et taxes nationaux CIV — et produit un CSV canonique compatible
avec ``cedeao_tec_adapter.py``.

Colonnes produites :
    Code_SH ; Designation ; DD ; TVA ; PCC ; PCS ; PUA ; RST ; TSB ; PSV

Source : https://www.douanes.ci/info/tec
Format source : tableau Markdown avec artefacts PDF (cellules fusionnées,
tags <p>...</p>, séparateur décimal virgule, backslash-escaped dots).

Usage :
    python engine/scripts/civ_tec_md_to_csv.py \\
        engine/sources/civ_tec_cedeao_enrichi_27032026.md \\
        engine/sources/cedeao_tec_2022.csv
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Colonnes du Markdown source (position 0-based après N° et CODE_SH et LIBELLE)
# En-tête: DD|TUB|TVA|DUS|TSB|PSV|TUF|TUE|PCC|PCS|PUA|PSS|RST|TAB|TAI|TBG|TCI|TCB|TCT|TFS|TMP|TPQ|TSM|TSS
_COL = {
    "DD": 0, "TUB": 1, "TVA": 2, "DUS": 3, "TSB": 4, "PSV": 5,
    "TUF": 6, "TUE": 7, "PCC": 8, "PCS": 9, "PUA": 10, "PSS": 11,
    "RST": 12,
}

_SH_RE = re.compile(r"^\d{8,12}$")
_FLOAT_RE = re.compile(r"[-\d.,]+")


def _clean_val(v: str) -> str:
    v = v.strip().replace("\\.", ".").replace(",", ".")
    m = _FLOAT_RE.search(v)
    if not m:
        return ""
    result = m.group()
    # Un tiret seul n'est pas un taux valide (exempt / régime spécial)
    return "" if result == "-" else result


def _flatten_cell(cell: str) -> list[str]:
    """Extrait toutes les valeurs atomiques d'une cellule (multi-<p>, multi-espace)."""
    text = re.sub(r"<[^>]+>", " ", cell)
    return [v for v in re.split(r"\s+", text.strip()) if v]


def _split_libelles(cell: str) -> list[str]:
    """Éclate le libellé en une liste d'un élément par <p> block."""
    if "<p>" not in cell:
        return [re.sub(r"<[^>]+>", " ", cell).strip()]
    blocks = re.split(r"</?p>", cell)
    return [re.sub(r"<[^>]+>", " ", b).strip() for b in blocks if b.strip()]


def _parse_line(line: str) -> list[tuple[str, str, dict]]:
    """
    Retourne une liste de (code_sh, libelle, tax_dict) pour la ligne.
    Une ligne Markdown peut contenir plusieurs positions tarifaires.
    """
    parts = [p for p in line.split("|")]
    # structure : '' | N° | CODE_SH | LIBELLE | DD | TUB | TVA | ... | ''
    if len(parts) < 17:
        return []

    # Tous les codes SH présents dans la cellule (séparés par espaces ou <p>)
    codes_flat = [re.sub(r"[\s.]", "", v) for v in _flatten_cell(parts[2])]
    codes_flat = [c for c in codes_flat if _SH_RE.match(c)]
    if not codes_flat:
        return []

    libelles = _split_libelles(parts[3])
    n = len(codes_flat)

    # Valeurs de taxes : aplatir puis aligner avec les codes
    def get_vals(col_idx: int) -> list[str]:
        idx = 4 + col_idx
        if idx >= len(parts):
            return []
        return [_clean_val(v) for v in _flatten_cell(parts[idx])]

    tax_cols: dict[str, list[str]] = {k: get_vals(v) for k, v in _COL.items()}

    results = []
    for i, code in enumerate(codes_flat):
        libelle = libelles[i] if i < len(libelles) else (libelles[0] if libelles else "")
        taxes = {}
        for k, vals in tax_cols.items():
            if not vals:
                taxes[k] = ""
            elif len(vals) == n:
                taxes[k] = vals[i]
            elif len(vals) == 1:
                taxes[k] = vals[0]       # valeur unique répétée pour tous
            elif i < len(vals):
                taxes[k] = vals[i]
            else:
                taxes[k] = vals[-1]      # débordement : prendre la dernière
        results.append((code, libelle, taxes))

    return results


def parse(md_path: Path) -> list[dict]:
    """Parse le fichier Markdown et retourne une liste de lignes tarifaires."""
    rows: list[dict] = []
    seen: set[str] = set()

    with md_path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line.startswith("|"):
                continue
            if "**N°**" in line or "| - |" in line:
                continue

            for code, libelle, taxes in _parse_line(line):
                if code in seen:
                    continue
                seen.add(code)
                rows.append({
                    "Code_SH": code,
                    "Designation": libelle,
                    "DD": taxes["DD"],
                    "TVA": taxes["TVA"],
                    "PCC": taxes["PCC"],
                    "PCS": taxes["PCS"],
                    "PUA": taxes["PUA"],
                    "RST": taxes["RST"],
                    "TSB": taxes["TSB"],
                    "PSV": taxes["PSV"],
                })

    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    fieldnames = ["Code_SH", "Designation", "DD", "TVA", "PCC", "PCS",
                  "PUA", "RST", "TSB", "PSV"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def run(md_path: str, csv_path: str) -> dict:
    rows = parse(Path(md_path))
    write_csv(rows, Path(csv_path))
    return {"lines": len(rows), "out": csv_path}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convertit le TEC CIV (Markdown) en CSV")
    ap.add_argument("md_path", help="Fichier Markdown source (douanes.ci)")
    ap.add_argument("csv_path", help="Fichier CSV de sortie")
    args = ap.parse_args()

    result = run(args.md_path, args.csv_path)
    print(f"{result['lines']} lignes → {result['out']}")
