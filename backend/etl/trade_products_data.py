"""
Données Commerce Africain - Top Produits Import/Export
========================================================
Sources:
- UNCTAD COMTRADE Database 2023-2024
- OEC/BACI Database 2024
- African Development Bank Trade Statistics
- ITC Trade Map 2024

Classification: HS Code (Système Harmonisé)
Mise à jour: 2024 (données 2023 conservées pour comparatif)
"""

from typing import Dict, List

# =============================================================================
# TOP 20 PRODUITS IMPORTÉS PAR L'AFRIQUE DU MONDE
# Source: UNCTAD/ITC Trade Map 2024 + OEC/BACI 2024
# =============================================================================

TOP_20_IMPORTS_FROM_WORLD = [
    {
        "rank": 1,
        "hs_code": "2710",
        "product": "Huiles de pétrole raffinées",
        "value_mln_usd": 72500,
        "share_percent": 12.8,
        "main_origins": ["Inde", "Arabie Saoudite", "Pays-Bas", "Chine"],
        "growth_2023_2024": 8.5,
        "top_importers": ["Afrique du Sud", "Nigéria", "Égypte", "Kenya"]
    },
    {
        "rank": 2,
        "hs_code": "8517",
        "product": "Téléphones et équipements de télécommunication",
        "value_mln_usd": 28500,
        "share_percent": 5.0,
        "main_origins": ["Chine", "Vietnam", "Corée du Sud", "Inde"],
        "growth_2023_2024": 12.3,
        "top_importers": ["Égypte", "Afrique du Sud", "Nigéria", "Maroc"]
    },
    {
        "rank": 3,
        "hs_code": "1001",
        "product": "Blé et méteil",
        "value_mln_usd": 22800,
        "share_percent": 4.0,
        "main_origins": ["Russie", "Ukraine", "France", "Canada"],
        "growth_2023_2024": 15.2,
        "top_importers": ["Égypte", "Algérie", "Nigéria", "Maroc"]
    },
    {
        "rank": 4,
        "hs_code": "8703",
        "product": "Véhicules automobiles",
        "value_mln_usd": 18500,
        "share_percent": 3.3,
        "main_origins": ["Japon", "Allemagne", "Chine", "Corée du Sud"],
        "growth_2023_2024": 6.8,
        "top_importers": ["Afrique du Sud", "Égypte", "Algérie", "Kenya"]
    },
    {
        "rank": 5,
        "hs_code": "8471",
        "product": "Machines automatiques de traitement de données (ordinateurs)",
        "value_mln_usd": 12800,
        "share_percent": 2.3,
        "main_origins": ["Chine", "États-Unis", "Pays-Bas", "Allemagne"],
        "growth_2023_2024": 9.5,
        "top_importers": ["Afrique du Sud", "Égypte", "Maroc", "Nigéria"]
    },
    {
        "rank": 6,
        "hs_code": "3004",
        "product": "Médicaments",
        "value_mln_usd": 12200,
        "share_percent": 2.2,
        "main_origins": ["Inde", "France", "Allemagne", "États-Unis"],
        "growth_2023_2024": 11.2,
        "top_importers": ["Afrique du Sud", "Algérie", "Égypte", "Nigéria"]
    },
    {
        "rank": 7,
        "hs_code": "1006",
        "product": "Riz",
        "value_mln_usd": 11500,
        "share_percent": 2.0,
        "main_origins": ["Inde", "Thaïlande", "Pakistan", "Vietnam"],
        "growth_2023_2024": 18.5,
        "top_importers": ["Côte d'Ivoire", "Sénégal", "Afrique du Sud", "Ghana"]
    },
    {
        "rank": 8,
        "hs_code": "8704",
        "product": "Véhicules pour transport de marchandises",
        "value_mln_usd": 9800,
        "share_percent": 1.7,
        "main_origins": ["Japon", "Chine", "Allemagne", "Inde"],
        "growth_2023_2024": 7.2,
        "top_importers": ["Afrique du Sud", "Algérie", "Égypte", "Éthiopie"]
    },
    {
        "rank": 9,
        "hs_code": "1507",
        "product": "Huile de soja",
        "value_mln_usd": 8500,
        "share_percent": 1.5,
        "main_origins": ["Argentine", "Brésil", "États-Unis", "Paraguay"],
        "growth_2023_2024": 5.8,
        "top_importers": ["Égypte", "Algérie", "Maroc", "Tunisie"]
    },
    {
        "rank": 10,
        "hs_code": "1701",
        "product": "Sucre de canne ou de betterave",
        "value_mln_usd": 7800,
        "share_percent": 1.4,
        "main_origins": ["Brésil", "Inde", "Thaïlande", "Guatemala"],
        "growth_2023_2024": 12.5,
        "top_importers": ["Algérie", "Égypte", "Nigéria", "Soudan"]
    },
    {
        "rank": 11,
        "hs_code": "7207",
        "product": "Produits semi-finis en fer ou acier",
        "value_mln_usd": 7200,
        "share_percent": 1.3,
        "main_origins": ["Chine", "Turquie", "Russie", "Ukraine"],
        "growth_2023_2024": 3.2,
        "top_importers": ["Égypte", "Algérie", "Afrique du Sud", "Maroc"]
    },
    {
        "rank": 12,
        "hs_code": "1511",
        "product": "Huile de palme",
        "value_mln_usd": 6800,
        "share_percent": 1.2,
        "main_origins": ["Indonésie", "Malaisie", "Côte d'Ivoire", "Colombie"],
        "growth_2023_2024": 8.9,
        "top_importers": ["Égypte", "Kenya", "Tanzanie", "Afrique du Sud"]
    },
    {
        "rank": 13,
        "hs_code": "8411",
        "product": "Turbines à gaz",
        "value_mln_usd": 6500,
        "share_percent": 1.1,
        "main_origins": ["États-Unis", "Allemagne", "Royaume-Uni", "France"],
        "growth_2023_2024": 22.5,
        "top_importers": ["Égypte", "Algérie", "Nigéria", "Angola"]
    },
    {
        "rank": 14,
        "hs_code": "3102",
        "product": "Engrais azotés",
        "value_mln_usd": 5800,
        "share_percent": 1.0,
        "main_origins": ["Russie", "Chine", "Égypte", "Qatar"],
        "growth_2023_2024": 15.8,
        "top_importers": ["Afrique du Sud", "Éthiopie", "Kenya", "Maroc"]
    },
    {
        "rank": 15,
        "hs_code": "1005",
        "product": "Maïs",
        "value_mln_usd": 5500,
        "share_percent": 1.0,
        "main_origins": ["Argentine", "Brésil", "États-Unis", "Ukraine"],
        "growth_2023_2024": 25.3,
        "top_importers": ["Égypte", "Algérie", "Kenya", "Maroc"]
    },
    {
        "rank": 16,
        "hs_code": "8429",
        "product": "Bulldozers, niveleuses, pelles mécaniques",
        "value_mln_usd": 5200,
        "share_percent": 0.9,
        "main_origins": ["Chine", "Japon", "États-Unis", "Allemagne"],
        "growth_2023_2024": 8.7,
        "top_importers": ["Afrique du Sud", "Égypte", "Algérie", "RD Congo"]
    },
    {
        "rank": 17,
        "hs_code": "8544",
        "product": "Fils et câbles électriques",
        "value_mln_usd": 4800,
        "share_percent": 0.8,
        "main_origins": ["Chine", "Turquie", "Allemagne", "Italie"],
        "growth_2023_2024": 6.5,
        "top_importers": ["Égypte", "Afrique du Sud", "Algérie", "Maroc"]
    },
    {
        "rank": 18,
        "hs_code": "0402",
        "product": "Lait et crème concentrés",
        "value_mln_usd": 4500,
        "share_percent": 0.8,
        "main_origins": ["Nouvelle-Zélande", "Pays-Bas", "Irlande", "France"],
        "growth_2023_2024": 9.2,
        "top_importers": ["Algérie", "Nigéria", "Sénégal", "Côte d'Ivoire"]
    },
    {
        "rank": 19,
        "hs_code": "2701",
        "product": "Houilles et combustibles solides",
        "value_mln_usd": 4200,
        "share_percent": 0.7,
        "main_origins": ["Russie", "Colombie", "Australie", "Afrique du Sud"],
        "growth_2023_2024": -5.2,
        "top_importers": ["Maroc", "Égypte", "Tunisie", "Sénégal"]
    },
    {
        "rank": 20,
        "hs_code": "8502",
        "product": "Groupes électrogènes",
        "value_mln_usd": 3900,
        "share_percent": 0.7,
        "main_origins": ["Chine", "États-Unis", "Allemagne", "Royaume-Uni"],
        "growth_2023_2024": 14.5,
        "top_importers": ["Nigéria", "Angola", "RD Congo", "Ghana"]
    },
]

