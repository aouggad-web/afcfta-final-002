"""
Translations for country names, regions and rules
"""

# Translations for country names and regions
COUNTRY_TRANSLATIONS = {
    "DZ": {"fr": "Algérie", "en": "Algeria"},
    "AO": {"fr": "Angola", "en": "Angola"},
    "BJ": {"fr": "Bénin", "en": "Benin"},
    "BW": {"fr": "Botswana", "en": "Botswana"},
    "BF": {"fr": "Burkina Faso", "en": "Burkina Faso"},
    "BI": {"fr": "Burundi", "en": "Burundi"},
    "CM": {"fr": "Cameroun", "en": "Cameroon"},
    "CV": {"fr": "Cap-Vert", "en": "Cape Verde"},
    "CF": {"fr": "République Centrafricaine", "en": "Central African Republic"},
    "TD": {"fr": "Tchad", "en": "Chad"},
    "KM": {"fr": "Comores", "en": "Comoros"},
    "CG": {"fr": "République du Congo", "en": "Republic of Congo"},
    "CD": {"fr": "République Démocratique du Congo", "en": "Democratic Republic of Congo"},
    "CI": {"fr": "Côte d'Ivoire", "en": "Ivory Coast"},
    "DJ": {"fr": "Djibouti", "en": "Djibouti"},
    "EG": {"fr": "Égypte", "en": "Egypt"},
    "GQ": {"fr": "Guinée Équatoriale", "en": "Equatorial Guinea"},
    "ER": {"fr": "Érythrée", "en": "Eritrea"},
    "SZ": {"fr": "Eswatini", "en": "Eswatini"},
    "ET": {"fr": "Éthiopie", "en": "Ethiopia"},
    "GA": {"fr": "Gabon", "en": "Gabon"},
    "GM": {"fr": "Gambie", "en": "Gambia"},
    "GH": {"fr": "Ghana", "en": "Ghana"},
    "GN": {"fr": "Guinée", "en": "Guinea"},
    "GW": {"fr": "Guinée-Bissau", "en": "Guinea-Bissau"},
    "KE": {"fr": "Kenya", "en": "Kenya"},
    "LS": {"fr": "Lesotho", "en": "Lesotho"},
    "LR": {"fr": "Libéria", "en": "Liberia"},
    "LY": {"fr": "Libye", "en": "Libya"},
    "MG": {"fr": "Madagascar", "en": "Madagascar"},
    "MW": {"fr": "Malawi", "en": "Malawi"},
    "ML": {"fr": "Mali", "en": "Mali"},
    "MR": {"fr": "Mauritanie", "en": "Mauritania"},
    "MU": {"fr": "Maurice", "en": "Mauritius"},
    "MA": {"fr": "Maroc", "en": "Morocco"},
    "MZ": {"fr": "Mozambique", "en": "Mozambique"},
    "NA": {"fr": "Namibie", "en": "Namibia"},
    "NE": {"fr": "Niger", "en": "Niger"},
    "NG": {"fr": "Nigéria", "en": "Nigeria"},
    "RW": {"fr": "Rwanda", "en": "Rwanda"},
    "ST": {"fr": "São Tomé-et-Príncipe", "en": "São Tomé and Príncipe"},
    "SN": {"fr": "Sénégal", "en": "Senegal"},
    "SC": {"fr": "Seychelles", "en": "Seychelles"},
    "SL": {"fr": "Sierra Leone", "en": "Sierra Leone"},
    "SO": {"fr": "Somalie", "en": "Somalia"},
    "ZA": {"fr": "Afrique du Sud", "en": "South Africa"},
    "SS": {"fr": "Soudan du Sud", "en": "South Sudan"},
    "SD": {"fr": "Soudan", "en": "Sudan"},
    "TZ": {"fr": "Tanzanie", "en": "Tanzania"},
    "TG": {"fr": "Togo", "en": "Togo"},
    "TN": {"fr": "Tunisie", "en": "Tunisia"},
    "UG": {"fr": "Ouganda", "en": "Uganda"},
    "ZM": {"fr": "Zambie", "en": "Zambia"},
    "ZW": {"fr": "Zimbabwe", "en": "Zimbabwe"}
}

REGION_TRANSLATIONS = {
    "Afrique du Nord": {"fr": "Afrique du Nord", "en": "North Africa"},
    "Afrique de l'Ouest": {"fr": "Afrique de l'Ouest", "en": "West Africa"},
    "Afrique de l'Est": {"fr": "Afrique de l'Est", "en": "East Africa"},
    "Afrique Centrale": {"fr": "Afrique Centrale", "en": "Central Africa"},
    "Afrique Australe": {"fr": "Afrique Australe", "en": "Southern Africa"}
}

RULES_TRANSLATIONS = {
    "Entièrement obtenus": {"fr": "Entièrement obtenus", "en": "Wholly obtained"},
    "Transformation substantielle": {"fr": "Transformation substantielle", "en": "Substantial transformation"},
    "Extraction ou transformation substantielle": {"fr": "Extraction ou transformation substantielle", "en": "Extraction or substantial transformation"},
    "Extraction": {"fr": "Extraction", "en": "Extraction"},
    "100% africain": {"fr": "100% africain", "en": "100% African"},
    "40% valeur ajoutée africaine": {"fr": "40% valeur ajoutée africaine", "en": "40% African value added"},
    "35% valeur ajoutée africaine": {"fr": "35% valeur ajoutée africaine", "en": "35% African value added"},
    "45% valeur ajoutée africaine": {"fr": "45% valeur ajoutée africaine", "en": "45% African value added"},
    "Entièrement extraits en Afrique": {"fr": "Entièrement extraits en Afrique", "en": "Wholly extracted in Africa"}
}

def translate_country_name(code: str, lang: str = "fr") -> str:
    """Get translated country name"""
    if code in COUNTRY_TRANSLATIONS:
        return COUNTRY_TRANSLATIONS[code].get(lang, COUNTRY_TRANSLATIONS[code]["fr"])
    return code

def translate_region(region: str, lang: str = "fr") -> str:
    """Get translated region name"""
    if region in REGION_TRANSLATIONS:
        return REGION_TRANSLATIONS[region].get(lang, region)
    return region

def translate_rule(text: str, lang: str = "fr") -> str:
    """Get translated rule text"""
    if text in RULES_TRANSLATIONS:
        return RULES_TRANSLATIONS[text].get(lang, text)
    return text
