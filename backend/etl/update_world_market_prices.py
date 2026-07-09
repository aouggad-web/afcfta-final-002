"""
Mise à jour quotidienne des cours mondiaux de matières premières.

Écrit ``data/json/cours_mondiaux.json`` (racine du dépôt), lu par
``backend/services/shipment_estimator.py`` en priorité sur ses valeurs
statiques (_WORLD_MARKET_BENCHMARKS). Conçu pour tourner dans GitHub Actions
(cron quotidien) — voir .github/workflows/update_market_prices.yml.

Source : API « chart » publique de Yahoo Finance (contrats rapprochés ICE,
CBOT, COMEX, NYMEX). Discipline « zéro fabrication » :

  - on n'écrit QUE des cotations effectivement renvoyées par l'API, avec la
    date de marché fournie par l'API elle-même (regularMarketTime) — jamais
    de valeur inventée ni recopiée d'un précédent run ;
  - un symbole qui échoue est simplement ABSENT du fichier de sortie (le
    backend retombe alors sur sa valeur statique datée) ;
  - chaque entrée conserve la cotation BRUTE et son unité d'origine avant
    conversion en USD/kg.

Couverture : seuls les produits disposant d'un contrat liquide accessible
gratuitement sont rafraîchis (~13). Les cours sans flux gratuit fiable
(cobalt Fastmarkets, minerai de fer Platts, riz thaï FOB, huile de palme
FCPO, caoutchouc SICOM, thé Mombasa, zinc/nickel LME) restent sur les
valeurs statiques datées du backend — les rafraîchir exigerait un abonnement
à un fournisseur de données de marché.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Conversions physiques (identiques à backend/services/shipment_estimator.py).
LB_TO_KG = 0.45359237
TROY_OZ_TO_KG = 0.0311034768
TONNE_TO_KG = 1000.0
BUSHEL_KG_WHEAT = 27.2155  # aussi soja (60 lb/bu)
BUSHEL_KG_CORN = 25.40117  # 56 lb/bu
BARREL_TO_KG = 158.987 * 0.85  # brut ~38-40° API

_OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "json", "cours_mondiaux.json"
)

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
_USER_AGENT = "Mozilla/5.0 (compatible; afcfta-data-bot; +https://github.com/aouggad-web)"

# Symbole Yahoo -> position SH cible + conversion vers USD/kg.
# "unit" décrit l'unité BRUTE de la cotation (pour le champ raw_quote).
SYMBOLS = {
    "KC=F": {
        "hs": "090111",
        "commodity": "Café Arabica (vert, non torréfié, non décaféiné)",
        "benchmark": "ICE Coffee C (contrat rapproché)",
        "unit": "¢/lb",
        "to_usd_per_kg": lambda p: p / 100 / LB_TO_KG,
    },
    "CC=F": {
        "hs": "1801",
        "commodity": "Cacao (fèves brutes)",
        "benchmark": "ICE Cocoa (contrat rapproché)",
        "unit": "USD/tonne",
        "to_usd_per_kg": lambda p: p / TONNE_TO_KG,
    },
    "CT=F": {
        "hs": "5201",
        "commodity": "Coton (brut, non cardé ni peigné)",
        "benchmark": "ICE Cotton No. 2 (contrat rapproché)",
        "unit": "¢/lb",
        "to_usd_per_kg": lambda p: p / 100 / LB_TO_KG,
    },
    "SB=F": {
        "hs": "1701",
        "commodity": "Sucre (canne ou betterave, brut)",
        "benchmark": "ICE Sugar No. 11 (contrat rapproché)",
        "unit": "¢/lb",
        "to_usd_per_kg": lambda p: p / 100 / LB_TO_KG,
    },
    "HG=F": {
        "hs": "7403",
        "commodity": "Cuivre affiné (non ouvré)",
        "benchmark": "COMEX Copper (contrat rapproché)",
        "unit": "USD/lb",
        "to_usd_per_kg": lambda p: p / LB_TO_KG,
    },
    "ALI=F": {
        "hs": "7601",
        "commodity": "Aluminium (non ouvré)",
        "benchmark": "COMEX Aluminum (contrat rapproché)",
        "unit": "USD/tonne",
        "to_usd_per_kg": lambda p: p / TONNE_TO_KG,
    },
    "ZW=F": {
        "hs": "1001",
        "commodity": "Blé",
        "benchmark": "CBOT Wheat (contrat rapproché)",
        "unit": "¢/boisseau",
        "to_usd_per_kg": lambda p: p / 100 / BUSHEL_KG_WHEAT,
    },
    "ZC=F": {
        "hs": "1005",
        "commodity": "Maïs",
        "benchmark": "CBOT Corn (contrat rapproché)",
        "unit": "¢/boisseau",
        "to_usd_per_kg": lambda p: p / 100 / BUSHEL_KG_CORN,
    },
    "ZS=F": {
        "hs": "1201",
        "commodity": "Soja (fèves)",
        "benchmark": "CBOT Soybeans (contrat rapproché)",
        "unit": "¢/boisseau",
        "to_usd_per_kg": lambda p: p / 100 / BUSHEL_KG_WHEAT,
    },
    "GC=F": {
        "hs": "7108",
        "commodity": "Or (non monétaire, brut ou semi-ouvré)",
        "benchmark": "COMEX Gold (contrat rapproché)",
        "unit": "USD/once troy",
        "to_usd_per_kg": lambda p: p / TROY_OZ_TO_KG,
    },
    "SI=F": {
        "hs": "7106",
        "commodity": "Argent (brut ou semi-ouvré)",
        "benchmark": "COMEX Silver (contrat rapproché)",
        "unit": "USD/once troy",
        "to_usd_per_kg": lambda p: p / TROY_OZ_TO_KG,
    },
    "PL=F": {
        "hs": "7110",
        "commodity": "Platine (brut ou semi-ouvré)",
        "benchmark": "NYMEX Platinum (contrat rapproché)",
        "unit": "USD/once troy",
        "to_usd_per_kg": lambda p: p / TROY_OZ_TO_KG,
    },
    "BZ=F": {
        "hs": "2709",
        "commodity": "Pétrole brut",
        "benchmark": "ICE Brent (contrat rapproché)",
        "unit": "USD/baril",
        "to_usd_per_kg": lambda p: p / BARREL_TO_KG,
    },
}

# Bornes de vraisemblance (USD/kg) par position SH : un cours hors bornes est
# REJETÉ (symbole cassé, changement d'unité côté API...) plutôt qu'écrit.
# Bornes volontairement très larges — c'est un garde-fou anti-aberration,
# pas une contrainte de marché.
PLAUSIBILITY_USD_PER_KG = {
    "090111": (1.0, 60.0),
    "1801": (1.0, 40.0),
    "5201": (0.5, 15.0),
    "1701": (0.1, 3.0),
    "7403": (3.0, 60.0),
    "7601": (1.0, 15.0),
    "1001": (0.05, 2.0),
    "1005": (0.05, 2.0),
    "1201": (0.1, 3.0),
    "7108": (20_000.0, 500_000.0),
    "7106": (200.0, 10_000.0),
    "7110": (10_000.0, 200_000.0),
    "2709": (0.1, 3.0),
}


def parse_chart_response(payload: dict) -> dict:
    """
    Extrait (prix, date de marché, devise) d'une réponse de l'API chart.

    Lève ValueError si la réponse ne contient pas une cotation exploitable —
    on ne devine jamais.
    """
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        raise ValueError("réponse sans 'chart.result'")
    meta = result[0].get("meta") or {}
    price = meta.get("regularMarketPrice")
    market_time = meta.get("regularMarketTime")
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError(f"prix absent ou invalide: {price!r}")
    if not isinstance(market_time, (int, float)) or market_time <= 0:
        raise ValueError(f"date de marché absente: {market_time!r}")
    as_of = datetime.fromtimestamp(int(market_time), tz=timezone.utc).strftime("%Y-%m-%d")
    return {
        "price": float(price),
        "as_of": as_of,
        "currency": meta.get("currency"),
        "contract_symbol": meta.get("symbol"),
    }


def build_entry(symbol: str, spec: dict, quote: dict) -> dict:
    """Construit l'entrée cours_mondiaux.json pour un symbole, ou lève ValueError."""
    if quote.get("currency") not in ("USD", "USd", "USX", None):
        raise ValueError(f"devise inattendue: {quote.get('currency')!r}")
    usd_per_kg = spec["to_usd_per_kg"](quote["price"])
    lo, hi = PLAUSIBILITY_USD_PER_KG[spec["hs"]]
    if not (lo <= usd_per_kg <= hi):
        raise ValueError(
            f"cours converti {usd_per_kg:.4f} USD/kg hors bornes de vraisemblance "
            f"[{lo}, {hi}] — rejeté (unité ou symbole probablement cassé)"
        )
    return {
        "hs": spec["hs"],
        "commodity": spec["commodity"],
        "benchmark": spec["benchmark"],
        "raw_quote": f"{quote['price']:g} {spec['unit']}",
        "as_of": quote["as_of"],
        "usd_per_kg": round(usd_per_kg, 6),
        "source": f"Yahoo Finance ({symbol}) — {spec['benchmark']}",
        "source_url": f"https://finance.yahoo.com/quote/{symbol}/",
    }


