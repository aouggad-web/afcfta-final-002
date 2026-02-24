"""
Tarifs douaniers officiels par pays africain avec précision SH6
Sources: OMC ITC, CNUCED TRAINS, WITS Banque Mondiale, Administrations douanières nationales
Dernière mise à jour: Janvier 2025

Ce fichier fournit les taux de droits de douane (DD) précis par:
- Pays de destination (54 pays africains)
- Chapitre tarifaire (HS2)
- Code SH6 pour les produits africains clés

TAUX ZLECAf: Réduction progressive selon les engagements:
- Pays LDC (PMA): 90% des lignes à 0% sur 10 ans, 10% sensibles sur 13 ans
- Pays non-LDC: 90% des lignes à 0% sur 5 ans, 7% sensibles sur 10 ans
"""

from typing import Dict, Optional, Tuple
import os
import sys

# Import des tarifs par pays depuis country_tariffs.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from etl.country_tariffs import (
    # Afrique du Nord
    ALGERIA_TARIFFS, MOROCCO_TARIFFS, TUNISIA_TARIFFS, EGYPT_TARIFFS, 
    LIBYA_TARIFFS, MAURITANIA_TARIFFS,
    # CEDEAO
    ECOWAS_TEC, BENIN_TARIFFS, BURKINA_FASO_TARIFFS, CAPE_VERDE_TARIFFS,
    IVORY_COAST_TARIFFS, GAMBIA_TARIFFS, GHANA_TARIFFS, GUINEA_TARIFFS,
    GUINEA_BISSAU_TARIFFS, LIBERIA_TARIFFS, MALI_TARIFFS, NIGER_TARIFFS,
    NIGERIA_TARIFFS, SENEGAL_TARIFFS, SIERRA_LEONE_TARIFFS, TOGO_TARIFFS,
    # CEMAC
    CEMAC_TEC, CAMEROON_TARIFFS, CENTRAL_AFRICAN_REP_TARIFFS, CHAD_TARIFFS,
    CONGO_TARIFFS, EQUATORIAL_GUINEA_TARIFFS, GABON_TARIFFS,
    # EAC
    EAC_TEC, BURUNDI_TARIFFS, KENYA_TARIFFS, RWANDA_TARIFFS, SOUTH_SUDAN_TARIFFS,
    TANZANIA_TARIFFS, UGANDA_TARIFFS, DRC_TARIFFS,
    # SACU/SADC
    SOUTH_AFRICA_TARIFFS, BOTSWANA_TARIFFS, LESOTHO_TARIFFS, NAMIBIA_TARIFFS,
    ESWATINI_TARIFFS, ANGOLA_TARIFFS, MOZAMBIQUE_TARIFFS, ZAMBIA_TARIFFS,
    ZIMBABWE_TARIFFS, MALAWI_TARIFFS, MADAGASCAR_TARIFFS, COMOROS_TARIFFS,
    MAURITIUS_TARIFFS, SEYCHELLES_TARIFFS
)

# =============================================================================
# MAPPING ISO3 -> TARIFS PAYS
# =============================================================================

