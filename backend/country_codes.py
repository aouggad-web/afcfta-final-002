"""
Mapping centralisé des codes pays ISO pour l'Afrique
Standard: ISO 3166-1 (ISO3 comme référence principale)

Ce fichier centralise tous les codes pays utilisés dans l'application
pour assurer la cohérence des données.

Utilisation:
- ISO3 est le standard principal (3 lettres: NGA, CMR, ZAF...)
- ISO2 est fourni pour compatibilité (2 lettres: NG, CM, ZA...)
- Les noms FR et EN sont inclus pour l'affichage

Dernière mise à jour: Janvier 2025
"""

from typing import Dict, Optional, List

# =============================================================================
# MAPPING COMPLET DES 55 PAYS AFRICAINS (incluant la RASD)
# =============================================================================

AFRICAN_COUNTRIES = {
    # Code ISO3 -> Détails complets
    "DZA": {"iso2": "DZ", "name_fr": "Algérie", "name_en": "Algeria", "region": "North Africa"},
    "AGO": {"iso2": "AO", "name_fr": "Angola", "name_en": "Angola", "region": "Southern Africa"},
    "BEN": {"iso2": "BJ", "name_fr": "Bénin", "name_en": "Benin", "region": "West Africa"},
    "BWA": {"iso2": "BW", "name_fr": "Botswana", "name_en": "Botswana", "region": "Southern Africa"},
    "BFA": {"iso2": "BF", "name_fr": "Burkina Faso", "name_en": "Burkina Faso", "region": "West Africa"},
    "BDI": {"iso2": "BI", "name_fr": "Burundi", "name_en": "Burundi", "region": "East Africa"},
    "CPV": {"iso2": "CV", "name_fr": "Cap-Vert", "name_en": "Cape Verde", "region": "West Africa"},
    "CMR": {"iso2": "CM", "name_fr": "Cameroun", "name_en": "Cameroon", "region": "Central Africa"},
    "CAF": {"iso2": "CF", "name_fr": "République Centrafricaine", "name_en": "Central African Republic", "region": "Central Africa"},
    "TCD": {"iso2": "TD", "name_fr": "Tchad", "name_en": "Chad", "region": "Central Africa"},
    "COM": {"iso2": "KM", "name_fr": "Comores", "name_en": "Comoros", "region": "East Africa"},
    "COG": {"iso2": "CG", "name_fr": "République du Congo", "name_en": "Republic of the Congo", "region": "Central Africa"},
    "COD": {"iso2": "CD", "name_fr": "République Démocratique du Congo", "name_en": "Democratic Republic of the Congo", "region": "Central Africa"},
    "CIV": {"iso2": "CI", "name_fr": "Côte d'Ivoire", "name_en": "Ivory Coast", "region": "West Africa"},
    "DJI": {"iso2": "DJ", "name_fr": "Djibouti", "name_en": "Djibouti", "region": "East Africa"},
    "EGY": {"iso2": "EG", "name_fr": "Égypte", "name_en": "Egypt", "region": "North Africa"},
    "GNQ": {"iso2": "GQ", "name_fr": "Guinée Équatoriale", "name_en": "Equatorial Guinea", "region": "Central Africa"},
    "ERI": {"iso2": "ER", "name_fr": "Érythrée", "name_en": "Eritrea", "region": "East Africa"},
    "SWZ": {"iso2": "SZ", "name_fr": "Eswatini", "name_en": "Eswatini", "region": "Southern Africa"},
    "ETH": {"iso2": "ET", "name_fr": "Éthiopie", "name_en": "Ethiopia", "region": "East Africa"},
    "GAB": {"iso2": "GA", "name_fr": "Gabon", "name_en": "Gabon", "region": "Central Africa"},
    "GMB": {"iso2": "GM", "name_fr": "Gambie", "name_en": "Gambia", "region": "West Africa"},
    "GHA": {"iso2": "GH", "name_fr": "Ghana", "name_en": "Ghana", "region": "West Africa"},
    "GIN": {"iso2": "GN", "name_fr": "Guinée", "name_en": "Guinea", "region": "West Africa"},
    "GNB": {"iso2": "GW", "name_fr": "Guinée-Bissau", "name_en": "Guinea-Bissau", "region": "West Africa"},
    "KEN": {"iso2": "KE", "name_fr": "Kenya", "name_en": "Kenya", "region": "East Africa"},
    "LSO": {"iso2": "LS", "name_fr": "Lesotho", "name_en": "Lesotho", "region": "Southern Africa"},
    "LBR": {"iso2": "LR", "name_fr": "Libéria", "name_en": "Liberia", "region": "West Africa"},
    "LBY": {"iso2": "LY", "name_fr": "Libye", "name_en": "Libya", "region": "North Africa"},
    "MDG": {"iso2": "MG", "name_fr": "Madagascar", "name_en": "Madagascar", "region": "East Africa"},
    "MWI": {"iso2": "MW", "name_fr": "Malawi", "name_en": "Malawi", "region": "Southern Africa"},
    "MLI": {"iso2": "ML", "name_fr": "Mali", "name_en": "Mali", "region": "West Africa"},
    "MRT": {"iso2": "MR", "name_fr": "Mauritanie", "name_en": "Mauritania", "region": "West Africa"},
    "MUS": {"iso2": "MU", "name_fr": "Maurice", "name_en": "Mauritius", "region": "East Africa"},
    "MAR": {"iso2": "MA", "name_fr": "Maroc", "name_en": "Morocco", "region": "North Africa"},
    "MOZ": {"iso2": "MZ", "name_fr": "Mozambique", "name_en": "Mozambique", "region": "Southern Africa"},
    "NAM": {"iso2": "NA", "name_fr": "Namibie", "name_en": "Namibia", "region": "Southern Africa"},
    "NER": {"iso2": "NE", "name_fr": "Niger", "name_en": "Niger", "region": "West Africa"},
    "NGA": {"iso2": "NG", "name_fr": "Nigéria", "name_en": "Nigeria", "region": "West Africa"},
    "RWA": {"iso2": "RW", "name_fr": "Rwanda", "name_en": "Rwanda", "region": "East Africa"},
    # RASD - République Arabe Sahraouie Démocratique (Sahara Occidental)
    # Membre fondateur de l'Union Africaine (UA) depuis 1984
    # ATTENTION: Territoire occupé - AUCUNE STATISTIQUE COMMERCIALE DISPONIBLE
    "ESH": {"iso2": "EH", "name_fr": "RASD (Sahara Occidental)", "name_en": "Sahrawi Arab Democratic Republic", "region": "North Africa", "has_trade_data": False, "note": "Territoire occupé - pas de données commerciales"},
    "STP": {"iso2": "ST", "name_fr": "São Tomé-et-Príncipe", "name_en": "São Tomé and Príncipe", "region": "Central Africa"},
    "SEN": {"iso2": "SN", "name_fr": "Sénégal", "name_en": "Senegal", "region": "West Africa"},
    "SYC": {"iso2": "SC", "name_fr": "Seychelles", "name_en": "Seychelles", "region": "East Africa"},
    "SLE": {"iso2": "SL", "name_fr": "Sierra Leone", "name_en": "Sierra Leone", "region": "West Africa"},
    "SOM": {"iso2": "SO", "name_fr": "Somalie", "name_en": "Somalia", "region": "East Africa"},
    "ZAF": {"iso2": "ZA", "name_fr": "Afrique du Sud", "name_en": "South Africa", "region": "Southern Africa"},
    "SSD": {"iso2": "SS", "name_fr": "Soudan du Sud", "name_en": "South Sudan", "region": "East Africa"},
    "SDN": {"iso2": "SD", "name_fr": "Soudan", "name_en": "Sudan", "region": "North Africa"},
    "TZA": {"iso2": "TZ", "name_fr": "Tanzanie", "name_en": "Tanzania", "region": "East Africa"},
    "TGO": {"iso2": "TG", "name_fr": "Togo", "name_en": "Togo", "region": "West Africa"},
    "TUN": {"iso2": "TN", "name_fr": "Tunisie", "name_en": "Tunisia", "region": "North Africa"},
    "UGA": {"iso2": "UG", "name_fr": "Ouganda", "name_en": "Uganda", "region": "East Africa"},
    "ZMB": {"iso2": "ZM", "name_fr": "Zambie", "name_en": "Zambia", "region": "Southern Africa"},
    "ZWE": {"iso2": "ZW", "name_fr": "Zimbabwe", "name_en": "Zimbabwe", "region": "Southern Africa"},
}

