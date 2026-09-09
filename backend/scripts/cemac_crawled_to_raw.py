#!/usr/bin/env python3
"""
Convertit les données CEMAC crawlées → format raw_crawl ingérable par le moteur
================================================================================
Les fichiers {CMR,GAB,TCD,CAF,COG}_tariffs.json dans backend/data/crawled/
contiennent déjà les données officielles CEMAC (TEC PDF + taxes nationales).

Ce script les convertit en format plat raw_crawl que le moteur accepte.
Il utilise les positions HS10 (sub_positions) quand disponibles, sinon HS6.

Usage :
    python backend/scripts/cemac_crawled_to_raw.py
    python backend/scripts/cemac_crawled_to_raw.py --countries CMR GAB
    python backend/scripts/cemac_crawled_to_raw.py --hs6-only  # 5 831 lignes HS6

Ingestion (moteur + garde-fous) :
    python engine/adapters/raw_crawl_adapter.py CMR engine/sources/CMR_raw.json engine/output/
    python engine/adapters/raw_crawl_adapter.py GAB engine/sources/GAB_raw.json engine/output/
    (etc. pour TCD, CAF, COG)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CRAWLED_DIR = REPO_ROOT / "backend" / "data" / "crawled"
ENGINE_SOURCES = REPO_ROOT / "engine" / "sources"

# Membres CEMAC avec fichier crawlé existant
CEMAC_AVAILABLE = {
    "CMR": ("Cameroun", "DGD Cameroun (douanes.cm) + TEC CEMAC PDF", "https://www.douanes.cm/"),
    "GAB": ("Gabon", "Douanes Gabon + TEC CEMAC PDF", "https://douanes.ga/"),
    "TCD": ("Tchad", "DGI Tchad (finances.gouv.td) + TEC CEMAC PDF", "https://finances.gouv.td/"),
    "CAF": (
        "Centrafrique",
        "Douanes CAF (edouanes.cf) + TEC CEMAC PDF",
        "https://www.finances.gouv.cf/",
    ),
    "COG": ("Congo", "Douanes Congo (douanes.gouv.cg) + TEC CEMAC PDF", "https://douanes.gouv.cg/"),
}


def _load_crawled(member: str) -> dict | None:
    path = CRAWLED_DIR / f"{member}_tariffs.json"
    if not path.exists():
        print(f"  ⚠ {member}: fichier absent ({path})")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _convert_line(line: dict, member: str, hs6_only: bool) -> list[dict]:
    """
    Convertit une tariff_line HS6 (avec sub_positions optionnels) en positions plates.
    Priorité : sub_positions HS10 si présentes et --hs6-only non activé.
    """
    hs6 = str(line.get("hs6", "")).replace(".", "").strip()
    desc_en = (line.get("description_en") or line.get("description_fr") or "").strip()
    chapter = str(line.get("chapter", hs6[:2])).strip()
    dd_rate = line.get("dd_rate")
    vat_rate = line.get("vat_rate")

    # Sub-positions HS10 disponibles et prioritaires
    subs = line.get("sub_positions", [])
    if subs and not hs6_only:
        result = []
        for sub in subs:
            code = str(sub.get("code", "")).replace(".", "").strip()
            if not code:
                continue
            digits = int(sub.get("digits", len(code)))
            sub_dd = sub.get("dd")
            # Hérite du DD HS6 si le sous-produit n'en a pas
            if sub_dd is None:
                sub_dd = dd_rate
            result.append(
                {
                    "code": code,
                    "description_en": sub.get("description_en")
                    or sub.get("description_fr")
                    or desc_en,
                    "chapter": chapter,
                    "digits": digits,
                    "dd_rate": float(sub_dd) if sub_dd is not None else None,
                    "dd_rate_raw": f"{sub_dd} %" if sub_dd is not None else "",
                    "vat_rate": float(vat_rate) if vat_rate is not None else None,
                    "export_levy_rate": None,
                }
            )
        return result

    # Repli HS6
    if not hs6 or len(hs6) < 6:
        return []
    return [
        {
            "code": hs6,
            "description_en": desc_en,
            "chapter": chapter,
            "digits": 6,
            "dd_rate": float(dd_rate) if dd_rate is not None else None,
            "dd_rate_raw": f"{dd_rate} %" if dd_rate is not None else "",
            "vat_rate": float(vat_rate) if vat_rate is not None else None,
            "export_levy_rate": None,
        }
    ]


def _assemble(member: str, data: dict, hs6_only: bool) -> dict:
    country_fr, source, source_url = CEMAC_AVAILABLE[member]
    tariff_lines = data.get("tariff_lines", [])

    positions: list[dict] = []
    for line in tariff_lines:
        positions.extend(_convert_line(line, member, hs6_only))

    # Statistiques DD pour vérification
    dd_vals = {float(p["dd_rate"]) for p in positions if p.get("dd_rate") is not None}

    generated_at = data.get("generated_at", datetime.now(timezone.utc).isoformat())
    # Conserver la date originale de crawl (source de provenance)
    try:
        from datetime import timezone as tz

        crawled_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).isoformat()
    except (ValueError, AttributeError):
        crawled_at = datetime.now(timezone.utc).isoformat()

    return {
        "country_code": member,
        "country_name": country_fr,
        "source": source,
        "source_url": source_url,
        "crawled_at": crawled_at,
        "data_type": "raw_crawl",
        "notes": [
            "TEC CEEAC — Tarif Extérieur Commun CEMAC",
            f"Bandes DD disponibles : {sorted(dd_vals)}",
            f"Nomenclature : {'HS10 (sub_positions)' if not hs6_only else 'HS6 uniquement'}",
            f"Source originale : {source}",
            f"Converti depuis backend/data/crawled/{member}_tariffs.json",
        ],
        "positions": positions,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--countries",
        nargs="+",
        choices=list(CEMAC_AVAILABLE),
        default=list(CEMAC_AVAILABLE),
        help="Membres CEMAC à convertir (défaut : tous disponibles)",
    )
    ap.add_argument(
        "--out-dir",
        default=str(ENGINE_SOURCES),
        help="Répertoire de sortie (défaut : engine/sources/)",
    )
    ap.add_argument(
        "--hs6-only",
        action="store_true",
        help="Utiliser uniquement les lignes HS6 (5 831 par pays)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Simuler sans écrire de fichier")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 64)
    print(" Conversion CEMAC crawled → raw_crawl (moteur tarifaire)")
    print("=" * 64)
    print(f"  Source  : {CRAWLED_DIR}")
    print(f"  Sortie  : {out_dir}")
    print(f"  Niveau  : {'HS6 seulement' if args.hs6_only else 'HS10 (sub-positions)'}")
    print()

    ok, total = 0, 0
    for member in args.countries:
        print(f"  {member} — {CEMAC_AVAILABLE[member][0]} ...")
        raw = _load_crawled(member)
        if raw is None:
            continue

        out = _assemble(member, raw, args.hs6_only)
        n = len(out["positions"])
        dd_vals = sorted(
            {float(p["dd_rate"]) for p in out["positions"] if p.get("dd_rate") is not None}
        )
        print(f"    {n:,} positions | bandes DD : {dd_vals}")

        if args.dry_run:
            print("    (--dry-run) fichier NON écrit")
        else:
            out_path = out_dir / f"{member}_raw.json"
            out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"    → {out_path}")

        ok += 1
        total += n

    print(f"\n  Total : {ok} pays / {total:,} positions")
    if not args.dry_run:
        print("\n  Ingestion (avec garde-fous) :")
        for m in args.countries:
            path = out_dir / f"{m}_raw.json"
            if (CRAWLED_DIR / f"{m}_tariffs.json").exists():
                print(
                    f"    python engine/adapters/raw_crawl_adapter.py " f"{m} {path} engine/output/"
                )


if __name__ == "__main__":
    main()
