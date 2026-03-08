"""
SADC Tariff Structures
=======================
Country-specific tariff rates and tax configurations for all 16 SADC member
states.  Follows the same layout used in the CEMAC / ECOWAS scrapers so that
the rest of the platform can consume the data uniformly.

Reference:
  - SACU Common External Tariff (South Africa SARS schedule)
  - SADC Trade Protocol preferences
  - Country-specific national tax legislation
"""

# ---------------------------------------------------------------------------
# SACU Common External Tariff bands
# ---------------------------------------------------------------------------

SACU_CET_BANDS = {
    "raw_materials": 0.0,
    "intermediate_goods": 5.0,
    "final_goods": 15.0,
    "luxury_goods": 30.0,
    "agricultural": 20.0,
    "textiles": 22.0,
    "automotive": 25.0,
}

# ---------------------------------------------------------------------------
# SADC Trade Protocol preferences
# ---------------------------------------------------------------------------

SADC_PREFERENCES = {
    "intra_sadc_reduction": 0.85,
    "ldc_preference": 0.70,
    "sensitive_products": 1.0,
    "rules_of_origin_min_value_addition": 25.0,
}

# ---------------------------------------------------------------------------
# Per-country tariff configurations
# (structure mirrors COUNTRY_CONFIGS in cemac_member_scraper.py)
# ---------------------------------------------------------------------------

