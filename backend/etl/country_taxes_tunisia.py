"""
TUNISIE (TUN) - Formalités administratives et taxes à l'importation
Sources:
  - Direction Générale des Douanes Tunisiennes — douane.finances.tn
  - Portail TarifWeb 2025 (douane.gov.tn/tarifwebnew/) — réglementation par NDP
  - Arrêté du Ministère du Commerce et de l'Industrie (régimes d'importation)
  - ONAGRI (Office National de l'Agriculture) — autorisations phytosanitaires
  - DGSV (Direction Générale des Services Vétérinaires) — certificats vétérinaires
  - INNORPI (Institut National de la Normalisation et de la Propriété Industrielle)
  - ANPE (Agence Nationale de Protection de l'Environnement)
  - Ministère de la Santé — autorisation préalable médicaments
  - GUCE (Guichet Unique du Commerce Extérieur) — procédures centralisées
Dernière mise à jour: 2025

TAXES NATIONALES À L'IMPORTATION (source: TarifWeb 2025 / douane.finances.tn):
- D.D (Droit de Douane): 0%, 10%, 20%, 30%, 36% selon NDP
- AIR (Acompte sur Impôt sur les Revenus): 1% (imputable, applicable à la plupart des imports)
- TVA: 19% taux normal, 13% et 7% taux réduits
- FODEC (Fonds de Développement de la Compétitivité): 1% (produits industriels)
- DC (Droit de Consommation): produits de luxe, tabac, alcool, véhicules
- TCL (Taxe au profit des Collectivités Locales): produits locaux revendus

AVANTAGES FISCAUX ZLECAf:
- Exonération DD avec certificat d'origine ZLECAf (AfCFTA)

RÉGIMES D'IMPORTATION (codes TarifWeb / GUCE):
  LI — Libre importation (sans restriction préalable)
  AI — Autorisation d'Importation (soumis à contrôle ou restriction)
  IN — Importation interdite (prohibition)

FORMALITÉS ADMINISTRATIVES (codes officiels GUCE — Guichet Unique du Commerce Extérieur):
Les codes suivants correspondent aux procédures officielles enregistrées dans le GUCE
(douane.finances.tn) et le portail TarifWeb 2025 pour chaque code NDP :

  910  Déclaration en Douane
       Obligatoire pour toute importation. Document de base soumis à
       la Direction Générale des Douanes Tunisiennes.

  101  Autorisation phytosanitaire — ONAGRI
       Requis pour végétaux, plants, semences, fruits, légumes, fleurs coupées
       et produits d'origine végétale pouvant véhiculer des organismes nuisibles.
       Autorité : ONAGRI (Office National de l'Agriculture) — Direction phytosanitaire.

  102  Certificat sanitaire vétérinaire — DGSV
       Requis pour animaux vivants, viandes, produits laitiers, œufs,
       produits de la pêche et préparations à base de protéines animales.
       Autorité : DGSV (Direction Générale des Services Vétérinaires),
                  Ministère de l'Agriculture.

  103  Autorisation du Ministère de la Santé (médicaments)
       Requis pour médicaments à usage humain, dispositifs médicaux et
       préparations pharmaceutiques soumis à AMM tunisienne.
       Autorité : DPHM (Direction de la Pharmacie et du Médicament),
                  Ministère de la Santé.

  104  Attestation de conformité INNORPI
       Requis pour produits industriels réglementés soumis à une norme
       tunisienne NT obligatoire (électronique, électroménager, jouets,
       matériaux de construction, quincaillerie électrique).
       Autorité : INNORPI (Institut National de la Normalisation et de la
                  Propriété Industrielle).

  105  Déclaration de conformité environnementale — ANPE
       Requis pour produits chimiques dangereux, déchets industriels,
       substances appauvrissant la couche d'ozone (SAO) et produits
       soumis à la convention de Bâle / Rotterdam / Stockholm.
       Autorité : ANPE (Agence Nationale de Protection de l'Environnement).

  106  Autorisation du Ministère du Commerce (produits alimentaires transformés)
       Homologation préalable pour denrées alimentaires transformées
       importées : dossier technique, étiquetage, durée de conservation.
       Autorité : Direction Générale du Commerce Intérieur (DGCI).

  107  Licence d'importation (produits sous restriction quantitative / AI)
       Autorisation préalable pour produits soumis à contingentement,
       mesures de sauvegarde ou restrictions quantitatives (code régime AI).
       Autorité : Ministère du Commerce et de l'Industrie.

  108  Autorisation d'importation hydrocarbures — STEG / ETAP
       Requis pour produits pétroliers et gazeux soumis à monopole partiel
       ou à autorisation d'exploitation.
       Autorité : STEG (Société Tunisienne de l'Electricité et du Gaz)
                  / ETAP (Entreprise Tunisienne d'Activités Pétrolières).

  109  Autorisation du Ministère de l'Intérieur (armes / sécurité)
       Requis pour armes, munitions, explosifs et matériel de sécurité.
       Autorité : Ministère de l'Intérieur de la République Tunisienne.
"""

