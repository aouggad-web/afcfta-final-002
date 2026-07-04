"""
Reconnaissance d'une SPA JavaScript via Playwright (exécutée sur le runner).

Certains portails tarifaires sont des applications monopage : le HTML servi est
vide, les données viennent d'appels XHR/fetch vers une API JSON. httpx ne voit
rien. Ce module charge la page dans Chromium (déjà installé par le workflow),
CAPTURE toutes les requêtes réseau, et imprime celles qui ressemblent à l'API
(XHR/fetch, réponses JSON) avec un extrait du corps — de quoi rétro-concevoir
l'endpoint AVANT d'écrire le scraper.

Aucune donnée n'est extraite/stockée : c'est un repérage réseau.

Usage (workflow) :
    python -m crawlers.scrapling_engine.recon_js https://etariff.douanes.gov.mg/
"""

from __future__ import annotations

import asyncio
import sys
from typing import List

INTERESTING = ("xhr", "fetch")


async def _probe(url: str, wait_ms: int = 8000) -> None:
    from playwright.async_api import async_playwright

    captured: List[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        async def on_response(resp):
            try:
                req = resp.request
                rtype = req.resource_type
                ct = (resp.headers or {}).get("content-type", "")
                if rtype in INTERESTING or "json" in ct:
                    body = ""
                    if "json" in ct:
                        try:
                            body = (await resp.text())[:300]
                        except Exception:
                            body = "(corps illisible)"
                    captured.append(
                        {
                            "method": req.method,
                            "type": rtype,
                            "status": resp.status,
                            "ct": ct.split(";")[0],
                            "url": resp.url,
                            "body": body,
                        }
                    )
            except Exception:
                pass

        page.on("response", on_response)

        print(f"\n### PLAYWRIGHT {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception as e:  # noqa: BLE001
            print(f"    goto: {type(e).__name__}: {str(e)[:120]}")
        await page.wait_for_timeout(wait_ms)

        try:
            title = await page.title()
            print(f"    <title>: {title!r}")
        except Exception:
            pass

        # Phase interaction : cliquer chaque élément de navigation dont le texte
        # évoque le tarif (browse/search/parcourir) pour déclencher les XHR de
        # DONNÉES (les endpoints tarif ne partent qu'après navigation).
        nav_keywords = [
            "tariff",
            "tarif",
            "browse",
            "parcour",
            "search",
            "recherch",
            "chapter",
            "chapitre",
        ]
        try:
            anchors = await page.query_selector_all("a, button, [role=menuitem], li")
            clicked = 0
            for el in anchors:
                if clicked >= 8:
                    break
                try:
                    txt = ((await el.inner_text()) or "").strip().lower()
                except Exception:
                    continue
                if txt and any(k in txt for k in nav_keywords) and len(txt) < 40:
                    try:
                        await el.click(timeout=3000)
                        clicked += 1
                        await page.wait_for_timeout(3500)
                    except Exception:
                        continue
            print(f"    éléments de nav cliqués : {clicked}")
        except Exception as e:  # noqa: BLE001
            print(f"    interaction: {type(e).__name__}: {str(e)[:80]}")

        await browser.close()

    if not captured:
        print("    (aucune requête XHR/fetch/JSON capturée)")
        return
    print(f"    {len(captured)} requête(s) API capturée(s) :")
    seen = set()
    for c in captured:
        key = (c["method"], c["url"].split("?")[0])
        if key in seen:
            continue
        seen.add(key)
        print(f"      {c['method']} {c['status']} [{c['type']}/{c['ct']}] {c['url'][:110]}")
        if c["body"]:
            print(f"          body: {c['body']!r}")


def main() -> int:
    urls = [a for a in sys.argv[1:] if a.startswith("http")]
    if not urls:
        print("Usage: python -m crawlers.scrapling_engine.recon_js <url> [url ...]")
        return 2
    for url in urls:
        asyncio.run(_probe(url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
