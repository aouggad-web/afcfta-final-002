#!/usr/bin/env python3
"""Build fail-closed Mauritius VAT coverage from the dated MRA tariff.

The tariff's blank VAT cells are recorded as unavailable, not interpreted as
zero-rated or exempt.  Only rows that actually publish a numeric VAT rate are
made executable.  An exemption may only be added manually from an independent
official exemption schedule with its own hash and exact HS scope.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "backend/data/MUS_tariffs.json"
OUTPUT = ROOT / "data/mauritius/vat_measures.json"
EFFECTIVE_FROM = "2026-04-01"


def _vat_rate(line: dict) -> str | None:
    for tax in line.get("taxes_detail") or []:
        name = str(tax.get("tax", "")).replace(".", "").upper()
        if name.startswith(("TVA", "VAT")):
            value = tax.get("rate")
            if value is not None:
                return f"{float(value):g}%"
    return None


def main() -> int:
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    digest = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    rated: dict[str, set[str]] = defaultdict(set)
    unavailable: dict[str, set[str]] = defaultdict(set)
    blank_lines = 0
    for line in canonical["tariff_lines"]:
        codes = {p["code"] for p in line.get("sub_positions") or [] if p.get("code")}
        rate = _vat_rate(line)
        if rate is None:
            blank_lines += 1
            unavailable[line["hs6"][:2]].update(codes)
        else:
            rated[rate].update(codes)

    common = {
        "effective_from": EFFECTIVE_FROM,
        "effective_to": None,
        "source_id": "MUS-MRA-TARIFF-20260401",
        "source_url": "https://www.mra.mu/download/TariffInfo010426.pdf",
        "source_sha256": digest,
        "source_hash_scope": "normalized canonical extraction: backend/data/MUS_tariffs.json",
        "source_document_sha256": None,
        "source_extraction_date": "2026-06-15",
        "source_effective_date": EFFECTIVE_FROM,
        "transformation_trace": "Numeric VAT value copied from taxes_detail; no missing value was imputed.",
    }
    rates = []
    for rate, codes in sorted(rated.items()):
        rates.append({
            "record_id": f"MUS-VAT-RATE-{rate.removesuffix('%').replace('.', '_')}-20260401",
            "rate": rate,
            "rate_basis": "customs value plus customs duty where supported by the official guide",
            "legal_status": "CURRENT_OFFICIAL_GUIDE",
            "legal_reference": "MRA Integrated Tariff Schedule, as at 01 April 2026, published VAT column",
            "verification_status": "VERIFIED_OFFICIAL_GUIDE",
            "hs_codes_explicit": sorted(codes),
            **common,
        })
    unavailable_records = [{
        "record_id": f"MUS-VAT-NOT-AVAILABLE-CH{chapter}",
        "availability": "NOT_AVAILABLE",
        "reason": "The tariff VAT field is blank; no independent official exemption schedule was supplied.",
        "hs_codes_explicit": sorted(codes),
        "transformation_trace": "Blank VAT field preserved as NOT_AVAILABLE; no rate or exemption inferred.",
        **{k: v for k, v in common.items() if k != "transformation_trace"},
    } for chapter, codes in sorted(unavailable.items())]
    document = {
        "schema_version": "1.0",
        "country": "MUS",
        "as_of": "2026-09-06",
        "vat_rates": rates,
        "vat_exemptions": [],
        "vat_zero_rated": [],
        "vat_unavailable": unavailable_records,
        "coverage_summary": {
            "lines_with_published_rate": len(canonical["tariff_lines"]) - blank_lines,
            "lines_with_blank_rate": blank_lines,
            "blank_sub_positions": sum(map(len, unavailable.values())),
            "coverage_complete": False,
        },
        "provenance": {"canonical_path": "backend/data/MUS_tariffs.json", "canonical_sha256": digest},
    }
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
