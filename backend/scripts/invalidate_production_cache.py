#!/usr/bin/env python3
"""
Invalidation du cache des analyses dépendant des données de production
======================================================================
À exécuter après une reconstruction de data/json/production_africaine.json
(build_production_real.py ou build_production_faostat_usgs.py).

Contexte
--------
Les analyses « opportunités » (mode export / industrial) sont enrichies des
capacités de production réelles (FAO/USGS/UNIDO) puis mises en cache (Redis +
fallback fichier JSON) avec un TTL de 90 jours. Un stamp de version des données
(`pdv`) est désormais inclus dans la clé de cache : tout rebuild change ce stamp
et rend automatiquement inaccessibles les analyses obsolètes (elles expirent
ensuite par TTL).

Ce script effectue en plus une PURGE explicite immédiate des entrées
`claude_analysis` (et, en option, des analyses produit/chaînes de valeur) afin
de :
  • supprimer les entrées « héritées » mises en cache AVANT l'introduction du
    stamp (qui resteraient sinon orphelines jusqu'à expiration) ;
  • forcer une régénération immédiate avec les nouvelles capacités de production.

Usage
-----
    python3 scripts/invalidate_production_cache.py            # purge claude_analysis
    python3 scripts/invalidate_production_cache.py --all      # + product + value_chains
    python3 scripts/invalidate_production_cache.py --dry-run  # affiche seulement
    python3 scripts/invalidate_production_cache.py --stats    # stats cache only
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.redis_cache_service import cache_service  # noqa: E402

# Préfixes de cache potentiellement impactés par les données de production.
# claude_analysis : opportunités export/industrial (enrichies production_capacity).
# Les autres ne portent pas de production_capacity embarquée mais sont proposés
# en option (--all) pour une régénération complète.
CORE_PREFIXES = ["claude_analysis"]
OPTIONAL_PREFIXES = ["claude_product", "claude_value_chains"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--all", action="store_true", help="Inclure aussi claude_product et claude_value_chains"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Afficher ce qui serait invalidé sans rien supprimer"
    )
    ap.add_argument(
        "--stats", action="store_true", help="Afficher les statistiques de cache et quitter"
    )
    args = ap.parse_args()

    print("=" * 64)
    print(" Invalidation du cache des analyses (capacités de production)")
    print("=" * 64)

    # Version courante du dataset (informatif)
    try:
        from production_data import get_production_data_version

        print(f"\n  Version dataset production (pdv) : {get_production_data_version()}")
    except Exception as e:
        print(f"\n  ⚠ Version dataset indisponible : {e}")

    stats = cache_service.get_stats()
    print(f"  Backend actif : {stats.get('active_backend', '?')}")
    redis_stats = stats.get("redis", {})
    file_stats = stats.get("json_file", {})
    if redis_stats.get("status") == "connected":
        print(f"  Redis  : {redis_stats.get('total_zlecaf_keys', 0)} clés zlecaf")
    else:
        print(f"  Redis  : {redis_stats.get('status', 'n/a')}")
    print(
        f"  Fichier: {file_stats.get('total_files', 0)} fichiers "
        f"({file_stats.get('active_entries', 0)} actifs)"
    )

    if args.stats:
        return 0

    prefixes = CORE_PREFIXES + (OPTIONAL_PREFIXES if args.all else [])
    print(f"\n  Préfixes ciblés : {', '.join(prefixes)}")

    if args.dry_run:
        print("\n  (--dry-run) Aucune entrée supprimée.")
        return 0

    total = 0
    for prefix in prefixes:
        n = cache_service.invalidate_pattern(prefix)
        print(f"    • {prefix:24s} → {n} entrée(s) invalidée(s)")
        total += n

    print(f"\n✅ {total} entrée(s) de cache invalidée(s).")
    print(
        "   Les prochaines requêtes régénéreront les analyses avec les "
        "capacités de production à jour."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