# =============================================================================
# MAPPINGS INVERSÉS POUR CONVERSIONS RAPIDES
# =============================================================================

# ISO2 -> ISO3
ISO2_TO_ISO3 = {info["iso2"]: iso3 for iso3, info in AFRICAN_COUNTRIES.items()}

# ISO3 -> ISO2
ISO3_TO_ISO2 = {iso3: info["iso2"] for iso3, info in AFRICAN_COUNTRIES.items()}

# Nom FR -> ISO3 (normalisé en minuscules sans accents)
def _normalize(text: str) -> str:
    """Normalise un texte pour la recherche"""
    import unicodedata
    text = unicodedata.normalize('NFD', text.lower())
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

NAME_FR_TO_ISO3 = {_normalize(info["name_fr"]): iso3 for iso3, info in AFRICAN_COUNTRIES.items()}
NAME_EN_TO_ISO3 = {info["name_en"].lower(): iso3 for iso3, info in AFRICAN_COUNTRIES.items()}

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_iso3_from_iso2(iso2: str) -> Optional[str]:
    """Convertit un code ISO2 en ISO3"""
    return ISO2_TO_ISO3.get(iso2.upper())

def get_iso2_from_iso3(iso3: str) -> Optional[str]:
    """Convertit un code ISO3 en ISO2"""
    return ISO3_TO_ISO2.get(iso3.upper())

