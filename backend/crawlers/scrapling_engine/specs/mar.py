"""
Spec MAR — Maroc (wave 1 : pays à tarif national autonome, pivots CSV présents).

Adaptateur autour du scraper ÉPROUVÉ `crawlers/countries/morocco_douane_scraper.py`
(portail ADIL douane.gov.ma). Le scraper produit un dict de taxes CLÉ = libellé
long ("Droit d'Importation (DI)") ; on le convertit ici vers le contrat v2
(taxes par CODE court : DI/TPI/TVA/TIC) sans autre transformation.

Les préférences tarifaires par pays (ADIL info_3.asp) ne sont PAS extraites par
`scrape_chapter_with_taxes` (méthode non appelée dans la boucle production) —
ce spec les ajoute pour ne pas perdre la couche « avantages » du contrat v2.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Optional

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
    from crawlers.countries.morocco_douane_scraper import MoroccoDouaneScraper

    chapters_env = os.getenv("CRAWL_CHAPTERS", "").strip()
    chapters = [c.strip().zfill(2) for c in chapters_env.split(",") if c.strip()] or [
        "01",
        "04",
        "17",
        "27",
    ]

    async def _run() -> List[Dict]:
        scraper = MoroccoDouaneScraper()
        client = scraper._new_client()
        out: List[Dict] = []
        try:
            for chapter in chapters:
                positions = await scraper.get_chapter_positions(chapter)
                if max_positions:
                    remaining = max_positions - len(out)
                    if remaining <= 0:
                        break
                    positions = positions[:remaining]
                for pos in positions:
                    code = pos["code"]
                    taxes_raw = await scraper.get_position_taxes(client, code)
                    formalities_raw = await scraper.get_position_formalities(client, code)
                    preferences_raw = await scraper.get_position_preferences(client, code)

                    taxes = {}
                    for label, value in taxes_raw.items():
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
                            "advantages": preferences_raw,
                            "formalities": formalities_raw,
                            "source": SOURCE,
                        }
                    )
                if max_positions and len(out) >= max_positions:
                    break
        finally:
            await client.aclose()
        return out

    return asyncio.run(_run())
