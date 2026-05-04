"""
HS Codes routes - Harmonized System codes browser and search
Using complete HS6_DATABASE with 5800+ codes
"""
from fastapi import APIRouter, HTTPException, Query

from etl.hs_codes_data import (
    get_hs_chapters,
    get_hs6_code,
)
from etl.hs6_database import (
    HS6_DATABASE,
    search_hs6_codes,
    get_database_stats,
    get_hs6_info,
    get_sub_position_suggestions,
    get_rule_of_origin,
    get_all_categories,
    get_codes_by_category as get_codes_by_category_db
)

router = APIRouter(prefix="/hs-codes")

@router.get("/chapters")
async def get_all_hs_chapters():
    """
    Get all HS chapters (2-digit codes) with labels in FR and EN
    """
    return {
        "chapters": get_hs_chapters(),
        "total": len(get_hs_chapters()),
        "source": "World Customs Organization (WCO) HS 2022"
    }

@router.get("/all")
async def get_all_hs6_codes_endpoint(language: str = Query("fr", description="Language: fr or en")):
    """
    Get all HS6 codes with their labels from the complete database (5800+ codes)
    """
    result = []
    chapters = get_hs_chapters()
    for code, data in HS6_DATABASE.items():
        desc_key = "description_fr" if language == "fr" else "description_en"
        result.append({
            "code": code,
            "label": data.get(desc_key, data.get("description_fr", "")),
            "chapter": code[:2],
            "chapter_name": chapters.get(code[:2], {}).get(language, "")
        })
    
    return {
        "codes": result,
        "total": len(result),
        "language": language,
        "source": "World Customs Organization (WCO) HS 2022 + AfCFTA Database"
    }

@router.get("/code/{hs_code}")
async def get_single_hs_code(hs_code: str, language: str = Query("fr", description="Language: fr or en")):
    """
    Get a specific HS6 code with its label from complete database
    """
    # Try complete database first
    if hs_code in HS6_DATABASE:
        data = HS6_DATABASE[hs_code]
        desc_key = "description_fr" if language == "fr" else "description_en"
        chapters = get_hs_chapters()
        return {
            "code": hs_code,
            "label": data.get(desc_key, data.get("description_fr", "")),
            "chapter": hs_code[:2],
            "chapter_name": chapters.get(hs_code[:2], {}).get(language, ""),
            "category": data.get("category", ""),
            "sensitivity": data.get("sensitivity", "normal")
        }
    
    # Fallback to old database for backwards compatibility
    result = get_hs6_code(hs_code, language)
    if not result:
        raise HTTPException(status_code=404, detail=f"HS code {hs_code} not found")
    return result

@router.get("/search")
async def search_hs_codes_endpoint(
    q: str = Query(..., min_length=2, description="Search query (code or label)"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Search HS codes by code or label keyword using complete database (5800+ codes)
    """
    # Use search_hs6_codes from hs6_database.py which has accent-insensitive search
    raw_results = search_hs6_codes(q, language, limit)
    chapters = get_hs_chapters()
    
    # Transform results to match frontend expected format (label, chapter_name)
    results = []
    for r in raw_results:
        code = r["code"]
        chapter = code[:2]
        results.append({
            "code": code,
            "label": r.get("description", ""),
            "chapter": chapter,
            "chapter_name": chapters.get(chapter, {}).get(language, ""),
            "category": r.get("category", ""),
            "sensitivity": r.get("sensitivity", "normal")
        })
    
    return {
        "query": q,
        "results": results,
        "count": len(results),
        "language": language
    }

@router.get("/chapter/{chapter}")
async def get_hs_codes_by_chapter(
    chapter: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Get all HS6 codes for a specific chapter (2-digit code) from complete database
    """
    chapters = get_hs_chapters()
    if len(chapter) != 2 or chapter not in chapters:
        raise HTTPException(status_code=404, detail=f"Chapter {chapter} not found")
    
    # Get codes from complete database
    codes = []
    desc_key = "description_fr" if language == "fr" else "description_en"
    for code, data in HS6_DATABASE.items():
        if code[:2] == chapter:
            codes.append({
                "code": code,
                "label": data.get(desc_key, data.get("description_fr", "")),
                "chapter": chapter,
                "category": data.get("category", ""),
                "sensitivity": data.get("sensitivity", "normal")
            })
    
    # Sort codes
    codes.sort(key=lambda x: x["code"])
    
    chapter_info = chapters.get(chapter, {})
    
    return {
        "chapter": chapter,
        "chapter_name_fr": chapter_info.get('fr', ''),
        "chapter_name_en": chapter_info.get('en', ''),
        "codes": codes,
        "count": len(codes)
    }

@router.get("/statistics")
async def get_hs_codes_statistics():
    """
    Get HS codes database statistics from complete database (5800+ codes)
    """
    chapters = get_hs_chapters()
    db_stats = get_database_stats()
    
    # Count codes per chapter from complete database
    codes_per_chapter = {}
    for code in HS6_DATABASE.keys():
        ch = code[:2]
        codes_per_chapter[ch] = codes_per_chapter.get(ch, 0) + 1
    
    top_chapters = sorted(codes_per_chapter.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_chapters": len(chapters),
        "total_codes": db_stats.get("total_codes", len(HS6_DATABASE)),
        "top_chapters": [
            {
                "chapter": ch,
                "chapter_name_fr": chapters.get(ch, {}).get('fr', ''),
                "code_count": count
            }
            for ch, count in top_chapters
        ],
        "source": "World Customs Organization (WCO) HS 2022 + AfCFTA Database",
        "last_updated": "2025-01"
    }
