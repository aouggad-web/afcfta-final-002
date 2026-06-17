"""
Convertisseur SACU — sars.gov.za (Schedule 1)
===============================================

5 membres : ZAF, NAM, BWA, LSO, SWZ.
TEC identique pour tous — taxes nationales (TVA) différentes par membre.

Format source : positions (HS6-8), taxes list[{code, name, rate_pct, raw_value}].
  GENERAL → Droit de Douane commun SACU
  EU_UK, EFTA, SADC, MERCOSUR, AfCFTA → FiscalAdvantage (taux préférentiels)
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, DataStatus, DutyBasis,
    FiscalAdvantage, Measure, MeasureType, Provenance, RateType,
    ReliabilityGrade, SCHEMA_VERSION,
)
from converters.base import (
    OUTPUT_DIR, clean_hs, digits_from_code, hs6_from_code,
    load_crawled, parse_duty_value, write_jsonl,
)

# Membres SACU et leur TVA nationale
SACU_MEMBERS: dict[str, tuple[str, float, str]] = {
    # iso3 → (TVA code, TVA rate %, TVA name)
    "ZAF": ("VAT", 15.0, "Value Added Tax"),
    "NAM": ("VAT", 15.0, "Value Added Tax"),
    "BWA": ("VAT", 14.0, "Value Added Tax"),
    "LSO": ("VAT", 15.0, "Value Added Tax"),
    "SWZ": ("VAT", 15.0, "Value Added Tax"),
}

SOURCE_NAME = "South African Revenue Service (SARS) — Schedule 1 Part 1"
SOURCE_URL  = "https://www.sars.gov.za/customs-and-excise/tariff-books/schedules/"
SOURCE_DOC  = "SARS Schedule 1 Part 1 — 2025 (Customs Tariff Act)"

# Codes préférentiels → accord
_PREF_MAP: dict[str, tuple[str, str]] = {
    "EU_UK":     ("EU / UK Preferential Rate",    "DETA EU-UK"),
    "EFTA":      ("EFTA Preferential Rate",        "Accord EFTA-SACU"),
    "SADC":      ("SADC Preferential Rate",        "Accord SADC"),
    "MERCOSUR":  ("MERCOSUR Preferential Rate",    "Accord MERCOSUR-SACU"),
    "AfCFTA":    ("AfCFTA Preferential Rate",      "ZLECAf"),
    "GSP":       ("GSP Preferential Rate",         "SGP"),
    "OTHER":     ("Taux préférentiel autre",        "Accord bilatéral"),
}

_DUTY_CODES = {"GENERAL", "GEN", "CUSTOMS", "CUSTOMS_DUTY"}


def _provenance(country: str) -> Provenance:
    return Provenance(
        data_status=DataStatus.PARTIAL,
        reliability=ReliabilityGrade.B,
        source_name=SOURCE_NAME,
        source_url=SOURCE_URL,
        source_document=SOURCE_DOC,
        version_date=date(2025, 1, 1),
        notes=(f"Crawl sars.gov.za — TEC SACU commun ; TVA {country} = "
               f"{SACU_MEMBERS[country][1]}% (taux national standard, à confirmer)"),
    )


def convert_country(country: str, output_path: Optional[Path] = None) -> int:
    if country not in SACU_MEMBERS:
        raise ValueError(f"{country} n'est pas un membre SACU")

    vat_code, vat_rate, vat_name = SACU_MEMBERS[country]
    prov = _provenance(country)

    data      = load_crawled(country)
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
            country_iso3=country,
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

        measures:   list[Measure]        = []
        advantages: list[FiscalAdvantage] = []
        dd_rate: Optional[float] = None

        for tax in (pos.get("taxes") or []):
            code  = str(tax.get("code") or "").strip().upper()
            name  = str(tax.get("name") or code).strip()
            duty  = parse_duty_value(str(tax.get("raw_value") or ""),
                                     rate_hint=tax.get("rate_pct"))

            if code in _DUTY_CODES or code == "GENERAL":
                dd_rate = duty["rate_pct"]
                measures.append(Measure(
                    country_iso3=country,
                    national_code=code_nat,
                    measure_type=MeasureType.CUSTOMS_DUTY,
                    code="DD",
                    name_fr=name,
                    name_en=name,
                    rate_pct=duty["rate_pct"],
                    rate_type=duty["rate_type"],
                    specific_amount=duty["specific_amount"],
                    specific_unit=duty["specific_unit"],
                    basis=DutyBasis.CIF,
                    sequence=10,
                    legal_reference="SARS Schedule 1 Part 1",
                ))

            elif code in _PREF_MAP:
                pref_name, agreement = _PREF_MAP[code]
                if duty["rate_pct"] is not None and duty["rate_pct"] < (dd_rate or 999):
                    advantages.append(FiscalAdvantage(
                        country_iso3=country,
                        national_code=code_nat,
                        tax_code="DD",
                        reduced_rate_pct=duty["rate_pct"] if duty["rate_pct"] is not None else 0.0,
                        condition_fr=f"Taux préférentiel — {pref_name}",
                        condition_en=pref_name,
                        agreement=agreement,
                        required_document="Certificat d'origine",
                    ))

        # TVA nationale (ajout systématique par membre)
        measures.append(Measure(
            country_iso3=country,
            national_code=code_nat,
            measure_type=MeasureType.VAT,
            code=vat_code,
            name_fr=f"{vat_name} ({country})",
            name_en=vat_name,
            rate_pct=vat_rate,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF_PLUS_INCLUDED,
            basis_includes=["DD"],
            sequence=90,
            observation="Taux national standard — à confirmer vs loi de finances en vigueur",
        ))

        dd_val  = dd_rate or 0.0
        total_npf = dd_val  # TVA non incluse dans NPF SACU (calculée séparément)

        lines.append(CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=[],
            fiscal_advantages=advantages,
            total_npf_pct=round(total_npf, 4),
            total_zlecaf_pct=0.0,
            savings_pct=0.0,
            source_file=f"backend/data/crawled/{country}_tariffs.json",
            last_updated=now,
            schema_version=SCHEMA_VERSION,
            provenance=prov,
        ))

    out = output_path or (OUTPUT_DIR / f"{country}_canonical.jsonl")
    count = write_jsonl(lines, out)
    print(f"[SACU/{country}] {count} lignes → {out}")
    return count


def convert_all(output_dir: Optional[Path] = None) -> dict[str, int]:
    results = {}
    for country in SACU_MEMBERS:
        out = (output_dir / f"{country}_canonical.jsonl") if output_dir else None
        results[country] = convert_country(country, out)
    return results


if __name__ == "__main__":
    import sys as _sys
    arg = _sys.argv[1] if len(_sys.argv) > 1 else "ALL"
    if arg == "ALL":
        convert_all()
    else:
        convert_country(arg.upper())
