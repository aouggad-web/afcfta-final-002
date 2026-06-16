"""
Convertisseur Nigeria — customs.gov.ng (ECOWAS CET + taxes nationales NGA)
===========================================================================

Format source : positions (HS10), taxes list[{code, name, rate_pct, raw_value}].

Taxes NGA spécifiques :
  ID  → Import Duty (Customs Duty) — CET CEDEAO
  VAT → Value Added Tax (7.5% — taux NGA, inférieur au standard CEDEAO 18%)
  IAT → Import Adjustment Tax (variable)
  EXC → Excise Duty (alcool, tabac, véhicules de luxe)

Les libellés officiels (name) sont préservés dans name_fr.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, DataStatus, DutyBasis,
    Measure, MeasureType, Provenance, RateType,
    ReliabilityGrade, SCHEMA_VERSION,
)
from converters.base import (
    OUTPUT_DIR, clean_hs, digits_from_code, hs6_from_code,
    load_crawled, parse_duty_value, write_jsonl,
)

COUNTRY      = "NGA"
SOURCE_NAME  = "Nigeria Customs Service — ECOWAS Common External Tariff"
SOURCE_URL   = "https://www.customs.gov.ng"
SOURCE_DOC   = "Nigeria CET Schedule 2024 — customs.gov.ng"
VERSION_DATE = date(2024, 1, 1)

_NGA_TAX_CONFIG: dict[str, tuple[int, MeasureType, DutyBasis]] = {
    "ID":  (10, MeasureType.CUSTOMS_DUTY, DutyBasis.CIF),
    "VAT": (90, MeasureType.VAT,          DutyBasis.CIF_PLUS_INCLUDED),
    "IAT": (30, MeasureType.OTHER_TAX,    DutyBasis.CIF),
    "EXC": (35, MeasureType.EXCISE,       DutyBasis.CIF),
    "RL":  (20, MeasureType.LEVY,         DutyBasis.CIF),
}

_PROVENANCE = Provenance(
    data_status=DataStatus.PARTIAL,
    reliability=ReliabilityGrade.B,
    source_name=SOURCE_NAME,
    source_url=SOURCE_URL,
    source_document=SOURCE_DOC,
    version_date=VERSION_DATE,
    notes=(
        "Crawl customs.gov.ng — 6 363 positions HS10. "
        "VAT Nigeria = 7.5% (inférieur au standard CEDEAO 18%). "
        "IAT et EXC à confirmer contre Finance Act en vigueur."
    ),
)


def convert(output_path: Optional[Path] = None) -> int:
    data      = load_crawled(COUNTRY)
    positions = data.get("positions", [])
    now       = datetime.utcnow()

    lines: list[CanonicalTariffLine] = []

    for pos in positions:
        code_raw = str(pos.get("code_clean") or pos.get("code_raw") or "").strip()
        code_nat = clean_hs(code_raw)
        hs6      = hs6_from_code(code_nat)
        desc     = (pos.get("designation") or "").strip()
        chapter  = (pos.get("chapter") or hs6[:2]).zfill(2)
        unit     = pos.get("statistical_unit") or pos.get("unit")

        commodity = CommodityCode(
            country_iso3=COUNTRY,
            national_code=code_nat,
            hs6=hs6,
            digits=digits_from_code(code_nat),
            description_fr=desc,
            description_en=desc,
            description_official_fr=desc,
            chapter=chapter,
            unit=unit,
            hs_version="HS2022",
        )

        measures: list[Measure] = []
        for tax in (pos.get("taxes") or []):
            tax_code = str(tax.get("code") or "").strip().upper()
            tax_name = str(tax.get("name") or tax_code).strip()
            raw_val  = str(tax.get("raw_value") or "").strip()
            rate_pct = tax.get("rate_pct")

            config = _NGA_TAX_CONFIG.get(tax_code)
            if config:
                seq, mtype, basis = config
            else:
                from converters.base import classify_measure
                seq, mtype, basis = 50, classify_measure(tax_code, tax_name), DutyBasis.CIF

            duty = parse_duty_value(raw_val, rate_hint=rate_pct)

            basis_inc = ["ID"] if tax_code == "VAT" else []

            measures.append(Measure(
                country_iso3=COUNTRY,
                national_code=code_nat,
                measure_type=mtype,
                code=tax_code,
                name_fr=tax_name,
                name_en=tax_name,
                rate_pct=duty["rate_pct"],
                rate_type=duty["rate_type"],
                specific_amount=duty["specific_amount"],
                specific_unit=duty["specific_unit"],
                basis=basis,
                basis_includes=basis_inc,
                sequence=seq,
            ))

        measures.sort(key=lambda m: m.sequence)

        dd_rate = next((m.rate_pct for m in measures
                        if m.measure_type == MeasureType.CUSTOMS_DUTY), 0.0) or 0.0
        total_npf = sum(m.rate_pct for m in measures if m.rate_pct is not None)

        lines.append(CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=[],
            fiscal_advantages=[],
            total_npf_pct=round(total_npf, 4),
            total_zlecaf_pct=0.0,
            savings_pct=0.0,
            source_file=f"backend/data/crawled/{COUNTRY}_tariffs.json",
            last_updated=now,
            schema_version=SCHEMA_VERSION,
            provenance=_PROVENANCE,
        ))

    out = output_path or (OUTPUT_DIR / f"{COUNTRY}_canonical.jsonl")
    count = write_jsonl(lines, out)
    print(f"[NGA] {count} lignes → {out}")
    return count


if __name__ == "__main__":
    convert()
