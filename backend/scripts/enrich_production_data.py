#!/usr/bin/env python3
"""
Surcouche d'enrichissement du fichier de production (idempotente)
================================================================
Enrichit ``data/json/production_africaine.json`` SANS le reconstruire depuis zéro,
afin de préserver les 10 000+ enregistrements agricoles FAOSTAT bulk déjà en place.

Applique quatre enrichissements curés (valeurs publiées uniquement) :

  1. MINING      — nouveaux minéraux + extension 2024   (etl/mining_extended.py)
  2. MACRO       — valeur ajoutée sectorielle & croissance PIB réels, World Bank
                   WDI 2023-2024 (etl/macro_extended.py ← etl/macro_wdi_data.py)
  3. AGRICULTURE — prévisions OECD-FAO (2025/2030)        (etl/faostat_projections.py)

La dimension MANUFACTURING est laissée aux valeurs publiées (aucune série
rétro-calculée : le contrat « valeurs publiées uniquement » interdit d'extrapoler
des années non sourcées).

Chaque dimension est fusionnée par clé naturelle (upsert) → le script est
IDEMPOTENT : le relancer ne crée pas de doublons.

Usage :
    python3 scripts/enrich_production_data.py            # enrichit + écrit
    python3 scripts/enrich_production_data.py --dry-run  # stats seulement
"""

from __future__ import annotations

import argparse
import json
import os
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

    # ── 2. Macro : World Bank WDI 2023-2024 réels (upsert) ──────────────────
    macro_add = build_macro_series()
    data["value_added_macro"], mac_add, mac_up = _upsert(
        data.get("value_added_macro", []),
        macro_add,
        ["country_iso3", "indicator_code", "sector_isic_section", "year"],
        overwrite=True,
    )
    print(f"[2] Macro       : +{mac_add} enreg., {mac_up} mis à jour (World Bank WDI 2023-2024)")

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

    # ── 4. Manufacturing : conservé aux valeurs PUBLIÉES (pas de back-cast) ──
    # Le contrat de données du projet interdit toute valeur extrapolée : sans
    # série UNIDO INDSTAT4 multi-années publiée en source, on ne fabrique pas
    # d'années antérieures. La dimension reste donc aux enregistrements publiés.
    print(
        f"[4] Manufacture : {len(data.get('manufacturing_unido', []))} enreg. publiés "
        "(inchangés — aucune extrapolation)"
    )

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
            "macro": "World Bank WDI 2023-2024 (valeurs réelles API) — etl/macro_wdi_data.py",
            "agriculture_projections": "OECD-FAO Agricultural Outlook 2024-2033 — etl/faostat_projections.py",
            "manufacturing": "UNIDO INDSTAT4 — valeurs publiées (2024, inchangées)",
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
        "Valeurs réelles publiées (macro = World Bank WDI via API) + prévisions "
        "agricoles étiquetées (is_projection). "
        "Aucune génération aléatoire. Sources : FAO/OCDE, UNIDO, USGS, WNA, EIA, "
        "OPEC, World Bank."
    )

    print("\n[APRÈS]")
    _summary(data)

    if args.dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return

    # Écriture ATOMIQUE : sérialise dans un fichier temporaire sibling puis
    # remplace la cible via os.replace (atomique sur le même système de fichiers).
    # Une interruption / erreur de sérialisation / disque plein laisse ainsi le
    # dataset d'origine intact (les 10 000+ enregistrements ne sont jamais perdus).
    tmp = OUT_FILE.with_name(OUT_FILE.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, OUT_FILE)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
