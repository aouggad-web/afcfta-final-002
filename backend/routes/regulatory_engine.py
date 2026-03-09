"""
Router FastAPI pour le Moteur Réglementaire AfCFTA v3
=====================================================

Endpoints:
- GET /api/regulatory-engine/countries - Liste des pays disponibles
- GET /api/regulatory-engine/details - Détails par code national ou HS6
- GET /api/regulatory-engine/summary/{country} - Résumé d'un pays
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

import importlib.util
from pathlib import Path

# Load engine_service using importlib to avoid sys.path pollution that would
# shadow the backend 'api' package with engine's 'api' package.
_engine_service_path = Path(__file__).parent.parent.parent / "engine" / "api" / "engine_service.py"

try:
    _spec = importlib.util.spec_from_file_location("engine_api_engine_service", _engine_service_path)
    _engine_service_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_engine_service_mod)
    get_service = _engine_service_mod.get_service
except Exception:
    def get_service():
        return None


router = APIRouter(prefix="/regulatory-engine", tags=["Regulatory Engine v3"])


class CountriesResponse(BaseModel):
    """Réponse pour la liste des pays"""
    success: bool
    countries: List[str]
    total: int


class DetailsResponse(BaseModel):
    """Réponse pour les détails tarifaires"""
    success: bool
    country_iso3: str
    code: str
    hs6: str
    commodity: Optional[dict] = None
    measures: Optional[List[dict]] = None
    requirements: Optional[List[dict]] = None
    fiscal_advantages: Optional[List[dict]] = None
    total_npf_pct: Optional[float] = None
    total_zlecaf_pct: Optional[float] = None
    savings_pct: Optional[float] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None


@router.get("/countries", response_model=CountriesResponse)
async def get_available_countries():
    """
    Liste des pays disponibles dans le moteur réglementaire.
    """
    service = get_service()
    countries = service.get_available_countries()
    
    return CountriesResponse(
        success=True,
        countries=countries,
        total=len(countries)
    )


@router.get("/details", response_model=DetailsResponse)
async def get_tariff_details(
    country: str = Query(..., description="Code ISO3 du pays (ex: DZA, MAR)"),
    code: str = Query(..., description="Code tarifaire national ou HS6"),
    search_type: str = Query("national", description="Type de recherche: 'national' ou 'hs6'")
):
    """
    Récupère les détails tarifaires complets pour un code donné.
    
    - **country**: Code ISO3 du pays (ex: DZA pour Algérie)
    - **code**: Code tarifaire national (ex: 0101101000) ou HS6 (ex: 010110)
    - **search_type**: 'national' pour code exact, 'hs6' pour toutes les sous-positions
    
    Retourne:
    - Informations sur le produit
    - Liste des mesures (droits et taxes)
    - Formalités administratives requises
    - Avantages fiscaux ZLECAf
    - Totaux NPF et ZLECAf avec économies
    """
    service = get_service()
    
    country = country.upper()
    
    if search_type == "hs6":
        # Recherche par HS6 - retourne la première correspondance
        results = service.get_by_hs6(country, code)
        if not results or not results[0].success:
            error_msg = results[0].error if results else "Aucun résultat"
            return DetailsResponse(
                success=False,
                country_iso3=country,
                code=code,
                hs6=code,
                error=error_msg
            )
        
        # Retourner le premier résultat
        result = results[0]
    else:
        # Recherche par code national exact
        result = service.get_by_national_code(country, code)
    
    if not result.success:
        return DetailsResponse(
            success=False,
            country_iso3=country,
            code=code,
            hs6=result.hs6,
            error=result.error
        )
    
    data = result.data
    
    return DetailsResponse(
        success=True,
        country_iso3=country,
        code=code,
        hs6=data.commodity.hs6,
        commodity=data.commodity.model_dump(),
        measures=[m.model_dump() for m in data.measures],
        requirements=[r.model_dump() for r in data.requirements],
        fiscal_advantages=[fa.model_dump() for fa in data.fiscal_advantages],
        total_npf_pct=data.total_npf_pct,
        total_zlecaf_pct=data.total_zlecaf_pct,
        savings_pct=data.savings_pct,
        processing_time_ms=result.processing_time_ms
    )


@router.get("/details/all", response_model=List[DetailsResponse])
async def get_all_sub_positions(
    country: str = Query(..., description="Code ISO3 du pays"),
    hs6: str = Query(..., description="Code HS6")
):
    """
    Récupère TOUTES les sous-positions nationales pour un code HS6 donné.
    Utile pour voir toutes les variantes d'un même produit.
    """
    service = get_service()
    country = country.upper()
    
    results = service.get_by_hs6(country, hs6)
    
    responses = []
    for result in results:
        if result.success and result.data:
            data = result.data
            responses.append(DetailsResponse(
                success=True,
                country_iso3=country,
                code=data.commodity.national_code,
                hs6=hs6,
                commodity=data.commodity.model_dump(),
                measures=[m.model_dump() for m in data.measures],
                requirements=[r.model_dump() for r in data.requirements],
                fiscal_advantages=[fa.model_dump() for fa in data.fiscal_advantages],
                total_npf_pct=data.total_npf_pct,
                total_zlecaf_pct=data.total_zlecaf_pct,
                savings_pct=data.savings_pct,
                processing_time_ms=result.processing_time_ms
            ))
        else:
            responses.append(DetailsResponse(
                success=False,
                country_iso3=country,
                code=hs6,
                hs6=hs6,
                error=result.error
            ))
    
    return responses


@router.get("/summary/{country}")
async def get_country_summary(country: str):
    """
    Récupère le résumé des données pour un pays.
    
    Inclut:
    - Nombre de lignes tarifaires
    - Nombre de sous-positions
    - Chapitres couverts
    - Taux de TVA
    - Plage des droits de douane
    """
    service = get_service()
    country = country.upper()
    
    summary = service.get_country_summary(country)
    
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=f"Résumé non disponible pour {country}"
        )
    
    return {
        "success": True,
        "country_iso3": country,
        "summary": summary
    }
