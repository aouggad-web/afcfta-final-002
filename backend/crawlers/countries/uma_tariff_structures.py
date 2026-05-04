"""
UMA/AMU (Union du Maghreb Arabe) Regional Tariff Structures
============================================================
Defines tariff structures for all 7 North African countries covered by the
UMA/AMU regional intelligence system:

  - Algeria  (DZA)  – Import substitution, 3-band structure (0%, 5%, 15%, 30%)
  - Egypt    (EGY)  – Investment Law 72/2017, QIZ zones
  - Libya    (LBY)  – Reconstruction priorities
  - Morocco  (MAR)  – Reference country, most reliable data
  - Tunisia  (TUN)  – EU association agreement, FODEC levy
  - Sudan    (SDN)  – COMESA integration
  - Mauritania (MRT) – ECOWAS transition / hybrid approach

Morocco is used as the reference country for the regional base tariff.

Sources:
  - Morocco   : ADII douane.gov.ma (DI: 2.5–40%, TVA 20%)
  - Algeria   : DGD douane.gov.dz (DD: 0–30%, TVA 19%)
  - Tunisia   : Douane douane.gov.tn (DD: 0–50%)
  - Egypt     : ECA customs.gov.eg (CD: 2–60%, VAT 14%)
  - Libya     : GCC-aligned rates (0–40%)
  - Sudan     : SCTA customs.gov.sd (0–25%, COMESA)
  - Mauritania: DGD douanes.gov.mr (0–20%)
"""

from typing import Dict, List, Any

# =============================================================================
# MOROCCAN BASE TARIFF STRUCTURE (REFERENCE COUNTRY)
# =============================================================================
# Morocco Droit d'Importation (DI) bands – average MFN 12.3% (2024)
# Source: ADII – douane.gov.ma

MOROCCO_TARIFF_BANDS = {
    "0%":    ["25", "26", "27", "30", "31", "86", "88", "89"],      # Raw materials, essentials
    "2.5%":  ["28", "29", "32", "35", "38", "47", "50", "51",
              "52", "53", "54", "55", "56", "58", "59", "60",
              "68", "74", "75", "84", "85", "87", "90"],            # Capital goods, inputs
    "10%":   ["06", "10", "11", "12", "23", "57"],                   # Intermediate goods
    "17.5%": ["01", "02", "03", "07", "08", "09", "15", "39",
              "40", "42", "44", "48", "69", "70", "72", "73",
              "76", "82", "83"],                                     # Consumer goods
    "25%":   ["04", "16", "17", "19", "20", "21", "33", "61",
              "62", "63", "64", "94", "95"],                         # Finished consumer goods
    "40%":   ["22", "24"],                                           # Alcohol, tobacco
}

# Moroccan taxes (all positions)
MOROCCO_FIXED_TAXES = {
    "TPI": {
        "code": "TPI",
        "name": "Taxe Parafiscale à l'Importation",
        "rate": 0.25,
        "type": "ad_valorem",
        "base": "CIF",
    },
    "TVA": {
        "code": "TVA",
        "name": "Taxe sur la Valeur Ajoutée",
        "standard_rate": 20.0,
        "reduced_rates": [7.0, 10.0, 14.0],
        "type": "ad_valorem",
        "base": "CIF + DI + TPI",
    },
}

MOROCCO_PREFERENTIAL = [
    "EU Association Agreement (0% on most industrial goods)",
    "US Free Trade Agreement",
    "GAFTA Arab Free Trade Area",
    "Agadir Agreement (with TUN, EGY, JOR)",
    "AfCFTA",
    "EFTA Agreement",
    "Turkey Agreement",
]

MOROCCO_SPECIAL_ZONES = [
    {"name": "Zone Franche de Tanger-Med", "location": "Tanger", "benefit": "Customs-free"},
    {"name": "Casablanca Finance City", "location": "Casablanca", "benefit": "Financial hub"},
    {"name": "Zone Franche d'Ait Melloul", "location": "Agadir", "benefit": "Industrial free zone"},
]

# =============================================================================
# COUNTRY-SPECIFIC CONFIGURATIONS
# =============================================================================

