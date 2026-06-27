"""
Orchestrateur résilient de séries temporelles commerciales
==========================================================
Objectif: ne jamais "tomber en rade" en production si OEC est indisponible
ou rate-limité, en essayant plusieurs sources dans l'ordre de priorité.

Chaîne de résilience (combinée au cache + stale-on-error de cache_service).
Les API GRATUITES passent en premier:
    1. OEC / BACI    (source primaire — riche, mise en cache ; gratuit)
    2. OMC / WTO     (secours GRATUIT sans clé, OPT-IN: WTO_FALLBACK_ENABLED=true)
    3. CNUCED/UNCTAD (secours gratuit, OPT-IN: UNCTAD_FALLBACK_ENABLED=true + UNCTAD_API_URL)
    4. UN Comtrade   (secours à CLÉ, OPT-IN: COMTRADE_FALLBACK_ENABLED=true + clé API)

Tous les secours sont désactivés par défaut, le temps d'être validés en réseau
via GET /api/oec/trade-series/sources/{pays}.

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

    Comtrade renvoie aussi une ligne agrégée toutes-marchandises (cmdCode
    'TOTAL'). Si elle est présente, on l'utilise SEULE pour éviter de
    double-compter avec les lignes par produit; sinon on somme les lignes.
    """
    rows = records or []

    def _year(row):
        try:
            return int(row.get("period") or 0)
        except (TypeError, ValueError):
            return None

    # Années disposant d'une ligne agrégée TOTAL : pour CELLES-CI on n'utilise
    # que les TOTAL (anti double-comptage) ; les autres années somment leurs
    # lignes détaillées. Décision par année, pas globale.
    years_with_total = {_year(r) for r in rows if str(r.get("cmdCode", "")).upper() == "TOTAL"}
    years_with_total.discard(None)

    exp = {y: 0.0 for y in years}
    imp = {y: 0.0 for y in years}
    for row in rows:
        year = _year(row)
        if year not in exp:
            continue
        is_total = str(row.get("cmdCode", "")).upper() == "TOTAL"
        if year in years_with_total and not is_total:
            continue  # année couverte par un TOTAL → ignorer les lignes produits
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