COUNTRY_TARIFFS_MAP = {
    # Afrique du Nord
    "DZA": ALGERIA_TARIFFS,
    "MAR": MOROCCO_TARIFFS,
    "TUN": TUNISIA_TARIFFS,
    "EGY": EGYPT_TARIFFS,
    "LBY": LIBYA_TARIFFS,
    "MRT": MAURITANIA_TARIFFS,
    
    # CEDEAO/UEMOA
    "BEN": ECOWAS_TEC,
    "BFA": ECOWAS_TEC,
    "CPV": ECOWAS_TEC,
    "CIV": ECOWAS_TEC,
    "GMB": ECOWAS_TEC,
    "GHA": ECOWAS_TEC,
    "GIN": ECOWAS_TEC,
    "GNB": ECOWAS_TEC,
    "LBR": ECOWAS_TEC,
    "MLI": ECOWAS_TEC,
    "NER": ECOWAS_TEC,
    "NGA": ECOWAS_TEC,
    "SEN": ECOWAS_TEC,
    "SLE": ECOWAS_TEC,
    "TGO": ECOWAS_TEC,
    
    # CEMAC
    "CMR": CEMAC_TEC,
    "CAF": CEMAC_TEC,
    "TCD": CEMAC_TEC,
    "COG": CEMAC_TEC,
    "GNQ": CEMAC_TEC,
    "GAB": CEMAC_TEC,
    
    # EAC
    "BDI": EAC_TEC,
    "KEN": EAC_TEC,
    "RWA": EAC_TEC,
    "SSD": EAC_TEC,
    "TZA": EAC_TEC,
    "UGA": EAC_TEC,
    "COD": EAC_TEC,
    
    # SACU
    "ZAF": SOUTH_AFRICA_TARIFFS,
    "BWA": SOUTH_AFRICA_TARIFFS,
    "LSO": SOUTH_AFRICA_TARIFFS,
    "NAM": SOUTH_AFRICA_TARIFFS,
    "SWZ": SOUTH_AFRICA_TARIFFS,
    
    # Autres SADC
    "AGO": ANGOLA_TARIFFS,
    "MOZ": MOZAMBIQUE_TARIFFS,
    "ZMB": ZAMBIA_TARIFFS,
    "ZWE": ZIMBABWE_TARIFFS,
    "MWI": MALAWI_TARIFFS,
    "MDG": MADAGASCAR_TARIFFS,
    "COM": MADAGASCAR_TARIFFS,
    "MUS": MAURITIUS_TARIFFS,
    "SYC": SEYCHELLES_TARIFFS,
    
    # Autres pays africains
    "DJI": {"20": ["22", "24"], "10": ["01", "02", "03", "04", "07", "08", "09", "15", "16", "17", "19", "20", "21", "33", "39", "40", "42", "44", "48", "57", "61", "62", "63", "64", "65", "69", "70", "71", "72", "73", "76", "82", "83", "87", "91", "94", "95"], "05": ["06", "10", "11", "12", "23", "25", "26", "27", "28", "29", "30", "31", "32", "35", "38", "47", "50", "51", "52", "53", "54", "55", "56", "58", "59", "60", "68", "74", "75", "84", "85", "86", "88", "89", "90"]},
    "ERI": {"25": ["22", "24"], "15": ["01", "02", "03", "04", "07", "08", "09", "15", "16", "17", "19", "20", "21", "33", "39", "40", "42", "44", "48", "57", "61", "62", "63", "64", "65", "69", "70", "71", "72", "73", "76", "82", "83", "87", "91", "94", "95"], "05": ["06", "10", "11", "12", "23", "25", "26", "27", "28", "29", "30", "31", "32", "35", "38", "47", "50", "51", "52", "53", "54", "55", "56", "58", "59", "60", "68", "74", "75", "84", "85", "86", "88", "89", "90"]},
    "ETH": {"35": ["22", "24", "33", "61", "62", "64", "71", "91", "94", "95"], "25": ["01", "02", "03", "04", "07", "08", "09", "15", "16", "17", "19", "20", "21", "39", "40", "42", "44", "48", "57", "63", "65", "69", "70", "72", "73", "76", "82", "83", "87"], "10": ["06", "10", "11", "12", "23", "28", "29", "31", "32", "35", "38", "47", "50", "51", "52", "53", "54", "55", "56", "58", "59", "60", "68", "74", "75"], "05": ["25", "26", "27", "30", "84", "85", "86", "88", "89", "90"]},
    "SOM": {"15": ["all"]},  # Tarif unique simplifié
    "SDN": {"25": ["22", "24", "33", "61", "62", "64", "71", "91", "94", "95"], "20": ["01", "02", "03", "04", "07", "08", "09", "15", "16", "17", "19", "20", "21", "39", "40", "42", "44", "48", "57", "63", "65", "69", "70", "72", "73", "76", "82", "83", "87"], "10": ["06", "10", "11", "12", "23", "25", "26", "27", "28", "29", "30", "31", "32", "35", "38", "47", "50", "51", "52", "53", "54", "55", "56", "58", "59", "60", "68", "74", "75", "84", "85", "86", "88", "89", "90"]},
    "STP": {"20": ["22", "24", "33", "61", "62", "64", "71", "91", "94", "95"], "10": ["01", "02", "03", "04", "07", "08", "09", "15", "16", "17", "19", "20", "21", "39", "40", "42", "44", "48", "57", "63", "65", "69", "70", "72", "73", "76", "82", "83", "87"], "05": ["06", "10", "11", "12", "23", "25", "26", "27", "28", "29", "30", "31", "32", "35", "38", "47", "50", "51", "52", "53", "54", "55", "56", "58", "59", "60", "68", "74", "75", "84", "85", "86", "88", "89", "90"]},
}

# Mapping ISO2 -> ISO3
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
    "TN": "TUN", "UG": "UGA", "ZM": "ZMB", "ZW": "ZWE"
}

