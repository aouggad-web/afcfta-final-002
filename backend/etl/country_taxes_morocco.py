"""
MAROC (MAR) - Formalités administratives et taxes à l'importation
Sources:
  - Administration des Douanes et Impôts Indirects (ADII) — douane.gov.ma
  - ADIL portal (portail.adii.gov.ma) — info_4.asp (contrôles par position)
  - Circulaire 6050/2024 ADII — mise à jour des procédures d'importation
  - ONSSA (Office National de Sécurité Sanitaire des Aliments) — contrôles sanitaires
  - IMANOR (Institut Marocain de Normalisation) — certificats de conformité
  - Office des Changes Maroc — contrôles de change
Dernière mise à jour: 2025

TAXES NATIONALES À L'IMPORTATION (source: ADIL/douane.gov.ma):
- D.D (Droit d'Importation): 2.5%, 10%, 17.5%, 25%, 32.5%, 40%
- TPI (Taxe Parafiscale à l'Importation): 0.25% (majorité des produits)
- TVA: 20% taux normal, 14%, 10%, 7% taux réduits
- TIC (Taxe Intérieure de Consommation): produits spécifiques (tabac, alcool, lubrifiants)
- TPCE (Taxe pour la Protection et la Conformité de l'Environnement): certains produits

AVANTAGES FISCAUX ZLECAf:
- Exonération DD avec certificat d'origine ZLECAf (AfCFTA)

FORMALITÉS ADMINISTRATIVES (codes ADII — info_4.asp):
Les codes suivants correspondent aux contrôles officiels enregistrés dans le système ADIL
de la douane marocaine (portail.adii.gov.ma/adil/info_4.asp?pos=<position>) :

  910  Déclaration d'Importation (DUM — Déclaration Unique de Marchandise)
       Obligatoire pour toute importation. Code universel ADII.

  C01  Contrôle vétérinaire ONSSA
       Requis pour animaux vivants, viandes, produits laitiers, œufs,
       produits aquatiques et préparations à base de protéines animales.
       Autorité délivrante : ONSSA - Direction des Contrôles aux Frontières.

  C02  Contrôle phytosanitaire ONSSA
       Requis pour végétaux, plants, graines, fruits, légumes et toute
       denrée d'origine végétale pouvant véhiculer des organismes nuisibles.
       Autorité délivrante : ONSSA - Service de la Protection des Végétaux.

  C03  Certificat de conformité aux normes marocaines (IMANOR)
       Requis pour produits industriels réglementés (électronique, électroménager,
       matériaux de construction, jouets, équipements électriques).
       Autorité délivrante : IMANOR (Institut Marocain de Normalisation).

  C04  Autorisation du Ministère de la Santé
       Requis pour médicaments à usage humain, dispositifs médicaux, produits
       pharmaceutiques et préparations officinales.
       Autorité délivrante : Direction du Médicament et de la Pharmacie (DMP).

  C05  Visa d'homologation pharmaceutique (MMSP)
       Enregistrement AMM (Autorisation de Mise sur le Marché) délivrée par
       le Ministère de la Santé — obligatoire avant première importation.

  C06  Autorisation du Ministère de l'Agriculture
       Requis pour semences, matières fertilisantes et supports de culture
       soumis à homologation phytosanitaire.
       Autorité délivrante : ONSSA - Direction des Intrants Agricoles.

  C07  Attestation de libre commercialisation produits alimentaires
       Confirme la conformité réglementaire des denrées alimentaires
       transformées aux exigences nationales marocaines (normes NM).

  C08  Licence d'importation (produits sous restriction quantitative)
       Autorisation préalable pour produits soumis à contingentement,
       mesures de sauvegarde ou restrictions quantitatives.

  C09  Autorisation ONHYM (Office National des Hydrocarbures et des Mines)
       Requis pour hydrocarbures, minéraux et produits pétroliers.

  C10  Autorisation du Ministère de l'Intérieur (armes/sécurité)
       Requis pour armes, munitions, explosifs et équipements de sécurité.

  C11  Certificat d'analyse chimique (laboratoire agréé MAMDA)
       Requis pour engrais chimiques, pesticides et biocides.

  C12  Contrôle Office des Changes (importations soumises à rapatriement)
       Déclaration préalable pour importations dépassant les seuils de
       contrôle de change définis par l'Office des Changes Maroc.
"""

# =============================================================================
# FORMALITÉS ADMINISTRATIVES PAR CATÉGORIE DE PRODUIT
# Source: ADIL portal (douane.gov.ma) — codes officiels par chapitre SH
# =============================================================================

