"""
Authentic Tariff Routes
API endpoints for authentic African tariff data with sub-positions,
detailed taxes, fiscal advantages, and administrative formalities
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from services.authentic_tariff_service import (
    get_fiscal_advantages,
    get_taxes_detail,
)
from services.crawled_data_service import crawled_service
from services.export_tariff_service import (
    compute_export_taxes,
    get_country_providers,
    get_export_profile,
)
from services.tariff_doctrine import (
    crawl_enregistre,
    get_country_doctrine_status,
    not_recrawled_http_detail,
    provider_fee_flags,
)
from services.tariff_enrichment_service import (
    get_country_enrichment,
    get_supported_enrichment_countries,
)
from services.tariff_provider_service import get_tariff_provider_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authentic-tariffs", tags=["Authentic Tariffs"])


def get_provider():
    return get_tariff_provider_service()


def _ensure_servable_or_404(country_iso3: str) -> None:
    """
    Doctrine tarifaire : refuser explicitement les pays dont les données
    nationales n'ont pas été re-collectées depuis une base officielle
    vérifiable, au lieu de servir des données estimées/synthétiques.
    """
    try:
        status = get_country_doctrine_status(country_iso3.upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if status.get("status") == "NOT_RECRAWLED":
        raise HTTPException(status_code=404, detail=not_recrawled_http_detail(country_iso3))
    if status.get("status") == "NO_FILE":
        raise HTTPException(
            status_code=404,
            detail={
                "error": "COUNTRY_NO_TARIFF_DATA",
                "country_iso3": country_iso3.upper(),
                "message_fr": status.get("message_fr"),
                "message_en": status.get("message_en"),
            },
        )


def _ensure_consultable_or_404(country_iso3: str) -> None:
    """Données de consultation : servies dès que le crawl du pays est enregistré.

    Sous-positions, formalités et recherche se lisent sur le crawl. Seul le
    calcul historique reste soumis à la doctrine du fichier ETL.
    """
    try:
        if crawl_enregistre(country_iso3):
            return
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    _ensure_servable_or_404(country_iso3)


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
    _ensure_servable_or_404(country_iso3)
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
    _ensure_servable_or_404(country_iso3)
    tariff = get_provider().get_tariff_line(country_iso3.upper(), hs_code)

    if not tariff:
        raise HTTPException(status_code=404, detail=f"No tariff found for {country_iso3}/{hs_code}")

    # Frais de prestataires (ex. redevances de prestations douanières) :
    # marquage explicite quand ils sont présents dans le détail des taxes.
    for tax in tariff.get("taxes_detail") or []:
        tax.update(provider_fee_flags(tax))

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
    _ensure_consultable_or_404(country_iso3)
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
    _ensure_servable_or_404(country_iso3)
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
    _ensure_servable_or_404(country_iso3)
    advantages = get_fiscal_advantages(country_iso3.upper(), hs_code)

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "advantages": advantages,
    }


@router.get("/country/{country_iso3}/export-taxes/{hs_code}")
async def get_export_taxes_endpoint(
    country_iso3: str, hs_code: str, language: str = Query("fr", description="Language: fr or en")
):
    """
    Taxes et redevances à l'EXPORT d'une position tarifaire

    Sources : documents douaniers nationaux crawlés (ex. douane.gov.tn —
    Tarif Web, redevances de prestations douanières à l'export).
    Inclut le marquage explicite des frais de prestataires quand ils sont
    présents.

    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)

    Returns:
        Liste des taxes/redevances export applicables, ou
        EXPORT_DATA_NOT_AVAILABLE si le pays crawlé n'en publie pas.
    """
    try:
        export_data = crawled_service.get_export_taxes(country_iso3.upper(), hs_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not export_data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "EXPORT_DATA_NOT_AVAILABLE",
                "country_iso3": country_iso3.upper(),
                "hs_code": hs_code,
                "message_fr": (
                    "Aucune taxe/redevance à l'export publiée par la source officielle "
                    "crawlée pour cette position."
                ),
                "message_en": (
                    "No export tax/levy published by the crawled official source "
                    "for this position."
                ),
            },
        )

    # Frais de prestataires : marquage explicite (redevances de prestations).
    for tax in export_data.get("export_taxes", []):
        tax.update(provider_fee_flags(tax))

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "position_code": export_data.get("code", ""),
        "designation": export_data.get("designation", ""),
        "export_taxes": export_data.get("export_taxes", []),
        "source": export_data.get("source", ""),
    }


async def _compute_export_or_404(
    country_iso3: str,
    hs_code: str,
    value: float,
    quantity: float,
    net_weight_kg: float,
):
    try:
        result = compute_export_taxes(
            country_iso3=country_iso3.upper(),
            hs_code=hs_code,
            customs_value=value,
            quantity=quantity,
            net_weight_kg=net_weight_kg,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get("/export-calculate/{country_iso3}/{hs_code}")
async def calculate_export_taxes_get_endpoint(
    country_iso3: str,
    hs_code: str,
    value: float = Query(
        0.0, ge=0, description="Valeur douane déclarée (devise du tarif national)"
    ),
    quantity: float = Query(0.0, ge=0, description="Quantité (unités statistiques)"),
    net_weight_kg: float = Query(
        0.0, ge=0, description="Poids net en kg (droits spécifiques au kg)"
    ),
):
    """
    Calculer la cascade de taxes et redevances à l'EXPORT (par pays) — GET

    Chaque pays a son propre système tarifaire export, documenté position par
    position dans sa source officielle crawlée (ex. douane.gov.tn — Tarif Web :
    droits export dattes, taxes ferrailles au kg, redevances de prestations
    douanières). Les assiettes officielles déclarées sont respectées
    (« SOMME D.T », « VALEUR DOUANE DINARS », « PN (KG) »).

    Les frais de prestataires délégataires de missions régaliennes sont marqués
    avec leur payeur (État ou opérateurs économiques) quand ils sont présents.

    Refus explicite (aucun calcul) si le pays n'a pas de données export
    officielles crawlées — jamais de données estimées.
    """
    return await _compute_export_or_404(country_iso3, hs_code, value, quantity, net_weight_kg)


@router.post("/export-calculate")
async def calculate_export_taxes_post_endpoint(
    country_iso3: str = Query(..., description="ISO3 du pays exportateur"),
    hs_code: str = Query(..., description="Code SH national (6-12 chiffres)"),
    value: float = Query(
        0.0, ge=0, description="Valeur douane déclarée (devise du tarif national)"
    ),
    quantity: float = Query(0.0, ge=0, description="Quantité (unités statistiques)"),
    net_weight_kg: float = Query(
        0.0, ge=0, description="Poids net en kg (droits spécifiques au kg)"
    ),
):
    """Version POST du calcul export (même moteur que le GET)."""
    return await _compute_export_or_404(country_iso3, hs_code, value, quantity, net_weight_kg)


@router.get("/country/{country_iso3}/tariff-system")
async def get_country_tariff_system_endpoint(country_iso3: str):
    """
    Système tarifaire d'un pays : cascades import/export documentées et
    prestataires délégataires de missions régaliennes (avec payeur des
    redevances), uniquement depuis des sources officielles vérifiables.
    """
    try:
        profile = get_export_profile(country_iso3)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "tariff_system": profile.get("tariff_system", {}),
        "providers": get_country_providers(country_iso3),
        "verification_status": profile.get("verification_status"),
        "note": (
            "Prestataires délégataires documentés uniquement — aucune entrée non "
            "vérifiée n'est servie (registre providers_registry.json)."
        ),
    }


def register_routes(api_router):
    """Register authentic tariff routes with the main API router"""
    api_router.include_router(router)
