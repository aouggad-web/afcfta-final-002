"""
Rafraîchissement du facteur de marché du fret vraquier (vrac sec).

Écrit ``data/json/fret_vraquier.json`` (racine du dépôt), lu par
``backend/logistics_bulk_fees_data.py`` en priorité sur son modèle
distance-coût statique. Conçu pour tourner dans GitHub Actions (cron jours
ouvrés) — voir .github/workflows/update_bulk_freight.yml.

Source live : ETF **Breakwave Dry Bulk Shipping (BDRY)** via l'API « chart »
publique de Yahoo Finance (même mécanisme que update_world_market_prices.py).
BDRY suit un panier de futures de fret vrac sec (Capesize/Panamax/Supramax).

IMPORTANT — c'est un PROXY du marché vrac sec, PAS l'indice Baltic par classe
(BHSI/BSI/BPI/BCI, propriétaires, sans flux gratuit fiable). Le même facteur
de marché est donc appliqué à TOUTES les classes, et clairement étiqueté comme
tel dans la sortie. Le facteur = cours BDRY courant / moyenne glissante 12 mois
du MÊME titre (dénominateur auto-sourcé depuis la série renvoyée par l'API —
jamais une valeur de référence inventée).

Discipline « zéro fabrication », identique à update_world_market_prices.py :

  - on n'écrit QU'un facteur calculé à partir d'un cours effectivement
    récupéré, avec la date de marché fournie par l'API — jamais une valeur
    inventée ni recopiée d'un run précédent ;
  - si le cours échoue, la série est vide, ou le facteur sort des bornes de
    vraisemblance, TOUTES les classes retombent sur un multiplicateur 1,0 daté
    (repli statique : le modèle reste calibré sur les benchmarks Baltic 2024) ;
  - le repli statique n'est jamais écrasé par une valeur douteuse.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

_OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "json", "fret_vraquier.json"
)

# Proxy de marché du fret vrac sec (ETF coté, suit des futures Baltic).
MARKET_PROXY_SYMBOL = "BDRY"
MARKET_PROXY_NAME = "Breakwave Dry Bulk Shipping ETF (BDRY)"
MARKET_PROXY_SOURCE = (
    "Yahoo Finance (BDRY) — proxy marché du fret vrac sec "
    "(panier futures Capesize/Panamax/Supramax)"
)
MARKET_PROXY_URL = "https://finance.yahoo.com/quote/BDRY/"

# Le facteur unique est appliqué à ces classes (le backend lit un multiplicateur
# par classe ; on écrit le même pour toutes, faute d'indice par classe gratuit).
VESSEL_CLASSES = ("handysize", "supramax", "panamax", "capesize")

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
_USER_AGENT = "Mozilla/5.0 (compatible; afcfta-data-bot; +https://github.com/aouggad-web)"

# Bornes de vraisemblance du facteur (identiques au backend) : un flux cassé
# hors de cette plage est REJETÉ, toutes les classes restent au repli 1,0.
MULTIPLIER_BOUNDS = (0.3, 3.0)

# Nombre minimal de clôtures exploitables dans la série pour établir une
# moyenne glissante crédible (sinon repli statique).
_MIN_SERIES_POINTS = 30


def compute_multiplier(current_level: float, baseline_level: float) -> float:
    """Facteur de marché = niveau courant / niveau de référence.

    Lève ValueError si les entrées sont inexploitables ou si le résultat sort
    des bornes de vraisemblance — on ne devine jamais, on ne borne pas en
    silence.
    """
    if not isinstance(current_level, (int, float)) or current_level <= 0:
        raise ValueError(f"niveau courant absent ou invalide: {current_level!r}")
    if not isinstance(baseline_level, (int, float)) or baseline_level <= 0:
        raise ValueError(f"référence invalide: {baseline_level!r}")
    mult = round(current_level / baseline_level, 4)
    lo, hi = MULTIPLIER_BOUNDS
    if not (lo <= mult <= hi):
        raise ValueError(
            f"facteur {mult} hors bornes de vraisemblance [{lo}, {hi}] — "
            "flux probablement cassé, rejeté"
        )
    return mult


def parse_chart_series(payload: dict) -> dict:
    """Extrait (cours courant, date de marché, série de clôtures) d'une réponse
    de l'API chart Yahoo.

    Lève ValueError si la réponse ne contient pas de cotation exploitable — on
    ne devine jamais.
    """
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        raise ValueError("réponse sans 'chart.result'")
    node = result[0]
    meta = node.get("meta") or {}
    current = meta.get("regularMarketPrice")
    market_time = meta.get("regularMarketTime")
    if not isinstance(current, (int, float)) or current <= 0:
        raise ValueError(f"cours courant absent ou invalide: {current!r}")
    if not isinstance(market_time, (int, float)) or market_time <= 0:
        raise ValueError(f"date de marché absente: {market_time!r}")
    quotes = (((node.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
    closes = [c for c in quotes if isinstance(c, (int, float)) and c > 0]
    as_of = datetime.fromtimestamp(int(market_time), tz=timezone.utc).strftime("%Y-%m-%d")
    return {"current": float(current), "as_of": as_of, "closes": closes}


def compute_market_factor(series: dict) -> dict:
    """Facteur de marché depuis une série chart : cours courant / moyenne glissante.

    Le dénominateur est la moyenne des clôtures renvoyées par l'API (auto-sourcé,
    jamais une référence inventée). Lève ValueError si la série est trop courte
    ou le facteur hors bornes.
    """
    closes = series.get("closes") or []
    if len(closes) < _MIN_SERIES_POINTS:
        raise ValueError(
            f"série trop courte ({len(closes)} < {_MIN_SERIES_POINTS} points) — "
            "moyenne glissante non crédible, rejeté"
        )
    baseline = sum(closes) / len(closes)
    factor = compute_multiplier(series["current"], baseline)
    return {
        "factor": factor,
        "current": round(float(series["current"]), 4),
        "baseline": round(float(baseline), 4),
        "as_of": series["as_of"],
        "window_points": len(closes),
    }


def build_static_entry(vessel_class: str) -> dict:
    """Entrée de repli statique daté (multiplicateur 1,0) pour une classe.

    Le modèle sous-jacent reste calibré sur les benchmarks Baltic 2024 ; en
    l'absence de facteur live, on applique 1,0 (= comportement calibré).
    """
    return {
        "multiplier": 1.0,
        "proxy": MARKET_PROXY_NAME,
        "as_of": "moyenne 2024",
        "source": "Modèle calibré sur benchmarks Baltic 2024 (repli statique, aucun facteur live)",
    }


def build_live_entry(vessel_class: str, factor_info: dict) -> dict:
    """Entrée live pour une classe : facteur de marché proxy appliqué uniformément."""
    return {
        "multiplier": factor_info["factor"],
        "proxy": MARKET_PROXY_NAME,
        "proxy_level": factor_info["current"],
        "proxy_baseline_12m": factor_info["baseline"],
        "as_of": factor_info["as_of"],
        "source": (
            f"{MARKET_PROXY_SOURCE} — cours {factor_info['current']} vs moyenne "
            f"glissante {factor_info['baseline']} ({factor_info['window_points']} j). "
            "Proxy marché vrac sec appliqué uniformément aux classes (pas l'indice "
            "Baltic par classe)."
        ),
    }


def fetch_chart(symbol: str = MARKET_PROXY_SYMBOL) -> dict:
    """Récupère la réponse chart Yahoo pour un symbole (réseau)."""
    req = urllib.request.Request(
        _CHART_URL.format(symbol=urllib.parse.quote(symbol)),
        headers={"User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_market_factor() -> dict | None:
    """Facteur de marché courant, ou ``None`` en cas d'échec (repli statique).

    Un chemin JSON local peut être fourni via ``BDRY_CHART_JSON`` (utile en CI
    si une étape amont a déjà récupéré la réponse) ; sinon appel réseau Yahoo.
    """
    local = os.environ.get("BDRY_CHART_JSON")
    try:
        if local:
            with open(local, encoding="utf-8") as fh:
                payload = json.load(fh)
        else:
            payload = fetch_chart()
        return compute_market_factor(parse_chart_series(payload))
    except (OSError, ValueError) as exc:
        print(f"SKIP proxy {MARKET_PROXY_SYMBOL}: {exc}", file=sys.stderr)
        return None


def build_payload(factor_info: dict | None) -> dict:
    """Assemble fret_vraquier.json : facteur live appliqué à toutes les classes,
    ou repli statique 1,0 si le facteur est indisponible/douteux."""
    live = factor_info is not None
    multipliers = {}
    for cls in VESSEL_CLASSES:
        multipliers[cls] = build_live_entry(cls, factor_info) if live else build_static_entry(cls)
    if live:
        print(
            f"OK   facteur marché x{factor_info['factor']} "
            f"({factor_info['as_of']}) appliqué à {len(VESSEL_CLASSES)} classes"
        )
    else:
        print("Repli statique intégral (aucun facteur live) — multiplicateurs 1,0.")

    return {
        "_meta": {
            "description": "Facteur de marché du fret vrac sec (proxy BDRY) appliqué au "
            "modèle distance-coût de backend/logistics_bulk_fees_data.py, uniformément par "
            "classe de navire. Proxy, pas l'indice Baltic par classe. Sans facteur live, "
            "repli statique 1,0 (modèle calibré Baltic 2024). Zéro fabrication.",
            "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "etl/update_bulk_freight_indices.py (GitHub Actions, jours ouvrés)",
            "market_proxy": MARKET_PROXY_NAME,
            "market_proxy_url": MARKET_PROXY_URL,
            "plausibility_multiplier_bounds": list(MULTIPLIER_BOUNDS),
            "is_live": live,
        },
        "vessel_class_multipliers": multipliers,
    }


def main() -> int:
    payload = build_payload(fetch_market_factor())
    os.makedirs(os.path.dirname(_OUT_PATH), exist_ok=True)
    with open(_OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    state = "live" if payload["_meta"]["is_live"] else "repli statique"
    print(f"\nÉcrit {_OUT_PATH} — {state}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
