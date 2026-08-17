#!/usr/bin/env python3
"""Extract the official South African AfCFTA duty column.

The input is SARS Schedule 1, Part 1.  Extraction uses the PDF bounding-box
layout so that the AfCFTA column is selected by position, not by guessing from
whitespace in plain text.  The generated JSON is deterministic and is intended
to be committed after review.

Compound and specific duties are preserved verbatim.  They are deliberately
marked non-calculable by the current value-only calculator: applying only their
ad-valorem component would understate the legal duty.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Iterable

SOURCE_DATE = "2026-08-06"
SOURCE_SHA256 = "e45e6d797a6372e881ef88063f4fde8eecbbcdf3c5f68d9c8183932478f90560"
SOURCE_URL = (
    "https://www.sars.gov.za/legal-counsel/primary-legislation/"
    "schedules-to-the-customs-and-excise-act-1964/"
)
SOURCE_PDF_URL = (
    "https://www.sars.gov.za/wp-content/uploads/Legal/SCEA1964/"
    "Legal-LPrim-CE-Sch1P1Chpt1-to-99-Schedule-No-1-Part-1-Chapters-1-to-99.pdf"
)

_TARIFF_CODE_RE = re.compile(r"\d[\d.]+")
_PERCENT_RE = re.compile(r"(?P<rate>\d+(?:[,.]\d+)?)%")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_rate_expression(expression: str) -> dict:
    """Classify a SARS duty expression without simplifying its legal effect."""
    normalized = " ".join(expression.split())
    if normalized.lower() == "free":
        return {
            "rate_expression": normalized,
            "rate_kind": "FREE",
            "ad_valorem_rate_pct": 0.0,
            "calculation_status": "CALCULABLE",
        }

    match = _PERCENT_RE.fullmatch(normalized)
    if match:
        return {
            "rate_expression": normalized,
            "rate_kind": "AD_VALOREM",
            "ad_valorem_rate_pct": float(match.group("rate").replace(",", ".")),
            "calculation_status": "CALCULABLE",
        }

    return {
        "rate_expression": normalized,
        "rate_kind": "COMPOUND" if "%" in normalized else "SPECIFIC",
        "ad_valorem_rate_pct": None,
        "calculation_status": "REQUIRES_QUANTITY",
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element: ET.Element, name: str) -> Iterable[ET.Element]:
    return (child for child in element.iter() if _local_name(child.tag) == name)


def extract_bbox_xml(xml_path: Path) -> list[dict]:
    """Return exact national tariff lines and their AfCFTA duty expressions."""
    root = ET.parse(xml_path).getroot()
    extracted: list[dict] = []

    for page_number, page in enumerate(_children(root, "page"), start=1):
        words = [
            (
                float(word.attrib["xMin"]),
                float(word.attrib["yMin"]),
                "".join(word.itertext()).strip(),
            )
            for word in _children(page, "word")
        ]
        blocks = []
        for block in _children(page, "block"):
            block_words = ["".join(word.itertext()).strip() for word in _children(block, "word")]
            if block_words:
                blocks.append(
                    (
                        float(block.attrib["xMin"]),
                        float(block.attrib["yMin"]),
                        " ".join(block_words),
                    )
                )

        for x_min, y_min, printed_code in words:
            clean_code = re.sub(r"\D", "", printed_code)
            if not (
                x_min < 100
                and len(clean_code) in (6, 8)
                and _TARIFF_CODE_RE.fullmatch(printed_code)
            ):
                continue

            # A legal tariff line has a one-digit check digit in the CD column.
            # Headings and intermediate grouping rows do not and must be skipped.
            has_check_digit = any(
                105 <= cd_x <= 135 and abs(cd_y - y_min) < 0.6 and re.fullmatch(r"\d", cd_text)
                for cd_x, cd_y, cd_text in words
            )
            if not has_check_digit:
                continue

            # The page is landscape (rotated A4).  The AfCFTA cell is a distinct
            # PDF text block beginning at x~=757.  Reading the whole block keeps
            # multi-line expressions such as "40% or 240c/kg" intact and avoids
            # swallowing long article descriptions that merely cross this x.
            rate_blocks = [
                text
                for block_x, block_y, text in blocks
                if block_x >= 750 and abs(block_y - y_min) < 0.8
            ]
            if len(rate_blocks) != 1:
                raise ValueError(
                    f"Expected one AfCFTA cell for {clean_code} on page {page_number}; "
                    f"found {len(rate_blocks)}"
                )

            extracted.append(
                {
                    "hs_code": clean_code,
                    "page": page_number,
                    **classify_rate_expression(rate_blocks[0]),
                }
            )

    codes = [line["hs_code"] for line in extracted]
    duplicates = [code for code, count in Counter(codes).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate tariff codes in SARS source: {duplicates[:10]}")
    if len(extracted) < 8500:
        raise ValueError(f"Suspiciously small SARS extraction: {len(extracted)} lines")
    return sorted(extracted, key=lambda line: line["hs_code"])


def build_dataset(pdf_path: Path, pdftotext: str = "pdftotext") -> dict:
    actual_sha256 = _sha256(pdf_path)
    if actual_sha256 != SOURCE_SHA256:
        raise ValueError(
            "SARS PDF hash mismatch: extraction refused until the new official "
            f"source is reviewed (got {actual_sha256})"
        )

    with tempfile.TemporaryDirectory(prefix="sars-afcfta-") as temp_dir:
        xml_path = Path(temp_dir) / "schedule.xml"
        subprocess.run(
            [pdftotext, "-bbox-layout", str(pdf_path), str(xml_path)],
            check=True,
        )
        lines = extract_bbox_xml(xml_path)

    counts = Counter(line["rate_kind"] for line in lines)
    return {
        "schema_version": 1,
        "country_iso3": "ZAF",
        "agreement": "AfCFTA",
        "source_title": "SARS Schedule 1 Part 1 — Customs Duty",
        "source_date": SOURCE_DATE,
        "source_url": SOURCE_URL,
        "source_pdf_url": SOURCE_PDF_URL,
        "source_pdf_sha256": SOURCE_SHA256,
        "source_column": "AfCFTA",
        "line_count": len(lines),
        "rate_kind_counts": dict(sorted(counts.items())),
        "lines": lines,
    }


def write_dataset(output: Path, dataset: dict) -> None:
    """Write deterministic JSON, gzip-compressed when the target is ``.gz``."""
    serialized = (json.dumps(dataset, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".gz":
        output.write_bytes(gzip.compress(serialized, compresslevel=9, mtime=0))
    else:
        output.write_bytes(serialized)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pdftotext", default="pdftotext")
    args = parser.parse_args()

    dataset = build_dataset(args.pdf, args.pdftotext)
    write_dataset(args.output, dataset)


if __name__ == "__main__":
    main()
