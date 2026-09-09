"""
Convertisseur Égypte — customs.gov.eg
======================================

Format source : sub_positions (HS10), taxes dict {DD, TVA},
official_instructions list[str] (codes réglementaires + texte arabe/français).

Les official_instructions contiennent :
  - Lignes "ر XXXX-..." : notes fiscales / règlements tarifaires
  - Lignes "غ XXXX-..." : formalités OBLIGATOIRES (autorisation, permis…)
  - Lignes "ق XXXX-..." : restrictions/prohibitions
  - Lignes ZLECAf (groupe A/B) : taux préférentiels ZLECAf
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from converters.base import (
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
    FiscalAdvantage,
    Measure,
    MeasureType,
    Provenance,
    RateType,
    ReliabilityGrade,
    Requirement,
    RequirementType,
)

COUNTRY = "EGY"
SOURCE_NAME = "Egyptian Customs Authority — مصلحة الجمارك المصرية"
SOURCE_URL = "https://customs.gov.eg/Services/Tarif"
SOURCE_DOC = "Tariff Schedule 2025 — customs.gov.eg/Services/Tarif"
VERSION_DATE = date(2025, 1, 1)

# Séquence fixe pour l'Égypte
_EGY_TAXES: dict[str, tuple[int, MeasureType, DutyBasis]] = {
    "DD": (10, MeasureType.CUSTOMS_DUTY, DutyBasis.CIF),
    "TVA": (90, MeasureType.VAT, DutyBasis.CIF_PLUS_INCLUDED),
}

# Préfixes arabes d'instructions
_PREF_OBLIGATION = "غ"  # formalité obligatoire
_PREF_PROHIBITION = "ق"  # restriction / prohibition
_PREF_REGULATION = "ر"  # note fiscale / réglementation

# ZLECAf dans les instructions
_ZLECAF_A_RE = re.compile(r"مجموعة\s*\[?\s*أ\s*\]?\s*تخفض\s*([\d.]+)\s*%", re.UNICODE)
_ZLECAF_B_RE = re.compile(r"مجموعة\s*\[?\s*ب\s*\]?\s*تخفض\s*([\d.]+)\s*%", re.UNICODE)
_PCT_RE = re.compile(r"([\d.]+)\s*%")

# Autorités égyptiennes reconnues
_EGY_AUTHORITIES = [
    (
        re.compile(r"حجر.*بيطر|وزارة.*زراع|veterinai", re.IGNORECASE),
        ("Direction Centrale de la Quarantaine Vétérinaire", "CAQV"),
    ),
    (re.compile(r"بيئ|environ", re.IGNORECASE), ("Ministère de l'Environnement", "MOE_EGY")),
    (
        re.compile(r"صحة.*نبات|phyto", re.IGNORECASE),
        ("Service de la Quarantaine Phytosanitaire", "PLANT_QUAR"),
    ),
    (re.compile(r"cites|أنواع.*مهددة", re.IGNORECASE), ("Autorité CITES Égypte", "CITES_EGY")),
    (re.compile(r"جمارك|douane|custom", re.IGNORECASE), ("Egyptian Customs Authority", "ECA")),
    (
        re.compile(r"تجارة.*خارجية|commerce.*extérieur", re.IGNORECASE),
        ("Ministère du Commerce Extérieur", "MOFT"),
    ),
    (
        re.compile(r"صناعة|industri", re.IGNORECASE),
        ("Ministère de l'Industrie et du Commerce", "MOIC"),
    ),
    (re.compile(r"صحة\b|santé\b|health\b", re.IGNORECASE), ("Ministère de la Santé", "MOH_EGY")),
]


def _authority_egy(text: str) -> tuple[Optional[str], Optional[str]]:
    for pat, (name, code) in _EGY_AUTHORITIES:
        if pat.search(text):
            return name, code
    auth, code = extract_authority(text)
    return auth, code


_PROVENANCE = Provenance(
    data_status=DataStatus.VERIFIED,
    reliability=ReliabilityGrade.A,
    source_name=SOURCE_NAME,
    source_url=SOURCE_URL,
    source_document=SOURCE_DOC,
    version_date=VERSION_DATE,
    notes="Crawl direct customs.gov.eg — 8 746 positions HS10, crawlé le 2026-06-13",
)


def _parse_instructions(
    instructions: list[str], code_nat: str, dd_rate: Optional[float]
) -> tuple[list[Requirement], list[FiscalAdvantage]]:
    """
    Analyse les official_instructions égyptiennes :
    - غ → Requirement (formalité obligatoire)
    - ق → Requirement (restriction/prohibition à l'exportation ou à l'importation)
    - ZLECAf → FiscalAdvantage
    """
    requirements: list[Requirement] = []
    advantages: list[FiscalAdvantage] = []
    req_idx = 0

    for instr in instructions:
        text = str(instr).strip()
        if not text:
            continue

        # ZLECAf groupe A (100%) ou B (60% de réduction)
        m_a = _ZLECAF_A_RE.search(text)
        if m_a:
            pct_reduction = float(m_a.group(1))
            if dd_rate is not None:
                zlecaf_rate = round(dd_rate * (1 - pct_reduction / 100), 4)
            else:
                zlecaf_rate = 0.0
            advantages.append(
                FiscalAdvantage(
                    country_iso3=COUNTRY,
                    national_code=code_nat,
                    tax_code="DD",
                    reduced_rate_pct=zlecaf_rate,
                    condition_fr=f"Accord ZLECAf — Groupe A (réduction {pct_reduction:.0f}%)",
                    condition_en=f"AfCFTA Schedule A ({pct_reduction:.0f}% reduction)",
                    agreement="ZLECAf",
                    required_document="Certificat d'origine ZLECAf",
                )
            )
            continue

        m_b = _ZLECAF_B_RE.search(text)
        if m_b:
            pct_reduction = float(m_b.group(1))
            if dd_rate is not None:
                zlecaf_rate = round(dd_rate * (1 - pct_reduction / 100), 4)
            else:
                zlecaf_rate = 0.0
            advantages.append(
                FiscalAdvantage(
                    country_iso3=COUNTRY,
                    national_code=code_nat,
                    tax_code="DD",
                    reduced_rate_pct=zlecaf_rate,
                    condition_fr=f"Accord ZLECAf — Groupe B (réduction {pct_reduction:.0f}%)",
                    condition_en=f"AfCFTA Schedule B ({pct_reduction:.0f}% reduction)",
                    agreement="ZLECAf",
                    required_document="Certificat d'origine ZLECAf",
                )
            )
            continue

        # Formalités obligatoires : غ
        first_char = text[:1] if text else ""
        if first_char == _PREF_OBLIGATION:
            req_idx += 1
            parts = text.split("-", 1)
            code_regl = parts[0].strip() if parts else f"EGY_{req_idx:04d}"
            desc = parts[1].strip() if len(parts) > 1 else text
            req_type = classify_requirement(desc)
            auth, auth_code = _authority_egy(desc)
            requirements.append(
                Requirement(
                    country_iso3=COUNTRY,
                    national_code=code_nat,
                    requirement_type=req_type,
                    code=code_regl,
                    document_fr=desc,
                    is_mandatory=True,
                    issuing_authority=auth,
                    issuing_authority_code=auth_code,
                    applies_to="IMPORT",
                    legal_reference=f"Instruction douanière {code_regl}",
                )
            )

        # Restrictions/prohibitions : ق
        elif first_char == _PREF_PROHIBITION:
            req_idx += 1
            parts = text.split("-", 1)
            code_regl = parts[0].strip() if parts else f"EGY_RESTR_{req_idx:04d}"
            desc = parts[1].strip() if len(parts) > 1 else text
            requirements.append(
                Requirement(
                    country_iso3=COUNTRY,
                    national_code=code_nat,
                    requirement_type=RequirementType.LICENSE,
                    code=code_regl,
                    document_fr=desc,
                    is_mandatory=True,
                    applies_to="BOTH",
                    legal_reference=f"Instruction douanière {code_regl}",
                    when_required="Restriction ou prohibition réglementaire",
                )
            )

    return requirements, advantages


def _build_measures(taxes: dict, code_nat: str) -> tuple[list[Measure], Optional[float]]:
    measures = []
    dd_rate: Optional[float] = None

    for tax_code, tax_info in taxes.items():
        if not isinstance(tax_info, dict):
            continue
        name_fr = (tax_info.get("name") or tax_code).strip()
        rate_pct = tax_info.get("rate")
        raw_val = (tax_info.get("raw") or "").strip()

        config = _EGY_TAXES.get(tax_code.upper())
        if config:
            seq, mtype, basis = config
        else:
            seq, mtype, basis = 50, classify_measure(tax_code, name_fr), DutyBasis.CIF

        if rate_pct is None:
            duty = parse_duty_value(raw_val)
            rate_pct = duty["rate_pct"]

        rate_type = RateType.EXEMPT if (rate_pct or 0) == 0.0 else RateType.AD_VALOREM

        if tax_code.upper() == "DD":
            dd_rate = rate_pct

        basis_inc = ["DD"] if tax_code.upper() == "TVA" else []

        measures.append(
            Measure(
                country_iso3=COUNTRY,
                national_code=code_nat,
                measure_type=mtype,
                code=tax_code,
                name_fr=name_fr,
                rate_pct=rate_pct,
                rate_type=rate_type,
                basis=basis,
                basis_includes=basis_inc,
                sequence=seq,
            )
        )

    measures.sort(key=lambda m: m.sequence)
    return measures, dd_rate


def convert_position(pos: dict, now: datetime) -> CanonicalTariffLine:
    code_raw = str(pos.get("hs_code") or "").strip()
    code_nat = clean_hs(code_raw)
    hs6 = hs6_from_code(code_nat)
    chapter = (pos.get("chapter") or hs6[:2]).zfill(2)

    desc = (pos.get("name") or pos.get("description") or "").strip()
    desc_ar = (pos.get("name_ar") or "").strip()

    commodity = CommodityCode(
        country_iso3=COUNTRY,
        national_code=code_nat,
        hs6=hs6,
        digits=digits_from_code(code_nat),
        description_fr=desc,
        description_en=desc if desc else None,
        description_official_fr=desc_ar or desc,
        chapter=chapter,
        hs_version="HS2022",
    )

    taxes = pos.get("taxes") or {}
    instructions = pos.get("official_instructions") or []

    measures, dd_rate = _build_measures(taxes, code_nat)
    requirements, advantages = _parse_instructions(instructions, code_nat, dd_rate)

    # ZLECAf rate pré-calculé si disponible
    zlecaf_rate = pos.get("zlecaf_rate")
    if zlecaf_rate is not None and dd_rate is not None and not advantages:
        advantages.append(
            FiscalAdvantage(
                country_iso3=COUNTRY,
                national_code=code_nat,
                tax_code="DD",
                reduced_rate_pct=float(zlecaf_rate),
                condition_fr="Accord ZLECAf — taux préférentiel officiel",
                agreement="ZLECAf",
                required_document="Certificat d'origine ZLECAf",
            )
        )

    ad_val = [m.rate_pct for m in measures if m.rate_pct is not None]
    total_npf = sum(ad_val)
    total_zlecaf = advantages[0].reduced_rate_pct if advantages else 0.0

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        requirements=requirements,
        fiscal_advantages=advantages,
        total_npf_pct=round(total_npf, 4),
        total_zlecaf_pct=round(total_zlecaf, 4),
        savings_pct=round(total_npf - total_zlecaf, 4),
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
    print(f"[EGY] {count} lignes → {out}")
    return count


if __name__ == "__main__":
    convert()
