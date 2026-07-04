"""
Reconnaissance des portails douaniers nationaux (exécutée sur le runner GitHub).

But : avant d'écrire un scraper par pays, savoir ce qui est RÉELLEMENT joignable
et sous quelle forme. Ce sandbox n'a pas d'accès réseau aux sites douaniers
(bloqués par la politique d'egress) ; le runner GitHub, si. On sonde donc
chaque portail candidat depuis le runner et on imprime un diagnostic compact :
  - statut HTTP + URL finale (après redirections)
  - type de contenu, taille
  - indice de structure : Cloudflare/anti-bot, <table>, <form>, JSON, PDF,
    application monopage JS (peu scrapable en HTTP simple)

Aucune donnée tarifaire n'est extraite ici — c'est un repérage. Les résultats
décident quels pays reçoivent un scraper (HTML/JSON) et lesquels sont hors
périmètre V1 (PDF-only, JS lourd, injoignable).

Usage (workflow) : python -m crawlers.scrapling_engine.recon
"""

from __future__ import annotations

import re
import sys
from typing import Dict, List

import httpx

# Portails douaniers nationaux candidats — pays à tarif autonome sans données.
# Plusieurs URL par pays quand la page tarifaire probable diffère de l'accueil.
CANDIDATES: Dict[str, List[str]] = {
    "LBY": ["https://customs.gov.ly/"],
    "SDN": ["https://customs.gov.sd/"],
    "MRT": ["https://douanes.gov.mr/", "https://www.douanes.gov.mr/"],
    "MDG": ["https://www.douanes.gov.mg/", "https://www.douanes.gov.mg/le-tarif-des-douanes/"],
    "MUS": ["https://www.mra.mu/", "https://www.mra.mu/index.php/customs1/customs-tariff"],
    "SYC": ["https://www.src.gov.sc/", "https://www.src.gov.sc/pages/customs/customstariff.aspx"],
    "ZMB": ["https://www.zra.org.zm/", "https://www.zra.org.zm/customs-tariff/"],
    "ZWE": ["https://www.zimra.co.zw/", "https://www.zimra.co.zw/customs-excise"],
    "MWI": ["https://www.mra.mw/", "https://www.mra.mw/customs/tariff"],
    "MOZ": ["https://www.at.gov.mz/", "https://www.at.gov.mz/por/Aduaneira"],
    "AGO": ["https://www.agt.minfin.gov.ao/", "https://www.sga.gov.ao/"],
    "GHA": ["https://gra.gov.gh/", "https://gra.gov.gh/customs/harmonized-system-code/"],
    "DJI": ["https://douane.dj/"],
    "COM": ["https://www.douanes.km/"],
    "SOM": ["https://customs.gov.so/"],
    "ERI": ["https://www.customs.gov.er/"],
    "STP": ["https://www.alfandega.st/"],
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
    "Accept-Language": "fr,en;q=0.8,ar;q=0.6,pt;q=0.6",
}


def _classify(resp: httpx.Response) -> str:
    ct = resp.headers.get("content-type", "").lower()
    body = resp.text[:200000] if "text" in ct or "html" in ct or "json" in ct else ""
    low = body.lower()
    hints = []
    server = resp.headers.get("server", "").lower()
    if "cloudflare" in server or "cf-ray" in {k.lower() for k in resp.headers}:
        hints.append("cloudflare")
    if "just a moment" in low or "challenge-platform" in low or "cf-browser-verification" in low:
        hints.append("ANTI-BOT-CHALLENGE")
    if "application/pdf" in ct:
        hints.append("PDF")
    if "application/json" in ct or (low.strip()[:1] in "{["):
        hints.append("JSON")
    if "<table" in low:
        hints.append(f"HTML-tables(x{low.count('<table')})")
    if "<form" in low:
        hints.append(f"form(x{low.count('<form')})")
    # SPA JS : peu/pas de contenu serveur, un div racine + bundles
    if re.search(r'id=["\'](root|app|__next)["\']', low) or "window.__nuxt__" in low:
        hints.append("SPA-JS")
    if not hints:
        hints.append("html-plain")
    return ", ".join(hints)


def _probe(url: str) -> str:
    try:
        with httpx.Client(
            headers=HEADERS, timeout=25.0, follow_redirects=True, verify=False
        ) as client:
            resp = client.get(url)
        size = len(resp.content)
        return (
            f"HTTP {resp.status_code}  {resp.headers.get('content-type','?').split(';')[0]}  "
            f"{size}o  -> {str(resp.url)[:80]}\n      [{_classify(resp)}]"
        )
    except Exception as e:  # noqa: BLE001 — repérage : on veut la raison exacte
        return f"ERREUR {type(e).__name__}: {str(e)[:120]}"


def main() -> int:
    only = {a.upper() for a in sys.argv[1:]}
    for iso, urls in CANDIDATES.items():
        if only and iso not in only:
            continue
        if not urls:
            continue
        print(f"\n### {iso}")
        for url in urls:
            print(f"  {url}")
            print(f"      {_probe(url)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
