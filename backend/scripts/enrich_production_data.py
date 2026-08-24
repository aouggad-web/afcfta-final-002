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
from etl.mining_extended import build_all as build_mining_additions
from etl.unido_data import UNIDO_INDUSTRY_DATA

# Années rétro-calculées AVANT l'année de référence (data_year, généralement 2024).
MANUF_BACKCAST_YEARS = [2021, 2022, 2023]


# =============================================================================
# Fusion générique par clé naturelle (upsert)
# =============================================================================
def _upsert(
    existing: List[Dict], additions: List[Dict], key_fields: List[str], overwrite: bool
) -> tuple[List[Dict], int, int]:
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
# MANUFACTURING — séries multi-années rétro-calculées
# =============================================================================
def build_manufacturing_backcast(existing: List[Dict]) -> List[Dict]:
    """Ajoute une série 2021-2023 de valeur ajoutée manufacturière PAR SECTEUR,
    dérivée des enregistrements existants (année de référence) en les déflatant
    par les taux de croissance PUBLIÉS (UNIDO).

    Principe : on ne touche PAS aux enregistrements existants (labels, valeurs et
    année de référence conservés à l'identique — indispensable pour ne pas casser
    la résolution HS→commodité et les calculs de couverture continentale, qui
    s'appuient sur l'année la plus récente). On ne fait qu'AJOUTER des années
    antérieures, en copiant chaque enregistrement existant et en déflatant sa
    valeur : val(N-1) = val(N) / (1 + taux/100). Aucune valeur aléatoire — les
    taux 2024→2023 (growth_rate_2024_est) et 2023→2022→2021 (growth_rate_2023)
    proviennent d'UNIDO. Les années ajoutées portent is_estimation=True.
    """
    # Taux publiés par pays.
    rates: Dict[str, tuple] = {}
    for iso3, d in UNIDO_INDUSTRY_DATA.items():
        rates[iso3] = (d.get("growth_rate_2024_est"), d.get("growth_rate_2023"))

    # Ne rétro-calcule qu'à partir de l'enregistrement de l'année de référence
    # (la plus récente) de chaque (pays, secteur ISIC).
    latest_by_key: Dict[tuple, Dict] = {}
    for rec in existing:
        key = (rec.get("country_iso3"), rec.get("isic_code"))
        cur = latest_by_key.get(key)
        if cur is None or (rec.get("year") or 0) > (cur.get("year") or 0):
            latest_by_key[key] = rec

    additions: List[Dict] = []
    for (iso3, _isic), base in latest_by_key.items():
        base_year = base.get("year")
        base_val = base.get("value")
        if base_year is None or not base_val:
            continue
        g24, g23 = rates.get(iso3, (None, None))
        rate23 = (g23 / 100.0) if g23 is not None else 0.0
        rate24 = (g24 / 100.0) if g24 is not None else 0.0

        # Valeurs déflatées année par année en repartant de l'année de référence.
        year_values: Dict[int, float] = {}
        v = float(base_val)
        # base_year -> 2023
        if base_year >= 2024:
            v = v / (1.0 + rate24)
            year_values[2023] = v
        elif base_year == 2023:
            year_values[2023] = v
        v23 = year_values.get(2023, float(base_val))
        year_values[2022] = v23 / (1.0 + rate23)
        year_values[2021] = year_values[2022] / (1.0 + rate23)

        for year in MANUF_BACKCAST_YEARS:
            if year >= base_year:
                continue  # ne jamais recouvrir l'année de référence
            val = year_values.get(year)
            if val is None:
                continue
            rec = dict(base)
            rec["year"] = year
            rec["value"] = round(val)
            rec["is_estimation"] = True
            additions.append(rec)
    return additions


# =============================================================================
# Point d'entrée
# =============================================================================
def _summary(data: Dict) -> None:
    for dim in (
        "value_added_macro",
        "agri_faostat",
        "agri_projections",
        "manufacturing_unido",
        "mining_usgs",
    ):
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
        data.get("mining_usgs", []),
        mining_add,
        ["country_iso3", "commodity_label", "year"],
        overwrite=False,
    )
    print(
        f"\n[1] Mining      : +{m_add} enreg. ({len({r['commodity_label'] for r in mining_add})} minéraux apportés)"
    )

    # ── 2. Macro : séries 2023-2025 (upsert, données plus récentes) ─────────
    macro_add = build_macro_series()
    data["value_added_macro"], mac_add, mac_up = _upsert(
        data.get("value_added_macro", []),
        macro_add,
        ["country_iso3", "indicator_code", "sector_isic_section", "year"],
        overwrite=True,
    )
    print(f"[2] Macro       : +{mac_add} enreg., {mac_up} mis à jour (WB 2024 + IMF WEO 2025)")

    # ── 3. Agriculture : prévisions OECD-FAO (clé DÉDIÉE agri_projections) ───
    # Stockées à part de agri_faostat : ce sont des PRÉVISIONS (pas des
    # productions observées), qui ne doivent pas alimenter la résolution
    # HS→capacité ni les calculs de besoin national du module Opportunités.
    proj_add = build_projections()
    data["agri_projections"], a_add, a_up = _upsert(
        data.get("agri_projections", []),
        proj_add,
        ["country_iso3", "commodity_label", "indicator_code", "year"],
        overwrite=True,
    )
    print(
        f"[3] Agriculture : {a_add} prévisions FAO/OCDE (clé agri_projections, horizons 2025/2030)"
    )

    # ── 4. Manufacturing : back-cast 2021-2023 (labels/2024 préservés) ──────
    manuf_backcast = build_manufacturing_backcast(data.get("manufacturing_unido", []))
    data["manufacturing_unido"], mf_add, mf_up = _upsert(
        data.get("manufacturing_unido", []),
        manuf_backcast,
        ["country_iso3", "isic_code", "year"],
        overwrite=False,
    )
    print(f"[4] Manufacture : +{mf_add} enreg. back-cast (séries 2021-2024, réf. préservée)")

    # ── Countries agrégés + metadata ────────────────────────────────────────
    all_recs = (
        data.get("value_added_macro", [])
        + data.get("agri_faostat", [])
        + data.get("agri_projections", [])
        + data.get("manufacturing_unido", [])
        + data.get("mining_usgs", [])
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
        "agriculture_projections": len(data.get("agri_projections", [])),
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
