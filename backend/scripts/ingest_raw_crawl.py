#!/usr/bin/env python3
"""
Ingesteur de fichiers raw_crawl → national_positions
======================================================
Convertit les fichiers JSON bruts générés par les crawlers locaux
en fichiers tarifaires au format national_positions (compatible API).

Usage (sur Replit) :
    python backend/scripts/ingest_raw_crawl.py backend/data/raw_crawls/zaf_raw.json
    python backend/scripts/ingest_raw_crawl.py backend/data/raw_crawls/*.json
    python backend/scripts/ingest_raw_crawl.py --all   # traite tous les fichiers raw_crawls/

Sortie : backend/data/crawled/{ISO3}_tariffs.json
"""

import argparse
import glob
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CRAWLED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw_crawls")

# ──────────────────────────────────────────────────────────────────────────────
# Configuration par pays : taxes nationales documentées, TVA, etc.
# ──────────────────────────────────────────────────────────────────────────────
COUNTRY_CONFIG = {
    "ZAF": {
        "name": "Afrique du Sud", "currency": "ZAR",
        "vat_rate": 15.0, "vat_name": "Value-Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "national_taxes": [],
        "notes": [
            "Schedule 1 Part 1 — SARS (South African Revenue Service)",
            "SACU Common External Tariff — mêmes taux pour NAM, BWA, LSO, SWZ",
            "VAT: 15% (Value-Added Tax Act 89 of 1991)",
            "Anti-dumping duties: séparés, non inclus ici",
        ],
        "sacu_note": "Taux SACU applicables aussi à: NAM, BWA, LSO, SWZ",
    },
    "MAR": {
        "name": "Maroc", "currency": "MAD",
        "vat_rate": 20.0, "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DD + TIC",
        "national_taxes": [
            {"code": "TIC", "name": "Taxe Intérieure de Consommation",
             "rate": None, "base": "variable",
             "note": "Taux spécifique par produit (alcool, tabac, carburant) — voir dd_rate_raw"},
        ],
        "notes": [
            "ADIL — Douanes Maroc (adil.douane.gov.ma)",
            "NDP: Nomenclature Douanière des Produits (10 chiffres)",
            "DD: 0/2.5/10/17.5/25/30/40/45/50%",
            "TVA: 20%/14%/10%/7%/exonéré selon produit",
            "TIC: Taxe Intérieure de Consommation (alcool, tabac, carburant, véhicules)",
            "Droits anti-dumping: non inclus",
        ],
    },
    "EGY": {
        "name": "Égypte", "currency": "EGP",
        "vat_rate": 14.0, "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "national_taxes": [
            {"code": "ACD", "name": "Additional Customs Duty",
             "rate": None, "base": "variable",
             "note": "Taux variable par produit"},
        ],
        "notes": [
            "Egyptian Customs Authority — egyptariffs.com",
            "Customs Duty (CD): 0/2/5/10/20/30/40%",
            "Additional Customs Duty (ACD): variable",
            "VAT: 14% standard (Law No. 67/2016)",
            "Sales Tax: certains produits spécifiques",
        ],
    },
    "ETH": {
        "name": "Éthiopie", "currency": "ETB",
        "vat_rate": 15.0, "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + CD + Excise + Surtax",
        "national_taxes": [
            {"code": "EXCISE", "name": "Excise Duty",
             "rate": None, "base": "variable",
             "note": "0/10/15/20/25/30/33/40/50/75/100% selon produit"},
            {"code": "SURTAX", "name": "Surtax",
             "rate": 10.0, "base": "CIF + CD + Excise",
             "note": "10% sur valeur CIF+CD+Excise — Proclamation 307/2002"},
            {"code": "WHT", "name": "Withholding Tax",
             "rate": 3.0, "base": "CIF",
             "note": "3% retenue à la source à l'importation"},
        ],
        "notes": [
            "Ethiopian Customs Commission (ECC) — customs.erca.gov.et",
            "Customs Duty (CD): 0/5/10/20/25/30/35%",
            "Excise: 0 à 100% selon produit",
            "Surtax: 10% sur CIF+CD+Excise",
            "VAT: 15% standard",
            "Withholding Tax: 3% à l'importation",
        ],
    },
    "MUS": {
        "name": "Maurice", "currency": "MUR",
        "vat_rate": 15.0, "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "national_taxes": [],
        "notes": [
            "MRA — Mauritius Revenue Authority (mra.mu)",
            "Customs Duty: 0/5/15/30% selon produit",
            "VAT: 15% standard (Value Added Tax Act)",
            "Excise Duty: alcool, tabac, véhicules",
            "COMESA: réductions tarifaires sur certains produits",
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def clean_code(code: str) -> str:
    return re.sub(r"[^\d]", "", str(code))


def to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        s = str(v).replace("%", "").replace(",", ".").strip()
        if s.lower() in ("free", "exempt", "exonéré", "—", "-", ""):
            return 0.0
        return float(s)
    except Exception:
        return None


def hs6_from_code(code: str) -> str:
    c = clean_code(code)
    return c[:6] if len(c) >= 6 else c


def infer_chapter(hs6: str) -> str:
    return hs6[:2] if len(hs6) >= 2 else "00"


def infer_category(ch: int) -> str:
    if ch <= 5:  return "livestock"
    if ch <= 15: return "agricultural"
    if ch <= 24: return "food"
    if ch <= 27: return "energy"
    if ch <= 40: return "chemicals"
    if ch <= 63: return "textiles"
    if ch <= 70: return "glass"
    if ch <= 83: return "metals"
    if ch <= 85: return "machinery"
    if ch <= 92: return "vehicles"
    return "general"


def build_taxes_detail(cfg: Dict, dd_rate: float, excise_rate: Optional[float] = None) -> List[Dict]:
    """Construit la liste taxes_detail pour une position."""
    taxes = []

    # DD
    if dd_rate is not None:
        taxes.append({
            "tax": "D.D",
            "rate": dd_rate,
            "base": "CIF",
            "methode": f"CIF × {dd_rate}%",
            "observation": cfg.get("notes", [""])[0],
        })

    # Taxes nationales fixes
    for nat in cfg.get("national_taxes", []):
        if nat.get("rate") is not None:
            taxes.append({
                "tax": nat["code"],
                "rate": nat["rate"],
                "base": nat.get("base", "CIF"),
                "methode": f"{nat['base']} × {nat['rate']}%",
                "observation": nat.get("note", nat.get("name", "")),
            })

    # Accise
    if excise_rate and excise_rate > 0:
        taxes.append({
            "tax": "EXCISE",
            "rate": excise_rate,
            "base": "CIF + DD",
            "methode": f"(CIF + DD) × {excise_rate}%",
            "observation": "Excise Duty",
        })

    # TVA
    tva_base = dd_rate + sum(
        n["rate"] for n in cfg.get("national_taxes", [])
        if n.get("rate") is not None
    ) + (excise_rate or 0)
    tva_base_mult = 1.0 + tva_base / 100
    tva_amount = round(100 * tva_base_mult * cfg["vat_rate"] / 100, 4)
    taxes.append({
        "tax": "TVA",
        "rate": cfg["vat_rate"],
        "base": cfg.get("vat_base", "CIF + DD"),
        "methode": f"({cfg.get('vat_base','CIF+DD')}) × {cfg['vat_rate']}%",
        "montant_sur_100": tva_amount,
        "observation": cfg.get("vat_name", "TVA"),
    })

    return taxes


# ──────────────────────────────────────────────────────────────────────────────
# Transformation raw → national_positions
# ──────────────────────────────────────────────────────────────────────────────

def transform(raw: Dict) -> Optional[Dict]:
    iso3 = raw.get("country_code", "").upper()
    if iso3 not in COUNTRY_CONFIG:
        logger.error(f"Pays non configuré: {iso3}. Ajouter dans COUNTRY_CONFIG.")
        return None

    cfg = COUNTRY_CONFIG[iso3]
    positions_raw = raw.get("positions", [])
    logger.info(f"{iso3}: {len(positions_raw)} positions brutes")

    # Grouper par HS6
    hs6_groups: Dict[str, List[Dict]] = defaultdict(list)
    for pos in positions_raw:
        code = clean_code(pos.get("code", ""))
        if len(code) < 6:
            continue
        hs6 = hs6_from_code(code)
        hs6_groups[hs6].append({
            "code": code,
            "description_en": pos.get("description_en", pos.get("description_fr", "")),
            "description_fr": pos.get("description_fr", pos.get("description_en", "")),
            "dd_rate": to_float(pos.get("dd_rate")),
            "dd_rate_raw": pos.get("dd_rate_raw", ""),
            "vat_rate": to_float(pos.get("vat_rate")) or cfg["vat_rate"],
            "excise_rate": to_float(pos.get("excise_rate")),
            "surtax_rate": to_float(pos.get("surtax_rate")),
            "withholding_rate": to_float(pos.get("withholding_rate")),
            "additional_customs_duty": to_float(pos.get("additional_customs_duty")),
            "tic_rate": to_float(pos.get("tic_rate")),
            "other_raw": pos.get("raw", {}),
        })

    tariff_lines = []
    total_positions = 0
    hs6_without = 0

    for hs6 in sorted(hs6_groups.keys()):
        subs = hs6_groups[hs6]
        chapter = infer_chapter(hs6)
        ch_int = int(chapter) if chapter.isdigit() else 0

        # Taux DD HS6 = le plus fréquent parmi les sous-positions
        dd_values = [s["dd_rate"] for s in subs if s["dd_rate"] is not None]
        if dd_values:
            dd_rate = Counter(dd_values).most_common(1)[0][0]
        else:
            dd_rate = 0.0
            hs6_without += 1

        # Trouver la meilleure description
        desc_en = next((s["description_en"] for s in subs if s["description_en"]), "")
        desc_fr = next((s["description_fr"] for s in subs if s["description_fr"]), desc_en)

        # Taxes
        excise_rate = subs[0].get("excise_rate") if subs else None
        taxes = build_taxes_detail(cfg, dd_rate, excise_rate)
        nat_sum = sum(n["rate"] for n in cfg.get("national_taxes", []) if n.get("rate"))

        # Sous-positions
        sub_positions_out = []
        for s in subs:
            s_dd = s["dd_rate"] if s["dd_rate"] is not None else dd_rate
            s_excise = s.get("excise_rate")
            s_taxes = build_taxes_detail(cfg, s_dd, s_excise)
            sub_positions_out.append({
                "code": s["code"],
                "national_code": s["code"],
                "digits": len(s["code"]),
                "description_en": s["description_en"],
                "description_fr": s["description_fr"],
                "dd_rate": s_dd,
                "dd_rate_raw": s.get("dd_rate_raw", ""),
                "excise_rate": s_excise,
                "vat_rate": s.get("vat_rate") or cfg["vat_rate"],
                "additional_taxes": {
                    k: s.get(k) for k in
                    ["surtax_rate", "withholding_rate", "additional_customs_duty", "tic_rate"]
                    if s.get(k) is not None
                },
                "taxes_detail": s_taxes,
                "source": raw.get("source", iso3),
            })
            total_positions += 1

        # Ligne HS6
        total_before_tva = dd_rate + nat_sum + (excise_rate or 0)
        tva_base_mult = 1.0 + total_before_tva / 100
        tva_amount = round(100 * tva_base_mult * cfg["vat_rate"] / 100, 4)
        full_total = round(total_before_tva + tva_amount, 2)

        tariff_lines.append({
            "hs6": hs6,
            "chapter": chapter,
            "description_fr": desc_fr,
            "description_en": desc_en,
            "category": infer_category(ch_int),
            "unit": "KG",
            "sensitivity": "sensitive" if dd_rate >= 25 else "normal",
            "dd_rate": dd_rate,
            "dd_source": raw.get("source", iso3),
            "zlecaf_rate": None,
            "zlecaf_rate_note": "Non disponible — calendrier ZLECAf officiel requis",
            "vat_rate": cfg["vat_rate"],
            "vat_note": cfg.get("vat_name", "TVA"),
            "other_taxes_rate": nat_sum,
            "taxes_detail": taxes,
            "total_taxes_pct": full_total,
            "fiscal_advantages": [],
            "administrative_formalities": [],
            "sub_positions": sub_positions_out,
            "has_sub_positions": len(sub_positions_out) > 0,
            "sub_position_count": len(sub_positions_out),
            "data_source": "crawl_authentic",
            "data_quality": "authentic",
        })

    if not tariff_lines:
        logger.error(f"{iso3}: aucune ligne tarifaire générée — vérifier le fichier raw")
        return None

    dd_rates = [l["dd_rate"] for l in tariff_lines]
    output = {
        "country_code": iso3,
        "country_name": cfg["name"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_format": "national_positions_crawl_authentic",
        "data_source": "crawl_authentic",
        "source_url": raw.get("source_url", ""),
        "original_source": raw.get("source", ""),
        "crawled_at": raw.get("crawled_at", ""),
        "notes": raw.get("notes", []) + cfg.get("notes", []),
        "summary": {
            "total_tariff_lines": len(tariff_lines),
            "total_national_positions": total_positions,
            "hs6_with_positions": len(tariff_lines) - hs6_without,
            "hs6_without_positions": hs6_without,
            "vat_rate_pct": cfg["vat_rate"],
            "dd_rate_range": {
                "min": min(dd_rates),
                "max": max(dd_rates),
                "avg": round(sum(dd_rates) / len(dd_rates), 2) if dd_rates else 0,
            },
        },
        "tariff_lines": tariff_lines,
    }

    return output


def process_file(path: str, force: bool = False) -> bool:
    logger.info(f"Traitement: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        logger.error(f"Erreur lecture {path}: {e}")
        return False

    if raw.get("data_type") != "raw_crawl":
        logger.error(f"{path}: data_type != 'raw_crawl' — fichier non compatible")
        return False

    iso3 = raw.get("country_code", "").upper()
    if not iso3:
        logger.error(f"{path}: country_code manquant")
        return False

    out_path = os.path.join(CRAWLED_DIR, f"{iso3}_tariffs.json")
    if os.path.exists(out_path) and not force:
        logger.warning(f"{out_path} existe déjà — utiliser --force pour écraser")
        return False

    result = transform(raw)
    if not result:
        return False

    os.makedirs(CRAWLED_DIR, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    sz = os.path.getsize(out_path) / 1024 / 1024
    logger.info(
        f"✅ {iso3}: {result['summary']['total_tariff_lines']} HS6 "
        f"| {result['summary']['total_national_positions']} positions "
        f"| {sz:.1f} MB → {out_path}"
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Ingesteur raw_crawl → national_positions")
    parser.add_argument("files", nargs="*", help="Fichiers raw_crawl JSON à traiter")
    parser.add_argument("--all", action="store_true", help="Traiter tous les fichiers dans raw_crawls/")
    parser.add_argument("--force", action="store_true", help="Écraser les fichiers existants")
    args = parser.parse_args()

    if args.all:
        files = sorted(glob.glob(os.path.join(RAW_DIR, "*_raw.json")))
        if not files:
            logger.error(f"Aucun fichier *_raw.json dans {RAW_DIR}")
            sys.exit(1)
    elif args.files:
        files = args.files
    else:
        parser.print_help()
        sys.exit(1)

    logger.info(f"Fichiers à traiter: {len(files)}")
    success = 0
    for path in files:
        if process_file(path, args.force):
            success += 1

    logger.info(f"=== Terminé: {success}/{len(files)} fichiers ingérés ===")
    if success > 0:
        logger.info("Redémarrer le serveur pour vider le cache tariff: workflows → Start application → Restart")


if __name__ == "__main__":
    main()