COUNTRY_TARIFF_CONFIGS = {
    # ------------------------------------------------------------------
    # ZAF – South Africa (SACU anchor)
    # ------------------------------------------------------------------
    "ZAF": {
        "country": "ZAF",
        "country_name": "South Africa",
        "source": "SARS Schedule No. 1 Part 1",
        "source_url": "https://www.sars.gov.za/customs-and-excise/tariff-books/",
        "currency": "ZAR",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": True,
        "national_taxes": {
            "AD": {
                "code": "AD",
                "name": "Ad valorem customs duty",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "note": "Per SACU CET schedule",
            },
            "FUEL_LEVY": {
                "code": "FUEL_LEVY",
                "name": "Fuel levy (petroleum products only)",
                "rate": "specific",
                "type": "specific",
                "base": "per_litre",
            },
        },
        "additional_duties": {
            "anti_dumping": "variable – ITAC determination",
            "safeguard_duties": "temporary – Board of Tariffs ruling",
        },
        "notes": [
            "SACU Common External Tariff applies to all non-SACU imports",
            "VAT: 15% standard rate (zero-rated: basic foodstuffs, exports)",
            "Anti-dumping and countervailing duties per ITAC Board determinations",
            "Source: SARS Schedule No. 1 (customs duty) + Schedule No. 2 (anti-dumping)",
        ],
    },
    # ------------------------------------------------------------------
    # BWA – Botswana (SACU member)
    # ------------------------------------------------------------------
    "BWA": {
        "country": "BWA",
        "country_name": "Botswana",
        "source": "BURS + SACU CET",
        "source_url": "https://burs.org.bw",
        "currency": "BWP",
        "vat_rate": 12.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": True,
        "national_taxes": {
            "AD": {
                "code": "AD",
                "name": "Ad valorem customs duty (SACU CET)",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 12% standard rate (reduced from 14% in 2023)",
            "Free trade within SACU – no duties on intra-SACU goods",
            "Source: BURS (Botswana Unified Revenue Service) + sacu.int",
        ],
    },
    # ------------------------------------------------------------------
    # NAM – Namibia (SACU member)
    # ------------------------------------------------------------------
    "NAM": {
        "country": "NAM",
        "country_name": "Namibia",
        "source": "NamRA + SACU CET",
        "source_url": "https://www.namra.org.na",
        "currency": "NAD",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": True,
        "national_taxes": {
            "AD": {
                "code": "AD",
                "name": "Ad valorem customs duty (SACU CET)",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 15% standard rate",
            "Walvis Bay – strategic transshipment port with reduced dwell times",
            "Source: NamRA + sacu.int",
        ],
    },
    # ------------------------------------------------------------------
    # LSO – Lesotho (SACU member, LDC)
    # ------------------------------------------------------------------
    "LSO": {
        "country": "LSO",
        "country_name": "Lesotho",
        "source": "LRA + SACU CET",
        "source_url": "https://www.lra.org.ls",
        "currency": "LSL",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": True,
        "is_ldc": True,
        "national_taxes": {
            "AD": {
                "code": "AD",
                "name": "Ad valorem customs duty (SACU CET)",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 15% standard rate",
            "LDC: eligible for LDC tariff preferences under AfCFTA",
            "AGOA beneficiary – duty-free textile/apparel access to US market",
            "Source: LRA (Lesotho Revenue Authority) + sacu.int",
        ],
    },
    # ------------------------------------------------------------------
    # SWZ – Eswatini (SACU member)
    # ------------------------------------------------------------------
    "SWZ": {
        "country": "SWZ",
        "country_name": "Eswatini",
        "source": "SRA + SACU CET",
        "source_url": "https://www.sra.org.sz",
        "currency": "SZL",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": True,
        "national_taxes": {
            "AD": {
                "code": "AD",
                "name": "Ad valorem customs duty (SACU CET)",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 15% standard rate",
            "Sugar production – major export commodity",
            "Source: SRA (Eswatini Revenue Authority) + sacu.int",
        ],
    },
    # ------------------------------------------------------------------
    # AGO – Angola
    # ------------------------------------------------------------------
    "AGO": {
        "country": "AGO",
        "country_name": "Angola",
        "source": "Alfândega de Angola",
        "source_url": "https://alfandega.gov.ao",
        "currency": "AOA",
        "vat_rate": 14.0,
        "vat_name": "Imposto sobre o Valor Acrescentado (IVA)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": False,
        "is_ldc": True,
        "national_taxes": {
            "DD": {
                "code": "DD",
                "name": "Direitos Aduaneiros",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"raw_materials": 2.0, "intermediate": 5.0, "final": 20.0, "luxury": 30.0},
            },
            "IC": {
                "code": "IC",
                "name": "Imposto de Consumo (excise)",
                "rate": "variable",
                "type": "specific_categories",
                "base": "CIF + DD",
            },
        },
        "notes": [
            "Pauta Aduaneira de Angola – 4-band structure",
            "IVA: 14% standard (zero-rated: basic goods, exports)",
            "Oil sector: separate fiscal regime under Petroleum Activities Law",
            "Source: alfandega.gov.ao + minfin.gov.ao",
        ],
    },
    # ------------------------------------------------------------------
    # ZMB – Zambia
    # ------------------------------------------------------------------
    "ZMB": {
        "country": "ZMB",
        "country_name": "Zambia",
        "source": "Zambia Revenue Authority",
        "source_url": "https://www.zra.org.zm",
        "currency": "ZMW",
        "vat_rate": 16.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": False,
        "is_ldc": True,
        "national_taxes": {
            "CD": {
                "code": "CD",
                "name": "Customs Duty",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"zero": 0.0, "intermediate": 15.0, "final": 25.0},
            },
            "EL": {
                "code": "EL",
                "name": "Excise Levy (selected goods)",
                "rate": "variable",
                "type": "specific_categories",
                "base": "CIF",
            },
        },
        "notes": [
            "Zambia uses EAC-aligned tariff bands (0%, 15%, 25%)",
            "VAT: 16% standard rate",
            "Mining royalties: separate regime per Mines and Minerals Act",
            "Source: ZRA (Zambia Revenue Authority) customs schedule",
        ],
    },
    # ------------------------------------------------------------------
    # ZWE – Zimbabwe
    # ------------------------------------------------------------------
    "ZWE": {
        "country": "ZWE",
        "country_name": "Zimbabwe",
        "source": "ZIMRA",
        "source_url": "https://www.zimra.co.zw",
        "currency": "ZWG",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty + Surtax",
        "is_sacu": False,
        "national_taxes": {
            "CD": {
                "code": "CD",
                "name": "Customs Duty",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
            "ST": {
                "code": "ST",
                "name": "Surtax",
                "rate": 10.0,
                "type": "ad_valorem",
                "base": "CIF",
                "note": "Applies to certain manufactured goods",
            },
        },
        "notes": [
            "Multi-currency environment – USD commonly used for customs valuation",
            "VAT: 15% standard rate",
            "Surtax: 10% on selected categories to protect local industry",
            "Source: ZIMRA Customs Tariff Book",
        ],
    },
    # ------------------------------------------------------------------
    # COD – DR Congo (dual EAC/SADC)
    # ------------------------------------------------------------------
    "COD": {
        "country": "COD",
        "country_name": "DR Congo",
        "source": "DGRAD + DGDA",
        "source_url": "https://www.dgrad.cd",
        "currency": "CDF",
        "vat_rate": 16.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + Droits de Douane",
        "is_sacu": False,
        "is_ldc": True,
        "dual_membership": ["EAC", "SADC"],
        "national_taxes": {
            "DD": {
                "code": "DD",
                "name": "Droits de Douane",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
            "ID": {
                "code": "ID",
                "name": "Impôt à la Douane",
                "rate": 2.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "Dual EAC + SADC membership – applies EAC CET as primary schedule",
            "TVA: 16% standard rate",
            "Mining sector: separate royalty regime (Mining Code 2018)",
            "Source: DGRAD + DGDA (Direction Générale des Douanes)",
        ],
    },
    # ------------------------------------------------------------------
    # MUS – Mauritius
    # ------------------------------------------------------------------
    "MUS": {
        "country": "MUS",
        "country_name": "Mauritius",
        "source": "Mauritius Revenue Authority",
        "source_url": "https://www.mra.mu",
        "currency": "MUR",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": False,
        "national_taxes": {
            "CD": {
                "code": "CD",
                "name": "Customs Duty",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "note": "Mauritius has unilaterally reduced most MFN rates to 0-3%",
            },
        },
        "notes": [
            "Very open trade regime – most MFN rates at 0%",
            "VAT: 15% standard rate",
            "Global Business Licence: 3% corporate tax for international companies",
            "Free Port: duty-free manufacturing and logistics zone",
            "Source: MRA (Mauritius Revenue Authority)",
        ],
    },
    # ------------------------------------------------------------------
    # SYC – Seychelles
    # ------------------------------------------------------------------
    "SYC": {
        "country": "SYC",
        "country_name": "Seychelles",
        "source": "Seychelles Revenue Commission",
        "source_url": "https://src.gov.sc",
        "currency": "SCR",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": False,
        "national_taxes": {
            "CD": {
                "code": "CD",
                "name": "Customs Duty",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
            },
            "ET": {
                "code": "ET",
                "name": "Excise Tax (beverages, tobacco, vehicles)",
                "rate": "variable",
                "type": "specific_categories",
                "base": "CIF",
            },
        },
        "notes": [
            "Small island economy with significant tourism revenue",
            "VAT: 15% standard rate",
            "Fisheries: zero-rated for export processing",
            "Source: Seychelles Revenue Commission",
        ],
    },
    # ------------------------------------------------------------------
    # COM – Comoros
    # ------------------------------------------------------------------
    "COM": {
        "country": "COM",
        "country_name": "Comoros",
        "source": "Direction Générale des Douanes des Comores",
        "source_url": "https://dgdcom.km",
        "currency": "KMF",
        "vat_rate": 10.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + Droits de Douane",
        "is_sacu": False,
        "is_ldc": True,
        "national_taxes": {
            "DD": {
                "code": "DD",
                "name": "Droits de Douane",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"essential": 0.0, "basic": 5.0, "standard": 20.0, "luxury": 40.0},
            },
        },
        "notes": [
            "LDC: eligible for AfCFTA LDC preferences",
            "TVA: 10% (lower than regional average)",
            "Agriculture focus – vanilla, cloves, ylang-ylang",
            "Source: DGD Comores",
        ],
    },
    # ------------------------------------------------------------------
    # MOZ – Mozambique
    # ------------------------------------------------------------------
    "MOZ": {
        "country": "MOZ",
        "country_name": "Mozambique",
        "source": "Autoridade Tributária de Moçambique (AT)",
        "source_url": "https://www.at.gov.mz",
        "currency": "MZN",
        "vat_rate": 17.0,
        "vat_name": "Imposto sobre o Valor Acrescentado (IVA)",
        "vat_base": "CIF + Direitos Aduaneiros",
        "is_sacu": False,
        "is_ldc": True,
        "national_taxes": {
            "DA": {
                "code": "DA",
                "name": "Direitos Aduaneiros",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"zero": 0.0, "reduced": 2.5, "standard": 7.5, "high": 20.0},
            },
            "IS": {
                "code": "IS",
                "name": "Imposto Selectivo (excise)",
                "rate": "variable",
                "type": "specific_categories",
                "base": "CIF + DA",
            },
        },
        "notes": [
            "4-band tariff structure: 0%, 2.5%, 7.5%, 20%",
            "IVA: 17% standard rate",
            "Natural gas sector: separate licensing and fiscal regime",
            "Nacala Corridor: key logistics route to Malawi and Zambia",
            "Source: AT Moçambique pauta aduaneira",
        ],
    },
    # ------------------------------------------------------------------
    # MDG – Madagascar
    # ------------------------------------------------------------------
    "MDG": {
        "country": "MDG",
        "country_name": "Madagascar",
        "source": "Direction Générale des Douanes Madagascar",
        "source_url": "https://www.douanes.mg",
        "currency": "MGA",
        "vat_rate": 20.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + Droits de Douane",
        "is_sacu": False,
        "is_ldc": True,
        "national_taxes": {
            "DD": {
                "code": "DD",
                "name": "Droits de Douane",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"zero": 0.0, "low": 5.0, "mid": 10.0, "high": 20.0},
            },
            "STAT": {
                "code": "STAT",
                "name": "Redevance Statistique",
                "rate": 0.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "TVA: 20% standard rate (higher than regional average)",
            "Vanilla: top global exporter – strategic agricultural export",
            "EPZ: Export Processing Zones for textiles",
            "Source: DGD Madagascar",
        ],
    },
    # ------------------------------------------------------------------
    # MWI – Malawi
    # ------------------------------------------------------------------
    "MWI": {
        "country": "MWI",
        "country_name": "Malawi",
        "source": "Malawi Revenue Authority",
        "source_url": "https://www.mra.mw",
        "currency": "MWK",
        "vat_rate": 16.5,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": False,
        "is_ldc": True,
        "national_taxes": {
            "CD": {
                "code": "CD",
                "name": "Customs Duty",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"zero": 0.0, "low": 10.0, "mid": 25.0},
            },
            "EL": {
                "code": "EL",
                "name": "Excise Levy",
                "rate": "variable",
                "type": "specific_categories",
                "base": "CIF",
            },
        },
        "notes": [
            "Tobacco: dominant export crop (>50% of export earnings)",
            "VAT: 16.5% standard rate",
            "Nacala Corridor access – route to Mozambican coast",
            "Source: MRA (Malawi Revenue Authority) Customs Tariff",
        ],
    },
    # ------------------------------------------------------------------
    # TZA – Tanzania (dual EAC/SADC)
    # ------------------------------------------------------------------
    "TZA": {
        "country": "TZA",
        "country_name": "Tanzania",
        "source": "Tanzania Revenue Authority",
        "source_url": "https://www.tra.go.tz",
        "currency": "TZS",
        "vat_rate": 18.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + Customs Duty",
        "is_sacu": False,
        "is_ldc": True,
        "dual_membership": ["EAC", "SADC"],
        "national_taxes": {
            "CD": {
                "code": "CD",
                "name": "EAC Common External Tariff",
                "rate": "variable",
                "type": "ad_valorem",
                "base": "CIF",
                "bands": {"zero": 0.0, "intermediate": 10.0, "final": 25.0, "sensitive": 35.0},
            },
        },
        "notes": [
            "Dual EAC + SADC membership – applies EAC CET as primary schedule",
            "VAT: 18% standard rate",
            "Dar-es-Salaam: major port servicing DRC, Zambia, Uganda",
            "Source: TRA (Tanzania Revenue Authority)",
        ],
    },
}