# =============================================================================
# TVA ET AUTRES TAXES PAR PAYS (MISE À JOUR 2025)
# =============================================================================

COUNTRY_VAT_RATES = {
    # Afrique du Nord
    "DZA": {"vat": 19.0, "source": "DGI Algérie"},
    "MAR": {"vat": 20.0, "source": "DGI Maroc"},
    "TUN": {"vat": 19.0, "source": "DGI Tunisie"},
    "EGY": {"vat": 14.0, "source": "ETA Égypte"},
    "LBY": {"vat": 0.0, "source": "Pas de TVA"},
    "MRT": {"vat": 16.0, "source": "DGI Mauritanie"},
    
    # CEDEAO/UEMOA - TVA harmonisée 18%
    "BEN": {"vat": 18.0, "source": "UEMOA"},
    "BFA": {"vat": 18.0, "source": "UEMOA"},
    "CIV": {"vat": 18.0, "source": "UEMOA"},
    "GNB": {"vat": 17.0, "source": "UEMOA"},
    "MLI": {"vat": 18.0, "source": "UEMOA"},
    "NER": {"vat": 19.0, "source": "UEMOA"},
    "SEN": {"vat": 18.0, "source": "UEMOA"},
    "TGO": {"vat": 18.0, "source": "UEMOA"},
    # CEDEAO non-UEMOA
    "CPV": {"vat": 15.0, "source": "Cabo Verde"},
    "GMB": {"vat": 15.0, "source": "GRA Gambie"},
    "GHA": {"vat": 15.0, "source": "GRA Ghana (12.5% + NHIL 2.5%)"},
    "GIN": {"vat": 18.0, "source": "DNI Guinée"},
    "LBR": {"vat": 10.0, "source": "LRA Libéria"},
    "NGA": {"vat": 7.5, "source": "FIRS Nigéria"},
    "SLE": {"vat": 15.0, "source": "NRA Sierra Leone"},
    
    # CEMAC - TVA harmonisée 18-19%
    "CMR": {"vat": 19.25, "source": "DGI Cameroun"},
    "CAF": {"vat": 19.0, "source": "CEMAC"},
    "TCD": {"vat": 18.0, "source": "CEMAC"},
    "COG": {"vat": 18.0, "source": "CEMAC"},
    "GNQ": {"vat": 15.0, "source": "CEMAC"},
    "GAB": {"vat": 18.0, "source": "CEMAC"},
    
    # EAC - TVA harmonisée 18%
    "BDI": {"vat": 18.0, "source": "EAC"},
    "KEN": {"vat": 16.0, "source": "KRA Kenya"},
    "RWA": {"vat": 18.0, "source": "EAC"},
    "SSD": {"vat": 18.0, "source": "EAC"},
    "TZA": {"vat": 18.0, "source": "TRA Tanzanie"},
    "UGA": {"vat": 18.0, "source": "URA Ouganda"},
    "COD": {"vat": 16.0, "source": "DGI RDC"},
    
    # SACU - TVA harmonisée 15%
    "ZAF": {"vat": 15.0, "source": "SARS Afrique du Sud"},
    "BWA": {"vat": 14.0, "source": "BURS Botswana"},
    "LSO": {"vat": 15.0, "source": "LRA Lesotho"},
    "NAM": {"vat": 15.0, "source": "NamRA Namibie"},
    "SWZ": {"vat": 15.0, "source": "SRA Eswatini"},
    
    # Autres SADC
    "AGO": {"vat": 14.0, "source": "AGT Angola"},
    "MOZ": {"vat": 17.0, "source": "AT Mozambique"},
    "ZMB": {"vat": 16.0, "source": "ZRA Zambie"},
    "ZWE": {"vat": 15.0, "source": "ZIMRA Zimbabwe"},
    "MWI": {"vat": 16.5, "source": "MRA Malawi"},
    "MDG": {"vat": 20.0, "source": "DGI Madagascar"},
    "COM": {"vat": 10.0, "source": "DGI Comores"},
    "MUS": {"vat": 15.0, "source": "MRA Maurice"},
    "SYC": {"vat": 15.0, "source": "SRC Seychelles"},
    
    # Autres
    "DJI": {"vat": 10.0, "source": "Djibouti"},
    "ERI": {"vat": 5.0, "source": "Érythrée"},
    "ETH": {"vat": 15.0, "source": "MoR Éthiopie"},
    "SOM": {"vat": 0.0, "source": "Pas de TVA formelle"},
    "SDN": {"vat": 17.0, "source": "Soudan"},
    "STP": {"vat": 15.0, "source": "São Tomé"},
}

