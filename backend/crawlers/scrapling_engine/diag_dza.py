"""
Diagnostic DZA — dump BRUT des blocs vstack d'une page sous-position.

But : trancher la divergence étalon (JSON committé 2026-06-18 vs crawl frais
2026-07-04) sur les positions NON couvertes par les pivots vérifiés à la main.
Le même parser page-par-page a produit les deux jeux à 17 jours d'écart avec
~93 % de divergence intra-rangée — impossible sans une lecture erronée d'un
côté. Seul le HTML LIVE de conformepro.dz (accessible du runner GitHub) tranche.

Pour chaque code SH demandé : récupère sa page (URL prise dans le JSON committé),
imprime TOUS les blocs `div.vstack` (h2 -> valeur fw-bold / contenu fs-3), et
rappelle les taxes stockées dans le committé. On voit ainsi, en clair, ce que la
page officielle affiche réellement pour DD/TVA/TCS/PRCT/DAPS.

Usage (sur le runner) :
    python -m crawlers.scrapling_engine.diag_dza 2710121100 2710121900 0402213400 \
        0401101000 0101299100 2707301000 2711292100
Aucun réseau requis en local (bloqué) — ce module tourne dans le workflow diag.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

from crawlers.countries.algeria_conformepro_scraper import AlgeriaConformeproScraper

BACKEND = Path(__file__).resolve().parent.parent.parent
COMMITTED = BACKEND / "data" / "crawled" / "DZA_tariffs.json"


def _committed_index() -> Dict[str, Dict]:
    data = json.load(open(COMMITTED, encoding="utf-8"))
    return {p.get("hs_code"): p for p in data.get("sub_positions", []) if p.get("hs_code")}


def _dump_vstacks(html: str) -> List[Dict[str, str]]:
    """Retourne la liste ordonnée de tous les blocs vstack : {label, value}."""
    soup = BeautifulSoup(html, "html.parser")
    blocks: List[Dict[str, str]] = []
    for div in soup.find_all("div", class_="vstack"):
        h2 = div.find("h2")
        label = h2.get_text(strip=True) if h2 else "(sans h2)"
        p = div.find("p", class_=lambda c: c and "fw-bold" in c)
        if p:
            value = p.get_text(" ", strip=True)
        else:
            div_fs = div.find("div", class_="fs-3")
            value = div_fs.get_text(" ", strip=True)[:200] if div_fs else "(vide)"
        blocks.append({"label": label, "value": value})
    return blocks


async def _run(hs_codes: List[str]) -> None:
    idx = _committed_index()
    scraper = AlgeriaConformeproScraper()
    try:
        for hs in hs_codes:
            pos = idx.get(hs)
            if not pos:
                print(f"\n### {hs} — ABSENT du committé (URL inconnue)")
                continue
            url = pos.get("source_url", "")
            committed_taxes = {k: v.get("rate") for k, v in (pos.get("taxes") or {}).items()}
            print(f"\n### {hs}  ch{pos.get('chapter')}  {(pos.get('name') or '')[:55]}")
            print(f"    URL         : {url}")
            print(f"    committé    : {committed_taxes}")
            html = await scraper._fetch_page(url)
            if not html:
                print("    LIVE        : (échec de récupération)")
                continue
            blocks = _dump_vstacks(html)
            print(f"    LIVE vstacks ({len(blocks)}) :")
            for b in blocks:
                print(f"      - {b['label']!r:32} -> {b['value']!r}")
    finally:
        await scraper._close_client()


def main() -> int:
    hs_codes = sys.argv[1:]
    if not hs_codes:
        print("Usage: python -m crawlers.scrapling_engine.diag_dza <hs_code> [hs_code ...]")
        return 2
    asyncio.run(_run(hs_codes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
