"""
Adaptateur générique — fichiers JSON tarifaires multi-pays
===========================================================

Ingère les fichiers {ISO3}_tariffs.json produits par le pipeline de collecte
(format ``national_positions_*``). Compatible avec tous les blocs régionaux
identifiés : TEC CEDEAO, CET EAC, TEC CEMAC, et tarifs nationaux.

Règles de provenance appliquées par couche :
  DD (bandes CET)            → PARTIAL / B  (bandes correctes, erreurs ponctuelles)
  Prélèvements communautaires → PARTIAL / B
  Accises / DA / EXCISE      → PARTIAL / B
  TVA / GST (flat, sans exo) → SYNTHETIC / D  (aucune exonération modélisée)
  zlecaf_rate                → ignoré  (= 10 % × DD, formula, pas de vrai calendrier)

Entrée  : un ou plusieurs fichiers {ISO3}_tariffs.json
Sortie  : un JSONL canonique v4 par pays ({ISO3}_canonical.jsonl)

Usage :
    python engine/adapters/json_tariffs_adapter.py \\
        engine/sources/RWA_tariffs.json \\
        engine/sources/LBR_tariffs.json \\
        engine/sources/CMR_tariffs.json \\
        engine/output/
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, FiscalAdvantage, Measure,
    MeasureType, Provenance, DataStatus, ReliabilityGrade, RateType,
    DutyBasis, SCHEMA_VERSION,
)

# ----------------------------------------------------------------------
# Mapping codes de taxes → types canoniques
# ----------------------------------------------------------------------

_DUTY_CODES = {
    "D.D", "DD", "CUSTOMS", "CUSTOMS_DUTY",
}
_VAT_CODES = {
    "T.V.A", "TVA", "VAT", "IVA", "IGV", "GST",
}
_EXCISE_CODES = {
    "EXCISE", "DA", "EXCISE_DUTY", "DRE", "ACCISE",
}
_LEVY_CODES = {
    "TCI", "TS", "PCC", "PCS", "PUA", "RST", "PC-CEDEAO", "PCS-UEMOA",
    "CISS", "NHIL", "GETFUND", "CRF", "IDL", "RDL",
}

# Taxes que l'on marque SYNTHETIC (flat sans exonérations)
_SYNTHETIC_CODES = _VAT_CODES

_VERIFY_NOTE = ("Taux issu du pipeline de collecte — à confirmer "
                "contre la loi de finances nationale en vigueur")


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
    """Filtre la position tarifaire fictive 000001 (chapitre 00)."""
    return line.get("chapter", "") == "00" or line.get("hs6", "").startswith("00")


def _dedup_taxes(taxes: list[dict]) -> list[dict]:
    """
    Supprime les doublons sémantiques.
    - même code + même taux → doublon exact
    - deux codes du même groupe (ex. GST + T.V.A) → garder le premier
      (LBR liste GST et T.V.A qui désignent le même impôt)
    """
    seen_key: set[tuple] = set()
    seen_group: set[str] = set()
    out = []
    for t in taxes:
        code = t["tax"].upper()
        rate = t.get("rate")
        exact_key = (code, rate)
        # Groupe sémantique (tous les codes VAT → même groupe)
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

def _build_measures(country_iso3: str, hs6: str,
                    taxes: list[dict]) -> list[Measure]:
    taxes = _dedup_taxes(taxes)
    measures: list[Measure] = []
    seq = 10
    for t in taxes:
        code = t["tax"]
        rate = float(t.get("rate") or 0)
        basis = _map_basis(t.get("base", "CIF"))
        mtype = _map_type(code)
        is_synth = code.upper() in {c.upper() for c in _SYNTHETIC_CODES}

        # Upstream codes pour l'assiette TVA (CIF_PLUS_INCLUDED)
        basis_includes: list[str] = []
        if basis == DutyBasis.CIF_PLUS_INCLUDED:
            basis_includes = [m.code for m in measures
                              if m.basis in (DutyBasis.CIF,
                                             DutyBasis.CIF_PLUS_INCLUDED)]

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
            observation=(
                (_VERIFY_NOTE + " ; TVA plate (exonérations non modélisées)")
                if is_synth else _VERIFY_NOTE
            ),
        )
        measures.append(m)
        seq += 10

    return measures


def _build_advantages(country_iso3: str, hs6: str,
                      raw_adv: list[dict]) -> list[FiscalAdvantage]:
    out = []
    for a in raw_adv or []:
        out.append(FiscalAdvantage(
            country_iso3=country_iso3,
            national_code=hs6,
            tax_code=a.get("tax", "D.D"),
            reduced_rate_pct=float(a.get("rate", 0)),
            condition_fr=a.get("condition_fr", ""),
            agreement="ZLECAf",
            required_document="Certificat d'origine ZLECAf",
        ))
    return out


# ----------------------------------------------------------------------
# Provenance
# ----------------------------------------------------------------------

def _provenance(source_name: str, source_url: str,
                generated_at: str) -> Provenance:
    return Provenance(
        data_status=DataStatus.PARTIAL,
        reliability=ReliabilityGrade.B,
        source_name=source_name,
        source_url=source_url,
        version_date=None,
        retrieved_at=generated_at,
        notes=(
            "Données issues du pipeline de collecte tarifaire. Bandes DD du "
            "TEC régional majoritairement correctes. TVA flat sans exonérations "
            "— à recouper avec la loi de finances nationale. Taux ZLECAf "
            "calculés par formule (10 % × DD) — non ingérés comme taux réels."
        ),
    )


# ----------------------------------------------------------------------
# Conversion d'une ligne
# ----------------------------------------------------------------------

def _convert_line(country_iso3: str, line: dict,
                  prov: Provenance) -> CanonicalTariffLine:
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

    measures = _build_measures(
        country_iso3, hs6, line.get("taxes_detail", []))
    advantages = _build_advantages(
        country_iso3, hs6, line.get("fiscal_advantages", []))
    total_npf = sum(m.rate_pct or 0 for m in measures
                    if m.basis == DutyBasis.CIF)

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

def process_file(json_path: str, output_dir: str) -> dict:
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    country = data["country_code"].upper()
    source_name = (f"{data.get('country_name', country)} — "
                   f"{data.get('data_source', 'tariff_pipeline')}")
    prov = _provenance(
        source_name=source_name,
        source_url=data.get("source_url", ""),
        generated_at=data.get("generated_at", datetime.now().isoformat()),
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{country}_canonical.jsonl"

    lines_written = 0
    lines_skipped = 0

    with out_path.open("w", encoding="utf-8") as f:
        for line in data.get("tariff_lines", []):
            if _is_fictitious(line):
                lines_skipped += 1
                continue
            record = _convert_line(country, line, prov)
            f.write(record.model_dump_json() + "\n")
            lines_written += 1

    print(f"  {country}: {lines_written} lignes → {out_path.name} "
          f"({lines_skipped} fictives filtrées)")
    return {
        "country": country,
        "lines_written": lines_written,
        "lines_skipped": lines_skipped,
        "output": str(out_path),
    }


def run(json_paths: list[str], output_dir: str) -> dict:
    results = {}
    for p in json_paths:
        r = process_file(p, output_dir)
        results[r["country"]] = r
    return {"countries": results}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Ingère les JSON tarifaires multi-pays → JSONL canoniques v4")
    ap.add_argument("json_files", nargs="+", help="Fichiers {ISO3}_tariffs.json")
    ap.add_argument("output_dir", help="Répertoire de sortie des JSONL")
    args = ap.parse_args()

    print("Ingestion des fichiers JSON tarifaires...")
    result = run(args.json_files[:-1], args.json_files[-1])
    total = sum(r["lines_written"] for r in result["countries"].values())
    print(f"\nTotal : {len(result['countries'])} pays — {total} lignes")
