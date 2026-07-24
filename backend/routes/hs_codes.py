"""
HS Codes routes - Harmonized System codes browser and search
Using complete HS6_DATABASE with 5800+ codes
"""

from etl.hs6_database import (
    HS6_DATABASE,
    get_all_categories,
)
from etl.hs6_database import get_codes_by_category as get_codes_by_category_db
from etl.hs6_database import (
    get_database_stats,
    get_hs6_info,
    get_rule_of_origin,
    get_sub_position_suggestions,
    search_hs6_codes,
)
from etl.hs_codes_data import (
    get_hs6_code,
    get_hs_chapters,
)
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/hs-codes")

# Intitulés des positions SH4 (anglais) — chargés une seule fois
_HS4_HEADINGS = {}
try:
    import json as _json
    import os as _os

    _hs4_path = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
        "data",
        "hs4_headings_en.json",
    )
    with open(_hs4_path, "r", encoding="utf-8") as _f:
        _HS4_HEADINGS = _json.load(_f)
except Exception:
    _HS4_HEADINGS = {}


@router.get("/label/{hs_code}")
async def get_hs_label(hs_code: str):
    """
    Retourne l'intitulé officiel d'un code SH selon son niveau :
    - 2 chiffres → chapitre SH2 (FR + EN)
    - 4 chiffres → position SH4 (EN, contexte chapitre FR)
    - 6 chiffres → sous-position SH6 (FR + EN)
    """
    code = "".join(c for c in hs_code if c.isdigit())
    chapters = get_hs_chapters()

    if len(code) == 2:
        ch = chapters.get(code)
        if not ch:
            raise HTTPException(status_code=404, detail=f"Chapitre {code} introuvable")
        return {
            "code": code,
            "level": "hs2",
            "label_fr": ch.get("fr", ""),
            "label_en": ch.get("en", ""),
            "label_lang": "both",
            "chapter": code,
            "chapter_name_fr": ch.get("fr", ""),
            "chapter_name_en": ch.get("en", ""),
            "source": "OMD — Système Harmonisé 2022",
        }

    if len(code) == 4:
        chapter = code[:2]
        ch = chapters.get(chapter, {})
        en = _HS4_HEADINGS.get(code, "")
        if not en and not ch:
            raise HTTPException(status_code=404, detail=f"Position {code} introuvable")
        return {
            "code": code,
            "level": "hs4",
            "label_fr": en,
            "label_en": en,
            "label_lang": "en",
            "chapter": chapter,
            "chapter_name_fr": ch.get("fr", ""),
            "chapter_name_en": ch.get("en", ""),
            "source": "OMD — Système Harmonisé 2022",
        }

    if len(code) == 6:
        chapter = code[:2]
        ch = chapters.get(chapter, {})
        data = HS6_DATABASE.get(code)
        if not data:
            raise HTTPException(status_code=404, detail=f"Sous-position {code} introuvable")
        return {
            "code": code,
            "level": "hs6",
            "label_fr": data.get("description_fr", ""),
            "label_en": data.get("description_en", ""),
            "label_lang": "both",
            "chapter": chapter,
            "chapter_name_fr": ch.get("fr", ""),
            "chapter_name_en": ch.get("en", ""),
            "heading": code[:4],
            "heading_name_en": _HS4_HEADINGS.get(code[:4], ""),
            "category": data.get("category", ""),
            "sensitivity": data.get("sensitivity", "normal"),
            "source": "OMD — Système Harmonisé 2022 + Base AfCFTA",
        }

    raise HTTPException(status_code=400, detail="Le code SH doit comporter 2, 4 ou 6 chiffres.")


