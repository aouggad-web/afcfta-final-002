"""
SADC Transport Corridors
========================
Logistics intelligence for the Southern African Development Community's
key transport corridors, one-stop border posts, and port infrastructure.
"""

SADC_TRANSPORT_CORRIDORS = {
    # -----------------------------------------------------------------------
    # North-South Corridor (Cape to Cairo)
    # -----------------------------------------------------------------------
    "north_south": {
        "name": "North-South Corridor",
        "alias": "Cape-to-Cairo Corridor (southern section)",
        "total_length_km": 3400,
        "countries": ["ZAF", "ZWE", "ZMB", "TZA", "COD"],
        "anchor_ports": ["Durban (ZAF)", "Richards Bay (ZAF)"],
        "key_border_posts": [
            {
                "name": "Beitbridge",
                "countries": ["ZAF", "ZWE"],
                "type": "one_stop_border_post",
                "status": "Operational (new infrastructure 2021)",
            },
            {
                "name": "Chirundu",
                "countries": ["ZWE", "ZMB"],
                "type": "one_stop_border_post",
                "status": "Operational – first OSBP in Africa (2009)",
            },
            {
                "name": "Nakonde / Tunduma",
                "countries": ["ZMB", "TZA"],
                "type": "border_post",
                "status": "High volume; OSBP under construction",
            },
        ],
        "mode": ["road", "rail"],
        "commodities": ["copper", "general_cargo", "fuel", "coal", "agricultural"],
        "annual_trade_volume_usd_billion": 25,
        "key_bottlenecks": [
            "Beitbridge – historically severe congestion (resolved by new infrastructure)",
            "Chirundu bridge – single-lane bridge limits capacity",
            "Rail capacity constraints Bulawayo–Beit Bridge",
        ],
        "investment_projects": [
            "Lusaka-Ndola dual carriageway (Zambia)",
            "Beitbridge border rehabilitation (completed 2021)",
            "North-South Corridor fibre optic backbone",
        ],
    },

    # -----------------------------------------------------------------------
    # Beira Corridor
    # -----------------------------------------------------------------------
    "beira": {
        "name": "Beira Corridor",
        "total_length_km": 620,
        "countries": ["ZWE", "MOZ"],
        "anchor_port": "Beira (MOZ) – natural hinterland port for Zimbabwe",
        "key_border_posts": [
            {
                "name": "Forbes / Machipanda",
                "countries": ["ZWE", "MOZ"],
                "type": "border_post",
                "status": "Operational",
            },
        ],
        "mode": ["road", "rail", "pipeline"],
        "commodities": ["fuel", "general_cargo", "fertilisers", "tobacco"],
        "pipeline": "CPMZ petroleum pipeline (Beira to Harare, 331 km)",
        "notes": "Critical for Zimbabwe fuel and general cargo imports",
        "development_projects": [
            "Beira port deepening project",
            "Sena rail line rehabilitation (Moatize coal)",
        ],
    },

    # -----------------------------------------------------------------------
    # Nacala Corridor
    # -----------------------------------------------------------------------
    "nacala": {
        "name": "Nacala Corridor",
        "total_length_km": 1580,
        "countries": ["MWI", "MOZ", "ZMB"],
        "anchor_port": "Nacala (MOZ) – deepwater port (14m draft, no tidal constraint)",
        "key_border_posts": [
            {
                "name": "Nayuchi / Entre-Lagos",
                "countries": ["MWI", "MOZ"],
                "type": "border_post",
                "status": "Rail and road crossing",
            },
            {
                "name": "Chipata / Mchinji",
                "countries": ["ZMB", "MWI"],
                "type": "border_post",
                "status": "Operational",
            },
        ],
        "mode": ["road", "rail"],
        "rail_operator": "CLN (Corredor de Nacala Logística)",
        "commodities": ["coal", "fertilisers", "general_cargo", "tobacco"],
        "notes": "Nacala has competitive advantages over Beira due to deepwater draft",
        "development_projects": [
            "Nacala Logistics Corridor (Vale-DFID-GOM funded)",
            "Nacala port container terminal expansion",
        ],
    },

    # -----------------------------------------------------------------------
    # Dar-es-Salaam Corridor
    # -----------------------------------------------------------------------
    "dar_es_salaam": {
        "name": "Dar-es-Salaam Corridor (Central Corridor)",
        "total_length_km": 2500,
        "countries": ["TZA", "ZMB", "COD", "RWA", "BDI", "UGA"],
        "anchor_port": "Dar-es-Salaam (TZA) – largest port in East/Central Africa",
        "key_border_posts": [
            {
                "name": "Kasumbalesa",
                "countries": ["ZMB", "COD"],
                "type": "border_post",
                "status": "High volume copper corridor post",
            },
        ],
        "mode": ["road", "rail"],
        "rail_network": "TAZARA (Tanzania-Zambia Railway Authority) – 1,860 km",
        "commodities": ["copper", "cobalt", "consumer_goods", "fuel", "mining_equipment"],
        "annual_trade_volume_usd_billion": 18,
        "notes": "Critical for DRC mineral exports; TAZARA rail under-utilised vs road",
    },

    # -----------------------------------------------------------------------
    # Lobito Corridor
    # -----------------------------------------------------------------------
    "lobito": {
        "name": "Lobito Corridor (Benguela Railway)",
        "total_length_km": 1344,
        "countries": ["AGO", "ZMB", "COD"],
        "anchor_port": "Lobito (AGO) – shortest route for DRC/Zambia copper to Atlantic",
        "key_border_posts": [
            {
                "name": "Jimbe / Luau",
                "countries": ["AGO", "COD"],
                "type": "rail_border",
                "status": "Under rehabilitation",
            },
        ],
        "mode": ["rail", "road"],
        "rail_operator": "CFB (Caminho de Ferro de Benguela)",
        "commodities": ["copper", "cobalt", "minerals", "general_cargo"],
        "status": "Under rehabilitation (G7 PGII investment – USD 1 billion+)",
        "strategic_importance": "Shortest Atlantic route for Copperbelt minerals – 30% shorter than Dar-es-Salaam route",
        "development_projects": [
            "G7 Partnership for Global Infrastructure (PGII) – Lobito Corridor",
            "Extension to Zambia Copperbelt (new track)",
            "Extension towards DRC Kamoa-Kakula mining area",
        ],
    },

    # -----------------------------------------------------------------------
    # Walvis Bay Corridor
    # -----------------------------------------------------------------------
    "walvis_bay": {
        "name": "Walvis Bay Corridors (Trans-Caprivi / Trans-Kalahari / Trans-Cunene)",
        "countries": ["NAM", "BWA", "ZMB", "ZAF"],
        "anchor_port": "Walvis Bay (NAM) – key Atlantic port with 30-day shorter route vs Durban",
        "sub_corridors": [
            {
                "name": "Trans-Caprivi Corridor",
                "countries": ["NAM", "ZMB", "ZWE"],
                "length_km": 1900,
                "mode": ["road"],
            },
            {
                "name": "Trans-Kalahari Corridor",
                "countries": ["NAM", "BWA", "ZAF"],
                "length_km": 1500,
                "mode": ["road"],
            },
            {
                "name": "Trans-Cunene Corridor",
                "countries": ["NAM", "AGO"],
                "length_km": 700,
                "mode": ["road"],
            },
        ],
        "port_specs": {
            "draft_m": 14.5,
            "capacity_teu_annual": 500000,
            "container_terminal": "Walvis Bay Container Terminal (WBCT)",
        },
        "commodities": ["copper", "minerals", "general_cargo", "vehicles"],
        "advantage": "Shorter sea route to Americas compared to Durban (saves ~30 transit days)",
    },

    # -----------------------------------------------------------------------
    # One-Stop Border Posts (OSBP) overview
    # -----------------------------------------------------------------------
    "one_stop_border_posts": {
        "description": "SADC One-Stop Border Post (OSBP) programme to reduce border dwell times",
        "target": "Reduce average border crossing time from 2–3 days to <4 hours",
        "operational_osbps": [
            {"name": "Chirundu", "countries": ["ZWE", "ZMB"], "since": 2009},
            {"name": "Beitbridge", "countries": ["ZAF", "ZWE"], "since": 2021},
            {"name": "Kasumbalesa", "countries": ["ZMB", "COD"], "since": 2013},
            {"name": "Kazungula", "countries": ["ZMB", "BWA", "ZWE", "NAM"], "since": 2021, "note": "4-nation border – world's first multi-country OSBP"},
        ],
        "planned_osbps": [
            {"name": "Nakonde/Tunduma", "countries": ["ZMB", "TZA"]},
            {"name": "Mwami/Mchinji", "countries": ["ZMB", "MWI"]},
        ],
    },
}

