"""
SADC Mining Intelligence
=========================
Comprehensive mining sector intelligence for the Southern African
Development Community (SADC) region, covering the diamond, platinum,
copper, coal, and emerging critical-minerals value chains.
"""

SADC_MINING_INTELLIGENCE = {
    # -----------------------------------------------------------------------
    # Diamond pipeline
    # -----------------------------------------------------------------------
    "diamond_pipeline": {
        "description": "SADC hosts ~60% of world diamond production by value",
        "global_market_share_pct": 60,
        "producers": [
            {
                "country": "BWA",
                "operator": "Debswana (De Beers 50% / Government of Botswana 50%)",
                "mines": ["Jwaneng (world's richest by value)", "Orapa", "Letlhakane", "Damtshaa"],
                "annual_production_carats_million": 24.5,
                "notes": "Jwaneng alone accounts for >25% of De Beers global production",
            },
            {
                "country": "ZAF",
                "operator": "De Beers, Petra Diamonds, Ekati",
                "mines": ["Venetia", "Finsch", "Cullinan"],
                "annual_production_carats_million": 9.0,
                "notes": "Cullinan mine – source of famous 3,106-carat Cullinan diamond",
            },
            {
                "country": "NAM",
                "operator": "Namdeb (De Beers 50% / Government of Namibia 50%)",
                "mines": ["Namdeb Diamond Corporation", "Orange River Marine"],
                "annual_production_carats_million": 1.9,
                "notes": "Marine diamond mining unique globally; extremely high gem quality",
            },
            {
                "country": "AGO",
                "operator": "Endiama (state), Catoca (joint venture)",
                "mines": ["Catoca", "Lulo", "Luaxe (under development)"],
                "annual_production_carats_million": 8.8,
                "notes": "Major growth potential; Luaxe projected to be top-5 mine globally",
            },
            {
                "country": "ZWE",
                "operator": "Zimbabwe Consolidated Diamond Company (ZCDC)",
                "mines": ["Marange", "Murowa"],
                "annual_production_carats_million": 4.5,
                "notes": "Marange – large alluvial deposit; governance challenges historically",
            },
        ],
        "processing_hubs": [
            {
                "location": "Gaborone, Botswana",
                "operator": "DTC Botswana (De Beers sightholder system)",
                "activity": "Rough diamond sorting, valuation, and sightholder sales",
                "notes": "De Beers relocated global sightholder sales from London to Gaborone (2013)",
            },
            {
                "location": "Johannesburg, South Africa",
                "operator": "Multiple – SABS-certified cutters",
                "activity": "Cutting, polishing, jewellery manufacturing",
                "notes": "Diamond Exchange and Export Centre (DEEC) – duty-free zone",
            },
        ],
        "beneficiation_policy": "All SADC diamond producers require in-country sorting before export",
        "key_buyers": ["De Beers", "Alrosa", "Rio Tinto", "Lucara Diamond Corp"],
        "trade_routes": ["Antwerp (Belgium)", "Dubai", "Mumbai", "Hong Kong"],
    },

    # -----------------------------------------------------------------------
    # Platinum Group Metals (PGMs)
    # -----------------------------------------------------------------------
    "platinum_group_metals": {
        "description": "SADC holds >80% of world's known platinum reserves",
        "global_reserves_share_pct": 80,
        "pgm_elements": ["Platinum", "Palladium", "Rhodium", "Iridium", "Ruthenium", "Osmium"],
        "producers": [
            {
                "country": "ZAF",
                "reserves_tonnes": 63000,
                "mining_clusters": [
                    "Bushveld Igneous Complex – Rustenburg, Bafokeng, Marikana",
                    "Waterberg Project (Mokopane)",
                ],
                "major_companies": ["Anglo American Platinum (Amplats)", "Sibanye-Stillwater", "Northam Platinum", "Impala Platinum"],
                "annual_production_tonnes": 130,
            },
            {
                "country": "ZWE",
                "reserves_tonnes": 2800,
                "mining_clusters": ["Great Dyke (world's second largest PGM reef)"],
                "major_companies": ["Zimplats (Implats)", "Unki (Anglo American)"],
                "annual_production_tonnes": 14,
            },
        ],
        "applications": [
            "Automotive catalytic converters (~40% demand)",
            "Jewellery (~30%)",
            "Industrial catalysts (~20%)",
            "Hydrogen fuel cell electrodes (growing)",
        ],
        "beneficiation_opportunity": {
            "current_state": "Most PGMs exported as concentrate or matte",
            "opportunity": "Fuel cell component manufacturing, jewellery, catalysts",
            "sadc_initiatives": "South Africa Hydrogen Society Roadmap (2021)",
        },
    },

    # -----------------------------------------------------------------------
    # Copper Belt
    # -----------------------------------------------------------------------
    "copper_belt": {
        "description": "Central African copper belt spanning DRC and Zambia – world's largest copper deposit",
        "producers": [
            {
                "country": "ZMB",
                "annual_production_tonnes_thousand": 810,
                "mines": [
                    "Kansanshi (First Quantum Minerals)",
                    "Lumwana (Barrick Gold)",
                    "Nchanga (Konkola Copper Mines)",
                    "Mopani (Glencore / Government)",
                ],
                "smelters": ["Mufulira Smelter", "Nkana Smelter"],
                "notes": "Copperbelt Province – Kitwe, Ndola, Chingola towns",
            },
            {
                "country": "COD",
                "annual_production_tonnes_thousand": 2200,
                "mines": [
                    "Tenke Fungurume (Ivanhoe Mines/CMOC)",
                    "Kamoa-Kakula (Ivanhoe Mines – world's largest undeveloped high-grade copper)",
                    "Mutanda (Glencore)",
                ],
                "refineries": ["Lubumbashi refinery cluster"],
                "notes": "DRC is world's largest cobalt producer (>70% of global supply) – key battery material",
            },
            {
                "country": "ZWE",
                "annual_production_tonnes_thousand": 28,
                "mines": ["Trojan Nickel Mine (also copper)", "Murowa"],
                "notes": "Smaller copper producer; significant growth potential",
            },
        ],
        "cobalt_co_production": {
            "description": "Cobalt is essential for lithium-ion batteries (EVs, grid storage)",
            "drc_share_pct": 70,
            "strategic_importance": "Critical mineral for global energy transition",
        },
        "transport_routes": [
            {
                "name": "Dar-es-Salaam Corridor",
                "countries": ["ZMB", "TZA"],
                "mode": "Road + TAZARA Rail",
                "port": "Dar-es-Salaam",
            },
            {
                "name": "North-South Corridor",
                "countries": ["ZMB", "ZWE", "ZAF"],
                "mode": "Road + Rail",
                "port": "Durban (primary) + Richards Bay",
            },
            {
                "name": "Walvis Bay Corridor",
                "countries": ["ZMB", "NAM"],
                "mode": "Road + Rail (TransCaprivi)",
                "port": "Walvis Bay",
            },
            {
                "name": "Lobito Corridor",
                "countries": ["COD", "ZMB", "AGO"],
                "mode": "Benguela Railway (under rehabilitation)",
                "port": "Lobito (Angola)",
                "notes": "G7 Partnership for Global Infrastructure and Investment backing",
            },
        ],
    },

    # -----------------------------------------------------------------------
    # Coal
    # -----------------------------------------------------------------------
    "coal": {
        "description": "SADC is a major global coal producer and exporter",
        "producers": [
            {
                "country": "ZAF",
                "annual_production_mt": 248,
                "export_terminal": "Richards Bay Coal Terminal (RBCT) – 91 Mtpa capacity",
                "major_mines": ["Grootegeluk", "Optimum", "Goedgevonden"],
                "companies": ["Exxaro", "Anglo American", "Glencore", "Seriti Resources"],
            },
            {
                "country": "MOZ",
                "annual_production_mt": 10,
                "major_mines": ["Moatize Basin (Vale, Vulcan Resources)"],
                "export_route": "Nacala Corridor to Port Nacala",
            },
            {
                "country": "ZWE",
                "annual_production_mt": 5,
                "major_mines": ["Hwange Colliery (Hwange)"],
                "notes": "Hwange also supplies ZESA power stations",
            },
            {
                "country": "BWA",
                "annual_production_mt": 3,
                "major_mines": ["Morupule Colliery"],
                "notes": "Domestic power generation focus",
            },
        ],
        "power_pool": {
            "name": "Southern African Power Pool (SAPP)",
            "members": 12,
            "installed_capacity_gw": 65,
            "role": "Regional electricity trading and interconnection",
        },
    },

    # -----------------------------------------------------------------------
    # Critical / Emerging Minerals
    # -----------------------------------------------------------------------
    "critical_minerals": {
        "description": "SADC holds major reserves of minerals critical to the energy transition",
        "minerals": [
            {
                "mineral": "Cobalt",
                "key_country": "COD",
                "global_share_pct": 70,
                "use": "EV batteries, aerospace alloys",
            },
            {
                "mineral": "Lithium",
                "key_countries": ["ZWE", "NAM"],
                "status": "Significant reserves; growing production",
                "use": "EV batteries, energy storage",
            },
            {
                "mineral": "Manganese",
                "key_country": "ZAF",
                "global_share_pct": 35,
                "use": "Steel alloys, battery cathodes (LMO)",
            },
            {
                "mineral": "Chromium",
                "key_country": "ZAF",
                "global_share_pct": 42,
                "use": "Stainless steel, ferro-chrome",
            },
            {
                "mineral": "Vanadium",
                "key_country": "ZAF",
                "global_share_pct": 27,
                "use": "Steel strengthening, vanadium flow batteries",
            },
            {
                "mineral": "Rare Earth Elements",
                "key_countries": ["ZAF", "NAM", "MOZ", "TZA"],
                "status": "Exploration stage",
                "use": "Wind turbines, EV motors",
            },
        ],
        "beneficiation_strategy": {
            "sadc_position": "SADC member states are shifting from raw mineral exports to beneficiation",
            "examples": [
                "Zimbabwe lithium – smelting and battery grade lithium carbonate",
                "South Africa manganese – ferro-manganese smelting",
                "DRC cobalt – cobalt hydroxide to refined cobalt",
            ],
        },
    },
}

