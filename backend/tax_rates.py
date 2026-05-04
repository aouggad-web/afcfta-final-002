# Taux de TVA et autres taxes par pays africain
# Sources: Réglementations nationales et communautaires 2025
# Dernière mise à jour: Janvier 2025
# STANDARD: Codes ISO3 (3 lettres)

# Taux de TVA standard par pays (en pourcentage)
# Sources: PwC Tax Summaries, IMF, Administrations fiscales nationales
VAT_RATES = {
    "DZA": 19.0,   # Algérie
    "AGO": 14.0,   # Angola
    "BEN": 18.0,   # Bénin (UEMOA)
    "BWA": 14.0,   # Botswana (SACU)
    "BFA": 18.0,   # Burkina Faso (UEMOA)
    "BDI": 18.0,   # Burundi (EAC)
    "CPV": 15.0,   # Cap-Vert
    "CMR": 19.25,  # Cameroun (CEMAC) - 19.25% avec centimes additionnels
    "CAF": 19.0,   # République Centrafricaine (CEMAC)
    "TCD": 18.0,   # Tchad (CEMAC)
    "COM": 10.0,   # Comores
    "COG": 18.0,   # République du Congo (CEMAC)
    "COD": 16.0,   # République Démocratique du Congo (EAC)
    "CIV": 18.0,   # Côte d'Ivoire (UEMOA)
    "DJI": 10.0,   # Djibouti
    "EGY": 14.0,   # Égypte
    "GNQ": 15.0,   # Guinée Équatoriale (CEMAC)
    "ERI": 5.0,    # Érythrée
    "SWZ": 15.0,   # Eswatini (SACU)
    "ETH": 15.0,   # Éthiopie
    "GAB": 18.0,   # Gabon (CEMAC)
    "GMB": 15.0,   # Gambie (CEDEAO)
    "GHA": 15.0,   # Ghana (CEDEAO) - 12.5% + NHIL 2.5%
    "GIN": 18.0,   # Guinée (CEDEAO)
    "GNB": 17.0,   # Guinée-Bissau (UEMOA)
    "KEN": 16.0,   # Kenya (EAC)
    "LSO": 15.0,   # Lesotho (SACU)
    "LBR": 10.0,   # Libéria (CEDEAO)
    "LBY": 0.0,    # Libye (pas de TVA)
    "MDG": 20.0,   # Madagascar
    "MWI": 16.5,   # Malawi
    "MLI": 18.0,   # Mali (UEMOA)
    "MRT": 16.0,   # Mauritanie
    "MUS": 15.0,   # Maurice
    "MAR": 20.0,   # Maroc
    "MOZ": 17.0,   # Mozambique (16% à partir de 2025)
    "NAM": 15.0,   # Namibie (SACU)
    "NER": 19.0,   # Niger (UEMOA)
    "NGA": 7.5,    # Nigéria (CEDEAO)
    "RWA": 18.0,   # Rwanda (EAC)
    "STP": 15.0,   # São Tomé-et-Príncipe
    "SEN": 18.0,   # Sénégal (UEMOA)
    "SYC": 15.0,   # Seychelles
    "SLE": 15.0,   # Sierra Leone (CEDEAO)
    "SOM": 0.0,    # Somalie (pas de TVA formelle)
    "ZAF": 15.0,   # Afrique du Sud (SACU) - 15.5% à partir de mai 2025
    "SSD": 18.0,   # Soudan du Sud (EAC)
    "SDN": 17.0,   # Soudan
    "TZA": 18.0,   # Tanzanie (EAC)
    "TGO": 18.0,   # Togo (UEMOA)
    "TUN": 19.0,   # Tunisie
    "UGA": 18.0,   # Ouganda (EAC)
    "ZMB": 16.0,   # Zambie
    "ZWE": 15.0,   # Zimbabwe (réduit de 14.5%)
}

# Redevance statistique (en pourcentage de la valeur CIF)
# Applicable dans certains pays
STATISTICAL_FEE = {
    "BEN": 1.0,
    "BFA": 1.0,
    "CIV": 1.0,
    "GIN": 1.0,
    "MLI": 1.0,
    "NER": 1.0,
    "SEN": 1.0,
    "TGO": 1.0,
    "CMR": 1.0,
    "GAB": 1.0,
    "TCD": 1.0,
    "CAF": 1.0,
    "COG": 1.0,
    "GNQ": 1.0,
}

# Prélèvement Communautaire de Solidarité (PCS) - CEDEAO/UEMOA
# En pourcentage de la valeur CIF
COMMUNITY_LEVY = {
    "BEN": 0.5,
    "BFA": 0.5,
    "CIV": 0.5,
    "GIN": 0.5,
    "GNB": 0.5,
    "MLI": 0.5,
    "NER": 0.5,
    "SEN": 0.5,
    "TGO": 0.5,
    "GMB": 0.5,
    "GHA": 0.5,
    "LBR": 0.5,
    "NGA": 0.5,
    "SLE": 0.5,
}

# Prélèvement CEMAC (CCI - Contribution Communautaire d'Intégration)
CEMAC_LEVY = {
    "CMR": 1.0,
    "CAF": 1.0,
    "TCD": 1.0,
    "COG": 1.0,
    "GNQ": 1.0,
    "GAB": 1.0,
}

