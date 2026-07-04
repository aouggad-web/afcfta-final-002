"""
Runner CLI du moteur de crawl Scrapling — un pays par exécution.

    python -m crawlers.scrapling_engine.runner --country DZA \
        [--max-positions 200] [--out data/crawled/DZA_tariffs.json]

Charge la spec du pays (crawlers/scrapling_engine/specs/{iso3}.py) qui expose :

    COUNTRY_NAME: str
    SOURCE: str                      # portail officiel (attribution)
    CALCULATION_RULES: dict          # contrat v2 §4 (assiettes, ordre, références)
    def crawl(max_positions=None) -> list[dict]   # positions brutes

Le runner normalise (contrat v2), assemble et écrit le JSON. Zéro fabrication :
la spec ne retourne que ce que la source publie ; le gate (quality_gate.py)
valide AVANT toute publication.

S1 : squelette (aucune spec livrée) — la spec DZA arrive en S2 (étalonnage).
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from crawlers.scrapling_engine.normalizer import assemble_output

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT_DIR = BACKEND_DIR / "data" / "crawled"


def load_spec(country_iso3: str):
    module_name = f"crawlers.scrapling_engine.specs.{country_iso3.lower()}"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        available = sorted(
            p.stem.upper()
            for p in (Path(__file__).parent / "specs").glob("[a-z]*.py")
            if p.stem != "__init__"
        )
        print(
            f"✗ Aucune spec pour {country_iso3.upper()} ({module_name}).\n"
            f"  Specs disponibles : {available or 'aucune (S1 : squelette)'}\n"
            f"  Écrire crawlers/scrapling_engine/specs/{country_iso3.lower()}.py "
            f"(voir docs/PLAN_SCRAPLING_CRAWLERS.md §3).",
            file=sys.stderr,
        )
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Crawl Scrapling des tarifs douaniers (1 pays)")
    ap.add_argument("--country", required=True, help="ISO3 (ex. DZA)")
    ap.add_argument("--max-positions", type=int, default=None, help="Borne pour les essais")
    ap.add_argument("--out", type=Path, default=None, help="Chemin de sortie JSON")
    args = ap.parse_args()

    iso3 = args.country.upper()
    spec = load_spec(iso3)
    if spec is None:
        return 2

    print(f"— Crawl {iso3} ({spec.COUNTRY_NAME}) — source : {spec.SOURCE}")
    positions = spec.crawl(max_positions=args.max_positions)
    if not positions:
        print("✗ Aucune position extraite — rien n'est écrit (zéro fabrication).")
        return 1

    output = assemble_output(
        country=iso3,
        country_name=spec.COUNTRY_NAME,
        source=spec.SOURCE,
        sub_positions=positions,
        calculation_rules=getattr(spec, "CALCULATION_RULES", None),
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )

    out_path = args.out or (DEFAULT_OUT_DIR / f"{iso3}_tariffs.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=1)
    stats = output["stats"]
    print(
        f"✅ Écrit {out_path} — {stats['sub_positions']} positions, "
        f"{stats['chapters']} chapitres, régimes : "
        f"{[r['code'] for r in output['regimes_registry'][:8]]}"
    )
    print(
        "→ Passer le gate : python -m crawlers.scrapling_engine.quality_gate "
        f"--candidate {out_path} [--reference …] [--pivots …]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