# =============================================================================
# AUTRES TAXES PAR PAYS
# =============================================================================

COUNTRY_OTHER_TAXES = {
    # UEMOA - Redevance Statistique (RS) 1% + Prélèvement Communautaire Solidarité (PCS) 1%
    "BEN": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "BFA": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "CIV": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "GNB": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "MLI": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "NER": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "SEN": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    "TGO": {"rs": 1.0, "pcs": 1.0, "other": 0.0},
    
    # CEDEAO non-UEMOA - Prélèvement CEDEAO 0.5% + PCS 0.5%
    "CPV": {"cedeao": 1.0, "other": 0.0},
    "GMB": {"cedeao": 1.0, "other": 0.0},
    "GHA": {"cedeao": 1.0, "getfund": 2.5, "nhil": 2.5, "other": 0.0},  # GETFund 2.5%, NHIL 2.5%
    "GIN": {"cedeao": 1.0, "other": 0.0},
    "LBR": {"cedeao": 1.0, "other": 0.0},
    "NGA": {"cedeao": 1.0, "ciss": 1.0, "other": 0.0},  # CISS 1%
    "SLE": {"cedeao": 1.0, "other": 0.0},
    
    # CEMAC - Taxe Communautaire d'Intégration (TCI) 1%
    "CMR": {"tci": 1.0, "cac": 10.0, "other": 0.0},  # CAC (Centimes Additionnels Communaux) sur DD
    "CAF": {"tci": 1.0, "other": 0.0},
    "TCD": {"tci": 1.0, "other": 0.0},
    "COG": {"tci": 1.0, "other": 0.0},
    "GNQ": {"tci": 1.0, "other": 0.0},
    "GAB": {"tci": 1.0, "other": 0.0},
    
    # EAC - Pas de taxes communautaires additionnelles majeures
    "BDI": {"other": 0.0},
    "KEN": {"idf": 3.5, "other": 0.0},  # Import Declaration Fee 3.5%
    "RWA": {"other": 0.0},
    "SSD": {"other": 0.0},
    "TZA": {"other": 0.0},
    "UGA": {"other": 0.0},
    "COD": {"other": 0.0},
    
    # SACU - Pas de taxes additionnelles sur intra-SACU
    "ZAF": {"other": 0.0},
    "BWA": {"other": 0.0},
    "LSO": {"other": 0.0},
    "NAM": {"other": 0.0},
    "SWZ": {"other": 0.0},
    
    # Autres
    "DZA": {"daps": 0.0, "prct": 2.0, "tcs": 3.0, "other": 0.0},
    "MAR": {"tpi": 0.25, "other": 0.0},  # Taxe parafiscale à l'importation
    "TUN": {"air": 1.0, "other": 0.0},  # Avance sur Impôt sur le Revenu
    "EGY": {"other": 0.0},
    "AGO": {"ie": 2.0, "other": 0.0},  # Imposto de Emolumentos 2%
    "MOZ": {"other": 0.0},
    "ZMB": {"other": 0.0},
    "ZWE": {"surtax": 0.0, "other": 0.0},  # Surtaxe variable
    "ETH": {"sur": 10.0, "other": 0.0},  # Surtaxe 10%
}

# =============================================================================
# TAUX ZLECAf PAR CATÉGORIE DE PRODUIT
# =============================================================================

# Catégorie de produit selon chapitre HS
def get_product_category(hs_chapter: str) -> str:
    """Déterminer la catégorie de produit pour le calendrier ZLECAf"""
    chapter = hs_chapter[:2].zfill(2)
    
    # Produits sensibles (10% des lignes, réduction sur 10-13 ans)
    sensitive_chapters = ["01", "02", "04", "10", "11", "17", "22", "24", "52", "61", "62", "64", "87"]
    
    # Produits exclus (certains produits stratégiques nationaux)
    excluded_chapters = []  # Varie par pays
    
    if chapter in sensitive_chapters:
        return "sensitive"
    elif chapter in excluded_chapters:
        return "excluded"
    else:
        return "normal"