MAR_FORMALITIES_BY_CATEGORY = {
    # -------------------------------------------------------------------------
    # ANIMAUX VIVANTS ET PRODUITS ANIMAUX (Ch 01-05, 16)
    # Source: C01 ONSSA — contrôle vétérinaire obligatoire aux frontières
    # -------------------------------------------------------------------------
    "animal_products": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII (Administration des Douanes et Impôts Indirects)",
            "authority_en": "ADII (Customs and Indirect Taxes Administration)",
            "is_mandatory": True,
        },
        {
            "code": "C01",
            "document_fr": "Certificat sanitaire vétérinaire / Contrôle ONSSA",
            "document_en": "Veterinary Health Certificate / ONSSA Control",
            "authority_fr": "ONSSA — Direction des Contrôles aux Frontières",
            "authority_en": "ONSSA — Border Controls Directorate",
            "is_mandatory": True,
        },
        {
            "code": "C07",
            "document_fr": "Attestation de libre commercialisation",
            "document_en": "Certificate of Free Sale",
            "authority_fr": "ONSSA",
            "authority_en": "ONSSA",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # PRODUITS ALIMENTAIRES D'ORIGINE VÉGÉTALE (Ch 06-15, 17-24)
    # Source: C02 ONSSA — contrôle phytosanitaire obligatoire aux frontières
    # -------------------------------------------------------------------------
    "food_agriculture": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C02",
            "document_fr": "Certificat phytosanitaire du pays d'origine",
            "document_en": "Phytosanitary Certificate from Country of Origin",
            "authority_fr": "ONSSA — Service de la Protection des Végétaux",
            "authority_en": "ONSSA — Plant Protection Service",
            "is_mandatory": True,
        },
        {
            "code": "C07",
            "document_fr": "Attestation de libre commercialisation / conformité alimentaire",
            "document_en": "Certificate of Free Sale / Food Compliance",
            "authority_fr": "ONSSA",
            "authority_en": "ONSSA",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # MÉDICAMENTS ET DISPOSITIFS MÉDICAUX (Ch 30)
    # Source: C04/C05 DMP — autorisation ministérielle obligatoire
    # -------------------------------------------------------------------------
    "pharmaceuticals": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C04",
            "document_fr": "Autorisation du Ministère de la Santé",
            "document_en": "Ministry of Health Authorization",
            "authority_fr": "Ministère de la Santé — Direction du Médicament et de la Pharmacie (DMP)",
            "authority_en": "Ministry of Health — Drug and Pharmacy Directorate (DMP)",
            "is_mandatory": True,
        },
        {
            "code": "C05",
            "document_fr": "Autorisation de Mise sur le Marché (AMM)",
            "document_en": "Marketing Authorization (AMM)",
            "authority_fr": "DMP — Ministère de la Santé du Maroc",
            "authority_en": "DMP — Ministry of Health of Morocco",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # PRODUITS CHIMIQUES ET ENGRAIS (Ch 28-29, 31-38)
    # Source: C11 MAMDA/ONSSA — analyse pour engrais, pesticides
    # -------------------------------------------------------------------------
    "chemicals": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C11",
            "document_fr": "Certificat d'analyse chimique (laboratoire agréé)",
            "document_en": "Chemical Analysis Certificate (accredited laboratory)",
            "authority_fr": "Laboratoire agréé MEFRA / Ministère de l'Environnement",
            "authority_en": "MEFRA accredited laboratory / Ministry of Environment",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # VÉHICULES ET ÉQUIPEMENTS (Ch 84-87, 90)
    # Source: C03 IMANOR — certificat de conformité technique obligatoire
    # -------------------------------------------------------------------------
    "vehicles_machinery": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C03",
            "document_fr": "Certificat de conformité aux normes marocaines (IMANOR)",
            "document_en": "Certificate of Conformity to Moroccan Standards (IMANOR)",
            "authority_fr": "IMANOR (Institut Marocain de Normalisation)",
            "authority_en": "IMANOR (Moroccan Standardization Institute)",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # HYDROCARBURES ET MINÉRAUX (Ch 26-27)
    # Source: C09 ONHYM — autorisation pour hydrocarbures
    # -------------------------------------------------------------------------
    "hydrocarbons": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C09",
            "document_fr": "Autorisation ONHYM (hydrocarbures et produits miniers)",
            "document_en": "ONHYM Authorization (hydrocarbons and mining products)",
            "authority_fr": "ONHYM (Office National des Hydrocarbures et des Mines)",
            "authority_en": "ONHYM (National Hydrocarbons and Mines Office)",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # ARMES, MUNITIONS ET MATÉRIEL DE SÉCURITÉ (Ch 93)
    # Source: C10 — autorisation préalable du Ministère de l'Intérieur
    # -------------------------------------------------------------------------
    "arms_security": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C10",
            "document_fr": "Autorisation préalable du Ministère de l'Intérieur",
            "document_en": "Prior Authorization from Ministry of Interior",
            "authority_fr": "Ministère de l'Intérieur du Maroc",
            "authority_en": "Ministry of Interior of Morocco",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # SEMENCES ET INTRANTS AGRICOLES (Ch 12, 31 — partie engrais)
    # Source: C06 ONSSA — homologation intrants agricoles
    # -------------------------------------------------------------------------
    "agri_inputs": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII",
            "authority_en": "ADII",
            "is_mandatory": True,
        },
        {
            "code": "C06",
            "document_fr": "Autorisation d'homologation phytosanitaire / intrants agricoles",
            "document_en": "Phytosanitary Homologation Authorization / Agricultural Inputs",
            "authority_fr": "ONSSA — Direction des Intrants Agricoles",
            "authority_en": "ONSSA — Agricultural Inputs Directorate",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # RÉGIME GÉNÉRAL (tous les autres chapitres)
    # -------------------------------------------------------------------------
    "general": [
        {
            "code": "910",
            "document_fr": "Déclaration d'Importation (DUM)",
            "document_en": "Import Declaration (DUM)",
            "authority_fr": "ADII (Administration des Douanes et Impôts Indirects)",
            "authority_en": "ADII (Customs and Indirect Taxes Administration)",
            "is_mandatory": True,
        },
    ],
}


