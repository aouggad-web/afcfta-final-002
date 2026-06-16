"""
Adaptateur tarifaire — Maurice (MUS)
=====================================
Source officielle : Mauritius Revenue Authority (MRA)
                   Integrated Tariff Schedule HS2022 (as at 01 April 2026)
URL               : https://www.mra.mu/download/TariffInfo010426.pdf
Format d'entrée   : raw_crawl JSON (positions[], champs plats dd_rate / excise_rate /
                    excise_rate_raw / vat_rate / vat_rate_raw)
Nomenclature      : 8 chiffres HS → HS6 = 6 premiers chiffres

Structure des taxes (séquence d'application officielle MUS) :
  10  D.D     — General (MFN) Duty              : % du CIF
  20  EXCISE  — Excise Duty                      : % du CIF (si > 0 ; tabac jusqu'à 230 %)
  30  T.V.A   — Value Added Tax (VAT 15 %)       : % de (CIF + DD + Excise) — si vat_rate > 0

  Nota : 1 415 positions sont exonérées de VAT (vat_rate = 0 % — biens essentiels).
         Taxe touristique/environnementale non modélisée (non présente dans ce dataset).

Provenance : VERIFIED / A
  → Les taux DD/Excise/VAT proviennent directement du crawl MRA (PDF officiel avril 2026).

Usage :
    python engine/adapters/mus_tariff_adapter.py \\
        /path/to/mus_raw.json engine/output/
    python engine/adapters/mus_tariff_adapter.py \\
        /path/to/mus_raw.json engine/output/ --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, date, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, Measure, Provenance,
    MeasureType, DataStatus, ReliabilityGrade, RateType, DutyBasis,
    SCHEMA_VERSION,
)

_SOURCE_NAME    = "MRA Integrated Tariff Schedule HS2022 (Maurice)"
_SOURCE_URL     = "https://www.mra.mu/download/TariffInfo010426.pdf"
_SOURCE_DOCUMENT = (
    "Mauritius Revenue Authority — Integrated Tariff Schedule HS2022 "
    "as at 01 April 2026 — https://www.mra.mu/download/TariffInfo010426.pdf"
)
_VERSION_DATE   = date(2026, 4, 1)


def _build_provenance(crawled_at: str) -> Provenance:
    return Provenance(
        data_status=DataStatus.VERIFIED,
        reliability=ReliabilityGrade.A,
        source_name=_SOURCE_NAME,
        source_url=_SOURCE_URL,
        source_document=_SOURCE_DOCUMENT,
        version_date=_VERSION_DATE,
        retrieved_at=datetime.fromisoformat(
            crawled_at.replace("Z", "+00:00")),
        notes=(
            "Crawl du PDF officiel MRA Integrated Tariff HS2022 (01/04/2026). "
            "Taux de droit général (NPF). Excise très élevé sur tabac/alcool (jusqu'à 230 %). "
            "1 415 positions exonérées de VAT (biens essentiels). "
            "Taxe de protection de l'environnement (EPL) non incluse."
        ),
    )


def _build_measures(pos: dict) -> list[Measure]:
    dd     = float(pos.get("dd_rate") or 0)
    excise = float(pos.get("excise_rate") or 0)
    vat    = float(pos.get("vat_rate") or 0)
    code   = pos["code"].strip()
    measures: list[Measure] = []

    # ── 10 : D.D — General (MFN) Duty ──────────────────────────────────────
    measures.append(Measure(
        country_iso3="MUS",
        national_code=code,
        measure_type=MeasureType.CUSTOMS_DUTY,
        code="D.D",
        name_fr="Droit de Douane général (NPF)",
        name_en="General (MFN) Customs Duty",
        rate_pct=dd,
        rate_type=RateType.EXEMPT if dd == 0 else RateType.AD_VALOREM,
        basis=DutyBasis.CIF,
        sequence=10,
        is_zlecaf_applicable=True,
        observation=f"MRA Tariff Schedule HS2022 — code {code}",
    ))

    # ── 20 : EXCISE — Excise Duty (si applicable) ──────────────────────────
    if excise > 0:
        # L'excise très élevée (>100 %) concerne le tabac (ch. 24) et certains
        # alcools. Le raw_rate est % ad valorem dans ce dataset (pas de spécifique).
        measures.append(Measure(
            country_iso3="MUS",
            national_code=code,
            measure_type=MeasureType.EXCISE,
            code="EXCISE",
            name_fr="Excise Duty",
            name_en="Excise Duty",
            rate_pct=excise,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF,
            sequence=20,
            is_zlecaf_applicable=False,
            observation=(
                f"Excise {excise:.0f}% — MRA Tariff Schedule HS2022"
                + (" [taux élevé tabac/alcool]" if excise >= 100 else "")
            ),
        ))

    # ── 30 : T.V.A — VAT 15 % (ou 0 % si exonéré) ─────────────────────────
    # Assiette : CIF + DD + Excise
    vat_includes = ["D.D"]
    if excise > 0:
        vat_includes.append("EXCISE")

    if vat > 0:
        measures.append(Measure(
            country_iso3="MUS",
            national_code=code,
            measure_type=MeasureType.VAT,
            code="T.V.A",
            name_fr="Taxe sur la Valeur Ajoutée (VAT) — 15 %",
            name_en="Value Added Tax (VAT)",
            rate_pct=vat,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF_PLUS_INCLUDED,
            basis_includes=vat_includes,
            sequence=30,
            is_zlecaf_applicable=False,
            legal_reference="Value Added Tax Act 1998 (as amended)",
            observation="VAT 15 % — assiette : CIF + DD + Excise",
        ))
    # Si vat == 0 : position exonérée — on n'émet pas de mesure VAT
    # (l'absence de mesure VAT dans la liste est déjà explicite)

    return measures


def _convert_position(pos: dict, prov: Provenance) -> CanonicalTariffLine:
    code   = pos["code"].strip()
    hs6    = code[:6]
    dd     = float(pos.get("dd_rate") or 0)
    excise = float(pos.get("excise_rate") or 0)
    vat    = float(pos.get("vat_rate") or 0)

    measures = _build_measures(pos)

    # total_npf indicatif = DD + Excise + VAT (somme des taux face à la valeur CIF)
    total_npf = round(dd + excise + vat, 4)
    total_zlecaf = round(excise + vat, 4)  # DD = 0 sous ZLECAf (hypothèse demantèlement)

    commodity = CommodityCode(
        country_iso3="MUS",
        national_code=code,
        hs6=hs6,
        digits=len(code),
        description_fr=pos.get("description_en", ""),
        description_en=pos.get("description_en"),
        chapter=pos.get("chapter", code[:2]),
        unit=pos.get("unit"),
        hs_version="HS2022",
        sensitivity=(
            "sensible" if dd >= 30 or excise >= 100 else
            "élevé"   if dd >= 15 or excise >= 30   else
            "normal"
        ),
    )

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        total_npf_pct=total_npf,
        total_zlecaf_pct=total_zlecaf,
        savings_pct=round(dd, 4),
        last_updated=datetime.now(timezone.utc),
        schema_version=SCHEMA_VERSION,
        provenance=prov,
    )


# ── API Python ─────────────────────────────────────────────────────────────────

def convert(data: dict) -> list[CanonicalTariffLine]:
    """Convertit un dict raw_crawl MUS en liste de CanonicalTariffLine."""
    prov = _build_provenance(
        data.get("crawled_at", datetime.now(timezone.utc).isoformat()))
    return [_convert_position(p, prov) for p in data.get("positions", [])]


def convert_file(json_path: str | Path) -> list[CanonicalTariffLine]:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return convert(data)


# ── CLI ────────────────────────────────────────────────────────────────────────

def process_file(json_path: str | Path, output_dir: str | Path,
                 dry_run: bool = False) -> dict:
    """
    Ingère mus_raw.json et écrit MUS_canonical.jsonl dans output_dir.
    Retourne un dict résumé.
    """
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    records = convert(data)

    chapters_seen: set[str] = set()
    dd_dist:  dict[float, int] = {}
    vat_dist: dict[float, int] = {}
    excise_hi: int = 0
    for r in records:
        chapters_seen.add(r.commodity.chapter)
        dd = next((m.rate_pct for m in r.measures if m.code == "D.D"), 0) or 0
        dd_dist[dd] = dd_dist.get(dd, 0) + 1
        vat = next((m.rate_pct for m in r.measures if m.code == "T.V.A"), 0) or 0
        vat_dist[vat] = vat_dist.get(vat, 0) + 1
        exc = next((m.rate_pct for m in r.measures if m.code == "EXCISE"), 0) or 0
        if exc >= 100:
            excise_hi += 1

    print(f"  MUS : {len(records):,} positions / "
          f"{len(chapters_seen)} chapitres / "
          f"VERIFIED/A")
    print(f"    DD bands  : {dict(sorted(dd_dist.items()))}")
    print(f"    VAT bands : {dict(sorted(vat_dist.items()))}")
    print(f"    Excise ≥100 % (tabac/alcool) : {excise_hi} positions")

    if dry_run:
        print("  (--dry-run) Fichier NON écrit.")
        return {"written": 0, "total": len(records)}

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "MUS_canonical.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")
    print(f"  → {out_path}")
    return {"written": len(records), "total": len(records), "output": str(out_path)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input",  help="Chemin vers mus_raw.json")
    ap.add_argument("output", help="Répertoire de sortie")
    ap.add_argument("--dry-run", action="store_true",
                    help="Afficher les stats sans écrire le fichier")
    args = ap.parse_args()
    process_file(args.input, args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
