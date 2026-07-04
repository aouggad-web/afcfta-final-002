"""
Spec EGY — Égypte (wave 1 : pas de pivot CSV vérifié — le gate tourne sans
--pivots, seulement reference_check (si un EGY_tariffs.json existe déjà),
parsing_check et national_layer_check).

Adaptateur autour du scraper ÉPROUVÉ `crawlers/countries/egypt_tariffs_scraper.py`
(egyptariffs.com, base sur les données de l'Autorité douanière égyptienne).

Limite connue et assumée (pas de fabrication) : ce scraper n'extrait ni
avantages fiscaux ni formalités structurées — seule une éventuelle mention de
« restrictions » est remontée en formalité brute. Le national_layer_check du
gate le signalera honnêtement (positions_with_advantages == 0) plutôt que de
masquer le manque.
"""

from __future__ import annotations

from typing import Dict, List, Optional

COUNTRY_NAME = "Égypte"
SOURCE = "egyptariffs.com (données Autorité douanière égyptienne)"

CALCULATION_RULES: Dict = {
    "order": ["ID", "VAT"],
    "bases": {},
    "source": "Ordre/assiette non confirmés indépendamment — à sourcer (Presidential Decree 419/2018 et modificatifs).",
}


def crawl(max_positions: Optional[int] = None) -> List[Dict]:
    from crawlers.countries.egypt_tariffs_scraper import EgyptTariffsScraper

    scraper = EgyptTariffsScraper()
    scraper.scrape(max_positions=max_positions or 60, delay=1.5, resume=False)

    out: List[Dict] = []
    for pos in scraper.positions:
        code_clean = pos.get("code_clean") or ""
        taxes = {}
        for t in pos.get("taxes_detail", []):
            code = t.get("tax_code")
            if not code:
                continue
            taxes[code] = {"name": t.get("tax_name", ""), "rate": t.get("rate")}

        out.append(
            {
                "hs_code": code_clean,
                "chapter": code_clean[:2] if code_clean else "",
                "name": pos.get("designation_en") or pos.get("designation", ""),
                "description": pos.get("designation", ""),
                "taxes": taxes,
                "advantages": [],
                "formalities": pos.get("administrative_formalities", []),
                "source": SOURCE,
            }
        )
    return out
