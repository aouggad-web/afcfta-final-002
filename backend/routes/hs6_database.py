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


@router.get("/smart-search")
async def smart_search_hs6(
    q: str = Query(..., min_length=2),
    language: str = Query(default="fr"),
    limit: int = Query(default=15)
):
    """Smart search with fuzzy matching and scoring"""
    hs6_data = load_hs6_data()
    query = q.lower().strip()
    query_words = set(query.split())
    
    scored_results = []
    
    for code, data in hs6_data.items():
        score = 0
        
        # Exact code match
        if code.startswith(query.replace(".", "")):
            score += 100
        
        # Description matching
        desc = data.get(f"description_{language}", data.get("description_fr", "")).lower()
        
        # Exact phrase match
        if query in desc:
            score += 50
        
        # Word matching
        desc_words = set(desc.split())
        matching_words = query_words & desc_words
        score += len(matching_words) * 20
        
        # Partial word matching
        for qw in query_words:
            for dw in desc_words:
                if qw in dw or dw in qw:
                    score += 5
        
        if score > 0:
            scored_results.append({
                "code": code,
                "description": data.get(f"description_{language}", data.get("description_fr", "")),
                "chapter": code[:2],
                "score": score
            })
    
    # Sort by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": q,
        "results": scored_results[:limit],
        "total": len(scored_results)
    }