# =============================================================================
# MAPPING CATÉGORIE → FORMALITY_CATEGORY
# Utilise les catégories existantes dans les données MAR enhanced_v2
# =============================================================================

# Catégories produit → bucket formality
_ANIMAL_CATS = {
    "livestock", "live_animals", "poultry", "wildlife",
    "meat", "fish", "dairy", "eggs", "honey",
    "animal_products", "meat_preparations",
}
_FOOD_AGRI_CATS = {
    "plants", "flowers", "vegetables", "legumes", "roots_tubers",
    "fruits", "nuts", "coffee_tea_spices", "coffee", "tea", "spices",
    "cereals", "flour", "milling", "starch", "oilseeds", "sugar",
    "lac_gums", "gums", "vegetable_materials", "fats_oils", "oils",
    "fats", "waxes", "processed_food", "confectionery", "cocoa",
    "bakery", "vegetable_preparations", "beverages", "misc_food",
    "animal_feed", "food_residues", "tobacco",
}
_PHARMA_CATS = {"pharmaceuticals", "pharma"}
_CHEMICAL_CATS = {
    "chemicals", "inorganic_chemicals", "organic_chemicals", "fertilizers",
    "tanning", "dyes", "tanning_dyes", "pigments", "paints", "inks",
    "essential_oils", "essential_oils_cosmetics", "fragrances", "cosmetics",
    "soap", "detergents", "soap_wax", "lubricants", "polishes", "candles",
    "proteins", "starches", "glues", "enzymes", "explosives", "pyrotechnics",
    "matches", "fuels", "photography", "pesticides", "chemicals_misc", "biofuels",
}
_VEHICLE_MACH_CATS = {
    "vehicles", "machinery", "electrical", "electronics",
    "railway", "aircraft", "ships", "optical_medical", "clocks",
}
_HYDRO_CATS = {"mineral_fuels", "oil_gas", "coal", "energy", "ores"}
_ARMS_CATS = {"arms"}
_AGRI_INPUT_CATS = set()  # handled separately by chapter check


def get_mar_formality_category(category: str, chapter: str = "") -> str:
    """
    Map a product category (from enhanced_v2 tariff line) to a formality bucket.

    Args:
        category: The `category` field from the tariff line
        chapter: 2-digit chapter string (used as tiebreaker)

    Returns:
        Formality category key for MAR_FORMALITIES_BY_CATEGORY
    """
    if category in _ANIMAL_CATS:
        return "animal_products"
    if category in _FOOD_AGRI_CATS:
        return "food_agriculture"
    if category in _PHARMA_CATS:
        return "pharmaceuticals"
    if category in _CHEMICAL_CATS:
        # Chapter 31 fertilizers → agri_inputs
        if chapter in ("31",):
            return "agri_inputs"
        return "chemicals"
    if category in _VEHICLE_MACH_CATS:
        return "vehicles_machinery"
    if category in _HYDRO_CATS:
        return "hydrocarbons"
    if category in _ARMS_CATS:
        return "arms_security"
    # Minerals (ch 25) and construction materials → general
    return "general"


def get_mar_formalities_for_line(category: str, chapter: str) -> list:
    """
    Return the list of required administrative documents for a MAR tariff line.

    Args:
        category: enhanced_v2 `category` field
        chapter:  2-digit chapter string

    Returns:
        List of formality dicts (code, document_fr, document_en, authority_fr,
        authority_en, is_mandatory)
    """
    bucket = get_mar_formality_category(category, chapter)
    return MAR_FORMALITIES_BY_CATEGORY.get(bucket, MAR_FORMALITIES_BY_CATEGORY["general"])
