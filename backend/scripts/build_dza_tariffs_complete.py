#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dza_tariffs_complete.py

Consolide les données tarifaires algériennes depuis 3 sources :
  1. DZA_tariffs_fast.json  → 17 115 positions nationales (10 chiffres) + descriptions conformepro.dz
  2. DZA_progress_*.json    → 5 136 positions ch.01-29 avec taux réels crawlés + formalités + avantages
  3. ETL country_taxes_algeria.py → taux DD/DAPS/TVA/TCS/PRCT calculés pour ch.30-97

Sortie : DZA_tariffs.json → 17 115 positions complètes
"""

import json
import glob
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
CRAWLED_DIR = BACKEND_DIR / "data" / "crawled"

sys.path.insert(0, str(BACKEND_DIR))
from etl.country_taxes_algeria import (
    get_dza_taxes_for_hs6,
    DZA_FORMALITIES_BY_CATEGORY,
    get_dza_formality_category,
)


def load_progress_index() -> dict:
    """Charge tous les DZA_progress_*.json, déduplique par hs_code (10 chiffres)."""
    pattern = str(CRAWLED_DIR / "DZA_progress_*.json")
    progress_files = sorted(glob.glob(pattern))
    index = {}
    duplicates = 0
    for pf in progress_files:
        with open(pf, encoding="utf-8") as f:
            d = json.load(f)
        for item in d.get("data", []):
            code = (item.get("hs_code") or item.get("raw_code") or "").replace(".", "").replace(" ", "")
            if not code:
                continue
            if code not in index:
                index[code] = item
            else:
                duplicates += 1
    print(f"  Progress files : {len(progress_files)} fichiers, {len(index)} positions uniques, {duplicates} doublons ignorés")
    return index


def build_taxes_from_progress(item: dict) -> tuple:
    """Extrait les taxes depuis un item progress file → (taxes_dict, advantages_list, formalities_list)."""
    taxes_raw = item.get("taxes", {})
    taxes = {}
    for code, info in taxes_raw.items():
        if isinstance(info, dict):
            taxes[code] = {
                "name": info.get("name", code),
                "rate": info.get("rate", 0),
                "raw": info.get("raw", f"{info.get('rate', 0):.0f}%"),
                "source": "conformepro.dz",
            }
        elif isinstance(info, (int, float)):
            taxes[code] = {"name": code, "rate": float(info), "raw": f"{info:.0f}%", "source": "conformepro.dz"}

    advantages = item.get("advantages", [])
    formalities = item.get("formalities", [])
    return taxes, advantages, formalities


def build_taxes_from_etl(hs6: str) -> tuple:
    """Calcule les taxes via l'ETL pour un code HS6 → (taxes_dict, advantages_list, formalities_list)."""
    t = get_dza_taxes_for_hs6(hs6)
    taxes = {}

    if t.get("daps_rate", 0) > 0:
        taxes["DAPS"] = {
            "name": "Droit Additionnel Provisoire de Sauvegarde",
            "rate": t["daps_rate"],
            "raw": f"{t['daps_rate']:.0f}%",
            "source": "douane.gov.dz (ETL)",
        }
    taxes["DD"] = {
        "name": "Droit de Douane",
        "rate": t["dd_rate"],
        "raw": f"{t['dd_rate']:.0f}%",
        "source": "douane.gov.dz (ETL)",
    }
    taxes["PRCT"] = {
        "name": "Prélèvement à la Compensation du Transport",
        "rate": t["prct_rate"],
        "raw": f"{t['prct_rate']:.0f}%",
        "source": "douane.gov.dz (ETL)",
    }
    if t.get("tcs_rate", 0) > 0:
        taxes["TCS"] = {
            "name": "Taxe de Contrôle Sanitaire",
            "rate": t["tcs_rate"],
            "raw": f"{t['tcs_rate']:.0f}%",
            "source": "douane.gov.dz (ETL)",
        }
    taxes["TVA"] = {
        "name": "Taxe sur la Valeur Ajoutée",
        "rate": t["tva_rate"],
        "raw": f"{t['tva_rate']:.0f}%",
        "source": "douane.gov.dz (ETL)",
    }

    # Avantages fiscaux (ZLECAf + conventions)
    advantages = []
    for adv in t.get("fiscal_advantages", []):
        if isinstance(adv, dict):
            advantages.append(adv.get("condition_fr", str(adv)))
        else:
            advantages.append(str(adv))

    # Formalités administratives
    formalities = []
    fmts_raw = t.get("administrative_formalities", [])
    if isinstance(fmts_raw, dict):
        for cat_items in fmts_raw.values():
            for fi in (cat_items if isinstance(cat_items, list) else []):
                formalities.append(fi.get("document_fr", str(fi)) if isinstance(fi, dict) else str(fi))
    elif isinstance(fmts_raw, list):
        for fi in fmts_raw:
            formalities.append(fi.get("document_fr", str(fi)) if isinstance(fi, dict) else str(fi))

    return taxes, advantages, formalities


