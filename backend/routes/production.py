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
    Inclut par défaut les pays avec données officielles ET estimées.
    """
    countries = list_covered_countries()
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
