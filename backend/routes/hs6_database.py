"""
HS6 Database Routes
API endpoints for HS6 code search and information
Extracted from server.py for better organization
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from etl.hs6_database import (
    get_hs6_info,
    get_sub_position_suggestions,
    get_rule_of_origin,
    search_hs6_codes,
    get_all_categories,
    get_codes_by_category,
    get_database_stats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hs6", tags=["HS6 Database"])


@router.get("/search")
async def search_hs6(
    query: str = Query(..., min_length=2, description="Search query"),
    language: str = Query("fr", description="Language (fr/en)"),
    limit: int = Query(20, ge=1, le=100, description="Max results")
):
    """
    Smart search in HS6 database
    Searches by code, description, or keywords
    """
    results = search_hs6_codes(query, language=language, limit=limit)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


@router.get("/info/{hs_code}")
async def get_hs6_information(
    hs_code: str,
    language: str = Query("fr", description="Language for response")
):
    """
    Get complete information for an HS6 code
    Includes sub-positions, rules of origin, etc.
    """
    info = get_hs6_info(hs_code, language=language)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"HS6 code {hs_code} not found"
        )
    
    return info


@router.get("/suggestions/{hs_code}")
async def get_hs6_suggestions(
    hs_code: str,
    language: str = Query("fr", description="Language for response")
):
    """
    Get sub-position suggestions for an HS6 code
    Helps users select the correct tariff classification
    """
    suggestions = get_sub_position_suggestions(hs_code, language=language)
    
    return {
        "hs_code": hs_code,
        "has_sub_positions": len(suggestions) > 0,
        "sub_positions": suggestions,
        "count": len(suggestions),
        "note": "Sélectionnez la sous-position appropriée pour un calcul de droits précis" if language == "fr" else "Select the appropriate sub-position for accurate duty calculation"
    }


@router.get("/rule-of-origin/{hs_code}")
async def get_hs6_rule_of_origin(
    hs_code: str,
    language: str = Query("fr", description="Language for response")
):
    """
    Get AfCFTA Rule of Origin for an HS6 code
    """
    rule = get_rule_of_origin(hs_code, language=language)
    
    return {
        "hs_code": hs_code,
        "rule": rule,
        "afcfta_applicable": True
    }


@router.get("/categories")
async def list_hs6_categories(
    language: str = Query("fr", description="Language for response")
):
    """
    List all HS6 categories/chapters
    """
    categories = get_all_categories(language=language)
    return {
        "categories": categories,
        "count": len(categories)
    }


@router.get("/category/{category}")
async def get_hs6_by_category(
    category: str,
    language: str = Query("fr", description="Language for response"),
    limit: int = Query(50, ge=1, le=500, description="Max results")
):
    """
    Get HS6 codes by category/chapter
    """
    codes = get_codes_by_category(category, language=language, limit=limit)
    
    return {
        "category": category,
        "codes": codes,
        "count": len(codes)
    }


@router.get("/statistics")
async def get_hs6_database_statistics():
    """
    Get statistics about the HS6 database
    """
    stats = get_database_stats()
    return stats


@router.get("/smart-search")
async def smart_search_hs6(
    query: str = Query(..., min_length=2, description="Search query"),
    language: str = Query("fr", description="Language (fr/en)"),
    include_suggestions: bool = Query(True, description="Include sub-position suggestions"),
    include_rules: bool = Query(True, description="Include rules of origin"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """
    Enhanced smart search with additional context
    Returns codes with suggestions and rules of origin
    """
    base_results = search_hs6_codes(query, language=language, limit=limit)
    
    enhanced_results = []
    for result in base_results:
        enhanced = dict(result)
        hs_code = result.get("hs_code", "")
        
        if include_suggestions:
            suggestions = get_sub_position_suggestions(hs_code, language=language)
            enhanced["sub_positions"] = suggestions[:5] if suggestions else []
            enhanced["has_sub_positions"] = len(suggestions) > 0
        
        if include_rules:
            rule = get_rule_of_origin(hs_code, language=language)
            enhanced["rule_of_origin"] = rule
        
        enhanced_results.append(enhanced)
    
    return {
        "query": query,
        "results": enhanced_results,
        "count": len(enhanced_results),
        "search_type": "smart"
    }


def register_routes(app_router):
    """Register HS6 database routes with the main API router"""
    app_router.include_router(router)