def get_designation_full(pos: dict, prog_item: Optional[dict]) -> str:
    """Construit la désignation hiérarchique complète."""
    if prog_item:
        full = prog_item.get("designation_full", "")
        if full:
            return full
    section = pos.get("section", "")
    chapter = pos.get("chapter", "")
    heading = pos.get("heading", "")
    name = pos.get("name", "")
    parts = []
    if section:
        parts.append(f"Section {section}")
    if chapter:
        parts.append(f"Chapitre {chapter}")
    if heading:
        parts.append(f"Position {heading}")
    if name:
        parts.append(name)
    return " > ".join(parts) if parts else name


def main():
    print("=" * 60)
    print("BUILD DZA_tariffs_complete → DZA_tariffs.json")
    print("=" * 60)

    # --- Chargement SOURCE 1 : fast file (descriptions) ---
    print("\n[1/3] Chargement DZA_tariffs_fast.json …")
    fast_path = CRAWLED_DIR / "DZA_tariffs_fast.json"
    with open(fast_path, encoding="utf-8") as f:
        fast = json.load(f)
    fast_positions = fast.get("sub_positions", [])
    print(f"  Positions : {len(fast_positions)}")

    # --- Chargement SOURCE 2 : progress files (taux réels ch.01-29) ---
    print("\n[2/3] Chargement DZA_progress_*.json …")
    progress_index = load_progress_index()

    # --- Construction du fichier consolidé ---
    print("\n[3/3] Consolidation …")
    consolidated = []
    stats = {
        "total": 0,
        "from_progress": 0,
        "from_etl": 0,
        "with_daps": 0,
        "chapters": set(),
        "errors": 0,
    }

    for pos in fast_positions:
        hs_code = (pos.get("hs_code") or pos.get("raw_code") or "").replace(".", "").replace(" ", "")
        if not hs_code:
            stats["errors"] += 1
            continue

        hs6 = hs_code[:6]
        chapter = pos.get("chapter") or (hs_code[:2] if len(hs_code) >= 2 else "")
        chapter = chapter.zfill(2) if chapter.isdigit() else chapter
        stats["chapters"].add(chapter)
        stats["total"] += 1

        # Cherche d'abord dans les progress files (taux crawlés réels)
        prog_item = progress_index.get(hs_code)

        if prog_item:
            taxes, advantages, formalities = build_taxes_from_progress(prog_item)
            designation = prog_item.get("designation", "")
            designation_full = prog_item.get("designation_full", "")
            source_quality = "crawled_authentic"
            stats["from_progress"] += 1
        else:
            # Taux calculés par l'ETL (ch.30-97 et positions non crawlées)
            try:
                taxes, advantages, formalities = build_taxes_from_etl(hs6)
            except Exception as e:
                taxes = {}
                advantages = ["Certificat d'origine dans le cadre ZLECAf - Exonération DD"]
                formalities = ["Déclaration d'importation du produit", "Autorisation de libre circulation"]
                stats["errors"] += 1
            designation = ""
            designation_full = get_designation_full(pos, None)
            source_quality = "etl_computed"
            stats["from_etl"] += 1

        if taxes.get("DAPS", {}).get("rate", 0) > 0:
            stats["with_daps"] += 1

        # Description : préférer fast file (propre) + compléter avec progress
        name = pos.get("name", "")
        if prog_item and not name:
            raw_name = prog_item.get("name", "")
            name = raw_name.split("Sous-position")[-1].strip() if "Sous-position" in raw_name else raw_name

        description = pos.get("description", "")
        if not description and prog_item:
            description = prog_item.get("designation", "") or prog_item.get("designation_full", "")

        # Assurer avantages ZLECAf minimum
        if not advantages:
            advantages = ["Certificat d'origine dans le cadre ZLECAf - Exonération DD"]

        # Assurer formalités minimum
        if not formalities:
            cat = get_dza_formality_category(chapter)
            cat_fmts = DZA_FORMALITIES_BY_CATEGORY.get(cat, DZA_FORMALITIES_BY_CATEGORY["general"])
            formalities = [fi.get("document_fr", "") for fi in cat_fmts if isinstance(fi, dict)]

        entry = {
            "raw_code": pos.get("raw_code", ""),
            "hs_code": hs_code,
            "display_code": pos.get("display_code", ""),
            "heading": pos.get("heading", ""),
            "chapter": chapter,
            "section": pos.get("section", ""),
            "name": name,
            "description": description,
            "designation": designation,
            "designation_full": designation_full or get_designation_full(pos, prog_item),
            "taxes": taxes,
            "advantages": list(dict.fromkeys(advantages)),   # dédupliqués, ordre préservé
            "formalities": list(dict.fromkeys(formalities)),
            "source": "conformepro.dz",
            "source_quality": source_quality,
            "source_url": pos.get("source_url", ""),
        }
        consolidated.append(entry)

    # --- Écriture DZA_tariffs.json ---
    out_path = CRAWLED_DIR / "DZA_tariffs.json"
    output = {
        "country": "DZA",
        "country_name": "Algérie",
        "source": "conformepro.dz (données douane.gov.dz)",
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "total_positions": stats["total"],
            "from_progress_crawled": stats["from_progress"],
            "from_etl_computed": stats["from_etl"],
            "with_daps": stats["with_daps"],
            "chapters_covered": len(stats["chapters"]),
            "errors": stats["errors"],
        },
        "sub_positions": consolidated,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Fichier généré : {out_path}")
    print(f"   Total positions  : {stats['total']:,}")
    print(f"   Crawlées réelles : {stats['from_progress']:,}  (ch.01-29, conformepro.dz)")
    print(f"   ETL calculées    : {stats['from_etl']:,}  (ch.30-97)")
    print(f"   Avec DAPS        : {stats['with_daps']:,}")
    print(f"   Chapitres        : {len(stats['chapters'])}")
    print(f"   Erreurs          : {stats['errors']}")
    print()

    # Vérification de la position 7610909910
    test_codes = ["7610909910", "7610909990", "7308100000", "2523100000", "9403600000"]
    print("=== Vérification positions clés ===")
    idx = {e["hs_code"]: e for e in consolidated}
    for code in test_codes:
        entry = idx.get(code)
        if entry:
            taxes = entry["taxes"]
            dd = taxes.get("DD", {}).get("rate", "N/A")
            daps = taxes.get("DAPS", {}).get("rate", 0)
            tva = taxes.get("TVA", {}).get("rate", "N/A")
            prct = taxes.get("PRCT", {}).get("rate", "N/A")
            tcs = taxes.get("TCS", {}).get("rate", 0)
            quality = entry["source_quality"]
            print(f"  {code} [{quality}]")
            print(f"    Désignation : {entry['name'][:80]}")
            if daps:
                print(f"    DAPS={daps}% | DD={dd}% | PRCT={prct}% | TVA={tva}%")
            else:
                print(f"    DD={dd}% | PRCT={prct}% | TVA={tva}%")
            print(f"    Avantages   : {entry['advantages'][:2]}")
            print(f"    Formalités  : {entry['formalities'][:3]}")
        else:
            print(f"  {code} → NON TROUVÉ")
        print()


if __name__ == "__main__":
    main()
