"""
Tariffs routes - Tariff calculations, rules of origin, country-specific rates
Complete tariff data for 54 African countries with ZLECAf rates
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from constants import AFRICAN_COUNTRIES
from etl.hs_codes_data import get_hs_chapters, get_hs6_code
from etl.hs6_tariffs import (
    get_hs6_tariff,
    get_hs6_tariff_rates,
    search_hs6_tariffs,
    get_hs6_tariffs_by_chapter,
    get_hs6_statistics,
    HS6_TARIFFS_AGRICULTURE,
    HS6_TARIFFS_MINING,
    HS6_TARIFFS_MANUFACTURED
)
from etl.country_tariffs_complete import (
    get_tariff_rate_for_country,
    get_zlecaf_tariff_rate,
    get_vat_rate_for_country,
    get_other_taxes_for_country,
    get_all_country_rates,
    ISO2_TO_ISO3
)
from etl.country_hs6_tariffs import (
    get_country_hs6_tariff,
    search_country_hs6_tariffs,
    get_available_country_tariffs,
    COUNTRY_HS6_TARIFFS
)
from etl.country_hs6_detailed import (
    get_detailed_tariff,
    get_sub_position_rate,
    get_all_sub_positions,
    has_varying_rates,
    get_tariff_summary,
    COUNTRY_HS6_DETAILED
)

router = APIRouter()

# =============================================================================
# HS6 TARIFFS ENDPOINTS
# =============================================================================

@router.get("/hs6-tariffs/search")
async def search_hs6_tariffs_endpoint(
    q: str = Query(..., description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Rechercher des codes SH6 avec leurs tarifs par mot-clé
    Retourne les taux NPF et ZLECAf avec les économies potentielles
    """
    results = search_hs6_tariffs(q, language, limit)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/hs6-tariffs/code/{hs6_code}")
async def get_hs6_tariff_endpoint(hs6_code: str, language: str = Query("fr")):
    """
    Obtenir les tarifs détaillés pour un code SH6 spécifique
    Inclut taux NPF, taux ZLECAf, et économies potentielles
    """
    tariff = get_hs6_tariff(hs6_code)
    if not tariff:
        hs_info = get_hs6_code(hs6_code, language)
        if hs_info:
            return {
                "code": hs6_code,
                "has_specific_tariff": False,
                "hs_info": hs_info,
                "message": "Pas de tarif SH6 spécifique - utiliser le taux par chapitre"
            }
        raise HTTPException(status_code=404, detail=f"Code SH6 {hs6_code} non trouvé")
    
    desc_key = f"description_{language}"
    return {
        "code": hs6_code,
        "has_specific_tariff": True,
        "description": tariff.get(desc_key, tariff.get("description_fr")),
        "normal_rate": tariff["normal"],
        "normal_rate_pct": f"{tariff['normal'] * 100:.1f}%",
        "zlecaf_rate": tariff["zlecaf"],
        "zlecaf_rate_pct": f"{tariff['zlecaf'] * 100:.1f}%",
        "savings_pct": round((tariff["normal"] - tariff["zlecaf"]) / tariff["normal"] * 100, 1) if tariff["normal"] > 0 else 0,
        "chapter": hs6_code[:2],
        "chapter_name": get_hs_chapters().get(hs6_code[:2], {}).get(language, "")
    }

@router.get("/hs6-tariffs/chapter/{chapter}")
async def get_hs6_tariffs_chapter_endpoint(
    chapter: str,
    language: str = Query("fr")
):
    """Obtenir tous les codes SH6 avec tarifs spécifiques pour un chapitre"""
    results = get_hs6_tariffs_by_chapter(chapter)
    chapter_info = get_hs_chapters().get(chapter.zfill(2), {})
    
    return {
        "chapter": chapter.zfill(2),
        "chapter_name": chapter_info.get(language, chapter_info.get("fr", "")),
        "count": len(results),
        "codes": results
    }

@router.get("/hs6-tariffs/statistics")
async def get_hs6_tariffs_statistics_endpoint():
    """Obtenir les statistiques sur les tarifs SH6 disponibles"""
    return get_hs6_statistics()

