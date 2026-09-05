"""
Convertisseur EAC — kra.go.ke (EAC CET 2022)
==============================================

7 membres : KEN, BDI, COD, RWA, SSD, TZA, UGA.
Chaque fichier crawlé contient déjà le CET + les taxes nationales du pays.

Format source : positions (HS8), taxes_detail list[{tax_name, rate, base, is_cet}].

Tous les libellés de taxes (tax_name) sont préservés dans name_fr.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from converters.base import (
    OUTPUT_DIR,
    classify_measure,
    clean_hs,
    digits_from_code,
    hs6_from_code,
    load_crawled,
    write_jsonl,
)
from schemas.canonical_model import (
    SCHEMA_VERSION,
    CanonicalTariffLine,
    CommodityCode,
    DataStatus,
    DutyBasis,
    Measure,
    MeasureType,
    Provenance,
    RateType,
    ReliabilityGrade,
)

EAC_MEMBERS = ["KEN", "BDI", "COD", "RWA", "SSD", "TZA", "UGA"]

SOURCE_NAME = "East African Community — EAC Common External Tariff 2022"
SOURCE_URL = "https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf"
SOURCE_DOC = "EAC CET 2022 (30 June 2022) — kra.go.ke"

# Taxes nationales connues par pays (séquence, code, name, type)
# Les taxes incluses dans le fichier crawlé sont prioritaires
_NATIONAL_CONTEXT: dict[str, str] = {
    "KEN": "VAT 16% — Import Declaration Fee (IDF) 3.5% CIF",
    "BDI": "TVA 18% — Prélèvements EAC standard",
    "COD": "TVA 16% — EAC CET (transition — certains taux peuvent différer)",
    "RWA": "VAT 18% — Rwanda Revenue Authority",
    "SSD": "Non-member VAT regime — Sud-Soudan",
    "TZA": "VAT 18% — Railway Development Levy 1.5%",
    "UGA": "VAT 18% — Withholding Tax sur certains produits",
}

# Déduction du type de mesure depuis le libellé EAC
_EAC_TYPE_HINTS: list[tuple] = [
    ("CET Import Duty", MeasureType.CUSTOMS_DUTY, 10, DutyBasis.CIF),
    ("Droit de Douane", MeasureType.CUSTOMS_DUTY, 10, DutyBasis.CIF),
    ("Import Declaration Fee", MeasureType.LEVY, 20, DutyBasis.CIF),
    ("Railway Development Levy", MeasureType.LEVY, 25, DutyBasis.CIF),
    ("Infrastructure Levy", MeasureType.LEVY, 26, DutyBasis.CIF),
    ("Value Added Tax", MeasureType.VAT, 90, DutyBasis.CIF_PLUS_INCLUDED),
    ("VAT", MeasureType.VAT, 90, DutyBasis.CIF_PLUS_INCLUDED),
    ("Taxe sur la Valeur", MeasureType.VAT, 90, DutyBasis.CIF_PLUS_INCLUDED),
    ("Excise", MeasureType.EXCISE, 30, DutyBasis.CIF),
]


def _match_tax_type(tax_name: str) -> tuple[MeasureType, int, DutyBasis]:
    for hint, mtype, seq, basis in _EAC_TYPE_HINTS:
        if hint.lower() in tax_name.lower():
            return mtype, seq, basis
    return classify_measure("", tax_name), 50, DutyBasis.CIF


def _provenance(country: str) -> Provenance:
    note = _NATIONAL_CONTEXT.get(country, "Taxes nationales à confirmer")
    return Provenance(
        data_status=DataStatus.PARTIAL,
        reliability=ReliabilityGrade.B,
        source_name=SOURCE_NAME,
        source_url=SOURCE_URL,
        source_document=SOURCE_DOC,
        version_date=date(2022, 6, 30),
        notes=f"EAC CET 2022 crawlé depuis kra.go.ke. {note}",
    )


def convert_country(country: str, output_path: Optional[Path] = None) -> int:
    if country not in EAC_MEMBERS:
        raise ValueError(f"{country} n'est pas un membre EAC")

    prov = _provenance(country)
    data = load_crawled(country)
    positions = data.get("positions", [])
    now = datetime.utcnow()

    lines: list[CanonicalTariffLine] = []

    for pos in positions:
        hs_raw = str(pos.get("hs_code") or "").strip()
        code_nat = clean_hs(hs_raw)
        hs6 = hs6_from_code(code_nat)
        desc = (pos.get("designation") or "").strip()
        chapter = (pos.get("chapter") or hs6[:2]).zfill(2)
        unit = pos.get("unit")

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
            sensitivity="sensible" if pos.get("is_sensitive_item") else "normal",
            hs_version="HS2022",
        )

        measures: list[Measure] = []
        for tax in pos.get("taxes_detail") or []:
            tax_name = str(tax.get("tax_name") or "").strip()
            rate = tax.get("rate")
            base = str(tax.get("base") or "CIF").strip()
            is_cet = tax.get("is_cet", False)

            mtype, seq, basis = _match_tax_type(tax_name)
            if is_cet:
                mtype = MeasureType.CUSTOMS_DUTY
                seq = 10

            # Assiette textuelle → enum
            if "+" in base:
                basis = DutyBasis.CIF_PLUS_INCLUDED

            rate_type = RateType.EXEMPT if (rate or 0) == 0 else RateType.AD_VALOREM

            measures.append(
                Measure(
                    country_iso3=country,
                    national_code=code_nat,
                    measure_type=mtype,
                    code="CET" if is_cet else tax_name[:10].replace(" ", "_").upper(),
                    name_fr=tax_name,
                    name_en=tax_name,
                    rate_pct=float(rate) if rate is not None else None,
                    rate_type=rate_type,
                    basis=basis,
                    basis_note=base if basis == DutyBasis.OTHER else None,
                    sequence=seq,
                    observation="Taxe CET communautaire EAC" if is_cet else None,
                )
            )

        measures.sort(key=lambda m: m.sequence)

        dd_rate = (
            next((m.rate_pct for m in measures if m.measure_type == MeasureType.CUSTOMS_DUTY), 0.0)
            or 0.0
        )
        total_npf = pos.get("total_taxes_pct") or sum(
            m.rate_pct for m in measures if m.rate_pct is not None
        )

        lines.append(
            CanonicalTariffLine(
                commodity=commodity,
                measures=measures,
                requirements=[],
                fiscal_advantages=[],
                total_npf_pct=round(float(total_npf), 4),
                total_zlecaf_pct=0.0,
                savings_pct=0.0,
                source_file=f"backend/data/crawled/{country}_tariffs.json",
                last_updated=now,
                schema_version=SCHEMA_VERSION,
                provenance=prov,
            )
        )

    out = output_path or (OUTPUT_DIR / f"{country}_canonical.jsonl")
    count = write_jsonl(lines, out)
    print(f"[EAC/{country}] {count} lignes → {out}")
    return count


def convert_all(output_dir: Optional[Path] = None) -> dict[str, int]:
    results = {}
    for country in EAC_MEMBERS:
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
