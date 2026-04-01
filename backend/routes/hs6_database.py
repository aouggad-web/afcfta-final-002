"""
HS6 Database Routes
Routes for searching and browsing HS6 codes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import os
import json
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hs6")

# Load HS6 data
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Cache for HS6 data
_hs6_cache = None

# ---------------------------------------------------------------------------
# Module-level chapter name lookups (HS chapter 01-97)
# ---------------------------------------------------------------------------
CHAPTER_NAMES: Dict[str, Dict[str, str]] = {
    "fr": {
        "01": "Animaux vivants", "02": "Viandes et abats comestibles", "03": "Poissons, crustacés",
        "04": "Produits laitiers, œufs, miel", "05": "Autres produits d'origine animale",
        "06": "Plantes vivantes, fleurs", "07": "Légumes, plantes, racines", "08": "Fruits comestibles, écorces",
        "09": "Café, thé, épices", "10": "Céréales", "11": "Produits de la minoterie",
        "12": "Graines oléagineuses", "13": "Gommes, résines", "14": "Matières à tresser",
        "15": "Graisses et huiles", "16": "Préparations de viandes", "17": "Sucres et sucreries",
        "18": "Cacao et préparations", "19": "Préparations de céréales", "20": "Préparations de légumes/fruits",
        "21": "Préparations alimentaires diverses", "22": "Boissons, vinaigres", "23": "Résidus alimentaires",
        "24": "Tabacs", "25": "Sel, soufre, pierres", "26": "Minerais, scories",
        "27": "Combustibles, huiles minérales", "28": "Produits chimiques inorganiques",
        "29": "Produits chimiques organiques", "30": "Produits pharmaceutiques",
        "31": "Engrais", "32": "Tanins, colorants, peintures", "33": "Huiles essentielles, parfumerie",
        "34": "Savons, détergents", "35": "Matières albuminoïdes, colles", "36": "Poudres, explosifs",
        "37": "Produits photographiques", "38": "Produits chimiques divers",
        "39": "Matières plastiques", "40": "Caoutchouc", "41": "Peaux et cuirs",
        "42": "Ouvrages en cuir", "43": "Pelleteries, fourrures", "44": "Bois et ouvrages en bois",
        "45": "Liège", "46": "Ouvrages de sparterie", "47": "Pâtes de bois",
        "48": "Papiers et cartons", "49": "Produits de l'édition", "50": "Soie",
        "51": "Laine et poils fins", "52": "Coton", "53": "Autres fibres végétales",
        "54": "Filaments synthétiques", "55": "Fibres synthétiques discontinues",
        "56": "Ouates, feutres, cordages", "57": "Tapis", "58": "Tissus spéciaux",
        "59": "Tissus imprégnés", "60": "Étoffes de bonneterie", "61": "Vêtements en bonneterie",
        "62": "Vêtements autres qu'en bonneterie", "63": "Autres articles textiles",
        "64": "Chaussures", "65": "Coiffures", "66": "Parapluies", "67": "Plumes, fleurs artificielles",
        "68": "Ouvrages en pierres", "69": "Produits céramiques", "70": "Verre et ouvrages",
        "71": "Perles, pierres précieuses", "72": "Fonte, fer et acier", "73": "Ouvrages en fonte/fer/acier",
        "74": "Cuivre et ouvrages", "75": "Nickel et ouvrages", "76": "Aluminium et ouvrages",
        "78": "Plomb et ouvrages", "79": "Zinc et ouvrages", "80": "Étain et ouvrages",
        "81": "Autres métaux communs", "82": "Outils, coutellerie", "83": "Ouvrages divers en métaux",
        "84": "Machines et appareils mécaniques", "85": "Machines et appareils électriques",
        "86": "Véhicules ferroviaires", "87": "Véhicules automobiles", "88": "Navigation aérienne",
        "89": "Navigation maritime", "90": "Instruments optiques, médicaux",
        "91": "Horlogerie", "92": "Instruments de musique", "93": "Armes et munitions",
        "94": "Meubles, literie", "95": "Jouets, jeux", "96": "Ouvrages divers", "97": "Objets d'art",
    },
    "en": {
        "01": "Live animals", "02": "Meat and edible offal", "03": "Fish, crustaceans",
        "04": "Dairy, eggs, honey", "05": "Other animal products", "06": "Live plants, flowers",
        "07": "Vegetables, roots", "08": "Edible fruits", "09": "Coffee, tea, spices",
        "10": "Cereals", "11": "Milling products", "12": "Oil seeds", "13": "Gums, resins",
        "14": "Plaiting materials", "15": "Fats and oils", "16": "Meat preparations",
        "17": "Sugars", "18": "Cocoa preparations", "19": "Cereal preparations",
        "20": "Vegetable/fruit preparations", "21": "Misc food preparations", "22": "Beverages",
        "23": "Food residues", "24": "Tobacco", "25": "Salt, stones", "26": "Ores, slag",
        "27": "Mineral fuels", "28": "Inorganic chemicals", "29": "Organic chemicals",
        "30": "Pharmaceutical products", "31": "Fertilizers", "32": "Dyes, paints",
        "33": "Essential oils, perfumery", "34": "Soaps, detergents", "35": "Albumins, glues",
        "36": "Explosives", "37": "Photographic products", "38": "Misc chemicals",
        "39": "Plastics", "40": "Rubber", "41": "Hides and skins", "42": "Leather goods",
        "43": "Furs", "44": "Wood and articles", "45": "Cork", "46": "Basketware",
        "47": "Wood pulp", "48": "Paper and paperboard", "49": "Printed books",
        "50": "Silk", "51": "Wool", "52": "Cotton", "53": "Other vegetable fibers",
        "54": "Man-made filaments", "55": "Man-made staple fibers", "56": "Wadding, felt",
        "57": "Carpets", "58": "Special fabrics", "59": "Coated fabrics", "60": "Knitted fabrics",
        "61": "Knitted apparel", "62": "Woven apparel", "63": "Other textile articles",
        "64": "Footwear", "65": "Headgear", "66": "Umbrellas", "67": "Feathers, artificial flowers",
        "68": "Stone articles", "69": "Ceramic products", "70": "Glass and articles",
        "71": "Pearls, precious stones", "72": "Iron and steel", "73": "Iron/steel articles",
        "74": "Copper and articles", "75": "Nickel and articles", "76": "Aluminum and articles",
        "78": "Lead and articles", "79": "Zinc and articles", "80": "Tin and articles",
        "81": "Other base metals", "82": "Tools, cutlery", "83": "Misc metal articles",
        "84": "Machinery", "85": "Electrical machinery", "86": "Railway vehicles",
        "87": "Motor vehicles", "88": "Aircraft", "89": "Ships and boats",
        "90": "Optical, medical instruments", "91": "Clocks and watches",
        "92": "Musical instruments", "93": "Arms and ammunition", "94": "Furniture",
        "95": "Toys, games", "96": "Misc articles", "97": "Works of art",
    },
}

def load_hs6_data():
    """Load HS6 database"""
    global _hs6_cache
    if _hs6_cache is not None:
        return _hs6_cache
    
    hs6_file = os.path.join(DATA_DIR, "hs6_database.json")
    if os.path.exists(hs6_file):
        try:
            with open(hs6_file, 'r', encoding='utf-8') as f:
                _hs6_cache = json.load(f)
                return _hs6_cache
        except Exception as e:
            logger.error(f"Error loading HS6 database: {e}")
    return {}


@router.get("/search")
async def search_hs6(
    q: str = Query(..., min_length=2, description="Search query"),
    language: str = Query(default="fr"),
    limit: int = Query(default=20, le=100)
):
    """Search HS6 codes by description or code"""
    hs6_data = load_hs6_data()
    query = q.lower().strip()
    results = []
    
    for code, data in hs6_data.items():
        # Match by code
        if code.startswith(query.replace(".", "")):
            results.append({
                "code": code,
                "description": data.get(f"description_{language}", data.get("description_fr", "")),
                "chapter": code[:2],
                "match_type": "code"
            })
            continue
        
        # Match by description
        desc_fr = data.get("description_fr", "").lower()
        desc_en = data.get("description_en", "").lower()
        
        if query in desc_fr or query in desc_en:
            results.append({
                "code": code,
                "description": data.get(f"description_{language}", data.get("description_fr", "")),
                "chapter": code[:2],
                "match_type": "description"
            })
    
    # Sort: code matches first, then by code
    results.sort(key=lambda x: (x["match_type"] != "code", x["code"]))
    
    return {
        "query": q,
        "results": results[:limit],
        "total": len(results)
    }


@router.get("/info/{hs_code}")
async def get_hs6_info(
    hs_code: str,
    language: str = Query(default="fr")
):
    """Get detailed info for an HS6 code"""
    hs6_data = load_hs6_data()
    clean_code = hs_code.replace(".", "").replace(" ", "")[:6]
    
    if clean_code in hs6_data:
        data = hs6_data[clean_code]
        return {
            "code": clean_code,
            "description": data.get(f"description_{language}", data.get("description_fr", "")),
            "description_fr": data.get("description_fr", ""),
            "description_en": data.get("description_en", ""),
            "chapter": clean_code[:2],
            "heading": clean_code[:4],
            "found": True
        }
    
    return {
        "code": clean_code,
        "description": f"Code HS {clean_code}",
        "chapter": clean_code[:2],
        "heading": clean_code[:4],
        "found": False
    }


@router.get("/suggestions/{hs_code}")
async def get_hs6_suggestions(
    hs_code: str,
    language: str = Query(default="fr"),
    limit: int = Query(default=10)
):
    """Get suggestions for related HS codes"""
    hs6_data = load_hs6_data()
    clean_code = hs_code.replace(".", "").replace(" ", "")
    
    # Find codes starting with the same prefix
    prefix_lengths = [4, 2]  # Try heading first, then chapter
    suggestions = []
    
    for prefix_len in prefix_lengths:
        if len(clean_code) >= prefix_len:
            prefix = clean_code[:prefix_len]
            for code, data in hs6_data.items():
                if code.startswith(prefix) and code != clean_code:
                    suggestions.append({
                        "code": code,
                        "description": data.get(f"description_{language}", data.get("description_fr", ""))
                    })
            if suggestions:
                break
    
    return {
        "code": clean_code,
        "suggestions": suggestions[:limit],
        "total": len(suggestions)
    }


@router.get("/rule-of-origin/{hs_code}")
async def get_rule_of_origin(
    hs_code: str,
    language: str = Query(default="fr")
):
    """Get rule of origin for an HS code"""
    clean_code = hs_code.replace(".", "").replace(" ", "")[:6]
    chapter = clean_code[:2]
    
    # Load rules of origin
    roo_file = os.path.join(DATA_DIR, "rules_of_origin.json")
    if os.path.exists(roo_file):
        try:
            with open(roo_file, 'r', encoding='utf-8') as f:
                roo_data = json.load(f)
                
            # Find rule for this code
            if clean_code in roo_data:
                return roo_data[clean_code]
            if chapter in roo_data:
                return roo_data[chapter]
        except Exception as e:
            logger.error(f"Error loading rules of origin: {e}")
    
    # Default rule
    return {
        "hs_code": clean_code,
        "rule": "CTH" if language == "en" else "CCT",
        "description": "Change of tariff heading" if language == "en" else "Changement de position tarifaire",
        "regional_content": 40,
        "additional_requirements": []
    }


@router.get("/categories")
async def get_hs6_categories(language: str = Query(default="fr")):
    """Get HS code categories (chapters)"""
    # Chapter names
    chapters_fr = {
        "01-05": "Animaux vivants et produits du règne animal",
        "06-14": "Produits du règne végétal",
        "15": "Graisses et huiles",
        "16-24": "Produits alimentaires",
        "25-27": "Produits minéraux",
        "28-38": "Produits chimiques",
        "39-40": "Plastiques et caoutchouc",
        "41-43": "Cuirs et peaux",
        "44-46": "Bois et ouvrages en bois",
        "47-49": "Papier et carton",
        "50-63": "Textiles et articles textiles",
        "64-67": "Chaussures et coiffures",
        "68-70": "Pierre, céramique, verre",
        "71": "Perles et métaux précieux",
        "72-83": "Métaux communs",
        "84-85": "Machines et appareils",
        "86-89": "Matériel de transport",
        "90-92": "Instruments et appareils",
        "93": "Armes et munitions",
        "94-96": "Marchandises diverses",
        "97": "Objets d'art et antiquités"
    }
    
    chapters_en = {
        "01-05": "Live animals and animal products",
        "06-14": "Vegetable products",
        "15": "Fats and oils",
        "16-24": "Food products",
        "25-27": "Mineral products",
        "28-38": "Chemical products",
        "39-40": "Plastics and rubber",
        "41-43": "Leather and hides",
        "44-46": "Wood and wood articles",
        "47-49": "Paper and cardboard",
        "50-63": "Textiles and textile articles",
        "64-67": "Footwear and headgear",
        "68-70": "Stone, ceramics, glass",
        "71": "Pearls and precious metals",
        "72-83": "Base metals",
        "84-85": "Machinery and appliances",
        "86-89": "Transport equipment",
        "90-92": "Instruments and apparatus",
        "93": "Arms and ammunition",
        "94-96": "Miscellaneous goods",
        "97": "Art objects and antiques"
    }
    
    chapters = chapters_fr if language == "fr" else chapters_en
    
    return {
        "categories": [
            {"code": k, "name": v} for k, v in chapters.items()
        ]
    }


@router.get("/category/{category}")
async def get_hs6_by_category(
    category: str,
    language: str = Query(default="fr"),
    limit: int = Query(default=50)
):
    """Get HS6 codes in a category"""
    hs6_data = load_hs6_data()
    
    # Parse category range
    if "-" in category:
        start, end = category.split("-")
    else:
        start = end = category
    
    results = []
    for code, data in hs6_data.items():
        chapter = code[:2]
        if start <= chapter <= end:
            results.append({
                "code": code,
                "description": data.get(f"description_{language}", data.get("description_fr", "")),
                "chapter": chapter
            })
    
    results.sort(key=lambda x: x["code"])
    
    return {
        "category": category,
        "results": results[:limit],
        "total": len(results)
    }


@router.get("/statistics")
async def get_hs6_statistics():
    """Get statistics about the HS6 database"""
    hs6_data = load_hs6_data()
    
    # Count by chapter
    chapter_counts = {}
    for code in hs6_data:
        chapter = code[:2]
        chapter_counts[chapter] = chapter_counts.get(chapter, 0) + 1
    
    return {
        "total_codes": len(hs6_data),
        "chapters": len(chapter_counts),
        "chapter_distribution": chapter_counts
    }


# ---------------------------------------------------------------------------
# Search scoring helpers (used by smart_search_hs6)
# ---------------------------------------------------------------------------

def _score_code_match(code: str, query_clean: str) -> int:
    """Return a relevance score for a numeric (code-prefix) query.

    Returns 0 if *code* does not start with *query_clean*.
    """
    if not code.startswith(query_clean):
        return 0
    # Shorter prefix → more results but individually lower score
    return 100 + (10 - len(query_clean))


def _score_text_match(description: str, query: str) -> int:
    """Return a relevance score for a text query against a description.

    Scoring:
    - +50 for an exact phrase match
    - +20 per full-word match
    - +3 per partial-word match (≥3-char query word contained in a desc word)
    """
    score = 0
    desc_lower = description.lower()
    if query in desc_lower:
        score += 50
    query_words = set(query.split())
    desc_words = set(desc_lower.split())
    score += len(query_words & desc_words) * 20
    for qw in query_words:
        if len(qw) >= 3:
            for dw in desc_words:
                if qw in dw and len(dw) > len(qw):
                    score += 3
    return score


def _build_search_result(
    code: str,
    data: Dict[str, Any],
    language: str,
    score: int,
) -> Dict[str, Any]:
    """Build the standardised result dict for a single HS6 code."""
    chapter = code[:2]
    lang_chapters = CHAPTER_NAMES.get(language, CHAPTER_NAMES["fr"])
    chapter_name = lang_chapters.get(chapter, "")
    label = "Chapitre" if language == "fr" else "Chapter"
    return {
        "code": code,
        "description": data.get(f"description_{language}", data.get("description_fr", "")),
        "chapter": chapter,
        "chapter_name": chapter_name,
        "full_position": f"{label} {chapter}: {chapter_name}",
        "position_4": code[:4],
        "score": score,
    }


def _enrich_with_sub_positions(
    results: List[Dict[str, Any]],
    country_code: str,
) -> List[Dict[str, Any]]:
    """Attach sub-position data for each result when a country code is given."""
    from services.authentic_tariff_service import get_sub_positions  # lazy import

    enriched: List[Dict[str, Any]] = []
    for result in results:
        hs6 = result["code"]
        try:
            sub_positions = get_sub_positions(country_code, hs6)
            result["sub_positions"] = sub_positions if isinstance(sub_positions, list) else []
        except Exception as exc:
            logger.warning("Error getting sub-positions for %s/%s: %s", country_code, hs6, exc)
            result["sub_positions"] = []
        result["has_sub_positions"] = bool(result["sub_positions"])
        enriched.append(result)
    return enriched


@router.get("/smart-search")
async def smart_search_hs6(
    q: str = Query(..., min_length=2),
    language: str = Query(default="fr"),
    country_code: str = Query(default=None),
    include_sub_positions: bool = Query(default=False),
    limit: int = Query(default=20),
) -> Dict[str, Any]:
    """Smart HS6 search with code-prefix and full-text modes.

    - **Numeric queries** (e.g. ``"76"``) return codes whose prefix starts with
      the query digits, sorted by code.
    - **Text queries** search French and English descriptions and rank results
      by relevance score.
    - When *include_sub_positions* is ``true`` and *country_code* is supplied,
      each result is enriched with the country's national sub-positions.
    """
    hs6_data = load_hs6_data()
    query = q.lower().strip()
    query_clean = query.replace(".", "").replace(" ", "")
    is_numeric_query = query_clean.isdigit()

    scored_results: List[Dict[str, Any]] = []
    for code, data in hs6_data.items():
        if is_numeric_query:
            score = _score_code_match(code, query_clean)
        else:
            desc = data.get(f"description_{language}", data.get("description_fr", ""))
            score = _score_text_match(desc, query)

        if score > 0:
            scored_results.append(_build_search_result(code, data, language, score))

    if is_numeric_query:
        scored_results.sort(key=lambda x: x["code"])
    else:
        scored_results.sort(key=lambda x: x["score"], reverse=True)

    final_results = scored_results[:limit]
    if include_sub_positions and country_code:
        final_results = _enrich_with_sub_positions(final_results, country_code)

    lang_chapters = CHAPTER_NAMES.get(language, CHAPTER_NAMES["fr"])
    return {
        "query": q,
        "is_code_search": is_numeric_query,
        "results": final_results,
        "total": len(scored_results),
        "chapter_info": (
            lang_chapters.get(query_clean[:2])
            if is_numeric_query and len(query_clean) >= 2
            else None
        ),
    }
