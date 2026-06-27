"""
Orchestrateur résilient de séries temporelles commerciales
==========================================================
Objectif: ne jamais "tomber en rade" en production si OEC est indisponible
ou rate-limité, en essayant plusieurs sources dans l'ordre de priorité.

Chaîne de résilience (combinée au cache + stale-on-error de cache_service):
    1. OEC / BACI    (source primaire — riche, mise en cache)
    2. UN Comtrade   (secours, OPT-IN: COMTRADE_FALLBACK_ENABLED=true + clé API)
    3. OMC / WTO     (secours, OPT-IN: WTO_FALLBACK_ENABLED=true)
    4. CNUCED/UNCTAD (secours, OPT-IN: UNCTAD_FALLBACK_ENABLED=true + UNCTAD_API_URL)

Tous les secours sont désactivés par défaut, le temps d'être validés en réseau.

Propriétés:
- Chaque source est isolée: une source qui échoue (exception / pas de données)
  n'interrompt pas la chaîne, on passe à la suivante.
- Dégradation propre: si aucune source n'a de données, on renvoie une
  structure valide (has_data=False) plutôt qu'une erreur → l'endpoint ne 500 pas.
- Transparence: la réponse indique `source_used` et `sources_tried`.

La logique d'orchestration est pure/testable (providers injectables).
Le mapping live Comtrade est opt-in et doit être validé en environnement réseau.
"""

import asyncio
import logging
import os
from typing import Awaitable, Callable, Dict, List, Optional

import httpx
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


def series_from_year_maps(
    exports_by_year: Dict[int, float],
    imports_by_year: Dict[int, float],
    years: List[int],
) -> List[Dict]:
    """
    Assemble une série exports/imports/balance à partir de deux dictionnaires
    {année: valeur}. Helper générique réutilisé par les adaptateurs WTO/UNCTAD.
    Fonction pure (testable).
    """
    rows = []
    for year in years:
        e = round(float(exports_by_year.get(year, 0) or 0), 2)
        i = round(float(imports_by_year.get(year, 0) or 0), 2)
        rows.append({"year": year, "exports": e, "imports": i, "balance": round(e - i, 2)})
    return rows


def extract_year_value_map(records: Optional[List[Dict]], year_key: str, value_key: str) -> Dict:
    """
    Extrait un dict {année:int -> valeur:float} d'une liste d'enregistrements,
    en lisant `year_key` et `value_key`. Tolérant aux valeurs manquantes/nulles.
    Utilisé pour normaliser les réponses WTO / UNCTAD (fonction pure, testable).
    """
    out: Dict[int, float] = {}
    for row in records or []:
        try:
            year = int(row.get(year_key))
        except (TypeError, ValueError):
            continue
        try:
            value = float(row.get(value_key) or 0)
        except (TypeError, ValueError):
            continue
        out[year] = out.get(year, 0.0) + value
    return out


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
        # comtrade_service.fetch est synchrone (requests + time.sleep) → on
        # l'exécute dans un thread pour ne pas bloquer l'event loop FastAPI.
        rows = await asyncio.to_thread(comtrade_service.fetch, reporter, "0", str(year))
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


def _build_country_result(
    iso3: str, years: List[int], chart_rows: List[Dict], source: str
) -> Optional[Dict]:
    """Construit la réponse normalisée d'un provider, ou None si aucune donnée."""
    has_data = any(r["exports"] > 0 or r["imports"] > 0 for r in chart_rows)
    if not has_data:
        return None
    info = AFRICAN_COUNTRIES_OEC.get(iso3.upper(), {})
    return {
        "country_iso3": iso3.upper(),
        "country_name": info.get("name_fr") or info.get("name_en") or iso3.upper(),
        "years": years,
        "chart_rows": chart_rows,
        "source": source,
        "source_used": source,
        "currency": "USD",
        "has_data": True,
    }


async def _wto_provider(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """
    Secours OMC (WTO) — OPT-IN (WTO_FALLBACK_ENABLED=true).
    Utilise le client wto_service existant; normalise les séries annuelles
    de valeur d'exports/imports de marchandises. À valider en réseau avant
    activation (la forme exacte de la réponse WTO dépend de l'indicateur).
    """
    if os.environ.get("WTO_FALLBACK_ENABLED", "false").lower() != "true":
        return None

    from services.wto_service import wto_service

    years = list(range(start_year, end_year + 1))
    # wto_service.get_trade_indicators est synchrone (requests + time.sleep) → on
    # exécute les 2 appels dans des threads, en parallèle, sans bloquer l'event loop.
    exp_resp, imp_resp = await asyncio.gather(
        asyncio.to_thread(wto_service.get_trade_indicators, iso3.upper(), "ITS_MTV_AX"),
        asyncio.to_thread(wto_service.get_trade_indicators, iso3.upper(), "ITS_MTV_AM"),
    )
    exp_rows = (exp_resp or {}).get("data") if isinstance(exp_resp, dict) else None
    imp_rows = (imp_resp or {}).get("data") if isinstance(imp_resp, dict) else None
    exports = extract_year_value_map(exp_rows, "Year", "Value")
    imports = extract_year_value_map(imp_rows, "Year", "Value")
    chart_rows = series_from_year_maps(exports, imports, years)
    return _build_country_result(iso3, years, chart_rows, "OMC / WTO")


async def _unctad_provider(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """
    Secours CNUCED (UNCTADstat) — OPT-IN (UNCTAD_FALLBACK_ENABLED=true).
    Appel minimal à l'API UNCTAD; normalise les valeurs annuelles
    d'exports/imports. À valider en réseau avant activation.
    """
    if os.environ.get("UNCTAD_FALLBACK_ENABLED", "false").lower() != "true":
        return None

    base = os.environ.get("UNCTAD_API_URL", "").rstrip("/")
    if not base:
        return None

    years = list(range(start_year, end_year + 1))
    params = {
        "iso3": iso3.upper(),
        "startYear": start_year,
        "endYear": end_year,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(base, params=params)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        logger.warning("UNCTAD fetch failed: %s", exc)
        return None

    rows = payload.get("data") if isinstance(payload, dict) else payload
    exports = extract_year_value_map(
        [r for r in (rows or []) if str(r.get("flow", "")).lower().startswith("ex")],
        "year",
        "value",
    )
    imports = extract_year_value_map(
        [r for r in (rows or []) if str(r.get("flow", "")).lower().startswith("im")],
        "year",
        "value",
    )
    chart_rows = series_from_year_maps(exports, imports, years)
    return _build_country_result(iso3, years, chart_rows, "CNUCED / UNCTAD")


def default_providers() -> List[tuple]:
    """
    Liste ordonnée (nom, provider) des sources. OEC est primaire; les secours
    (Comtrade, WTO, UNCTAD) sont opt-in via variables d'environnement et
    désactivés par défaut, le temps d'être validés en environnement réseau.
    """
    providers = [("OEC / BACI", _oec_provider)]
    if os.environ.get("COMTRADE_FALLBACK_ENABLED", "false").lower() == "true":
        providers.append(("UN Comtrade", _comtrade_provider))
    if os.environ.get("WTO_FALLBACK_ENABLED", "false").lower() == "true":
        providers.append(("OMC / WTO", _wto_provider))
    if os.environ.get("UNCTAD_FALLBACK_ENABLED", "false").lower() == "true":
        providers.append(("CNUCED / UNCTAD", _unctad_provider))
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
