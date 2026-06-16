"""
Adaptateur tarifaire — Éthiopie (ETH)
======================================
Source officielle : Ethiopian Customs Commission (ECC)
URL               : https://customs.erca.gov.et/trade/customs-division/tariff
Format d'entrée   : raw_crawl JSON (positions[], champs plats dd_rate / excise_rate /
                    vat_rate / withholding_rate / surtax_rate)
Nomenclature      : 11 chiffres HS → HS6 = 6 premiers chiffres

Structure des taxes (séquence d'application officielle ETH) :
  10  D.D   — Customs Duty (Droit de Douane)    : % du CIF
  20  ER    — Excise Duty                        : % du CIF (si > 0)
  30  SR    — Surtax                             : 10 % de (CIF + DD + Excise) [systématique]
  40  T.V.A — Value Added Tax                    : 15 % de (CIF + DD + Excise + Surtax)
  50  WHR   — Withholding Tax at Import           : 3 % du CIF [systématique]

Provenance : VERIFIED / A
  → Les taux DD et Excise proviennent directement du crawl ECC officiel.
  → SR (10 %) et VAT (15 %) et WHR (3 %) sont des taux légaux fixes publiés dans
    la réglementation éthiopienne (Proclamation 312/2002, Income Tax Proc. 979/2016).

Usage :
    python engine/adapters/eth_tariff_adapter.py \\
        /path/to/eth_raw.json engine/output/
    python engine/adapters/eth_tariff_adapter.py \\
        /path/to/eth_raw.json engine/output/ --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, Measure, Provenance,
    MeasureType, DataStatus, ReliabilityGrade, RateType, DutyBasis,
    SCHEMA_VERSION,
)

# ── Constantes réglementaires ETH ──────────────────────────────────────────────
_SURTAX_RATE   = 10.0   # Surtax (SR) — Proclamation 312/2002, universelle
_VAT_RATE      = 15.0   # TVA standard — Value Added Tax Proclamation 285/2002
_WHR_RATE      = 3.0    # Withholding Tax at Import — Income Tax Proc. 979/2016

_SOURCE_NAME    = "Ethiopian Customs Commission (ECC) — Tariff Schedule"
_SOURCE_URL     = "https://customs.erca.gov.et/trade/customs-division/tariff"
_SOURCE_DOCUMENT = (
    "Ethiopian Customs Commission — Tariff Schedule officiel "
    "(DR/ER/SR/VAT/WHR) — https://customs.erca.gov.et/trade/customs-division/tariff"
)


def _build_provenance(crawled_at: str) -> Provenance:
    return Provenance(
        data_status=DataStatus.VERIFIED,
        reliability=ReliabilityGrade.A,
        source_name=_SOURCE_NAME,
        source_url=_SOURCE_URL,
        source_document=_SOURCE_DOCUMENT,
        version_date=None,
        retrieved_at=datetime.fromisoformat(
            crawled_at.replace("Z", "+00:00")),
        notes=(
            "Crawl direct depuis le portail douanier ECC officiel. "
            "SR=10% et VAT=15% et WHR=3% sont des taux fixes (non stockés par ligne). "
            "Exonérations spécifiques non modélisées — vérifier auprès de l'ECC."
        ),
    )


def _build_measures(pos: dict) -> list[Measure]:
    dd      = float(pos.get("dd_rate") or 0)
    excise  = float(pos.get("excise_rate") or 0)
    measures: list[Measure] = []

    # ── 10 : D.D — Droit de Douane ─────────────────────────────────────────
    measures.append(Measure(
        country_iso3="ETH",
        national_code=pos["code"],
        measure_type=MeasureType.CUSTOMS_DUTY,
        code="D.D",
        name_fr="Droit de Douane (DD)",
        name_en="Customs Duty",
        rate_pct=dd,
        rate_type=RateType.EXEMPT if dd == 0 else RateType.AD_VALOREM,
        basis=DutyBasis.CIF,
        sequence=10,
        is_zlecaf_applicable=True,
        observation=f"ECC Tariff Schedule — code {pos['code']}",
    ))

    # ── 20 : ER — Excise Duty (si applicable) ──────────────────────────────
    if excise > 0:
        measures.append(Measure(
            country_iso3="ETH",
            national_code=pos["code"],
            measure_type=MeasureType.EXCISE,
            code="ER",
            name_fr="Excise Duty (ER)",
            name_en="Excise Duty",
            rate_pct=excise,
            rate_type=RateType.AD_VALOREM,
            basis=DutyBasis.CIF,
            sequence=20,
            is_zlecaf_applicable=False,
            observation=f"Excise — ECC Tariff Schedule",
        ))

    # ── 30 : SR — Surtax 10 % (CIF + DD + Excise) ─────────────────────────
    sr_includes = ["D.D"]
    if excise > 0:
        sr_includes.append("ER")
    measures.append(Measure(
        country_iso3="ETH",
        national_code=pos["code"],
        measure_type=MeasureType.LEVY,
        code="SR",
        name_fr="Surtax (SR) — 10 % de (CIF + DD + Excise)",
        name_en="Surtax",
        rate_pct=_SURTAX_RATE,
        rate_type=RateType.AD_VALOREM,
        basis=DutyBasis.CIF_PLUS_INCLUDED,
        basis_includes=sr_includes,
        sequence=30,
        is_zlecaf_applicable=False,
        legal_reference="Proclamation 312/2002",
        observation="Surtax universelle 10 % — Proclamation 312/2002",
    ))

    # ── 40 : T.V.A — 15 % (CIF + DD + Excise + Surtax) ───────────────────
    vat_includes = ["D.D", "SR"]
    if excise > 0:
        vat_includes.insert(1, "ER")
    measures.append(Measure(
        country_iso3="ETH",
        national_code=pos["code"],
        measure_type=MeasureType.VAT,
        code="T.V.A",
        name_fr="Taxe sur la Valeur Ajoutée (TVA) — 15 %",
        name_en="Value Added Tax (VAT)",
        rate_pct=_VAT_RATE,
        rate_type=RateType.AD_VALOREM,
        basis=DutyBasis.CIF_PLUS_INCLUDED,
        basis_includes=vat_includes,
        sequence=40,
        is_zlecaf_applicable=False,
        legal_reference="Value Added Tax Proclamation 285/2002",
        observation="TVA 15 % — exonérations spécifiques non modélisées",
    ))

    # ── 50 : WHR — Withholding Tax at Import 3 % (CIF) ────────────────────
    measures.append(Measure(
        country_iso3="ETH",
        national_code=pos["code"],
        measure_type=MeasureType.OTHER_TAX,
        code="WHR",
        name_fr="Retenue à la source (WHR) — 3 % du CIF",
        name_en="Withholding Tax at Import",
        rate_pct=_WHR_RATE,
        rate_type=RateType.AD_VALOREM,
        basis=DutyBasis.CIF,
        sequence=50,
        is_zlecaf_applicable=False,
        legal_reference="Income Tax Proclamation 979/2016",
        observation="Retenue à la source à l'importation — 3 % du CIF",
    ))

    return measures


def _convert_position(pos: dict, prov: Provenance) -> CanonicalTariffLine:
    code   = pos["code"].strip()
    hs6    = code[:6]
    dd     = float(pos.get("dd_rate") or 0)
    excise = float(pos.get("excise_rate") or 0)

    measures = _build_measures(pos)

    # total_npf indicatif = DD + Excise + SR + VAT + WHR (somme simple des taux)
    total_npf = round(dd + excise + _SURTAX_RATE + _VAT_RATE + _WHR_RATE, 4)

    commodity = CommodityCode(
        country_iso3="ETH",
        national_code=code,
        hs6=hs6,
        digits=len(code),
        description_fr=pos.get("description_en", ""),
        description_en=pos.get("description_en"),
        chapter=pos.get("chapter", code[:2]),
        unit=pos.get("unit"),
        hs_version="HS2022",
        sensitivity=(
            "sensible" if dd >= 30 else
            "élevé"   if dd >= 20 else
            "normal"
        ),
    )

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        total_npf_pct=total_npf,
        total_zlecaf_pct=round(excise + _SURTAX_RATE + _VAT_RATE + _WHR_RATE, 4),
        savings_pct=round(dd, 4),
        last_updated=datetime.now(timezone.utc),
        schema_version=SCHEMA_VERSION,
        provenance=prov,
    )


# ── API Python ─────────────────────────────────────────────────────────────────

def convert(data: dict) -> list[CanonicalTariffLine]:
    """Convertit un dict raw_crawl ETH en liste de CanonicalTariffLine."""
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
    Ingère eth_raw.json et écrit ETH_canonical.jsonl dans output_dir.
    Retourne un dict résumé.
    """
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    records = convert(data)

    chapters_seen: set[str] = set()
    dd_dist: dict[float, int] = {}
    for r in records:
        chapters_seen.add(r.commodity.chapter)
        dd = next((m.rate_pct for m in r.measures if m.code == "D.D"), 0) or 0
        dd_dist[dd] = dd_dist.get(dd, 0) + 1

    print(f"  ETH : {len(records):,} positions / "
          f"{len(chapters_seen)} chapitres / "
          f"VERIFIED/A")
    print(f"    DD bands : {dict(sorted(dd_dist.items()))}")

    if dry_run:
        print("  (--dry-run) Fichier NON écrit.")
        return {"written": 0, "total": len(records)}

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ETH_canonical.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")
    print(f"  → {out_path}")
    return {"written": len(records), "total": len(records), "output": str(out_path)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input",  help="Chemin vers eth_raw.json")
    ap.add_argument("output", help="Répertoire de sortie")
    ap.add_argument("--dry-run", action="store_true",
                    help="Afficher les stats sans écrire le fichier")
    args = ap.parse_args()
    process_file(args.input, args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
