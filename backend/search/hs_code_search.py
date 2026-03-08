"""
Advanced HS Code Search with fuzzy matching and natural-language queries.
Uses only stdlib difflib – no external ML dependencies required.
"""

from __future__ import annotations

import difflib
import re
from typing import Any

# ~50 common HS codes across major chapters used in African trade
_HS_CATALOGUE: list[dict[str, Any]] = [
    {"code": "0101.21", "chapter": 1, "description": "Live horses, pure-bred breeding"},
    {"code": "0201.10", "chapter": 2, "description": "Carcasses and half-carcasses of bovine animals, fresh or chilled"},
    {"code": "0302.13", "chapter": 3, "description": "Salmon, fresh or chilled, excluding fillets"},
    {"code": "0401.10", "chapter": 4, "description": "Milk and cream, not concentrated, fat ≤1%"},
    {"code": "0701.10", "chapter": 7, "description": "Seed potatoes, fresh or chilled"},
    {"code": "0803.90", "chapter": 8, "description": "Bananas, fresh or dried (other)"},
    {"code": "0901.11", "chapter": 9, "description": "Coffee, not roasted, not decaffeinated"},
    {"code": "1001.91", "chapter": 10, "description": "Wheat seed, other than durum"},
    {"code": "1006.10", "chapter": 10, "description": "Rice in the husk (paddy or rough)"},
    {"code": "1201.90", "chapter": 12, "description": "Soybeans, whether or not broken (other)"},
    {"code": "1511.10", "chapter": 15, "description": "Crude palm oil"},
    {"code": "1701.12", "chapter": 17, "description": "Raw cane sugar, for refining"},
    {"code": "1801.00", "chapter": 18, "description": "Cocoa beans, whole or broken, raw or roasted"},
    {"code": "2101.11", "chapter": 21, "description": "Extracts, essences and concentrates of coffee"},
    {"code": "2203.00", "chapter": 22, "description": "Beer made from malt"},
    {"code": "2402.20", "chapter": 24, "description": "Cigarettes containing tobacco"},
    {"code": "2709.00", "chapter": 27, "description": "Petroleum oils and oils from bituminous minerals, crude"},
    {"code": "2710.12", "chapter": 27, "description": "Light oils and preparations from petroleum"},
    {"code": "2711.12", "chapter": 27, "description": "Propane, liquefied"},
    {"code": "2716.00", "chapter": 27, "description": "Electrical energy"},
    {"code": "3004.20", "chapter": 30, "description": "Medicaments containing antibiotics"},
    {"code": "3808.91", "chapter": 38, "description": "Insecticides put up for retail sale"},
    {"code": "3901.10", "chapter": 39, "description": "Polyethylene having a specific gravity < 0.94"},
    {"code": "4011.10", "chapter": 40, "description": "New pneumatic tyres, of rubber, for motor cars"},
    {"code": "4407.10", "chapter": 44, "description": "Wood sawn or chipped lengthwise, coniferous"},
    {"code": "5201.00", "chapter": 52, "description": "Cotton, not carded or combed"},
    {"code": "5208.11", "chapter": 52, "description": "Woven fabrics of cotton, plain weave, ≤100 g/m²"},
    {"code": "6109.10", "chapter": 61, "description": "T-shirts, singlets and similar garments, of cotton, knitted"},
    {"code": "6203.42", "chapter": 62, "description": "Men's trousers and breeches, of cotton"},
    {"code": "6402.99", "chapter": 64, "description": "Other footwear with outer soles and uppers of rubber"},
    {"code": "7108.12", "chapter": 71, "description": "Gold in non-monetary form, other unwrought"},
    {"code": "7204.10", "chapter": 72, "description": "Waste and scrap of cast iron"},
    {"code": "7601.10", "chapter": 76, "description": "Aluminium, not alloyed, unwrought"},
    {"code": "8414.51", "chapter": 84, "description": "Table, floor, wall, window, ceiling or roof fans"},
    {"code": "8471.30", "chapter": 84, "description": "Portable automatic data-processing machines (laptops)"},
    {"code": "8481.80", "chapter": 84, "description": "Taps, cocks, valves and similar appliances"},
    {"code": "8507.60", "chapter": 85, "description": "Lithium-ion accumulators (batteries)"},
    {"code": "8517.12", "chapter": 85, "description": "Telephones for cellular networks (smartphones)"},
    {"code": "8528.72", "chapter": 85, "description": "Colour television receivers"},
    {"code": "8703.23", "chapter": 87, "description": "Motor cars with spark-ignition engine, 1000–1500 cc"},
    {"code": "8704.21", "chapter": 87, "description": "Motor vehicles for goods transport, diesel, ≤5 t GVW"},
    {"code": "8802.30", "chapter": 88, "description": "Aeroplanes, unladen weight 2 000–15 000 kg"},
    {"code": "8901.10", "chapter": 89, "description": "Cruise ships and similar vessels for transport of persons"},
    {"code": "9006.53", "chapter": 90, "description": "Cameras for photography (other)"},
    {"code": "9403.60", "chapter": 94, "description": "Other wooden furniture"},
    {"code": "9503.00", "chapter": 95, "description": "Tricycles, scooters, pedal cars and similar wheeled toys"},
    {"code": "9701.10", "chapter": 97, "description": "Paintings, drawings and pastels"},
    {"code": "2601.11", "chapter": 26, "description": "Iron ores and concentrates, non-agglomerated"},
    {"code": "2603.00", "chapter": 26, "description": "Copper ores and concentrates"},
    {"code": "2606.00", "chapter": 26, "description": "Aluminium ores and concentrates (bauxite)"},
    {"code": "2614.00", "chapter": 26, "description": "Titanium ores and concentrates"},
]

