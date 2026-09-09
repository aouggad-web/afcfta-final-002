"""
Convertisseur Algérie — conformepro.dz / douane.gov.dz
=======================================================

Format source : sub_positions (HS10), taxes dict {code → {name, rate, raw, source}},
formalities list[str], advantages list[str].

Séquence de calcul DZA :
  10  DD    Droit de Douane        → sur valeur CAF
  20  TCS   Taxe Complémentaire Provisoire de Sauvegarde → sur valeur CAF
  30  PRCT  Prélèvement Complémentaire Temporaire         → sur valeur CAF
  90  TVA   Taxe sur la Valeur Ajoutée → sur CAF + DD + TCS + PRCT

Les libellés officiels (taxes[].name) sont préservés dans name_fr.
Les formalités sont copiées telles quelles dans document_fr.
"""

from __future__ import annotations

import re
import sys
import unicodedata
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
)

COUNTRY = "DZA"
SOURCE_NAME = "Direction Générale des Douanes — Algérie (DGD)"
SOURCE_URL = "https://www.douane.gov.dz"
SOURCE_DOC = "Tarif Intégré National (TIN) 2025 — conformepro.dz/douane.gov.dz"
VERSION_DATE = date(2025, 1, 1)

# Séquence et type par code de taxe DZA
_DZA_TAXES: dict[str, tuple[int, MeasureType, DutyBasis, list]] = {
    # code  → (séquence, type, assiette, basis_includes)
    "DD": (10, MeasureType.CUSTOMS_DUTY, DutyBasis.CIF, []),
    "TCS": (20, MeasureType.OTHER_TAX, DutyBasis.CIF, []),
    "PRCT": (30, MeasureType.OTHER_TAX, DutyBasis.CIF, []),
    "DAPS": (15, MeasureType.SAFEGUARD, DutyBasis.CIF, []),
    "TVA": (90, MeasureType.VAT, DutyBasis.CIF_PLUS_INCLUDED, ["DD", "TCS", "PRCT"]),
}

# Mots-clés préférentiels dans advantages[] → accord
_AGREEMENT_PATTERNS = [
    ("zlecaf", "ZLECAf"),
    ("africaine", "ZLECAf"),
    ("zale", "ZALE (Zone Arabe de Libre-Échange)"),
    ("arabe", "ZALE (Zone Arabe de Libre-Échange)"),
    ("europe", "Accord UE-Algérie"),
    ("union européenne", "Accord UE-Algérie"),
    ("tunisie", "Accord Algérie-Tunisie"),
    ("maroc", "Accord Algérie-Maroc"),
    ("jordanie", "Accord Algérie-Jordanie"),
]

_PROVENANCE = Provenance(
    data_status=DataStatus.VERIFIED,
    reliability=ReliabilityGrade.A,
    source_name=SOURCE_NAME,
    source_url=SOURCE_URL,
    source_document=SOURCE_DOC,
    version_date=VERSION_DATE,
    notes="Crawl direct conformepro.dz (agrégateur officiel douane.gov.dz) — 17 115 sous-positions HS10",
)


def _build_measures(taxes: dict, code_nat: str) -> list[Measure]:
    """Taxes DZA : dict {code → {name, rate, raw, source}}."""
    measures = []
    for tax_code, tax_info in taxes.items():
        if not isinstance(tax_info, dict):
            continue
        name_fr = (tax_info.get("name") or tax_code).strip()
        rate_pct = tax_info.get("rate")
        raw_val = (tax_info.get("raw") or "").strip()

        config = _DZA_TAXES.get(tax_code.upper())
        if config:
            seq, mtype, basis, basis_inc = config
        else:
            seq, mtype, basis, basis_inc = (
                50,
                classify_measure(tax_code, name_fr),
                DutyBasis.CIF,
                [],
            )

        if rate_pct is None:
            duty = parse_duty_value(raw_val)
            rate_pct = duty["rate_pct"]
            rate_type = duty["rate_type"]
            specific_amount = duty["specific_amount"]
            specific_unit = duty["specific_unit"]
        else:
            rate_type = RateType.EXEMPT if rate_pct == 0.0 else RateType.AD_VALOREM
            specific_amount = None
            specific_unit = None

        measures.append(
            Measure(
                country_iso3=COUNTRY,
                national_code=code_nat,
                measure_type=mtype,
                code=tax_code,
                name_fr=name_fr,
                rate_pct=rate_pct,
                rate_type=rate_type,
                specific_amount=specific_amount,
                specific_unit=specific_unit,
                basis=basis,
                basis_includes=basis_inc,
                sequence=seq,
                legal_reference="LF 2025 — Code des Douanes DZA",
            )
        )

    measures.sort(key=lambda m: m.sequence)
    return measures