# =============================================================================
# TOP 20 PRODUITS EXPORTÉS PAR L'AFRIQUE VERS LE MONDE
# Source: UNCTAD/ITC Trade Map 2024 + OEC/BACI 2024
# =============================================================================

TOP_20_EXPORTS_TO_WORLD = [
    {
        "rank": 1,
        "hs_code": "2709",
        "product": "Huiles brutes de pétrole",
        "value_mln_usd": 125000,
        "share_percent": 22.5,
        "main_destinations": ["Chine", "Inde", "Espagne", "Italie"],
        "growth_2023_2024": 5.2,
        "top_exporters": ["Nigéria", "Angola", "Algérie", "Libye"]
    },
    {
        "rank": 2,
        "hs_code": "2711",
        "product": "Gaz naturel (GNL et gazoduc)",
        "value_mln_usd": 52000,
        "share_percent": 9.4,
        "main_destinations": ["Espagne", "Italie", "France", "Turquie"],
        "growth_2023_2024": 18.5,
        "top_exporters": ["Algérie", "Nigéria", "Égypte", "Guinée Équatoriale"]
    },
    {
        "rank": 3,
        "hs_code": "7108",
        "product": "Or",
        "value_mln_usd": 38500,
        "share_percent": 6.9,
        "main_destinations": ["Suisse", "Émirats Arabes Unis", "Inde", "Royaume-Uni"],
        "growth_2023_2024": 12.8,
        "top_exporters": ["Afrique du Sud", "Ghana", "Mali", "Burkina Faso"]
    },
    {
        "rank": 4,
        "hs_code": "7102",
        "product": "Diamants",
        "value_mln_usd": 18500,
        "share_percent": 3.3,
        "main_destinations": ["Belgique", "Émirats Arabes Unis", "Inde", "Israël"],
        "growth_2023_2024": -2.5,
        "top_exporters": ["Botswana", "Angola", "Afrique du Sud", "RD Congo"]
    },
    {
        "rank": 5,
        "hs_code": "1801",
        "product": "Cacao en fèves",
        "value_mln_usd": 15800,
        "share_percent": 2.8,
        "main_destinations": ["Pays-Bas", "États-Unis", "Allemagne", "Belgique"],
        "growth_2023_2024": 35.2,
        "top_exporters": ["Côte d'Ivoire", "Ghana", "Cameroun", "Nigéria"]
    },
    {
        "rank": 6,
        "hs_code": "2601",
        "product": "Minerais de fer",
        "value_mln_usd": 12500,
        "share_percent": 2.3,
        "main_destinations": ["Chine", "Japon", "Corée du Sud", "Allemagne"],
        "growth_2023_2024": 8.5,
        "top_exporters": ["Afrique du Sud", "Mauritanie", "Libéria", "Sierra Leone"]
    },
    {
        "rank": 7,
        "hs_code": "2603",
        "product": "Minerais de cuivre",
        "value_mln_usd": 11800,
        "share_percent": 2.1,
        "main_destinations": ["Chine", "Japon", "Inde", "Espagne"],
        "growth_2023_2024": 15.2,
        "top_exporters": ["RD Congo", "Zambie", "Afrique du Sud", "Maroc"]
    },
    {
        "rank": 8,
        "hs_code": "2710",
        "product": "Huiles de pétrole raffinées",
        "value_mln_usd": 10500,
        "share_percent": 1.9,
        "main_destinations": ["Espagne", "Pays-Bas", "France", "États-Unis"],
        "growth_2023_2024": 6.8,
        "top_exporters": ["Algérie", "Égypte", "Afrique du Sud", "Nigéria"]
    },
    {
        "rank": 9,
        "hs_code": "0901",
        "product": "Café",
        "value_mln_usd": 8500,
        "share_percent": 1.5,
        "main_destinations": ["Allemagne", "États-Unis", "Belgique", "Italie"],
        "growth_2023_2024": 22.5,
        "top_exporters": ["Éthiopie", "Ouganda", "Côte d'Ivoire", "Kenya"]
    },
    {
        "rank": 10,
        "hs_code": "3104",
        "product": "Engrais potassiques",
        "value_mln_usd": 7800,
        "share_percent": 1.4,
        "main_destinations": ["Brésil", "Inde", "États-Unis", "Chine"],
        "growth_2023_2024": 28.5,
        "top_exporters": ["Maroc", "Égypte", "Tunisie", "Algérie"]
    },
    {
        "rank": 11,
        "hs_code": "8703",
        "product": "Véhicules automobiles",
        "value_mln_usd": 7200,
        "share_percent": 1.3,
        "main_destinations": ["Europe", "Japon", "États-Unis", "Afrique"],
        "growth_2023_2024": 8.9,
        "top_exporters": ["Afrique du Sud", "Maroc", "Égypte"]
    },
    {
        "rank": 12,
        "hs_code": "0803",
        "product": "Bananes",
        "value_mln_usd": 6500,
        "share_percent": 1.2,
        "main_destinations": ["Europe", "Moyen-Orient", "Russie"],
        "growth_2023_2024": 5.2,
        "top_exporters": ["Côte d'Ivoire", "Cameroun", "Ghana", "Égypte"]
    },
    {
        "rank": 13,
        "hs_code": "2606",
        "product": "Minerais de bauxite et aluminium",
        "value_mln_usd": 6200,
        "share_percent": 1.1,
        "main_destinations": ["Chine", "Irlande", "Espagne", "Canada"],
        "growth_2023_2024": 12.5,
        "top_exporters": ["Guinée", "Ghana", "Sierra Leone", "Mozambique"]
    },
    {
        "rank": 14,
        "hs_code": "0805",
        "product": "Agrumes",
        "value_mln_usd": 5800,
        "share_percent": 1.0,
        "main_destinations": ["Russie", "Pays-Bas", "Royaume-Uni", "France"],
        "growth_2023_2024": 8.5,
        "top_exporters": ["Afrique du Sud", "Égypte", "Maroc", "Zimbabwe"]
    },
    {
        "rank": 15,
        "hs_code": "0902",
        "product": "Thé",
        "value_mln_usd": 5500,
        "share_percent": 1.0,
        "main_destinations": ["Pakistan", "Égypte", "Royaume-Uni", "Afghanistan"],
        "growth_2023_2024": 6.2,
        "top_exporters": ["Kenya", "Ouganda", "Malawi", "Rwanda"]
    },
    {
        "rank": 16,
        "hs_code": "0804",
        "product": "Dattes, figues, ananas, avocats",
        "value_mln_usd": 4800,
        "share_percent": 0.9,
        "main_destinations": ["Europe", "Inde", "Moyen-Orient"],
        "growth_2023_2024": 15.8,
        "top_exporters": ["Tunisie", "Algérie", "Égypte", "Kenya"]
    },
    {
        "rank": 17,
        "hs_code": "5201",
        "product": "Coton",
        "value_mln_usd": 4500,
        "share_percent": 0.8,
        "main_destinations": ["Bangladesh", "Vietnam", "Chine", "Turquie"],
        "growth_2023_2024": -8.5,
        "top_exporters": ["Mali", "Bénin", "Burkina Faso", "Côte d'Ivoire"]
    },
    {
        "rank": 18,
        "hs_code": "2608",
        "product": "Minerais de zinc",
        "value_mln_usd": 4200,
        "share_percent": 0.8,
        "main_destinations": ["Chine", "Corée du Sud", "Japon", "Inde"],
        "growth_2023_2024": 5.5,
        "top_exporters": ["Afrique du Sud", "Namibie", "RD Congo", "Maroc"]
    },
    {
        "rank": 19,
        "hs_code": "0306",
        "product": "Crustacés (crevettes, homards)",
        "value_mln_usd": 3800,
        "share_percent": 0.7,
        "main_destinations": ["Espagne", "France", "Portugal", "Italie"],
        "growth_2023_2024": 12.2,
        "top_exporters": ["Mozambique", "Madagascar", "Sénégal", "Tanzanie"]
    },
    {
        "rank": 20,
        "hs_code": "0801",
        "product": "Noix de cajou",
        "value_mln_usd": 3500,
        "share_percent": 0.6,
        "main_destinations": ["Vietnam", "Inde", "Pays-Bas", "États-Unis"],
        "growth_2023_2024": 18.5,
        "top_exporters": ["Côte d'Ivoire", "Tanzanie", "Guinée-Bissau", "Mozambique"]
    },
]

