"""
Authentic Tariff Routes
API endpoints for authentic African tariff data with sub-positions,
detailed taxes, fiscal advantages, and administrative formalities
"""

import logging
from datetime import date
from typing import Optional

from entitlement_guard import require_calculations_quota
from fastapi import APIRouter, Depends, HTTPException, Query
from services.authentic_tariff_service import (
    calculate_import_taxes,
    get_administrative_formalities,
    get_fiscal_advantages,
    get_taxes_detail,
)
from services.national_legal_calculation_service import (
    SUPPORTED_JURISDICTIONS,
    calculate_kenya_legal_layer,
    calculate_national_legal_layer,
)
from services.regulatory_fee_service import build_regulatory_blocks
from services.tariff_enrichment_service import (
    get_country_enrichment,
    get_supported_enrichment_countries,
)
from services.tariff_provider_service import get_tariff_provider_service

from engine.schemas.legal_override import RemissionEligibility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authentic-tariffs", tags=["Authentic Tariffs"])


def get_provider():
    return get_tariff_provider_service()


@router.get("/enrichment/countries")
async def list_enrichment_countries():
    """Liste exacte des pays couverts par la vague d'enrichissement."""

    countries = get_supported_enrichment_countries()
    return {"success": True, "total": len(countries), "countries": countries}


@router.get("/country/{country_iso3}/enrichment")
async def get_country_enrichment_endpoint(country_iso3: str):
    """Couverture tarifaire, fiscale, documentaire et réglementaire traçable."""

    enrichment = get_country_enrichment(country_iso3)
    if enrichment is None:
        raise HTTPException(
            status_code=404,
            detail=f"No enrichment registry found for country {country_iso3.upper()}",
        )
    return {"success": True, "country_iso3": country_iso3.upper(), "enrichment": enrichment}


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


@router.post("/calculate", dependencies=[Depends(require_calculations_quota())])
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

    country = country_iso3.upper()
    result["country_enrichment"] = get_country_enrichment(country)

    # ── Formalités, prestataires mandatés et frais réglementaires ──
    # Bloc informatif STRICTEMENT SÉPARÉ des droits et taxes : jamais ajouté au
    # coût douanier. Fail-closed : toute erreur de données ou pays non couvert
    # laisse les trois champs à None sans jamais interrompre le calcul
    # tarifaire. Même point d'entrée que /calculate-tariff (routes/calculator.py)
    # afin que ces frais apparaissent quel que soit le chemin de calcul emprunté
    # par le frontend (données "authentiques" vs registre générique).
    origin_iso3 = (origin or "").upper() or None
    try:
        blocks = build_regulatory_blocks(
            country, origin_iso3, fob_value=cif_value, cif_value=cif_value
        )
        result["regulatory_compliance"] = blocks["regulatory_compliance"]
        result["regulatory_cost"] = blocks["regulatory_cost"]
        result["regulatory_reported"] = blocks["regulatory_reported"]
    except Exception as exc:  # pragma: no cover - garde-fou fail-closed
        logger.warning(
            "Regulatory-compliance/fee lookup failed for %s->%s (calcul tarifaire non affecté): %s",
            origin_iso3,
            country,
            exc,
        )
        result["regulatory_compliance"] = None
        result["regulatory_cost"] = None
        result["regulatory_reported"] = None

    parsed_authorization_hs_codes = [
        value.strip() for value in (authorization_hs_codes or "").split(",") if value.strip()
    ]
    parsed_authorization_goods = [
        value.strip() for value in (authorization_goods or "").split(",") if value.strip()
    ]

    if country == "KEN":
        # Alias historique conservé pour compatibilité (frontend, tests) —
        # voir aussi la clé générique ``national_legal_calculation`` ci-dessous.
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
            authorization_hs_codes=parsed_authorization_hs_codes,
            authorization_goods=parsed_authorization_goods,
            beneficiary=beneficiary,
            import_purpose=import_purpose,
            quantity=quantity,
            currency_code="USD",
        )
        result["national_legal_calculation"] = result["kenya_legal_calculation"]
    elif country in SUPPORTED_JURISDICTIONS:
        result["national_legal_calculation"] = calculate_national_legal_layer(
            jurisdiction=country,
            hs_code=hs_code,
            on_date=calculation_date or date.today(),
            customs_value=cif_value,
            base_cet_rate=float(result.get("rates", {}).get("dd_rate_pct", 0) or 0),
            origin=(origin or "").upper() or None,
            remission_eligibility=remission_eligibility,
            authorization_reference=authorization_reference,
            authorization_effective_from=authorization_valid_from,
            authorization_effective_to=authorization_valid_to,
            authorization_hs_codes=parsed_authorization_hs_codes,
            authorization_goods=parsed_authorization_goods,
            beneficiary=beneficiary,
            import_purpose=import_purpose,
            quantity=quantity,
        )

    return result


@router.get(
    "/calculate/{country_iso3}/{hs_code}", dependencies=[Depends(require_calculations_quota())]
)
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
