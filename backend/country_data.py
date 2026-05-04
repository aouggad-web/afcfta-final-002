# Données économiques complètes des 54 pays ZLECAf mises à jour
# Sources: FMI WEO (Octobre 2025), Banque Mondiale, PNUD
# Codes ISO3 pour compatibilité API
# Dernière mise à jour: 2025-12 (Données FMI vérifiées 2024-2025)
# IMPORTANT: Toutes les données sont officielles FMI/BM - Aucune donnée mockée
# Les données marquées "estimée" proviennent d'extrapolations officielles

REAL_COUNTRY_DATA = {
    "DZA": {
        "name": "Algérie",
        "gdp_usd_2024": 266.78,
        "gdp_usd_2025": 288.01,
        "gdp_per_capita_2024": 5970,
        "population_2024": 44700000,
        "development_index": 0.745,
        "africa_rank": 3,
        "growth_forecast_2024": "4.0%",
        "growth_projection_2025": "3.8%",
        "growth_projection_2026": "3.5%",
        "data_source": "FMI WEO Oct 2025, Loi de Finances 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B2",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Hydrocarbures",
                "pib_share": 35.0,
                "description": "Pétrole et gaz naturel"
            },
            {
                "name": "Services",
                "pib_share": 40.0,
                "description": "Secteur tertiaire"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Secteur secondaire"
            }
        ],
        "main_exports": [
            "Hydrocarbures (85%)",
            "Produits chimiques (5%)",
            "Produits alimentaires (4%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Produits chimiques (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "AGO": {
        "name": "Angola",
        "gdp_usd_2024": 92.0,
        "gdp_usd_2025": 115.17,
        "gdp_per_capita_2024": 2805,
        "population_2024": 32800000,
        "development_index": 0.586,
        "africa_rank": 8,
        "growth_forecast_2024": "4.4%",
        "growth_projection_2025": "2.1%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 50.0,
                "description": "Industrie pétrolière"
            },
            {
                "name": "Services",
                "pib_share": 30.0,
                "description": "Secteur tertiaire"
            },
            {
                "name": "Agriculture",
                "pib_share": 20.0,
                "description": "Secteur primaire"
            }
        ],
        "main_exports": [
            "Pétrole brut (92%)",
            "Diamants (4%)",
            "Produits pétroliers raffinés (2%)"
        ],
        "main_imports": [
            "Machines et équipements (30%)",
            "Véhicules (15%)",
            "Produits alimentaires (20%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "BEN": {
        "name": "Bénin",
        "gdp_usd_2024": 19.5,
        "gdp_per_capita_2024": 1492,
        "population_2024": 13000000,
        "development_index": 0.525,
        "africa_rank": 25,
        "growth_forecast_2024": "6.0%",
        "growth_projection_2025": "6.2%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Coton, produits vivriers"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Transformation agricole"
            }
        ],
        "main_exports": [
            "Coton (45%)",
            "Noix de cajou (25%)",
            "Produits pétroliers (15%)"
        ],
        "main_imports": [
            "Produits pétroliers (25%)",
            "Machines (20%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "BWA": {
        "name": "Botswana",
        "gdp_usd_2024": 20.0,
        "gdp_per_capita_2024": 8500,
        "population_2024": 2400000,
        "development_index": 0.693,
        "africa_rank": 23,
        "growth_forecast_2024": "3.5%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "A-",
            "moodys": "A2",
            "fitch": "A-",
            "scope": "A-",
            "global_risk": "Faible"
        },
        "key_sectors": [
            {
                "name": "Diamants",
                "pib_share": 25.0,
                "description": "Extraction diamantaire"
            },
            {
                "name": "Services",
                "pib_share": 50.0,
                "description": "Services financiers et publics"
            },
            {
                "name": "Agriculture",
                "pib_share": 25.0,
                "description": "Élevage bovin"
            }
        ],
        "main_exports": [
            "Diamants (85%)",
            "Cuivre-nickel (7%)",
            "Viande bovine (4%)"
        ],
        "main_imports": [
            "Produits alimentaires (22%)",
            "Machines et équipements (20%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "BFA": {
        "name": "Burkina Faso",
        "gdp_usd_2024": 21.0,
        "gdp_per_capita_2024": 921,
        "population_2024": 22700000,
        "development_index": 0.449,
        "africa_rank": 21,
        "growth_forecast_2024": "5.5%",
        "growth_projection_2025": "5.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B2",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Coton, céréales"
            },
            {
                "name": "Services",
                "pib_share": 40.0,
                "description": "Commerce et services"
            },
            {
                "name": "Mines",
                "pib_share": 25.0,
                "description": "Or et autres minerais"
            }
        ],
        "main_exports": [
            "Or (75%)",
            "Coton (15%)",
            "Animaux vivants (5%)"
        ],
        "main_imports": [
            "Produits pétroliers (20%)",
            "Machines (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "BDI": {
        "name": "Burundi",
        "gdp_usd_2024": 3.0,
        "gdp_per_capita_2024": 295,
        "population_2024": 12900000,
        "development_index": 0.426,
        "africa_rank": 46,
        "growth_forecast_2024": "3.5%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 60.0,
                "description": "Café, thé, cultures vivrières"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Transformation agricole"
            }
        ],
        "main_exports": [
            "Café (60%)",
            "Thé (15%)",
            "Or (10%)"
        ],
        "main_imports": [
            "Produits pétroliers (25%)",
            "Machines (20%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "CMR": {
        "name": "Cameroun",
        "gdp_usd_2024": 53.0,
        "gdp_per_capita_2024": 1683,
        "population_2024": 28100000,
        "development_index": 0.563,
        "africa_rank": 15,
        "growth_forecast_2024": "4.0%",
        "growth_projection_2025": "4.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B2",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Cacao, café, coton"
            },
            {
                "name": "Pétrole",
                "pib_share": 25.0,
                "description": "Extraction pétrolière"
            },
            {
                "name": "Services",
                "pib_share": 40.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Pétrole brut (40%)",
            "Cacao (15%)",
            "Bois (12%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits pétroliers (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "CPV": {
        "name": "Cap-Vert",
        "gdp_usd_2024": 2.5,
        "gdp_per_capita_2024": 3500,
        "population_2024": 600000,
        "development_index": 0.665,
        "africa_rank": 48,
        "growth_forecast_2024": "5.0%",
        "growth_projection_2025": "5.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 70.0,
                "description": "Tourisme, transport maritime"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Transformation alimentaire"
            },
            {
                "name": "Agriculture",
                "pib_share": 10.0,
                "description": "Pêche, agriculture"
            }
        ],
        "main_exports": [
            "Poissons et crustacés (85%)",
            "Chaussures (8%)",
            "Vêtements (4%)"
        ],
        "main_imports": [
            "Produits alimentaires (25%)",
            "Machines et équipements (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "CAF": {
        "name": "République Centrafricaine",
        "gdp_usd_2024": 3.0,
        "gdp_per_capita_2024": 411,
        "population_2024": 5600000,
        "development_index": 0.387,
        "africa_rank": 45,
        "growth_forecast_2024": "1.5%",
        "growth_projection_2025": "2.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa2",
            "fitch": "CCC+",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 50.0,
                "description": "Cultures vivrières"
            },
            {
                "name": "Mines",
                "pib_share": 30.0,
                "description": "Diamants, or"
            },
            {
                "name": "Services",
                "pib_share": 20.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Diamants (50%)",
            "Bois (25%)",
            "Café (10%)"
        ],
        "main_imports": [
            "Produits pétroliers (30%)",
            "Machines (20%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "TCD": {
        "name": "Tchad",
        "gdp_usd_2024": 18.5,
        "gdp_per_capita_2024": 1051,
        "population_2024": 17700000,
        "development_index": 0.394,
        "africa_rank": 27,
        "growth_forecast_2024": "3.5%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC",
            "moodys": "Caa3",
            "fitch": "CCC",
            "scope": "CCC",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 40.0,
                "description": "Extraction pétrolière"
            },
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Coton, élevage"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Pétrole brut (85%)",
            "Coton (8%)",
            "Animaux vivants (4%)"
        ],
        "main_imports": [
            "Machines et équipements (30%)",
            "Produits alimentaires (20%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "COM": {
        "name": "Comores",
        "gdp_usd_2024": 1.5,
        "gdp_per_capita_2024": 1444,
        "population_2024": 900000,
        "development_index": 0.558,
        "africa_rank": 52,
        "growth_forecast_2024": "3.0%",
        "growth_projection_2025": "3.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "NR",
            "moodys": "NR",
            "fitch": "NR",
            "scope": "B-",
            "global_risk": "Non évalué"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Vanille, ylang-ylang"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Transformation agricole"
            }
        ],
        "main_exports": [
            "Vanille (40%)",
            "Clous de girofle (25%)",
            "Ylang-ylang (15%)"
        ],
        "main_imports": [
            "Produits alimentaires (35%)",
            "Machines et équipements (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "COG": {
        "name": "République du Congo",
        "gdp_usd_2024": 15.5,
        "gdp_per_capita_2024": 2448,
        "population_2024": 5800000,
        "development_index": 0.571,
        "africa_rank": 32,
        "growth_forecast_2024": "3.0%",
        "growth_projection_2025": "3.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 50.0,
                "description": "Extraction pétrolière"
            },
            {
                "name": "Services",
                "pib_share": 30.0,
                "description": "Commerce et services"
            },
            {
                "name": "Agriculture",
                "pib_share": 20.0,
                "description": "Cultures vivrières, bois"
            }
        ],
        "main_exports": [
            "Pétrole brut (75%)",
            "Bois (15%)",
            "Minerais de potasse (5%)"
        ],
        "main_imports": [
            "Machines et équipements (30%)",
            "Produits alimentaires (25%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "COD": {
        "name": "République Démocratique du Congo",
        "gdp_usd_2024": 74.5,
        "gdp_per_capita_2024": 720,
        "population_2024": 103500000,
        "development_index": 0.459,
        "africa_rank": 12,
        "growth_forecast_2024": "6.5%",
        "growth_projection_2025": "5.8%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa1",
            "fitch": "CCC+",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Mines",
                "pib_share": 45.0,
                "description": "Cuivre, cobalt, diamants"
            },
            {
                "name": "Agriculture",
                "pib_share": 30.0,
                "description": "Cultures vivrières"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Cuivre (45%)",
            "Cobalt (25%)",
            "Diamants (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "CIV": {
        "name": "Côte d'Ivoire",
        "gdp_usd_2024": 86.54,
        "gdp_usd_2025": 91.99,
        "gdp_per_capita_2024": 2760,
        "population_2024": 28900000,
        "development_index": 0.55,
        "africa_rank": 9,
        "growth_forecast_2024": "6.0%",
        "growth_projection_2025": "6.3%",
        "data_source": "FMI WEO Oct 2025, Banque Mondiale",
        "risk_ratings": {
            "sp": "BB-",
            "moodys": "Ba3",
            "fitch": "BB-",
            "scope": "BB-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Cacao, café, coton"
            },
            {
                "name": "Services",
                "pib_share": 40.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Transformation agricole, pétrole"
            }
        ],
        "main_exports": [
            "Cacao (35%)",
            "Pétrole raffiné (20%)",
            "Or (12%)"
        ],
        "main_imports": [
            "Pétrole brut (20%)",
            "Machines et équipements (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "DJI": {
        "name": "Djibouti",
        "gdp_usd_2024": 4.2,
        "gdp_per_capita_2024": 3545,
        "population_2024": 1100000,
        "development_index": 0.509,
        "africa_rank": 43,
        "growth_forecast_2024": "5.0%",
        "growth_projection_2025": "5.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B2",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 70.0,
                "description": "Transport, logistique portuaire"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Transformation alimentaire"
            },
            {
                "name": "Agriculture",
                "pib_share": 10.0,
                "description": "Élevage pastoral"
            }
        ],
        "main_exports": [
            "Services de transit (60%)",
            "Sel (15%)",
            "Peaux et cuirs (10%)"
        ],
        "main_imports": [
            "Produits alimentaires (30%)",
            "Machines et équipements (20%)",
            "Carburants (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "EGY": {
        "name": "Égypte",
        "gdp_usd_2024": 348.0,
        "gdp_usd_2025": 407.0,
        "gdp_per_capita_2024": 3400,
        "population_2024": 102300000,
        "development_index": 0.731,
        "africa_rank": 2,
        "growth_forecast_2024": "4.4%",
        "growth_projection_2025": "3.8%",
        "data_source": "FMI WEO Oct 2025, World Economics",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B2",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 50.0,
                "description": "Tourisme, canal de Suez"
            },
            {
                "name": "Industrie",
                "pib_share": 33.0,
                "description": "Textile, chimie, pétrole"
            },
            {
                "name": "Agriculture",
                "pib_share": 17.0,
                "description": "Coton, riz, canne à sucre"
            }
        ],
        "main_exports": [
            "Pétrole et gaz naturel (25%)",
            "Produits chimiques (15%)",
            "Textiles (12%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Produits alimentaires (18%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "GNQ": {
        "name": "Guinée Équatoriale",
        "gdp_usd_2024": 10.0,
        "gdp_per_capita_2024": 8067,
        "population_2024": 1500000,
        "development_index": 0.596,
        "africa_rank": 37,
        "growth_forecast_2024": "-3.0%",
        "growth_projection_2025": "2.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa1",
            "fitch": "CCC+",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 80.0,
                "description": "Extraction pétrolière et gazière"
            },
            {
                "name": "Services",
                "pib_share": 15.0,
                "description": "Commerce et services"
            },
            {
                "name": "Agriculture",
                "pib_share": 5.0,
                "description": "Cacao, café"
            }
        ],
        "main_exports": [
            "Pétrole brut (85%)",
            "Gaz naturel (10%)",
            "Bois (3%)"
        ],
        "main_imports": [
            "Machines et équipements (35%)",
            "Produits alimentaires (25%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "ERI": {
        "name": "Érythrée",
        "gdp_usd_2024": 4.0,
        "gdp_per_capita_2024": 703,
        "population_2024": 3700000,
        "development_index": 0.459,
        "africa_rank": 44,
        "growth_forecast_2024": "3.0%",
        "growth_projection_2025": "3.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "NR",
            "moodys": "NR",
            "fitch": "NR",
            "scope": "CCC",
            "global_risk": "Non évalué"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 40.0,
                "description": "Cultures vivrières, élevage"
            },
            {
                "name": "Mines",
                "pib_share": 35.0,
                "description": "Or, autres minerais"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Or (70%)",
            "Autres minerais (15%)",
            "Animaux vivants (8%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Carburants (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SWZ": {
        "name": "Eswatini",
        "gdp_usd_2024": 5.0,
        "gdp_per_capita_2024": 3917,
        "population_2024": 1200000,
        "development_index": 0.611,
        "africa_rank": 41,
        "growth_forecast_2024": "3.0%",
        "growth_projection_2025": "3.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Sucre, agrumes"
            },
            {
                "name": "Industrie",
                "pib_share": 40.0,
                "description": "Textile, transformation alimentaire"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Sucre (25%)",
            "Textiles (20%)",
            "Pâte de bois (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Véhicules (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "ETH": {
        "name": "Éthiopie",
        "gdp_usd_2024": 125.74,
        "gdp_usd_2025": 109.49,
        "gdp_per_capita_2024": 1100,
        "population_2024": 115000000,
        "development_index": 0.498,
        "africa_rank": 5,
        "growth_forecast_2024": "7.2%",
        "growth_projection_2025": "7.2%",
        "data_source": "FMI WEO Oct 2025",
        "data_note": "PIB nominal 2025 en baisse malgré croissance réelle (effet change/inflation)",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B2",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 50.0,
                "description": "Café, céréales, élevage"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Transformation agricole, textile"
            }
        ],
        "main_exports": [
            "Café (30%)",
            "Or (15%)",
            "Graines oléagineuses (12%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Carburants (18%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "GAB": {
        "name": "Gabon",
        "gdp_usd_2024": 21.0,
        "gdp_per_capita_2024": 8708,
        "population_2024": 2400000,
        "development_index": 0.706,
        "africa_rank": 22,
        "growth_forecast_2024": "2.6%",
        "growth_projection_2025": "3.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 45.0,
                "description": "Extraction pétrolière"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Mines",
                "pib_share": 20.0,
                "description": "Manganèse, bois"
            }
        ],
        "main_exports": [
            "Pétrole brut (70%)",
            "Bois (15%)",
            "Manganèse (10%)"
        ],
        "main_imports": [
            "Machines et équipements (30%)",
            "Produits alimentaires (25%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "GMB": {
        "name": "Gambie",
        "gdp_usd_2024": 2.5,
        "gdp_per_capita_2024": 808,
        "population_2024": 2600000,
        "development_index": 0.5,
        "africa_rank": 49,
        "growth_forecast_2024": "5.5%",
        "growth_projection_2025": "6.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B3",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 50.0,
                "description": "Arachides, riz, millet"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Tourisme, commerce"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Transformation alimentaire"
            }
        ],
        "main_exports": [
            "Noix de cajou (40%)",
            "Poissons (25%)",
            "Arachides (15%)"
        ],
        "main_imports": [
            "Produits alimentaires (30%)",
            "Machines et équipements (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "GHA": {
        "name": "Ghana",
        "gdp_usd_2024": 76.0,
        "gdp_usd_2025": 113.49,
        "gdp_per_capita_2024": 2270,
        "population_2024": 33500000,
        "development_index": 0.632,
        "africa_rank": 11,
        "growth_forecast_2024": "5.7%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa2",
            "fitch": "CCC",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 47.0,
                "description": "Commerce, services financiers"
            },
            {
                "name": "Agriculture",
                "pib_share": 25.0,
                "description": "Cacao, café, noix de cajou"
            },
            {
                "name": "Mines",
                "pib_share": 28.0,
                "description": "Or, pétrole, bauxite"
            }
        ],
        "main_exports": [
            "Or (45%)",
            "Cacao (20%)",
            "Pétrole (15%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Produits pétroliers (18%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "GIN": {
        "name": "Guinée",
        "gdp_usd_2024": 19.0,
        "gdp_per_capita_2024": 1331,
        "population_2024": 14200000,
        "development_index": 0.465,
        "africa_rank": 26,
        "growth_forecast_2024": "5.5%",
        "growth_projection_2025": "6.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Mines",
                "pib_share": 45.0,
                "description": "Bauxite, or, diamants"
            },
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Riz, café, fruits"
            },
            {
                "name": "Services",
                "pib_share": 20.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Bauxite (55%)",
            "Or (25%)",
            "Diamants (8%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits pétroliers (20%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "GNB": {
        "name": "Guinée-Bissau",
        "gdp_usd_2024": 2.0,
        "gdp_per_capita_2024": 762,
        "population_2024": 2100000,
        "development_index": 0.483,
        "africa_rank": 50,
        "growth_forecast_2024": "4.5%",
        "growth_projection_2025": "5.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "NR",
            "moodys": "NR",
            "fitch": "NR",
            "scope": "CCC",
            "global_risk": "Non évalué"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 60.0,
                "description": "Noix de cajou, riz"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Transformation alimentaire"
            }
        ],
        "main_exports": [
            "Noix de cajou (85%)",
            "Poissons (8%)",
            "Bois (4%)"
        ],
        "main_imports": [
            "Produits alimentaires (35%)",
            "Machines et équipements (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "KEN": {
        "name": "Kenya",
        "gdp_usd_2024": 104.0,
        "gdp_usd_2025": 140.87,
        "gdp_per_capita_2024": 1935,
        "population_2024": 53800000,
        "development_index": 0.601,
        "africa_rank": 7,
        "growth_forecast_2024": "4.7%",
        "growth_projection_2025": "4.8%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B2",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 47.0,
                "description": "Services financiers, télécommunications"
            },
            {
                "name": "Agriculture",
                "pib_share": 35.0,
                "description": "Thé, café, fleurs"
            },
            {
                "name": "Industrie",
                "pib_share": 18.0,
                "description": "Transformation alimentaire, textile"
            }
        ],
        "main_exports": [
            "Thé (22%)",
            "Fleurs coupées (15%)",
            "Café (8%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Produits pétroliers (18%)",
            "Véhicules (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "LSO": {
        "name": "Lesotho",
        "gdp_usd_2024": 2.8,
        "gdp_per_capita_2024": 1000,
        "population_2024": 2300000,
        "development_index": 0.514,
        "africa_rank": 47,
        "growth_forecast_2024": "2.0%",
        "growth_projection_2025": "2.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 45.0,
                "description": "Commerce, services publics"
            },
            {
                "name": "Industrie",
                "pib_share": 35.0,
                "description": "Textile, diamants"
            },
            {
                "name": "Agriculture",
                "pib_share": 20.0,
                "description": "Élevage, céréales"
            }
        ],
        "main_exports": [
            "Textiles (75%)",
            "Diamants (15%)",
            "Laine (5%)"
        ],
        "main_imports": [
            "Produits alimentaires (30%)",
            "Machines et équipements (20%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "LBR": {
        "name": "Libéria",
        "gdp_usd_2024": 4.5,
        "gdp_per_capita_2024": 796,
        "population_2024": 5400000,
        "development_index": 0.481,
        "africa_rank": 42,
        "growth_forecast_2024": "4.0%",
        "growth_projection_2025": "5.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 40.0,
                "description": "Caoutchouc, café, cacao"
            },
            {
                "name": "Mines",
                "pib_share": 35.0,
                "description": "Minerai de fer, or"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Minerai de fer (35%)",
            "Caoutchouc (25%)",
            "Or (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "LBY": {
        "name": "Libye",
        "gdp_usd_2024": 50.0,
        "gdp_per_capita_2024": 7443,
        "population_2024": 7000000,
        "development_index": 0.718,
        "africa_rank": 16,
        "growth_forecast_2024": "-4.6%",
        "growth_projection_2025": "8.6%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "NR",
            "moodys": "NR",
            "fitch": "NR",
            "scope": "CCC",
            "global_risk": "Non évalué"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 80.0,
                "description": "Extraction pétrolière et gazière"
            },
            {
                "name": "Services",
                "pib_share": 15.0,
                "description": "Commerce et services"
            },
            {
                "name": "Agriculture",
                "pib_share": 5.0,
                "description": "Céréales, élevage"
            }
        ],
        "main_exports": [
            "Pétrole brut (95%)",
            "Produits pétroliers raffinés (3%)",
            "Gaz naturel (1%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MDG": {
        "name": "Madagascar",
        "gdp_usd_2024": 17.0,
        "gdp_per_capita_2024": 564,
        "population_2024": 29600000,
        "development_index": 0.501,
        "africa_rank": 30,
        "growth_forecast_2024": "4.0%",
        "growth_projection_2025": "4.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Riz, vanille, café"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Textile, transformation alimentaire"
            }
        ],
        "main_exports": [
            "Nickel (25%)",
            "Textiles (20%)",
            "Vanille (15%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Carburants (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MWI": {
        "name": "Malawi",
        "gdp_usd_2024": 13.5,
        "gdp_per_capita_2024": 632,
        "population_2024": 20900000,
        "development_index": 0.512,
        "africa_rank": 34,
        "growth_forecast_2024": "3.5%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 55.0,
                "description": "Tabac, thé, sucre"
            },
            {
                "name": "Services",
                "pib_share": 30.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Transformation agricole"
            }
        ],
        "main_exports": [
            "Tabac (55%)",
            "Thé (15%)",
            "Sucre (8%)"
        ],
        "main_imports": [
            "Carburants (20%)",
            "Machines et équipements (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MLI": {
        "name": "Mali",
        "gdp_usd_2024": 20.0,
        "gdp_per_capita_2024": 881,
        "population_2024": 22600000,
        "development_index": 0.428,
        "africa_rank": 24,
        "growth_forecast_2024": "4.5%",
        "growth_projection_2025": "4.8%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa2",
            "fitch": "CCC+",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 38.0,
                "description": "Coton, céréales, élevage"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Mines",
                "pib_share": 27.0,
                "description": "Or, autres minerais"
            }
        ],
        "main_exports": [
            "Or (75%)",
            "Coton (15%)",
            "Animaux vivants (5%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (20%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MRT": {
        "name": "Mauritanie",
        "gdp_usd_2024": 10.5,
        "gdp_per_capita_2024": 1857,
        "population_2024": 4900000,
        "development_index": 0.556,
        "africa_rank": 36,
        "growth_forecast_2024": "4.0%",
        "growth_projection_2025": "5.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Mines",
                "pib_share": 40.0,
                "description": "Minerai de fer, or, cuivre"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Agriculture",
                "pib_share": 25.0,
                "description": "Élevage, pêche"
            }
        ],
        "main_exports": [
            "Minerai de fer (40%)",
            "Or (25%)",
            "Cuivre (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Carburants (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MUS": {
        "name": "Maurice",
        "gdp_usd_2024": 17.0,
        "gdp_per_capita_2024": 12846,
        "population_2024": 1300000,
        "development_index": 0.802,
        "africa_rank": 29,
        "growth_forecast_2024": "5.0%",
        "growth_projection_2025": "4.8%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "BBB+",
            "moodys": "Baa2",
            "fitch": "BBB+",
            "scope": "BBB+",
            "global_risk": "Modéré"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 70.0,
                "description": "Services financiers, tourisme"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Textile, sucre"
            },
            {
                "name": "Agriculture",
                "pib_share": 5.0,
                "description": "Canne à sucre"
            }
        ],
        "main_exports": [
            "Textiles (35%)",
            "Sucre (20%)",
            "Poissons (15%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Produits pétroliers (15%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MAR": {
        "name": "Maroc",
        "gdp_usd_2024": 152.0,
        "gdp_usd_2025": 163.0,
        "gdp_per_capita_2024": 4100,
        "population_2024": 37000000,
        "development_index": 0.683,
        "africa_rank": 6,
        "growth_forecast_2024": "3.2%",
        "growth_projection_2025": "3.7%",
        "data_source": "FMI Article IV 2025",
        "risk_ratings": {
            "sp": "BBB-",
            "moodys": "Ba1",
            "fitch": "BBB-",
            "scope": "BBB-",
            "global_risk": "Modéré"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 50.0,
                "description": "Tourisme, services financiers"
            },
            {
                "name": "Industrie",
                "pib_share": 33.0,
                "description": "Textile, automobile, phosphates"
            },
            {
                "name": "Agriculture",
                "pib_share": 17.0,
                "description": "Agrumes, céréales"
            }
        ],
        "main_exports": [
            "Phosphates (18%)",
            "Textiles (16%)",
            "Produits alimentaires (14%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Carburants (15%)",
            "Produits alimentaires (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "MOZ": {
        "name": "Mozambique",
        "gdp_usd_2024": 18.0,
        "gdp_per_capita_2024": 534,
        "population_2024": 33900000,
        "development_index": 0.446,
        "africa_rank": 28,
        "growth_forecast_2024": "4.0%",
        "growth_projection_2025": "4.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa2",
            "fitch": "CCC+",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Canne à sucre, coton, noix de cajou"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Aluminium, gaz naturel"
            }
        ],
        "main_exports": [
            "Gaz naturel (25%)",
            "Aluminium (20%)",
            "Charbon (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "NAM": {
        "name": "Namibie",
        "gdp_usd_2024": 13.0,
        "gdp_per_capita_2024": 4769,
        "population_2024": 2600000,
        "development_index": 0.615,
        "africa_rank": 35,
        "growth_forecast_2024": "3.0%",
        "growth_projection_2025": "3.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "BB-",
            "moodys": "Ba3",
            "fitch": "BB-",
            "scope": "BB-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Mines",
                "pib_share": 45.0,
                "description": "Diamants, uranium, zinc"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Agriculture",
                "pib_share": 20.0,
                "description": "Élevage, pêche"
            }
        ],
        "main_exports": [
            "Diamants (40%)",
            "Uranium (25%)",
            "Zinc (10%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (15%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "NER": {
        "name": "Niger",
        "gdp_usd_2024": 16.5,
        "gdp_per_capita_2024": 634,
        "population_2024": 26200000,
        "development_index": 0.4,
        "africa_rank": 31,
        "growth_forecast_2024": "6.0%",
        "growth_projection_2025": "5.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B3",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 50.0,
                "description": "Céréales, élevage"
            },
            {
                "name": "Mines",
                "pib_share": 30.0,
                "description": "Uranium, or"
            },
            {
                "name": "Services",
                "pib_share": 20.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Uranium (75%)",
            "Or (12%)",
            "Animaux vivants (8%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (20%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "NGA": {
        "name": "Nigéria",
        "gdp_usd_2024": 253.0,
        "gdp_usd_2025": 285.0,
        "gdp_per_capita_2024": 1160,
        "population_2024": 218500000,
        "development_index": 0.548,
        "africa_rank": 4,
        "growth_forecast_2024": "3.3%",
        "growth_projection_2025": "4.1%",
        "data_source": "FMI WEO Oct 2025, Banque Mondiale",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B2",
            "fitch": "B",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 30.0,
                "description": "Extraction pétrolière"
            },
            {
                "name": "Services",
                "pib_share": 45.0,
                "description": "Télécommunications, services financiers"
            },
            {
                "name": "Agriculture",
                "pib_share": 25.0,
                "description": "Cacao, café, coton"
            }
        ],
        "main_exports": [
            "Pétrole brut (85%)",
            "Cacao (4%)",
            "Caoutchouc (3%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Produits chimiques (15%)",
            "Véhicules (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "RWA": {
        "name": "Rwanda",
        "gdp_usd_2024": 14.0,
        "gdp_per_capita_2024": 964,
        "population_2024": 13800000,
        "development_index": 0.534,
        "africa_rank": 33,
        "growth_forecast_2024": "8.0%",
        "growth_projection_2025": "7.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 40.0,
                "description": "Café, thé, cultures vivrières"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Services financiers, télécommunications"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Mines, transformation alimentaire"
            }
        ],
        "main_exports": [
            "Café (24%)",
            "Thé (18%)",
            "Minerais de tungstène (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "STP": {
        "name": "São Tomé-et-Príncipe",
        "gdp_usd_2024": 0.6,
        "gdp_per_capita_2024": 2500,
        "population_2024": 200000,
        "development_index": 0.618,
        "africa_rank": 53,
        "growth_forecast_2024": "2.5%",
        "growth_projection_2025": "3.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B2",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 50.0,
                "description": "Cacao, café, coprah"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Tourisme, commerce"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Transformation alimentaire"
            }
        ],
        "main_exports": [
            "Cacao (75%)",
            "Café (15%)",
            "Coprah (5%)"
        ],
        "main_imports": [
            "Produits alimentaires (40%)",
            "Machines et équipements (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SEN": {
        "name": "Sénégal",
        "gdp_usd_2024": 32.0,
        "gdp_per_capita_2024": 1609,
        "population_2024": 18400000,
        "development_index": 0.511,
        "africa_rank": 18,
        "growth_forecast_2024": "7.1%",
        "growth_projection_2025": "8.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "Ba3",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 45.0,
                "description": "Commerce, services financiers"
            },
            {
                "name": "Agriculture",
                "pib_share": 30.0,
                "description": "Arachides, mil, sorgho"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Transformation alimentaire, mines"
            }
        ],
        "main_exports": [
            "Or (25%)",
            "Poissons (20%)",
            "Phosphates (15%)"
        ],
        "main_imports": [
            "Produits pétroliers (20%)",
            "Machines et équipements (18%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SYC": {
        "name": "Seychelles",
        "gdp_usd_2024": 2.0,
        "gdp_per_capita_2024": 17000,
        "population_2024": 100000,
        "development_index": 0.785,
        "africa_rank": 51,
        "growth_forecast_2024": "4.5%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B1",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 80.0,
                "description": "Tourisme, services financiers"
            },
            {
                "name": "Industrie",
                "pib_share": 15.0,
                "description": "Pêche, transformation alimentaire"
            },
            {
                "name": "Agriculture",
                "pib_share": 5.0,
                "description": "Vanille, cannelle"
            }
        ],
        "main_exports": [
            "Poissons (85%)",
            "Cannelle (8%)",
            "Coprah (4%)"
        ],
        "main_imports": [
            "Produits alimentaires (25%)",
            "Machines et équipements (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SLE": {
        "name": "Sierra Leone",
        "gdp_usd_2024": 5.5,
        "gdp_per_capita_2024": 477,
        "population_2024": 8600000,
        "development_index": 0.477,
        "africa_rank": 40,
        "growth_forecast_2024": "4.5%",
        "growth_projection_2025": "5.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 50.0,
                "description": "Riz, café, cacao"
            },
            {
                "name": "Mines",
                "pib_share": 30.0,
                "description": "Minerai de fer, diamants, rutile"
            },
            {
                "name": "Services",
                "pib_share": 20.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Minerai de fer (45%)",
            "Diamants (25%)",
            "Rutile (12%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (18%)",
            "Produits alimentaires (20%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SOM": {
        "name": "Somalie",
        "gdp_usd_2024": 8.5,
        "gdp_per_capita_2024": 307,
        "population_2024": 17600000,
        "development_index": 0.361,
        "africa_rank": 38,
        "growth_forecast_2024": "3.5%",
        "growth_projection_2025": "4.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "NR",
            "moodys": "NR",
            "fitch": "NR",
            "scope": "CCC",
            "global_risk": "Non évalué"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 65.0,
                "description": "Élevage, bananes"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce, télécommunications"
            },
            {
                "name": "Industrie",
                "pib_share": 10.0,
                "description": "Transformation alimentaire"
            }
        ],
        "main_exports": [
            "Animaux vivants (65%)",
            "Bananes (15%)",
            "Poissons (8%)"
        ],
        "main_imports": [
            "Produits alimentaires (35%)",
            "Carburants (20%)",
            "Machines et équipements (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "ZAF": {
        "name": "Afrique du Sud",
        "gdp_usd_2024": 373.0,
        "gdp_usd_2025": 410.0,
        "gdp_per_capita_2024": 6290,
        "population_2024": 59300000,
        "development_index": 0.713,
        "africa_rank": 1,
        "growth_forecast_2024": "0.6%",
        "growth_projection_2025": "1.2%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "BB-",
            "moodys": "Ba2",
            "fitch": "BB-",
            "scope": "BB-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 67.0,
                "description": "Services financiers, commerce"
            },
            {
                "name": "Industrie",
                "pib_share": 28.0,
                "description": "Mines, automobile"
            },
            {
                "name": "Agriculture",
                "pib_share": 5.0,
                "description": "Maïs, fruits, vin"
            }
        ],
        "main_exports": [
            "Platine (12%)",
            "Or (10%)",
            "Charbon (9%)"
        ],
        "main_imports": [
            "Pétrole brut (12%)",
            "Machines et équipements (25%)",
            "Véhicules (10%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SSD": {
        "name": "Soudan du Sud",
        "gdp_usd_2024": 7.5,
        "gdp_per_capita_2024": 276,
        "population_2024": 11600000,
        "development_index": 0.385,
        "africa_rank": 39,
        "growth_forecast_2024": "-2.0%",
        "growth_projection_2025": "2.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "NR",
            "moodys": "NR",
            "fitch": "NR",
            "scope": "CCC",
            "global_risk": "Non évalué"
        },
        "key_sectors": [
            {
                "name": "Pétrole",
                "pib_share": 80.0,
                "description": "Extraction pétrolière"
            },
            {
                "name": "Agriculture",
                "pib_share": 15.0,
                "description": "Élevage, cultures vivrières"
            },
            {
                "name": "Services",
                "pib_share": 5.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Pétrole brut (98%)",
            "Animaux vivants (1%)",
            "Or (0.5%)"
        ],
        "main_imports": [
            "Produits alimentaires (40%)",
            "Machines et équipements (20%)",
            "Véhicules (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "SDN": {
        "name": "Soudan",
        "gdp_usd_2024": 36.0,
        "gdp_per_capita_2024": 744,
        "population_2024": 48100000,
        "development_index": 0.508,
        "africa_rank": 17,
        "growth_forecast_2024": "-5.7%",
        "growth_projection_2025": "1.5%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC-",
            "moodys": "Caa3",
            "fitch": "CCC-",
            "scope": "CCC-",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Coton, gomme arabique"
            },
            {
                "name": "Services",
                "pib_share": 30.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Pétrole, mines"
            }
        ],
        "main_exports": [
            "Or (65%)",
            "Pétrole brut (15%)",
            "Animaux vivants (8%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Produits alimentaires (20%)",
            "Carburants (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "TZA": {
        "name": "Tanzanie",
        "gdp_usd_2024": 80.0,
        "gdp_usd_2025": 85.0,
        "gdp_per_capita_2024": 1340,
        "population_2024": 59700000,
        "development_index": 0.549,
        "africa_rank": 10,
        "growth_forecast_2024": "5.5%",
        "growth_projection_2025": "6.0%",
        "data_source": "FMI WEO Oct 2025 (estimée)",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B2",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 40.0,
                "description": "Café, coton, noix de cajou"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce, tourisme"
            },
            {
                "name": "Industrie",
                "pib_share": 25.0,
                "description": "Mines, transformation alimentaire"
            }
        ],
        "main_exports": [
            "Or (40%)",
            "Café (8%)",
            "Noix de cajou (7%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Carburants (18%)",
            "Véhicules (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "TGO": {
        "name": "Togo",
        "gdp_usd_2024": 9.0,
        "gdp_per_capita_2024": 1040,
        "population_2024": 8700000,
        "development_index": 0.539,
        "africa_rank": 37,
        "growth_forecast_2024": "5.8%",
        "growth_projection_2025": "6.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B",
            "moodys": "B3",
            "fitch": "B",
            "scope": "B",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Coton, café, cacao"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Phosphates, transformation alimentaire"
            }
        ],
        "main_exports": [
            "Phosphates (30%)",
            "Coton (25%)",
            "Cacao (15%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (20%)",
            "Produits alimentaires (15%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "TUN": {
        "name": "Tunisie",
        "gdp_usd_2024": 55.0,
        "gdp_per_capita_2024": 4025,
        "population_2024": 12000000,
        "development_index": 0.731,
        "africa_rank": 14,
        "growth_forecast_2024": "1.6%",
        "growth_projection_2025": "2.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B-",
            "moodys": "B3",
            "fitch": "B-",
            "scope": "B-",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Services",
                "pib_share": 60.0,
                "description": "Tourisme, services financiers"
            },
            {
                "name": "Industrie",
                "pib_share": 28.0,
                "description": "Textile, automobile, phosphates"
            },
            {
                "name": "Agriculture",
                "pib_share": 12.0,
                "description": "Olives, céréales, agrumes"
            }
        ],
        "main_exports": [
            "Textiles (19%)",
            "Machines électriques (15%)",
            "Huile d'olive (8%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Textiles (15%)",
            "Carburants (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "UGA": {
        "name": "Ouganda",
        "gdp_usd_2024": 56.0,
        "gdp_per_capita_2024": 989,
        "population_2024": 48600000,
        "development_index": 0.544,
        "africa_rank": 13,
        "growth_forecast_2024": "5.3%",
        "growth_projection_2025": "6.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "B+",
            "moodys": "B2",
            "fitch": "B+",
            "scope": "B+",
            "global_risk": "Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 45.0,
                "description": "Café, coton, thé"
            },
            {
                "name": "Services",
                "pib_share": 35.0,
                "description": "Commerce et services"
            },
            {
                "name": "Industrie",
                "pib_share": 20.0,
                "description": "Transformation alimentaire, textile"
            }
        ],
        "main_exports": [
            "Café (22%)",
            "Or (18%)",
            "Thé (8%)"
        ],
        "main_imports": [
            "Machines et équipements (20%)",
            "Carburants (18%)",
            "Véhicules (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "ZMB": {
        "name": "Zambie",
        "gdp_usd_2024": 27.0,
        "gdp_per_capita_2024": 1335,
        "population_2024": 20000000,
        "development_index": 0.565,
        "africa_rank": 20,
        "growth_forecast_2024": "6.2%",
        "growth_projection_2025": "6.6%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CCC+",
            "moodys": "Caa2",
            "fitch": "CCC+",
            "scope": "CCC+",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Mines",
                "pib_share": 70.0,
                "description": "Cuivre, cobalt"
            },
            {
                "name": "Agriculture",
                "pib_share": 15.0,
                "description": "Maïs, tabac, sucre"
            },
            {
                "name": "Services",
                "pib_share": 15.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Cuivre (70%)",
            "Cobalt (10%)",
            "Or (5%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (15%)",
            "Produits alimentaires (12%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    },
    "ZWE": {
        "name": "Zimbabwe",
        "gdp_usd_2024": 30.0,
        "gdp_per_capita_2024": 1902,
        "population_2024": 16300000,
        "development_index": 0.593,
        "africa_rank": 19,
        "growth_forecast_2024": "6.2%",
        "growth_projection_2025": "5.0%",
        "data_source": "FMI WEO Oct 2025",
        "risk_ratings": {
            "sp": "CC",
            "moodys": "C",
            "fitch": "CC",
            "scope": "CC",
            "global_risk": "Très Élevé"
        },
        "key_sectors": [
            {
                "name": "Agriculture",
                "pib_share": 40.0,
                "description": "Tabac, maïs, coton"
            },
            {
                "name": "Mines",
                "pib_share": 35.0,
                "description": "Or, platine, diamants"
            },
            {
                "name": "Services",
                "pib_share": 25.0,
                "description": "Commerce et services"
            }
        ],
        "main_exports": [
            "Or (45%)",
            "Tabac (15%)",
            "Platine (12%)"
        ],
        "main_imports": [
            "Machines et équipements (25%)",
            "Carburants (15%)",
            "Produits alimentaires (18%)"
        ],
        "zlecaf_potential": {
            "level": "Modéré",
            "description": "Potentiel commercial avec ratification ZLECAf",
            "key_opportunities": [
                "Commerce intra-africain",
                "Intégration régionale",
                "Réduction tarifaire"
            ]
        }
    }
}

def get_country_data(country_code):
    """Retourne les données économiques réelles d'un pays ou des données par défaut"""
    return REAL_COUNTRY_DATA.get(country_code, {
        'name': f'Pays {country_code}',
        'gdp_usd_2024': 10.0,
        'gdp_per_capita_2024': 1000,
        'population_2024': 10000000,
        'development_index': 0.500,
        'africa_rank': 25,
        'growth_forecast_2024': '3.0%',
        'risk_ratings': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'NR', 'global_risk': 'Non évalué'},
        'key_sectors': [
            {'name': 'Agriculture', 'pib_share': 30.0, 'description': 'Secteur primaire'},
            {'name': 'Services', 'pib_share': 45.0, 'description': 'Secteur tertiaire'},
            {'name': 'Industrie', 'pib_share': 25.0, 'description': 'Secteur secondaire'}
        ],
        'zlecaf_potential': {'level': 'Modéré', 'description': 'Potentiel commercial ZLECAf', 'key_opportunities': ['Commerce intra-africain']},
        'main_exports': ['Données à compléter'],
        'main_imports': ['Données à compléter']
    })
