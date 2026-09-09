"""
Registre des crawlers authentiques branchés sur le pipeline.

Chaque crawler est une fonction sans argument qui réalise la collecte (réseau)
et renvoie un document canonique prêt à valider (voir canonical.build_file).

Point de branchement progressif : on enregistre ici un crawler par pays au fur
et à mesure de leur implémentation/validation. Tant qu'un pays n'a pas de
crawler authentique, le runner le SKIP — il ne produit jamais d'estimation.

Important : ce module ne doit PAS importer `motor`/MongoDB ni le package
`crawlers/` (dont l'__init__ tire `motor`), afin de rester exécutable sur une
machine de crawl ordinaire. Les scrapers réseau réels sont chargés en import
tardif à l'intérieur de leur fonction enregistrée.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

# iso3 -> callable() -> document canonique (dict)
AUTHENTIC_CRAWLERS: Dict[str, Callable[[], Dict[str, Any]]] = {}


def register(iso3: str) -> Callable[[Callable[[], Dict[str, Any]]], Callable[[], Dict[str, Any]]]:
    """Décorateur d'enregistrement d'un crawler authentique pour un pays."""

    def _wrap(fn: Callable[[], Dict[str, Any]]) -> Callable[[], Dict[str, Any]]:
        AUTHENTIC_CRAWLERS[iso3.upper()] = fn
        return fn

    return _wrap


# ---------------------------------------------------------------------------
# Les crawlers réseau réels s'enregistrent ici via @register("XXX").
# Exemple (à activer sur un environnement avec réseau + dépendances httpx/bs4) :
#
#   @register("MAR")
#   def crawl_mar() -> dict:
#       from tariff_crawl.adapters.mar import scrape_adil
#       positions = scrape_adil()              # accès réseau réel
#       return build_file("MAR", "Maroc",
#                         provenance=Provenance.NATIONAL_CRAWL.value,
#                         source="douane.gov.ma/adil",
#                         source_url="https://www.douane.gov.ma",
#                         positions=positions)
#
# Aucun crawler n'est branché par défaut : le pipeline reste honnête (skip
# plutôt qu'inventer) tant que la collecte authentique n'est pas implémentée.
# ---------------------------------------------------------------------------