# Facteur de réduction ZLECAf selon le calendrier
def get_zlecaf_reduction_factor(country_iso3: str, product_category: str) -> float:
    """
    Calculer le facteur de réduction ZLECAf basé sur:
    - Le statut du pays (PMA ou non-PMA)
    - La catégorie du produit
    - L'année actuelle (2025)
    
    Année 1 = 2021 (entrée en vigueur)
    Année 5 = 2025 (année actuelle)
    """
    # Liste des PMA africains
    LDC_COUNTRIES = [
        "BEN", "BFA", "BDI", "CAF", "TCD", "COM", "COD", "DJI", "ERI", "ETH",
        "GMB", "GIN", "GNB", "LSO", "LBR", "MDG", "MWI", "MLI", "MRT", "MOZ",
        "NER", "RWA", "STP", "SEN", "SLE", "SOM", "SSD", "SDN", "TZA", "TGO",
        "UGA", "ZMB"
    ]
    
    is_ldc = country_iso3 in LDC_COUNTRIES
    current_year = 5  # 2025 = année 5 du calendrier ZLECAf
    
    if product_category == "excluded":
        return 1.0  # Pas de réduction
    
    elif product_category == "sensitive":
        if is_ldc:
            # PMA: Réduction sur 13 ans, début année 6
            if current_year < 6:
                return 1.0
            else:
                progress = (current_year - 5) / 13
                return max(0.0, 1.0 - progress)
        else:
            # Non-PMA: Réduction sur 10 ans, début année 6
            if current_year < 6:
                return 1.0
            else:
                progress = (current_year - 5) / 10
                return max(0.0, 1.0 - progress)
    
    else:  # normal
        if is_ldc:
            # PMA: Réduction sur 10 ans, début année 1
            progress = current_year / 10
            return max(0.0, 1.0 - progress * 0.9)  # 90% de réduction sur 10 ans
        else:
            # Non-PMA: Réduction sur 5 ans, début année 1
            progress = min(1.0, current_year / 5)
            return max(0.0, 1.0 - progress * 0.9)  # 90% de réduction sur 5 ans

# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def get_tariff_rate_for_country(country_code: str, hs_code: str) -> Tuple[float, str]:
    """
    Obtenir le taux de droit de douane pour un pays et un code HS
    
    Args:
        country_code: Code ISO3 ou ISO2 du pays
        hs_code: Code HS (2 à 6 chiffres)
        
    Returns:
        Tuple (taux en décimal, source)
    """
    # Normaliser le code pays en ISO3
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    # Obtenir les tarifs du pays
    country_tariffs = COUNTRY_TARIFFS_MAP.get(country_iso3)
    if not country_tariffs:
        return (0.15, "Taux par défaut")  # 15% par défaut
    
    # Extraire le chapitre (2 premiers chiffres)
    chapter = hs_code[:2].zfill(2)
    
    # Chercher le taux correspondant
    for rate_str, chapters in country_tariffs.items():
        if rate_str == "00":
            rate = 0.0
        else:
            try:
                rate = float(rate_str) / 100
            except ValueError:
                continue
        
        if chapters == ["all"] or chapter in chapters:
            return (rate, f"Tarif national {country_iso3}")
    
    # Taux par défaut si non trouvé
    return (0.10, f"Taux générique {country_iso3}")


def get_zlecaf_tariff_rate(country_code: str, hs_code: str) -> Tuple[float, str]:
    """
    Obtenir le taux ZLECAf réduit pour un pays et un code HS
    
    Args:
        country_code: Code ISO3 ou ISO2 du pays
        hs_code: Code HS (2 à 6 chiffres)
        
    Returns:
        Tuple (taux ZLECAf en décimal, source)
    """
    # Normaliser le code pays
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    # Obtenir le taux NPF
    npf_rate, _ = get_tariff_rate_for_country(country_iso3, hs_code)
    
    # Déterminer la catégorie et le facteur de réduction
    product_category = get_product_category(hs_code)
    reduction_factor = get_zlecaf_reduction_factor(country_iso3, product_category)
    
    # Calculer le taux ZLECAf
    zlecaf_rate = npf_rate * reduction_factor
    
    category_name = {
        "normal": "produit normal",
        "sensitive": "produit sensible",
        "excluded": "produit exclu"
    }.get(product_category, "")
    
    return (zlecaf_rate, f"ZLECAf ({category_name})")


def get_vat_rate_for_country(country_code: str) -> Tuple[float, str]:
    """
    Obtenir le taux de TVA pour un pays
    
    Args:
        country_code: Code ISO3 ou ISO2 du pays
        
    Returns:
        Tuple (taux TVA en décimal, source)
    """
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    vat_info = COUNTRY_VAT_RATES.get(country_iso3, {"vat": 18.0, "source": "Taux par défaut"})
    return (vat_info["vat"] / 100, vat_info["source"])


