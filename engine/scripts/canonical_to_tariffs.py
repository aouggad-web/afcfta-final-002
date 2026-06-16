"""
Publication des données canoniques v4 vers le format API live
================================================================

Lit `engine/output/{ISO3}_canonical.jsonl` (sortie des convertisseurs
pays-spécifiques, données réelles/dérivées — jamais générées) et écrit
le même document dans les deux emplacements consommés par le backend :
  - `backend/data/{ISO3}_tariffs.json`         (authentic_tariff_service.py — primaire)
  - `backend/data/tariffs/{ISO3}_tariffs.json` (tariff_data_service.py — secondaire)

Ne réécrit RIEN par interprétation : chaque champ du fichier de sortie est
une simple reprojection des champs canoniques (measures, requirements,
fiscal_advantages) groupés par HS6. Aucun taux n'est recalculé ou inventé.

Usage:
    python engine/scripts/canonical_to_tariffs.py            # tous les pays
    python engine/scripts/canonical_to_tariffs.py DZA TUN    # pays sélectionnés
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
BACKEND_DATA_DIR = Path(__file__).parent.parent.parent / "backend" / "data"
TARIFFS_DIR = BACKEND_DATA_DIR / "tariffs"


def _measure_to_tax_detail(m: dict) -> dict:
    return {
        "tax": m["code"],
        "rate": m.get("rate_pct"),
        "observation": m.get("name_fr") or m["code"],
    }


def _requirement_to_formality(r: dict) -> dict:
    return {
        "code": r.get("code") or "",
        "document_fr": r.get("document_fr") or "",
        "document_en": r.get("document_en") or r.get("document_fr") or "",
    }


def _advantage_to_fiscal(a: dict) -> dict:
    return {
        "tax": a.get("tax_code") or "",
        "rate": a.get("reduced_rate_pct"),
        "condition_fr": a.get("condition_fr") or "",
        "condition_en": a.get("condition_en") or a.get("condition_fr") or "",
    }


def _build_sub_position(line: dict) -> dict:
    commodity = line["commodity"]
    dd = next((m["rate_pct"] for m in line["measures"]
               if m["measure_type"] == "CUSTOMS_DUTY"), None)
    return {
        "code": commodity["national_code"],
        "digits": commodity["digits"],
        "dd": dd,
        "description_fr": commodity.get("description_fr") or "",
        "description_en": commodity.get("description_en") or commodity.get("description_fr") or "",
        "source": line["provenance"]["source_name"],
    }


def convert_country(country: str) -> dict:
    in_path = OUTPUT_DIR / f"{country}_canonical.jsonl"
    if not in_path.exists():
        raise FileNotFoundError(f"Pas de sortie canonique pour {country} : {in_path}")

    lines = [json.loads(l) for l in in_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        raise ValueError(f"{country} : fichier canonique vide")

    by_hs6: dict[str, list[dict]] = defaultdict(list)
    for line in lines:
        by_hs6[line["commodity"]["hs6"]].append(line)

    tariff_lines = []
    dd_rates: list[float] = []
    vat_rates: list[float] = []
    other_rates: list[float] = []

    for hs6, group in sorted(by_hs6.items()):
        group.sort(key=lambda l: l["commodity"]["national_code"])
        rep = group[0]
        commodity = rep["commodity"]

        dd_rate = next((m["rate_pct"] for m in rep["measures"]
                         if m["measure_type"] == "CUSTOMS_DUTY"), None)
        vat_rate = next((m["rate_pct"] for m in rep["measures"]
                          if m["measure_type"] == "VAT"), None)
        other_total = round(sum(
            m["rate_pct"] for m in rep["measures"]
            if m["measure_type"] not in ("CUSTOMS_DUTY", "VAT") and m.get("rate_pct") is not None
        ), 4)

        if dd_rate is not None:
            dd_rates.append(dd_rate)
        if vat_rate is not None:
            vat_rates.append(vat_rate)
        other_rates.append(other_total)

        zlecaf_measure = next((m for m in rep["measures"]
                                if m["measure_type"] == "CUSTOMS_DUTY" and m.get("zlecaf_rate_pct") is not None), None)
        zlecaf_rate = zlecaf_measure["zlecaf_rate_pct"] if zlecaf_measure else rep.get("total_zlecaf_pct")

        sub_positions = [_build_sub_position(l) for l in group if l["commodity"]["national_code"] != hs6]

        fiscal_advantages = []
        seen_advantages = set()
        for l in group:
            for a in l.get("fiscal_advantages", []):
                key = (a.get("tax_code"), a.get("condition_fr"))
                if key not in seen_advantages:
                    seen_advantages.add(key)
                    fiscal_advantages.append(_advantage_to_fiscal(a))

        administrative_formalities = []
        seen_formalities = set()
        for l in group:
            for r in l.get("requirements", []):
                key = (r.get("code"), r.get("document_fr"))
                if key not in seen_formalities:
                    seen_formalities.add(key)
                    administrative_formalities.append(_requirement_to_formality(r))

        tariff_lines.append({
            "hs6": hs6,
            "chapter": commodity.get("chapter") or hs6[:2],
            "description_fr": commodity.get("description_fr") or "",
            "description_en": commodity.get("description_en") or commodity.get("description_fr") or "",
            "category": commodity.get("category"),
            "unit": commodity.get("unit"),
            "sensitivity": commodity.get("sensitivity") or "normal",
            "dd_rate": dd_rate,
            "dd_source": rep["provenance"]["source_name"],
            "zlecaf_rate": zlecaf_rate,
            "zlecaf_source": "ZLECAf" if zlecaf_rate is not None else None,
            "vat_rate": vat_rate,
            "other_taxes_rate": other_total,
            "taxes_detail": [_measure_to_tax_detail(m) for m in rep["measures"]],
            "total_taxes_pct": round(sum(
                m["rate_pct"] for m in rep["measures"] if m.get("rate_pct") is not None
            ), 4),
            "fiscal_advantages": fiscal_advantages,
            "administrative_formalities": administrative_formalities,
            "sub_positions": sub_positions,
        })

    summary = {
        "total_tariff_lines": len(tariff_lines),
        "total_sub_positions": sum(len(t["sub_positions"]) for t in tariff_lines),
        "total_positions": len(lines),
        "lines_with_sub_positions": sum(1 for t in tariff_lines if t["sub_positions"]),
        "vat_rate_pct": round(statistics.mode(vat_rates), 4) if vat_rates else 0.0,
        "other_taxes_pct": round(statistics.mean(other_rates), 4) if other_rates else 0.0,
        "dd_rate_range": {
            "min": round(min(dd_rates), 4) if dd_rates else 0.0,
            "max": round(max(dd_rates), 4) if dd_rates else 0.0,
            "avg": round(statistics.mean(dd_rates), 4) if dd_rates else 0.0,
        },
        "chapters_covered": len({t["chapter"] for t in tariff_lines}),
        "has_detailed_taxes": True,
        "data_status": lines[0]["provenance"]["data_status"],
        "reliability": lines[0]["provenance"]["reliability"],
        "source_name": lines[0]["provenance"]["source_name"],
        "source_url": lines[0]["provenance"]["source_url"],
    }

    doc = {
        "country_code": country,
        "generated_at": datetime.utcnow().isoformat(),
        "data_format": "canonical_v4",
        "summary": summary,
        "tariff_lines": tariff_lines,
    }

    TARIFFS_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, ensure_ascii=False, indent=2)
    primary_path = BACKEND_DATA_DIR / f"{country}_tariffs.json"
    secondary_path = TARIFFS_DIR / f"{country}_tariffs.json"
    primary_path.write_text(payload, encoding="utf-8")
    secondary_path.write_text(payload, encoding="utf-8")
    print(f"[{country}] {len(tariff_lines)} HS6 ({len(lines)} positions) → {primary_path} + {secondary_path}")
    return doc


def convert_all(countries: list[str] | None = None) -> None:
    targets = countries or sorted(p.stem.replace("_canonical", "") for p in OUTPUT_DIR.glob("*_canonical.jsonl"))
    ok, failed = 0, []
    for country in targets:
        try:
            convert_country(country)
            ok += 1
        except Exception as e:
            failed.append((country, str(e)))
            print(f"[{country}] ERREUR : {e}")
    print(f"\n{ok}/{len(targets)} pays publiés vers backend/data/tariffs/")
    if failed:
        print("Échecs :", ", ".join(c for c, _ in failed))


if __name__ == "__main__":
    args = sys.argv[1:]
    convert_all([a.upper() for a in args] if args else None)