_CHAPTER_DESCRIPTIONS: dict[int, str] = {
    1: "Live animals",
    2: "Meat and edible meat offal",
    3: "Fish and crustaceans",
    4: "Dairy produce; eggs; natural honey",
    7: "Edible vegetables, roots and tubers",
    8: "Edible fruit and nuts",
    9: "Coffee, tea, maté and spices",
    10: "Cereals",
    12: "Oil seeds and oleaginous fruits",
    15: "Animal or vegetable fats and oils",
    17: "Sugars and sugar confectionery",
    18: "Cocoa and cocoa preparations",
    21: "Miscellaneous edible preparations",
    22: "Beverages, spirits and vinegar",
    24: "Tobacco and manufactured tobacco substitutes",
    26: "Ores, slag and ash",
    27: "Mineral fuels, mineral oils and products",
    30: "Pharmaceutical products",
    38: "Miscellaneous chemical products",
    39: "Plastics and articles thereof",
    40: "Rubber and articles thereof",
    44: "Wood and articles of wood",
    52: "Cotton",
    61: "Knitted or crocheted clothing and accessories",
    62: "Not knitted or crocheted clothing and accessories",
    64: "Footwear",
    71: "Natural or cultured pearls, precious stones and metals",
    72: "Iron and steel",
    76: "Aluminium and articles thereof",
    84: "Nuclear reactors, boilers, machinery",
    85: "Electrical machinery and equipment",
    87: "Vehicles other than railway/tramway",
    88: "Aircraft, spacecraft",
    89: "Ships, boats and floating structures",
    90: "Optical, photographic, measuring instruments",
    94: "Furniture; bedding, mattresses",
    95: "Toys, games and sports equipment",
    97: "Works of art, collectors' pieces and antiques",
}


class AdvancedHSCodeSearch:
    """Search HS codes using fuzzy matching or natural-language descriptions."""

    def __init__(self) -> None:
        self._catalogue = _HS_CATALOGUE
        self._all_descriptions = [item["description"].lower() for item in self._catalogue]

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fuzzy_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return the *limit* best-matching HS codes using sequence-ratio scoring."""
        q = query.lower().strip()
        scored: list[tuple[float, dict[str, Any]]] = []
        for item, desc in zip(self._catalogue, self._all_descriptions):
            # ratio against description
            ratio_desc = difflib.SequenceMatcher(None, q, desc).ratio()
            # ratio against code
            ratio_code = difflib.SequenceMatcher(None, q, item["code"]).ratio()
            # partial substring bonus
            bonus = 0.2 if q in desc else 0.0
            score = max(ratio_desc, ratio_code) + bonus
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, item in scored[:limit]:
            results.append({**item, "match_score": round(score, 4)})
        return results

    def natural_language_search(self, description: str) -> list[dict[str, Any]]:
        """Extract keywords and return best-matching HS codes."""
        tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", description.lower()))
        stop_words = {"the", "and", "for", "are", "not", "with", "this", "that", "from"}
        tokens -= stop_words

        scored: list[tuple[int, dict[str, Any]]] = []
        for item in self._catalogue:
            desc_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", item["description"].lower()))
            hits = len(tokens & desc_words)
            if hits:
                scored.append((hits, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for hits, item in scored[:10]:
            results.append({**item, "keyword_matches": hits})
        return results

    def get_chapter_summary(self, chapter_num: int) -> dict[str, Any]:
        """Return chapter description and list of all known codes in that chapter."""
        codes_in_chapter = [item for item in self._catalogue if item["chapter"] == chapter_num]
        return {
            "chapter": chapter_num,
            "title": _CHAPTER_DESCRIPTIONS.get(chapter_num, f"Chapter {chapter_num}"),
            "total_codes_in_catalogue": len(codes_in_chapter),
            "codes": codes_in_chapter,
        }