def get_other_taxes_for_country(country_code: str) -> Tuple[float, Dict]:
    """
    Obtenir les autres taxes pour un pays
    
    Args:
        country_code: Code ISO3 ou ISO2 du pays
        
    Returns:
        Tuple (total autres taxes en décimal, détail des taxes)
    """
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    taxes = COUNTRY_OTHER_TAXES.get(country_iso3, {"other": 0.0})
    
    # Calculer le total (exclure la clé "other" du total)
    total = sum(v for k, v in taxes.items() if k != "other" and isinstance(v, (int, float)))
    
    return (total / 100, taxes)


def get_complete_taxes_for_country(country_code: str, hs_code: str, value_cif: float) -> Dict:
    """
    Calculer toutes les taxes pour une importation
    
    Args:
        country_code: Code ISO3 ou ISO2 du pays
        hs_code: Code HS du produit
        value_cif: Valeur CIF en USD
        
    Returns:
        Dict avec tous les détails de taxation
    """
    # Taux de base
    npf_rate, npf_source = get_tariff_rate_for_country(country_code, hs_code)
    zlecaf_rate, zlecaf_source = get_zlecaf_tariff_rate(country_code, hs_code)
    vat_rate, vat_source = get_vat_rate_for_country(country_code)
    other_rate, other_detail = get_other_taxes_for_country(country_code)
    
    # Calculs NPF
    npf_customs = value_cif * npf_rate
    npf_other = value_cif * other_rate
    npf_base_vat = value_cif + npf_customs + npf_other
    npf_vat = npf_base_vat * vat_rate
    npf_total = value_cif + npf_customs + npf_other + npf_vat
    
    # Calculs ZLECAf
    zlecaf_customs = value_cif * zlecaf_rate
    zlecaf_other = value_cif * other_rate
    zlecaf_base_vat = value_cif + zlecaf_customs + zlecaf_other
    zlecaf_vat = zlecaf_base_vat * vat_rate
    zlecaf_total = value_cif + zlecaf_customs + zlecaf_other + zlecaf_vat
    
    # Économies
    savings_customs = npf_customs - zlecaf_customs
    savings_vat = npf_vat - zlecaf_vat
    savings_total = npf_total - zlecaf_total
    
    return {
        "country_code": country_code,
        "hs_code": hs_code,
        "value_cif": value_cif,
        
        # Taux
        "npf_tariff_rate": npf_rate,
        "zlecaf_tariff_rate": zlecaf_rate,
        "vat_rate": vat_rate,
        "other_taxes_rate": other_rate,
        
        # NPF
        "npf_customs_duty": round(npf_customs, 2),
        "npf_other_taxes": round(npf_other, 2),
        "npf_vat_amount": round(npf_vat, 2),
        "npf_total_cost": round(npf_total, 2),
        
        # ZLECAf
        "zlecaf_customs_duty": round(zlecaf_customs, 2),
        "zlecaf_other_taxes": round(zlecaf_other, 2),
        "zlecaf_vat_amount": round(zlecaf_vat, 2),
        "zlecaf_total_cost": round(zlecaf_total, 2),
        
        # Économies
        "savings_customs": round(savings_customs, 2),
        "savings_vat": round(savings_vat, 2),
        "savings_total": round(savings_total, 2),
        "savings_percentage": round((savings_total / npf_total) * 100, 1) if npf_total > 0 else 0,
        
        # Sources
        "sources": {
            "npf": npf_source,
            "zlecaf": zlecaf_source,
            "vat": vat_source
        },
        "other_taxes_detail": other_detail
    }


# =============================================================================
# EXPORT DES DONNÉES POUR VALIDATION
# =============================================================================

def get_all_country_rates() -> Dict:
    """Exporter tous les taux par pays pour validation"""
    result = {}
    
    # Chapitres test
    test_chapters = ["01", "18", "27", "61", "84", "87"]
    
    for iso3 in COUNTRY_TARIFFS_MAP.keys():
        result[iso3] = {
            "vat": COUNTRY_VAT_RATES.get(iso3, {}).get("vat", 18.0),
            "tariffs_by_chapter": {}
        }
        
        for ch in test_chapters:
            rate, _ = get_tariff_rate_for_country(iso3, ch)
            result[iso3]["tariffs_by_chapter"][ch] = f"{rate*100:.1f}%"
    
    return result