async def _comtrade_fetch(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """
    Récupération UN Comtrade (sans garde d'env — utilisée par le provider gardé
    et par la sonde de diagnostic). Requiert le mapping M49 + une clé API.
    """
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


async def _wto_fetch(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """
    Récupération OMC/WTO (sans garde d'env). Utilise le client wto_service
    existant; normalise les séries annuelles d'exports/imports de marchandises.
    """
    from services.wto_service import wto_service

    years = list(range(start_year, end_year + 1))
    # wto_service.get_trade_indicators est synchrone (requests + time.sleep) → on
    # exécute les 2 appels dans des threads, en parallèle, sans bloquer l'event loop.
    exp_resp, imp_resp = await asyncio.gather(
        asyncio.to_thread(wto_service.get_trade_indicators, iso3.upper(), "ITS_MTV_AX"),
        asyncio.to_thread(wto_service.get_trade_indicators, iso3.upper(), "ITS_MTV_AM"),
    )
    # get_trade_indicators renvoie None sur erreur HTTP/réseau. Si les deux
    # échouent, on lève pour que le diagnostic reporte 'error' (et non 'no_data').
    if exp_resp is None and imp_resp is None:
        raise RuntimeError("WTO indisponible (aucune réponse)")
    exp_rows = (exp_resp or {}).get("data") if isinstance(exp_resp, dict) else None
    imp_rows = (imp_resp or {}).get("data") if isinstance(imp_resp, dict) else None
    exports = extract_year_value_map(exp_rows, "Year", "Value")
    imports = extract_year_value_map(imp_rows, "Year", "Value")
    chart_rows = series_from_year_maps(exports, imports, years)
    return _build_country_result(iso3, years, chart_rows, "OMC / WTO")


async def _unctad_fetch(iso3: str, start_year: int, end_year: int) -> Optional[Dict]:
    """
    Récupération CNUCED/UNCTADstat (sans garde d'env). Appel minimal à l'API
    UNCTAD (UNCTAD_API_URL requis); normalise les valeurs annuelles.
    """
    base = os.environ.get("UNCTAD_API_URL", "").rstrip("/")
    if not base:
        return None

    years = list(range(start_year, end_year + 1))
    params = {
        "iso3": iso3.upper(),
        "startYear": start_year,
        "endYear": end_year,
    }
    # On laisse les erreurs HTTP/réseau remonter: la chaîne et la sonde les
    # capturent et rapportent 'error' (et non 'no_data', trompeur en diagnostic).
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(base, params=params)
        resp.raise_for_status()
        payload = resp.json()

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


# Registre des sources, dans l'ordre de priorité. Les API GRATUITES passent en
# premier (OEC puis OMC/WTO sans clé), avant les sources nécessitant une clé.
#   flag=None  → toujours active (source primaire)
#   free=True  → API gratuite (WTO sans clé ; UNCTAD gratuit mais URL requise)
#   free=False → nécessite une clé d'API (Comtrade)
SOURCE_REGISTRY = [
    {"name": "OEC / BACI", "flag": None, "fetch": _oec_provider, "free": True},
    {"name": "OMC / WTO", "flag": "WTO_FALLBACK_ENABLED", "fetch": _wto_fetch, "free": True},
    {
        "name": "CNUCED / UNCTAD",
        "flag": "UNCTAD_FALLBACK_ENABLED",
        "fetch": _unctad_fetch,
        "free": True,
    },
    {
        "name": "UN Comtrade",
        "flag": "COMTRADE_FALLBACK_ENABLED",
        "fetch": _comtrade_fetch,
        "free": False,
    },
]


def _is_enabled(entry: Dict) -> bool:
    """Une source est active si elle est primaire (flag=None) ou son flag d'env est 'true'."""
    flag = entry["flag"]
    return flag is None or os.environ.get(flag, "false").lower() == "true"


def default_providers() -> List[tuple]:
    """
    Liste ordonnée (nom, fetch) des sources actives. OEC est primaire; les
    secours sont opt-in via variables d'environnement et désactivés par défaut,
    le temps d'être validés en environnement réseau (gratuit d'abord: WTO).
    """
    return [(e["name"], e["fetch"]) for e in SOURCE_REGISTRY if _is_enabled(e)]


async def probe_sources(
    country_iso3: str,
    start_year: int = 2018,
    end_year: int = DEFAULT_YEAR,
) -> Dict:
    """
    Sonde de diagnostic: interroge CHAQUE source en direct (même désactivée) et
    rapporte son état — pour valider en environnement réseau avant d'activer.

    Pour chaque source: nom, gratuite ?, activée (env) ?, statut (ok/no_data/
    error) et un échantillon de la dernière année. Ne lève jamais.
    """
    iso3 = country_iso3.upper()
    if start_year > end_year:
        start_year, end_year = end_year, start_year

    results = []
    for entry in SOURCE_REGISTRY:
        report = {
            "source": entry["name"],
            "free": entry["free"],
            "enabled": _is_enabled(entry),
            "env_flag": entry["flag"],
        }
        try:
            res = await entry["fetch"](iso3, start_year, end_year)
            if res and res.get("has_data"):
                report["status"] = "ok"
                report["sample"] = (res.get("chart_rows") or [])[-1:]
            else:
                report["status"] = "no_data"
        except Exception as exc:  # une source défaillante ne casse pas la sonde
            # On logge le détail (avec stack) côté serveur, mais on ne renvoie
            # qu'un type d'erreur stable/sanitisé au client.
            logger.warning("probe source %s failed", entry["name"], exc_info=True)
            report["status"] = "error"
            report["error_type"] = type(exc).__name__
        results.append(report)

    return {
        "country_iso3": iso3,
        "years": list(range(start_year, end_year + 1)),
        "sources": results,
    }


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
