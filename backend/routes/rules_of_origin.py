"""
Rules of Origin Routes
API endpoints for AfCFTA Rules of Origin
Using official AfCFTA data from Appendix IV
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules-of-origin", tags=["Rules of Origin"])

# Import data from constants (will be passed during registration)
ZLECAF_RULES_OF_ORIGIN = {}
ORIGIN_TYPES = {}


def init_data(rules_data: dict, origin_types: dict = None):
    """Initialize with rules data from main app"""
    global ZLECAF_RULES_OF_ORIGIN, ORIGIN_TYPES
    ZLECAF_RULES_OF_ORIGIN = rules_data
    if origin_types:
        ORIGIN_TYPES = origin_types


@router.get("/stats")
async def get_rules_of_origin_statistics():
    """Get statistics about the rules of origin database"""
    if not ZLECAF_RULES_OF_ORIGIN:
        return {"total_rules": 0, "categories": [], "status": "No data loaded"}
    
    wo_count = sum(1 for r in ZLECAF_RULES_OF_ORIGIN.values() if r.get("primary") == "WO")
    cth_count = sum(1 for r in ZLECAF_RULES_OF_ORIGIN.values() if r.get("primary") == "CTH")
    va_count = sum(1 for r in ZLECAF_RULES_OF_ORIGIN.values() if "VA" in str(r.get("primary", "")))
    
    return {
        "total_rules": len(ZLECAF_RULES_OF_ORIGIN),
        "wholly_obtained": wo_count,
        "change_tariff_heading": cth_count,
        "value_added": va_count,
        "categories": list(set(r.get("primary", "Unknown") for r in ZLECAF_RULES_OF_ORIGIN.values())),
        "data_source": "AfCFTA Appendix IV - December 2023"
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
    is_french = lang == "fr"
    
    # Get chapter (first 2 digits)
    chapter = hs_code[:2].lstrip('0') or hs_code[:2]
    chapter_padded = hs_code[:2]
    
    # Try to find the rule
    rule_data = None
    match_type = "default"
    
    # Try exact chapter match
    if chapter_padded in ZLECAF_RULES_OF_ORIGIN:
        rule_data = ZLECAF_RULES_OF_ORIGIN[chapter_padded]
        match_type = "chapter"
    elif chapter in ZLECAF_RULES_OF_ORIGIN:
        rule_data = ZLECAF_RULES_OF_ORIGIN[chapter]
        match_type = "chapter"
    
    if rule_data:
        primary_rule = rule_data.get("primary", "CTH")
        alt_rule = rule_data.get("alt")
        max_non_orig = rule_data.get("max_non_orig", 0)
        
        # Determine if wholly obtained
        is_wholly_obtained = primary_rule == "WO"
        
        # Calculate regional content
        if is_wholly_obtained:
            regional_content = 100
        elif max_non_orig > 0:
            regional_content = 100 - max_non_orig
        else:
            regional_content = 60  # Default minimum for CTH rules
        
        # Get rule type translation
        rule_type_label = ORIGIN_TYPES.get(primary_rule, {}).get(lang, primary_rule)
        
        # Build PSR text
        if is_french:
            if is_wholly_obtained:
                psr_text = "Entièrement obtenu dans les États parties de la ZLECAf"
            else:
                psr_text = rule_data.get("rule_text_fr", f"Changement de position tarifaire (CTH)")
                if alt_rule and max_non_orig > 0:
                    psr_text += f" ou max {max_non_orig}% de valeur non-originaire"
        else:
            if is_wholly_obtained:
                psr_text = "Wholly obtained in AfCFTA State Parties"
            else:
                psr_text = rule_data.get("rule_text_en", f"Change of tariff heading (CTH)")
                if alt_rule and max_non_orig > 0:
                    psr_text += f" or max {max_non_orig}% non-originating value"
        
        return {
            "hs_code": hs_code,
            "rule": {
                "psr": psr_text,
                "wholly_obtained": is_wholly_obtained,
                "value_added_threshold": regional_content,
                "category": rule_type_label,
                "primary_rule": primary_rule,
                "alternative_rule": alt_rule,
                "max_non_originating": max_non_orig,
                "notes": rule_data.get(f"description_{lang[:2]}", ""),
                "status": rule_data.get("status", "AGREED")
            },
            "match_type": match_type,
            "matched_code": chapter_padded,
            "data_source": "AfCFTA Appendix IV - December 2023"
        }
    
    # Default fallback rule (should rarely happen with complete data)
    default_rule = {
        "psr": is_french and "Changement de position tarifaire (CTH) + 40% valeur ajoutée locale" or "Change of tariff heading (CTH) + 40% local value added",
        "wholly_obtained": False,
        "value_added_threshold": 40,
        "category": is_french and "Règle par défaut" or "Default rule",
        "primary_rule": "CTH",
        "alternative_rule": "VA40",
        "max_non_originating": 60,
        "notes": is_french and "Règle générale applicable en l'absence de règle spécifique" or "General rule applicable in absence of specific rule",
        "status": "DEFAULT"
    }
    
    return {
        "hs_code": hs_code,
        "rule": default_rule,
        "match_type": "default",
        "warning": is_french and "Aucune règle spécifique trouvée - règle par défaut appliquée" or "No specific rule found - default rule applied"
    }


def register_routes(app_router, rules_data: dict = None, origin_types: dict = None):
    """Register rules of origin routes with the main API router"""
    if rules_data:
        init_data(rules_data, origin_types)
    app_router.include_router(router)
