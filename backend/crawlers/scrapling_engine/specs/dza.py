"""
Spec DZA — Algérie (étalon qualité du plan docs/PLAN_SCRAPLING_CRAWLERS.md).

Adaptateur autour du scraper ÉPROUVÉ `crawlers/countries/
algeria_conformepro_scraper.py` (DOM confirmé de conformepro.dz, données
douane.gov.dz — celui qui a produit les 17 061 positions committées). On ne
réécrit pas des sélecteurs à l'aveugle : Scrapling n'interviendra que si le
site se durcit (anti-bot / refonte).

Différences avec l'orchestrateur historique :
  - pas de save_final() (pas d'écriture directe dans data/crawled pendant un
    run `validate` — le runner/gate décident de la publication) ;
  - resume désactivé (déterminisme sur runner neuf) ;
  - borne `max_positions` → approximée en nombre de rangées (headings).

Throttle hérité : 1,5 s/page → crawl complet ≈ plusieurs heures. L'étalonnage
complet se fait PAR TRANCHES via la variable d'env CRAWL_CHAPTERS
(ex. "01,02,03") ou une borne max_positions ; le gate agrège ensuite.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Optional

COUNTRY_NAME = "Algérie"
SOURCE = "conformepro.dz (données douane.gov.dz)"

# Méthode de calcul (contrat v2 §4) — telle qu'appliquée par le Calculateur de
# la plateforme et VALIDÉE numériquement sur ses réponses (ex. TVA 19 % assise
# sur CIF+DD+TCS+PRCT). Références légales détaillées (code des douanes, LF en
# vigueur) à citer lors du crawl des pages officielles correspondantes.
CALCULATION_RULES: Dict = {
    "order": ["DD", "TCS", "PRCT", "DAPS", "TVA"],
    "bases": {
        "DD": {"basis": "CIF", "type": "ad_valorem"},
        "TCS": {"basis": "CIF", "type": "ad_valorem"},
        "PRCT": {"basis": "CIF", "type": "ad_valorem"},
        "DAPS": {"basis": "CIF", "type": "ad_valorem"},
        "TVA": {"basis": "CIF + DD + TCS + PRCT + DAPS", "type": "ad_valorem"},
    },
    "source": (
        "Implémentation opérationnelle du calculateur de la plateforme "
        "(cohérente douane.gov.dz) ; références légales à joindre au crawl."
    ),
}

# ≈ positions par rangée (heading) observées sur le dataset existant.
_POSITIONS_PER_HEADING = 14


def crawl(max_positions: Optional[int] = None) -> List[Dict]:
    """Exécute le scraper conformepro et retourne les positions brutes
    (format directement consommé par normalizer.assemble_output)."""
    from crawlers.countries.algeria_conformepro_scraper import AlgeriaConformeproScraper

    max_headings = None
    if max_positions:
        max_headings = max(1, max_positions // _POSITIONS_PER_HEADING)

    chapters_env = os.getenv("CRAWL_CHAPTERS", "").strip()
    chapters = {c.strip().zfill(2) for c in chapters_env.split(",") if c.strip()} or None

    async def _run() -> List[Dict]:
        scraper = AlgeriaConformeproScraper()
        try:
            await scraper.scrape_sections()
            await scraper.scrape_chapters()
            if chapters:
                scraper.chapters = [c for c in scraper.chapters if c["code"] in chapters]
            await scraper.scrape_headings()
            await scraper.scrape_all_sub_positions(max_headings=max_headings, resume=False)
        finally:
            await scraper._close_client()
        return scraper.sub_positions

    return asyncio.run(_run())
