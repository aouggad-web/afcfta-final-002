"""
Réseau ZLECAf — statut de mise en œuvre par État et liaisons préférentielles,
pour la carte « Réseau ZLECAf » (onglet Statistiques).
"""

from fastapi import APIRouter
from services.zlecaf_network import construire_reseau
from translations import translate_country_name

router = APIRouter()


@router.get("/zlecaf/network")
async def get_zlecaf_network(lang: str = "fr"):
    """Statut ZLECAf de chaque État, preuves sourcées, PIB et liaisons.

    Chaque statut est dérivé des modules qui servent le moteur de calcul
    (adhésion, registre de mise en œuvre, listes algérienne et sud-africaine) ;
    voir ``services/zlecaf_network.py``.
    """
    reseau = construire_reseau()
    for pays in reseau["pays"]:
        nom_constants = pays.pop("nom_constants")
        traduit = translate_country_name(pays["iso2"], lang)
        # translate_country_name renvoie le code lui-même quand il n'a pas de
        # traduction (cas de la RASD, « EH ») : on retombe alors sur le nom
        # de constants.AFRICAN_COUNTRIES.
        pays["nom"] = traduit if traduit and traduit != pays["iso2"] else nom_constants
    return reseau
