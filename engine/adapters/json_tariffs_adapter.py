"""
Adaptateur générique — fichiers JSON tarifaires officiels multi-pays
====================================================================

**POLITIQUE DE DONNÉES : données réelles et vérifiables uniquement.**

Ce module refuse d'ingérer des fichiers générés automatiquement sans
référence à un document officiel vérifiable. Tout fichier sans
``source_document`` (référence à une publication officielle) est
automatiquement classé SYNTHETIC/D et rejeté si le mode strict est actif.

Champs obligatoires dans le JSON source pour obtenir PARTIAL/B ou mieux :
  source_document  : référence précise (titre + URL + date de publication)
  source_url       : URL de téléchargement direct du document
  data_source      : identifiant de la source (ex. "rra_tariff_2024")

Règles de provenance :
  DD avec source_document vérifié  → PARTIAL / B
  Prélèvements communautaires       → PARTIAL / B si documentés
  TVA sans exonérations modélisées  → SYNTHETIC / D (flag dans observation)
  zlecaf_rate calculé par formule   → ignoré (non ingéré)
  Fichier sans source_document      → SYNTHETIC / D (ou REFUS si strict)

Usage :
    # Mode strict (recommandé en production)
    python engine/adapters/json_tariffs_adapter.py \\
        engine/sources/RWA_tariffs.json \\
        engine/output/ --strict

    # Mode permissif (ingestion avec statut SYNTHETIC si pas de source_document)
    python engine/adapters/json_tariffs_adapter.py \\
        engine/sources/RWA_tariffs.json \\
        engine/output/ --allow-synthetic
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

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
)

# ----------------------------------------------------------------------
# Validation de la source
# ----------------------------------------------------------------------


class SourceNotVerifiedException(ValueError):
    """Levée quand un fichier ne contient pas de référence documentaire vérifiable."""


def _validate_source(data: dict, strict: bool = True) -> tuple[DataStatus, ReliabilityGrade, str]:
    """
    Vérifie si le fichier JSON a une provenance vérifiable.

    Retourne (data_status, reliability, warning_message).

    Un fichier est considéré non-vérifiable si :
    - il n'a pas de champ ``source_document``
    - il a été généré aujourd'hui (même jour UTC → pipeline automatique)
    - son ``data_source`` contient 'authentic' auto-déclaré sans document
    """
    source_doc = data.get("source_document", "").strip()
    generated_at = data.get("generated_at", "")
    country = data.get("country_code", "?")

    # Détection fichier généré automatiquement : même jour UTC que maintenant
    auto_generated = False
    if generated_at:
        try:
            gen_date = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).date()
            today = datetime.now(timezone.utc).date()
            if gen_date == today:
                auto_generated = True
        except ValueError:
            pass

    # Un fichier qui se déclare 'authentic' sans source_document est suspect
    auto_claimed = data.get("data_source", "").endswith("_authentic") and not source_doc

    has_real_source = bool(source_doc) and not auto_generated

    if has_real_source:
        return DataStatus.PARTIAL, ReliabilityGrade.B, ""

    # Pas de source vérifiable
    reasons = []
    if auto_generated:
        reasons.append(f"généré automatiquement le {generated_at[:10]}")
    if not source_doc:
        reasons.append("aucun champ 'source_document' (référence officielle manquante)")
    if auto_claimed:
        reasons.append("'data_source' se termine par '_authentic' sans document justificatif")

    msg = (
        f"[{country}] Source non vérifiable : {' ; '.join(reasons)}. "
        f"Ajoutez un champ 'source_document' pointant vers le document officiel "
        f"(JO, gazette, publication de l'administration douanière)."
    )

    if strict:
        raise SourceNotVerifiedException(msg)

    return DataStatus.SYNTHETIC, ReliabilityGrade.D, msg


# ----------------------------------------------------------------------
# Mapping codes de taxes → types canoniques
# ----------------------------------------------------------------------

_DUTY_CODES = {"D.D", "DD", "CUSTOMS", "CUSTOMS_DUTY"}
_VAT_CODES = {"T.V.A", "TVA", "VAT", "IVA", "IGV", "GST"}
_EXCISE_CODES = {"EXCISE", "DA", "EXCISE_DUTY", "DRE", "ACCISE"}
_LEVY_CODES = {
    "TCI",
    "TS",
    "PCC",
    "PCS",
    "PUA",
    "RST",
    "PC-CEDEAO",
    "PCS-UEMOA",
    "CISS",
    "NHIL",
    "GETFUND",
    "CRF",
    "IDL",
    "RDL",
}


def _map_type(code: str) -> MeasureType:
    c = code.upper()
    if c in _DUTY_CODES:
        return MeasureType.CUSTOMS_DUTY
    if c in _VAT_CODES:
        return MeasureType.VAT
    if c in _EXCISE_CODES:
        return MeasureType.EXCISE
    if c in _LEVY_CODES:
        return MeasureType.LEVY
    return MeasureType.OTHER_TAX


def _map_basis(base_str: str) -> DutyBasis:
    b = (base_str or "").upper().replace(" ", "").replace("+", "PLUS")
    if "CIFPLUSDD" in b or "CIFDD" in b or "CIFPLUSD" in b:
        return DutyBasis.CIF_PLUS_INCLUDED
    if "FOB" in b:
        return DutyBasis.FOB
    return DutyBasis.CIF


def _is_fictitious(line: dict) -> bool:
    return line.get("chapter", "") == "00" or line.get("hs6", "").startswith("00")


def _dedup_taxes(taxes: list[dict]) -> list[dict]:
    """
    Supprime les doublons sémantiques.
    Ex. LBR : GST et T.V.A désignent le même impôt → on garde le premier.
    """
    seen_key: set[tuple] = set()
    seen_group: set[str] = set()
    out = []
    for t in taxes:
        code = t["tax"].upper()
        rate = t.get("rate")
        exact_key = (code, rate)
        if code in {c.upper() for c in _VAT_CODES}:
            group = "VAT"
        elif code in {c.upper() for c in _EXCISE_CODES}:
            group = "EXCISE"
        else:
            group = code
        if exact_key in seen_key or group in seen_group:
            continue
        seen_key.add(exact_key)
        seen_group.add(group)
        out.append(t)
    return out


# ----------------------------------------------------------------------
# Construction des mesures
# ----------------------------------------------------------------------


def _build_measures(
    country_iso3: str, hs6: str, taxes: list[dict], is_synthetic: bool = False
) -> list[Measure]:
    taxes = _dedup_taxes(taxes)
    measures: list[Measure] = []
    seq = 10
    for t in taxes:
        code = t["tax"]
        rate = float(t.get("rate") or 0)
        basis = _map_basis(t.get("base", "CIF"))
        mtype = _map_type(code)
        is_vat = code.upper() in {c.upper() for c in _VAT_CODES}

        basis_includes: list[str] = []
        if basis == DutyBasis.CIF_PLUS_INCLUDED:
            basis_includes = [
                m.code for m in measures if m.basis in (DutyBasis.CIF, DutyBasis.CIF_PLUS_INCLUDED)
            ]

        obs_parts = [t.get("observation", code)]
        if is_synthetic:
            obs_parts.append("SYNTHETIC — source non vérifiée")
        if is_vat and not is_synthetic:
            obs_parts.append("TVA plate — exonérations non modélisées, à vérifier")

        m = Measure(
            country_iso3=country_iso3,
            national_code=hs6,
            measure_type=mtype,
            code=code,
            name_fr=t.get("observation", code),
            name_en=t.get("observation", code),
            rate_pct=rate,
            rate_type=RateType.EXEMPT if rate == 0.0 else RateType.AD_VALOREM,
            basis=basis,
            basis_includes=basis_includes if basis_includes else [],
            sequence=seq,
            is_zlecaf_applicable=(mtype == MeasureType.CUSTOMS_DUTY),
            observation=" ; ".join(obs_parts),
        )
        measures.append(m)
        seq += 10

    return measures


def _build_advantages(country_iso3: str, hs6: str, raw_adv: list[dict]) -> list[FiscalAdvantage]:
    out = []
    for a in raw_adv or []:
        out.append(
            FiscalAdvantage(
                country_iso3=country_iso3,
                national_code=hs6,
                tax_code=a.get("tax", "D.D"),
                reduced_rate_pct=float(a.get("rate", 0)),
                condition_fr=a.get("condition_fr", ""),
                agreement="ZLECAf",
                required_document="Certificat d'origine ZLECAf",
            )
        )
    return out


# ----------------------------------------------------------------------
# Provenance
# ----------------------------------------------------------------------


def _build_provenance(
    data: dict, status: DataStatus, reliability: ReliabilityGrade, warning: str
) -> Provenance:
    notes = data.get("notes", [])
    if isinstance(notes, list):
        notes = " | ".join(notes)
    if warning:
        notes = f"AVERTISSEMENT : {warning} | {notes}"

    return Provenance(
        data_status=status,
        reliability=reliability,
        source_name=(
            f"{data.get('country_name', data['country_code'])} — "
            f"{data.get('data_source', 'inconnu')}"
        ),
        source_url=data.get("source_url", ""),
        source_document=data.get("source_document") or None,
        version_date=None,
        retrieved_at=data.get("generated_at", datetime.now().isoformat()),
        notes=notes or None,
    )


# ----------------------------------------------------------------------
# Conversion d'une ligne
# ----------------------------------------------------------------------


def _convert_line(
    country_iso3: str, line: dict, prov: Provenance, is_synthetic: bool
) -> CanonicalTariffLine:
    hs6 = line["hs6"]
    commodity = CommodityCode(
        country_iso3=country_iso3,
        national_code=hs6,
        hs6=hs6,
        digits=6,
        description_fr=line.get("description_fr", ""),
        description_en=line.get("description_en", ""),
        chapter=line.get("chapter", hs6[:2]),
        unit=line.get("unit"),
        hs_version="HS2022",
    )

    measures = _build_measures(country_iso3, hs6, line.get("taxes_detail", []), is_synthetic)
    advantages = _build_advantages(country_iso3, hs6, line.get("fiscal_advantages", []))
    total_npf = sum(
        m.rate_pct or 0 for m in measures if m.basis in (DutyBasis.CIF, DutyBasis.CIF_PLUS_INCLUDED)
    )

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        fiscal_advantages=advantages,
        total_npf_pct=round(total_npf, 4),
        last_updated=datetime.now(),
        schema_version=SCHEMA_VERSION,
        provenance=prov,
    )


# ----------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------


def process_file(json_path: str, output_dir: str, strict: bool = True) -> dict:
    """
    Ingère un fichier JSON tarifaire.

    En mode strict (défaut), lève SourceNotVerifiedException si le fichier
    ne contient pas de référence à un document officiel vérifiable.
    En mode permissif (strict=False), ingère avec statut SYNTHETIC/D.
    """
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    country = data["country_code"].upper()
    if not re.fullmatch(r"[A-Z]{3}", country):
        raise ValueError(
            f"country_code invalide : {data['country_code']!r} " "(code ISO3 attendu, ex. 'RWA')"
        )

    status, reliability, warning = _validate_source(data, strict=strict)
    is_synthetic = status == DataStatus.SYNTHETIC

    if warning:
        print(f"  ⚠  {warning}")

    prov = _build_provenance(data, status, reliability, warning)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{country}_canonical.jsonl"

    lines_written = lines_skipped = 0
    with out_path.open("w", encoding="utf-8") as f:
        for line in data.get("tariff_lines", []):
            if _is_fictitious(line):
                lines_skipped += 1
                continue
            record = _convert_line(country, line, prov, is_synthetic)
            f.write(record.model_dump_json() + "\n")
            lines_written += 1

    status_label = f"{status.value}/{reliability.value}"
    print(f"  {country}: {lines_written} lignes [{status_label}] → {out_path.name}")
    return {
        "country": country,
        "lines_written": lines_written,
        "lines_skipped": lines_skipped,
        "data_status": status.value,
        "output": str(out_path),
    }


def run(json_paths: list[str], output_dir: str, strict: bool = True) -> dict:
    results = {}
    for p in json_paths:
        r = process_file(p, output_dir, strict=strict)
        results[r["country"]] = r
    return {"countries": results}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Ingère les JSON tarifaires officiels → JSONL canoniques v4"
    )
    ap.add_argument(
        "json_files", nargs="+", help="Fichiers {ISO3}_tariffs.json (dernier argument = output_dir)"
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Refuse les fichiers sans source_document (défaut)",
    )
    mode.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Accepte les fichiers non-vérifiés avec statut SYNTHETIC/D",
    )
    args = ap.parse_args()

    strict = not args.allow_synthetic
    print(
        f"Mode : {'STRICT (source_document requis)' if strict else 'PERMISSIF (SYNTHETIC/D si non-vérifié)'}"
    )

    result = run(args.json_files[:-1], args.json_files[-1], strict=strict)
    total = sum(r["lines_written"] for r in result["countries"].values())
    print(f"\nTotal : {len(result['countries'])} pays — {total} lignes")