def fetch_symbol(symbol: str) -> dict:
    req = urllib.request.Request(
        _CHART_URL.format(symbol=urllib.parse.quote(symbol)),
        headers={"User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    entries = {}
    failures = []
    for symbol, spec in SYMBOLS.items():
        try:
            quote = parse_chart_response(fetch_symbol(symbol))
            entry = build_entry(symbol, spec, quote)
            entries[spec["hs"]] = entry
            print(
                f"OK   {symbol:6s} -> SH {spec['hs']}: {entry['usd_per_kg']} USD/kg "
                f"({entry['raw_quote']}, {entry['as_of']})"
            )
        except Exception as exc:  # noqa: BLE001 — fail-soft par symbole, jamais de valeur inventée
            failures.append(f"{symbol}: {exc}")
            print(f"SKIP {symbol:6s} -> {exc}", file=sys.stderr)

    if not entries:
        print("Aucun cours récupéré — fichier de sortie laissé intact.", file=sys.stderr)
        return 1

    out = {
        "_meta": {
            "description": "Cours mondiaux rafraîchis automatiquement — lus par "
            "backend/services/shipment_estimator.py en priorité sur ses valeurs "
            "statiques. Un SH absent ici retombe sur la valeur statique datée.",
            "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "etl/update_world_market_prices.py (GitHub Actions quotidien)",
            "symbols_ok": len(entries),
            "symbols_failed": failures,
        },
        "benchmarks": entries,
    }
    os.makedirs(os.path.dirname(_OUT_PATH), exist_ok=True)
    with open(_OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\nÉcrit {_OUT_PATH} — {len(entries)} cours, {len(failures)} échec(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
