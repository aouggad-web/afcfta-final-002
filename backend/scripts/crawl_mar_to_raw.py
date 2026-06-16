#!/usr/bin/env python3
"""
Crawl MAR (Maroc) → fichier raw_crawl ingérable par le moteur tarifaire
=======================================================================
Pourquoi ce script ?
--------------------
Le crawler MAR intégré (`services/crawlers/mar_tariff_crawler.py`) importe la
chaîne `crawlers/__init__.py` qui dépend de `motor` (MongoDB). Sur une machine
de dev (VSCode) sans MongoDB, l'import échoue AVANT même d'atteindre le réseau :

    ModuleNotFoundError: No module named 'motor'

Ce script contourne le problème : il charge le scraper `MoroccoDouaneScraper`
DIRECTEMENT (sans passer par le package `crawlers`), vérifie les dépendances
réseau, lance le crawl du portail ADIL (douane.gov.ma), puis convertit la
sortie au format « raw_crawl » plat attendu par
`engine/adapters/raw_crawl_adapter.py` (profil PROFILES["MAR"]).

Dépendances (à installer sur VSCode) :
    pip install httpx beautifulsoup4

Usage :
    # Échantillon rapide (quelques chapitres) pour valider la chaîne
    python backend/scripts/crawl_mar_to_raw.py --sample

    # Crawl complet (96 chapitres — long, site ASP lent + rate-limit 2s)
    python backend/scripts/crawl_mar_to_raw.py --out engine/sources/mar_raw.json

Puis ingestion (avec garde-fous anti-données-génériques) :
    python engine/adapters/raw_crawl_adapter.py MAR engine/sources/mar_raw.json engine/output/
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import re
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
        print("  Installez-les puis relancez :")
        print(f"    pip install {' '.join(missing)}")
        sys.exit(2)


def _load_scraper():
    """Charge MoroccoDouaneScraper SANS déclencher crawlers/__init__ (→ motor)."""
    path = BACKEND_DIR / "crawlers" / "countries" / "morocco_douane_scraper.py"
    if not path.exists():
        print(f"✗ Scraper introuvable : {path}")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("morocco_douane_scraper", path)
    mod = importlib.util.module_from_spec(spec)
    # Empêche l'exécution de crawlers/__init__ si le module y fait référence
    sys.modules["morocco_douane_scraper"] = mod
    spec.loader.exec_module(mod)
    return mod.MoroccoDouaneScraper


# ── Conversion sortie scraper → format raw_crawl plat ───────────────────────

_PCT_RE = re.compile(r"([\d]+(?:[.,]\d+)?)\s*%")


def _pct(value: str | None) -> tuple[float | None, str]:
    """Extrait un % d'une valeur type '10 %' → (10.0, '10 %'). Sinon (None, brut)."""
    if not value:
        return None, ""
    m = _PCT_RE.search(value)
    if m:
        return float(m.group(1).replace(",", ".")), value.strip()
    return None, value.strip()  # ex. 'X DH' (spécifique) → non réduit


def _convert_position(p: dict) -> dict:
    """Mappe {code, designation, taxes:{...}} → champs plats raw_crawl."""
    taxes = p.get("taxes", {}) or {}
    # Récupère par sous-chaîne de clé (robuste aux variations de libellé)
    def find(key_part: str) -> str | None:
        for k, v in taxes.items():
            if key_part.lower() in k.lower():
                return v
        return None

    dd, dd_raw = _pct(find("Droit d'Importation") or find("(DI)") or find("(DD)"))
    tpi, _ = _pct(find("Parafiscale") or find("(TPI)"))
    tva, _ = _pct(find("Valeur Ajout") or find("(TVA)"))
    tic, tic_raw = _pct(find("Consommation") or find("(TIC)"))

    code = str(p.get("code", "")).strip()
    return {
        "code": code,
        "description_en": p.get("designation", ""),
        "dd_rate": dd,
        "dd_rate_raw": dd_raw,
        "tpi_rate": tpi,
        "vat_rate": tva,
        "tic_rate": tic,
        "tic_rate_raw": tic_raw,
        "chapter": code[:2] if len(code) >= 2 else "",
        "digits": len(code),
        "formalities": p.get("formalities", []),
    }


def _assemble(positions: list[dict]) -> dict:
    return {
        "country_code": "MAR",
        "country_name": "Morocco",
        "source": "Douane Maroc (ADII) — portail ADIL",
        "source_url": "https://www.douane.gov.ma/adil/",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Nomenclature NTS HS10",
            "Taxes : DD (Droit d'Importation), TPI, TIC, TVA (20% std)",
            "Source: portail ADIL douane.gov.ma",
        ],
        "positions": [_convert_position(p) for p in positions],
    }


async def _run(sample: bool, chapters: list[str] | None,
               max_per_chapter: int) -> list[dict]:
    Scraper = _load_scraper()
    scraper = Scraper()
    if sample:
        chs = chapters or ["01", "04", "10", "17", "27", "30", "39", "72", "84", "87"]
        print(f"  Crawl échantillon : chapitres {chs} (max {max_per_chapter}/chap)")
        return await scraper.scrape_sample(chapters=chs, max_per_chapter=max_per_chapter)
    # Crawl complet
    all_pos: list[dict] = []
    chs = chapters or [f"{i:02d}" for i in range(1, 98) if i != 77]
    for ch in chs:
        try:
            pos = await scraper.scrape_chapter_with_taxes(ch)
            all_pos.extend(pos)
            print(f"  ch {ch}: {len(pos)} positions (cumul {len(all_pos)})")
        except Exception as e:  # réseau instable : on continue
            print(f"  ⚠ ch {ch}: {type(e).__name__}: {e}")
    return all_pos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="engine/sources/mar_raw.json",
                    help="Fichier de sortie raw_crawl")
    ap.add_argument("--sample", action="store_true",
                    help="Crawl d'échantillon rapide (validation de la chaîne)")
    ap.add_argument("--chapters", nargs="*", default=None,
                    help="Liste de chapitres (ex. 01 27 84)")
    ap.add_argument("--max-per-chapter", type=int, default=5)
    args = ap.parse_args()

    print("=" * 64)
    print(" Crawl MAR (douane.gov.ma/ADIL) → raw_crawl")
    print("=" * 64)
    _check_deps()

    positions = asyncio.run(_run(args.sample, args.chapters, args.max_per_chapter))
    if not positions:
        print("\n✗ Aucune position récupérée (site injoignable ou bloqué ?).")
        print("  Vérifiez l'accès réseau à https://www.douane.gov.ma/adil/")
        sys.exit(1)

    out = _assemble(positions)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    dd_present = sum(1 for p in out["positions"] if p["dd_rate"] is not None)
    print(f"\n✅ {len(out['positions'])} positions écrites → {out_path}")
    print(f"   DD résolu : {dd_present}/{len(out['positions'])}")
    print("\n   Ingestion (avec garde-fous) :")
    print(f"     python engine/adapters/raw_crawl_adapter.py MAR {out_path} engine/output/")


if __name__ == "__main__":
    main()
