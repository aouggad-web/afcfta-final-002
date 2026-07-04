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
from bs4 import BeautifulSoup

# Mots-clés d'un lien/formulaire menant à une base tarifaire (FR/EN/PT/AR-lat).
TARIFF_KEYWORDS = re.compile(
    r"tarif|tariff|nomenclat|douan|customs|hs\s*code|sh\d|harmoniz|"
    r"position|pauta|aduaneir|classific|import\s*dut|\bndp\b",
    re.IGNORECASE,
)

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


def _dump_tariff_links(url: str) -> str:
    """Fetche une page et liste ancres + formulaires qui semblent mener à une
    base tarifaire (mots-clés). Sert à localiser la vraie page tarif avant
    d'écrire un scraper."""
    try:
        with httpx.Client(
            headers=HEADERS, timeout=25.0, follow_redirects=True, verify=False
        ) as client:
            resp = client.get(url)
    except Exception as e:  # noqa: BLE001
        return f"ERREUR {type(e).__name__}: {str(e)[:120]}"
    if resp.status_code != 200:
        return f"HTTP {resp.status_code} — pas d'analyse de liens"
    soup = BeautifulSoup(resp.text, "html.parser")
    base = str(resp.url)
    out: List[str] = []
    seen = set()
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]
        if TARIFF_KEYWORDS.search(text) or TARIFF_KEYWORDS.search(href):
            full = httpx.URL(base).join(href)
            key = str(full)
            if key in seen:
                continue
            seen.add(key)
            out.append(f"      LIEN [{text[:45]!r}] -> {str(full)[:95]}")
    for form in soup.find_all("form"):
        action = form.get("action", "")
        fields = [i.get("name") for i in form.find_all(["input", "select"]) if i.get("name")]
        ftext = form.get_text(" ", strip=True)[:60]
        if (
            TARIFF_KEYWORDS.search(action)
            or TARIFF_KEYWORDS.search(ftext)
            or any(TARIFF_KEYWORDS.search(f or "") for f in fields)
        ):
            full = httpx.URL(base).join(action) if action else base
            out.append(f"      FORM action={str(full)[:80]} champs={fields[:8]}")
    return "\n".join(out) if out else "      (aucun lien/formulaire tarifaire détecté)"


def main() -> int:
    args = [a for a in sys.argv[1:]]
    deep = "--links" in args
    # URL brute passée en argument -> sonde directe (repérage ciblé d'une page
    # tarif découverte, ex. etariff.douanes.gov.mg — sans éditer CANDIDATES).
    raw_urls = [a for a in args if a.startswith("http://") or a.startswith("https://")]
    only = {a.upper() for a in args if not a.startswith("--") and a not in raw_urls}

    for url in raw_urls:
        print(f"\n### URL {url}")
        print(f"      {_probe(url)}")
        if deep:
            print(_dump_tariff_links(url))

    for iso, urls in CANDIDATES.items():
        if raw_urls and not only:
            break
        if only and iso not in only:
            continue
        if not urls:
            continue
        print(f"\n### {iso}")
        for url in urls:
            print(f"  {url}")
            print(f"      {_probe(url)}")
            if deep:
                print(_dump_tariff_links(url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