def get_country_info(code: str) -> Optional[Dict]:
    """
    Récupère les informations d'un pays à partir de son code (ISO2 ou ISO3)
    """
    code = code.upper()
    
    # Essayer ISO3 d'abord
    if code in AFRICAN_COUNTRIES:
        return {"iso3": code, **AFRICAN_COUNTRIES[code]}
    
    # Essayer ISO2
    iso3 = ISO2_TO_ISO3.get(code)
    if iso3:
        return {"iso3": iso3, **AFRICAN_COUNTRIES[iso3]}
    
    return None

def get_country_by_name(name: str, lang: str = "fr") -> Optional[Dict]:
    """
    Récupère les informations d'un pays à partir de son nom
    
    Args:
        name: Nom du pays (FR ou EN)
        lang: Langue préférée ("fr" ou "en")
    """
    normalized = _normalize(name)
    
    # Chercher dans les noms FR
    if normalized in NAME_FR_TO_ISO3:
        iso3 = NAME_FR_TO_ISO3[normalized]
        return {"iso3": iso3, **AFRICAN_COUNTRIES[iso3]}
    
    # Chercher dans les noms EN
    if name.lower() in NAME_EN_TO_ISO3:
        iso3 = NAME_EN_TO_ISO3[name.lower()]
        return {"iso3": iso3, **AFRICAN_COUNTRIES[iso3]}
    
    return None

def get_all_countries(lang: str = "fr") -> List[Dict]:
    """
    Retourne la liste de tous les pays africains
    
    Args:
        lang: Langue pour le tri ("fr" ou "en")
    """
    name_key = f"name_{lang}"
    return [
        {"iso3": iso3, "iso2": info["iso2"], "name": info.get(name_key, info["name_en"]), **info}
        for iso3, info in sorted(AFRICAN_COUNTRIES.items(), key=lambda x: x[1].get(name_key, ""))
    ]

def get_countries_by_region(region: str, lang: str = "fr") -> List[Dict]:
    """
    Retourne les pays d'une région spécifique
    
    Args:
        region: "North Africa", "West Africa", "Central Africa", "East Africa", "Southern Africa"
        lang: Langue pour le tri
    """
    name_key = f"name_{lang}"
    return [
        {"iso3": iso3, **info}
        for iso3, info in sorted(AFRICAN_COUNTRIES.items(), key=lambda x: x[1].get(name_key, ""))
        if info["region"] == region
    ]

# =============================================================================
# RÉGIONS ÉCONOMIQUES
# =============================================================================

ECONOMIC_COMMUNITIES = {
    "UEMOA": ["BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"],
    "CEMAC": ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"],
    "CEDEAO": ["BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO"],
    "EAC": ["BDI", "COD", "KEN", "RWA", "SSD", "TZA", "UGA"],
    "SACU": ["BWA", "LSO", "NAM", "ZAF", "SWZ"],
    "SADC": ["AGO", "BWA", "COM", "COD", "SWZ", "LSO", "MDG", "MWI", "MUS", "MOZ", "NAM", "SYC", "ZAF", "TZA", "ZMB", "ZWE"],
    "UMA": ["DZA", "LBY", "MRT", "MAR", "TUN"],
    "IGAD": ["DJI", "ERI", "ETH", "KEN", "SOM", "SSD", "SDN", "UGA"],
    "COMESA": ["BDI", "COM", "COD", "DJI", "EGY", "ERI", "SWZ", "ETH", "KEN", "LBY", "MDG", "MWI", "MUS", "RWA", "SYC", "SOM", "SDN", "TUN", "UGA", "ZMB", "ZWE"],
}

def get_community_members(community: str) -> List[str]:
    """Retourne les codes ISO3 des membres d'une communauté économique"""
    return ECONOMIC_COMMUNITIES.get(community.upper(), [])
