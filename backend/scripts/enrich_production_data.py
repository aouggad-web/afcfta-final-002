#!/usr/bin/env python3
"""
Surcouche d'enrichissement du fichier de production (idempotente)
================================================================
Enrichit ``data/json/production_africaine.json`` SANS le reconstruire depuis zéro,
afin de préserver les 10 000+ enregistrements agricoles FAOSTAT bulk déjà en place.

Applique quatre enrichissements curés (valeurs publiées uniquement) :

  1. MINING      — nouveaux minéraux + extension 2024   (etl/mining_extended.py)
  2. MACRO       — séries 2023-2025, WB + IMF WEO 2025   (etl/macro_extended.py)
  3. AGRICULTURE — prévisions OECD-FAO (2025/2030)        (etl/faostat_projections.py)
  4. MANUFACTURING — séries multi-années 2021-2024 rétro-calculées depuis les taux
                     de croissance publiés UNIDO          (etl/unido_data.py)

Chaque dimension est fusionnée par clé naturelle (upsert) → le script est
IDEMPOTENT : le relancer ne crée pas de doublons.

Usage :
    python3 scripts/enrich_production_data.py            # enrichit + écrit
    python3 scripts/enrich_production_data.py --dry-run  # stats seulement
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
OUT_FILE = REPO_ROOT / "data" / "json" / "production_africaine.json"

sys.path.insert(0, str(BACKEND_DIR))

from etl.faostat_projections import build_projections
from etl.macro_extended import build_macro_series
from etl.mining_extended import ISO3_FR_NAME, build_all as build_mining_additions
from etl.unido_data import ISIC_SECTORS, UNIDO_INDUSTRY_DATA

# ISIC labels EN alignés sur le reste du build (fallback : label FR).
ISIC_LABELS_EN = {
    "10": "Manufacture of food products",
    "11": "Manufacture of beverages",
    "12": "Manufacture of tobacco products",
    "13": "Manufacture of textiles",
    "14": "Manufacture of wearing apparel",
    "15": "Manufacture of leather and related products",
    "16": "Manufacture of wood products",
    "17": "Manufacture of paper and paper products",
    "18": "Printing and reproduction of recorded media",
    "19": "Manufacture of coke and refined petroleum products",
    "20": "Manufacture of chemicals and chemical products",
    "21": "Manufacture of pharmaceuticals",
    "22": "Manufacture of rubber and plastics products",
    "23": "Manufacture of other non-metallic mineral products",
    "24": "Manufacture of basic metals",
    "25": "Manufacture of fabricated metal products",
    "26": "Manufacture of computer, electronic and optical products",
    "27": "Manufacture of electrical equipment",
    "28": "Manufacture of machinery and equipment n.e.c.",
    "29": "Manufacture of motor vehicles, trailers and semi-trailers",
    "30": "Manufacture of other transport equipment",
    "31": "Manufacture of furniture",
    "32": "Other manufacturing",
    "33": "Repair and installation of machinery and equipment",
}

MANUF_SERIES_YEARS = [2021, 2022, 2023, 2024]


# =============================================================================
# Fusion générique par clé naturelle (upsert)
# =============================================================================
def _upsert(existing: List[Dict], additions: List[Dict], key_fields: List[str],
            overwrite: bool) -> tuple[List[Dict], int, int]:
    """Fusionne ``additions`` dans ``existing`` par clé naturelle.

    overwrite=True  → une addition remplace l'enregistrement existant de même clé.
    overwrite=False → l'existant est préservé, seules les clés absentes sont ajoutées.
    Retourne (liste fusionnée, nb ajoutés, nb mis à jour).
    """
    def key(rec: Dict) -> tuple:
        return tuple(rec.get(f) for f in key_fields)

    index = {key(r): i for i, r in enumerate(existing)}
    merged = list(existing)
    added = updated = 0
    for rec in additions:
        k = key(rec)
        if k in index:
            if overwrite:
                merged[index[k]] = rec
                updated += 1
        else:
            index[k] = len(merged)
            merged.append(rec)
            added += 1
    return merged, added, updated


# =============================================================================
# MANUFACTURING — séries multi-années 2021-2024 depuis les taux UNIDO publiés
# =============================================================================
def build_manufacturing_series() -> List[Dict]:
    """Rétro-calcule une série 2021-2024 de valeur ajoutée manufacturière par
    secteur ISIC, à partir des taux de croissance PUBLIÉS (UNIDO). Aucune valeur
    aléatoire : chaque année antérieure est déflatée par le taux publié
    (2024→2023 via growth_rate_2024_est ; 2023→2022 et 2022→2021 via
    growth_rate_2023). Les années < data_year portent is_estimation=True.
    """
    records: List[Dict] = []
    for iso3, d in UNIDO_INDUSTRY_DATA.items():
        country_name = d.get("country_name", iso3)
        data_year = d.get("data_year", 2024)
        mva_total = d.get("mva_2024_mln_usd", d.get("mva_2023_mln_usd"))
        g24 = d.get("growth_rate_2024_est")
        g23 = d.get("growth_rate_2023")

        for sector in d.get("top_sectors", []):
            isic = str(sector.get("isic", ""))
            base_val = sector.get("value_mln_usd")
            base_is_est = False
            if not base_val and mva_total and sector.get("share_mva"):
                base_val = mva_total * sector["share_mva"] / 100.0
                base_is_est = True
            if not base_val:
                continue

            label_en = ISIC_LABELS_EN.get(isic, sector.get("name") or ISIC_SECTORS.get(isic, f"ISIC {isic}"))

            # Reconstruit la valeur de chaque année en déflatant depuis data_year.
            year_values: Dict[int, float] = {data_year: base_val}
            if g24 is not None:
                year_values[2023] = base_val / (1.0 + g24 / 100.0)
            else:
                year_values[2023] = base_val
            rate23 = (g23 / 100.0) if g23 is not None else 0.0
            year_values[2022] = year_values[2023] / (1.0 + rate23)
            year_values[2021] = year_values[2022] / (1.0 + rate23)

            for year in MANUF_SERIES_YEARS:
                val_mln = year_values.get(year)
                if val_mln is None:
                    continue
                records.append(
                    {
                        "country_name": country_name,
                        "country_iso3": iso3,
                        "year": year,
                        "sector_isic_section": "C",
                        "sector_detail": label_en,
                        "indicator_code": "INDSTAT_VA",
                        "indicator_label": "Value added",
                        "value": round(val_mln * 1_000_000),
                        "unit": "USD",
                        "currency": "USD",
                        "price_base_year": "current",
                        "source_institution": "UNIDO",
                        "source_dataset": "INDSTAT4 (ISIC Rev.4)",
                        "source_url": "https://stat.unido.org/",
                        "unido_dataset": "INDSTAT4",
                        "isic_revision": "4",
                        "isic_code": isic,
                        "isic_label": label_en,
                        "is_estimation": base_is_est or (year != data_year),
                    }
                )
    return records


# =============================================================================
# Point d'entrée
# =============================================================================
def _summary(data: Dict) -> None:
    for dim in ("value_added_macro", "agri_faostat", "manufacturing_unido", "mining_usgs"):
        recs = data.get(dim, [])
        years = sorted({r.get("year") for r in recs if r.get("year") is not None})
        countries = len({r.get("country_iso3") for r in recs})
        print(f"   {dim:22s}: {len(recs):6d} enreg. — {countries:3d} pays — années {years}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="N'écrit pas le fichier")
    args = ap.parse_args()

    print("=" * 70)
    print(" Enrichissement production_africaine.json (surcouche idempotente)")
    print("=" * 70)

    if not OUT_FILE.exists():
        print(f"❌ Fichier introuvable : {OUT_FILE}")
        sys.exit(1)

    with open(OUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n[AVANT]")
    _summary(data)

    # ── 1. Mining : nouveaux minéraux + 2024 (préserve l'existant) ──────────
    mining_add = build_mining_additions()
    data["mining_usgs"], m_add, m_up = _upsert(
        data.get("mining_usgs", []), mining_add,
        ["country_iso3", "commodity_label", "year"], overwrite=False,
    )
    print(f"\n[1] Mining      : +{m_add} enreg. ({len({r['commodity_label'] for r in mining_add})} minéraux apportés)")

    # ── 2. Macro : séries 2023-2025 (upsert, données plus récentes) ─────────
    macro_add = build_macro_series()
    data["value_added_macro"], mac_add, mac_up = _upsert(
        data.get("value_added_macro", []), macro_add,
        ["country_iso3", "indicator_code", "sector_isic_section", "year"], overwrite=True,
    )
    print(f"[2] Macro       : +{mac_add} enreg., {mac_up} mis à jour (WB 2024 + IMF WEO 2025)")

    # ── 3. Agriculture : prévisions OECD-FAO ────────────────────────────────
    proj_add = build_projections()
    data["agri_faostat"], a_add, a_up = _upsert(
        data.get("agri_faostat", []), proj_add,
        ["country_iso3", "commodity_label", "indicator_code", "year"], overwrite=True,
    )
    print(f"[3] Agriculture : +{a_add} prévisions FAO/OCDE (horizons 2025/2030)")

    # ── 4. Manufacturing : séries 2021-2024 ─────────────────────────────────
    manuf_series = build_manufacturing_series()
    data["manufacturing_unido"], mf_add, mf_up = _upsert(
        data.get("manufacturing_unido", []), manuf_series,
        ["country_iso3", "isic_code", "year"], overwrite=True,
    )
    print(f"[4] Manufacture : +{mf_add} enreg., {mf_up} mis à jour (séries 2021-2024)")

    # ── Countries agrégés + metadata ────────────────────────────────────────
    all_recs = (
        data.get("value_added_macro", []) + data.get("agri_faostat", [])
        + data.get("manufacturing_unido", []) + data.get("mining_usgs", [])
    )
    data["countries"] = sorted({r.get("country_iso3") for r in all_recs if r.get("country_iso3")})

    meta = data.setdefault("metadata", {})
    meta["last_updated"] = datetime.now(timezone.utc).isoformat()
    meta["enriched_by"] = "scripts/enrich_production_data.py — surcouche curée idempotente"
    meta.setdefault("sources", {})
    meta["sources"].update(
        {
            "mining_extended": "USGS MCS 2024/2025, WNA, EIA/OPEC — etl/mining_extended.py",
            "macro": "World Bank WDI 2024 + IMF WEO (avr. 2025) — etl/macro_extended.py",
            "agriculture_projections": "OECD-FAO Agricultural Outlook 2024-2033 — etl/faostat_projections.py",
            "manufacturing": "UNIDO INDSTAT4 — séries 2021-2024 (taux publiés)",
        }
    )
    meta["record_counts"] = {
        "agriculture": len(data.get("agri_faostat", [])),
        "manufacturing": len(data.get("manufacturing_unido", [])),
        "mining": len(data.get("mining_usgs", [])),
        "macro": len(data.get("value_added_macro", [])),
        "total": len(all_recs),
    }
    meta["note"] = (
        "Valeurs réelles publiées + projections étiquetées (is_projection). "
        "Aucune génération aléatoire. Sources : FAO/OCDE, UNIDO, USGS, WNA, EIA, "
        "OPEC, World Bank, IMF."
    )

    print("\n[APRÈS]")
    _summary(data)

    if args.dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