# =============================================================================
# FORMALITÉS ADMINISTRATIVES PAR CATÉGORIE DE PRODUIT
# Source: GUCE (douane.finances.tn) — codes officiels TarifWeb 2025
# =============================================================================

TUN_FORMALITIES_BY_CATEGORY = {
    # -------------------------------------------------------------------------
    # ANIMAUX VIVANTS ET PRODUITS ANIMAUX (Ch 01-05, 16)
    # Source: code 102 DGSV — certificat sanitaire vétérinaire obligatoire
    # -------------------------------------------------------------------------
    "animal_products": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "102",
            "document_fr": "Certificat sanitaire vétérinaire",
            "document_en": "Veterinary Health Certificate",
            "authority_fr": "DGSV — Direction Générale des Services Vétérinaires (Ministère de l'Agriculture)",
            "authority_en": "DGSV — General Directorate of Veterinary Services (Ministry of Agriculture)",
            "is_mandatory": True,
        },
        {
            "code": "106",
            "document_fr": "Attestation de libre commercialisation / conformité alimentaire",
            "document_en": "Certificate of Free Sale / Food Compliance",
            "authority_fr": "DGCI — Direction Générale du Commerce Intérieur",
            "authority_en": "DGCI — General Directorate of Internal Trade",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # PRODUITS ALIMENTAIRES D'ORIGINE VÉGÉTALE (Ch 06-15, 17-24)
    # Source: code 101 ONAGRI — autorisation phytosanitaire obligatoire
    # -------------------------------------------------------------------------
    "food_agriculture": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "101",
            "document_fr": "Autorisation phytosanitaire et certificat de conformité agricole",
            "document_en": "Phytosanitary Authorization and Agricultural Compliance Certificate",
            "authority_fr": "ONAGRI (Office National de l'Agriculture) — Direction phytosanitaire",
            "authority_en": "ONAGRI (National Agriculture Office) — Phytosanitary Directorate",
            "is_mandatory": True,
        },
        {
            "code": "106",
            "document_fr": "Autorisation d'importation denrées alimentaires (dossier technique)",
            "document_en": "Food Import Authorization (technical file)",
            "authority_fr": "DGCI — Ministère du Commerce et de l'Industrie",
            "authority_en": "DGCI — Ministry of Commerce and Industry",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # MÉDICAMENTS ET DISPOSITIFS MÉDICAUX (Ch 30)
    # Source: code 103 DPHM — autorisation ministérielle obligatoire
    # -------------------------------------------------------------------------
    "pharmaceuticals": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "103",
            "document_fr": "Autorisation d'importation médicaments (AMM tunisienne)",
            "document_en": "Drug Import Authorization (Tunisian AMM)",
            "authority_fr": "DPHM — Direction de la Pharmacie et du Médicament (Ministère de la Santé)",
            "authority_en": "DPHM — Pharmacy and Drug Directorate (Ministry of Health)",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # PRODUITS CHIMIQUES ET ENGRAIS (Ch 28-29, 31-38)
    # Source: code 105 ANPE — déclaration environnementale pour produits dangereux
    # -------------------------------------------------------------------------
    "chemicals": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "105",
            "document_fr": "Déclaration de conformité environnementale",
            "document_en": "Environmental Compliance Declaration",
            "authority_fr": "ANPE (Agence Nationale de Protection de l'Environnement)",
            "authority_en": "ANPE (National Environmental Protection Agency)",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # VÉHICULES ET ÉQUIPEMENTS INDUSTRIELS (Ch 84-87, 90)
    # Source: code 104 INNORPI — conformité norme tunisienne NT obligatoire
    # -------------------------------------------------------------------------
    "vehicles_machinery": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "104",
            "document_fr": "Attestation de conformité aux normes tunisiennes (NT)",
            "document_en": "Certificate of Conformity to Tunisian Standards (NT)",
            "authority_fr": "INNORPI (Institut National de la Normalisation et de la Propriété Industrielle)",
            "authority_en": "INNORPI (National Institute of Standardization and Industrial Property)",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # HYDROCARBURES ET PRODUITS ÉNERGÉTIQUES (Ch 26-27)
    # Source: code 108 STEG/ETAP — autorisation produits pétroliers
    # -------------------------------------------------------------------------
    "hydrocarbons": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "108",
            "document_fr": "Autorisation d'importation hydrocarbures (STEG / ETAP)",
            "document_en": "Hydrocarbons Import Authorization (STEG / ETAP)",
            "authority_fr": "STEG / ETAP — sous tutelle du Ministère de l'Industrie",
            "authority_en": "STEG / ETAP — under Ministry of Industry",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # ARMES, MUNITIONS ET MATÉRIEL DE SÉCURITÉ (Ch 93)
    # Source: code 109 — autorisation Ministère de l'Intérieur obligatoire
    # -------------------------------------------------------------------------
    "arms_security": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "109",
            "document_fr": "Autorisation préalable du Ministère de l'Intérieur (armes / sécurité)",
            "document_en": "Prior Authorization from Ministry of Interior (arms / security)",
            "authority_fr": "Ministère de l'Intérieur de la République Tunisienne",
            "authority_en": "Ministry of Interior of the Republic of Tunisia",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # INTRANTS AGRICOLES (Ch 31 — engrais, Ch 12 — semences)
    # Source: code 101 ONAGRI — homologation intrants obligatoire
    # -------------------------------------------------------------------------
    "agri_inputs": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
        {
            "code": "101",
            "document_fr": "Homologation phytosanitaire / autorisation intrants agricoles",
            "document_en": "Phytosanitary Registration / Agricultural Inputs Authorization",
            "authority_fr": "ONAGRI — Direction des Intrants Agricoles",
            "authority_en": "ONAGRI — Agricultural Inputs Directorate",
            "is_mandatory": True,
        },
    ],

    # -------------------------------------------------------------------------
    # RÉGIME GÉNÉRAL (tous les autres chapitres)
    # -------------------------------------------------------------------------
    "general": [
        {
            "code": "910",
            "document_fr": "Déclaration en Douane",
            "document_en": "Customs Declaration",
            "authority_fr": "Direction Générale des Douanes Tunisiennes",
            "authority_en": "Tunisian General Customs Directorate",
            "is_mandatory": True,
        },
    ],
}


