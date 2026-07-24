"""
Spec ETH — Éthiopie (wave 2 : pays à tarif national autonome, COMESA/IGAD sans
TEC contraignant).

Adaptateur autour du scraper ÉPROUVÉ `crawlers/countries/ethiopia_customs_scraper.py`
— vrai scrape HTTP live du portail douanier officiel (customs.erca.gov.et).
Aucun pivot CSV vérifié pour ETH : le gate tourne sans --pivots (reference_check
si un ETH_tariffs.json existe déjà, parsing_check, national_layer_check).

Limite connue et assumée (pas de fabrication) : ce scraper ne remonte pas de
formalités structurées. Il expose en revanche le droit préférentiel COMESA
(colonnes D2R / comesa_duty) qu'on remonte comme avantage. national_layer_check
signalera honnêtement l'absence de formalités plutôt que de la masquer.
"""

from __future__ import annotations

from typing import Dict, List, Optional

COUNTRY_NAME = "Éthiopie"
SOURCE = "customs.erca.gov.et (portail douanier officiel)"

CALCULATION_RULES: Dict = {
    "order": [],
    "bases": {},
    "source": "Ordre/assiette non confirmés indépendamment — à sourcer (proclamation tarifaire éthiopienne).",
}

# ≈ positions par rangée HS4 observées — pour convertir une borne max_positions
# en nombre de chapitres/rangées à crawler (le scraper borne par max_chapters).
_POSITIONS_PER_CHAPTER = 40


def crawl(max_positions: Optional[int] = None) -> List[Dict]:
    from crawlers.countries.ethiopia_customs_scraper import EthiopiaCustomsScraper

    max_chapters = None
    if max_positions:
        max_chapters = max(1, max_positions // _POSITIONS_PER_CHAPTER)

    scraper = EthiopiaCustomsScraper()
    scraper.scrape(max_chapters=max_chapters, delay=1.0, resume=False)

    out: List[Dict] = []
    for pos in scraper.positions:
        if max_positions and len(out) >= max_positions:
            break
        code_clean = pos.get("code_clean") or ""

        taxes = {}
        detail_by_code = {d.get("tax_code"): d for d in pos.get("taxes_detail", [])}
        for code, rate in (pos.get("taxes") or {}).items():
            name = (detail_by_code.get(code) or {}).get("tax_name", code)
            taxes[code] = {"name": name, "rate": rate}

        # Droit préférentiel COMESA (le cas échéant) : avantage, pas taxe nationale.
        advantages = []
        comesa = pos.get("comesa_duty")
        if comesa is not None:
            advantages.append(f"Droit préférentiel COMESA (D2R) : {comesa}%")

        out.append(
            {
                "hs_code": code_clean,
                "chapter": code_clean[:2] if code_clean else "",
                "name": pos.get("designation_en") or pos.get("designation", ""),
                "description": pos.get("designation", ""),
                "taxes": taxes,
                "advantages": advantages,
                "formalities": [],
                "source": SOURCE,
            }
        )
    return out
