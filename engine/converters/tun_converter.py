"""
Convertisseur Tunisie — douane.gov.tn/tarifweb2025
====================================================

Format source : sub_positions (HS11), taxes_import + taxes_export (séparées),
reglementation_import / reglementation_export (formalités codées), preferences.

Toutes les dénominations officielles (tax_name, description réglementation)
sont préservées mot pour mot dans name_fr / document_fr.
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
    FiscalAdvantage,
    Measure,
    MeasureType,
    Provenance,
    RateType,
    ReliabilityGrade,
    Requirement,
    RequirementType,
)

# ------------------------------------------------------------------
# Constantes Tunisie
# ------------------------------------------------------------------

COUNTRY = "TUN"
SOURCE_NAME = "Direction Générale des Douanes — Tunisie (douane.gov.tn)"
SOURCE_URL = "https://www.douane.gov.tn/tarifweb2025"
SOURCE_DOC = "Tarif des Douanes 2025 — douane.gov.tn/tarifweb2025"
VERSION_DATE = date(2025, 1, 1)

# Codes de formalités TUN → infos structurées
# Code source numérique (ex: "705") → (RequirementType, autorité)
_REGL_CODES: dict[str, tuple] = {
    "705": (RequirementType.CERTIFICATE, "Direction des Services Vétérinaires", "DSV"),
    "706": (RequirementType.CERTIFICATE, "Direction des Services Vétérinaires", "DSV"),
    "707": (RequirementType.PERMIT, "Direction des Services Vétérinaires", "DSV"),
    "715": (RequirementType.CERTIFICATE, "Direction de la Protection des Végétaux", "DPV"),
    "716": (RequirementType.CERTIFICATE, "Direction de la Protection des Végétaux", "DPV"),
    "720": (RequirementType.AUTHORIZATION, "Ministère du Commerce", "MCII"),
    "725": (RequirementType.LICENSE, "Ministère du Commerce", "MCII"),
    "730": (RequirementType.INSPECTION, "Institut National de la Normalisation", "INNORPI"),
    "740": (RequirementType.CERTIFICATE, "Direction Générale des Douanes", "DGD"),
    "745": (RequirementType.AUTHORIZATION, "Ministère de l'Environnement", "ANPE"),
    "750": (RequirementType.PERMIT, "Ministère de l'Environnement — CITES", "CITES"),
    "760": (RequirementType.AUTHORIZATION, "Ministère de la Santé Publique", "MSP"),
    "765": (RequirementType.CERTIFICATE, "Ministère de la Santé Publique", "MSP"),
    "770": (RequirementType.LICENSE, "Agence Nationale de Contrôle Sanitaire", "ANCSEP"),
}

# Codes internes TUN → MeasureType forcé
_TUN_TAX_TYPE: dict[str, MeasureType] = {
    "DDDROIT": MeasureType.CUSTOMS_DUTY,
    "DD": MeasureType.CUSTOMS_DUTY,
    "TVA/APTAXE": MeasureType.VAT,
    "TVA": MeasureType.VAT,
    "RPD/IMPORREDEV": MeasureType.OTHER_TAX,
    "RPD": MeasureType.OTHER_TAX,
    "D": MeasureType.OTHER_TAX,  # droit sanitaire vétérinaire spécifique
    "DSANIT": MeasureType.OTHER_TAX,
    "TXTCE": MeasureType.LEVY,
    "PCC": MeasureType.LEVY,
    "DRFTF": MeasureType.OTHER_TAX,
}

# Séquence d'application par code
_SEQ: dict[str, int] = {
    "DDDROIT": 10,
    "DD": 10,
    "D": 20,
    "RPD/IMPORREDEV": 30,
    "RPD": 30,
    "TXTCE": 35,
    "PCC": 36,
    "DRFTF": 40,
    "TVA/APTAXE": 90,
    "TVA": 90,
}

_PROVENANCE = Provenance(
    data_status=DataStatus.VERIFIED,
    reliability=ReliabilityGrade.A,
    source_name=SOURCE_NAME,
    source_url=SOURCE_URL,
    source_document=SOURCE_DOC,
    version_date=VERSION_DATE,
    notes="Crawl direct du portail douane.gov.tn/tarifweb2025 — HS11, import + export",
)


def _build_measure(tax: dict, country: str, code_nat: str, applies_to: str = "IMPORT") -> Measure:
    """Construit une Measure depuis un élément taxes_import/taxes_export TUN."""
    tax_code = (tax.get("code") or "").strip()
    tax_name = (tax.get("name") or tax_code).strip()
    raw_val = (tax.get("raw_value") or "").strip()
    rate_pct = tax.get("rate_pct")
    specific_val = (tax.get("specific_value") or "").strip()
    assiette = (tax.get("assiette") or "").strip()

    mtype = _TUN_TAX_TYPE.get(tax_code) or classify_measure(tax_code, tax_name)
    seq = _SEQ.get(tax_code, 50)

    # Analyse du taux (peut être spécifique ex: "0.100 dinars")
    if specific_val and specific_val != "0":
        duty = parse_duty_value(specific_val, rate_hint=rate_pct)
    else:
        duty = parse_duty_value(raw_val, rate_hint=rate_pct)

    # Assiette
    basis = DutyBasis.CIF
    basis_note = assiette if assiette else None
    if "SOMME" in assiette.upper() or "+" in assiette:
        basis = DutyBasis.CIF_PLUS_INCLUDED
    elif "QUANTIT" in assiette.upper() or "QCS" in assiette.upper():
        basis = DutyBasis.QUANTITY

    obs = None
    if applies_to == "EXPORT":
        obs = "Taxe/droit à l'exportation"

    return Measure(
        country_iso3=country,
        national_code=code_nat,
        measure_type=mtype,
        code=tax_code,
        name_fr=tax_name,
        rate_pct=duty["rate_pct"],
        rate_type=duty["rate_type"],
        specific_amount=duty["specific_amount"],
        specific_unit=duty["specific_unit"],
        basis=basis,
        basis_note=basis_note,
        sequence=seq + (100 if applies_to == "EXPORT" else 0),
        observation=obs,
    )


def _build_requirement(
    regl: dict, country: str, code_nat: str, applies_to: str = "IMPORT"
) -> Requirement:
    """Construit une Requirement depuis un élément reglementation TUN."""
    code = str(regl.get("code") or "").strip()
    desc = (regl.get("description") or "").strip()

    known = _REGL_CODES.get(code)
    if known:
        req_type, authority, auth_code = known
    else:
        req_type = classify_requirement(desc)
        authority, auth_code = extract_authority(desc)

    return Requirement(
        country_iso3=country,
        national_code=code_nat,
        requirement_type=req_type,
        code=code,
        document_fr=desc,
        is_mandatory=True,
        issuing_authority=authority,
        issuing_authority_code=auth_code,
        applies_to=applies_to,
    )


def _build_fiscal_advantage(
    pref: dict, country: str, code_nat: str, tax_code: str = "DD"
) -> Optional[FiscalAdvantage]:
    """Construit un FiscalAdvantage depuis une préférence TUN."""
    country_name = (pref.get("country_name") or "").strip()
    rate_raw = (pref.get("rate") or "").strip()
    if not country_name or not rate_raw:
        return None
    duty = parse_duty_value(rate_raw)
    if duty["rate_pct"] is None:
        return None
    return FiscalAdvantage(
        country_iso3=country,
        national_code=code_nat,
        tax_code=tax_code,
        reduced_rate_pct=duty["rate_pct"],
        condition_fr=f"Taux préférentiel — pays partenaire : {country_name}",
        agreement=f"Accord Tunisie-{country_name}",
        required_document="Certificat d'origine",
    )


def convert_position(pos: dict, now: datetime) -> CanonicalTariffLine:
    hs_raw = str(pos.get("hs_code") or "").strip()
    code_nat = clean_hs(hs_raw)
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

    measures: list[Measure] = []
    for tax in pos.get("taxes_import") or []:
        raw_val = (tax.get("raw_value") or "").strip()
        rate = tax.get("rate_pct")
        # Ne pas omettre les taxes à 0 — elles font partie du tarif officiel
        measures.append(_build_measure(tax, COUNTRY, code_nat, "IMPORT"))

    for tax in pos.get("taxes_export") or []:
        measures.append(_build_measure(tax, COUNTRY, code_nat, "EXPORT"))

    requirements: list[Requirement] = []
    for regl in pos.get("reglementation_import") or []:
        requirements.append(_build_requirement(regl, COUNTRY, code_nat, "IMPORT"))
    for regl in pos.get("reglementation_export") or []:
        requirements.append(_build_requirement(regl, COUNTRY, code_nat, "EXPORT"))

    advantages: list[FiscalAdvantage] = []
    for pref in pos.get("preferences") or []:
        fa = _build_fiscal_advantage(pref, COUNTRY, code_nat)
        if fa:
            advantages.append(fa)

    # Total indicatif NPF (import uniquement, ad valorem)
    import_ad_val = [m for m in measures if m.rate_pct is not None and m.sequence < 100]
    total_npf = sum(m.rate_pct for m in import_ad_val if m.rate_pct)

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        requirements=requirements,
        fiscal_advantages=advantages,
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
    print(f"[TUN] {count} lignes → {out}")
    return count


if __name__ == "__main__":
    convert()
