"""
Authentic Tariff Routes
API endpoints for authentic African tariff data with sub-positions,
detailed taxes, fiscal advantages, and administrative formalities
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from services.authentic_tariff_service import (
    calculate_import_taxes,
    get_administrative_formalities,
    get_fiscal_advantages,
    get_taxes_detail,
)
from services.kenya_legal_calculation_service import calculate_kenya_legal_layer
from services.tariff_provider_service import get_tariff_provider_service

from engine.schemas.legal_override import RemissionEligibility
from engine.import_charges import (
    OVERALL_STATUS_ALIASES,
    OVERALL_STATUS_VALUES,
    QUALITY_DIMENSION_KEYS,
    QUALITY_DIMENSION_VALUES,
    calculate_import_charges,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authentic-tariffs", tags=["Authentic Tariffs"])


def get_provider():
    return get_tariff_provider_service()


@router.get("/countries")
async def list_available_countries():
    """
    Liste des pays avec données tarifaires authentiques

    Returns:
        Liste des pays et leurs statistiques tarifaires
    """
    countries = get_provider().get_available_countries()
    return {
        "success": True,
        "total": len(countries),
        "countries": countries,
        "data_format": "hybrid_postgres_first",
        "source": "Tariff Provider (postgres-first)",
    }


@router.get("/country/{country_iso3}/summary")
async def get_tariff_summary(country_iso3: str):
    """
    Résumé des données tarifaires d'un pays

    Args:
        country_iso3: Code ISO3 du pays (ex: DZA, ETH)

    Returns:
        Statistiques et résumé des tarifs
    """
    summary = get_provider().get_country_summary(country_iso3.upper())

    if not summary:
        raise HTTPException(
            status_code=404, detail=f"No tariff data found for country {country_iso3}"
        )

    return {"success": True, "country_iso3": country_iso3.upper(), "summary": summary}


@router.get("/country/{country_iso3}/line/{hs_code}")
async def get_tariff_line_endpoint(
    country_iso3: str, hs_code: str, language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir une ligne tarifaire complète avec sous-positions

    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        language: Langue pour les descriptions

    Returns:
        Ligne tarifaire complète avec taxes, avantages, formalités
    """
    tariff = get_provider().get_tariff_line(country_iso3.upper(), hs_code)

    if not tariff:
        raise HTTPException(status_code=404, detail=f"No tariff found for {country_iso3}/{hs_code}")

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "tariff_line": tariff,
    }


@router.get("/country/{country_iso3}/sub-positions/{hs6}")
async def get_sub_positions_endpoint(
    country_iso3: str, hs6: str, language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir toutes les sous-positions nationales pour un code HS6

    Args:
        country_iso3: Code ISO3 du pays
        hs6: Code HS6 (6 chiffres)

    Returns:
        Liste des sous-positions avec leurs taux DD spécifiques
    """
    sub_positions = get_provider().get_sub_positions(country_iso3.upper(), hs6[:6])

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs6": hs6[:6],
        "total": len(sub_positions),
        "sub_positions": sub_positions,
        "note_fr": "Les sous-positions nationales peuvent avoir des taux DD différents du code HS6 parent",
        "note_en": "National sub-positions may have different DD rates than the parent HS6 code",
    }


@router.get("/country/{country_iso3}/taxes/{hs_code}")
async def get_taxes_detail_endpoint(
    country_iso3: str, hs_code: str, language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir le détail des taxes pour un code HS

    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS

    Returns:
        Détail de chaque taxe (DD, TVA, PRCT, TCS, etc.)
    """
    taxes = get_taxes_detail(country_iso3.upper(), hs_code)

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "taxes": taxes,
    }


@router.get("/country/{country_iso3}/advantages/{hs_code}")
async def get_fiscal_advantages_endpoint(
    country_iso3: str, hs_code: str, language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir les avantages fiscaux (dont ZLECAf) pour un code HS

    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS

    Returns:
        Liste des avantages fiscaux applicables
    """
    advantages = get_fiscal_advantages(country_iso3.upper(), hs_code)

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "advantages": advantages,
    }


@router.get("/country/{country_iso3}/formalities/{hs_code}")
async def get_formalities_endpoint(
    country_iso3: str, hs_code: str, language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir les formalités administratives requises pour un code HS

    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS

    Returns:
        Liste des documents/formalités requis
    """
    formalities = get_administrative_formalities(country_iso3.upper(), hs_code)

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "formalities": formalities,
    }


