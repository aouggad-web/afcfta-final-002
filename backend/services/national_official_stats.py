"""
Statistiques officielles NATIONALES — registre piloté par la donnée
====================================================================
Bulletins des offices statistiques nationaux et des agences de promotion,
en complément des sources internationales (OEC/UN Comtrade, FAOSTAT, USGS,
UNIDO, UNSD, ILOSTAT).

POURQUOI CES SOURCES, ALORS QUE LES INTERNATIONALES COUVRENT DÉJÀ 54 PAYS
--------------------------------------------------------------------------
Parce que certaines distinctions ne sont pas servies au même niveau de détail
par les sources internationales — en premier lieu la séparation entre
**exportations domestiques** et **réexportations**, décisive pour les règles
d'origine ZLECAf : une marchandise réexportée depuis une zone franche
n'acquiert pas l'origine locale, seule la production ou la transformation
domestique peut y prétendre.

.. warning::

   Ce module a longtemps affirmé ici qu'« aucune source internationale ne
   publie cette ventilation ». **C'était faux**, et l'affirmation justifiait
   à elle seule une collecte office par office qui a rendu un pays sur cinq.
   UN Comtrade publie les flux ``DX`` / ``RX`` sur un endpoint SANS CLÉ, pour
   quatorze pays africains dont la ventilation réconcilie — voir
   ``etl/comtrade_export_split.py`` et son registre.

   Ce que cette couche-ci garde en propre, et que Comtrade ne donne pas à ce
   niveau : **la ventilation par produit et par marché**. Maurice en est la
   démonstration — son office la publie jusqu'au produit, et Comtrade ne
   réconcilie pas pour elle. Les deux couches sont complémentaires : l'une
   couvre plus de pays, l'autre descend plus bas.

REGISTRE, ET NON DICTIONNAIRE EN DUR
-------------------------------------
Les blocs vivent dans ``data/national_stats/<ISO3>.json`` et sont documentés
par ``docs/data-sources/<ISO3>_STATS_REGISTER.md``, sur le modèle des
registres de sources juridiques du dépôt : éditeur, publication, URL, année
des données, devise, empreinte. Ajouter un pays ne demande plus de toucher au
Python.

GARDE-FOUS « ZÉRO FABRICATION »
--------------------------------
- Les valeurs sont reprises TELLES QUE PUBLIÉES, dans la monnaie de
  publication (ex. millions de MUR pour Maurice) — aucune conversion USD
  maison, aucun chiffre complété, aucune agrégation inventée.
- Chaque bloc porte sa source. Un bloc incomplet est REFUSÉ au chargement
  plutôt que servi à moitié : voir ``_REQUIRED_SOURCE_FIELDS``.
- Le champ ``value`` est un nombre dans l'unité déclarée par la source ; il
  n'est comparable ni entre pays ni à un montant en USD sans conversion
  explicite, que cette couche ne fait pas.

QUAND LA VENTILATION N'EST PAS PUBLIABLE
-----------------------------------------
Certains pays ne publient pas la séparation, même en ayant des zones franches
très actives. Le bloc porte alors ``export_flow_caveat`` : l'avertissement
daté et la définition citée de la source, qui interdisent de lire un chiffre
d'export du pays comme de la production domestique. C'est un fait sourcé, pas
un chiffre reconstitué — voir ``docs/data-sources/TGO_STATS_REGISTER.md``, où
la tentative de recomposition est montrée en échec contre le total publié.

Premier pays intégré : Maurice (EDB, newsletter de juillet 2024).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

REGISTRY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "national_stats"

#: Sans l'un de ces champs, une entrée n'est pas vérifiable : elle est écartée.
#: Un chiffre dont on ne peut pas dire qui l'a publié, quand, et dans quelle
#: unité ne vaut pas mieux qu'un chiffre absent — il vaut moins, parce qu'il
#: inspire confiance.
#: ``unit`` en fait partie parce que ``grounding_lines`` l'injecte dans le
#: texte servi au modèle : l'omettre produirait « values in None ».
_REQUIRED_SOURCE_FIELDS = ("publisher", "publication", "url", "data_year", "currency", "unit")

_registry_cache: Optional[Dict[str, Dict]] = None


def _entry_is_valid(iso3: str, entry: object) -> bool:
    """Un bloc est-il assez vérifiable pour être servi ?

    Trois refus, dans cet ordre, parce qu'ils échouent différemment :

    * **forme.** Un JSON valide n'est pas un bloc valide : ``[]`` ou
      ``{"source": []}`` se chargent sans erreur puis font tomber la lecture
      plus loin. Le type est donc vérifié avant tout accès.
    * **provenance.** Sans éditeur, publication, URL, année, devise ou unité,
      le chiffre n'est pas vérifiable par un lecteur — et ``unit`` manquante
      se retrouverait telle quelle dans le texte servi au modèle.
    * **identité.** Le code porté par le fichier doit correspondre à son nom.
      Un bloc copié d'un pays à l'autre sans changer le code servirait les
      chiffres de l'un sous le nom de l'autre — l'erreur la plus difficile à
      repérer à l'écran, parce que rien n'a l'air cassé.
    """
    if not isinstance(entry, dict):
        logger.warning(
            "Statistiques nationales %s ignorées — le fichier ne contient pas un objet", iso3
        )
        return False

    source = entry.get("source")
    if not isinstance(source, dict):
        logger.warning(
            "Statistiques nationales %s ignorées — bloc « source » absent ou mal formé", iso3
        )
        return False

    missing = [f for f in _REQUIRED_SOURCE_FIELDS if not source.get(f)]
    if missing:
        logger.warning(
            "Statistiques nationales %s ignorées — champs de source manquants : %s",
            iso3,
            ", ".join(missing),
        )
        return False

    declared = entry.get("country_iso3")
    if not declared:
        logger.warning("Statistiques nationales %s ignorées — country_iso3 absent", iso3)
        return False
    if str(declared).strip().upper() != iso3:
        logger.warning(
            "Statistiques nationales %s ignorées — le fichier déclare %s : "
            "un bloc servi sous le nom d'un autre pays est pire qu'un bloc absent",
            iso3,
            declared,
        )
        return False
    return True


def load_registry(force: bool = False) -> Dict[str, Dict]:
    """{ISO3: bloc} depuis ``data/national_stats/``, entrées invalides écartées."""
    global _registry_cache
    if _registry_cache is not None and not force:
        return _registry_cache

    registry: Dict[str, Dict] = {}
    if REGISTRY_DIR.is_dir():
        for path in sorted(REGISTRY_DIR.glob("*.json")):
            iso3 = path.stem.upper()
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Statistiques nationales %s illisibles : %s", iso3, exc)
                continue
            if _entry_is_valid(iso3, entry):
                registry[iso3] = entry
    _registry_cache = registry
    return registry


def list_covered_countries() -> List[str]:
    """Codes ISO3 disposant d'un bloc de statistiques nationales."""
    return sorted(load_registry())


