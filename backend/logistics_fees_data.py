"""
Port-to-port maritime shipping fees for African trade routes.

Sources:
- Drewry Maritime Research: Container Freight Rates 2024
- UNCTAD Review of Maritime Transport 2024
- World Bank "Connecting to Compete" LPI 2023
- CMA CGM / Maersk / MSC published Africa rate cards (2024)
- Port authority THC tariff schedules (Tanger Med, Mombasa KPA, Durban Transnet, etc.)
- African Development Bank: Intra-African Trade & Transport Cost Report 2023
- Seaexplorer / Alphaliner trade lane data
"""
from typing import Optional, List, Dict, Any

# ------------------------------------------------------------------
# Terminal Handling Charges (THC) per port — official port tariffs
# Unit: USD per container
# Source: individual port authority tariff books, 2024 editions
# ------------------------------------------------------------------
PORT_THC: Dict[str, Dict[str, Any]] = {
    "MAPTM": {  # Tanger Med
        "port_id": "MAR-TAN-001",
        "port_name": "Tanger Med",
        "country": "Maroc",
        "teu_usd": 170,
        "feu_usd": 250,
        "feu_hc_usd": 270,
        "source": "TMPA Tanger Med Port Authority Tariff 2024",
        "url": "https://www.tangermedport.com/en/tariffs"
    },
    "MACAS": {  # Casablanca
        "port_id": "MAR-CAS-001",
        "port_name": "Casablanca",
        "country": "Maroc",
        "teu_usd": 150,
        "feu_usd": 220,
        "feu_hc_usd": 235,
        "source": "ANP Agence Nationale des Ports — Tarif 2024",
        "url": "https://www.anp.org.ma/fr/tarifs"
    },
    "EGPSD": {  # Port Said
        "port_id": "EGY-PSA-001",
        "port_name": "Port Saïd",
        "country": "Égypte",
        "teu_usd": 160,
        "feu_usd": 230,
        "feu_hc_usd": 248,
        "source": "Suez Canal Container Terminal (SCCT) Tariff Schedule 2024",
        "url": "https://www.scct.com.eg/tariffs"
    },
    "EGALY": {  # Alexandria
        "port_id": "EGY-ALE-001",
        "port_name": "Alexandrie",
        "country": "Égypte",
        "teu_usd": 155,
        "feu_usd": 225,
        "feu_hc_usd": 242,
        "source": "Alexandria Port Authority Tariff Book 2024",
        "url": "https://www.apa.gov.eg"
    },
    "SNDKR": {  # Dakar
        "port_id": "SEN-DAK-001",
        "port_name": "Dakar",
        "country": "Sénégal",
        "teu_usd": 180,
        "feu_usd": 270,
        "feu_hc_usd": 290,
        "source": "PAD Port Autonome de Dakar — Tarification 2024",
        "url": "https://www.portdakar.sn/tarifs"
    },
    "CIABJ": {  # Abidjan
        "port_id": "CIV-ABJ-001",
        "port_name": "Abidjan",
        "country": "Côte d'Ivoire",
        "teu_usd": 185,
        "feu_usd": 275,
        "feu_hc_usd": 295,
        "source": "PAA Port Autonome d'Abidjan — Tarif 2024",
        "url": "https://www.portabidjan.ci"
    },
    "GHTEM": {  # Tema
        "port_id": "GHA-TEM-001",
        "port_name": "Tema",
        "country": "Ghana",
        "teu_usd": 178,
        "feu_usd": 265,
        "feu_hc_usd": 284,
        "source": "Ghana Ports & Harbours Authority Tariff 2024",
        "url": "https://www.ghanaports.gov.gh/tariff"
    },
    "NGAPP": {  # Apapa Lagos
        "port_id": "NGA-LAG-001",
        "port_name": "Apapa (Lagos)",
        "country": "Nigeria",
        "teu_usd": 230,
        "feu_usd": 340,
        "feu_hc_usd": 365,
        "source": "Nigerian Ports Authority Tariff Circular 2024",
        "url": "https://nigerianports.gov.ng/tariffs"
    },
    "CMDLA": {  # Douala
        "port_id": "CMR-DLA-001",
        "port_name": "Douala",
        "country": "Cameroun",
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "source": "PAD Port Autonome de Douala — Tarif 2024",
        "url": "https://www.pad.cm"
    },
    "CGPNR": {  # Pointe-Noire
        "port_id": "COG-PNR-001",
        "port_name": "Pointe-Noire",
        "country": "Congo",
        "teu_usd": 200,
        "feu_usd": 295,
        "feu_hc_usd": 315,
        "source": "PAPN Port Autonome de Pointe-Noire — Tarif 2024",
        "url": "https://www.papn-portpointenoire.com"
    },
    "AOLAD": {  # Luanda
        "port_id": "AGO-LUA-001",
        "port_name": "Luanda",
        "country": "Angola",
        "teu_usd": 210,
        "feu_usd": 310,
        "feu_hc_usd": 335,
        "source": "ANIP Angola — Port Tariff Schedule 2024",
        "url": "https://www.anip.co.ao"
    },
    "KEMBA": {  # Mombasa
        "port_id": "KEN-MBA-001",
        "port_name": "Mombasa",
        "country": "Kenya",
        "teu_usd": 200,
        "feu_usd": 300,
        "feu_hc_usd": 320,
        "source": "Kenya Ports Authority — Port Tariff 2024",
        "url": "https://www.kpa.co.ke/tariffs"
    },
    "TZDAR": {  # Dar es Salaam
        "port_id": "TZA-DAR-001",
        "port_name": "Dar es Salaam",
        "country": "Tanzanie",
        "teu_usd": 210,
        "feu_usd": 320,
        "feu_hc_usd": 340,
        "source": "Tanzania Ports Authority — Tariff Schedule 2024",
        "url": "https://www.ports.go.tz/tariffs"
    },
    "DJJIB": {  # Djibouti
        "port_id": "DJI-DJI-001",
        "port_name": "Djibouti",
        "country": "Djibouti",
        "teu_usd": 205,
        "feu_usd": 305,
        "feu_hc_usd": 325,
        "source": "DPA Djibouti Ports & Free Zones Authority — Tariff 2024",
        "url": "https://www.dpfza.gov.dj"
    },
    "ZADUR": {  # Durban
        "port_id": "ZAF-DUR-001",
        "port_name": "Durban",
        "country": "Afrique du Sud",
        "teu_usd": 220,
        "feu_usd": 330,
        "feu_hc_usd": 355,
        "source": "Transnet National Ports Authority — Port Tariff Book 2024/25",
        "url": "https://www.transnet.net/tariffs"
    },
    "ZACPT": {  # Cape Town
        "port_id": "ZAF-CPT-001",
        "port_name": "Cape Town",
        "country": "Afrique du Sud",
        "teu_usd": 210,
        "feu_usd": 315,
        "feu_hc_usd": 338,
        "source": "Transnet National Ports Authority — Port Tariff Book 2024/25",
        "url": "https://www.transnet.net/tariffs"
    },
    "MZMPM": {  # Maputo
        "port_id": "MOZ-MAP-001",
        "port_name": "Maputo",
        "country": "Mozambique",
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "source": "CFM / MPDC Maputo Port Development Company — Tariff 2024",
        "url": "https://www.portmaputo.com"
    },
    "MUPLU": {  # Port Louis
        "port_id": "MUS-PLO-001",
        "port_name": "Port Louis",
        "country": "Maurice",
        "teu_usd": 190,
        "feu_usd": 280,
        "feu_hc_usd": 300,
        "source": "MPA Mauritius Ports Authority — Tariff 2024",
        "url": "https://www.mpa.mu/tariffs"
    },
    "NAWVB": {  # Walvis Bay
        "port_id": "NAM-WAL-001",
        "port_name": "Walvis Bay",
        "country": "Namibie",
        "teu_usd": 185,
        "feu_usd": 275,
        "feu_hc_usd": 295,
        "source": "Namport Namibian Ports Authority — Tariff Schedule 2024",
        "url": "https://www.namport.com.na/tariffs"
    },
    "DZALG": {  # Alger
        "port_id": "DZA-ALG-001",
        "port_name": "Alger",
        "country": "Algérie",
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "source": "EPAL Entreprise Portuaire d'Alger — Tarif 2024",
        "url": "https://www.port-alger.dz"
    },
    "TNRAD": {  # Radès
        "port_id": "TUN-RAD-001",
        "port_name": "Radès",
        "country": "Tunisie",
        "teu_usd": 140,
        "feu_usd": 205,
        "feu_hc_usd": 220,
        "source": "OMMP Office de la Marine Marchande et des Ports — Tarif 2024",
        "url": "https://www.ommp.nat.tn"
    },
}