@router.get("/hs6-tariffs/products/african-exports")
async def get_african_export_products(language: str = Query("fr")):
    """
    Obtenir la liste des produits africains clés avec leurs tarifs SH6
    Groupés par catégorie (agriculture, mining, manufactured)
    """
    desc_key = f"description_{language}"
    
    def format_products(products_dict, category_name):
        formatted = []
        for code, data in products_dict.items():
            formatted.append({
                "code": code,
                "description": data.get(desc_key, data.get("description_fr", "")),
                "normal_rate_pct": f"{data['normal'] * 100:.1f}%",
                "zlecaf_rate_pct": f"{data['zlecaf'] * 100:.1f}%",
                "savings_pct": round((data["normal"] - data["zlecaf"]) / data["normal"] * 100, 1) if data["normal"] > 0 else 0
            })
        return formatted
    
    return {
        "agriculture": {
            "title": "Produits Agricoles" if language == "fr" else "Agricultural Products",
            "count": len(HS6_TARIFFS_AGRICULTURE),
            "products": format_products(HS6_TARIFFS_AGRICULTURE, "agriculture")
        },
        "mining": {
            "title": "Produits Miniers" if language == "fr" else "Mining Products",
            "count": len(HS6_TARIFFS_MINING),
            "products": format_products(HS6_TARIFFS_MINING, "mining")
        },
        "manufactured": {
            "title": "Produits Manufacturés" if language == "fr" else "Manufactured Products",
            "count": len(HS6_TARIFFS_MANUFACTURED),
            "products": format_products(HS6_TARIFFS_MANUFACTURED, "manufactured")
        }
    }

# =============================================================================
# COUNTRY-SPECIFIC TARIFFS ENDPOINTS
# =============================================================================

@router.get("/country-tariffs/{country_code}")
async def get_country_tariffs_endpoint(
    country_code: str,
    hs_code: str = Query("18", description="HS code (2-6 digits)")
):
    """
    Obtenir les tarifs douaniers spécifiques à un pays
    Retourne les taux NPF, ZLECAf, TVA et autres taxes
    """
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    npf_rate, npf_source = get_tariff_rate_for_country(country_iso3, hs_code)
    zlecaf_rate, zlecaf_source = get_zlecaf_tariff_rate(country_iso3, hs_code)
    vat_rate, vat_source = get_vat_rate_for_country(country_iso3)
    other_rate, other_detail = get_other_taxes_for_country(country_iso3)
    
    country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == country_iso3), None)
    country_name = country['name'] if country else country_iso3
    
    return {
        "country_code": country_iso3,
        "country_name": country_name,
        "hs_code": hs_code,
        "chapter": hs_code[:2],
        "tariffs": {
            "npf_rate": npf_rate,
            "npf_rate_pct": f"{npf_rate * 100:.1f}%",
            "zlecaf_rate": zlecaf_rate,
            "zlecaf_rate_pct": f"{zlecaf_rate * 100:.1f}%",
            "potential_savings_pct": round((npf_rate - zlecaf_rate) / npf_rate * 100, 1) if npf_rate > 0 else 0
        },
        "taxes": {
            "vat_rate": vat_rate,
            "vat_rate_pct": f"{vat_rate * 100:.1f}%",
            "other_taxes_rate": other_rate,
            "other_taxes_pct": f"{other_rate * 100:.1f}%",
            "other_taxes_detail": other_detail
        },
        "sources": {
            "tariff": npf_source,
            "zlecaf": zlecaf_source,
            "vat": vat_source
        },
        "last_updated": "2025-01"
    }

