"""
Premium Opportunités report endpoints.

Exposes the report engine (bilateral product-opportunity report + composite
indicators) and the macro-indicator profile (GAI, gold/FX reserves, import
cover). These endpoints are the API surface of the reworked, premium
Opportunités module described in ``docs/MODULE_OPPORTUNITES_PLAN_PREMIUM.md``.

All values are real or explicitly flagged unavailable — never fabricated.
"""

from typing import Optional

from fastapi import APIRouter, Query
from services import macro_indicators_service as macro
from services import report_engine

router = APIRouter(prefix="/reports")


@router.get("/opportunity", summary="Rapport d'opportunité bilatéral (produit)")
async def opportunity_report(
    hs_code: str = Query(..., description="Code SH (HS6 ou plus court)"),
    origin: str = Query(..., description="Pays exportateur (ISO3)"),
    destination: str = Query(..., description="Marché importateur (ISO3)"),
    goods_value_usd: Optional[float] = Query(
        default=None, description="Valeur FOB des marchandises (USD), pour le coût rendu"
    ),
    weight_kg: float = Query(default=21600.0, description="Poids de l'expédition (kg)"),
    volume_m3: float = Query(default=33.5, description="Volume de l'expédition (m³)"),
):
    """
    Compose supply (production), logistics (multimodal freight), finance & macro
    (trade finance, PAPSS, risque, change, GAI, réserves, couverture des
    importations) et calcule les indicateurs composites (coût rendu, indices,
    score de bout en bout).
    """
    return report_engine.get_opportunity_report(
        hs_code=hs_code,
        origin_iso3=origin,
        destination_iso3=destination,
        goods_value_usd=goods_value_usd,
        weight_kg=weight_kg,
        volume_m3=volume_m3,
    )


@router.get("/market-seeking", summary="Marchés potentiels pour un produit (producteur)")
async def market_seeking_report(
    hs_code: str = Query(..., description="Code SH du produit (HS6 ou HS4)"),
    year: int = Query(default=2022, description="Année des flux commerciaux"),
    lang: str = Query(default="fr", description="Langue du nom de produit (fr/en)"),
):
    """
    Pour un producteur : quels marchés africains **importent** ce produit (la
    demande, via OEC) et qui le **produit** sur le continent (l'offre, via les
    données de production réelles FAO/USGS/UNIDO).

    La demande dégrade gracieusement si l'API OEC est injoignable (plan payant) ;
    l'offre reste disponible localement.
    """
    return await report_engine.get_market_seeking_report(hs_code, year=year, lang=lang)


@router.get("/macro/{country_iso3}", summary="Profil macro-financier d'un pays")
async def macro_profile(country_iso3: str):
    """
    GAI (Global Attractiveness Index), réserves d'or, réserves de change et
    taux de couverture des importations pour un pays (ISO3).
    """
    return macro.get_macro_profile(country_iso3)


@router.get("/oec-health", summary="Diagnostic de connexion OEC (avec token)")
async def oec_health(year: int = Query(default=2022, description="Année de test")):
    """
    Vérifie la connexion à l'API OEC depuis l'environnement courant et indique
    si un token payant est configuré (``OEC_API_TOKEN`` / ``OEC_API_KEY``).

    Utile pour valider le branchement OEC sur le déploiement : ``reachable:true``
    + ``token_configured:true`` confirme que le plan payant répond. Dans ce bac à
    sable, l'accès OEC est bloqué par la politique réseau (``reachable:false``).
    """
    from services.real_trade_data_service import real_trade_service

    return await real_trade_service.ping_oec(year)


@router.get("/health", summary="Diagnostic de disponibilité des données du moteur")
async def reports_health():
    """
    Indique quelles sources d'angle répondent dans l'environnement courant
    (utile car OEC et l'API Banque Mondiale sont bloqués dans certains bacs à
    sable, comme documenté dans le plan).
    """
    # Probe with a well-known pair (Morocco -> Nigeria) and a common HS code.
    probe = report_engine.get_opportunity_report("100590", "MAR", "NGA", goods_value_usd=100000.0)
    ci = probe.get("composite_indicators", {})
    return {
        "supply_available": probe.get("supply", {}).get("available"),
        "logistics_available": (probe.get("logistics", {}).get("accessibility_index", {})).get(
            "available"
        ),
        "financing_available": (ci.get("financing_feasibility_index", {})).get("available"),
        "end_to_end_score_available": (ci.get("end_to_end_score", {})).get("available"),
        "fx_reserves_available": macro.get_fx_reserves("NGA").get("available"),
        "import_cover_available": macro.get_import_cover("NGA").get("available"),
        "gai_available": macro.get_gai("NGA") is not None,
    }