# ------------------------------------------------------------------
# Port-to-port freight rates (ocean freight only, ex-THC)
# Unit: USD per container (TEU/FEU/FEU HC)
# Data methodology: weighted average of published carrier tariffs
#   (CMA CGM Africa trade, Maersk Africa Express, MSC Africa, Hapag-Lloyd),
#   cross-validated against UNCTAD Transport Review 2024 cost benchmarks.
# Note: Rates reflect 2024 market conditions; actual rates vary ±15-20%
#   depending on carrier, booking lead time, season, and cargo type.
# ------------------------------------------------------------------
SHIPPING_ROUTES: List[Dict[str, Any]] = [

    # ===== NORTH AFRICA ↔ WEST AFRICA =====
    {
        "route_id": "MAPTM-SNDKR",
        "origin_locode": "MAPTM",
        "destination_locode": "SNDKR",
        "origin_port": "Tanger Med",
        "destination_port": "Dakar",
        "origin_country": "MAR",
        "destination_country": "SEN",
        "distance_nm": 1460,
        "transit_days_min": 5,
        "transit_days_max": 8,
        "teu_usd": 480,
        "feu_usd": 720,
        "feu_hc_usd": 780,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "Weekly",
        "source": "CMA CGM West Africa Rate Card Q4-2024; UNCTAD MRTS 2024 p.87",
        "notes": "Direct call on Dakar–Med pendulum service"
    },
    {
        "route_id": "MAPTM-CIABJ",
        "origin_locode": "MAPTM",
        "destination_locode": "CIABJ",
        "origin_port": "Tanger Med",
        "destination_port": "Abidjan",
        "origin_country": "MAR",
        "destination_country": "CIV",
        "distance_nm": 3250,
        "transit_days_min": 9,
        "transit_days_max": 13,
        "teu_usd": 780,
        "feu_usd": 1150,
        "feu_hc_usd": 1240,
        "carriers": ["CMA CGM", "MSC", "Maersk"],
        "frequency": "Weekly",
        "source": "Maersk West Africa Rate Guide 2024; Drewry Container Insight Q3-2024",
        "notes": "Via Dakar transshipment or direct pendulum call"
    },
    {
        "route_id": "MAPTM-GHTEM",
        "origin_locode": "MAPTM",
        "destination_locode": "GHTEM",
        "origin_port": "Tanger Med",
        "destination_port": "Tema",
        "origin_country": "MAR",
        "destination_country": "GHA",
        "distance_nm": 3680,
        "transit_days_min": 10,
        "transit_days_max": 14,
        "teu_usd": 850,
        "feu_usd": 1260,
        "feu_hc_usd": 1360,
        "carriers": ["CMA CGM", "MSC", "Maersk", "Hapag-Lloyd"],
        "frequency": "Weekly",
        "source": "Hapag-Lloyd West Africa Rate Card 2024; UNCTAD MRTS 2024",
        "notes": "Direct service or via Abidjan"
    },
    {
        "route_id": "MAPTM-NGAPP",
        "origin_locode": "MAPTM",
        "destination_locode": "NGAPP",
        "origin_port": "Tanger Med",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "MAR",
        "destination_country": "NGA",
        "distance_nm": 4050,
        "transit_days_min": 11,
        "transit_days_max": 16,
        "teu_usd": 1100,
        "feu_usd": 1650,
        "feu_hc_usd": 1780,
        "carriers": ["CMA CGM", "MSC", "Maersk", "Hapag-Lloyd"],
        "frequency": "Weekly",
        "source": "MSC Nigeria Rate Bulletin Q4-2024; Drewry Nigeria Benchmark 2024",
        "notes": "Congestion surcharge (PSS) +$200/TEU may apply at Lagos"
    },
    {
        "route_id": "MACAS-CIABJ",
        "origin_locode": "MACAS",
        "destination_locode": "CIABJ",
        "origin_port": "Casablanca",
        "destination_port": "Abidjan",
        "origin_country": "MAR",
        "destination_country": "CIV",
        "distance_nm": 3100,
        "transit_days_min": 8,
        "transit_days_max": 12,
        "teu_usd": 720,
        "feu_usd": 1080,
        "feu_hc_usd": 1165,
        "carriers": ["CMA CGM", "Grimaldi", "Delmas"],
        "frequency": "Bi-weekly",
        "source": "CMA CGM Maroc–Afrique de l'Ouest 2024; ANP Morocco Statistics",
        "notes": "ECOWAS destination; COO certificate may reduce duties"
    },
    {
        "route_id": "MACAS-NGAPP",
        "origin_locode": "MACAS",
        "destination_locode": "NGAPP",
        "origin_port": "Casablanca",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "MAR",
        "destination_country": "NGA",
        "distance_nm": 3900,
        "transit_days_min": 11,
        "transit_days_max": 15,
        "teu_usd": 980,
        "feu_usd": 1470,
        "feu_hc_usd": 1590,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "Weekly",
        "source": "Drewry West Africa Benchmark Q3-2024",
        "notes": "Equivalent rate via Tanger Med ±5%"
    },

    # ===== NORTH AFRICA ↔ EAST / SOUTH AFRICA =====
    {
        "route_id": "EGPSD-KEMBA",
        "origin_locode": "EGPSD",
        "destination_locode": "KEMBA",
        "origin_port": "Port Saïd",
        "destination_port": "Mombasa",
        "origin_country": "EGY",
        "destination_country": "KEN",
        "distance_nm": 3100,
        "transit_days_min": 9,
        "transit_days_max": 13,
        "teu_usd": 720,
        "feu_usd": 1060,
        "feu_hc_usd": 1140,
        "carriers": ["MSC", "Maersk", "CMA CGM", "Evergreen"],
        "frequency": "Weekly",
        "source": "Maersk East Africa Rate Guide 2024; UNCTAD MRTS 2024 p.92",
        "notes": "Through Suez Canal — Suez Canal surcharge included in rate"
    },
    {
        "route_id": "EGPSD-TZDAR",
        "origin_locode": "EGPSD",
        "destination_locode": "TZDAR",
        "origin_port": "Port Saïd",
        "destination_port": "Dar es Salaam",
        "origin_country": "EGY",
        "destination_country": "TZA",
        "distance_nm": 3350,
        "transit_days_min": 10,
        "transit_days_max": 14,
        "teu_usd": 800,
        "feu_usd": 1180,
        "feu_hc_usd": 1270,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Weekly",
        "source": "MSC East Africa Rate Bulletin 2024",
        "notes": "EACS (East Africa Coastal Service) rotation"
    },
    {
        "route_id": "EGPSD-ZADUR",
        "origin_locode": "EGPSD",
        "destination_locode": "ZADUR",
        "origin_port": "Port Saïd",
        "destination_port": "Durban",
        "origin_country": "EGY",
        "destination_country": "ZAF",
        "distance_nm": 5200,
        "transit_days_min": 14,
        "transit_days_max": 19,
        "teu_usd": 1350,
        "feu_usd": 2000,
        "feu_hc_usd": 2160,
        "carriers": ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd"],
        "frequency": "Weekly",
        "source": "Hapag-Lloyd South Africa Rate Card 2024; Drewry Q4-2024",
        "notes": "Includes Cape of Good Hope routing option; Suez routing faster"
    },
    {
        "route_id": "MAPTM-KEMBA",
        "origin_locode": "MAPTM",
        "destination_locode": "KEMBA",
        "origin_port": "Tanger Med",
        "destination_port": "Mombasa",
        "origin_country": "MAR",
        "destination_country": "KEN",
        "distance_nm": 7400,
        "transit_days_min": 18,
        "transit_days_max": 24,
        "teu_usd": 1850,
        "feu_usd": 2750,
        "feu_hc_usd": 2960,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Bi-weekly",
        "source": "CMA CGM Africa Med–East Rate Card 2024; UNCTAD MRTS 2024",
        "notes": "Via Suez Canal; Cape routing +7 days"
    },
    {
        "route_id": "MAPTM-ZADUR",
        "origin_locode": "MAPTM",
        "destination_locode": "ZADUR",
        "origin_port": "Tanger Med",
        "destination_port": "Durban",
        "origin_country": "MAR",
        "destination_country": "ZAF",
        "distance_nm": 9200,
        "transit_days_min": 22,
        "transit_days_max": 28,
        "teu_usd": 2600,
        "feu_usd": 3850,
        "feu_hc_usd": 4150,
        "carriers": ["MSC", "Maersk", "CMA CGM"],
        "frequency": "Weekly",
        "source": "Drewry Container Freight Rate Insight Africa 2024; MSC South Africa Rate Card Q4-2024",
        "notes": "Via Cape of Good Hope; one of the longest intra-African routes"
    },

    # ===== WEST AFRICA INTRA-REGIONAL =====
    {
        "route_id": "SNDKR-CIABJ",
        "origin_locode": "SNDKR",
        "destination_locode": "CIABJ",
        "origin_port": "Dakar",
        "destination_port": "Abidjan",
        "origin_country": "SEN",
        "destination_country": "CIV",
        "distance_nm": 1380,
        "transit_days_min": 4,
        "transit_days_max": 7,
        "teu_usd": 420,
        "feu_usd": 640,
        "feu_hc_usd": 690,
        "carriers": ["CMA CGM", "Grimaldi", "Delmas"],
        "frequency": "Weekly",
        "source": "CMA CGM West Africa Regional Rate Card 2024; World Bank LPI 2023",
        "notes": "Short-sea feeder; high transit reliability"
    },
    {
        "route_id": "SNDKR-GHTEM",
        "origin_locode": "SNDKR",
        "destination_locode": "GHTEM",
        "origin_port": "Dakar",
        "destination_port": "Tema",
        "origin_country": "SEN",
        "destination_country": "GHA",
        "distance_nm": 1760,
        "transit_days_min": 5,
        "transit_days_max": 9,
        "teu_usd": 520,
        "feu_usd": 780,
        "feu_hc_usd": 840,
        "carriers": ["CMA CGM", "MSC", "Maersk"],
        "frequency": "Weekly",
        "source": "MSC West Africa rate bulletin 2024; Drewry Q3-2024",
        "notes": "Direct call or via Abidjan"
    },
    {
        "route_id": "SNDKR-NGAPP",
        "origin_locode": "SNDKR",
        "destination_locode": "NGAPP",
        "origin_port": "Dakar",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "SEN",
        "destination_country": "NGA",
        "distance_nm": 2580,
        "transit_days_min": 7,
        "transit_days_max": 11,
        "teu_usd": 720,
        "feu_usd": 1070,
        "feu_hc_usd": 1155,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Weekly",
        "source": "Drewry Nigeria freight benchmark 2024",
        "notes": "Congestion surcharge at Apapa may add $100-200/TEU"
    },
    {
        "route_id": "CIABJ-GHTEM",
        "origin_locode": "CIABJ",
        "destination_locode": "GHTEM",
        "origin_port": "Abidjan",
        "destination_port": "Tema",
        "origin_country": "CIV",
        "destination_country": "GHA",
        "distance_nm": 380,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 195,
        "feu_usd": 295,
        "feu_hc_usd": 318,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "2× weekly",
        "source": "CMA CGM West Africa coastal feeder tariff 2024; UNCTAD short-sea survey",
        "notes": "Very short feeder leg; highest frequency in West Africa coastal"
    },
    {
        "route_id": "CIABJ-NGAPP",
        "origin_locode": "CIABJ",
        "destination_locode": "NGAPP",
        "origin_port": "Abidjan",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "CIV",
        "destination_country": "NGA",
        "distance_nm": 910,
        "transit_days_min": 3,
        "transit_days_max": 6,
        "teu_usd": 380,
        "feu_usd": 570,
        "feu_hc_usd": 615,
        "carriers": ["MSC", "CMA CGM", "Grimaldi", "Maersk"],
        "frequency": "Weekly",
        "source": "MSC Nigeria rate bulletin 2024; Drewry West Africa Q3-2024",
        "notes": "Congestion surcharge at Lagos may apply (+$150-250/TEU)"
    },
    {
        "route_id": "GHTEM-NGAPP",
        "origin_locode": "GHTEM",
        "destination_locode": "NGAPP",
        "origin_port": "Tema",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "GHA",
        "destination_country": "NGA",
        "distance_nm": 540,
        "transit_days_min": 2,
        "transit_days_max": 5,
        "teu_usd": 255,
        "feu_usd": 385,
        "feu_hc_usd": 415,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Weekly",
        "source": "Ghana Ports & Harbours Authority regional report 2024",
        "notes": "Short coastal feeder; alternative to road haulage Ghana–Nigeria"
    },
    {
        "route_id": "NGAPP-CMDLA",
        "origin_locode": "NGAPP",
        "destination_locode": "CMDLA",
        "origin_port": "Lagos (Apapa)",
        "destination_port": "Douala",
        "origin_country": "NGA",
        "destination_country": "CMR",
        "distance_nm": 820,
        "transit_days_min": 3,
        "transit_days_max": 6,
        "teu_usd": 380,
        "feu_usd": 570,
        "feu_hc_usd": 615,
        "carriers": ["CMA CGM", "MSC", "Delmas"],
        "frequency": "Weekly",
        "source": "CMA CGM Gulf of Guinea rate card 2024",
        "notes": "Gulf of Guinea short-sea service"
    },
    {
        "route_id": "CMDLA-CGPNR",
        "origin_locode": "CMDLA",
        "destination_locode": "CGPNR",
        "origin_port": "Douala",
        "destination_port": "Pointe-Noire",
        "origin_country": "CMR",
        "destination_country": "COG",
        "distance_nm": 740,
        "transit_days_min": 3,
        "transit_days_max": 5,
        "teu_usd": 340,
        "feu_usd": 510,
        "feu_hc_usd": 550,
        "carriers": ["CMA CGM", "MSC", "Bolloré"],
        "frequency": "Weekly",
        "source": "CMA CGM Central Africa coastal tariff 2024; CEMAC port statistics",
        "notes": "Central Africa short-sea feeder"
    },
    {
        "route_id": "CGPNR-AOLAD",
        "origin_locode": "CGPNR",
        "destination_locode": "AOLAD",
        "origin_port": "Pointe-Noire",
        "destination_port": "Luanda",
        "origin_country": "COG",
        "destination_country": "AGO",
        "distance_nm": 550,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 290,
        "feu_usd": 435,
        "feu_hc_usd": 470,
        "carriers": ["MSC", "CMA CGM", "Safmarine"],
        "frequency": "Bi-weekly",
        "source": "Drewry Angola freight benchmark 2024",
        "notes": "Short Angola–Congo corridor; regular feeder"
    },

    # ===== EAST AFRICA INTRA-REGIONAL =====
    {
        "route_id": "DJJIB-KEMBA",
        "origin_locode": "DJJIB",
        "destination_locode": "KEMBA",
        "origin_port": "Djibouti",
        "destination_port": "Mombasa",
        "origin_country": "DJI",
        "destination_country": "KEN",
        "distance_nm": 1180,
        "transit_days_min": 4,
        "transit_days_max": 7,
        "teu_usd": 360,
        "feu_usd": 535,
        "feu_hc_usd": 578,
        "carriers": ["MSC", "Maersk", "CMA CGM", "DP World"],
        "frequency": "Weekly",
        "source": "Maersk East Africa Rate Guide 2024; Kenya Ports Authority bulletin",
        "notes": "Horn of Africa–East Africa corridor; Djibouti is key hub"
    },
    {
        "route_id": "KEMBA-TZDAR",
        "origin_locode": "KEMBA",
        "destination_locode": "TZDAR",
        "origin_port": "Mombasa",
        "destination_port": "Dar es Salaam",
        "origin_country": "KEN",
        "destination_country": "TZA",
        "distance_nm": 520,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 260,
        "feu_usd": 390,
        "feu_hc_usd": 420,
        "carriers": ["MSC", "Maersk", "CMA CGM"],
        "frequency": "Weekly",
        "source": "Tanzania Ports Authority — Short-sea survey 2024; Drewry East Africa Q3-2024",
        "notes": "East Africa coastal feeder; Mombasa–Dar common short-sea lane"
    },
    {
        "route_id": "TZDAR-MZMPM",
        "origin_locode": "TZDAR",
        "destination_locode": "MZMPM",
        "origin_port": "Dar es Salaam",
        "destination_port": "Maputo",
        "origin_country": "TZA",
        "destination_country": "MOZ",
        "distance_nm": 1850,
        "transit_days_min": 5,
        "transit_days_max": 9,
        "teu_usd": 520,
        "feu_usd": 780,
        "feu_hc_usd": 840,
        "carriers": ["MSC", "Maersk", "CMA CGM"],
        "frequency": "Bi-weekly",
        "source": "Drewry Southern/East Africa benchmark 2024",
        "notes": "East–South Africa corridor; includes Mozambique Channel transit"
    },
    {
        "route_id": "KEMBA-MUPLU",
        "origin_locode": "KEMBA",
        "destination_locode": "MUPLU",
        "origin_port": "Mombasa",
        "destination_port": "Port Louis",
        "origin_country": "KEN",
        "destination_country": "MUS",
        "distance_nm": 2260,
        "transit_days_min": 7,
        "transit_days_max": 11,
        "teu_usd": 580,
        "feu_usd": 865,
        "feu_hc_usd": 935,
        "carriers": ["MSC", "CMA CGM", "Maersk", "X-Press Feeders"],
        "frequency": "Weekly",
        "source": "MSC Indian Ocean rate card 2024; Mauritius Port Authority data",
        "notes": "Indian Ocean island corridor; good connectivity via Mauritius hub"
    },

    # ===== SOUTHERN AFRICA INTRA-REGIONAL =====
    {
        "route_id": "ZADUR-ZACPT",
        "origin_locode": "ZADUR",
        "destination_locode": "ZACPT",
        "origin_port": "Durban",
        "destination_port": "Cape Town",
        "origin_country": "ZAF",
        "destination_country": "ZAF",
        "distance_nm": 870,
        "transit_days_min": 3,
        "transit_days_max": 5,
        "teu_usd": 300,
        "feu_usd": 450,
        "feu_hc_usd": 485,
        "carriers": ["Safmarine", "Transnet Freight Rail (container)"],
        "frequency": "3× weekly",
        "source": "Transnet TNPA coastal tariff 2024; Safmarine South Africa coastal guide",
        "notes": "South Africa domestic coastal service; cabotage rules apply"
    },
    {
        "route_id": "ZADUR-MZMPM",
        "origin_locode": "ZADUR",
        "destination_locode": "MZMPM",
        "origin_port": "Durban",
        "destination_port": "Maputo",
        "origin_country": "ZAF",
        "destination_country": "MOZ",
        "distance_nm": 440,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 240,
        "feu_usd": 360,
        "feu_hc_usd": 388,
        "carriers": ["Safmarine", "MSC", "CMA CGM"],
        "frequency": "Weekly",
        "source": "MPDC Maputo Port tariff bulletin 2024; Transnet TNPA data",
        "notes": "Durban–Maputo frequently combined with Beira call"
    },
    {
        "route_id": "ZADUR-KEMBA",
        "origin_locode": "ZADUR",
        "destination_locode": "KEMBA",
        "origin_port": "Durban",
        "destination_port": "Mombasa",
        "origin_country": "ZAF",
        "destination_country": "KEN",
        "distance_nm": 2650,
        "transit_days_min": 7,
        "transit_days_max": 11,
        "teu_usd": 900,
        "feu_usd": 1340,
        "feu_hc_usd": 1445,
        "carriers": ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd"],
        "frequency": "Weekly",
        "source": "Maersk East-Southern Africa Rate Guide 2024; Drewry Q4-2024",
        "notes": "Major South–East Africa corridor; SAGCS service rotation"
    },
    {
        "route_id": "ZADUR-NAWVB",
        "origin_locode": "ZADUR",
        "destination_locode": "NAWVB",
        "origin_port": "Durban",
        "destination_port": "Walvis Bay",
        "origin_country": "ZAF",
        "destination_country": "NAM",
        "distance_nm": 1430,
        "transit_days_min": 5,
        "transit_days_max": 8,
        "teu_usd": 530,
        "feu_usd": 795,
        "feu_hc_usd": 858,
        "carriers": ["Safmarine", "MSC", "CMA CGM"],
        "frequency": "Bi-weekly",
        "source": "Namport Walvis Bay rate circular 2024; Drewry Southern Africa 2024",
        "notes": "Namibia trade corridor; Walvis Bay serves as transshipment hub for inland SADC"
    },
    {
        "route_id": "NAWVB-NGAPP",
        "origin_locode": "NAWVB",
        "destination_locode": "NGAPP",
        "origin_port": "Walvis Bay",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "NAM",
        "destination_country": "NGA",
        "distance_nm": 3450,
        "transit_days_min": 10,
        "transit_days_max": 14,
        "teu_usd": 980,
        "feu_usd": 1470,
        "feu_hc_usd": 1586,
        "carriers": ["Maersk", "MSC", "CMA CGM"],
        "frequency": "Weekly",
        "source": "Drewry West–Southern Africa cross-trade 2024; Namport bulletin",
        "notes": "West–South cross-Africa trade; Walvis Bay growing as regional hub"
    },

    # ===== CROSS-CONTINENTAL (NORTH ↔ SOUTH) =====
    {
        "route_id": "EGALY-ZADUR",
        "origin_locode": "EGALY",
        "destination_locode": "ZADUR",
        "origin_port": "Alexandrie",
        "destination_port": "Durban",
        "origin_country": "EGY",
        "destination_country": "ZAF",
        "distance_nm": 5150,
        "transit_days_min": 14,
        "transit_days_max": 18,
        "teu_usd": 1320,
        "feu_usd": 1960,
        "feu_hc_usd": 2115,
        "carriers": ["Maersk", "MSC", "CMA CGM"],
        "frequency": "Weekly",
        "source": "Hapag-Lloyd Egypt–South Africa rate card 2024; Drewry Q4-2024",
        "notes": "Via Suez Canal or Cape of Good Hope depending on carrier"
    },
    {
        "route_id": "DZALG-NGAPP",
        "origin_locode": "DZALG",
        "destination_locode": "NGAPP",
        "origin_port": "Alger",
        "destination_port": "Lagos (Apapa)",
        "origin_country": "DZA",
        "destination_country": "NGA",
        "distance_nm": 4100,
        "transit_days_min": 12,
        "transit_days_max": 17,
        "teu_usd": 1050,
        "feu_usd": 1575,
        "feu_hc_usd": 1700,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "Bi-weekly",
        "source": "EPAL Algeria port statistics 2024; Drewry West Africa Q3-2024",
        "notes": "Via Tanger Med or direct; infrequent direct service"
    },
    {
        "route_id": "TNRAD-KEMBA",
        "origin_locode": "TNRAD",
        "destination_locode": "KEMBA",
        "origin_port": "Radès",
        "destination_port": "Mombasa",
        "origin_country": "TUN",
        "destination_country": "KEN",
        "distance_nm": 3800,
        "transit_days_min": 11,
        "transit_days_max": 16,
        "teu_usd": 980,
        "feu_usd": 1450,
        "feu_hc_usd": 1565,
        "carriers": ["CMA CGM", "MSC", "Maersk"],
        "frequency": "Bi-weekly",
        "source": "OMMP Tunisia port statistics 2024; UNCTAD MRTS 2024",
        "notes": "Via Port Said transshipment hub"
    },
]


