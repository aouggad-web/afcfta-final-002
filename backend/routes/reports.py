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
    with_market_potential: bool = Query(
        default=True,
        description=(
            "Activer la composante potentiel de marché via les imports OEC réels "
            "du marché destination (1 requête OEC). Dégrade gracieusement si OEC "
            "injoignable."
        ),
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

    Le potentiel de marché (demande OEC du marché destination) alimente le score
    quand ``with_market_potential`` est actif et l'OEC répond ; sinon il est exclu
    (jamais inventé).

    Tous les chiffres sont réels ou flaggés indisponibles (zéro fabrication).
    """
    # Fetch the destination's real imports of the product (single OEC request) to
    # activate the market-potential component. Gracefully None if OEC is blocked.
    market_imports = None
    if with_market_potential:
        try:
            from services.real_trade_data_service import real_trade_service

            market_imports = await real_trade_service.get_country_product_imports(
                destination, hs_code
            )
        except Exception:  # OEC unavailable -> component stays excluded
            market_imports = None

    if mode == "ultra_fine":
        return await report_engine.get_opportunity_report_ultra_fine(
            hs_code=hs_code,
            origin_iso3=origin,
            destination_iso3=destination,
            goods_value_usd=goods_value_usd,
            weight_kg=weight_kg,
            volume_m3=volume_m3,
            market_imports=market_imports,
        )
    else:
        return report_engine.get_opportunity_report(
            hs_code=hs_code,
            origin_iso3=origin,
            destination_iso3=destination,
            goods_value_usd=goods_value_usd,
            weight_kg=weight_kg,
            volume_m3=volume_m3,
            market_imports=market_imports,
        )


@router.get("/market-seeking", summary="Marchés potentiels pour un produit (producteur)")
async def market_seeking_report(
    hs_code: str = Query(..., description="Code SH du produit (HS6 ou HS4)"),
    lang: str = Query(default="fr", description="Langue du nom de produit (fr/en)"),
):
    """
    Pour un producteur : quels marchés africains **importent** ce produit (la
    demande, via OEC) et qui le **produit** sur le continent (l'offre, via les
    données de production réelles FAO/USGS/UNIDO).

    Utilise toujours la dernière année de données disponible (pas de choix
    d'année exposé : les flux commerciaux et la production continentale ne
    sont pas des séries que l'utilisateur a de raison de vouloir figer dans
    le passé pour ce cas d'usage — trouver des débouchés aujourd'hui).

    La demande dégrade gracieusement si l'API OEC est injoignable (plan payant) ;
    l'offre reste disponible localement.
    """
    return await report_engine.get_market_seeking_report(hs_code, lang=lang)


@router.get(
    "/import-opportunities",
    summary="Scénario S4 : meilleures opportunités d'IMPORTATION pour un pays",
)
async def import_opportunities_scenario(
    country: str = Query(..., description="Pays importateur (ISO3)"),
    top_k: int = Query(default=8, ge=1, le=20, description="Nb de produits analysés en profondeur"),
    goods_value_usd: float = Query(default=50000.0, description="Valeur FOB de référence (USD)"),
    with_observed_imports: bool = Query(
        default=False,
        description=(
            "Enrichir chaque produit du top avec les imports observés du pays (OEC, "
            "canal partagé avec le module Statistiques — une réponse cachée par pays "
            "sert tous les codes SH)."
        ),
    ),
):
    """
    Scénario **S4** — le miroir de S2 côté import : pour un pays, quels produits
    sourcer en Afrique, auprès de qui, avec quel avantage ZLECAf réel ?

    Interconnecte les modules de la plateforme : production (FAOSTAT/USGS/UNIDO),
    statistiques (besoins, imports OEC optionnels), calculateur (régime
    préférentiel réel par origine — ex. réciprocité algérienne), logistique et
    finance (score bilatéral de bout en bout). Classement par part de besoin non
    couvert puis pression d'import ; fournisseur choisi par avantage tarifaire
    réel puis poids de production. Zéro fabrication : estimations étiquetées.
    """
    rep = report_engine.get_import_opportunities_scenario(
        destination_iso3=country, top_k=top_k, goods_value_usd=goods_value_usd
    )

    # Enrichissement optionnel : imports observés (OEC) par produit du top —
    # peu coûteux grâce au canal partagé (le cache par pays sert tous les HS).
    if with_observed_imports:
        try:
            from services.real_trade_data_service import real_trade_service

            for opp in rep.get("ranked_opportunities", []):
                imp = await real_trade_service.get_country_product_imports(
                    country, opp.get("hs_code")
                )
                if imp and imp.get("available"):
                    opp["observed_imports"] = {
                        "import_value_usd": imp.get("import_value_usd"),
                        "year": imp.get("year"),
                        "source": imp.get("source"),
                    }
        except Exception:  # OEC indisponible -> enrichissement simplement absent
            pass

    return rep


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


@router.get("/direct-export", summary="Scénario S2 : production → export direct (marchés classés)")
async def direct_export_scenario(
    hs_code: str = Query(..., description="Code SH du produit"),
    producer: str = Query(..., description="Pays producteur/exportateur (ISO3)"),
    top_k: int = Query(
        default=5, ge=1, le=15, description="Nombre de marchés à analyser en profondeur"
    ),
    goods_value_usd: Optional[float] = Query(default=None, description="Valeur FOB (USD)"),
    weight_kg: float = Query(default=21600.0, description="Poids de l'expédition (kg)"),
    volume_m3: float = Query(default=33.5, description="Volume de l'expédition (m³)"),
):
    """
    Pour un producteur d'un produit : **quels marchés africains viser en export ?**
    Classe les marchés par besoin estimé (proxy population / consommation
    apparente), puis analyse en profondeur les ``top_k`` plus gros (logistique,
    finance, tarif ZLECAf réel, score de bout en bout) et les ordonne par score.

    Données réelles ou marquées indisponibles ; besoins étiquetés comme estimations.
    """
    return report_engine.get_direct_export_scenario(
        hs_code=hs_code,
        producer_iso3=producer,
        top_k=top_k,
        goods_value_usd=goods_value_usd,
        weight_kg=weight_kg,
        volume_m3=volume_m3,
    )


@router.get("/national-need", summary="Estimation du besoin national d'un produit")
async def national_need(
    hs_code: str = Query(..., description="Code SH du produit (HS6 ou HS4)"),
    country: str = Query(..., description="Pays (ISO3)"),
    elasticity: Optional[float] = Query(
        default=None,
        description=(
            "Élasticité-revenu (ajustement niveau de vie, L3). Défaut : résolue "
            "par classe de produit (chapitre SH) — aliments de base ~0,3, "
            "pharma ~0,9, biens durables ~1,2."
        ),
    ),
    with_observed_imports: bool = Query(
        default=False,
        description=(
            "Ajouter le signal d'import observé (OEC) du pays. Passe par le canal "
            "OEC partagé avec le module Statistiques (cache persistant) — "
            "désactivé par défaut pour rester indépendant du réseau."
        ),
    ),
):
    """
    Estime le besoin national d'un produit via une cascade transparente :
    L1 consommation apparente mesurée (production+import−export) si disponible,
    sinon L2 proxy population (× disponibilité continentale par habitant), puis
    L3 ajustement au PIB/habitant si le dataset est présent.

    Toute valeur estimée est marquée ``is_estimation:true`` avec formule, intrants
    et sources — jamais présentée comme mesurée, jamais inventée.

    Le signal d'import observé (OEC) est **opt-in** (``with_observed_imports``) ;
    quand il est présent, il sert de PLANCHER mesuré à l'estimation (le besoin
    d'un pays est au moins ce qu'il importe déjà — recalage signalé dans
    ``calibration``). Il interroge le pays demandé uniquement (plus de fan-out
    54 pays), via le même client OEC que la recherche SH2/SH4/SH6 du module
    Statistiques : cache persistant partagé, servi même si l'OEC est
    momentanément injoignable (stale-on-error).
    """
    from services import demand_estimation_service as demand

    # Observed-imports is a supplemental signal only. Off by default so the
    # estimate stays fast and never depends on OEC. Single-country request via
    # the OEC channel shared with the statistics module (persistent cache).
    observed_imports = None
    if with_observed_imports:
        try:
            from services.real_trade_data_service import real_trade_service

            imp = await real_trade_service.get_country_product_imports(country, hs_code)
            if imp and imp.get("available"):
                observed_imports = {
                    "import_value_usd": imp.get("import_value_usd"),
                    "year": imp.get("year"),
                    "source": imp.get("source") or "OEC / UN Comtrade (BACI)",
                }
        except Exception:  # OEC unavailable -> no observed-imports signal
            observed_imports = None

    result = demand.estimate_national_need(
        hs_code, country, income_elasticity=elasticity, observed_imports=observed_imports
    )

    # Repli automatique (pas opt-in) : quand aucune production continentale de
    # référence n'existe pour ce SH (ex. instruments médicaux SH90 — aucun
    # mapping FAO/USGS/UNIDO), l'estimation serait sinon "impossible". On va
    # chercher l'historique d'imports RÉEL du pays lui-même (canal OEC partagé,
    # cache persistant) et on relance le calcul avec ce signal mesuré — moyenné
    # sur plusieurs années pour les biens durables/longue conservation.
    if not result.get("available") and "production continentale indisponible" in (
        result.get("note") or ""
    ):
        try:
            from services.real_trade_data_service import real_trade_service

            history = await real_trade_service.get_country_product_import_history(country, hs_code)
            if history and history.get("available") and history.get("imports"):
                result = demand.estimate_national_need(
                    hs_code,
                    country,
                    income_elasticity=elasticity,
                    observed_imports=observed_imports,
                    own_imports_history=history["imports"],
                )
        except Exception:  # OEC indisponible -> le message "impossible" est conservé
            pass

    return result


@router.get("/risk-ratio/{country_iso3}", summary="Ratio de risque pays composite (détaillé)")
async def risk_ratio(country_iso3: str):
    """
    Ratio de risque composite 0-100 (100 = risque minimal) pour un pays
    partenaire du module Opportunités :

    - **composante souveraine** : notations Standard & Poor's, Moody's,
      Fitch Ratings, Scope converties en crans standard (AAA = 100, défaut = 0)
      — plafond macro-financier du pays ;
    - **composante opérationnelle** : grade A1→D (convention d'échelle
      Coface/OCDE, du type des évaluations publiées par la Coface ou Allianz
      Trade) issu des profils curés de la plateforme — risque d'impayé
      commercial court terme, change, politique, transfert, assurance-crédit.

    Pondération nominale 60 % opérationnel / 40 % souverain (une opportunité
    est une transaction commerciale, pas un investissement souverain). La
    réponse embarque la formule, les poids effectifs, le détail des intrants,
    la méthodologie complète et les mises en garde — aucune valeur n'est
    inventée : composante manquante = poids reporté + confiance « dégradée ».
    """
    from services import country_risk_service

    return country_risk_service.get_risk_ratio(country_iso3)


@router.get("/macro/{country_iso3}", summary="Profil macro-financier d'un pays")
async def macro_profile(country_iso3: str):
    """
    GAI (Global Attractiveness Index), réserves d'or, réserves de change et
    taux de couverture des importations pour un pays (ISO3).
    """
    return macro.get_macro_profile(country_iso3)


@router.get("/oec-health", summary="Diagnostic de connexion OEC (canal gratuit + direct)")
async def oec_health(year: int = Query(default=2022, description="Année de test")):
    """
    Vérifie la connexion à l'OEC depuis l'environnement courant, en sondant
    d'abord le **canal gratuit du module Statistiques** (``api.oec.world``,
    aucun token requis — c'est le canal qu'utilise le module Opportunités),
    puis l'API directe historique (``api-v2.oec.world``).

    ``reachable:true`` dès que l'un des deux canaux répond. ``token_configured``
    indique si un token payant optionnel est présent (``OEC_API_TOKEN``) — il
    n'est PAS nécessaire au fonctionnement du module.
    """
    import time

    from services.real_trade_data_service import real_trade_service

    # 1) Canal gratuit du module Statistiques (celui des Opportunités).
    free_channel = {"reachable": False, "endpoint": "api.oec.world (module Statistiques)"}
    try:
        from services.oec_trade_service import oec_service

        t0 = time.monotonic()
        res = await oec_service.get_top_african_importers("180100", year)
        rows = (res or {}).get("data") or []
        free_channel = {
            "reachable": bool(rows),
            "endpoint": "api.oec.world (module Statistiques, gratuit, sans token)",
            "latency_ms": round((time.monotonic() - t0) * 1000),
            "records": len(rows),
        }
    except Exception as e:
        free_channel["error"] = str(e)

    # 2) API directe historique (diagnostic complémentaire).
    direct = await real_trade_service.ping_oec(year)

    return {
        "reachable": bool(free_channel.get("reachable") or direct.get("reachable")),
        "primary_channel": "statistics_free",
        "channels": {"statistics_free": free_channel, "direct_api_v2": direct},
        "token_configured": direct.get("token_configured"),
        "note": (
            "Le module Opportunités consomme l'OEC via le canal gratuit du module "
            "Statistiques (cache partagé, stale-on-error) ; aucun token requis."
        ),
    }


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
