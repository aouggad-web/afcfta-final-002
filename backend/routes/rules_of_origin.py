"""
Rules of Origin Routes
API endpoints for AfCFTA Rules of Origin
Extracted from server.py for better organization
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules-of-origin", tags=["Rules of Origin"])


# Import data from constants (will be passed during registration)
ZLECAF_RULES_OF_ORIGIN = {}


def init_data(rules_data: dict):
    """Initialize with rules data from main app"""
    global ZLECAF_RULES_OF_ORIGIN
    ZLECAF_RULES_OF_ORIGIN = rules_data


@router.get("/stats")
async def get_rules_of_origin_statistics():
    """Get statistics about the rules of origin database"""
    return {
        "total_rules": len(ZLECAF_RULES_OF_ORIGIN),
        "categories": list(set(r.get("category", "Non classé") for r in ZLECAF_RULES_OF_ORIGIN.values()))
    }


@router.get("/{hs_code}")
async def get_rules_of_origin(
    hs_code: str,
    lang: str = Query(default="fr", description="Language for response (fr/en)")
):
    """
    Get AfCFTA Rules of Origin for a specific HS code
    
    Args:
        hs_code: HS code (2, 4, or 6 digits)
        lang: Language for the response
    
    Returns:
        Rules of origin details including PSR, wholly obtained criteria, etc.
    """
    # Try exact match first
    if hs_code in ZLECAF_RULES_OF_ORIGIN:
        rule = ZLECAF_RULES_OF_ORIGIN[hs_code]
        return {
            "hs_code": hs_code,
            "rule": rule,
            "match_type": "exact"
        }
    
    # Try chapter match (first 2 digits)
    chapter = hs_code[:2]
    if chapter in ZLECAF_RULES_OF_ORIGIN:
        return {
            "hs_code": hs_code,
            "rule": ZLECAF_RULES_OF_ORIGIN[chapter],
            "match_type": "chapter",
            "matched_code": chapter
        }
    
    # Try 4-digit match
    if len(hs_code) >= 4:
        hs4 = hs_code[:4]
        if hs4 in ZLECAF_RULES_OF_ORIGIN:
            return {
                "hs_code": hs_code,
                "rule": ZLECAF_RULES_OF_ORIGIN[hs4],
                "match_type": "heading",
                "matched_code": hs4
            }
    
    # Default fallback rule
    default_rule = {
        "psr": lang == "fr" and "Changement de position tarifaire (CTH) + 30% valeur ajoutée locale" or "Change of tariff heading (CTH) + 30% local value added",
        "wholly_obtained": False,
        "value_added_threshold": 30,
        "category": lang == "fr" and "Règle par défaut" or "Default rule",
        "notes": lang == "fr" and "Règle générale applicable en l'absence de règle spécifique" or "General rule applicable in absence of specific rule"
    }
    
    return {
        "hs_code": hs_code,
        "rule": default_rule,
        "match_type": "default",
        "warning": lang == "fr" and "Aucune règle spécifique trouvée - règle par défaut appliquée" or "No specific rule found - default rule applied"
    }


def register_routes(app_router, rules_data: dict = None):
    """Register rules of origin routes with the main API router"""
    if rules_data:
        init_data(rules_data)
    app_router.include_router(router)
