#!/usr/bin/env python3
"""
Crawl TUN (Tunisie) → fichier raw_crawl ingérable par le moteur tarifaire
=========================================================================
Même problématique que MAR : le crawler intégré importe `crawlers/__init__.py`
qui dépend de `motor` (MongoDB) → échec sur une machine de dev sans MongoDB.

Ce runner charge `TunisiaDouaneScraper` DIRECTEMENT (sans le package crawlers),
vérifie les dépendances, crawle le portail tarifweb (douane.gov.tn) et convertit
la sortie au format « raw_crawl » plat du moteur (PROFILES["TUN"]).

Le scraper TUN renvoie par position :
    {hs_code, chapter, designation, taxes_import: [{code, rate_pct, raw_value,
     specific_value, assiette}], ...}
On aplatit taxes_import en champs dd_rate / dc_rate / fodec_rate / tcl_rate /
vat_rate (taux lus du crawl, jamais inventés).

Dépendances :
    pip install httpx beautifulsoup4

Usage :
    python backend/scripts/crawl_tun_to_raw.py --sample
    python backend/scripts/crawl_tun_to_raw.py --out engine/sources/tun_raw.json

Ingestion (avec garde-fous) :
    python engine/adapters/raw_crawl_adapter.py TUN engine/sources/tun_raw.json engine/output/
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _check_deps() -> None:
    missing = []
    for mod in ("httpx", "bs4"):
        if importlib.util.find_spec(mod) is None:
            missing.append("beautifulsoup4" if mod == "bs4" else mod)
    if missing:
        print("✗ Dépendances manquantes : " + ", ".join(missing))
        print(f"    pip install {' '.join(missing)}")
        sys.exit(2)


def _load_scraper():
    """Charge TunisiaDouaneScraper SANS déclencher crawlers/__init__ (→ motor)."""
    path = BACKEND_DIR / "crawlers" / "countries" / "tunisia_douane_scraper.py"
    if not path.exists():
        print(f"✗ Scraper introuvable : {path}")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("tunisia_douane_scraper", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tunisia_douane_scraper"] = mod
    spec.loader.exec_module(mod)
    return mod.TunisiaDouaneScraper


# ── Conversion taxes_import/taxes_export → champs plats ────────────────────

# Mappe un code de taxe du portail tarifweb vers un champ plat (import)
_TAX_FIELD_IMPORT = {
    "DD": "dd_rate",
    "DC": "dc_rate",
    "FODEC": "fodec_rate",
    "TCL": "tcl_rate",
    "TVA": "vat_rate",
}

# Mappe un code de taxe du portail tarifweb vers un champ plat (export)
_TAX_FIELD_EXPORT = {
    "DD": "export_dd_rate",
    "DC": "export_dc_rate",
    "PRÉLEV": "export_levy_rate",
    "LEVY": "export_levy_rate",
    "TVA": "export_vat_rate",
}


def _convert_position(p: dict) -> dict:
    code = str(p.get("hs_code", "")).strip()
    flat = {
        "code": code,
        "description_en": p.get("designation", ""),
        "chapter": p.get("chapter") or (code[:2] if len(code) >= 2 else ""),
        "digits": len(code),
        # Côté import
        "dd_rate": None,
        "dd_rate_raw": "",
        "dc_rate": None,
        "fodec_rate": None,
        "tcl_rate": None,
        "vat_rate": None,
        # Côté export
        "export_dd_rate": None,
        "export_dc_rate": None,
        "export_levy_rate": None,
        "export_vat_rate": None,
        "formalities": p.get("reglementation_import", []),
    }

    # Traitement côté import
    for tax in p.get("taxes_import", []) or []:
        tcode = str(tax.get("code", "")).upper().strip()
        key = None
        for known, field_name in _TAX_FIELD_IMPORT.items():
            if known.replace(".", "") in tcode.replace(".", ""):
                key = field_name
                break
        if not key:
            continue
        rate = tax.get("rate_pct")
        flat[key] = float(rate) if rate is not None else None
        if key == "dd_rate":
            flat["dd_rate_raw"] = tax.get("raw_value", "") or (
                f"{rate} %" if rate is not None else ""
            )

    # Traitement côté export
    for tax in p.get("taxes_export", []) or []:
        tcode = str(tax.get("code", "")).upper().strip()
        key = None
        for known, field_name in _TAX_FIELD_EXPORT.items():
            if known.replace(".", "") in tcode.replace(".", ""):
                key = field_name
                break
        if not key:
            continue
        rate = tax.get("rate_pct")
        flat[key] = float(rate) if rate is not None else None

    return flat


def _assemble(positions: list[dict]) -> dict:
    return {
        "country_code": "TUN",
        "country_name": "Tunisia",
        "source": "Douane Tunisienne — tarifweb (douane.gov.tn)",
        "source_url": "https://www.douane.gov.tn/tarifwebnew/getresultat.php",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Nomenclature NDP HS11",
            "Taxes import : DD, DC (Droit de Consommation), FODEC, TCL, TVA (19% std)",
            "Taxes export : prélèvements à l'export (si présents)",
            "Source: tarifweb douane.gov.tn",
        ],
        "positions": [_convert_position(p) for p in positions],
    }


async def _run(sample: bool, chapters: list[str] | None, max_per_chapter: int) -> list[dict]:
    Scraper = _load_scraper()
    scraper = Scraper()
    if sample:
        chs = chapters or ["01", "10", "27", "39", "72", "84", "87"]
        print(f"  Crawl échantillon : chapitres {chs} (max {max_per_chapter}/chap)")
        return await scraper.scrape_sample(chapters=chs, max_per_chapter=max_per_chapter)
    all_pos: list[dict] = []
    chs = chapters or [f"{i:02d}" for i in range(1, 98) if i != 77]
    for ch in chs:
        try:
            pos = await scraper.scrape_chapter(ch)
            all_pos.extend(pos)
            print(f"  ch {ch}: {len(pos)} positions (cumul {len(all_pos)})")
        except Exception as e:
            print(f"  ⚠ ch {ch}: {type(e).__name__}: {e}")
    return all_pos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="engine/sources/tun_raw.json")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--chapters", nargs="*", default=None)
    ap.add_argument("--max-per-chapter", type=int, default=5)
    args = ap.parse_args()

    print("=" * 64)
    print(" Crawl TUN (douane.gov.tn/tarifweb) → raw_crawl")
    print("=" * 64)
    _check_deps()

    positions = asyncio.run(_run(args.sample, args.chapters, args.max_per_chapter))
    if not positions:
        print("\n✗ Aucune position récupérée (site injoignable ou bloqué ?).")
        print("  Vérifiez l'accès réseau à https://www.douane.gov.tn/tarifweb2025/")
        sys.exit(1)

    out = _assemble(positions)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    dd_present = sum(1 for p in out["positions"] if p["dd_rate"] is not None)
    print(f"\n✅ {len(out['positions'])} positions écrites → {out_path}")
    print(f"   DD résolu : {dd_present}/{len(out['positions'])}")
    print("\n   Ingestion (avec garde-fous) :")
    print(f"     python engine/adapters/raw_crawl_adapter.py TUN {out_path} engine/output/")


if __name__ == "__main__":
    main()
