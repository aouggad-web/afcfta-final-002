"""Marchés africains pour le tableau de bord de direction : cours mensuels des
matières premières (Banque mondiale) et indices des bourses africaines.

GET /api/marches/apercu
"""

from auth import get_db
from etl.marches_africains import MARCHES
from fastapi import APIRouter

router = APIRouter(prefix="/marches")


@router.get("/apercu")
async def apercu_marches():
    """Cours du dernier mois publié (avec les 12 mois précédents) et points à
    l'ouverture et à la clôture de la dernière séance de chaque bourse."""
    return await MARCHES.apercu(get_db())
