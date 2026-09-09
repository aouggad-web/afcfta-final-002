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

# Unité PHYSIQUE de chaque contrat (indépendante de l'échelle cents/dollars,
# qui est déterminée à l'exécution depuis le champ `currency` de l'API — voir
# _dollars_from_quote). Associe un diviseur (-> kg) et un libellé d'affichage.
_PHYSICAL_UNITS = {
    "lb": (LB_TO_KG, "lb"),
    "tonne": (TONNE_TO_KG, "tonne"),
    "troy_oz": (TROY_OZ_TO_KG, "once troy"),
    "bushel_wheat": (BUSHEL_KG_WHEAT, "boisseau"),
    "bushel_corn": (BUSHEL_KG_CORN, "boisseau"),
    "barrel": (BARREL_TO_KG, "baril"),
}

# Symbole Yahoo -> position SH cible + unité physique de cotation.
# L'échelle (cents vs dollars pleins) N'EST PAS supposée ici : elle est lue
# dans le champ `currency` de chaque réponse API ("USd"/"USX" = cents,
# "USD" = dollars pleins) par _dollars_from_quote — jamais devinée par
# contrat, pour éviter une conversion silencieusement fausse d'un facteur
# 100 si la convention de cotation d'un contrat diffère de l'hypothèse.
SYMBOLS = {
    "KC=F": {
        "hs": "090111",
        "commodity": "Café Arabica (vert, non torréfié, non décaféiné)",
        "benchmark": "ICE Coffee C (contrat rapproché)",
        "physical_unit": "lb",
    },
    "CC=F": {
        "hs": "1801",
        "commodity": "Cacao (fèves brutes)",
        "benchmark": "ICE Cocoa (contrat rapproché)",
        "physical_unit": "tonne",
    },
    "CT=F": {
        "hs": "5201",
        "commodity": "Coton (brut, non cardé ni peigné)",
        "benchmark": "ICE Cotton No. 2 (contrat rapproché)",
        "physical_unit": "lb",
    },
    "SB=F": {
        "hs": "1701",
        "commodity": "Sucre (canne ou betterave, brut)",
        "benchmark": "ICE Sugar No. 11 (contrat rapproché)",
        "physical_unit": "lb",
    },
    "HG=F": {
        "hs": "7403",
        "commodity": "Cuivre affiné (non ouvré)",
        "benchmark": "COMEX Copper (contrat rapproché)",
        "physical_unit": "lb",
    },
    "ALI=F": {
        "hs": "7601",
        "commodity": "Aluminium (non ouvré)",
        "benchmark": "COMEX Aluminum (contrat rapproché)",
        "physical_unit": "tonne",
    },
    "ZW=F": {
        "hs": "1001",
        "commodity": "Blé",
        "benchmark": "CBOT Wheat (contrat rapproché)",
        "physical_unit": "bushel_wheat",
    },
    "ZC=F": {
        "hs": "1005",
        "commodity": "Maïs",
        "benchmark": "CBOT Corn (contrat rapproché)",
        "physical_unit": "bushel_corn",
    },
    "ZS=F": {
        "hs": "1201",
        "commodity": "Soja (fèves)",
        "benchmark": "CBOT Soybeans (contrat rapproché)",
        "physical_unit": "bushel_wheat",
    },
    "GC=F": {
        "hs": "7108",
        "commodity": "Or (non monétaire, brut ou semi-ouvré)",
        "benchmark": "COMEX Gold (contrat rapproché)",
        "physical_unit": "troy_oz",
    },
    "SI=F": {
        "hs": "7106",
        "commodity": "Argent (brut ou semi-ouvré)",
        "benchmark": "COMEX Silver (contrat rapproché)",
        "physical_unit": "troy_oz",
    },
    "PL=F": {
        "hs": "7110",
        "commodity": "Platine (brut ou semi-ouvré)",
        "benchmark": "NYMEX Platinum (contrat rapproché)",
        "physical_unit": "troy_oz",
    },
    "BZ=F": {
        "hs": "2709",
        "commodity": "Pétrole brut",
        "benchmark": "ICE Brent (contrat rapproché)",
        "physical_unit": "barrel",
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


# Devises Yahoo Finance signalant un prix coté en CENTS de dollar (convention
# ICE/CBOT/COMEX pour cafés, céréales, coton, sucre, cuivre...). "USD" signale
# un prix déjà en dollars pleins (or, argent, platine, cacao, aluminium,
# Brent...). Toute autre valeur est rejetée : on ne devine jamais l'échelle
# à partir du symbole ou d'une hypothèse fixe par contrat — uniquement à
# partir de ce que l'API annonce elle-même pour CETTE cotation.
_CENTS_CURRENCIES = {"USd", "USX"}
_DOLLAR_CURRENCIES = {"USD", None}


def _dollars_from_quote(quote: dict) -> float:
    """Normalise le prix brut en USD pleins selon la devise renvoyée par l'API."""
    currency = quote.get("currency")
    if currency in _CENTS_CURRENCIES:
        return quote["price"] / 100.0
    if currency in _DOLLAR_CURRENCIES:
        return quote["price"]
    raise ValueError(f"devise inattendue: {currency!r}")


def build_entry(symbol: str, spec: dict, quote: dict) -> dict:
    """Construit l'entrée cours_mondiaux.json pour un symbole, ou lève ValueError."""
    usd_price = _dollars_from_quote(quote)
    divisor, unit_label = _PHYSICAL_UNITS[spec["physical_unit"]]
    usd_per_kg = usd_price / divisor
    lo, hi = PLAUSIBILITY_USD_PER_KG[spec["hs"]]
    if not (lo <= usd_per_kg <= hi):
        raise ValueError(
            f"cours converti {usd_per_kg:.4f} USD/kg hors bornes de vraisemblance "
            f"[{lo}, {hi}] — rejeté (devise/unité ou symbole probablement cassé)"
        )
    is_cents = quote.get("currency") in _CENTS_CURRENCIES
    raw_unit = f"¢/{unit_label}" if is_cents else f"USD/{unit_label}"
    return {
        "hs": spec["hs"],
        "commodity": spec["commodity"],
        "benchmark": spec["benchmark"],
        "raw_quote": f"{quote['price']:g} {raw_unit}",
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