def get_official_stats(country_iso3: str) -> Optional[Dict]:
    """Bloc de statistiques officielles nationales pour un pays, s'il existe."""
    return load_registry().get((country_iso3 or "").strip().upper())


def _amount(value, unit_short: str) -> str:
    """Montant formaté dans l'unité PUBLIÉE, jamais convertie."""
    return f"{value:,} {unit_short}" if isinstance(value, (int, float)) else str(value)


def grounding_lines(country_iso3: str) -> List[str]:
    """
    Lignes prêtes à injecter dans un bloc VERIFIED REAL DATA de prompt LLM.
    Vide si aucune statistique officielle n'est intégrée pour ce pays.
    """
    stats = get_official_stats(country_iso3)
    if not stats:
        return []
    src = stats["source"]
    unit_short = src.get("unit_short") or src.get("currency", "")
    lines = [
        f"OFFICIAL NATIONAL STATISTICS FOR {stats['country_name']} "
        f"({src['publisher']}, {src['publication']}, data year {src['data_year']}, "
        f"values in {src['unit']} — LOCAL CURRENCY, not USD):"
    ]
    top = stats.get("top_domestic_export_product")
    if top:
        lines.append(
            f"- #1 DOMESTIC export product {src['data_year']}: {top['label']} "
            f"(HS {top['hs4']}), {_amount(top.get('value'), unit_short)}"
        )
    products = stats.get("domestic_export_products") or []
    if products:
        lines.append(
            "- Domestic export products (local processing, NOT re-exports): "
            + ", ".join(f"{p['label']} (HS {p['hs4']})" for p in products)
        )
    markets = stats.get("top_domestic_export_markets") or []
    if markets:
        lines.append(
            "- Top domestic export markets: "
            + ", ".join(f"{m['market']} ({m['share_pct']}%)" for m in markets[:6])
        )
    reexports = stats.get("top_reexport_markets") or []
    if reexports:
        lines.append(
            "- RE-EXPORTS are tracked SEPARATELY by the national source; top re-export "
            "markets: "
            + ", ".join(f"{m['market']} ({m['share_pct']}%)" for m in reexports[:5])
            + " — re-exported merchandise does NOT acquire local AfCFTA origin and must "
            "never be presented as domestic production or origin-qualifying supply."
        )
    caveat = stats.get("export_flow_caveat")
    if isinstance(caveat, dict):
        lines.append(
            f"- WARNING — the two flows are NOT separable for {stats['country_name']}: "
            f"the national source records total exports "
            f"({_amount(caveat.get('total_exports_fob'), unit_short)} in "
            f"{caveat.get('period')}) as domestic exports PLUS re-exports, and publishes "
            "no split by product or by market. No export figure for this country, from "
            "this source or from any international source derived from it, may be read "
            "as domestic production or as origin-qualifying supply. Source definition: "
            f"\u00ab\u00a0{caveat.get('source_definition')}\u00a0\u00bb"
        )
    zones = stats.get("free_zone_regimes") or []
    if zones:
        lines.append(
            "- Free-zone customs regimes, as published (values in "
            f"{src['unit']}): "
            + "; ".join(
                f"{z['label']} = {_amount(z.get('value'), unit_short)}" for z in zones
            )
            + " — goods merely entering and leaving a free zone are transformed there at "
            "most partially; free-zone outflows do not by themselves establish local "
            "origin."
        )
    return lines
