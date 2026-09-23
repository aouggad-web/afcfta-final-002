"""
Industrie nationale et marchés d'export — module Opportunités
=============================================================
Industrie par branche d'après l'office statistique national, exportations par
produit et demande mondiale d'après CEPII BACI. Un pays non couvert renvoie
``available: False`` ; chaque valeur porte sa nature (officiel, calcul
officiel, estimation). Voir ``services/industrie_nationale_service.py``.
"""

from fastapi import APIRouter, Query
from services import industrie_nationale_service as ins

router = APIRouter(prefix="/industrie-nationale", tags=["Industrie nationale"])


@router.get("/pays")
async def pays_couverts():
    """Pays dont les séries nationales sont intégrées."""
    return {"pays": ins.pays_couverts()}


@router.get("/{country_iso3}")
async def industrie_par_branche(
    country_iso3: str,
    lang: str = Query(default="fr", description="Langue des libellés (fr/en)"),
):
    """Industrie manufacturière par branche : officiel, calcul officiel, estimation 2025."""
    return ins.industrie(country_iso3, lang)


@router.get("/{country_iso3}/exportations")
async def exportations_par_produit(
    country_iso3: str,
    lang: str = Query(default="fr", description="Langue des libellés (fr/en)"),
    region: str = Query(
        default="monde", pattern="^(monde|afrique)$", description="Tri : monde ou Afrique"
    ),
    limite: int = Query(default=30, ge=1, le=400),
    hors_hydrocarbures: bool = Query(
        default=False, description="Écarter le chapitre 27 (définition ONS « hors hydrocarbures »)"
    ),
):
    """Produits exportés en 2024, avec la demande mondiale et africaine (BACI)."""
    return ins.exportations(country_iso3, lang, region, limite, hors_hydrocarbures)


@router.get("/{country_iso3}/exportations/{hs6}")
async def fiche_exportation(
    country_iso3: str,
    hs6: str,
    lang: str = Query(default="fr", description="Langue des libellés (fr/en)"),
    seuil_import_usd: float = Query(default=ins.SEUIL_IMPORT_USD, ge=0),
    seuil_part_pct: float = Query(default=ins.SEUIL_PART_PCT, ge=0, le=100),
):
    """Exportations d'un produit 2016-2024, destinations, importateurs et marchés où le pays est absent."""
    return ins.fiche_produit(country_iso3, hs6, lang, seuil_import_usd, seuil_part_pct)