# ---------------------------------------------------------------------------
# Mining regulatory overview per country
# ---------------------------------------------------------------------------

MINING_REGULATORY_OVERVIEW = {
    "ZAF": {
        "primary_law": "Mineral and Petroleum Resources Development Act (MPRDA, 2002)",
        "regulator": "DMRE (Department of Mineral Resources and Energy)",
        "royalty_system": "Ad valorem – 0.5% to 7% depending on mineral",
        "bbbee_requirement": "26% HDSA ownership for new mineral rights",
    },
    "BWA": {
        "primary_law": "Mines and Minerals Act (2011)",
        "regulator": "Department of Mines",
        "royalty_system": "10% on diamonds; 3–5% on other minerals",
    },
    "ZMB": {
        "primary_law": "Mines and Minerals Development Act (2015)",
        "regulator": "Zambia Environmental Management Agency (ZEMA) + MCTI",
        "royalty_system": "5.5–8.5% sliding scale on copper based on price",
    },
    "COD": {
        "primary_law": "Mining Code (Law No. 007/2002, amended 2018)",
        "regulator": "SAEMAPE + CAMI",
        "royalty_system": "2% base + super-profit levy on strategic minerals",
    },
    "ZWE": {
        "primary_law": "Mines and Minerals Act (Chapter 21:05)",
        "regulator": "Ministry of Mines and Mining Development",
        "royalty_system": "1–15% depending on mineral category",
    },
    "NAM": {
        "primary_law": "Minerals (Prospecting and Mining) Act (1992)",
        "regulator": "Ministry of Mines and Energy",
        "royalty_system": "2% on base metals; 10% on diamonds",
    },
}
