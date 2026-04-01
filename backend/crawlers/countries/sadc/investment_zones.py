"""
SADC Investment Zones
======================
Special Economic Zones (SEZs), industrial parks, and investment incentive
data for all 16 SADC member states.
"""

SADC_INVESTMENT_ZONES = {
    # ------------------------------------------------------------------
    # ZAF – South Africa
    # ------------------------------------------------------------------
    "ZAF": {
        "country": "ZAF",
        "investment_framework": "Special Economic Zones Act (No. 16 of 2014)",
        "investment_body": "dtic (Department of Trade, Industry and Competition)",
        "zones": [
            {
                "name": "Coega Special Economic Zone",
                "location": "Port Elizabeth (Gqeberha), Eastern Cape",
                "type": "multi_sector_sez",
                "focus_sectors": ["automotive", "agro-processing", "energy", "logistics"],
                "incentives": [
                    "15% corporate tax (vs 27%)",
                    "Employment tax incentive",
                    "Accelerated depreciation (50:30:20)",
                    "Import duty rebates on production inputs",
                ],
                "operational_since": 2001,
            },
            {
                "name": "Dube TradePort SEZ",
                "location": "KwaZulu-Natal",
                "type": "air_cargo_logistics_sez",
                "focus_sectors": ["air_freight", "perishables", "manufacturing"],
                "incentives": [
                    "15% corporate tax",
                    "VAT exemption on imported inputs",
                    "Employment tax incentive",
                ],
                "operational_since": 2010,
            },
            {
                "name": "Richards Bay Industrial Development Zone",
                "location": "Richards Bay, KwaZulu-Natal",
                "type": "industrial_development_zone",
                "focus_sectors": ["aluminium_smelting", "chemicals", "minerals_processing"],
                "incentives": [
                    "Duty-free imports of production inputs",
                    "VAT zero-rating on exports",
                    "World-class coal terminal access",
                ],
                "operational_since": 2003,
            },
        ],
        "key_incentives": [
            "15% preferential corporate tax in SEZs",
            "Industrial Development Corporation financing",
            "Black Economic Empowerment requirements",
            "Technology Innovation Agency grants",
        ],
    },
    # ------------------------------------------------------------------
    # BWA – Botswana
    # ------------------------------------------------------------------
    "BWA": {
        "country": "BWA",
        "investment_framework": "Special Economic Zones Act (2015)",
        "investment_body": "BITC (Botswana Investment and Trade Centre)",
        "zones": [
            {
                "name": "Gaborone International Finance Service Centre",
                "location": "Gaborone",
                "type": "financial_services_sez",
                "focus_sectors": ["financial_services", "insurance", "asset_management"],
                "incentives": [
                    "0% corporate tax on international business",
                    "Fast-track business registration",
                    "No exchange controls",
                ],
            },
            {
                "name": "Diamond Trading Company Botswana (DTCB)",
                "location": "Gaborone",
                "type": "diamond_beneficiation_zone",
                "focus_sectors": ["diamond_cutting", "diamond_polishing", "jewellery"],
                "incentives": [
                    "Sightholder agreements with De Beers",
                    "Local beneficiation requirements",
                    "Preferential rough diamond access",
                ],
            },
            {
                "name": "Lobatse Agro-Industrial Hub",
                "location": "Lobatse",
                "type": "agro_industrial",
                "focus_sectors": ["beef_processing", "leather", "dairy"],
                "incentives": [
                    "Export Development Programme grants",
                    "Duty drawback on imported inputs",
                ],
            },
        ],
        "key_incentives": [
            "Citizen Economic Empowerment Programme",
            "International Financial Services Centre incentives",
            "Export Development Programme grants",
            "BURS streamlined customs procedures",
        ],
    },
    # ------------------------------------------------------------------
    # NAM – Namibia
    # ------------------------------------------------------------------
    "NAM": {
        "country": "NAM",
        "investment_framework": "Export Processing Zone Act (1995) + Investment Promotion Act (2016)",
        "investment_body": "NIPDB (Namibia Investment Promotion and Development Board)",
        "zones": [
            {
                "name": "Walvis Bay Export Processing Zone",
                "location": "Walvis Bay",
                "type": "export_processing_zone",
                "focus_sectors": ["fish_processing", "logistics", "light_manufacturing"],
                "incentives": [
                    "0% corporate tax (15-year holiday)",
                    "Duty-free imports of raw materials",
                    "0% withholding tax on dividends",
                    "VAT exemption",
                ],
            },
            {
                "name": "Walvis Bay Industrial Park",
                "location": "Walvis Bay",
                "type": "logistics_industrial",
                "focus_sectors": ["port_logistics", "cold_chain", "distribution"],
                "incentives": [
                    "Access to deepwater port (16m draft)",
                    "TransNamib rail connections",
                    "Trans-Caprivi corridor access",
                ],
            },
        ],
        "key_incentives": [
            "Export Processing Zone incentives",
            "Namibia Development Corporation funding",
            "Green hydrogen investment potential",
            "Walvis Bay – gateway to landlocked SADC states",
        ],
    },
    # ------------------------------------------------------------------
    # LSO – Lesotho
    # ------------------------------------------------------------------
    "LSO": {
        "country": "LSO",
        "investment_framework": "Investment Policy Act (2015)",
        "investment_body": "LNDC (Lesotho National Development Corporation)",
        "zones": [
            {
                "name": "Maseru Industrial Zone",
                "location": "Maseru",
                "type": "industrial_estate",
                "focus_sectors": ["textiles", "garments", "light_manufacturing"],
                "incentives": [
                    "AGOA duty-free access to US market",
                    "EU GSP+ preferences",
                    "Subsidised factory shells",
                ],
            },
        ],
        "key_incentives": [
            "AGOA third-country fabric rule – duty-free garment exports to USA",
            "Lesotho Highlands Water Project royalties",
            "Low corporate tax (10%)",
            "LNDC factory lease subsidies",
        ],
    },
    # ------------------------------------------------------------------
    # SWZ – Eswatini
    # ------------------------------------------------------------------
    "SWZ": {
        "country": "SWZ",
        "investment_framework": "Investment Promotion Act (1998)",
        "investment_body": "ESRIC (Eswatini Investment Promotion Authority)",
        "zones": [
            {
                "name": "Matsapha Industrial Estate",
                "location": "Matsapha",
                "type": "industrial_estate",
                "focus_sectors": ["textiles", "sugar_processing", "beverages"],
                "incentives": [
                    "10% corporate tax (reduced rate)",
                    "AGOA duty-free textile access",
                    "Streamlined customs at Oshoek border",
                ],
            },
        ],
        "key_incentives": [
            "AGOA beneficiary – textiles and sugar",
            "10% corporate tax for manufacturers",
            "Duty drawback on exported goods",
        ],
    },
    # ------------------------------------------------------------------
    # AGO – Angola
    # ------------------------------------------------------------------
    "AGO": {
        "country": "AGO",
        "investment_framework": "Private Investment Law 10/18 (2018)",
        "investment_body": "AIPEX (Agência de Investimento Privado e Promoção das Exportações)",
        "zones": [
            {
                "name": "Luanda-Bengo Special Economic Zone (ZEE)",
                "location": "Luanda-Bengo Province",
                "type": "multi_sector_sez",
                "focus_sectors": ["manufacturing", "logistics", "services"],
                "incentives": [
                    "Corporate tax 10% (vs 25% standard)",
                    "Import duty exemptions on production inputs",
                    "Accelerated depreciation",
                    "Dividend repatriation guarantees",
                ],
            },
            {
                "name": "Soyo Oil & Gas Free Zone",
                "location": "Soyo, Zaire Province",
                "type": "energy_free_zone",
                "focus_sectors": ["oil_gas", "petrochemicals", "logistics"],
                "incentives": [
                    "0% corporate tax",
                    "Free repatriation of profits",
                    "Duty-free imports of equipment",
                ],
            },
        ],
        "key_incentives": [
            "Reconstruction priority incentives",
            "Agricultural modernisation programme grants",
            "Infrastructure corridor investment packages",
            "Lobito Atlantic Railway corridor access",
        ],
    },
    # ------------------------------------------------------------------
    # ZMB – Zambia
    # ------------------------------------------------------------------
    "ZMB": {
        "country": "ZMB",
        "investment_framework": "Zambia Development Agency Act (2006)",
        "investment_body": "ZDA (Zambia Development Agency)",
        "zones": [
            {
                "name": "Lusaka South Multi-Facility Economic Zone",
                "location": "Lusaka",
                "type": "multi_sector_mfez",
                "focus_sectors": ["manufacturing", "agro_processing", "electronics"],
                "incentives": [
                    "0% corporate tax (5 years)",
                    "0% import duty on raw materials",
                    "0% VAT on exports",
                    "Employment tax credit",
                ],
            },
            {
                "name": "Chambishi Multi-Facility Economic Zone",
                "location": "Copperbelt Province",
                "type": "mining_industrial_mfez",
                "focus_sectors": ["copper_smelting", "metal_fabrication", "mining_equipment"],
                "incentives": [
                    "0% import duty on production inputs",
                    "0% corporate tax (5 years)",
                    "Rebate on VAT for exports",
                ],
            },
        ],
        "key_incentives": [
            "ZDA Multi-Facility Economic Zone incentives",
            "Copper beneficiation priority",
            "TAZARA rail to Dar-es-Salaam port",
            "North-South Corridor logistics hub",
        ],
    },
    # ------------------------------------------------------------------
    # ZWE – Zimbabwe
    # ------------------------------------------------------------------
    "ZWE": {
        "country": "ZWE",
        "investment_framework": "Zimbabwe Investment and Development Agency Act (2020)",
        "investment_body": "ZIDA (Zimbabwe Investment and Development Agency)",
        "zones": [
            {
                "name": "Beitbridge Border Post Special Economic Zone",
                "location": "Beitbridge",
                "type": "border_sez",
                "focus_sectors": ["logistics", "cross_border_trade", "warehousing"],
                "incentives": [
                    "Reduced corporate tax (15%)",
                    "Duty-free on production inputs",
                    "Expedited customs processing",
                ],
            },
            {
                "name": "Sunway City Special Economic Zone",
                "location": "Harare",
                "type": "technology_sez",
                "focus_sectors": ["ict", "fintech", "bpo"],
                "incentives": [
                    "Tax holiday (5 years)",
                    "Duty-free ICT equipment imports",
                ],
            },
        ],
        "key_incentives": [
            "ZIDA one-stop investment shop",
            "Beitbridge – key North-South corridor border post",
            "Victoria Falls tourism and MICE hub",
            "Mineral beneficiation incentives",
        ],
    },
    # ------------------------------------------------------------------
    # COD – DR Congo
    # ------------------------------------------------------------------
    "COD": {
        "country": "COD",
        "investment_framework": "Investment Code (Law No. 004/2002)",
        "investment_body": "ANAPI (Agence Nationale pour la Promotion des Investissements)",
        "zones": [
            {
                "name": "Zone Economique Spéciale de Maluku",
                "location": "Kinshasa-Maluku",
                "type": "industrial_sez",
                "focus_sectors": ["agro_industry", "manufacturing", "logistics"],
                "incentives": [
                    "10-year corporate tax holiday",
                    "Import duty exemptions",
                    "Guaranteed profit repatriation",
                ],
            },
        ],
        "key_incentives": [
            "ANAPI investment facilitation",
            "Mining Code 2018 – modernised mineral licensing",
            "Cobalt and lithium strategic mineral access",
            "Grand Inga hydropower development opportunity",
        ],
    },
    # ------------------------------------------------------------------
    # MUS – Mauritius
    # ------------------------------------------------------------------
    "MUS": {
        "country": "MUS",
        "investment_framework": "Investment Promotion Act (2000) + Finance Act updates",
        "investment_body": "EDB (Economic Development Board Mauritius)",
        "zones": [
            {
                "name": "Mauritius International Financial Centre",
                "location": "Port Louis",
                "type": "financial_services_hub",
                "focus_sectors": ["global_business", "banking", "asset_management", "fintech"],
                "incentives": [
                    "3% corporate tax on eligible income",
                    "Partial income exemption (80% on eligible foreign income)",
                    "No withholding tax on dividends/interest",
                    "Double taxation treaties (45+ countries)",
                ],
            },
            {
                "name": "Mauritius Freeport",
                "location": "Port Louis Harbour + Sir Seewoosagur Ramgoolam Airport",
                "type": "freeport_logistics",
                "focus_sectors": ["warehousing", "distribution", "transshipment", "light_manufacturing"],
                "incentives": [
                    "Duty-free operations",
                    "24/7 customs clearance",
                    "Transhipment hub benefits (Indian Ocean)",
                    "0% customs duty on freeport goods",
                ],
            },
        ],
        "key_incentives": [
            "Gateway to Africa position for international investors",
            "Mauritius Africa Fund (investment facilitation for Africa)",
            "Africa Investment and Trade Centre",
            "45+ double taxation treaties",
        ],
    },
    # ------------------------------------------------------------------
    # SYC – Seychelles
    # ------------------------------------------------------------------
    "SYC": {
        "country": "SYC",
        "investment_framework": "Investment Act (2013)",
        "investment_body": "Seychelles Investment Board (SIB)",
        "zones": [
            {
                "name": "Seychelles International Trade Zone (SITZ)",
                "location": "Mahé Island",
                "type": "free_trade_zone",
                "focus_sectors": ["yacht_servicing", "logistics", "light_manufacturing"],
                "incentives": [
                    "0% corporate tax on non-Seychelles income",
                    "Duty-free equipment imports",
                ],
            },
        ],
        "key_incentives": [
            "Tourism blue economy opportunity",
            "Fisheries licensing and processing",
            "Offshore financial services (non-bank financial centre)",
        ],
    },
    # ------------------------------------------------------------------
    # COM – Comoros
    # ------------------------------------------------------------------
    "COM": {
        "country": "COM",
        "investment_framework": "Investment Charter (2007)",
        "investment_body": "ANPI (Agence Nationale pour la Promotion des Investissements)",
        "zones": [],
        "key_incentives": [
            "Tax exemptions for priority sector investments",
            "Ylang-ylang and vanilla premium crop opportunity",
            "Blue economy (fishing, maritime tourism)",
        ],
    },
    # ------------------------------------------------------------------
    # MOZ – Mozambique
    # ------------------------------------------------------------------
    "MOZ": {
        "country": "MOZ",
        "investment_framework": "Investment Law (Law No. 3/93, updated 2021)",
        "investment_body": "CPI (Centro de Promoção de Investimentos)",
        "zones": [
            {
                "name": "Nacala Special Economic Zone",
                "location": "Nacala, Nampula Province",
                "type": "port_industrial_sez",
                "focus_sectors": ["agro_processing", "logistics", "manufacturing"],
                "incentives": [
                    "Corporate tax holiday (10 years)",
                    "Duty-free capital imports",
                    "Custom bonded warehousing",
                ],
            },
            {
                "name": "Beira Industrial Free Zone",
                "location": "Beira, Sofala Province",
                "type": "industrial_free_zone",
                "focus_sectors": ["logistics", "services", "light_manufacturing"],
                "incentives": [
                    "Reduced corporate tax (15%)",
                    "Duty-free imports of inputs",
                ],
            },
        ],
        "key_incentives": [
            "Nacala Corridor – rail link to Malawi and Zambia",
            "LNG natural gas project opportunities",
            "Agriculture land availability for large-scale farming",
            "Beira Corridor – link to Zimbabwe and beyond",
        ],
    },
    # ------------------------------------------------------------------
    # MDG – Madagascar
    # ------------------------------------------------------------------
    "MDG": {
        "country": "MDG",
        "investment_framework": "Investment Law (Law No. 2007-036)",
        "investment_body": "EDBM (Economic Development Board of Madagascar)",
        "zones": [
            {
                "name": "Antananarivo Export Processing Zone",
                "location": "Antananarivo",
                "type": "epz",
                "focus_sectors": ["textiles", "garments", "seafood_processing"],
                "incentives": [
                    "0% corporate tax (EPZ entities)",
                    "Duty-free imports of raw materials",
                    "VAT exemption on exports",
                    "AGOA and EU Everything But Arms access",
                ],
            },
        ],
        "key_incentives": [
            "AGOA and EU EBA duty-free access",
            "Vanilla – world's largest exporter",
            "Mining sector – nickel, cobalt, chromite",
            "EDBM one-stop-shop for investors",
        ],
    },
    # ------------------------------------------------------------------
    # MWI – Malawi
    # ------------------------------------------------------------------
    "MWI": {
        "country": "MWI",
        "investment_framework": "Investment and Export Promotion Act (2012)",
        "investment_body": "MIB (Malawi Investment and Trade Centre)",
        "zones": [
            {
                "name": "Lilongwe Industrial Zone",
                "location": "Lilongwe",
                "type": "industrial_zone",
                "focus_sectors": ["agro_processing", "textiles", "packaging"],
                "incentives": [
                    "Reduced corporate tax (30% → 15% for priority sectors)",
                    "Export allowance (25% of profit)",
                    "Import duty exemption on capital goods",
                ],
            },
        ],
        "key_incentives": [
            "Tobacco beneficiation opportunity",
            "Nacala Corridor access to Mozambican coast",
            "SADC trade protocol preferences",
            "MIB investment promotion services",
        ],
    },
    # ------------------------------------------------------------------
    # TZA – Tanzania (dual EAC/SADC)
    # ------------------------------------------------------------------
    "TZA": {
        "country": "TZA",
        "investment_framework": "Tanzania Investment Act (1997, updated 2022)",
        "investment_body": "TIC (Tanzania Investment Centre)",
        "zones": [
            {
                "name": "Benjamin William Mkapa Special Economic Zone",
                "location": "Dar-es-Salaam",
                "type": "multi_sector_sez",
                "focus_sectors": ["manufacturing", "agro_processing", "ict", "logistics"],
                "incentives": [
                    "0% corporate tax (10 years)",
                    "Duty-free imports of capital goods",
                    "VAT suspension on business inputs",
                ],
            },
            {
                "name": "Tanga Export Processing Zone",
                "location": "Tanga",
                "type": "epz",
                "focus_sectors": ["textiles", "sisal", "agro_processing"],
                "incentives": [
                    "0% corporate tax",
                    "Duty-free raw material imports",
                    "Streamlined port access",
                ],
            },
        ],
        "key_incentives": [
            "Dar-es-Salaam Corridor hub (DRC, Zambia, Uganda, Rwanda)",
            "TAZARA railway – Zambia copper export route",
            "Zanzibar – Blue Economy and spice tourism",
            "Natural gas offshore – LNG project pipeline",
        ],
    },
}