@router.get("/country-tariffs-comparison")
async def compare_country_tariffs(
    countries: str = Query("NGA,GHA,KEN,ZAF,EGY", description="Comma-separated country codes"),
    hs_code: str = Query("18", description="HS code")
):
    """Comparer les tarifs entre plusieurs pays africains"""
    country_list = [c.strip().upper() for c in countries.split(",")]
    
    results = []
    for cc in country_list:
        if len(cc) == 2:
            iso3 = ISO2_TO_ISO3.get(cc, cc)
        else:
            iso3 = cc
        
        npf_rate, _ = get_tariff_rate_for_country(iso3, hs_code)
        zlecaf_rate, _ = get_zlecaf_tariff_rate(iso3, hs_code)
        vat_rate, _ = get_vat_rate_for_country(iso3)
        other_rate, _ = get_other_taxes_for_country(iso3)
        
        country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == iso3), None)
        
        results.append({
            "country_code": iso3,
            "country_name": country['name'] if country else iso3,
            "npf_rate_pct": f"{npf_rate * 100:.1f}%",
            "zlecaf_rate_pct": f"{zlecaf_rate * 100:.1f}%",
            "vat_rate_pct": f"{vat_rate * 100:.1f}%",
            "other_taxes_pct": f"{other_rate * 100:.1f}%",
            "total_cost_factor_npf": round(1 + npf_rate + vat_rate * (1 + npf_rate) + other_rate, 3),
            "total_cost_factor_zlecaf": round(1 + zlecaf_rate + vat_rate * (1 + zlecaf_rate) + other_rate, 3)
        })
    
    results.sort(key=lambda x: x['total_cost_factor_npf'])
    
    return {
        "hs_code": hs_code,
        "chapter": hs_code[:2],
        "countries_compared": len(results),
        "comparison": results,
        "note": "total_cost_factor = multiplicateur du coût d'importation (1.0 = pas de taxes)"
    }

@router.get("/all-country-rates")
async def get_all_rates_endpoint():
    """Obtenir un aperçu de tous les taux par pays africain"""
    return get_all_country_rates()

# =============================================================================
# COUNTRY HS6 TARIFFS ENDPOINTS
# =============================================================================

@router.get("/country-hs6-tariffs/{country_code}/search")
async def search_country_hs6_endpoint(
    country_code: str,
    q: str = Query(..., description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, ge=1, le=100)
):
    """Rechercher les tarifs SH6 spécifiques à un pays"""
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    results = search_country_hs6_tariffs(iso3, q, language, limit)
    return {
        "country_code": iso3,
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/country-hs6-tariffs/{country_code}/{hs6_code}")
async def get_country_hs6_tariff_endpoint(
    country_code: str,
    hs6_code: str,
    language: str = Query("fr")
):
    """Obtenir le tarif SH6 spécifique à un pays"""
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    tariff = get_country_hs6_tariff(iso3, hs6_code)
    if not tariff:
        raise HTTPException(
            status_code=404, 
            detail=f"Tarif SH6 {hs6_code} non trouvé pour {iso3}"
        )
    
    return {
        "country_code": iso3,
        "hs6_code": hs6_code,
        "tariff": tariff,
        "chapter": hs6_code[:2],
        "language": language
    }

@router.get("/country-hs6-tariffs/available")
async def get_available_country_tariffs_endpoint():
    """Liste des pays avec tarifs SH6 spécifiques disponibles"""
    return get_available_country_tariffs()

@router.get("/country-hs6-tariffs/{country_code}/all")
async def get_all_country_hs6_tariffs(
    country_code: str,
    language: str = Query("fr")
):
    """Obtenir tous les tarifs SH6 d'un pays"""
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    if iso3 not in COUNTRY_HS6_TARIFFS:
        return {
            "country_code": iso3,
            "available": False,
            "message": f"Pas de tarifs SH6 spécifiques pour {iso3}",
            "tariffs": []
        }
    
    tariffs = COUNTRY_HS6_TARIFFS[iso3]
    return {
        "country_code": iso3,
        "available": True,
        "count": len(tariffs),
        "tariffs": tariffs
    }

# =============================================================================
# DETAILED TARIFFS WITH SUB-POSITIONS ENDPOINTS
# =============================================================================

@router.get("/tariffs/detailed/{country_code}/{hs_code}")
async def get_detailed_tariff_endpoint(
    country_code: str,
    hs_code: str,
    language: str = Query("fr")
):
    """
    Obtenir les tarifs détaillés avec sous-positions nationales
    Supporte les codes de 6 à 12 chiffres
    """
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    result = get_detailed_tariff(iso3, hs_code)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Tarif non trouvé pour {iso3}/{hs_code}"
        )
    
    return result