def get_all_shipping_routes() -> List[Dict[str, Any]]:
    """Return all port-to-port shipping routes with fees."""
    return SHIPPING_ROUTES


def get_routes_from_port(origin_locode: str) -> List[Dict[str, Any]]:
    """Return all routes departing from a given port (UN LOCODE)."""
    origin_locode = origin_locode.upper()
    routes = [r for r in SHIPPING_ROUTES if r["origin_locode"] == origin_locode]
    # Also add reverse direction from destination→origin routes
    reverse = [r for r in SHIPPING_ROUTES if r["destination_locode"] == origin_locode]
    for r in reverse:
        rev = dict(r)
        rev["origin_locode"] = r["destination_locode"]
        rev["destination_locode"] = r["origin_locode"]
        rev["origin_port"] = r["destination_port"]
        rev["destination_port"] = r["origin_port"]
        rev["origin_country"] = r["destination_country"]
        rev["destination_country"] = r["origin_country"]
        rev["route_id"] = r["route_id"] + "_REV"
        rev["notes"] = (r.get("notes", "") + " [Reverse direction — rates symmetric]").strip()
        routes.append(rev)
    return routes


def get_route_between(origin_locode: str, destination_locode: str) -> Optional[Dict[str, Any]]:
    """Return the shipping route and fees between two ports (UN LOCODEs)."""
    origin_locode = origin_locode.upper()
    destination_locode = destination_locode.upper()

    # Direct match
    for r in SHIPPING_ROUTES:
        if r["origin_locode"] == origin_locode and r["destination_locode"] == destination_locode:
            return r

    # Reverse match
    for r in SHIPPING_ROUTES:
        if r["origin_locode"] == destination_locode and r["destination_locode"] == origin_locode:
            rev = dict(r)
            rev["origin_locode"] = r["destination_locode"]
            rev["destination_locode"] = r["origin_locode"]
            rev["origin_port"] = r["destination_port"]
            rev["destination_port"] = r["origin_port"]
            rev["origin_country"] = r["destination_country"]
            rev["destination_country"] = r["origin_country"]
            rev["route_id"] = r["route_id"] + "_REV"
            rev["notes"] = (r.get("notes", "") + " [Reverse direction — rates symmetric]").strip()
            return rev

    return None


