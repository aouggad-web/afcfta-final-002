"""
Réseau ZLECAf — statut de mise en œuvre par État et liaisons préférentielles,
pour la carte « Réseau ZLECAf » (onglet Statistiques).
"""

from fastapi import APIRouter
from services.zlecaf_network import construire_reseau
from translations import translate_country_name

router = APIRouter()

# Entités sans entrée dans translations.COUNTRY_TRANSLATIONS (qui renvoie
# alors le code ISO2 lui-même).
NOMS_HORS_TABLE = {"EH": {"fr": "RASD (Sahara occidental)", "en": "SADR (Western Sahara)"}}


@router.get("/zlecaf/network")
async def get_zlecaf_network(lang: str = "fr"):
    """Statut ZLECAf de chaque État, preuves sourcées, PIB et liaisons.

    Chaque statut est dérivé des modules qui servent le moteur de calcul
    (adhésion, registre de mise en œuvre, listes algérienne et sud-africaine) ;
    voir ``services/zlecaf_network.py``.
    """
    reseau = construire_reseau(lang=lang)
    for pays in reseau["pays"]:
        nom_constants = pays.pop("nom_constants")
        traduit = translate_country_name(pays["iso2"], lang)
        if traduit and traduit != pays["iso2"]:
            pays["nom"] = traduit
        else:
            hors_table = NOMS_HORS_TABLE.get(pays["iso2"], {})
            pays["nom"] = hors_table.get("en" if lang == "en" else "fr", nom_constants)
    return reseau
