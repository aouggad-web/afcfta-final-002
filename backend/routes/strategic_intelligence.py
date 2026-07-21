"""
Strategic Trade Intelligence Routes
===================================

Expose le sous-module « flux stratégiques » : des opportunités d'export
enrichies (rationale, transformation industrielle, avantage ZLECAf, règles
d'origine, signal High Growth adossé aux projets structurants) plus une vue
agrégée (flux identifiés, potentiel total, partenaires & commodités prioritaires).

S'appuie sur les flux réels OEC (via real_substitution_service) fusionnés avec
la base d'intelligence industrielle.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from services import industrial_intelligence_service as intel
from services.real_trade_data_service import AFRICAN_COUNTRIES, get_country_name
from services.strategic_trade_service import get_strategic_flows

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategic", tags=["Strategic Trade Intelligence"])


@router.get("/flows/{country_iso3}")
async def get_country_strategic_flows(
    country_iso3: str,
    year: int = Query(default=2022, description="Année des données commerciales"),
    min_market_size: int = Query(
        default=5_000_000, description="Taille de marché minimale à considérer (USD)"
    ),
    lang: str = Query(default="fr", description="Langue des libellés (fr/en)"),
    limit: int = Query(default=30, ge=1, le=100, description="Nombre max de flux retournés"),
):
    """
    Flux stratégiques d'export pour un pays africain.

    Renvoie la vue agrégée + la liste des flux enrichis, à la manière du
    tableau de bord « Trade Potential Summary » de référence.
    """
    iso3 = country_iso3.upper()
    if iso3 not in AFRICAN_COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Pays {iso3} hors périmètre AfCFTA")

    try:
        result = await get_strategic_flows(
            iso3, year=year, min_market_size=min_market_size, lang=lang, limit=limit
        )
    except Exception:  # pragma: no cover - garde-fou runtime
        # Détail loggé côté serveur uniquement ; message générique au client
        # (ne pas exposer messages d'erreur/chemins/dépendances internes).
        logger.exception("Échec du calcul des flux stratégiques pour %s", iso3)
        raise HTTPException(status_code=502, detail="Erreur interne du moteur stratégique")

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/intelligence/{country_iso3}")
async def get_country_industrial_intelligence(
    country_iso3: str,
    lang: str = Query(default="fr", description="Langue des libellés (fr/en)"),
):
    """
    Fiche d'intelligence industrielle d'un pays : champions industriels (curés)
    et capacités futures (curées + dérivées des projets structurants), plus la
    liste des commodités prioritaires.
    """
    iso3 = country_iso3.upper()
    if iso3 not in AFRICAN_COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Pays {iso3} hors périmètre AfCFTA")

    profile = intel.get_country_intelligence(iso3)
    return {
        "country": {"iso3": iso3, "name": get_country_name(iso3, lang)},
        "has_intelligence": intel.has_intelligence(iso3),
        "is_curated": intel.is_curated(iso3),
        "champions": (profile or {}).get("champions", []),
        "future_capacity": (profile or {}).get("future_capacity", []),
        "priority_commodities": intel.priority_commodities(iso3),
    }
