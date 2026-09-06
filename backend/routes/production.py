"""
Routes pour le module Production — ISIC4 + Capacité de production africaine
============================================================================
Endpoints pour exposer :
  - Données UNIDO ISIC Rev.4 (IDSB + INDSTAT) par pays
  - Capacité de production réelle (FAO/USGS/UNIDO) par code HS
  - Classements continentaux et scénarios d'intégration ZLECAf
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional, Dict, List

from etl.isic4_idsb_data import (
    get_country_isic4_summary,
    get_isic4_timeseries,
    list_covered_countries,
    list_covered_countries_filtered,
    is_country_covered,
)

# Production capacity service is optional (depends on production_data.py)
try:
    from services.production_capacity_service import (
        get_capacity,
        get_country_profile,
        get_continental_producers,
        list_tracked_products,
    )
    HAS_CAPACITY_SERVICE = True
except (ImportError, ModuleNotFoundError):
    HAS_CAPACITY_SERVICE = False

router = APIRouter(prefix="/api/production", tags=["production"])


# ═══════════════════════════════════════════════════════════════════════════════
# UNIDO ISIC4 ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/isic4/countries",
    summary="Liste des pays couverts UNIDO",
    description="Retourne la liste ISO3 des pays ayant des données ISIC4 (officielles ou estimées).",
)
def list_isic4_countries(
    include_estimates: bool = Query(True, description="Inclure les pays avec données estimées UNIDO (par défaut: vrai)")
):
    """GET /api/production/isic4/countries?include_estimates=true

    Retourne les pays couverts par UNIDO IDSB/INDSTAT.
    - include_estimates=true (défaut): tous les pays avec données officielles ET estimées
    - include_estimates=false: pays avec données officielles uniquement
    """
    countries = list_covered_countries_filtered(official_only=not include_estimates)
    return {
        "countries": countries,
        "count": len(countries),
        "include_estimates": include_estimates,
        "source": "UNIDO IDSB + INDSTAT (2018-2024, ISIC Rev.4 4-digit class)",
        "note": "Les données incluent à la fois OFFICIAL_STATISTICS et UNIDO_DERIVED_ESTIMATE. Voir badges dans les réponses détaillées."
    }


@router.get(
    "/isic4/{country_iso3}",
    summary="Données ISIC Rev.4 par pays — UNIDO IDSB + INDSTAT",
    description="Retourne tous les secteurs ISIC 4 chiffres pour un pays avec "
    "dernière année disponible par indicateur (officielles et estimées). "
    "Données : output, imports, exports, apparent consumption (IDSB), "
    "establishments, employees, wages, value added (INDSTAT).",
)
def get_isic4_country_data(country_iso3: str = Path(..., description="Code ISO3 du pays")):
    """
    GET /api/production/isic4/{country_iso3}

    Retourne un tableau ISIC4 optimisé pour affichage :
    - Formaté avec colonnes adaptées au nombre d'indicateurs
    - Tri par code ISIC (ordre croissant)
    - Métadonnées source + années couvertes
    """
    if not is_country_covered(country_iso3.upper()):
        raise HTTPException(
            status_code=404,
            detail=f"Pays {country_iso3} non couvert par les données UNIDO IDSB/INDSTAT. "
            f"Pays couverts : {', '.join(list_covered_countries())}",
        )

    summary = get_country_isic4_summary(country_iso3.upper())
    if not summary:
        raise HTTPException(status_code=404, detail=f"Données non trouvées pour {country_iso3}")

    # Réformat pour optimiser l'affichage tableau
    return {
        "country_iso3": summary["country_iso3"],
        "country_name": summary["country_name"],
        "classification": "ISIC Rev.4 (4 chiffres)",
        "source": summary["source"],
        "years_covered": summary["years_covered"],
        "total_sectors": len(summary["sectors"]),
        "data_includes": "OFFICIAL_STATISTICS et UNIDO_DERIVED_ESTIMATE (voir champ 'data_nature' par indicateur)",
        "sectors": [
            {
                "isic4": s["isic4"],
                "description": s["isic_description"],
                "indicators": s["indicators"],
                "indicator_count": len(s["indicators"]),
            }
            for s in summary["sectors"]
        ],
    }


@router.get(
    "/isic4/{country_iso3}/{isic4_code}",
    summary="Série temporelle ISIC4 — 2018-2024",
    description="Retourne la série complète 2018-2024 pour un secteur ISIC4 et un pays donnés.",
)
def get_isic4_timeseries_data(
    country_iso3: str = Path(..., description="Code ISO3"),
    isic4_code: str = Path(..., description="Code ISIC 4 chiffres (ex: 1010, 2411)"),
):
    """
    GET /api/production/isic4/{country_iso3}/{isic4_code}

    Retourne tous les indicateurs (output, imports, exports, etc.) année par année
    pour faciliter les graphiques de tendance.
    """
    if not is_country_covered(country_iso3.upper()):
        raise HTTPException(status_code=404, detail=f"Pays {country_iso3} non couvert")

    timeseries = get_isic4_timeseries(country_iso3.upper(), isic4_code)
    if not timeseries:
        raise HTTPException(
            status_code=404,
            detail=f"Pas de données pour ISIC {isic4_code} en {country_iso3}",
        )
    return timeseries


# ═══════════════════════════════════════════════════════════════════════════════
# CAPACITÉ DE PRODUCTION ENDPOINTS (FAO/USGS/UNIDO)
# ═══════════════════════════════════════════════════════════════════════════════

if HAS_CAPACITY_SERVICE:
    @router.get(
        "/capacity",
        summary="Capacité de production — code HS + pays",
        description="Retourne capacité réelle, classement continental, part africaine, "
        "et scénarios d'intégration ZLECAf pour un code HS et un pays.",
    )
    def get_production_capacity(
        country_iso3: str = Query(..., description="Code ISO3 du pays"),
        hs_code: str = Query(..., description="Code HS (ex: 0901, 080390)"),
    ):
        """
        GET /api/production/capacity?country_iso3=ETH&hs_code=0901

        Retourne :
        - Capacité réelle du pays (dernière année)
        - CAGR 2021-2024
        - Classement continental & part africaine
        - Top 5 producteurs
        - Scénarios : conservateur / ZLECAf / transformation locale
        - Caveats de couverture & commodité
        """
        return get_capacity(country_iso3, hs_code)

    @router.get(
        "/country-profile/{country_iso3}",
        summary="Profil pays — tous produits avec capacité de production",
        description="Retourne tous les produits que le pays produit réellement selon "
        "FAO/USGS/UNIDO, trié par part africaine décroissante.",
    )
    def get_country_production_profile(
        country_iso3: str = Path(..., description="Code ISO3"),
        top_n: int = Query(20, ge=1, le=100, description="Nombre de top produits à retourner (1-100)"),
    ):
        """GET /api/production/country-profile/ETH?top_n=20"""
        return get_country_profile(country_iso3, top_n)

    @router.get(
        "/continental-producers/{hs_code}",
        summary="Top producteurs africains — par code HS",
        description="Retourne les 10 principaux producteurs africains pour une commodité donnée.",
    )
    def get_continental_producers_data(
        hs_code: str = Path(..., description="Code HS (ex: 0901)"),
    ):
        """GET /api/production/continental-producers/0901"""
        return get_continental_producers(hs_code)

    @router.get(
        "/tracked-products",
        summary="Univers de produits traçables — 330+ codes HS",
        description="Retourne tous les codes HS mappés avec données FAO/USGS/UNIDO réelles.",
    )
    def list_tracked_products_data():
        """
        GET /api/production/tracked-products

        Retourne [
            {"hs_code": "0901", "dataset": "agri", "commodity": "Coffee"},
            ...
        ]
        """
        return {
            "products": list_tracked_products(),
            "total": len(list_tracked_products()),
            "sources": [
                "FAO FAOSTAT (agriculture)",
                "UNIDO INDSTAT4 (manufacturier)",
                "USGS/EIA/OPEC (mines & hydrocarbures)",
            ],
        }
else:
    # Capacity service not available - return 503
    @router.get("/capacity")
    @router.get("/country-profile/{country_iso3}")
    @router.get("/continental-producers/{hs_code}")
    @router.get("/tracked-products")
    def capacity_service_unavailable():
        raise HTTPException(
            status_code=503,
            detail="Production capacity service not available (missing data files)",
        )

# ---------------------------------------------------------------------------
# Routes legacy restaurées (fe425a8f) — Macro / Agriculture / Manufacturing /
# Mining / Overview / UNIDO INDSTAT. Perdues lors du merge du 05/09 (la branche
# conflict/PR #445 ne les contenait pas). Prefix: /api/production (voir router
# ci-dessus — l'ancien fichier utilisait /production monté sous /api).
# ---------------------------------------------------------------------------
from production_data import (
    get_agriculture_by_country,
    get_agriculture_production,
    get_agriculture_projections,
    get_country_production_overview,
    get_manufacturing_by_country,
    get_manufacturing_production,
)
from production_data import get_mining_by_country as get_mining_by_country_data
from production_data import (
    get_mining_production,
    get_production_statistics,
    get_value_added,
    get_value_added_by_country,
)
from services import manufacturing_proxy_service, production_capacity_service

try:
    from etl.unido_data import UNIDO_INDUSTRY_DATA
except ImportError:
    UNIDO_INDUSTRY_DATA = {}



@router.get("/statistics")
async def get_production_stats():
    """
    Get global production statistics for all African countries
    Returns overview of data coverage across 4 dimensions
    """
    return get_production_statistics()


@router.get("/macro")
async def get_macro_value_added(
    country_iso3: Optional[str] = None, year: Optional[int] = None, sector: Optional[str] = None
):
    """
    Get macro-level value added data (World Bank/IMF)

    Query parameters:
    - country_iso3: ISO3 country code (e.g., 'ZAF')
    - year: Year (2021-2024)
    - sector: ISIC section ('A', 'B-F', 'C')
    """
    return get_value_added(country_iso3=country_iso3, year=year, sector=sector)


@router.get("/macro/{country_iso3}")
async def get_macro_by_country(country_iso3: str):
    """
    Get all macro value added series for a specific country
    Organized by sector with time series
    """
    return get_value_added_by_country(country_iso3)


@router.get("/agriculture")
async def get_agri_production(
    country_iso3: Optional[str] = None, year: Optional[int] = None, commodity: Optional[str] = None
):
    """
    Get agricultural production data (FAOSTAT)

    Query parameters:
    - country_iso3: ISO3 country code
    - year: Year (2021-2024)
    - commodity: Commodity name or code (e.g., 'Maize', '0015')
    """
    return get_agriculture_production(country_iso3=country_iso3, year=year, commodity=commodity)


@router.get("/agriculture/projections")
async def get_agri_projections(
    country_iso3: Optional[str] = None, year: Optional[int] = None, commodity: Optional[str] = None
):
    """
    Get agricultural production PROJECTIONS (OECD-FAO Agricultural Outlook).

    Query parameters:
    - country_iso3: ISO3 country code
    - year: Projection horizon (2025, 2030)
    - commodity: Aggregate name (e.g., 'Cereals')
    """
    return get_agriculture_projections(country_iso3=country_iso3, year=year, commodity=commodity)


@router.get("/agriculture/{country_iso3}")
async def get_agri_by_country(country_iso3: str):
    """
    Get all agricultural production for a specific country
    Organized by commodity with time series
    """
    return get_agriculture_by_country(country_iso3)


@router.get("/manufacturing")
async def get_manuf_production(
    country_iso3: Optional[str] = None, year: Optional[int] = None, isic_code: Optional[str] = None
):
    """
    Get manufacturing production data (UNIDO)

    Query parameters:
    - country_iso3: ISO3 country code
    - year: Year (2021-2024)
    - isic_code: ISIC Rev.4 code (e.g., '10', '11')
    """
    return get_manufacturing_production(country_iso3=country_iso3, year=year, isic_code=isic_code)


@router.get("/manufacturing/{country_iso3}")
async def get_manuf_by_country(country_iso3: str):
    """
    Get all manufacturing production for a specific country
    Organized by ISIC sector with time series
    """
    return get_manufacturing_by_country(country_iso3)


@router.get("/mining")
async def get_mining_prod(
    country_iso3: Optional[str] = None, year: Optional[int] = None, commodity: Optional[str] = None
):
    """
    Get mining production data (USGS)

    Query parameters:
    - country_iso3: ISO3 country code
    - year: Year (2021-2024)
    - commodity: Mineral name or code (e.g., 'Gold', 'AU')
    """
    return get_mining_production(country_iso3=country_iso3, year=year, commodity=commodity)


@router.get("/mining/{country_iso3}")
async def get_mining_by_country(country_iso3: str):
    """
    Get all mining production for a specific country
    Organized by commodity with time series
    """
    return get_mining_by_country_data(country_iso3)


@router.get("/overview/{country_iso3}")
async def get_country_production_full_overview(country_iso3: str):
    """
    Get complete production overview for a country
    Includes all 4 dimensions: macro, agriculture, manufacturing, mining
    """
    return get_country_production_overview(country_iso3)


# =============================================================================
# CAPACITÉ DE PRODUCTION ↔ OPPORTUNITÉS (croisement par code HS)
# Relie un produit (HS) aux données de production réelles FAO/USGS/UNIDO
# et génère des scénarios d'intégration africaine.
# =============================================================================


@router.get("/capacity/{country_iso3}/{hs_code}")
async def get_production_capacity(country_iso3: str, hs_code: str):
    """
    Capacité de production réelle d'un pays pour un produit (code HS).

    Retourne : commodité associée, série 2021-2024, CAGR, rang continental,
    part africaine, top producteurs et scénarios d'intégration ZLECAf.
    Sources : FAO (FAOSTAT), USGS (MCS), UNIDO (INDSTAT4).
    """
    return production_capacity_service.get_capacity(country_iso3, hs_code)


@router.get("/capacity/{hs_code}")
async def get_continental_capacity(hs_code: str):
    """
    Vue continentale : top producteurs africains réels pour un code HS
    (dernière année disponible). Utilisé par la recherche HS6 des chaînes de valeur.
    """
    return production_capacity_service.get_continental_producers(hs_code)


# =============================================================================
# SIGNAL D'ASSEMBLAGE PAR PROXY D'INTRANTS (biens d'équipement non couverts
# par FAOSTAT/USGS/UNIDO — ex. réfrigérateurs, climatiseurs, téléviseurs).
# Voir services/manufacturing_proxy_service.py pour la méthodologie et les
# garde-fous anti-fabrication.
# =============================================================================


@router.get("/assembly-signal/chapters")
async def list_assembly_signal_chapters():
    """Codes HS couverts par le signal d'assemblage (proxy d'intrants)."""
    return {"chapters": manufacturing_proxy_service.list_proxy_chapters()}


@router.get("/assembly-signal/{country_iso3}/{hs_code}")
async def get_assembly_signal(country_iso3: str, hs_code: str):
    """
    Signal INDIRECT d'assemblage local pour un produit fini non mesuré par
    FAOSTAT/USGS/UNIDO (ex. réfrigérateurs HS 8418, téléviseurs HS 8528),
    dérivé des importations réelles (OEC/UN Comtrade) de son composant-clé
    (ex. compresseurs, modules d'affichage). Ce n'est PAS une production
    mesurée — voir le champ "methodology" de la réponse.
    """
    return await manufacturing_proxy_service.estimate_assembly_signal(country_iso3, hs_code)


# =============================================================================
# UNIDO INDSTAT4 - Routes spécifiques UNIDO
# Source: UNIDO INDUSTRY_DATA (54 pays africains)
# =============================================================================


@router.get("/unido/statistics")
async def get_unido_statistics():
    """
    Statistiques globales UNIDO - Valeur Ajoutée Manufacturière africaine
    Retourne: MVA total, nb pays, top secteurs, etc.
    """
    if not UNIDO_INDUSTRY_DATA:
        return {"error": "UNIDO data not available", "total_countries": 0}

    total_mva = sum(d.get("mva_2023_mln_usd", 0) for d in UNIDO_INDUSTRY_DATA.values())
    total_employment = sum(d.get("industry_employment", 0) for d in UNIDO_INDUSTRY_DATA.values())
    total_exports = sum(d.get("exports_manuf_mln_usd", 0) for d in UNIDO_INDUSTRY_DATA.values())

    return {
        "total_countries": len(UNIDO_INDUSTRY_DATA),
        "total_mva_mln_usd": round(total_mva, 1),
        "total_mva_bln_usd": round(total_mva / 1000, 1),
        "total_employment": total_employment,
        "total_exports_manuf_mln_usd": round(total_exports, 1),
        "source": "UNIDO INDSTAT4 2024 — International Yearbook of Industrial Statistics",
        "data_year": 2023,
        "coverage": "54 pays membres AfCFTA",
        "classification": "ISIC Rev.4",
    }


@router.get("/unido/ranking")
async def get_unido_ranking():
    """
    Classement africain par Valeur Ajoutée Manufacturière (MVA 2023)
    """
    if not UNIDO_INDUSTRY_DATA:
        return {"ranking": []}

    ranking = []
    for iso3, data in UNIDO_INDUSTRY_DATA.items():
        ranking.append(
            {
                "country_iso3": iso3,
                "country_name": data.get("country_name", iso3),
                "region": data.get("region", ""),
                "mva_2023_mln_usd": data.get("mva_2023_mln_usd", 0),
                "mva_gdp_percent": data.get("mva_gdp_percent", 0),
                "mva_per_capita_usd": data.get("mva_per_capita_usd", 0),
                "growth_rate_2023": data.get("growth_rate_2023", 0),
                "cip_index_rank": data.get("cip_index_rank"),
            }
        )

    ranking.sort(key=lambda x: x["mva_2023_mln_usd"], reverse=True)

    return {
        "ranking": ranking,
        "total": len(ranking),
        "source": "UNIDO INDSTAT4 2024",
        "data_year": 2023,
    }


@router.get("/unido/isic4/{country_iso3}")
async def get_unido_isic4_breakdown(country_iso3: str):
    """
    Désagrégation ISIC Rev.4 4 chiffres (classe) des principaux secteurs
    manufacturiers (top_sectors) d'un pays, à partir des données UNIDO
    INDSTAT4 (division, 2 chiffres) et de la nomenclature officielle UNSD
    ISIC Rev.4. Ne couvre PAS l'ensemble des divisions manufacturières du
    pays — voir les champs "coverage" et "methodology" de la réponse.
    """
    from etl.unido_data import get_isic4_breakdown

    breakdown = get_isic4_breakdown(country_iso3)
    if breakdown is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune donnée UNIDO disponible pour {country_iso3.upper()}",
        )
    return breakdown


@router.get("/unido/isic4-classification")
async def get_isic4_classification():
    """Table de référence ISIC Rev.4 4 chiffres (classes) par division manufacturière."""
    from etl.isic4_classification import ISIC4_CLASSES

    return {
        "classification": "ISIC Rev.4",
        "source": "UNSD - International Standard Industrial Classification Rev.4",
        "divisions": ISIC4_CLASSES,
    }


# =============================================================================
# Correspondance ISIC Rev.4 (4 chiffres) <-> SH6 HS 2022 (utilisée par OEC)
# Chaînage officiel WCO Table I + UNSD SH2017<->CPC2.1 + UNSD CPC2.1<->ISIC4
# Voir backend/etl/isic4_hs6_correspondence.py
# =============================================================================


@router.get("/isic4-hs6/coverage")
async def get_isic4_hs6_coverage():
    """Statistiques de couverture de la correspondance SH6 (HS 2022) <-> ISIC4."""
    from etl.isic4_hs6_correspondence import coverage_stats

    return coverage_stats()


@router.get("/isic4-hs6/isic4/{isic4_code}")
async def get_hs6_for_isic4(isic4_code: str):
    """Liste des codes SH6 (HS 2022) correspondant à une classe ISIC Rev.4 4 chiffres."""
    from etl.isic4_hs6_correspondence import hs6_for_isic4

    hs6_codes = hs6_for_isic4(isic4_code)
    if not hs6_codes:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun code SH6 mappé à ISIC {isic4_code}",
        )
    return {"isic4": isic4_code, "hs6_codes": hs6_codes, "total": len(hs6_codes)}


@router.get("/isic4-hs6/hs6/{hs6_code}")
async def get_isic4_for_hs6(hs6_code: str):
    """Liste des classes ISIC Rev.4 4 chiffres correspondant à un code SH6 (HS 2022)."""
    from etl.isic4_hs6_correspondence import isic4_for_hs6

    isic4_codes = isic4_for_hs6(hs6_code)
    if not isic4_codes:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune classe ISIC4 mappée au SH6 {hs6_code}",
        )
    return {"hs6": hs6_code, "isic4_codes": isic4_codes, "total": len(isic4_codes)}


@router.get("/unido/{country_iso3}")
async def get_unido_country_data(country_iso3: str):
    """
    Données UNIDO complètes pour un pays africain
    - MVA, secteurs ISIC, emplois, exportations, produits clés
    """
    iso3_upper = country_iso3.upper()

    if iso3_upper not in UNIDO_INDUSTRY_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune donnée UNIDO disponible pour {iso3_upper}. Pays couverts: {len(UNIDO_INDUSTRY_DATA)}",
        )

    data = UNIDO_INDUSTRY_DATA[iso3_upper].copy()
    data["country_iso3"] = iso3_upper
    return data
