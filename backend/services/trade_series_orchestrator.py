"""
Orchestrateur résilient de séries temporelles commerciales
==========================================================
Objectif: ne jamais "tomber en rade" en production si OEC est indisponible
ou rate-limité, en essayant plusieurs sources dans l'ordre de priorité.

Chaîne de résilience (combinée au cache + stale-on-error de cache_service):
    1. OEC / BACI  (source primaire — riche, mise en cache)
    2. UN Comtrade (secours, OPT-IN: COMTRADE_FALLBACK_ENABLED=true + clé API)

Propriétés:
- Chaque source est isolée: une source qui échoue (exception / pas de données)
  n'interrompt pas la chaîne, on passe à la suivante.
- Dégradation propre: si aucune source n'a de données, on renvoie une
  structure valide (has_data=False) plutôt qu'une erreur → l'endpoint ne 500 pas.
- Transparence: la réponse indique `source_used` et `sources_tried`.

La logique d'orchestration est pure/testable (providers injectables).
Le mapping live Comtrade est opt-in et doit être validé en environnement réseau.
"""

import logging
import os
from typing import Awaitable, Callable, Dict, List, Optional

from services.oec_trade_service import AFRICAN_COUNTRIES_OEC, DEFAULT_YEAR, oec_service

logger = logging.getLogger(__name__)

# Un provider: async (iso3, start_year, end_year) -> dict|None
# Le dict doit contenir au minimum: chart_rows: [{year, exports, imports, balance}]
# et has_data: bool. Retourne None (ou lève) s'il ne peut pas fournir.
Provider = Callable[[str, int, int], Awaitable[Optional[Dict]]]


# ---------------------------------------------------------------------------
# Mapping ISO3 -> code numérique M49 (UN Comtrade) pour les pays africains
# ---------------------------------------------------------------------------
AFRICAN_ISO3_TO_M49: Dict[str, str] = {
    "DZA": "12",
    "AGO": "24",
    "BEN": "204",
    "BWA": "72",
    "BFA": "854",
    "BDI": "108",
    "CPV": "132",
    "CMR": "120",
    "CAF": "140",
    "TCD": "148",
    "COM": "174",
    "COG": "178",
    "COD": "180",
    "CIV": "384",
    "DJI": "262",
    "EGY": "818",
    "GNQ": "226",
    "ERI": "232",
    "SWZ": "748",
    "ETH": "231",
    "GAB": "266",
    "GMB": "270",
    "GHA": "288",
    "GIN": "324",
    "GNB": "624",
    "KEN": "404",
    "LSO": "426",
    "LBR": "430",
    "LBY": "434",
    "MDG": "450",
    "MWI": "454",
    "MLI": "466",
    "MRT": "478",
    "MUS": "480",
    "MAR": "504",
    "MOZ": "508",
    "NAM": "516",
    "NER": "562",
    "NGA": "566",
    "RWA": "646",
    "STP": "678",
    "SEN": "686",
    "SYC": "690",
    "SLE": "694",
    "SOM": "706",
    "ZAF": "710",
    "SSD": "728",
    "SDN": "729",
    "TZA": "834",
    "TGO": "768",
    "TUN": "788",
    "UGA": "800",
    "ZMB": "894",
    "ZWE": "716",
}


def aggregate_comtrade_series(records: Optional[List[Dict]], years: List[int]) -> List[Dict]:
    """
    Agrège des enregistrements UN Comtrade (partenaire = Monde) en une série
    exports/imports/balance par année. Fonction pure (testable).

    Comtrade: flowCode 'X' = exports, 'M' = imports; primaryValue = valeur USD;
    period = année.
    """
    exp = {y: 0.0 for y in years}
    imp = {y: 0.0 for y in years}
    for row in records or []:
        try:
            year = int(row.get("period") or 0)
        except (TypeError, ValueError):
            continue
        if year not in exp:
            continue
        flow = str(row.get("flowCode") or "").upper()
        value = float(row.get("primaryValue") or 0)
        if flow == "X":
            exp[year] += value
        elif flow == "M":
            imp[year] += value

    series = []
    for year in years:
        e = round(exp[year], 2)
        i = round(imp[year], 2)
        series.append({"year": year, "exports": e, "imports": i, "balance": round(e - i, 2)})
    return series


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
async def _oec_provider(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """Source primaire OEC (mise en cache + stale-on-error en aval)."""
    result = await oec_service.get_country_trade_series(iso3, start_year, end_year)
    if not result or result.get("error") or not result.get("has_data"):
        return None
    result["source_used"] = "OEC / BACI"
    return result


async def _comtrade_provider(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """
    Secours UN Comtrade — OPT-IN (COMTRADE_FALLBACK_ENABLED=true + clé API).
    Désactivé par défaut: à valider en environnement réseau avant activation,
    pour éviter de servir des données mal mappées.
    """
    if os.environ.get("COMTRADE_FALLBACK_ENABLED", "false").lower() != "true":
        return None
    reporter = AFRICAN_ISO3_TO_M49.get(iso3.upper())
    if not reporter:
        return None

    from services.comtrade_service import comtrade_service

    years = list(range(start_year, end_year + 1))
    records: List[Dict] = []
    for year in years:
        rows = comtrade_service.fetch(reporter, partner_code="0", period=str(year))
        if rows:
            records.extend(rows)
    chart_rows = aggregate_comtrade_series(records, years)
    has_data = any(r["exports"] > 0 or r["imports"] > 0 for r in chart_rows)
    if not has_data:
        return None
    info = AFRICAN_COUNTRIES_OEC.get(iso3.upper(), {})
    return {
        "country_iso3": iso3.upper(),
        "country_name": info.get("name_fr") or info.get("name_en") or iso3.upper(),
        "years": years,
        "chart_rows": chart_rows,
        "source": "UN Comtrade",
        "source_used": "UN Comtrade",
        "currency": "USD",
        "has_data": True,
    }


def default_providers() -> List[tuple]:
    """Liste ordonnée (nom, provider) des sources, secours opt-in inclus."""
    providers = [("OEC / BACI", _oec_provider)]
    if os.environ.get("COMTRADE_FALLBACK_ENABLED", "false").lower() == "true":
        providers.append(("UN Comtrade", _comtrade_provider))
    return providers


async def get_trade_series_resilient(
    country_iso3: str,
    start_year: int = 2018,
    end_year: int = DEFAULT_YEAR,
    providers: Optional[List[tuple]] = None,
) -> Dict:
    """
    Essaie chaque source dans l'ordre; renvoie la première qui a des données,
    en annotant `source_used` et `sources_tried`. Ne lève jamais: en dernier
    recours renvoie une structure vide valide (has_data=False).
    """
    iso3 = country_iso3.upper()
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    chain = providers if providers is not None else default_providers()

    tried: List[Dict] = []
    for name, provider in chain:
        try:
            result = await provider(iso3, start_year, end_year)
        except Exception as exc:  # une source défaillante ne casse pas la chaîne
            logger.warning("Trade-series source %s failed: %s", name, exc)
            tried.append({"source": name, "status": "error"})
            continue
        if result and result.get("has_data"):
            result["sources_tried"] = tried + [{"source": name, "status": "success"}]
            return result
        tried.append({"source": name, "status": "no_data"})

    # Aucune source: dégradation propre.
    info = AFRICAN_COUNTRIES_OEC.get(iso3, {})
    return {
        "country_iso3": iso3,
        "country_name": info.get("name_fr") or info.get("name_en") or iso3,
        "years": list(range(start_year, end_year + 1)),
        "chart_rows": [],
        "has_data": False,
        "source_used": None,
        "sources_tried": tried,
    }