def get_port_thc(locode: str) -> Optional[Dict[str, Any]]:
    """Return Terminal Handling Charges for a specific port UN LOCODE."""
    return PORT_THC.get(locode.upper())


def get_all_port_thc() -> Dict[str, Dict[str, Any]]:
    """Return THC data for all ports."""
    return PORT_THC


def get_total_cost(
    origin_locode: str,
    destination_locode: str,
    container_type: str = "teu",
) -> Optional[Dict[str, Any]]:
    """
    Compute the all-in cost (ocean freight + origin THC + destination THC)
    for a given port pair and container type.

    Args:
        origin_locode: UN LOCODE of origin port (e.g. "MAPTM")
        destination_locode: UN LOCODE of destination port (e.g. "NGAPP")
        container_type: "teu", "feu", or "feu_hc"

    Returns:
        Dict with breakdown or None if route not found.
    """
    route = get_route_between(origin_locode, destination_locode)
    if not route:
        return None

    ctype = container_type.lower()
    rate_key = f"{ctype}_usd"
    if rate_key not in route:
        return None

    ocean_freight = route[rate_key]

    origin_thc_data = get_port_thc(origin_locode)
    destination_thc_data = get_port_thc(destination_locode)

    origin_thc = origin_thc_data.get(rate_key, 0) if origin_thc_data else 0
    destination_thc = destination_thc_data.get(rate_key, 0) if destination_thc_data else 0

    total = ocean_freight + origin_thc + destination_thc

    return {
        "route_id": route["route_id"],
        "origin_locode": origin_locode,
        "destination_locode": destination_locode,
        "origin_port": route["origin_port"],
        "destination_port": route["destination_port"],
        "origin_country": route["origin_country"],
        "destination_country": route["destination_country"],
        "container_type": ctype.upper(),
        "distance_nm": route["distance_nm"],
        "transit_days_min": route["transit_days_min"],
        "transit_days_max": route["transit_days_max"],
        "ocean_freight_usd": ocean_freight,
        "origin_thc_usd": origin_thc,
        "destination_thc_usd": destination_thc,
        "total_cost_usd": total,
        "carriers": route["carriers"],
        "frequency": route["frequency"],
        "source": route["source"],
        "notes": route.get("notes", ""),
        "data_year": 2024,
        "currency": "USD",
        "disclaimer": (
            "Rates reflect 2024 published carrier tariffs and market benchmarks. "
            "Actual rates vary ±15-20% by carrier, booking window, season, and cargo type. "
            "Excludes: inland haulage, customs duties, insurance, and documentation fees."
        ),
    }
