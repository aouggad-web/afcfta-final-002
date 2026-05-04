"""
SADC Trade Protocols
=====================
Key trade agreements, protocols, and preferential arrangements covering
the Southern African Development Community (SADC) region.
"""

SADC_TRADE_PROTOCOLS = {
    # -----------------------------------------------------------------------
    # SADC Trade Protocol (1996 / Free Trade Area 2008)
    # -----------------------------------------------------------------------
    "sadc_trade_protocol": {
        "name": "SADC Trade Protocol",
        "signed": 1996,
        "fta_effective": 2008,
        "scope": "Goods trade liberalisation among SADC member states",
        "tariff_elimination": {
            "target": "85% of intra-SADC trade tariff-free by 2012",
            "achieved": True,
            "remaining": "Sensitive products list (~15%) – phased reduction schedule",
        },
        "rules_of_origin": {
            "general_rule": "25% minimum value addition in SADC",
            "wholly_obtained": "Products entirely produced in SADC",
            "cumulation": "SADC cumulation allowed for inputs from member states",
        },
        "sensitive_products": {
            "description": "Products excluded or on slower liberalisation schedule",
            "examples": ["textiles", "clothing", "sugar", "certain agricultural products"],
            "note": "South Africa maintains longer phase-down for sensitive sectors",
        },
        "trade_facilitation": {
            "osbp_programme": "One-Stop Border Post implementation across SADC",
            "customs_harmonisation": "SADC Customs Modernisation Programme",
            "e_certificate_of_origin": "Electronic CoO system under development",
        },
        "members": ["ZAF", "BWA", "NAM", "LSO", "SWZ", "ZMB", "ZWE", "MOZ", "MWI", "TZA", "AGO", "COD", "MUS", "MDG", "SYC", "COM"],
    },

    # -----------------------------------------------------------------------
    # SACU Agreement (2002)
    # -----------------------------------------------------------------------
    "sacu_agreement": {
        "name": "Southern African Customs Union Agreement (2002)",
        "signed": 2002,
        "predecessor": "Original SACU Agreement of 1910",
        "members": ["ZAF", "BWA", "NAM", "LSO", "SWZ"],
        "key_provisions": {
            "common_external_tariff": {
                "description": "Single CET applied by all SACU members to non-SACU imports",
                "administered_by": "South Africa (SARS) on behalf of SACU",
                "tariff_book": "South Africa Customs and Excise Act Schedule 1",
            },
            "free_internal_trade": {
                "description": "Zero tariff on goods moving between SACU members",
                "exceptions": "Excise duties collected at point of consumption",
            },
            "revenue_sharing": {
                "customs_component": "48% of SACU customs revenue pool",
                "excise_component": "23% of SACU excise revenue pool",
                "development_component": "15% earmarked for BLNS (Botswana, Lesotho, Namibia, Eswatini)",
                "distribution_formula": "Based on intra-SACU trade flows and GDP",
                "note": "BLNS countries receive disproportionate share relative to GDP due to development component",
            },
            "common_policies": [
                "Customs procedures harmonisation",
                "Trade facilitation",
                "Rules of origin",
                "Industrial development policy coordination",
            ],
        },
        "institutions": {
            "council_of_ministers": "Policy oversight body",
            "customs_union_commission": "Technical coordination",
            "secretariat": "Windhoek, Namibia",
            "tariff_board": "Recommends tariff changes",
        },
        "strengths": [
            "Oldest functioning customs union globally (since 1910)",
            "Deep economic integration – common exchange rate zone (ZAR)",
            "Streamlined intra-SACU trade",
        ],
        "challenges": [
            "Revenue sharing tensions (BLNS argue formula undervalues their contribution)",
            "South Africa dominates policy-setting",
            "Divergent development levels within SACU",
        ],
    },

    # -----------------------------------------------------------------------
    # SADC Finance and Investment Protocol (2006)
    # -----------------------------------------------------------------------
    "sadc_finance_investment_protocol": {
        "name": "SADC Finance and Investment Protocol",
        "signed": 2006,
        "scope": "Investment protection and financial integration",
        "key_provisions": {
            "investment_protection": "Non-discrimination, fair and equitable treatment, expropriation protection",
            "payment_systems": "Regional Payment Settlement System (SIRESS)",
            "siress": {
                "name": "SADC Integrated Regional Electronic Settlement System",
                "launched": 2013,
                "purpose": "Real-time settlement of cross-border transactions in ZAR",
                "members": 8,
            },
            "capital_flows": "Progressive liberalisation of capital account",
        },
    },

    # -----------------------------------------------------------------------
    # SADC-EAC-COMESA Tripartite FTA (T-FTA)
    # -----------------------------------------------------------------------
    "tripartite_fta": {
        "name": "Tripartite Free Trade Area (T-FTA)",
        "blocs": ["SADC", "EAC", "COMESA"],
        "signed": 2015,
        "status": "Phase 1 in force; Phase 2 (services, IP) under negotiation",
        "coverage": "26 countries + 625 million people + USD 1.2 trillion GDP",
        "tariff_elimination": "85% of tariff lines over 8 years from entry into force",
        "significance": "Largest FTA on the African continent prior to AfCFTA",
        "harmonised_rules": [
            "Common rules of origin",
            "Harmonised customs procedures",
            "Mutual recognition of certificates of conformity",
        ],
    },

    # -----------------------------------------------------------------------
    # AfCFTA (covers all SADC members)
    # -----------------------------------------------------------------------
    "afcfta": {
        "name": "African Continental Free Trade Area (AfCFTA)",
        "operational": "January 2021",
        "sadc_coverage": "All 16 SADC member states are AfCFTA signatories",
        "tariff_elimination": {
            "standard_countries": "90% of tariff lines – duty-free within 5 years",
            "ldc_countries": "90% of tariff lines – duty-free within 10 years",
            "sadc_ldc_members": ["AGO", "ZMB", "COD", "LSO", "MOZ", "MDG", "MWI", "TZA", "COM"],
        },
        "relationship_with_sadc": {
            "note": "AfCFTA aims to consolidate existing RECs (SADC, EAC, ECOWAS, etc.)",
            "transition": "Countries can maintain deeper integration within their REC",
        },
        "services": "Services protocol under negotiation (5 priority sectors: financial, transport, tourism, communications, business)",
    },

    # -----------------------------------------------------------------------
    # EU-SADC Economic Partnership Agreement (EPA)
    # -----------------------------------------------------------------------
    "eu_sadc_epa": {
        "name": "EU-SADC Economic Partnership Agreement",
        "signed": 2016,
        "in_force": 2016,
        "sadc_epa_group_members": ["ZAF", "BWA", "NAM", "LSO", "SWZ", "MOZ"],
        "key_provisions": {
            "eu_access": "Duty-free, quota-free access for substantially all SADC goods to EU",
            "sadc_liberalisation": "Progressive opening of SADC markets to EU goods",
            "special_provisions": {
                "south_africa": "Market access terms negotiated under TDCA (Trade, Development and Cooperation Agreement)",
                "mozambique": "EBA (Everything But Arms) backstop as LDC",
            },
        },
        "agricultural_provisions": {
            "sugar": "SADC sugar – duty-free access to EU (replacing ACP sugar protocol)",
            "fisheries": "Rules of origin for fish processing",
            "wine": "South African wine – reduced EU tariffs",
        },
    },

    # -----------------------------------------------------------------------
    # AGOA (US Generalized System of Preferences for sub-Saharan Africa)
    # -----------------------------------------------------------------------
    "agoa": {
        "name": "African Growth and Opportunity Act (AGOA)",
        "signed": 2000,
        "current_extension_to": 2025,
        "sadc_beneficiaries": ["ZAF", "BWA", "NAM", "LSO", "SWZ", "MOZ", "MWI", "TZA", "ZMB", "MDG", "MUS"],
        "key_benefit": "Duty-free access for 6,500+ products to US market",
        "textile_rule": "Third-country fabric rule allows AGOA LDC garments from Asian fabric",
        "key_exporters": {
            "ZAF": "Vehicles, auto parts, agricultural products",
            "LSO": "Garments and textiles (major AGOA user)",
            "SWZ": "Sugar and textiles",
            "NAM": "Fish and seafood",
        },
    },
}

# -----------------------------------------------------------------------
# Key trade statistics
# -----------------------------------------------------------------------

SADC_TRADE_STATISTICS = {
    "intra_sadc_trade_share_pct": 19,
    "total_sadc_gdp_usd_billion": 800,
    "total_sadc_trade_usd_billion": 350,
    "largest_economy": "ZAF",
    "largest_trader": "ZAF",
    "top_intra_sadc_trade_routes": [
        {"from": "ZAF", "to": "ZWE", "value_usd_billion": 2.5},
        {"from": "ZAF", "to": "ZMB", "value_usd_billion": 1.8},
        {"from": "ZAF", "to": "MOZ", "value_usd_billion": 1.5},
        {"from": "ZAF", "to": "NAM", "value_usd_billion": 2.0},
        {"from": "ZAF", "to": "BWA", "value_usd_billion": 3.2},
    ],
    "top_export_products": [
        "gold", "diamonds", "platinum", "copper", "coal",
        "vehicles_and_parts", "machinery", "food_and_beverages",
        "tobacco", "cut_flowers",
    ],
    "main_external_partners": ["China", "EU", "USA", "India", "UAE"],
}