# =============================================================================
# TOP 20 PRODUITS ÉCHANGÉS EN COMMERCE INTRA-AFRICAIN (IMPORTATIONS)
# Source: UNCTAD/AfCFTA Secretariat 2024
# =============================================================================

TOP_20_INTRA_AFRICAN_IMPORTS = [
    {
        "rank": 1,
        "hs_code": "2710",
        "product": "Huiles de pétrole raffinées",
        "value_mln_usd": 8500,
        "share_percent": 12.5,
        "main_origins": ["Afrique du Sud", "Algérie", "Égypte", "Nigéria"],
        "growth_2023_2024": 8.2,
        "top_importers": ["Zimbabwe", "Zambie", "Botswana", "Mozambique"]
    },
    {
        "rank": 2,
        "hs_code": "2716",
        "product": "Énergie électrique",
        "value_mln_usd": 4200,
        "share_percent": 6.2,
        "main_origins": ["Afrique du Sud", "Mozambique", "Zambie", "Éthiopie"],
        "growth_2023_2024": 15.5,
        "top_importers": ["Zimbabwe", "Botswana", "Namibie", "Lesotho"]
    },
    {
        "rank": 3,
        "hs_code": "8703",
        "product": "Véhicules automobiles",
        "value_mln_usd": 3800,
        "share_percent": 5.6,
        "main_origins": ["Afrique du Sud", "Maroc", "Égypte"],
        "growth_2023_2024": 12.8,
        "top_importers": ["Zimbabwe", "Zambie", "Kenya", "Ghana"]
    },
    {
        "rank": 4,
        "hs_code": "1701",
        "product": "Sucre de canne",
        "value_mln_usd": 2800,
        "share_percent": 4.1,
        "main_origins": ["Eswatini", "Afrique du Sud", "Zimbabwe", "Mozambique"],
        "growth_2023_2024": 9.5,
        "top_importers": ["Kenya", "RD Congo", "Soudan", "Tanzanie"]
    },
    {
        "rank": 5,
        "hs_code": "7207",
        "product": "Produits semi-finis en fer ou acier",
        "value_mln_usd": 2500,
        "share_percent": 3.7,
        "main_origins": ["Afrique du Sud", "Égypte", "Algérie"],
        "growth_2023_2024": 6.2,
        "top_importers": ["Kenya", "Zimbabwe", "Zambie", "Tanzanie"]
    },
    {
        "rank": 6,
        "hs_code": "2523",
        "product": "Ciment Portland",
        "value_mln_usd": 2200,
        "share_percent": 3.2,
        "main_origins": ["Égypte", "Afrique du Sud", "Tanzanie", "Sénégal"],
        "growth_2023_2024": 18.5,
        "top_importers": ["RD Congo", "Ghana", "Côte d'Ivoire", "Libéria"]
    },
    {
        "rank": 7,
        "hs_code": "1005",
        "product": "Maïs",
        "value_mln_usd": 1950,
        "share_percent": 2.9,
        "main_origins": ["Afrique du Sud", "Zambie", "Tanzanie", "Malawi"],
        "growth_2023_2024": 22.5,
        "top_importers": ["Zimbabwe", "Kenya", "Botswana", "Mozambique"]
    },
    {
        "rank": 8,
        "hs_code": "0713",
        "product": "Légumes à cosse secs (haricots, lentilles)",
        "value_mln_usd": 1800,
        "share_percent": 2.6,
        "main_origins": ["Éthiopie", "Tanzanie", "Kenya", "Ouganda"],
        "growth_2023_2024": 14.2,
        "top_importers": ["Kenya", "Afrique du Sud", "Soudan", "Égypte"]
    },
    {
        "rank": 9,
        "hs_code": "1511",
        "product": "Huile de palme",
        "value_mln_usd": 1650,
        "share_percent": 2.4,
        "main_origins": ["Côte d'Ivoire", "Ghana", "Cameroun", "RD Congo"],
        "growth_2023_2024": 11.8,
        "top_importers": ["Sénégal", "Burkina Faso", "Mali", "Niger"]
    },
    {
        "rank": 10,
        "hs_code": "2202",
        "product": "Boissons non alcoolisées",
        "value_mln_usd": 1500,
        "share_percent": 2.2,
        "main_origins": ["Afrique du Sud", "Kenya", "Nigéria", "Égypte"],
        "growth_2023_2024": 8.5,
        "top_importers": ["Zimbabwe", "Zambie", "Mozambique", "Botswana"]
    },
    {
        "rank": 11,
        "hs_code": "1101",
        "product": "Farine de blé",
        "value_mln_usd": 1350,
        "share_percent": 2.0,
        "main_origins": ["Égypte", "Afrique du Sud", "Kenya", "Éthiopie"],
        "growth_2023_2024": 16.2,
        "top_importers": ["Soudan", "RD Congo", "Somalie", "Libye"]
    },
    {
        "rank": 12,
        "hs_code": "0207",
        "product": "Viandes et abats de volailles",
        "value_mln_usd": 1200,
        "share_percent": 1.8,
        "main_origins": ["Afrique du Sud", "Égypte", "Maroc"],
        "growth_2023_2024": 9.8,
        "top_importers": ["Ghana", "RD Congo", "Angola", "Gabon"]
    },
    {
        "rank": 13,
        "hs_code": "7210",
        "product": "Produits laminés plats en fer ou acier",
        "value_mln_usd": 1100,
        "share_percent": 1.6,
        "main_origins": ["Afrique du Sud", "Égypte", "Algérie"],
        "growth_2023_2024": 5.5,
        "top_importers": ["Kenya", "Tanzanie", "Ghana", "Côte d'Ivoire"]
    },
    {
        "rank": 14,
        "hs_code": "3923",
        "product": "Articles de transport ou d'emballage en plastiques",
        "value_mln_usd": 980,
        "share_percent": 1.4,
        "main_origins": ["Afrique du Sud", "Kenya", "Égypte", "Nigéria"],
        "growth_2023_2024": 12.5,
        "top_importers": ["Zimbabwe", "Zambie", "Tanzanie", "Ouganda"]
    },
    {
        "rank": 15,
        "hs_code": "2208",
        "product": "Alcools éthyliques et spiritueux",
        "value_mln_usd": 920,
        "share_percent": 1.4,
        "main_origins": ["Afrique du Sud", "Kenya", "Ouganda", "Tanzanie"],
        "growth_2023_2024": 7.8,
        "top_importers": ["Zimbabwe", "Zambie", "RD Congo", "Botswana"]
    },
    {
        "rank": 16,
        "hs_code": "0402",
        "product": "Lait et crème concentrés",
        "value_mln_usd": 850,
        "share_percent": 1.3,
        "main_origins": ["Afrique du Sud", "Kenya", "Égypte"],
        "growth_2023_2024": 10.2,
        "top_importers": ["Zimbabwe", "Zambie", "Ouganda", "RD Congo"]
    },
    {
        "rank": 17,
        "hs_code": "4818",
        "product": "Papier hygiénique et mouchoirs",
        "value_mln_usd": 780,
        "share_percent": 1.1,
        "main_origins": ["Afrique du Sud", "Égypte", "Kenya"],
        "growth_2023_2024": 8.5,
        "top_importers": ["Zimbabwe", "Zambie", "Botswana", "Mozambique"]
    },
    {
        "rank": 18,
        "hs_code": "3402",
        "product": "Agents de surface organiques (savons, détergents)",
        "value_mln_usd": 720,
        "share_percent": 1.1,
        "main_origins": ["Afrique du Sud", "Kenya", "Égypte", "Nigéria"],
        "growth_2023_2024": 11.5,
        "top_importers": ["Zimbabwe", "Zambie", "Tanzanie", "RD Congo"]
    },
    {
        "rank": 19,
        "hs_code": "1006",
        "product": "Riz",
        "value_mln_usd": 680,
        "share_percent": 1.0,
        "main_origins": ["Tanzanie", "Égypte", "Mali", "Sénégal"],
        "growth_2023_2024": 15.8,
        "top_importers": ["Kenya", "Ouganda", "RD Congo", "Burundi"]
    },
    {
        "rank": 20,
        "hs_code": "8544",
        "product": "Fils et câbles électriques",
        "value_mln_usd": 650,
        "share_percent": 1.0,
        "main_origins": ["Afrique du Sud", "Égypte", "Kenya", "Maroc"],
        "growth_2023_2024": 9.2,
        "top_importers": ["Zimbabwe", "Zambie", "Tanzanie", "Ghana"]
    },
]

