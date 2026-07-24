#!/usr/bin/env python3
"""
Seed the AI analysis cache for all 54 AfCFTA countries.

Generates analyses once using the Claude API (Haiku model = ~10x cheaper),
stores them in backend/data/ai_cache/ as JSON files with 90-day TTL.
Commit those files to git → Emergent deployment serves everything from cache
with ZERO ongoing API costs.

Usage:
    # Dry-run (cost estimate only, no API calls):
    python3 seed_ai_cache.py --dry-run

    # Seed with Haiku (cheap, ~$2-4 total):
    ANTHROPIC_API_KEY=sk-ant-... CLAUDE_BULK_MODE=true python3 seed_ai_cache.py

    # Seed specific country only:
    ANTHROPIC_API_KEY=sk-ant-... CLAUDE_BULK_MODE=true python3 seed_ai_cache.py --country Algeria

    # Seed only missing (skip already cached entries):
    ANTHROPIC_API_KEY=sk-ant-... CLAUDE_BULK_MODE=true python3 seed_ai_cache.py --skip-existing

    # Resume after partial run:
    ANTHROPIC_API_KEY=sk-ant-... CLAUDE_BULK_MODE=true python3 seed_ai_cache.py --skip-existing --modes export,import

Cost estimate (Haiku, Dec 2024 pricing):
    - Per call: ~1500 input tokens × $0.80/MTok + ~3500 output tokens × $4/MTok = $0.015
    - 54 countries × 3 modes × 2 langs = 324 calls × $0.015 = ~$4.86 total
    - Value chains (6 sectors × 2 langs) = 12 calls × $0.015 = ~$0.18
    TOTAL ONE-TIME COST: ~$5
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("CLAUDE_BULK_MODE", "true")

from services.claude_trade_service import claude_trade_service
from services.redis_cache_service import CACHE_TTL, cache_service

# ── 54 AfCFTA countries ────────────────────────────────────────────────────────
COUNTRIES_EN = [
    ("DZA", "Algeria"),
    ("AGO", "Angola"),
    ("BEN", "Benin"),
    ("BWA", "Botswana"),
    ("BFA", "Burkina Faso"),
    ("BDI", "Burundi"),
    ("CMR", "Cameroon"),
    ("CPV", "Cabo Verde"),
    ("CAF", "Central African Republic"),
    ("TCD", "Chad"),
    ("COM", "Comoros"),
    ("COG", "Republic of Congo"),
    ("COD", "DR Congo"),
    ("DJI", "Djibouti"),
    ("EGY", "Egypt"),
    ("GNQ", "Equatorial Guinea"),
    ("ERI", "Eritrea"),
    ("SWZ", "Eswatini"),
    ("ETH", "Ethiopia"),
    ("GAB", "Gabon"),
    ("GMB", "Gambia"),
    ("GHA", "Ghana"),
    ("GIN", "Guinea"),
    ("GNB", "Guinea-Bissau"),
    ("CIV", "Ivory Coast"),
    ("KEN", "Kenya"),
    ("LSO", "Lesotho"),
    ("LBR", "Liberia"),
    ("LBY", "Libya"),
    ("MDG", "Madagascar"),
    ("MWI", "Malawi"),
    ("MLI", "Mali"),
    ("MRT", "Mauritania"),
    ("MUS", "Mauritius"),
    ("MAR", "Morocco"),
    ("MOZ", "Mozambique"),
    ("NAM", "Namibia"),
    ("NER", "Niger"),
    ("NGA", "Nigeria"),
    ("RWA", "Rwanda"),
    ("STP", "Sao Tome and Principe"),
    ("SEN", "Senegal"),
    ("SLE", "Sierra Leone"),
    ("SOM", "Somalia"),
    ("ZAF", "South Africa"),
    ("SSD", "South Sudan"),
    ("SDN", "Sudan"),
    ("TZA", "Tanzania"),
    ("TGO", "Togo"),
    ("TUN", "Tunisia"),
    ("UGA", "Uganda"),
    ("ZMB", "Zambia"),
    ("ZWE", "Zimbabwe"),
]

MODES = ["export", "import", "industrial"]
LANGS = ["fr", "en"]
VALUE_CHAIN_SECTORS = ["coffee", "cocoa", "cotton", "minerals", "petroleum", "automotive"]


def estimate_cost(n_countries, modes, langs, sectors):
    """Rough cost estimate using Haiku pricing."""
    # Haiku: $0.80/MTok input, $4/MTok output
    # Per call: ~1500 input + ~3500 output tokens
    per_call = (1500 * 0.80 + 3500 * 4.0) / 1_000_000
    n_analysis = n_countries * len(modes) * len(langs)
    n_sectors = len(sectors) * len(langs)
    n_summary = len(langs)
    total_calls = n_analysis + n_sectors + n_summary
    return total_calls, total_calls * per_call


def check_cached(country_name, mode, lang):
    """Returns True if this combination is already cached."""
    params = {"country": country_name, "mode": mode, "lang": lang}
    return cache_service.get("claude_analysis", params) is not None


async def seed_country(
    country_name: str, modes: list, langs: list, skip_existing: bool, stats: dict
):
    for mode in modes:
        for lang in langs:
            key = f"{country_name}/{mode}/{lang}"
            if skip_existing and check_cached(country_name, mode, lang):
                print(f"  SKIP (cached): {key}")
                stats["skipped"] += 1
                continue
            try:
                t0 = time.time()
                result = await claude_trade_service.analyze_trade_opportunities(
                    country_name=country_name, mode=mode, lang=lang
                )
                elapsed = time.time() - t0
                n_opps = len(result.get("opportunities", []))
                model = result.get("generated_by", "?")
                print(f"  OK  ({elapsed:.1f}s, {n_opps} opps): {key}  [{model}]")
                stats["done"] += 1
            except Exception as e:
                print(f"  ERR: {key} — {e}")
                stats["errors"] += 1
            # Respect rate limits (Haiku: 50 req/min free tier)
            await asyncio.sleep(1.2)


async def seed_value_chains(sectors: list, langs: list, skip_existing: bool, stats: dict):
    for sector in sectors:
        for lang in langs:
            params = {"sector": sector, "lang": lang}
            if skip_existing and cache_service.get("claude_value_chains", params):
                print(f"  SKIP (cached): value_chains/{sector}/{lang}")
                stats["skipped"] += 1
                continue
            try:
                t0 = time.time()
                await claude_trade_service.get_value_chains_analysis(sector=sector, lang=lang)
                print(f"  OK  ({time.time()-t0:.1f}s): value_chains/{sector}/{lang}")
                stats["done"] += 1
            except Exception as e:
                print(f"  ERR: value_chains/{sector}/{lang} — {e}")
                stats["errors"] += 1
            await asyncio.sleep(1.2)


async def main():
    parser = argparse.ArgumentParser(description="Seed AfCFTA AI analysis cache")
    parser.add_argument("--dry-run", action="store_true", help="Cost estimate only, no API calls")
    parser.add_argument("--skip-existing", action="store_true", help="Skip already-cached entries")
    parser.add_argument("--country", default=None, help="Seed single country (English name)")
    parser.add_argument("--modes", default="export,import,industrial", help="Comma-separated modes")
    parser.add_argument("--langs", default="fr,en", help="Comma-separated langs")
    parser.add_argument("--no-value-chains", action="store_true", help="Skip value chains seeding")
    args = parser.parse_args()

    selected_modes = args.modes.split(",")
    selected_langs = args.langs.split(",")

    if args.country:
        countries = [
            (iso3, name) for iso3, name in COUNTRIES_EN if name.lower() == args.country.lower()
        ]
        if not countries:
            print(
                f"ERROR: country '{args.country}' not found. Use exact English name from COUNTRIES_EN list."
            )
            sys.exit(1)
    else:
        countries = COUNTRIES_EN

    total_calls, cost = estimate_cost(
        len(countries), selected_modes, selected_langs, VALUE_CHAIN_SECTORS
    )

    print("=" * 60)
    print(f"AfCFTA AI Cache Seeder — Model: {claude_trade_service.MODEL}")
    print("=" * 60)
    print(f"Countries  : {len(countries)}")
    print(f"Modes      : {selected_modes}")
    print(f"Languages  : {selected_langs}")
    print(f"Total calls: ~{total_calls}")
    print(f"Est. cost  : ~${cost:.2f} (Haiku pricing)")
    print(f"Cache dir  : {cache_service._file.cache_dir}")
    print(f"Cache TTL  : {CACHE_TTL.get('claude_analysis', 0) // 86400} days")
    print("=" * 60)

    if args.dry_run:
        print("\nDRY RUN — no API calls made.")
        print("Run without --dry-run to proceed.")
        return

    if not claude_trade_service._is_ready():
        print("\nERROR: ANTHROPIC_API_KEY not set.")
        print("Export it: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    stats = {"done": 0, "skipped": 0, "errors": 0}
    t_start = time.time()

    # ── Countries ──
    for i, (iso3, name) in enumerate(countries):
        print(f"\n[{i+1}/{len(countries)}] {name} ({iso3})")
        await seed_country(name, selected_modes, selected_langs, args.skip_existing, stats)

    # ── Value chains ──
    if not args.no_value_chains:
        print(f"\n[Value Chains] 6 sectors × {len(selected_langs)} langs")
        await seed_value_chains(VALUE_CHAIN_SECTORS, selected_langs, args.skip_existing, stats)

    elapsed = time.time() - t_start
    cache_files = list(cache_service._file.cache_dir.glob("claude_*.json"))

    print("\n" + "=" * 60)
    print(f"DONE in {elapsed/60:.1f} min")
    print(f"  Generated : {stats['done']} entries")
    print(f"  Skipped   : {stats['skipped']} (already cached)")
    print(f"  Errors    : {stats['errors']}")
    print(
        f"  Cache files: {len(cache_files)} claude_*.json in {cache_service._json_cache.cache_dir}"
    )
    print("\nNext step: commit cache files to git so Emergent deploys with pre-populated cache:")
    print(f"  git add backend/data/ai_cache/claude_*.json")
    print(f"  git commit -m 'data: pre-seed Claude AI cache — 54 countries × 3 modes'")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
