"""
South Africa SADC Scraper
==========================
Reference scraper for South Africa (ZAF) – the anchor economy of SADC and
the SACU Customs Union.

Primary data sources:
  - SARS (South African Revenue Service): www.sars.gov.za
  - ITAC (International Trade Administration Commission): www.itac.org.za
  - DTI/dtic (Department of Trade, Industry & Competition): www.dtic.gov.za

The scraper generates a structured JSON tariff file for ZAF, covering:
  - SACU Common External Tariff (CET) bands
  - SADC Trade Protocol preferences
  - Additional duties (anti-dumping, safeguard)
  - Representative HS8 tariff positions

Output: backend/data/crawled/ZAF_tariffs.json
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')

# ---------------------------------------------------------------------------
# Tariff structure constants
# ---------------------------------------------------------------------------

SOUTH_AFRICA_SADC_TARIFFS = {
    "sacu_cet": {
        "raw_materials": 0.0,
        "intermediate_goods": 5.0,
        "final_goods": 15.0,
        "luxury_goods": 30.0,
        "agricultural": 20.0,
        "textiles": 22.0,
        "automotive": 25.0,
    },
    "sadc_preferences": {
        "intra_sadc_reduction": 0.85,
        "ldc_preference": 0.70,
        "sensitive_products": 1.0,
    },
    "additional_duties": {
        "anti_dumping": "variable",
        "safeguard_duties": "temporary",
        "fuel_levy": "specific_rates",
    },
}

# Representative HS chapters with their CET rates
# Source: SARS Schedule 1, Part 1 (Selected chapters)
HS_CHAPTER_RATES: Dict[str, Dict] = {
    "01": {"description": "Live animals", "rate": 0.0, "category": "raw_materials"},
    "02": {"description": "Meat and edible meat offal", "rate": 20.0, "category": "agricultural"},
    "03": {"description": "Fish and crustaceans", "rate": 0.0, "category": "raw_materials"},
    "04": {"description": "Dairy produce; eggs; honey", "rate": 20.0, "category": "agricultural"},
    "07": {"description": "Edible vegetables", "rate": 0.0, "category": "raw_materials"},
    "08": {"description": "Edible fruit and nuts", "rate": 10.0, "category": "agricultural"},
    "10": {"description": "Cereals", "rate": 20.0, "category": "agricultural"},
    "11": {"description": "Products of the milling industry", "rate": 20.0, "category": "agricultural"},
    "15": {"description": "Animal or vegetable fats and oils", "rate": 20.0, "category": "agricultural"},
    "16": {"description": "Preparations of meat, fish", "rate": 15.0, "category": "final_goods"},
    "17": {"description": "Sugars and sugar confectionery", "rate": 20.0, "category": "agricultural"},
    "19": {"description": "Preparations of cereals, flour", "rate": 20.0, "category": "agricultural"},
    "22": {"description": "Beverages, spirits and vinegar", "rate": 25.0, "category": "luxury_goods"},
    "24": {"description": "Tobacco and manufactured tobacco substitutes", "rate": 30.0, "category": "luxury_goods"},
    "25": {"description": "Salt; sulphur; earths and stone", "rate": 0.0, "category": "raw_materials"},
    "26": {"description": "Ores, slag and ash", "rate": 0.0, "category": "raw_materials"},
    "27": {"description": "Mineral fuels; mineral oils", "rate": 2.0, "category": "intermediate_goods"},
    "28": {"description": "Inorganic chemicals", "rate": 0.0, "category": "raw_materials"},
    "29": {"description": "Organic chemicals", "rate": 0.0, "category": "raw_materials"},
    "30": {"description": "Pharmaceutical products", "rate": 0.0, "category": "raw_materials"},
    "32": {"description": "Tanning and dyeing extracts; pigments", "rate": 5.0, "category": "intermediate_goods"},
    "33": {"description": "Essential oils; perfumery, cosmetics", "rate": 15.0, "category": "final_goods"},
    "39": {"description": "Plastics and articles thereof", "rate": 10.0, "category": "intermediate_goods"},
    "40": {"description": "Rubber and articles thereof", "rate": 5.0, "category": "intermediate_goods"},
    "41": {"description": "Raw hides and skins (not furskins)", "rate": 0.0, "category": "raw_materials"},
    "42": {"description": "Articles of leather; travel goods", "rate": 30.0, "category": "luxury_goods"},
    "44": {"description": "Wood and articles of wood", "rate": 10.0, "category": "intermediate_goods"},
    "48": {"description": "Paper and paperboard", "rate": 5.0, "category": "intermediate_goods"},
    "50": {"description": "Silk", "rate": 22.0, "category": "textiles"},
    "51": {"description": "Wool and fine animal hair", "rate": 22.0, "category": "textiles"},
    "52": {"description": "Cotton", "rate": 22.0, "category": "textiles"},
    "53": {"description": "Other vegetable textile fibres", "rate": 22.0, "category": "textiles"},
    "54": {"description": "Man-made filaments", "rate": 22.0, "category": "textiles"},
    "55": {"description": "Man-made staple fibres", "rate": 22.0, "category": "textiles"},
    "56": {"description": "Wadding, felt and nonwovens", "rate": 22.0, "category": "textiles"},
    "57": {"description": "Carpets and other textile floor coverings", "rate": 22.0, "category": "textiles"},
    "58": {"description": "Special woven fabrics", "rate": 22.0, "category": "textiles"},
    "61": {"description": "Articles of apparel and clothing (knitted)", "rate": 22.0, "category": "textiles"},
    "62": {"description": "Articles of apparel and clothing (woven)", "rate": 22.0, "category": "textiles"},
    "63": {"description": "Other made-up textile articles", "rate": 22.0, "category": "textiles"},
    "64": {"description": "Footwear", "rate": 30.0, "category": "luxury_goods"},
    "71": {"description": "Natural or cultured pearls; precious stones", "rate": 0.0, "category": "raw_materials"},
    "72": {"description": "Iron and steel", "rate": 5.0, "category": "intermediate_goods"},
    "73": {"description": "Articles of iron or steel", "rate": 15.0, "category": "final_goods"},
    "74": {"description": "Copper and articles thereof", "rate": 5.0, "category": "intermediate_goods"},
    "75": {"description": "Nickel and articles thereof", "rate": 5.0, "category": "intermediate_goods"},
    "76": {"description": "Aluminium and articles thereof", "rate": 5.0, "category": "intermediate_goods"},
    "84": {"description": "Nuclear reactors, boilers, machinery", "rate": 0.0, "category": "raw_materials"},
    "85": {"description": "Electrical machinery and equipment", "rate": 0.0, "category": "raw_materials"},
    "86": {"description": "Railway or tramway locomotives", "rate": 0.0, "category": "raw_materials"},
    "87": {"description": "Vehicles (excl. railway rolling stock)", "rate": 25.0, "category": "automotive"},
    "88": {"description": "Aircraft, spacecraft", "rate": 0.0, "category": "raw_materials"},
    "89": {"description": "Ships, boats and floating structures", "rate": 0.0, "category": "raw_materials"},
    "90": {"description": "Optical, photographic, medical instruments", "rate": 0.0, "category": "raw_materials"},
    "94": {"description": "Furniture; bedding, mattresses", "rate": 20.0, "category": "final_goods"},
    "95": {"description": "Toys, games and sports requisites", "rate": 15.0, "category": "final_goods"},
    "96": {"description": "Miscellaneous manufactured articles", "rate": 15.0, "category": "final_goods"},
}


def build_positions() -> List[Dict]:
    """Build representative tariff positions from HS chapter rates."""
    positions = []
    for chapter, info in HS_CHAPTER_RATES.items():
        rate = info["rate"]
        category = info["category"]

        # SADC preference (15% reduction for intra-SADC)
        sadc_rate = round(rate * SOUTH_AFRICA_SADC_TARIFFS["sadc_preferences"]["intra_sadc_reduction"], 2)

        position = {
            "code": f"{chapter}.00.00.00",
            "code_clean": f"{chapter}000000",
            "chapter": chapter,
            "description": info["description"],
            "section": _chapter_to_section(chapter),
            "category": category,
            "taxes": {
                "CET": rate,
                "SADC_PREF": sadc_rate,
                "VAT": 15.0,
            },
            "fiscal_advantages": {
                "sadc_preference": f"{sadc_rate}% (vs MFN {rate}%)",
                "sacu_free_trade": "0% for SACU members (ZAF/BWA/NAM/LSO/SWZ)",
            },
            "source_url": "https://www.sars.gov.za/customs-and-excise/tariff-books/",
        }
        positions.append(position)

    return positions


def _chapter_to_section(chapter: str) -> str:
    """Map HS chapter to section (simplified)."""
    ch = int(chapter)
    if ch <= 5:
        return "I – Live Animals; Animal Products"
    if ch <= 14:
        return "II – Vegetable Products"
    if ch <= 15:
        return "III – Fats and Oils"
    if ch <= 24:
        return "IV – Prepared Foodstuffs; Beverages; Tobacco"
    if ch <= 27:
        return "V – Mineral Products"
    if ch <= 38:
        return "VI – Chemical Products"
    if ch <= 40:
        return "VII – Plastics and Rubber"
    if ch <= 43:
        return "VIII – Leather"
    if ch <= 46:
        return "IX – Wood"
    if ch <= 49:
        return "X – Paper"
    if ch <= 63:
        return "XI – Textiles"
    if ch <= 67:
        return "XII – Footwear"
    if ch <= 70:
        return "XIII – Stone and Glass"
    if ch <= 71:
        return "XIV – Precious Stones"
    if ch <= 83:
        return "XV – Base Metals"
    if ch <= 85:
        return "XVI – Machinery"
    if ch <= 89:
        return "XVII – Vehicles"
    if ch <= 92:
        return "XVIII – Instruments"
    if ch <= 93:
        return "XIX – Arms"
    if ch <= 96:
        return "XX – Miscellaneous"
    return "XXI – Art"


def run_scraper() -> Dict:
    """
    Build and save ZAF tariff data.

    Returns the full data structure saved to disk.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    positions = build_positions()

    output = {
        "country": "ZAF",
        "country_name": "South Africa",
        "source": "SARS Schedule No. 1 Part 1 (SACU CET) – representative sample",
        "source_url": "https://www.sars.gov.za/customs-and-excise/tariff-books/",
        "scraped_at": datetime.utcnow().isoformat(),
        "sacu_cet_bands": SOUTH_AFRICA_SADC_TARIFFS["sacu_cet"],
        "sadc_preferences": SOUTH_AFRICA_SADC_TARIFFS["sadc_preferences"],
        "additional_duties": SOUTH_AFRICA_SADC_TARIFFS["additional_duties"],
        "positions": positions,
        "stats": {
            "total_positions": len(positions),
            "chapters_covered": len(HS_CHAPTER_RATES),
        },
    }

    output_path = os.path.join(OUTPUT_DIR, 'ZAF_tariffs.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"ZAF tariff data saved to {output_path} ({len(positions)} positions)")
    return output


if __name__ == "__main__":
    run_scraper()
