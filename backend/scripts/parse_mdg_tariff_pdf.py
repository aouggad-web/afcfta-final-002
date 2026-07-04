#!/usr/bin/env python3
"""Parseur du Tarif des Douanes Madagascar depuis le PDF officiel.

Le réseau de l'environnement courant bloque l'API eTariff. Ce script permet de
travailler à partir du PDF officiel téléchargé manuellement depuis la page des
Douanes Madagascar, ou à partir d'un texte déjà extrait du PDF.

Exemples:
  python backend/scripts/parse_mdg_tariff_pdf.py \
    --input engine/audits/official_sources/MDG/TARIF-DES-DOUANES-2026.pdf \
    --out backend/data/crawled/MDG_tariffs.json

  python backend/scripts/parse_mdg_tariff_pdf.py \
    --text engine/audits/official_sources/MDG/TARIF-DES-DOUANES-2026.txt \
    --out backend/data/crawled/MDG_tariffs.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

DEFAULT_SOURCE_URL = "https://www.douanes.gov.mg/srcs/uploads/2026/01/TARIF-DES-DOUANES-2026.pdf"
DEFAULT_SOURCE_PAGE = "https://www.douanes.gov.mg/tarifs-des-douanes/"

CODE_RE = re.compile(
    r"^\s*(?P<code>\d{4}[.\s]\d{2}(?:[.\s]\d{2}){1,2})\s+[-–—]*\s*(?P<rest>.+?)\s*$"
)
TRAILING_COLUMNS_RE = re.compile(
    r"^(?P<designation>.*?)(?:\s{2,}|\s[-–—]{2,}\s*)"
    r"(?P<columns>(?:[A-Za-z%./]+|\d+(?:[,.]\d+)?%?)(?:\s+|$).*)$"
)
RATE_TOKEN_RE = re.compile(r"^(?:ex|EX|Ex|\d+(?:[,.]\d+)?%?|-)\Z")


@dataclass(frozen=True)
class MdgTariffPosition:
    code: str
    code_clean: str
    code_length: int
    designation: str
    chapter: str
    hs2: str
    hs4: str
    hs6: str
    unit: str | None = None
    raw_columns: list[str] | None = None
    source_quality: str = "official_pdf_extracted"


def normalize_code(raw: str) -> tuple[str, str]:
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 8:
        raise ValueError(f"Code tarifaire trop court: {raw!r}")
    dotted = ".".join([digits[:4], digits[4:6], digits[6:8], digits[8:10]]).rstrip(".")
    return dotted, digits


def _split_designation_and_columns(rest: str) -> tuple[str, list[str]]:
    rest = rest.strip()
    match = TRAILING_COLUMNS_RE.match(rest)
    if not match:
        return rest.strip(" -–—"), []

    designation = match.group("designation").strip(" -–—")
    tokens = [t.strip() for t in match.group("columns").split() if t.strip()]
    if not tokens:
        return rest.strip(" -–—"), []
    return designation, tokens


def parse_lines(lines: Iterable[str]) -> list[MdgTariffPosition]:
    """Extrait les positions tarifaires depuis du texte PDF déjà linéarisé."""
    positions: list[MdgTariffPosition] = []
    seen: set[str] = set()

    for line in lines:
        match = CODE_RE.match(line)
        if not match:
            continue

        code, code_clean = normalize_code(match.group("code"))
        if code_clean in seen:
            continue

        designation, columns = _split_designation_and_columns(match.group("rest"))
        if not designation or len(designation) < 2:
            continue

        unit = None
        if columns and not RATE_TOKEN_RE.match(columns[0]):
            unit = columns[0]

        positions.append(
            MdgTariffPosition(
                code=code,
                code_clean=code_clean,
                code_length=len(code_clean),
                designation=designation,
                chapter=code_clean[:2],
                hs2=code_clean[:2],
                hs4=code_clean[:4],
                hs6=code_clean[:6],
                unit=unit,
                raw_columns=columns or None,
            )
        )
        seen.add(code_clean)

    return positions


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrait le texte via l'outil système pdftotext lorsqu'il est disponible."""
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError(
            "pdftotext est requis pour extraire directement un PDF. "
            "Installe poppler-utils ou fournis --text avec un fichier texte déjà extrait."
        )
    try:
        completed = subprocess.run(
            [pdftotext, "-layout", str(pdf_path), "-"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        details = (e.stderr or "").strip()
        raise RuntimeError(f"Échec pdftotext{': ' + details if details else ''}") from e
    return completed.stdout


def build_output(positions: list[MdgTariffPosition], source_file: str | None = None) -> dict:
    return {
        "country_code": "MDG",
        "country_name": "Madagascar",
        "source": "Direction Générale des Douanes de Madagascar — Tarif des Douanes 2026",
        "source_url": DEFAULT_SOURCE_URL,
        "source_page": DEFAULT_SOURCE_PAGE,
        "source_file": source_file,
        "data_status": "PARTIAL",
        "data_quality": "SOURCE_FOUND_PDF_PARSED — à valider par gate de couverture",
        "method": "official_pdf_parser",
        "hs_base": "SH 2022",
        "edition": "Janvier 2026",
        "extracted_at": datetime.now(UTC).isoformat(),
        "total_positions": len(positions),
        "positions": [asdict(p) for p in positions],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", type=Path, help="PDF officiel Madagascar à parser")
    src.add_argument("--text", type=Path, help="Texte déjà extrait du PDF")
    parser.add_argument("--out", type=Path, required=True, help="JSON de sortie")
    parser.add_argument("--min-positions", type=int, default=1000)
    args = parser.parse_args()

    if args.text:
        text = args.text.read_text(encoding="utf-8")
        source_file = str(args.text)
    else:
        text = extract_text_from_pdf(args.input)
        source_file = str(args.input)

    positions = parse_lines(text.splitlines())
    if len(positions) < args.min_positions:
        raise SystemExit(
            f"Extraction insuffisante: {len(positions)} positions < {args.min_positions}. "
            "Vérifier le PDF/texte source ou ajuster --min-positions pour un test."
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = build_output(positions, source_file=source_file)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MDG: {len(positions)} positions écrites dans {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