def _normalize_fap_text(text: str) -> str:
    """Normalise un libellé pour le rapprochement avec la liste officielle FAP
    (insensible aux accents/casse/ponctuation/espaces)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return text


# Liste officielle des codes "FAP" (Formalités Administratives Préalables) de la
# Direction Générale des Douanes algérienne — "LISTE DES DOCUMENTS F,A,P" fournie
# par l'utilisateur (PDF DOCUMENTS_FAP). Rapprochement par libellé exact normalisé
# uniquement : aucun code n'est deviné pour les libellés sans correspondance —
# ceux-ci restent sans code (code="") en attendant une correspondance vérifiée.
_FAP_CODES: dict[str, tuple[str, str]] = {
    # libellé normalisé → (code FAP, base légale / Doccar)
    _normalize_fap_text("Autorisation Spéciale du Ministère de la Défense Nationale"): (
        "100",
        "DE n° 98/96 du 18/06/98 relatif aux armes et munitions.",
    ),
    _normalize_fap_text(
        "Autorisation prealable a l'import et/ou l'export de stupefiants et "
        "substances psychotropes(m.sante)"
    ): (
        "109",
        "Convention des Nations Unies contre le trafic illicite des "
        "stupéfiants et des substances psychotropes.",
    ),
    _normalize_fap_text(
        "Autorisation technique prealable d'importation des produits "
        "phytosanitaires a usage agricole"
    ): (
        "113",
        "DE 99-165 du 20/07/99 modifiant et complétant le DE 95-405 du "
        "02/12/95 relatif au contrôle des produits phytosanitaires à "
        "usage agricole.",
    ),
    _normalize_fap_text(
        "Acquit du service des alcools, titres de regie " "(passavant,acquit-@-caution)."
    ): ("140", "Article 73 du Code des Impôts Indirects."),
    _normalize_fap_text("Visa de controle sanitaire veterinaire (m. agriculture)"): (
        "160",
        "DE 91.452 du 16/11/1991 relatif aux inspections vétérinaires "
        "des postes frontières (en application de la loi 88.08 du "
        "26/01/1988).",
    ),
    _normalize_fap_text("Derogation sanitaire veterinaire (m. agriculture)"): (
        "180",
        "DE 91.452 du 16/11/1991 relatif aux inspections vétérinaires "
        "des postes frontières (en application de la loi 88.08 du "
        "26/01/1988).",
    ),
    _normalize_fap_text("Certificat Phytosanitaire du Pays d'Origine"): (
        "215",
        "DE 93.286 du 23/11/93 relatif à la protection phytosanitaire "
        "aux frontières (en application de la loi 87.17 du "
        "01/08/1987).",
    ),
    _normalize_fap_text(
        "Autorisation d'importation et d'exportation des produits sources de "
        "rayonnements ionisants (asri)"
    ): (
        "242",
        "DP 05-117 du 11/04/2005 relatif aux mesures de protection "
        "contre les rayonnements ionisants.",
    ),
}


def _build_requirements(formalities: list, code_nat: str) -> list[Requirement]:
    reqs = []
    for idx, item in enumerate(formalities, 1):
        text = str(item).strip()
        if not text:
            continue
        req_type = classify_requirement(text)
        authority, auth_code = extract_authority(text)
        fap_match = _FAP_CODES.get(_normalize_fap_text(text))
        code = fap_match[0] if fap_match else ""
        legal_ref = fap_match[1] if fap_match else None
        reqs.append(
            Requirement(
                country_iso3=COUNTRY,
                national_code=code_nat,
                requirement_type=req_type,
                code=code,
                document_fr=text,
                is_mandatory=True,
                issuing_authority=authority,
                issuing_authority_code=auth_code,
                applies_to="IMPORT",
                legal_reference=legal_ref,
            )
        )
    return reqs


def _build_advantages(advantages: list, code_nat: str) -> list[FiscalAdvantage]:
    fas = []
    for item in advantages:
        text = str(item).lower()
        agreement = None
        for keyword, name in _AGREEMENT_PATTERNS:
            if keyword in text:
                agreement = name
                break
        fas.append(
            FiscalAdvantage(
                country_iso3=COUNTRY,
                national_code=code_nat,
                tax_code="DD",
                reduced_rate_pct=0.0,  # taux souvent "exonération" sans % précis
                condition_fr=str(item).strip(),
                agreement=agreement,
                required_document="Certificat d'origine",
            )
        )
    return fas


def convert_position(pos: dict, now: datetime) -> CanonicalTariffLine:
    code_raw = str(pos.get("hs_code") or pos.get("raw_code") or "").strip()
    code_nat = clean_hs(code_raw)
    hs6 = hs6_from_code(code_nat)
    chapter = (pos.get("chapter") or hs6[:2]).zfill(2)

    # Prend le libellé le plus complet disponible
    desc = (pos.get("designation_full") or pos.get("designation") or pos.get("name") or "").strip()

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
    advantages = pos.get("advantages") or []

    measures = _build_measures(taxes, code_nat)
    requirements = _build_requirements(formalities, code_nat)
    fiscal_adv = _build_advantages(advantages, code_nat)

    ad_val = [m.rate_pct for m in measures if m.rate_pct is not None and m.sequence < 90]
    total_npf = sum(ad_val)

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        requirements=requirements,
        fiscal_advantages=fiscal_adv,
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
    print(f"[DZA] {count} lignes → {out}")
    return count


if __name__ == "__main__":
    convert()
