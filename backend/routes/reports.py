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
    mode: str = Query(
        default="standard",
        description="Mode rapport : 'standard' (indicateurs + scores) ou 'ultra_fine' (+ narrative + benchmarking + segmentation)",
    ),
):
    """
    Compose supply (production), logistics (multimodal freight), finance & macro
    (trade finance, PAPSS, risque, change, GAI, réserves, couverture des
    importations) et calcule les indicateurs composites (coût rendu, indices,
    score de bout en bout).

    Mode 'ultra_fine' enrichit le rapport avec :
    - Analyse narrative factuelle de chaque volet (supply, market, logistics, financing)
    - Benchmarking : classement meilleurs producteurs, analyse coût, infrastructure
    - Segmentation : matrices effort/impact et risque/récompense, factor breakdown,
      priority tier (QUICK_WIN, STRATEGIC_BET, etc.)

    Tous les chiffres sont réels ou flaggés indisponibles (zéro fabrication).
    """
    if mode == "ultra_fine":
        return report_engine.get_opportunity_report_ultra_fine(
            hs_code=hs_code,
            origin_iso3=origin,
            destination_iso3=destination,
            goods_value_usd=goods_value_usd,
            weight_kg=weight_kg,
            volume_m3=volume_m3,
        )
    else:
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


@router.get("/transformation", summary="Scénario S1 : import intrants → production → export")
async def transformation_scenario(
    input_hs_code: str = Query(..., description="Code SH de l'intrant importé"),
    input_origin: str = Query(..., description="Origine de l'intrant (ISO3)"),
    producer: str = Query(..., description="Pays transformateur/producteur (ISO3)"),
    finished_hs_code: str = Query(..., description="Code SH du produit fini"),
    destination: str = Query(..., description="Marché d'export du produit fini (ISO3)"),
    input_value_usd: Optional[float] = Query(
        default=None, description="Valeur FOB des intrants (USD)"
    ),
    finished_value_usd: Optional[float] = Query(
        default=None, description="Valeur FOB du produit fini (USD)"
    ),
    weight_kg: float = Query(default=21600.0, description="Poids de l'expédition (kg)"),
    volume_m3: float = Query(default=33.5, description="Volume de l'expédition (m³)"),
):
    """
    Modélise la chaîne **import intrants → production locale → export** :
    coût rendu des intrants (logistique + tarif réel), capacité de production du
    transformateur, rapport d'opportunité complet pour l'export du produit fini,
    et valeur ajoutée BRUTE (fini − intrant, hors coûts de transformation).

    Toutes les briques sont réelles ou marquées indisponibles ; aucune fabrication.
    """
    return report_engine.get_transformation_scenario(
        input_hs_code=input_hs_code,
        input_origin_iso3=input_origin,
        producer_iso3=producer,
        finished_hs_code=finished_hs_code,
        destination_iso3=destination,
        input_value_usd=input_value_usd,
        finished_value_usd=finished_value_usd,
        weight_kg=weight_kg,
        volume_m3=volume_m3,
    )


@router.get("/national-need", summary="Estimation du besoin national d'un produit")
async def national_need(
    hs_code: str = Query(..., description="Code SH du produit (HS6 ou HS4)"),
    country: str = Query(..., description="Pays (ISO3)"),
    elasticity: float = Query(
        default=0.4, description="Élasticité-revenu (ajustement niveau de vie, L3)"
    ),
):
    """
    Estime le besoin national d'un produit via une cascade transparente :
    L1 consommation apparente mesurée (production+import−export) si disponible,
    sinon L2 proxy population (× disponibilité continentale par habitant), puis
    L3 ajustement au PIB/habitant si le dataset est présent.

    Toute valeur estimée est marquée ``is_estimation:true`` avec formule, intrants
    et sources — jamais présentée comme mesurée, jamais inventée.
    """
    from services import demand_estimation_service as demand

    # Fetch the country's own observed imports of the product (USD) from OEC, when
    # reachable, as a direct demand signal. Gracefully None if OEC is blocked.
    observed_imports = None
    try:
        from services.real_trade_data_service import real_trade_service

        importers = await real_trade_service.get_african_importers_for_product(hs_code)
        for m in importers or []:
            if (m.get("country_iso3") or "").upper() == country.upper():
                observed_imports = {
                    "import_value_usd": m.get("import_value"),
                    "source": "OEC / UN Comtrade (BACI)",
                }
                break
    except Exception:  # OEC unavailable -> no observed-imports signal
        observed_imports = None

    return demand.estimate_national_need(
        hs_code, country, income_elasticity=elasticity, observed_imports=observed_imports
    )


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