# -----------------------------------------------------------------------
# Port profiles
# -----------------------------------------------------------------------

SADC_MAJOR_PORTS = {
    "Durban": {
        "country": "ZAF",
        "type": "container_bulk_general",
        "annual_teu": 2800000,
        "draft_m": 12.8,
        "hinterland": ["ZWE", "ZMB", "BWA", "MOZ"],
        "operator": "Transnet National Ports Authority",
    },
    "Richards Bay": {
        "country": "ZAF",
        "type": "dry_bulk_coal",
        "annual_tonnes_mt": 91,
        "draft_m": 19,
        "speciality": "World's largest coal export terminal",
        "operator": "Richards Bay Coal Terminal (RBCT)",
    },
    "Cape Town": {
        "country": "ZAF",
        "type": "container_general",
        "annual_teu": 900000,
        "draft_m": 12.8,
        "hinterland": ["ZAF Western Cape", "Namibia via road"],
    },
    "Walvis Bay": {
        "country": "NAM",
        "type": "container_general",
        "annual_teu": 500000,
        "draft_m": 14.5,
        "hinterland": ["BWA", "ZMB", "ZWE"],
        "advantage": "30-day shorter route to South America vs Durban",
    },
    "Nacala": {
        "country": "MOZ",
        "type": "deepwater_container_bulk",
        "annual_teu": 300000,
        "draft_m": 14,
        "hinterland": ["MWI", "ZMB"],
        "advantage": "No tidal constraints; natural deepwater",
    },
    "Beira": {
        "country": "MOZ",
        "type": "container_bulk_pipeline",
        "annual_teu": 200000,
        "draft_m": 8,
        "hinterland": ["ZWE", "ZMB", "MWI"],
        "constraint": "Shallow draft – dredging required periodically",
    },
    "Dar-es-Salaam": {
        "country": "TZA",
        "type": "container_general_bulk",
        "annual_teu": 800000,
        "draft_m": 11,
        "hinterland": ["ZMB", "MWI", "COD", "RWA", "BDI", "UGA"],
        "operator": "Tanzania Ports Authority (TPA)",
    },
    "Lobito": {
        "country": "AGO",
        "type": "container_bulk",
        "annual_teu": 200000,
        "draft_m": 13,
        "hinterland": ["COD", "ZMB"],
        "status": "Under expansion (G7 PGII backing)",
    },
    "Port Louis": {
        "country": "MUS",
        "type": "container_freeport",
        "annual_teu": 600000,
        "draft_m": 15,
        "role": "Transshipment hub for Indian Ocean and East Africa",
        "operator": "Mauritius Ports Authority",
    },
}