# =============================================================================
# TOP 20 PRODUITS ÉCHANGÉS EN COMMERCE INTRA-AFRICAIN (EXPORTATIONS)
# Source: UNCTAD/AfCFTA Secretariat 2024
# =============================================================================

TOP_20_INTRA_AFRICAN_EXPORTS = [
    {
        "rank": 1,
        "hs_code": "2710",
        "product": "Huiles de pétrole raffinées",
        "value_mln_usd": 8500,
        "share_percent": 12.5,
        "main_destinations": ["Zimbabwe", "Zambie", "Botswana", "Mozambique"],
        "growth_2023_2024": 8.2,
        "top_exporters": ["Afrique du Sud", "Algérie", "Égypte", "Nigéria"]
    },
    {
        "rank": 2,
        "hs_code": "2716",
        "product": "Énergie électrique",
        "value_mln_usd": 4200,
        "share_percent": 6.2,
        "main_destinations": ["Zimbabwe", "Botswana", "Namibie", "Lesotho"],
        "growth_2023_2024": 15.5,
        "top_exporters": ["Afrique du Sud", "Mozambique", "Zambie", "Éthiopie"]
    },
    {
        "rank": 3,
        "hs_code": "8703",
        "product": "Véhicules automobiles",
        "value_mln_usd": 3800,
        "share_percent": 5.6,
        "main_destinations": ["Zimbabwe", "Zambie", "Kenya", "Ghana"],
        "growth_2023_2024": 12.8,
        "top_exporters": ["Afrique du Sud", "Maroc", "Égypte"]
    },
    {
        "rank": 4,
        "hs_code": "7108",
        "product": "Or",
        "value_mln_usd": 3200,
        "share_percent": 4.7,
        "main_destinations": ["Afrique du Sud", "Émirats (via)", "Kenya"],
        "growth_2023_2024": 18.5,
        "top_exporters": ["Ghana", "Mali", "Tanzanie", "RD Congo"]
    },
    {
        "rank": 5,
        "hs_code": "1701",
        "product": "Sucre de canne",
        "value_mln_usd": 2800,
        "share_percent": 4.1,
        "main_destinations": ["Kenya", "RD Congo", "Soudan", "Tanzanie"],
        "growth_2023_2024": 9.5,
        "top_exporters": ["Eswatini", "Afrique du Sud", "Zimbabwe", "Mozambique"]
    },
    {
        "rank": 6,
        "hs_code": "7207",
        "product": "Produits semi-finis en fer ou acier",
        "value_mln_usd": 2500,
        "share_percent": 3.7,
        "main_destinations": ["Kenya", "Zimbabwe", "Zambie", "Tanzanie"],
        "growth_2023_2024": 6.2,
        "top_exporters": ["Afrique du Sud", "Égypte", "Algérie"]
    },
    {
        "rank": 7,
        "hs_code": "2523",
        "product": "Ciment Portland",
        "value_mln_usd": 2200,
        "share_percent": 3.2,
        "main_destinations": ["RD Congo", "Ghana", "Côte d'Ivoire", "Libéria"],
        "growth_2023_2024": 18.5,
        "top_exporters": ["Égypte", "Afrique du Sud", "Tanzanie", "Sénégal"]
    },
    {
        "rank": 8,
        "hs_code": "0901",
        "product": "Café",
        "value_mln_usd": 2100,
        "share_percent": 3.1,
        "main_destinations": ["Afrique du Sud", "Égypte", "Maroc", "Algérie"],
        "growth_2023_2024": 14.5,
        "top_exporters": ["Ouganda", "Éthiopie", "Kenya", "Tanzanie"]
    },
    {
        "rank": 9,
        "hs_code": "1005",
        "product": "Maïs",
        "value_mln_usd": 1950,
        "share_percent": 2.9,
        "main_destinations": ["Zimbabwe", "Kenya", "Botswana", "Mozambique"],
        "growth_2023_2024": 22.5,
        "top_exporters": ["Afrique du Sud", "Zambie", "Tanzanie", "Malawi"]
    },
    {
        "rank": 10,
        "hs_code": "0713",
        "product": "Légumes à cosse secs",
        "value_mln_usd": 1800,
        "share_percent": 2.6,
        "main_destinations": ["Kenya", "Afrique du Sud", "Soudan", "Égypte"],
        "growth_2023_2024": 14.2,
        "top_exporters": ["Éthiopie", "Tanzanie", "Kenya", "Ouganda"]
    },
    {
        "rank": 11,
        "hs_code": "0902",
        "product": "Thé",
        "value_mln_usd": 1650,
        "share_percent": 2.4,
        "main_destinations": ["Égypte", "Soudan", "Afrique du Sud", "Libye"],
        "growth_2023_2024": 8.5,
        "top_exporters": ["Kenya", "Ouganda", "Rwanda", "Malawi"]
    },
    {
        "rank": 12,
        "hs_code": "1511",
        "product": "Huile de palme",
        "value_mln_usd": 1650,
        "share_percent": 2.4,
        "main_destinations": ["Sénégal", "Burkina Faso", "Mali", "Niger"],
        "growth_2023_2024": 11.8,
        "top_exporters": ["Côte d'Ivoire", "Ghana", "Cameroun", "RD Congo"]
    },
    {
        "rank": 13,
        "hs_code": "2202",
        "product": "Boissons non alcoolisées",
        "value_mln_usd": 1500,
        "share_percent": 2.2,
        "main_destinations": ["Zimbabwe", "Zambie", "Mozambique", "Botswana"],
        "growth_2023_2024": 8.5,
        "top_exporters": ["Afrique du Sud", "Kenya", "Nigéria", "Égypte"]
    },
    {
        "rank": 14,
        "hs_code": "0201",
        "product": "Viandes bovines",
        "value_mln_usd": 1400,
        "share_percent": 2.1,
        "main_destinations": ["Angola", "RD Congo", "Gabon", "Congo"],
        "growth_2023_2024": 12.8,
        "top_exporters": ["Botswana", "Namibie", "Afrique du Sud", "Zimbabwe"]
    },
    {
        "rank": 15,
        "hs_code": "0803",
        "product": "Bananes",
        "value_mln_usd": 1300,
        "share_percent": 1.9,
        "main_destinations": ["Sénégal", "Mauritanie", "Mali", "Burkina Faso"],
        "growth_2023_2024": 6.5,
        "top_exporters": ["Côte d'Ivoire", "Cameroun", "Ghana", "Guinée"]
    },
    {
        "rank": 16,
        "hs_code": "1101",
        "product": "Farine de blé",
        "value_mln_usd": 1350,
        "share_percent": 2.0,
        "main_destinations": ["Soudan", "RD Congo", "Somalie", "Libye"],
        "growth_2023_2024": 16.2,
        "top_exporters": ["Égypte", "Afrique du Sud", "Kenya", "Éthiopie"]
    },
    {
        "rank": 17,
        "hs_code": "5201",
        "product": "Coton",
        "value_mln_usd": 1200,
        "share_percent": 1.8,
        "main_destinations": ["Égypte", "Afrique du Sud", "Maurice", "Maroc"],
        "growth_2023_2024": 5.2,
        "top_exporters": ["Mali", "Bénin", "Burkina Faso", "Côte d'Ivoire"]
    },
    {
        "rank": 18,
        "hs_code": "0207",
        "product": "Viandes et abats de volailles",
        "value_mln_usd": 1200,
        "share_percent": 1.8,
        "main_destinations": ["Ghana", "RD Congo", "Angola", "Gabon"],
        "growth_2023_2024": 9.8,
        "top_exporters": ["Afrique du Sud", "Égypte", "Maroc"]
    },
    {
        "rank": 19,
        "hs_code": "0805",
        "product": "Agrumes",
        "value_mln_usd": 1100,
        "share_percent": 1.6,
        "main_destinations": ["Zambie", "Zimbabwe", "Botswana", "RD Congo"],
        "growth_2023_2024": 10.5,
        "top_exporters": ["Afrique du Sud", "Égypte", "Maroc", "Zimbabwe"]
    },
    {
        "rank": 20,
        "hs_code": "0801",
        "product": "Noix de cajou et noix de coco",
        "value_mln_usd": 980,
        "share_percent": 1.4,
        "main_destinations": ["Afrique du Sud", "Ghana", "Sénégal", "Kenya"],
        "growth_2023_2024": 15.8,
        "top_exporters": ["Côte d'Ivoire", "Tanzanie", "Mozambique", "Bénin"]
    },
]


