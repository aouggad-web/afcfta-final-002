#!/usr/bin/env python3
"""
Crawl CEMAC (6 pays) → fichier raw_crawl ingérable par le moteur tarifaire
===========================================================================
CEMAC = Communauté Économique et Monétaire de l'Afrique Centrale
6 membres : CMR, GAB, TCD, CAF, COG, GNQ
Tous appliquent le TEC CEEAC commun (depuis 2026-01-01) ; taxes nationales différentes

Ce runner charge `CemacTariffScraper` DIRECTEMENT (sans le package crawlers),
vérifie les dépendances, crawle les portails tarifaires nationaux, et convertit
la sortie au format « raw_crawl » plat du moteur (PROFILES[CMR/GAB/TCD/CAF/COG/GNQ]).

Le scraper CEMAC doit renvoyer par position :
    {hs_code, chapter, designation, taxes_import: [{code, rate_pct, raw_value,
     assiette}], taxes_export: [{code, rate_pct, ...}], ...}
On aplatit taxes_import/taxes_export en champs dd_rate / vat_rate (import),
export_levy_rate (export), etc. (taux lus du crawl, jamais inventés).

Dépendances :
    pip install httpx beautifulsoup4

Usage :
    python backend/scripts/crawl_cemac_to_raw.py --sample
    python backend/scripts/crawl_cemac_to_raw.py --countries CMR GAB --out engine/sources/cemac_raw.json

Ingestion (avec garde-fous) :
    python engine/adapters/raw_crawl_adapter.py CMR engine/sources/cemac_raw.json engine/output/
    python engine/adapters/raw_crawl_adapter.py GAB engine/sources/cemac_raw.json engine/output/
    (etc. pour les 6 membres)
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

# Membres CEMAC
CEMAC_MEMBERS = {
    "CMR": "Cameroon",
    "GAB": "Gabon",
    "TCD": "Chad",
    "CAF": "Central African Republic",
    "COG": "Republic of the Congo",
    "GNQ": "Equatorial Guinea",
}


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
    """Charge CemacTariffScraper SANS déclencher crawlers/__init__ (→ motor)."""
    path = BACKEND_DIR / "crawlers" / "countries" / "cemac_tariff_scraper.py"
    if not path.exists():
        print(f"✗ Scraper introuvable : {path}")
        print("  Le scraper CEMAC n'existe pas encore. Créer un crawler auprès des portails")
        print("  des douanes nationales (CMR, GAB, TCD, CAF, COG, GNQ).")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("cemac_tariff_scraper", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cemac_tariff_scraper"] = mod
    spec.loader.exec_module(mod)
    return mod.CemacTariffScraper


# ── Conversion taxes_import/taxes_export → champs plats ────────────────────

# Mappe un code de taxe CEMAC vers un champ plat (import)
_TAX_FIELD_IMPORT = {
    "DD": "dd_rate",
    "TPI": "tpi_rate",
    "TIC": "tic_rate",
    "VAT": "vat_rate",
    "TVA": "vat_rate",
}

# Mappe un code de taxe CEMAC vers un champ plat (export)
_TAX_FIELD_EXPORT = {
    "DD": "export_dd_rate",
    "PRÉLEV": "export_levy_rate",
    "LEVY": "export_levy_rate",
    "VAT": "export_vat_rate",
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
        "tpi_rate": None,
        "tic_rate": None,
        "vat_rate": None,
        # Côté export
        "export_dd_rate": None,
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


def _assemble(member: str, positions: list[dict]) -> dict:
    country_name = CEMAC_MEMBERS.get(member, member)
    return {
        "country_code": member,
        "country_name": country_name,
        "source": "CEMAC — Tarif Extérieur Commun CEEAC",
        "source_url": "https://www.cemac.int/",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Nomenclature HS2022",
            "Taxes import : DD (TEC CEEAC 0/5/10/20/30/40%), TPI, TIC, VAT",
            "Taxes export : prélèvements nationaux (si présents)",
            f"TEC CEEAC en vigueur depuis 2026-01-01 pour {country_name}",
            f"Source: CEMAC TEC CEEAC + douanes nationales {member}",
        ],
        "positions": [_convert_position(p) for p in positions],
    }


async def _run(sample: bool, countries: list[str] | None, max_per_chapter: int) -> dict[str, list]:
    """Crawle les pays CEMAC demandés."""
    try:
        Scraper = _load_scraper()
    except SystemExit:
        # Scraper n'existe pas — retourner crawl vide avec message
        return {}

    members = countries or list(CEMAC_MEMBERS.keys())
    result = {}

    for member in members:
        if member not in CEMAC_MEMBERS:
            print(f"  ⚠ {member}: non-membre CEMAC ignoré")
            continue

        scraper = Scraper(member)
        print(f"\n  Crawl {member} ({CEMAC_MEMBERS[member]})...")

        try:
            if sample:
                chs = ["01", "10", "27", "39", "72", "84", "87"]
                print(f"    Échantillon : chapitres {chs} (max {max_per_chapter}/chap)")
                positions = await scraper.scrape_sample(
                    chapters=chs, max_per_chapter=max_per_chapter
                )
            else:
                all_pos: list[dict] = []
                chs = [f"{i:02d}" for i in range(1, 98) if i != 77]
                for ch in chs:
                    try:
                        pos = await scraper.scrape_chapter(ch)
                        all_pos.extend(pos)
                        print(f"    ch {ch}: {len(pos)} positions (cumul {len(all_pos)})")
                    except Exception as e:
                        print(f"    ⚠ ch {ch}: {type(e).__name__}: {e}")
                positions = all_pos

            if positions:
                result[member] = positions
                print(f"  → {member}: {len(positions)} positions crawlées")
            else:
                print(f"  ⚠ {member}: aucune position récupérée")
        except Exception as e:
            print(f"  ✗ {member}: {type(e).__name__}: {e}")

    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="engine/sources/cemac_raw.json")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument(
        "--countries",
        nargs="+",
        choices=list(CEMAC_MEMBERS.keys()),
        default=None,
        help="Membres CEMAC à crawler (défaut : tous)",
    )
    ap.add_argument("--max-per-chapter", type=int, default=5)
    args = ap.parse_args()

    print("=" * 64)
    print(" Crawl CEMAC (6 pays) → raw_crawl avec support export")
    print("=" * 64)
    _check_deps()

    all_crawls = asyncio.run(_run(args.sample, args.countries, args.max_per_chapter))

    if not all_crawls:
        print("\n✗ Aucune position crawlée pour aucun membre.")
        print("  Vérifier l'accès réseau aux portails douaniers CEMAC.")
        sys.exit(1)

    # Assembler un fichier multi-pays ou par pays
    # Pour simplicité : un fichier par pays
    out_dir = Path(args.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    for member, positions in all_crawls.items():
        out_data = _assemble(member, positions)
        # Chemins alternatifs : {out}/cemac_raw.json ou {out}/{member}_raw.json
        if len(all_crawls) == 1:
            out_path = Path(args.out)
        else:
            out_path = out_dir / f"{member}_raw.json"

        out_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")

        dd_present = sum(1 for p in out_data["positions"] if p["dd_rate"] is not None)
        print(f"\n✅ {member}: {len(out_data['positions'])} positions écrites → {out_path}")
        print(f"   DD résolu : {dd_present}/{len(out_data['positions'])}")

    print("\n   Ingestion (avec garde-fous) :")
    for member in all_crawls.keys():
        if len(all_crawls) == 1:
            crawl_path = Path(args.out)
        else:
            crawl_path = out_dir / f"{member}_raw.json"
        print(
            f"     python engine/adapters/raw_crawl_adapter.py {member} {crawl_path} engine/output/"
        )


if __name__ == "__main__":
    main()
