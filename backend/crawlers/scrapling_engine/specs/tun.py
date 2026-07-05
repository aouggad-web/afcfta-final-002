"""
Spec TUN — Tunisie (wave 1 : pays à tarif national autonome ; export CSV existant mais pivots non vérifiables automatiquement).

Adaptateur autour du scraper ÉPROUVÉ `crawlers/countries/tunisia_douane_scraper.py`
(portail douane.gov.tn/tarifweb2025). Conversion vers le contrat v2 :
  - taxes_import (liste {code,name,rate_pct,raw_value}) -> taxes {code: {...}}
  - preferences (liste {country_code,country_name,rate}) -> advantages (texte)
  - reglementation_import (liste {code,description}) -> formalities (texte)
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Dict, List, Optional

COUNTRY_NAME = "Tunisie"
SOURCE = "douane.gov.tn/tarifweb2025"

# get_position_detail retourne un dict par défaut (jamais d'exception) même en
# échec réseau — le scraper retente déjà en interne (_fetch_page, 3 tentatives).
# Filet de sécurité supplémentaire pour un crawl de plusieurs heures : au-delà
# d'une longue série de positions manifestement vides (échec réseau persistant
# malgré les retries internes), on arrête plutôt que de publier un jeu épars.
_MAX_CONSECUTIVE_EMPTY = 40

CALCULATION_RULES: Dict = {
    "order": [],
    "bases": {},
    "source": "Ordre/assiette non confirmés indépendamment — à sourcer (code des douanes tunisien).",
}


def crawl(max_positions: Optional[int] = None) -> List[Dict]:
    from crawlers.countries.tunisia_douane_scraper import TunisiaDouaneScraper

    chapters_env = os.getenv("CRAWL_CHAPTERS", "").strip()
    chapters = [c.strip().zfill(2) for c in chapters_env.split(",") if c.strip()] or [
        "01",
        "04",
        "17",
        "27",
    ]

    async def _run() -> List[Dict]:
        scraper = TunisiaDouaneScraper()
        out: List[Dict] = []
        consecutive_empty = 0
        try:
            for chapter in chapters:
                positions = await scraper.get_chapter_positions(chapter)
                if max_positions:
                    remaining = max_positions - len(out)
                    if remaining <= 0:
                        break
                    positions = positions[:remaining]
                for pos in positions:
                    detail = await scraper.get_position_detail(
                        pos["choix"], pos["chapter"], pos["code"]
                    )
                    if not any(
                        detail.get(k)
                        for k in ("taxes_import", "preferences", "reglementation_import")
                    ):
                        consecutive_empty += 1
                        print(f"[tun] {pos['code']} sans donnée (échec réseau ?)", file=sys.stderr)
                        if consecutive_empty >= _MAX_CONSECUTIVE_EMPTY:
                            print(
                                f"[tun] {consecutive_empty} positions vides consécutives — "
                                "portail probablement indisponible, arrêt du crawl.",
                                file=sys.stderr,
                            )
                            raise SystemExit(1)
                        continue
                    consecutive_empty = 0

                    taxes = {}
                    for t in detail.get("taxes_import", []):
                        code = (t.get("code") or "").strip()
                        if not code:
                            continue
                        taxes[code] = {
                            "name": t.get("name", ""),
                            "rate": t.get("rate_pct"),
                            "raw": t.get("raw_value", ""),
                        }

                    advantages = [
                        f"Préférence tarifaire {p.get('country_name', '').strip()} : "
                        f"{p.get('rate', '').strip()}"
                        for p in detail.get("preferences", [])
                        if p.get("country_name")
                    ]
                    formalities = [
                        r.get("description", "").strip()
                        for r in detail.get("reglementation_import", [])
                        if r.get("description")
                    ]

                    out.append(
                        {
                            "hs_code": pos["code"],
                            "chapter": pos.get("chapter", pos["code"][:2]),
                            "name": pos.get("designation", ""),
                            "description": pos.get("designation", ""),
                            "taxes": taxes,
                            "advantages": advantages,
                            "formalities": formalities,
                            "source": SOURCE,
                        }
                    )
                    await asyncio.sleep(1.5)
                if max_positions and len(out) >= max_positions:
                    break
        finally:
            await scraper._close_client()
        return out

    return asyncio.run(_run())
