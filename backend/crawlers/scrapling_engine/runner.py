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


def _wits_spec(iso3: str):
    """Spec synthétique adossée à WITS/TRAINS (couverture SH6 multi-pays) —
    utilisée quand aucune spec nationale dédiée n'existe et que --source wits
    est demandé. Voir wits_source.py (nature SH6, DD seul, sans couche nationale)."""
    from crawlers.scrapling_engine import wits_source

    class _Spec:
        COUNTRY_NAME = wits_source.COUNTRY_NAMES.get(iso3.upper(), iso3.upper())
        SOURCE = wits_source.SOURCE
        CALCULATION_RULES = {
            "order": ["DD"],
            "bases": {"DD": {"basis": "CIF", "type": "ad_valorem"}},
            "source": "MFN appliqué SH6 (WITS/TRAINS) — couche nationale non couverte par cette source.",
        }

        @staticmethod
        def crawl(max_positions=None):
            return wits_source.crawl(iso3, max_positions=max_positions)

    return _Spec


def main() -> int:
    ap = argparse.ArgumentParser(description="Crawl Scrapling des tarifs douaniers (1 pays)")
    ap.add_argument("--country", required=True, help="ISO3 (ex. DZA)")
    ap.add_argument("--max-positions", type=int, default=None, help="Borne pour les essais")
    ap.add_argument("--out", type=Path, default=None, help="Chemin de sortie JSON")
    ap.add_argument(
        "--source",
        choices=["spec", "wits"],
        default="spec",
        help="spec = portail national dédié ; wits = WITS/TRAINS (SH6, DD seul).",
    )
    args = ap.parse_args()

    iso3 = args.country.upper()
    spec = _wits_spec(iso3) if args.source == "wits" else load_spec(iso3)
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