# =============================================================================
# FONCTIONS D'ACCÈS
# =============================================================================

def get_top_imports_from_world() -> List[Dict]:
    """Retourne le top 20 des produits importés du monde."""
    return TOP_20_IMPORTS_FROM_WORLD

def get_top_exports_to_world() -> List[Dict]:
    """Retourne le top 20 des produits exportés vers le monde."""
    return TOP_20_EXPORTS_TO_WORLD

def get_top_intra_african_imports() -> List[Dict]:
    """Retourne le top 20 des produits importés en commerce intra-africain."""
    return TOP_20_INTRA_AFRICAN_IMPORTS

def get_top_intra_african_exports() -> List[Dict]:
    """Retourne le top 20 des produits exportés en commerce intra-africain."""
    return TOP_20_INTRA_AFRICAN_EXPORTS

def get_all_trade_products_data() -> Dict:
    """Retourne toutes les données de produits commerciaux."""
    return {
        "imports_from_world": TOP_20_IMPORTS_FROM_WORLD,
        "exports_to_world": TOP_20_EXPORTS_TO_WORLD,
        "intra_african_imports": TOP_20_INTRA_AFRICAN_IMPORTS,
        "intra_african_exports": TOP_20_INTRA_AFRICAN_EXPORTS,
        "metadata": {
            "source": "UNCTAD/ITC Trade Map, AfCFTA Secretariat 2023",
            "year": 2023,
            "classification": "HS Code (Système Harmonisé)"
        }
    }

def get_trade_summary() -> Dict:
    """Retourne un résumé des échanges commerciaux."""
    total_imports_world = sum(p["value_mln_usd"] for p in TOP_20_IMPORTS_FROM_WORLD)
    total_exports_world = sum(p["value_mln_usd"] for p in TOP_20_EXPORTS_TO_WORLD)
    total_intra_imports = sum(p["value_mln_usd"] for p in TOP_20_INTRA_AFRICAN_IMPORTS)
    total_intra_exports = sum(p["value_mln_usd"] for p in TOP_20_INTRA_AFRICAN_EXPORTS)
    
    return {
        "top_20_imports_world_total_mln_usd": total_imports_world,
        "top_20_exports_world_total_mln_usd": total_exports_world,
        "top_20_intra_african_imports_total_mln_usd": total_intra_imports,
        "top_20_intra_african_exports_total_mln_usd": total_intra_exports,
        "intra_african_trade_share_percent": round((total_intra_imports / total_imports_world) * 100, 1) if total_imports_world > 0 else 0,
        "data_year": 2024
    }