@router.get("/chapters")
async def get_all_hs_chapters():
    """
    Get all HS chapters (2-digit codes) with labels in FR and EN
    """
    return {
        "chapters": get_hs_chapters(),
        "total": len(get_hs_chapters()),
        "source": "World Customs Organization (WCO) HS 2022",
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
        result.append(
            {
                "code": code,
                "label": data.get(desc_key, data.get("description_fr", "")),
                "chapter": code[:2],
                "chapter_name": chapters.get(code[:2], {}).get(language, ""),
            }
        )

    return {
        "codes": result,
        "total": len(result),
        "language": language,
        "source": "World Customs Organization (WCO) HS 2022 + AfCFTA Database",
    }


@router.get("/code/{hs_code}")
async def get_single_hs_code(
    hs_code: str, language: str = Query("fr", description="Language: fr or en")
):
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
            "sensitivity": data.get("sensitivity", "normal"),
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
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
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
        results.append(
            {
                "code": code,
                "label": r.get("description", ""),
                "chapter": chapter,
                "chapter_name": chapters.get(chapter, {}).get(language, ""),
                "category": r.get("category", ""),
                "sensitivity": r.get("sensitivity", "normal"),
            }
        )

    return {"query": q, "results": results, "count": len(results), "language": language}


@router.get("/product-index")
async def search_product_index(
    q: str = Query(..., min_length=2, description="Nom courant du produit/marchandise"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
):
    """
    Recherche « nom de marchandise -> code SH » via l'index alphabétique OFFICIEL
    de l'OMD (Système Harmonisé, 7e éd. 2022).

    Complète ``/hs-codes/search`` (qui interroge la base technique SH6 par code ou
    intitulé) en partant du VOCABULAIRE COURANT : un utilisateur sans connaissance
    douanière tape « huile de palme », « machine à coudre », « thé vert » et
    obtient les positions SH correspondantes. Chaque code SH6 est enrichi de son
    intitulé technique officiel pour lever toute ambiguïté.
    """
    from services import omd_hs_index_service as omd
    from services.wco_index_adapter import get_wco_index_metadata

    found = omd.search(q, limit=limit)
    chapters = get_hs_chapters()

    results = []
    for r in found["results"]:
        enriched_codes = []
        for code in r.get("hs_codes", []):
            chapter = code[:2]
            official = ""
            if len(code) == 6:
                info = get_hs6_info(code, language) or {}
                official = info.get("description", "") or info.get("label", "")
            enriched_codes.append(
                {
                    "code": code,
                    "level": {2: "chapter", 4: "heading", 6: "subheading"}.get(len(code), "other"),
                    "official_label": official,
                    "chapter": chapter,
                    "chapter_name": chapters.get(chapter, {}).get(language, ""),
                }
            )
        results.append(
            {
                "label": r["label"],
                "term": r["term"],
                "qualifier": r.get("qualifier"),
                "codes": enriched_codes,
                "codes_display": r.get("codes_display"),
                "is_range": r.get("is_range", False),
                "see_also": r.get("see_also"),
            }
        )

    return {
        "query": q,
        "count": found["count"],
        "results": results,
        "source": found.get("source"),
        "metadata": get_wco_index_metadata(),
        "language": language,
    }


@router.get("/chapter/{chapter}")
async def get_hs_codes_by_chapter(
    chapter: str, language: str = Query("fr", description="Language: fr or en")
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
            codes.append(
                {
                    "code": code,
                    "label": data.get(desc_key, data.get("description_fr", "")),
                    "chapter": chapter,
                    "category": data.get("category", ""),
                    "sensitivity": data.get("sensitivity", "normal"),
                }
            )

    # Sort codes
    codes.sort(key=lambda x: x["code"])

    chapter_info = chapters.get(chapter, {})

    return {
        "chapter": chapter,
        "chapter_name_fr": chapter_info.get("fr", ""),
        "chapter_name_en": chapter_info.get("en", ""),
        "codes": codes,
        "count": len(codes),
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
                "chapter_name_fr": chapters.get(ch, {}).get("fr", ""),
                "code_count": count,
            }
            for ch, count in top_chapters
        ],
        "source": "World Customs Organization (WCO) HS 2022 + AfCFTA Database",
        "last_updated": "2025-01",
    }
