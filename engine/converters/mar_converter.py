"""
Convertisseur Maroc — douane.gov.ma/adil
=========================================

Format source : sub_positions (HS10), taxes dict {libellé_complet: "X %"},
formalities list[str].

Les libellés des taxes ("Droit d'Importation (DI)", "Taxe Parafiscale…", etc.)
sont préservés intégralement dans name_fr.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from converters.base import (
    CRAWLED_DIR,
    OUTPUT_DIR,
    classify_measure,
    classify_requirement,
    clean_hs,
    digits_from_code,
    extract_authority,
    hs6_from_code,
    load_crawled,
    parse_duty_value,
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
    Requirement,
)

COUNTRY = "MAR"
SOURCE_NAME = "Administration des Douanes et Impôts Indirects — Maroc (ADII)"
SOURCE_URL = "https://www.douane.gov.ma/adil"
SOURCE_DOC = "Tarif des Droits d'Importation 2025/2026 — douane.gov.ma/adil"
VERSION_DATE = date(2025, 1, 1)

# Mapping libellé MAR → (code court, séquence, MeasureType)
_MAR_TAX_MAP: list[tuple] = [
    ("Droit d'Importation", "DI", 10, MeasureType.CUSTOMS_DUTY),
    ("Taxe Parafiscale", "TPI", 20, MeasureType.OTHER_TAX),
    ("Taxe Intérieure de Consommation", "TIC", 30, MeasureType.EXCISE),
    ("Taxe sur la Valeur Ajoutée", "TVA", 90, MeasureType.VAT),
    ("Droit Antidumping", "DAD", 15, MeasureType.ANTI_DUMPING),
    ("Mesure de Sauvegarde", "SVG", 15, MeasureType.SAFEGUARD),
    ("Redevance", "RED", 25, MeasureType.LEVY),
    ("Prélèvement", "PRL", 25, MeasureType.LEVY),
]


def _match_tax(libelle: str) -> tuple[str, int, MeasureType]:
    """Retourne (code_court, séquence, type) depuis le libellé officiel MAR."""
    low = libelle.lower()
    for substr, code, seq, mtype in _MAR_TAX_MAP:
        if substr.lower() in low:
            return code, seq, mtype
    return "TAX", 50, classify_measure("", libelle)


_PROVENANCE = Provenance(
    data_status=DataStatus.VERIFIED,
    reliability=ReliabilityGrade.A,
    source_name=SOURCE_NAME,
    source_url=SOURCE_URL,
    source_document=SOURCE_DOC,
    version_date=VERSION_DATE,
    notes="Crawl direct douane.gov.ma/adil — 13 114 sous-positions HS10",
)


def _build_measures(taxes: dict, code_nat: str) -> list[Measure]:
    measures = []
    for libelle, raw_val in taxes.items():
        code_court, seq, mtype = _match_tax(libelle)
        duty = parse_duty_value(str(raw_val))

        basis = DutyBasis.CIF
        if mtype == MeasureType.VAT:
            basis = DutyBasis.CIF_PLUS_INCLUDED

        measures.append(
            Measure(
                country_iso3=COUNTRY,
                national_code=code_nat,
                measure_type=mtype,
                code=code_court,
                name_fr=libelle,  # libellé officiel exact
                rate_pct=duty["rate_pct"],
                rate_type=duty["rate_type"],
                specific_amount=duty["specific_amount"],
                specific_unit=duty["specific_unit"],
                basis=basis,
                sequence=seq,
            )
        )
    return measures


def _build_requirements(formalities: list, code_nat: str) -> list[Requirement]:
    reqs = []
    seen = set()
    idx = 0
    for item in formalities:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        # Ignorer les lignes-titre sans contenu actionnable
        if text.lower() in ("documents et normes à l'import.", "documents et normes à l'export."):
            continue
        req_type = classify_requirement(text)
        authority, auth_code = extract_authority(text)
        idx += 1
        reqs.append(
            Requirement(
                country_iso3=COUNTRY,
                national_code=code_nat,
                requirement_type=req_type,
                code=f"MAR_{idx:03d}",
                document_fr=text,  # libellé officiel exact
                is_mandatory=True,
                issuing_authority=authority,
                issuing_authority_code=auth_code,
                applies_to="IMPORT",
            )
        )
    return reqs


def convert_position(pos: dict, now: datetime) -> CanonicalTariffLine:
    code_raw = str(pos.get("code") or "").strip()
    code_nat = clean_hs(code_raw)
    hs6 = hs6_from_code(code_nat)
    desc = (pos.get("designation") or "").strip()
    chapter = (pos.get("chapter") or hs6[:2]).zfill(2)

    commodity = CommodityCode(
        country_iso3=COUNTRY,
        national_code=code_nat,
        hs6=hs6,
        digits=digits_from_code(code_nat),
        description_fr=desc,
        description_official_fr=desc,
        chapter=chapter,
        hs_version="HS2022",
    )

    taxes = pos.get("taxes") or {}
    formalities = pos.get("formalities") or []

    measures = _build_measures(taxes, code_nat)
    requirements = _build_requirements(formalities, code_nat)

    ad_val_import = [m for m in measures if m.rate_pct is not None]
    total_npf = sum(m.rate_pct for m in ad_val_import if m.rate_pct)

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        requirements=requirements,
        fiscal_advantages=[],
        total_npf_pct=round(total_npf, 4),
        total_zlecaf_pct=0.0,
        savings_pct=0.0,
        source_file=f"backend/data/crawled/{COUNTRY}_tariffs.json",
        last_updated=now,
        schema_version=SCHEMA_VERSION,
        provenance=_PROVENANCE,
    )


def convert(output_path: Optional[Path] = None) -> int:
    data = load_crawled(COUNTRY)
    positions = data.get("sub_positions", [])
    now = datetime.utcnow()

    lines = [convert_position(p, now) for p in positions]

    out = output_path or (OUTPUT_DIR / f"{COUNTRY}_canonical.jsonl")
    count = write_jsonl(lines, out)
    print(f"[MAR] {count} lignes → {out}")
    return count


if __name__ == "__main__":
    convert()
