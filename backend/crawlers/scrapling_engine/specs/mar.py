"""
Spec MAR — Maroc (wave 1 : pays à tarif national autonome, pivots CSV présents).

Adaptateur autour du scraper ÉPROUVÉ `crawlers/countries/morocco_douane_scraper.py`
(portail ADIL douane.gov.ma). Le scraper produit un dict de taxes CLÉ = libellé
long ("Droit d'Importation (DI)") ; on le convertit ici vers le contrat v2
(taxes par CODE court : DI/TPI/TVA/TIC) sans autre transformation.

Les préférences tarifaires par pays (ADIL info_3.asp) ne sont PAS extraites par
`scrape_chapter_with_taxes` (méthode non appelée dans la boucle production) —
ce spec les ajoute pour ne pas perdre la couche « avantages » du contrat v2.

ADIL est un portail à SESSION serveur (classic ASP) : chaque position doit être
sélectionnée par un POST sur SEARCH_URL avant que les pages de détail
(info_2/3/4.asp) ne renvoient SES données — sans ce POST elles renvoient encore
celles de la position précédente. Bug réel détecté par le gate qualité (pivots
CSV décalés d'exactement une position) avant correction ici.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Dict, List, Optional

import httpx

# Un crawl MAR complet fait des milliers de requêtes sur plusieurs heures : un
# aléa réseau isolé (ReadError, timeout, reset) ne doit pas faire échouer tout
# le run. Retry court avec backoff ; une position qui échoue malgré tout est
# journalisée et SAUTÉE (jamais de donnée fabriquée pour la remplacer).
_RETRY_ATTEMPTS = 4
_RETRY_BASE_DELAY = 3.0
_MAX_CONSECUTIVE_FAILURES = 25  # site probablement mort au-delà -> on arrête


async def _retry(coro_fn, *args, **kwargs):
    last_exc = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            return await coro_fn(*args, **kwargs)
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            last_exc = e
            if attempt < _RETRY_ATTEMPTS - 1:
                await asyncio.sleep(_RETRY_BASE_DELAY * (attempt + 1))
    raise last_exc


COUNTRY_NAME = "Maroc"
SOURCE = "douane.gov.ma/adil"

# Ordre/assiette NON confirmés indépendamment (à sourcer sur le code des douanes
# marocain) — on ne fabrique pas de règle : seul le champ "source" est renseigné.
CALCULATION_RULES: Dict = {
    "order": ["DI", "TPI", "TVA", "TIC"],
    "bases": {},
    "source": "Ordre non confirmé indépendamment — à sourcer (code des douanes marocain).",
}

_TAX_LABEL_TO_CODE = {
    "Droit d'Importation (DI)": "DI",
    "Taxe Parafiscale à l'Importation (TPI)": "TPI",
    "Taxe sur la Valeur Ajoutée (TVA)": "TVA",
    "Taxe Intérieure de Consommation (TIC)": "TIC",
}


def crawl(max_positions: Optional[int] = None) -> List[Dict]:
    from crawlers.countries.morocco_douane_scraper import FORM_URL, SEARCH_URL, MoroccoDouaneScraper

    chapters_env = os.getenv("CRAWL_CHAPTERS", "").strip()
    chapters = [c.strip().zfill(2) for c in chapters_env.split(",") if c.strip()] or [
        "01",
        "04",
        "17",
        "27",
    ]

    async def _fetch_position(client, scraper, code: str) -> Dict:
        await client.post(
            SEARCH_URL,
            data={"lposition": code},
            headers={"Referer": FORM_URL, "Content-Type": "application/x-www-form-urlencoded"},
        )
        taxes_raw = await scraper.get_position_taxes(client, code)
        formalities_raw = await scraper.get_position_formalities(client, code)
        preferences_raw = await scraper.get_position_preferences(client, code)
        return {
            "taxes_raw": taxes_raw,
            "formalities_raw": formalities_raw,
            "preferences_raw": preferences_raw,
        }

    async def _run() -> List[Dict]:
        scraper = MoroccoDouaneScraper()
        client = scraper._new_client()
        out: List[Dict] = []
        skipped = 0
        consecutive_failures = 0
        try:
            await _retry(client.get, "https://www.douane.gov.ma/adil/")
            await _retry(client.get, FORM_URL)
            for chapter in chapters:
                positions = await _retry(scraper.get_chapter_positions, chapter)
                if max_positions:
                    remaining = max_positions - len(out)
                    if remaining <= 0:
                        break
                    positions = positions[:remaining]
                for pos in positions:
                    code = pos["code"]
                    try:
                        fetched = await _retry(_fetch_position, client, scraper, code)
                        consecutive_failures = 0
                    except (httpx.TransportError, httpx.HTTPStatusError) as e:
                        skipped += 1
                        consecutive_failures += 1
                        print(f"[mar] {code} sauté après échecs réseau : {e}", file=sys.stderr)
                        if consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                            print(
                                f"[mar] {consecutive_failures} échecs consécutifs — "
                                "portail probablement indisponible, arrêt du crawl.",
                                file=sys.stderr,
                            )
                            raise SystemExit(1)
                        continue

                    taxes = {}
                    for label, value in fetched["taxes_raw"].items():
                        tax_code = _TAX_LABEL_TO_CODE.get(label)
                        if not tax_code:
                            continue
                        rate = None
                        if isinstance(value, str) and "%" in value:
                            try:
                                rate = float(value.replace("%", "").strip().replace(",", "."))
                            except ValueError:
                                rate = None
                        taxes[tax_code] = {"name": label, "rate": rate, "raw": value}

                    out.append(
                        {
                            "hs_code": code,
                            "chapter": pos.get("chapter", code[:2]),
                            "name": pos.get("designation", ""),
                            "description": pos.get("designation", ""),
                            "taxes": taxes,
                            "advantages": fetched["preferences_raw"],
                            "formalities": fetched["formalities_raw"],
                            "source": SOURCE,
                        }
                    )
                    await asyncio.sleep(2.0)
                if max_positions and len(out) >= max_positions:
                    break
        finally:
            await client.aclose()
        if skipped:
            print(
                f"[mar] {skipped} position(s) sautée(s) (échecs réseau persistants)",
                file=sys.stderr,
            )
        return out

    return asyncio.run(_run())