UMA_COUNTRY_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------------------------------
    # ALGERIA (DZA)
    # DD: 0%, 5%, 15%, 30%  TVA: 19%  DAPS on 1 095 products
    # Policy: Import substitution, protects local industry
    # ------------------------------------------------------------------
    "DZA": {
        "country": "DZA",
        "country_name": "Algeria",
        "country_name_fr": "Algérie",
        "source": "Direction Générale des Douanes (DGD)",
        "source_url": "https://www.douane.gov.dz",
        "currency": "DZD (Dinar Algérien)",
        "vat_rate": 19.0,
        "vat_name": "Taxe sur la Valeur Ajoutée",
        "vat_base": "CIF + DD",
        "tariff_bands": {
            "0%":  ["25", "26", "27", "28", "29", "30", "31"],
            "5%":  ["01", "02", "03", "06", "07", "08", "09", "10",
                    "11", "12", "13", "14", "15", "23", "35", "36",
                    "37", "38", "39", "40", "41", "43", "44", "45",
                    "46", "47", "48", "49", "50", "51", "52", "53",
                    "54", "55", "56", "57", "58", "59", "60", "66",
                    "67", "68", "72", "73", "74", "75", "76", "78",
                    "79", "80", "81", "82", "83", "84", "85", "86",
                    "87", "88", "89", "90", "93"],
            "15%": ["05", "32", "65", "69", "70", "71"],
            "30%": ["04", "16", "17", "18", "19", "20", "21", "22",
                    "24", "33", "34", "42", "61", "62", "63", "64",
                    "91", "92", "94", "95", "96"],
        },
        "national_taxes": {
            "TSS": {
                "code": "TSS",
                "name": "Taxe de Solidarité Sociale",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "special_policy": "import_substitution",
        "special_zones": [],
        "preferential_agreements": [
            "GAFTA (Arab Free Trade Area)",
            "EU Association Agreement (transitional)",
            "AfCFTA",
        ],
        "notes": [
            "DD bands: 0%, 5%, 15%, 30% (4 taux principaux)",
            "DAPS (Droit Additionnel Provisoire de Sauvegarde): 30–200% sur 1 095 produits",
            "Politique d'import-substitution: restrictions sur 900+ produits",
            "TVA 19% (taux standard), 9% (réduit pour médicaments et alimentation de base)",
            "TSS 1% sur la plupart des importations",
        ],
    },
    # ------------------------------------------------------------------
    # EGYPT (EGY)
    # CD: 2%–60%  VAT: 14%  QIZ zones, Investment Law 72/2017
    # Policy: Market liberalisation, industrial investment
    # ------------------------------------------------------------------
    "EGY": {
        "country": "EGY",
        "country_name": "Egypt",
        "country_name_fr": "Égypte",
        "source": "Egyptian Customs Authority (ECA)",
        "source_url": "https://www.customs.gov.eg",
        "currency": "EGP (Livre Égyptienne)",
        "vat_rate": 14.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + CD",
        "tariff_bands": {
            "0%":  [],
            "2%":  ["01", "02", "03", "06", "07", "08", "09", "10",
                    "11", "12", "15", "23", "25", "26", "27", "28",
                    "29", "30", "31", "32", "35", "38", "47"],
            "5%":  ["84", "85", "86", "88", "89", "90"],
            "12%": ["50", "51", "52", "53", "54", "55", "56", "58",
                    "59", "60", "68", "74", "75"],
            "22%": ["39", "40", "44", "48", "57", "72", "73", "76",
                    "82", "83"],
            "30%": ["04", "16", "17", "19", "20", "21", "42", "63",
                    "65", "69", "70", "87", "94"],
            "40%": ["33", "61", "62", "64", "71", "91", "95"],
            "60%": ["22", "24"],
        },
        "national_taxes": {
            "SALESTAX": {
                "code": "ST",
                "name": "Sales Tax (additional on some products)",
                "rate": 0.0,
                "type": "variable",
                "base": "CIF + CD",
                "note": "Applied to specific goods per ECA schedule",
            },
        },
        "special_policy": "qiz_investment_law",
        "special_zones": [
            {"name": "SCZONE (Suez Canal Zone)", "location": "Suez Canal corridor",
             "benefit": "5% flat customs rate, VAT exemption on inputs"},
            {"name": "QIZ Zones", "location": "Cairo, Alexandria, Port Said",
             "benefit": "0% US tariff if ≥10.5% Israeli content"},
            {"name": "New Capital SEZ", "location": "New Administrative Capital",
             "benefit": "Tax incentives, 10% flat income tax"},
        ],
        "preferential_agreements": [
            "EU Association Agreement (EuroMed)",
            "US QIZ Agreement (textile quota-free)",
            "GAFTA",
            "COMESA",
            "Agadir Agreement",
            "AfCFTA",
        ],
        "notes": [
            "Investment Law 72/2017: 50% tax deduction for 7 years in Upper Egypt",
            "QIZ: US tariff-free for textile/apparel with ≥10.5% Israeli input",
            "SCZONE: Strategic location on Suez Canal (12% of world trade)",
            "COMESA: 0% on intra-COMESA goods with CoO",
        ],
    },
    # ------------------------------------------------------------------
    # LIBYA (LBY)
    # DD: 0%–40%  No VAT  Reconstruction-focused
    # Policy: Post-conflict reconstruction, basic needs
    # ------------------------------------------------------------------
    "LBY": {
        "country": "LBY",
        "country_name": "Libya",
        "country_name_fr": "Libye",
        "source": "Libyan Customs Authority",
        "source_url": "https://customs.ly",
        "currency": "LYD (Dinar Libyen)",
        "vat_rate": 0.0,
        "vat_name": "No VAT",
        "vat_base": "N/A",
        "tariff_bands": {
            "0%":  ["06", "10", "11", "12", "23", "32", "35", "38",
                    "47", "50", "51", "52", "53", "54", "55", "56",
                    "58", "59", "60", "68", "74", "75"],
            "5%":  ["25", "26", "27", "28", "29", "30", "31", "84",
                    "85", "86", "87", "88", "89", "90"],
            "15%": ["01", "02", "03", "07", "08", "09", "15", "39",
                    "40", "42", "44", "48", "57", "69", "70", "72",
                    "73", "76", "82", "83"],
            "25%": ["04", "16", "17", "19", "20", "21", "33", "61",
                    "62", "63", "64", "94", "95"],
            "40%": ["22", "24"],
        },
        "national_taxes": {
            "TS": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 0.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "special_policy": "reconstruction_priorities",
        "special_zones": [
            {"name": "Misurata Free Zone", "location": "Misurata",
             "benefit": "Customs exemption for reconstruction materials"},
        ],
        "preferential_agreements": [
            "GAFTA",
            "COMESA",
            "AfCFTA",
        ],
        "notes": [
            "Pas de TVA appliquée en Libye",
            "Exemptions douanières larges pour les équipements de reconstruction",
            "Instabilité politique – vérifier auprès des autorités locales",
            "TS (Taxe Statistique) 0.5% sur CIF",
        ],
    },
    # ------------------------------------------------------------------
    # MOROCCO (MAR) – Reference country
    # DI: 0%–40%  TVA: 20%  TPI: 0.25%
    # Policy: Industrial acceleration plan
    # ------------------------------------------------------------------
    "MAR": {
        "country": "MAR",
        "country_name": "Morocco",
        "country_name_fr": "Maroc",
        "source": "ADII – Administration des Douanes et Impôts Indirects",
        "source_url": "https://www.douane.gov.ma",
        "currency": "MAD (Dirham Marocain)",
        "vat_rate": 20.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DI + TPI",
        "tariff_bands": MOROCCO_TARIFF_BANDS,
        "national_taxes": {
            "TPI": MOROCCO_FIXED_TAXES["TPI"],
        },
        "special_policy": "industrial_acceleration_plan",
        "special_zones": MOROCCO_SPECIAL_ZONES,
        "preferential_agreements": MOROCCO_PREFERENTIAL,
        "notes": [
            "DI (Droit d'Importation): 0%, 2.5%, 10%, 17.5%, 25%, 40%",
            "TPI: 0.25% sur CIF pour la plupart des produits",
            "TVA: 20% (taux normal), taux réduits: 7%, 10%, 14%",
            "Plan d'Accélération Industrielle: secteur automobile, aéronautique",
            "Tanger-Med: premier port d'Afrique par capacité de conteneurs",
        ],
    },
    # ------------------------------------------------------------------
    # TUNISIA (TUN)
    # DD: 0%–50%  TVA: 19%  FODEC: 1%
    # Policy: EU association agreement, DCFTA negotiations
    # ------------------------------------------------------------------
    "TUN": {
        "country": "TUN",
        "country_name": "Tunisia",
        "country_name_fr": "Tunisie",
        "source": "Direction Générale des Douanes de Tunisie",
        "source_url": "https://www.douane.gov.tn",
        "currency": "TND (Dinar Tunisien)",
        "vat_rate": 19.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DD + FODEC",
        "tariff_bands": {
            "0%":  ["25", "26", "27", "28", "29", "30", "31"],
            "10%": ["06", "10", "11", "12", "23", "32", "35", "38",
                    "47", "50", "51", "52", "53", "54", "55", "56",
                    "58", "59", "60", "68", "74", "75", "84", "85",
                    "86", "88", "89", "90"],
            "20%": ["01", "02", "03", "07", "08", "09", "15", "39",
                    "40", "44", "48", "57", "72", "73", "76", "82",
                    "83", "87"],
            "30%": ["42", "63", "65", "69", "70"],
            "36%": ["04", "16", "17", "19", "20", "21", "71", "91",
                    "95"],
            "43%": ["33", "61", "62", "64", "94"],
            "50%": ["22", "24"],
        },
        "national_taxes": {
            "FODEC": {
                "code": "FODEC",
                "name": "Fonds de Développement de la Compétitivité",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "DCE": {
                "code": "DCE",
                "name": "Droit de Consommation Élevé (Excise)",
                "rate": 0.0,
                "type": "variable",
                "base": "CIF + DD",
                "note": "Applicable sur alcool, tabac, véhicules de luxe",
            },
        },
        "special_policy": "eu_association_agreement",
        "special_zones": [
            {"name": "Zone Franche de Bizerte", "location": "Bizerte",
             "benefit": "Exonération DD, TVA, IS sur 10 ans"},
            {"name": "Parcs de Technologie de Sousse", "location": "Sousse",
             "benefit": "Incitations pour le secteur ICT"},
        ],
        "preferential_agreements": [
            "EU Association Agreement (Accord d'Association – 0% industriel)",
            "GAFTA",
            "Agadir Agreement",
            "AfCFTA",
            "EFTA Agreement",
        ],
        "notes": [
            "DD: jusqu'à 200% sur alcool/tabac; taux courant 0–50%",
            "FODEC: 1% sur CIF (sauf produits exemptés)",
            "TVA: 19% (taux normal), 13% (taux réduit), 7% (taux réduit spécial)",
            "Accord UE: 0% sur 90% des produits industriels depuis 2008",
            "Négociations DCFTA UE-Tunisie en cours",
        ],
    },
    # ------------------------------------------------------------------
    # SUDAN (SDN)
    # CD: 0%–25%  VAT: 17%  COMESA integration
    # Policy: COMESA integration, Port Sudan gateway
    # ------------------------------------------------------------------
    "SDN": {
        "country": "SDN",
        "country_name": "Sudan",
        "country_name_fr": "Soudan",
        "source": "Sudan Customs and Tax Authority (SCTA)",
        "source_url": "https://www.customs.gov.sd",
        "currency": "SDG (Livre Soudanaise)",
        "vat_rate": 17.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + CD",
        "tariff_bands": {
            "0%":  ["25", "26", "27", "28", "29", "30", "31", "84",
                    "85", "86", "88", "89", "90"],
            "10%": ["06", "10", "11", "12", "23", "32", "35", "38",
                    "47", "50", "51", "52", "53", "54", "55", "56",
                    "58", "59", "60", "68", "74", "75"],
            "20%": ["01", "02", "03", "04", "07", "08", "09", "15",
                    "16", "17", "19", "20", "21", "39", "40", "42",
                    "44", "48", "57", "63", "65", "69", "70", "72",
                    "73", "76", "82", "83", "87"],
            "25%": ["22", "24", "33", "61", "62", "64", "71", "91",
                    "94", "95"],
        },
        "national_taxes": {
            "DS": {
                "code": "DS",
                "name": "Development Surcharge",
                "rate": 2.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "special_policy": "comesa_integration",
        "special_zones": [
            {"name": "Port Sudan Free Zone", "location": "Port Sudan",
             "benefit": "Free trade zone, customs exemption on inputs"},
        ],
        "preferential_agreements": [
            "COMESA (0% intra-COMESA avec CoO)",
            "GAFTA",
            "AfCFTA",
        ],
        "notes": [
            "CD bands: 0%, 10%, 20%, 25%",
            "Development Surcharge (DS): 2% sur CIF",
            "COMESA: 0% pour les membres avec Certificat d'Origine",
            "Port Sudan: point d'entrée stratégique Mer Rouge",
            "Instabilité politique – confirmer les taux auprès des douanes locales",
        ],
    },
    # ------------------------------------------------------------------
    # MAURITANIA (MRT)
    # DD: 0%–20%  TVA: 16%  ECOWAS transition / UMA hybrid
    # Policy: Fishing/mining economy, ECOWAS observer
    # ------------------------------------------------------------------
    "MRT": {
        "country": "MRT",
        "country_name": "Mauritania",
        "country_name_fr": "Mauritanie",
        "source": "Direction Générale des Douanes (DGD Mauritanie)",
        "source_url": "https://www.douanes.gov.mr",
        "currency": "MRU (Ouguiya)",
        "vat_rate": 16.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DD",
        "tariff_bands": {
            "0%":  ["25", "26", "27", "28", "29", "30", "31", "84",
                    "85", "86", "88", "89", "90"],
            "5%":  ["06", "10", "11", "12", "23", "32", "35", "38",
                    "47", "50", "51", "52", "53", "54", "55", "56",
                    "58", "59", "60", "68", "74", "75", "87"],
            "10%": ["01", "02", "03", "07", "08", "09", "15", "39",
                    "40", "44", "48", "57", "72", "73", "76", "82",
                    "83"],
            "15%": ["04", "16", "17", "19", "20", "21", "42", "63",
                    "69", "70", "71"],
            "20%": ["22", "24", "33", "61", "62", "64", "94", "95"],
        },
        "national_taxes": {
            "TS": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "special_policy": "ecowas_transition",
        "special_zones": [],
        "preferential_agreements": [
            "GAFTA",
            "AfCFTA",
            "UMA/AMU",
        ],
        "notes": [
            "Membre UMA et observateur CEDEAO",
            "DD: 0%, 5%, 10%, 15%, 20% (5 taux)",
            "TVA: 16%",
            "TS: 1% sur CIF (Taxe Statistique)",
            "Économie basée sur pêche, mines de fer (SNIM), hydrocarbures",
        ],
    },
}

# =============================================================================
# UMA REGIONAL PREFERENTIAL AGREEMENTS
# =============================================================================

UMA_REGIONAL_AGREEMENTS = {
    "GAFTA": {
        "name": "Greater Arab Free Trade Area",
        "members": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"],
        "rate": "0% on most goods",
        "coverage": "Arabic-origin goods with valid CoO",
    },
    "AfCFTA": {
        "name": "African Continental Free Trade Area",
        "members": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"],
        "rate": "Progressive reduction to 0% (90% of lines in 5-10 years)",
        "coverage": "Pan-African goods",
    },
    "Agadir": {
        "name": "Agadir Agreement",
        "members": ["MAR", "TUN", "EGY"],
        "rate": "0% between members",
        "coverage": "Industrial and agricultural goods with EU rules of origin",
    },
    "EU_Association": {
        "name": "EU Association Agreements (EuroMed)",
        "members": ["MAR", "TUN", "EGY"],
        "rate": "0% on industrial goods (phased)",
        "coverage": "Industrial goods, partial agricultural",
    },
    "COMESA": {
        "name": "Common Market for Eastern & Southern Africa",
        "members": ["EGY", "LBY", "SDN"],
        "rate": "0% for COMESA members with CoO",
        "coverage": "Goods originating in COMESA",
    },
    "US_QIZ": {
        "name": "Qualifying Industrial Zones (QIZ)",
        "members": ["EGY"],
        "rate": "0% US tariff on textile/apparel",
        "coverage": "Textiles/apparel with ≥10.5% Israeli content",
    },
    "US_FTA": {
        "name": "US Free Trade Agreement",
        "members": ["MAR"],
        "rate": "0% (phased from 2006)",
        "coverage": "Most goods",
    },
}

# =============================================================================
# UMA VAT RATES QUICK REFERENCE
# =============================================================================

UMA_VAT_RATES: Dict[str, float] = {
    "DZA": 19.0,
    "EGY": 14.0,
    "LBY":  0.0,   # No VAT in Libya
    "MAR": 20.0,
    "TUN": 19.0,
    "SDN": 17.0,
    "MRT": 16.0,
}

# =============================================================================
# ALL 7 UMA COUNTRIES
# =============================================================================

UMA_COUNTRIES: List[str] = ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"]
