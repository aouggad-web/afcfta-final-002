"""
Convertisseur CEMAC — portails nationaux + TEC CEMAC
=====================================================

5 membres avec données crawlées réelles :
  CMR, CAF, COG, GAB, TCD

Format source : positions (HS8), taxes dict {code: float},
taxes_detail list[{tax_code, tax_name, rate, rate_type, base}].

Séquence CEMAC :
  10  DD    Droit de Douane (TEC)
  20  TCI   Taxe Communautaire d'Intégration (1%)
  25+ taxes nationales spécifiques (RI, CIA, TS, OHADA…)
  90  TVA   (avec CAC pour CMR)

Les libellés officiels (tax_name) sont préservés intégralement dans name_fr.
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
    OUTPUT_DIR, classify_measure, clean_hs, digits_from_code,
    hs6_from_code, load_crawled, write_jsonl,
)

CEMAC_CRAWLED = ["CMR", "CAF", "COG", "GAB", "TCD"]

_SOURCES: dict[str, tuple[str, str]] = {
    "CMR": ("CEMAC Tarif des Douanes (DGD Cameroun)",  "https://www.douanescameroun.com"),
    "CAF": ("finances.gouv.cf + TEC CEMAC",            "https://finances.gouv.cf"),
    "COG": ("douanes.gouv.cg + TEC CEMAC",             "https://douanes.gouv.cg"),
    "GAB": ("douanes.ga + TEC CEMAC",                  "https://douanes.ga"),
    "TCD": ("finances.gouv.td + TEC CEMAC",            "https://finances.gouv.td"),
}

_CEMAC_TAX_CONFIG: dict[str, tuple[int, MeasureType, DutyBasis]] = {
    "DD":    (10, MeasureType.CUSTOMS_DUTY, DutyBasis.CIF),
    "TCI":   (20, MeasureType.LEVY,         DutyBasis.CIF),
    "RI":    (25, MeasureType.OTHER_TAX,    DutyBasis.CIF),   # Redevance Informatique (CMR)
    "CIA":   (25, MeasureType.LEVY,         DutyBasis.CIF),   # Contribution UA (GAB)
    "TS":    (25, MeasureType.OTHER_TAX,    DutyBasis.CIF),   # Taxe Statistique (TCD/COG)
    "OHADA": (28, MeasureType.LEVY,         DutyBasis.CIF),   # Prélèvement OHADA (COG)
    "RS":    (26, MeasureType.LEVY,         DutyBasis.CIF),   # Redevance Stat (CAF)
    "PUA":   (27, MeasureType.LEVY,         DutyBasis.CIF),   # Prélèvement UA
    "TVA":   (90, MeasureType.VAT,          DutyBasis.CIF_PLUS_INCLUDED),
}


def _provenance(country: str) -> Provenance:
    src, url = _SOURCES.get(country, ("TEC CEMAC", ""))
    return Provenance(
        data_status=DataStatus.PARTIAL,
        reliability=ReliabilityGrade.B,
        source_name=src,
        source_url=url,
        source_document="TEC CEMAC 2022 — 4 bandes : 5/10/20/30%",
        version_date=date(2022, 1, 1),
        notes=(
            f"Crawl {src}. TEC commun CEMAC officiel. "
            "Taxes nationales à confirmer contre LF en vigueur."
        ),
    )


def _build_measures(taxes_detail: list, code_nat: str, country: str) -> list[Measure]:
    measures = []
    for tax in taxes_detail:
        tax_code = str(tax.get("tax_code") or "").strip()
        tax_name = str(tax.get("tax_name") or tax_code).strip()
        rate     = tax.get("rate")
        rate_type_src = str(tax.get("rate_type") or "ad_valorem").lower()
        base_src = str(tax.get("base") or "CIF").strip()

        config = _CEMAC_TAX_CONFIG.get(tax_code.upper())
        if config:
            seq, mtype, basis = config
        else:
            seq, mtype, basis = 50, classify_measure(tax_code, tax_name), DutyBasis.CIF

        rate_type = RateType.AD_VALOREM
        if (rate or 0) == 0:
            rate_type = RateType.EXEMPT
        elif rate_type_src in ("specific", "spécifique"):
            rate_type = RateType.SPECIFIC

        basis_inc = []
        if mtype == MeasureType.VAT and "+" in base_src:
            parts = [p.strip() for p in base_src.split("+")]
            basis_inc = [p for p in parts if p and p != "CIF"]

        measures.append(Measure(
            country_iso3=country,
            national_code=code_nat,
            measure_type=mtype,
            code=tax_code,
            name_fr=tax_name,
            rate_pct=float(rate) if rate is not None else None,
            rate_type=rate_type,
            basis=basis,
            basis_includes=basis_inc,
            basis_note=base_src if "plafond" in base_src.lower() else None,
            sequence=seq,
        ))

    measures.sort(key=lambda m: m.sequence)
    return measures


def convert_country(country: str, output_path: Optional[Path] = None) -> int:
    if country not in CEMAC_CRAWLED:
        raise ValueError(f"{country} : pas de crawl CEMAC disponible")

    prov = _provenance(country)
    data = load_crawled(country)
    positions = data.get("positions", [])
    now  = datetime.utcnow()

    lines: list[CanonicalTariffLine] = []

    for pos in positions:
        code_raw = str(pos.get("code_clean") or pos.get("code") or "").strip()
        code_nat = clean_hs(code_raw)
        hs6      = hs6_from_code(code_nat)
        desc     = (pos.get("designation") or "").strip()
        chapter  = (pos.get("chapter") or hs6[:2]).zfill(2)

        commodity = CommodityCode(
            country_iso3=country,
            national_code=code_nat,
            hs6=hs6,
            digits=digits_from_code(code_nat),
            description_fr=desc,
            description_official_fr=desc,
            chapter=chapter,
            hs_version="HS2022",
        )

        taxes_detail = pos.get("taxes_detail") or []
        measures = _build_measures(taxes_detail, code_nat, country)

        total_npf = sum(m.rate_pct for m in measures if m.rate_pct is not None)

        lines.append(CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=[],
            fiscal_advantages=[],
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
    print(f"[CEMAC/{country}] {count} lignes → {out}")
    return count


def convert_all(output_dir: Optional[Path] = None) -> dict[str, int]:
    results = {}
    for country in CEMAC_CRAWLED:
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