@router.post("/calculate")
async def calculate_taxes_endpoint(
    country_iso3: str = Query(..., description="ISO3 country code"),
    hs_code: str = Query(..., description="HS code (6-12 digits)"),
    cif_value: float = Query(..., description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en"),
    origin: str = Query(None, description="Origin country ISO3 (gates ZLECAf eligibility)"),
    calculation_date: Optional[date] = Query(None, description="Legal calculation date"),
    remission_eligibility: RemissionEligibility = Query(
        RemissionEligibility.ELIGIBILITY_UNKNOWN,
        description="Eligibility for a conditional EAC duty remission",
    ),
    authorization_reference: Optional[str] = Query(None),
    authorization_valid_from: Optional[date] = Query(None),
    authorization_valid_to: Optional[date] = Query(None),
    authorization_hs_codes: Optional[str] = Query(
        None, description="Comma-separated exact tariff lines in the authorization"
    ),
    authorization_goods: Optional[str] = Query(
        None, description="Comma-separated authorized-goods descriptions for audit"
    ),
    beneficiary: Optional[str] = Query(None),
    import_purpose: Optional[str] = Query(None),
    quantity: Optional[float] = Query(None, ge=0),
):
    """
    Calculer les taxes d'importation avec données authentiques

    Calcule et compare:
    - Régime NPF (Normal)
    - Régime ZLECAf (avec exonérations)
    - Économies réalisées

    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        cif_value: Valeur CIF en USD
        language: Langue pour les descriptions

    Returns:
        Calcul détaillé NPF vs ZLECAf avec économies
    """
    result = calculate_import_taxes(
        country_iso3=country_iso3.upper(),
        hs_code=hs_code,
        cif_value=cif_value,
        language=language,
        origin_country=origin,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    if country_iso3.upper() == "KEN":
        result["kenya_legal_calculation"] = calculate_kenya_legal_layer(
            hs_code=hs_code,
            on_date=calculation_date or date.today(),
            customs_value=cif_value,
            base_cet_rate=float(result.get("rates", {}).get("dd_rate_pct", 0) or 0),
            origin=(origin or "").upper() or None,
            remission_eligibility=remission_eligibility,
            authorization_reference=authorization_reference,
            authorization_effective_from=authorization_valid_from,
            authorization_effective_to=authorization_valid_to,
            authorization_hs_codes=(authorization_hs_codes or "").split(","),
            authorization_goods=(authorization_goods or "").split(","),
            beneficiary=beneficiary,
            import_purpose=import_purpose,
            quantity=quantity,
            currency_code="USD",
        )
    else:
        # All non-Kenya destinations use the shared regional/national facade.
        # Providers are intentionally not guessed here: absent dated layers
        # produce INFORMATIVE_PARTIAL with the missing sources in the trace.
        result["generic_legal_calculation"] = calculate_import_charges(
            importing_country=country_iso3.upper(),
            exporting_country=(origin or "").upper(),
            hs6=hs_code[:6],
            national_code=hs_code,
            customs_value=cif_value,
            calculation_date=calculation_date or date.today(),
            importer_profile={
                "base_rate": float(result.get("rates", {}).get("dd_rate_pct", 0) or 0),
                "origin": (origin or "").upper() or None,
                "beneficiary": beneficiary,
                "import_purpose": import_purpose,
                "quantity": quantity,
                "administrative_formalities": get_administrative_formalities(country_iso3.upper(), hs_code) or [],
            },
            intended_use=import_purpose,
            authorizations={
                "remission_eligibility": remission_eligibility,
                "authorization_reference": authorization_reference,
                "authorization_effective_from": authorization_valid_from,
                "authorization_effective_to": authorization_valid_to,
                "authorization_hs_codes": [value.strip() for value in (authorization_hs_codes or "").split(",") if value.strip()],
                "authorization_goods": [value.strip() for value in (authorization_goods or "").split(",") if value.strip()],
            },
            regional_coverage_complete=False,
            national_coverage_complete=False,
            currency_code="USD",
        )

    legal_result = result.get("kenya_legal_calculation") or result.get("generic_legal_calculation") or {}
    # Normalize legacy nested statuses at the API boundary without changing
    # existing route fields or the supplied tariff rates.
    raw_status = legal_result.get("overall_status") or legal_result.get("calculation_status") or legal_result.get("status")
    if raw_status:
        normalized_status = OVERALL_STATUS_ALIASES.get(str(raw_status).upper(), str(raw_status).upper())
        if normalized_status in OVERALL_STATUS_VALUES:
            result["overall_status"] = normalized_status
    raw_dimensions = legal_result.get("quality_dimensions")
    if isinstance(raw_dimensions, dict):
        defaults = {
            "source": "PARTIAL",
            "temporal_validity": "PARTIAL",
            "classification": "DOCUMENTED",
            "taxes_and_levies": "PARTIAL",
            "preference_and_origin": "UNVERIFIED",
            "formalities": "NOT_AVAILABLE",
        }
        if set(raw_dimensions).issubset(set(QUALITY_DIMENSION_KEYS)) and all(
            value in QUALITY_DIMENSION_VALUES for value in raw_dimensions.values()
        ):
            result["quality_dimensions"] = {**defaults, **raw_dimensions}
    result["disclaimer"] = {
        "informational_only": True,
        "legally_binding": False,
        "message": "Simulation informative fondée sur les données disponibles.",
    }
    result["informational_only"] = True
    result["legally_binding"] = False
    result.setdefault("administrative_confirmation_recommended", True)
    result.setdefault("administrative_confirmation_required", True)
    # Keep the established top-level response shape while exposing the
    # documentary envelope to API consumers that do not inspect the nested
    # legal calculation object.
    for key in (
        "known_data_gaps",
        "source_authority",
        "source_date",
        "effective_date",
        "completeness_status",
        "technical_validation_status",
    ):
        if key in legal_result:
            result.setdefault(key, legal_result[key])
    result.setdefault("overall_status", "INFORMATIVE_PARTIAL")
    result.setdefault("quality_dimensions", {
        "source": "PARTIAL",
        "temporal_validity": "PARTIAL",
        "classification": "DOCUMENTED",
        "taxes_and_levies": "PARTIAL",
        "preference_and_origin": "UNVERIFIED",
        "formalities": "NOT_AVAILABLE",
    })
    result.setdefault("known_data_gaps", [])
    result.setdefault("completeness_status", result["overall_status"])
    return result


@router.get("/calculate/{country_iso3}/{hs_code}")
async def calculate_taxes_get_endpoint(
    country_iso3: str,
    hs_code: str,
    value: float = Query(10000, description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en"),
    origin: str = Query(None, description="Origin country ISO3 (gates ZLECAf eligibility)"),
    calculation_date: Optional[date] = Query(None, description="Legal calculation date"),
    remission_eligibility: RemissionEligibility = Query(RemissionEligibility.ELIGIBILITY_UNKNOWN),
    authorization_reference: Optional[str] = Query(None),
    authorization_valid_from: Optional[date] = Query(None),
    authorization_valid_to: Optional[date] = Query(None),
    authorization_hs_codes: Optional[str] = Query(None),
    authorization_goods: Optional[str] = Query(None),
    beneficiary: Optional[str] = Query(None),
    import_purpose: Optional[str] = Query(None),
    quantity: Optional[float] = Query(None, ge=0),
):
    """
    Version GET du calculateur (pour tests rapides)
    """
    return await calculate_taxes_endpoint(
        country_iso3=country_iso3,
        hs_code=hs_code,
        cif_value=value,
        language=language,
        origin=origin,
        calculation_date=calculation_date,
        remission_eligibility=remission_eligibility,
        authorization_reference=authorization_reference,
        authorization_valid_from=authorization_valid_from,
        authorization_valid_to=authorization_valid_to,
        authorization_hs_codes=authorization_hs_codes,
        authorization_goods=authorization_goods,
        beneficiary=beneficiary,
        import_purpose=import_purpose,
        quantity=quantity,
    )


@router.get("/search/{country_iso3}")
async def search_tariffs_endpoint(
    country_iso3: str,
    q: str = Query(..., min_length=2, description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, le=100, description="Max results"),
):
    """
    Rechercher dans les lignes tarifaires d'un pays

    Args:
        country_iso3: Code ISO3 du pays
        q: Requête de recherche (code HS ou description)
        language: Langue
        limit: Nombre max de résultats

    Returns:
        Liste des lignes tarifaires correspondantes
    """
    results = get_provider().search_tariff_lines(
        country_iso3=country_iso3.upper(), query=q, language=language, limit=limit
    )

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "query": q,
        "total": len(results),
        "results": results,
    }


def register_routes(api_router):
    """Register authentic tariff routes with the main API router"""
    api_router.include_router(router)