@router.get("/tariffs/sub-position/{country_code}/{full_code}")
async def get_sub_position_rate_endpoint(
    country_code: str,
    full_code: str
):
    """Obtenir le taux pour une sous-position nationale spécifique (8-12 chiffres)"""
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    rate, description, source = get_sub_position_rate(iso3, full_code)
    
    if rate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sous-position {full_code} non trouvée pour {iso3}"
        )
    
    return {
        "country_code": iso3,
        "full_code": full_code,
        "hs6_code": full_code[:6],
        "sub_position": full_code[6:],
        "rate": rate,
        "rate_pct": f"{rate * 100:.1f}%",
        "description": description,
        "source": source
    }

@router.get("/tariffs/sub-positions/{country_code}/{hs6_code}")
async def get_all_sub_positions_endpoint(
    country_code: str,
    hs6_code: str
):
    """Obtenir toutes les sous-positions nationales pour un code SH6"""
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    sub_positions = get_all_sub_positions(iso3, hs6_code)
    has_varying = has_varying_rates(iso3, hs6_code)
    summary = get_tariff_summary(iso3, hs6_code)
    
    return {
        "country_code": iso3,
        "hs6_code": hs6_code,
        "has_sub_positions": len(sub_positions) > 0,
        "has_varying_rates": has_varying,
        "summary": summary,
        "sub_positions": sub_positions
    }

@router.get("/tariffs/detailed-countries")
async def get_detailed_countries_list():
    """Liste des pays avec tarifs détaillés (sous-positions nationales) disponibles"""
    return {
        "countries": list(COUNTRY_HS6_DETAILED.keys()),
        "count": len(COUNTRY_HS6_DETAILED),
        "description": "Pays avec sous-positions nationales (8-12 chiffres) disponibles"
    }


# =============================================================================
# ENHANCED CALCULATOR - DETAILED NPF vs ZLECAf BREAKDOWN
# =============================================================================

@router.post("/calculate/detailed")
async def calculate_detailed_tariff_endpoint(
    country_code: str = Query(..., description="ISO3 or ISO2 country code"),
    hs_code: str = Query(..., description="HS code (6-12 digits)"),
    fob_value: float = Query(..., description="FOB value in USD"),
    freight: float = Query(0, description="Freight cost in USD"),
    insurance: float = Query(0, description="Insurance cost in USD"),
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Calcul détaillé des droits et taxes avec comparaison NPF vs ZLECAf
    
    Retourne:
    - Détail ligne par ligne de chaque taxe (DD, TVA, autres)
    - Base de calcul pour chaque taxe
    - Comparaison complète NPF vs ZLECAf
    - Économies réalisées avec ZLECAf
    - Sous-positions disponibles si variantes de taux
    
    Méthodologie:
    - CIF = FOB + Fret + Assurance
    - DD (NPF) = CIF × Taux DD
    - DD (ZLECAf) = 0% (exonéré)
    - TVA = (CIF + DD) × Taux TVA
    - Autres taxes = CIF × Taux
    """
    from services.enhanced_calculator_service import calculate_detailed_tariff
    
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    try:
        result = calculate_detailed_tariff(
            country_iso3=iso3,
            hs_code=hs_code,
            fob_value=fob_value,
            freight=freight,
            insurance=insurance,
            language=language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculate/detailed/{country_code}/{hs_code}")
async def get_detailed_calculation(
    country_code: str,
    hs_code: str,
    value: float = Query(10000, description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Version GET du calculateur détaillé pour une valeur donnée
    Utilise value comme valeur CIF (FOB + Fret + Assurance combinés)
    """
    from services.enhanced_calculator_service import calculate_detailed_tariff
    
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    # Assume value is CIF (combined FOB + freight + insurance)
    result = calculate_detailed_tariff(
        country_iso3=iso3,
        hs_code=hs_code,
        fob_value=value,  # Treat as total CIF
        freight=0,
        insurance=0,
        language=language
    )
    return result