# =============================================================================
# MAPPING CATÉGORIE → FORMALITY_CATEGORY
# Utilise les catégories existantes dans les données TUN enhanced_v2
# =============================================================================

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


def get_tun_formality_category(category: str, chapter: str = "") -> str:
    """
    Map a product category (from enhanced_v2 tariff line) to a formality bucket.

    Args:
        category: The `category` field from the tariff line
        chapter: 2-digit chapter string (used as tiebreaker)

    Returns:
        Formality category key for TUN_FORMALITIES_BY_CATEGORY
    """
    if category in _ANIMAL_CATS:
        return "animal_products"
    if category in _FOOD_AGRI_CATS:
        return "food_agriculture"
    if category in _PHARMA_CATS:
        return "pharmaceuticals"
    if category in _CHEMICAL_CATS:
        if chapter in ("31",):
            return "agri_inputs"
        return "chemicals"
    if category in _VEHICLE_MACH_CATS:
        return "vehicles_machinery"
    if category in _HYDRO_CATS:
        return "hydrocarbons"
    if category in _ARMS_CATS:
        return "arms_security"
    return "general"


def get_tun_formalities_for_line(category: str, chapter: str) -> list:
    """
    Return the list of required administrative documents for a TUN tariff line.

    Args:
        category: enhanced_v2 `category` field
        chapter:  2-digit chapter string

    Returns:
        List of formality dicts (code, document_fr, document_en, authority_fr,
        authority_en, is_mandatory)
    """
    bucket = get_tun_formality_category(category, chapter)
    return TUN_FORMALITIES_BY_CATEGORY.get(bucket, TUN_FORMALITIES_BY_CATEGORY["general"])