# =============================================================================
# FONCTIONS UTILITAIRES AVEC SUPPORT ISO2/ISO3
# =============================================================================

# Import du mapping centralisé
try:
    from country_codes import get_iso3_from_iso2, ISO2_TO_ISO3
except ImportError:
    # Fallback si le fichier n'est pas accessible
    ISO2_TO_ISO3 = {
        "DZ": "DZA", "AO": "AGO", "BJ": "BEN", "BW": "BWA", "BF": "BFA",
        "BI": "BDI", "CV": "CPV", "CM": "CMR", "CF": "CAF", "TD": "TCD",
        "KM": "COM", "CG": "COG", "CD": "COD", "CI": "CIV", "DJ": "DJI",
        "EG": "EGY", "GQ": "GNQ", "ER": "ERI", "SZ": "SWZ", "ET": "ETH",
        "GA": "GAB", "GM": "GMB", "GH": "GHA", "GN": "GIN", "GW": "GNB",
        "KE": "KEN", "LS": "LSO", "LR": "LBR", "LY": "LBY", "MG": "MDG",
        "MW": "MWI", "ML": "MLI", "MR": "MRT", "MU": "MUS", "MA": "MAR",
        "MZ": "MOZ", "NA": "NAM", "NE": "NER", "NG": "NGA", "RW": "RWA",
        "ST": "STP", "SN": "SEN", "SC": "SYC", "SL": "SLE", "SO": "SOM",
        "ZA": "ZAF", "SS": "SSD", "SD": "SDN", "TZ": "TZA", "TG": "TGO",
        "TN": "TUN", "UG": "UGA", "ZM": "ZMB", "ZW": "ZWE",
    }
    def get_iso3_from_iso2(iso2):
        return ISO2_TO_ISO3.get(iso2.upper())

def _normalize_country_code(code: str) -> str:
    """Normalise un code pays vers ISO3"""
    code = code.upper()
    # Si c'est déjà ISO3, retourner tel quel
    if len(code) == 3:
        return code
    # Sinon, convertir ISO2 -> ISO3
    return ISO2_TO_ISO3.get(code, code)

def get_vat_rate(country_code: str) -> float:
    """Retourne le taux de TVA pour un pays (supporte ISO2 et ISO3)"""
    iso3 = _normalize_country_code(country_code)
    return VAT_RATES.get(iso3, 0.0)

def get_statistical_fee(country_code: str) -> float:
    """Retourne la redevance statistique pour un pays (supporte ISO2 et ISO3)"""
    iso3 = _normalize_country_code(country_code)
    return STATISTICAL_FEE.get(iso3, 0.0)

def get_community_levy(country_code: str) -> float:
    """Retourne le prélèvement communautaire pour un pays (supporte ISO2 et ISO3)"""
    iso3 = _normalize_country_code(country_code)
    return COMMUNITY_LEVY.get(iso3, 0.0)

def get_cemac_levy(country_code: str) -> float:
    """Retourne le prélèvement CEMAC pour un pays (supporte ISO2 et ISO3)"""
    iso3 = _normalize_country_code(country_code)
    return CEMAC_LEVY.get(iso3, 0.0)

def get_total_import_taxes(country_code: str, cif_value: float, customs_duty: float) -> dict:
    """
    Calcule l'ensemble des taxes à l'importation pour un pays
    
    Args:
        country_code: Code ISO2 ou ISO3 du pays
        cif_value: Valeur CIF de la marchandise
        customs_duty: Droits de douane calculés
        
    Returns:
        Dict avec le détail des taxes
    """
    iso3 = _normalize_country_code(country_code)
    
    vat_rate = VAT_RATES.get(iso3, 0.0)
    stat_fee_rate = STATISTICAL_FEE.get(iso3, 0.0)
    community_rate = COMMUNITY_LEVY.get(iso3, 0.0)
    cemac_rate = CEMAC_LEVY.get(iso3, 0.0)
    
    # Calcul des montants - assiette cumulative
    # stat_fee: base = CIF + DD
    stat_fee = (cif_value + customs_duty) * (stat_fee_rate / 100)
    # community_levy: base = CIF + DD + stat_fee
    community_levy = (cif_value + customs_duty + stat_fee) * (community_rate / 100)
    # cemac_levy: base = CIF + DD + stat_fee + community_levy
    cemac_levy = (cif_value + customs_duty + stat_fee + community_levy) * (cemac_rate / 100)

    # Base TVA = CIF + DD + toutes les taxes précédentes
    vat_base = cif_value + customs_duty + stat_fee + community_levy + cemac_levy
    vat_amount = vat_base * (vat_rate / 100)

    total = customs_duty + stat_fee + community_levy + cemac_levy + vat_amount
    
    return {
        "country_code": iso3,
        "cif_value": cif_value,
        "customs_duty": customs_duty,
        "statistical_fee": stat_fee,
        "community_levy": community_levy,
        "cemac_levy": cemac_levy,
        "vat_base": vat_base,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total_taxes": total,
        "effective_rate": (total / cif_value * 100) if cif_value > 0 else 0
    }

# Alias pour compatibilité avec l'ancien code
def calculate_all_taxes(country_code: str, cif_value: float, customs_duty: float) -> dict:
    """Alias pour get_total_import_taxes - maintenu pour compatibilité"""
    return get_total_import_taxes(country_code, cif_value, customs_duty)
