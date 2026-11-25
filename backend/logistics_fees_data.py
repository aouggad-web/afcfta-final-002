"""
Port-to-port maritime shipping fees for African trade routes.

Couverture : tous les principaux ports à conteneurs africains (59 ports, 5 façades
maritimes, dont 7 ports algériens) avec une matrice de routes complète (~1 700 paires).

Sources :
- Devis professionnels 2026 : Marseille→Alger 1 200 USD/20' (fret + surcharges)
- Grille Maersk départ Douala : fret de base 1 295 USD/20' vers Algésiras
- Grilles FAK MSC Asie→Afrique du Nord 2026 (prime Algérie ≈ +18 % / Maghreb)
- Drewry Maritime Research — Container Freight Rate Insight / World Container Index 2024
- UNCTAD Review of Maritime Transport (MRTS) 2024
- Tarifs publiés CMA CGM / Maersk / MSC / Hapag-Lloyd (rate cards Afrique 2024)
- Barèmes THC des autorités portuaires (Tanger Med, Mombasa KPA, Durban Transnet, etc.)

Méthodologie des tarifs (niveau de marché 2026, fret + surcharges, hors THC) :
- Modèle distance-coût recalibré : 900 USD/EVP de coût fixe + 0,265 USD/mille,
  calé sur les deux devis ci-dessus. La distance maritime est calculée par
  segments great-circle via les points de passage obligés (Gibraltar, Suez,
  Bab-el-Mandeb, Cap de Bonne-Espérance).
- Transbordement : sans service direct (ex. Afrique centrale → Algérie), la route
  passe par le hub qui minimise la distance (Tanger Med, Port-Saïd, Lomé, Durban,
  Port-Louis, Djibouti) : +150 USD/EVP de manutention au hub, +3 à 7 jours.
- Prime de marché à l'import par pays de destination (Algérie ×1,18).
- Les routes "benchmark" (tarifs 2024 publiés) sont actualisées au niveau 2026
  en conservant leur écart propre à la ligne (``rate_basis = benchmark_actualise``).
- Reefer (20' RF, 40' RH) et marchandises dangereuses (IMDG) : coefficients de
  pratique de marché, signalés comme hypothèses dans le résultat.
- Les tarifs réels varient ±15 % selon l'armateur, la saison et le délai de réservation.
"""

from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional

# ------------------------------------------------------------------
# Registre des ports africains à conteneurs
# coast ∈ {MED, ATL, RED, IND}  (façade maritime, pour le routage)
# THC = Terminal Handling Charges (USD / conteneur), barèmes portuaires 2024
# ------------------------------------------------------------------
PORTS: Dict[str, Dict[str, Any]] = {
    # ===================== AFRIQUE DU NORD — MÉDITERRANÉE =====================
    "MAPTM": {
        "name": "Tanger Med",
        "country": "Maroc",
        "iso": "MAR",
        "flag": "🇲🇦",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 35.88,
        "lon": -5.50,
        "teu_usd": 170,
        "feu_usd": 250,
        "feu_hc_usd": 270,
        "thc_source": "TMPA Tanger Med Port Authority Tariff 2024",
    },
    "MACAS": {
        "name": "Casablanca",
        "country": "Maroc",
        "iso": "MAR",
        "flag": "🇲🇦",
        "region": "Afrique du Nord",
        "coast": "ATL",
        "lat": 33.60,
        "lon": -7.62,
        "teu_usd": 150,
        "feu_usd": 220,
        "feu_hc_usd": 235,
        "thc_source": "ANP Agence Nationale des Ports — Tarif 2024",
    },
    "MAAGA": {
        "name": "Agadir",
        "country": "Maroc",
        "iso": "MAR",
        "flag": "🇲🇦",
        "region": "Afrique du Nord",
        "coast": "ATL",
        "lat": 30.42,
        "lon": -9.62,
        "teu_usd": 150,
        "feu_usd": 220,
        "feu_hc_usd": 235,
        "thc_source": "ANP Agence Nationale des Ports — Tarif 2024",
    },
    "DZALG": {
        "name": "Alger",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 36.77,
        "lon": 3.06,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "EPAL Entreprise Portuaire d'Alger — Tarif 2024",
    },
    "DZORN": {
        "name": "Oran",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 35.71,
        "lon": -0.62,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "EPO Entreprise Portuaire d'Oran — Tarif 2024",
    },
    "DZBJA": {
        "name": "Bejaia",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 36.75,
        "lon": 5.08,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "EPB Entreprise Portuaire de Bejaia — Tarif 2024",
    },
    # Ports algériens ajoutés en 2026 : THC non publiés ici, alignés sur le
    # barème des ports d'Alger / Oran / Bejaia (estimation à confirmer).
    "DZDJE": {
        "name": "Djen Djen (Jijel)",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 36.82,
        "lon": 5.89,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "Estimation — alignée sur le barème EPAL/EPO/EPB 2024 (EP Djen Djen)",
    },
    "DZMOS": {
        "name": "Mostaganem",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 35.94,
        "lon": 0.07,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "Estimation — alignée sur le barème EPAL/EPO/EPB 2024 (EP Mostaganem)",
    },
    "DZAAE": {
        "name": "Annaba",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 36.90,
        "lon": 7.77,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "Estimation — alignée sur le barème EPAL/EPO/EPB 2024 (EP Annaba)",
    },
    "DZSKI": {
        "name": "Skikda",
        "country": "Algérie",
        "iso": "DZA",
        "flag": "🇩🇿",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 36.88,
        "lon": 6.90,
        "teu_usd": 145,
        "feu_usd": 210,
        "feu_hc_usd": 226,
        "thc_source": "Estimation — alignée sur le barème EPAL/EPO/EPB 2024 (EP Skikda)",
    },
    "TNRAD": {
        "name": "Radès",
        "country": "Tunisie",
        "iso": "TUN",
        "flag": "🇹🇳",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 36.79,
        "lon": 10.30,
        "teu_usd": 140,
        "feu_usd": 205,
        "feu_hc_usd": 220,
        "thc_source": "OMMP Office de la Marine Marchande et des Ports — Tarif 2024",
    },
    "TNSFA": {
        "name": "Sfax",
        "country": "Tunisie",
        "iso": "TUN",
        "flag": "🇹🇳",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 34.72,
        "lon": 10.77,
        "teu_usd": 140,
        "feu_usd": 205,
        "feu_hc_usd": 220,
        "thc_source": "OMMP — Tarif 2024",
    },
    "LYTIP": {
        "name": "Tripoli",
        "country": "Libye",
        "iso": "LBY",
        "flag": "🇱🇾",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 32.90,
        "lon": 13.18,
        "teu_usd": 160,
        "feu_usd": 235,
        "feu_hc_usd": 252,
        "thc_source": "Libyan Ports Company — Tariff 2024",
    },
    "LYMRA": {
        "name": "Misratah",
        "country": "Libye",
        "iso": "LBY",
        "flag": "🇱🇾",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 32.37,
        "lon": 15.22,
        "teu_usd": 160,
        "feu_usd": 235,
        "feu_hc_usd": 252,
        "thc_source": "Libyan Ports Company — Tariff 2024",
    },
    "EGALY": {
        "name": "Alexandrie",
        "country": "Égypte",
        "iso": "EGY",
        "flag": "🇪🇬",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 31.18,
        "lon": 29.87,
        "teu_usd": 155,
        "feu_usd": 225,
        "feu_hc_usd": 242,
        "thc_source": "Alexandria Port Authority Tariff Book 2024",
    },
    "EGPSD": {
        "name": "Port Saïd",
        "country": "Égypte",
        "iso": "EGY",
        "flag": "🇪🇬",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 31.25,
        "lon": 32.30,
        "teu_usd": 160,
        "feu_usd": 230,
        "feu_hc_usd": 248,
        "thc_source": "Suez Canal Container Terminal (SCCT) Tariff 2024",
    },
    "EGDAM": {
        "name": "Damiette",
        "country": "Égypte",
        "iso": "EGY",
        "flag": "🇪🇬",
        "region": "Afrique du Nord",
        "coast": "MED",
        "lat": 31.42,
        "lon": 31.81,
        "teu_usd": 155,
        "feu_usd": 225,
        "feu_hc_usd": 242,
        "thc_source": "Damietta Port Authority Tariff 2024",
    },
    # ===================== MER ROUGE / CORNE DE L'AFRIQUE =====================
    "EGSOK": {
        "name": "Ain Sokhna",
        "country": "Égypte",
        "iso": "EGY",
        "flag": "🇪🇬",
        "region": "Mer Rouge",
        "coast": "RED",
        "lat": 29.66,
        "lon": 32.35,
        "teu_usd": 160,
        "feu_usd": 230,
        "feu_hc_usd": 248,
        "thc_source": "Sokhna Port (DP World) Tariff 2024",
    },
    "SDPZU": {
        "name": "Port Soudan",
        "country": "Soudan",
        "iso": "SDN",
        "flag": "🇸🇩",
        "region": "Mer Rouge",
        "coast": "RED",
        "lat": 19.62,
        "lon": 37.22,
        "teu_usd": 180,
        "feu_usd": 265,
        "feu_hc_usd": 285,
        "thc_source": "Sea Ports Corporation Sudan — Tariff 2024",
    },
    "DJJIB": {
        "name": "Djibouti",
        "country": "Djibouti",
        "iso": "DJI",
        "flag": "🇩🇯",
        "region": "Mer Rouge",
        "coast": "RED",
        "lat": 11.60,
        "lon": 43.14,
        "teu_usd": 205,
        "feu_usd": 305,
        "feu_hc_usd": 325,
        "thc_source": "DPFZA Djibouti Ports & Free Zones — Tariff 2024",
    },
    "SOBBO": {
        "name": "Berbera",
        "country": "Somalie",
        "iso": "SOM",
        "flag": "🇸🇴",
        "region": "Mer Rouge",
        "coast": "RED",
        "lat": 10.44,
        "lon": 45.02,
        "teu_usd": 200,
        "feu_usd": 300,
        "feu_hc_usd": 320,
        "thc_source": "Berbera Port (DP World) Tariff 2024",
    },
    # ===================== AFRIQUE DE L'OUEST — ATLANTIQUE =====================
    "MRNKC": {
        "name": "Nouakchott",
        "country": "Mauritanie",
        "iso": "MRT",
        "flag": "🇲🇷",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 18.02,
        "lon": -16.03,
        "teu_usd": 175,
        "feu_usd": 260,
        "feu_hc_usd": 280,
        "thc_source": "PANPA Port de Nouakchott — Tarif 2024",
    },
    "SNDKR": {
        "name": "Dakar",
        "country": "Sénégal",
        "iso": "SEN",
        "flag": "🇸🇳",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 14.68,
        "lon": -17.42,
        "teu_usd": 180,
        "feu_usd": 270,
        "feu_hc_usd": 290,
        "thc_source": "PAD Port Autonome de Dakar — Tarification 2024",
    },
    "GMBJL": {
        "name": "Banjul",
        "country": "Gambie",
        "iso": "GMB",
        "flag": "🇬🇲",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 13.45,
        "lon": -16.58,
        "teu_usd": 175,
        "feu_usd": 260,
        "feu_hc_usd": 280,
        "thc_source": "Gambia Ports Authority — Tariff 2024",
    },
    "GWOXB": {
        "name": "Bissau",
        "country": "Guinée-Bissau",
        "iso": "GNB",
        "flag": "🇬🇼",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 11.86,
        "lon": -15.57,
        "teu_usd": 175,
        "feu_usd": 260,
        "feu_hc_usd": 280,
        "thc_source": "APGB Bissau — Tarif 2024",
    },
    "GNCKY": {
        "name": "Conakry",
        "country": "Guinée",
        "iso": "GIN",
        "flag": "🇬🇳",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 9.51,
        "lon": -13.71,
        "teu_usd": 180,
        "feu_usd": 270,
        "feu_hc_usd": 290,
        "thc_source": "Port Autonome de Conakry — Tarif 2024",
    },
    "SLFNA": {
        "name": "Freetown",
        "country": "Sierra Leone",
        "iso": "SLE",
        "flag": "🇸🇱",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 8.50,
        "lon": -13.23,
        "teu_usd": 180,
        "feu_usd": 270,
        "feu_hc_usd": 290,
        "thc_source": "Sierra Leone Ports Authority — Tariff 2024",
    },
    "LRMLW": {
        "name": "Monrovia",
        "country": "Liberia",
        "iso": "LBR",
        "flag": "🇱🇷",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 6.35,
        "lon": -10.80,
        "teu_usd": 180,
        "feu_usd": 270,
        "feu_hc_usd": 290,
        "thc_source": "National Port Authority Liberia — Tariff 2024",
    },
    "CIABJ": {
        "name": "Abidjan",
        "country": "Côte d'Ivoire",
        "iso": "CIV",
        "flag": "🇨🇮",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 5.25,
        "lon": -4.01,
        "teu_usd": 185,
        "feu_usd": 275,
        "feu_hc_usd": 295,
        "thc_source": "PAA Port Autonome d'Abidjan — Tarif 2024",
    },
    "CISPY": {
        "name": "San Pédro",
        "country": "Côte d'Ivoire",
        "iso": "CIV",
        "flag": "🇨🇮",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 4.74,
        "lon": -6.63,
        "teu_usd": 185,
        "feu_usd": 275,
        "feu_hc_usd": 295,
        "thc_source": "PASP Port de San Pédro — Tarif 2024",
    },
    "GHTEM": {
        "name": "Tema",
        "country": "Ghana",
        "iso": "GHA",
        "flag": "🇬🇭",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 5.62,
        "lon": 0.01,
        "teu_usd": 178,
        "feu_usd": 265,
        "feu_hc_usd": 284,
        "thc_source": "Ghana Ports & Harbours Authority Tariff 2024",
    },
    "GHTKD": {
        "name": "Takoradi",
        "country": "Ghana",
        "iso": "GHA",
        "flag": "🇬🇭",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 4.88,
        "lon": -1.75,
        "teu_usd": 178,
        "feu_usd": 265,
        "feu_hc_usd": 284,
        "thc_source": "Ghana Ports & Harbours Authority Tariff 2024",
    },
    "TGLFW": {
        "name": "Lomé",
        "country": "Togo",
        "iso": "TGO",
        "flag": "🇹🇬",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 6.13,
        "lon": 1.29,
        "teu_usd": 180,
        "feu_usd": 270,
        "feu_hc_usd": 290,
        "thc_source": "Port Autonome de Lomé — Tarif 2024",
    },
    "BJCOO": {
        "name": "Cotonou",
        "country": "Bénin",
        "iso": "BEN",
        "flag": "🇧🇯",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 6.35,
        "lon": 2.43,
        "teu_usd": 182,
        "feu_usd": 272,
        "feu_hc_usd": 292,
        "thc_source": "PAC Port Autonome de Cotonou — Tarif 2024",
    },
    "NGAPP": {
        "name": "Lagos (Apapa)",
        "country": "Nigeria",
        "iso": "NGA",
        "flag": "🇳🇬",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 6.45,
        "lon": 3.37,
        "teu_usd": 230,
        "feu_usd": 340,
        "feu_hc_usd": 365,
        "thc_source": "Nigerian Ports Authority Tariff Circular 2024",
    },
    "NGONN": {
        "name": "Onne",
        "country": "Nigeria",
        "iso": "NGA",
        "flag": "🇳🇬",
        "region": "Afrique de l'Ouest",
        "coast": "ATL",
        "lat": 4.72,
        "lon": 7.15,
        "teu_usd": 230,
        "feu_usd": 340,
        "feu_hc_usd": 365,
        "thc_source": "Nigerian Ports Authority Tariff Circular 2024",
    },
    # ===================== AFRIQUE CENTRALE — ATLANTIQUE =====================
    "CMDLA": {
        "name": "Douala",
        "country": "Cameroun",
        "iso": "CMR",
        "flag": "🇨🇲",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": 4.05,
        "lon": 9.68,
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "thc_source": "PAD Port Autonome de Douala — Tarif 2024",
    },
    "CMKBI": {
        "name": "Kribi",
        "country": "Cameroun",
        "iso": "CMR",
        "flag": "🇨🇲",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": 2.94,
        "lon": 9.91,
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "thc_source": "PAK Port Autonome de Kribi — Tarif 2024",
    },
    "GQSSG": {
        "name": "Malabo",
        "country": "Guinée équatoriale",
        "iso": "GNQ",
        "flag": "🇬🇶",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": 3.75,
        "lon": 8.78,
        "teu_usd": 200,
        "feu_usd": 295,
        "feu_hc_usd": 315,
        "thc_source": "GEPetrol / APGE — Tariff 2024",
    },
    "GALBV": {
        "name": "Libreville (Owendo)",
        "country": "Gabon",
        "iso": "GAB",
        "flag": "🇬🇦",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": 0.30,
        "lon": 9.50,
        "teu_usd": 200,
        "feu_usd": 295,
        "feu_hc_usd": 315,
        "thc_source": "OPRAG / Owendo Container Terminal — Tarif 2024",
    },
    "CGPNR": {
        "name": "Pointe-Noire",
        "country": "Congo",
        "iso": "COG",
        "flag": "🇨🇬",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": -4.79,
        "lon": 11.84,
        "teu_usd": 200,
        "feu_usd": 295,
        "feu_hc_usd": 315,
        "thc_source": "PAPN Port Autonome de Pointe-Noire — Tarif 2024",
    },
    "CDMAT": {
        "name": "Matadi",
        "country": "RD Congo",
        "iso": "COD",
        "flag": "🇨🇩",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": -5.82,
        "lon": 13.46,
        "teu_usd": 205,
        "feu_usd": 305,
        "feu_hc_usd": 325,
        "thc_source": "SCTP Matadi — Tarif 2024",
    },
    "AOLAD": {
        "name": "Luanda",
        "country": "Angola",
        "iso": "AGO",
        "flag": "🇦🇴",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": -8.78,
        "lon": 13.24,
        "teu_usd": 210,
        "feu_usd": 310,
        "feu_hc_usd": 335,
        "thc_source": "Porto de Luanda — Tariff 2024",
    },
    "AOLOB": {
        "name": "Lobito",
        "country": "Angola",
        "iso": "AGO",
        "flag": "🇦🇴",
        "region": "Afrique Centrale",
        "coast": "ATL",
        "lat": -12.35,
        "lon": 13.55,
        "teu_usd": 210,
        "feu_usd": 310,
        "feu_hc_usd": 335,
        "thc_source": "Porto do Lobito — Tariff 2024",
    },
    # ===================== AFRIQUE DE L'EST / OCÉAN INDIEN =====================
    "KEMBA": {
        "name": "Mombasa",
        "country": "Kenya",
        "iso": "KEN",
        "flag": "🇰🇪",
        "region": "Afrique de l'Est",
        "coast": "IND",
        "lat": -4.04,
        "lon": 39.67,
        "teu_usd": 200,
        "feu_usd": 300,
        "feu_hc_usd": 320,
        "thc_source": "Kenya Ports Authority — Port Tariff 2024",
    },
    "TZDAR": {
        "name": "Dar es Salaam",
        "country": "Tanzanie",
        "iso": "TZA",
        "flag": "🇹🇿",
        "region": "Afrique de l'Est",
        "coast": "IND",
        "lat": -6.83,
        "lon": 39.30,
        "teu_usd": 210,
        "feu_usd": 320,
        "feu_hc_usd": 340,
        "thc_source": "Tanzania Ports Authority — Tariff 2024",
    },
    "TZTGT": {
        "name": "Tanga",
        "country": "Tanzanie",
        "iso": "TZA",
        "flag": "🇹🇿",
        "region": "Afrique de l'Est",
        "coast": "IND",
        "lat": -5.07,
        "lon": 39.10,
        "teu_usd": 205,
        "feu_usd": 310,
        "feu_hc_usd": 330,
        "thc_source": "Tanzania Ports Authority — Tariff 2024",
    },
    "MZNAC": {
        "name": "Nacala",
        "country": "Mozambique",
        "iso": "MOZ",
        "flag": "🇲🇿",
        "region": "Afrique de l'Est",
        "coast": "IND",
        "lat": -14.54,
        "lon": 40.67,
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "thc_source": "CDN Nacala — Tariff 2024",
    },
    "MZBEW": {
        "name": "Beira",
        "country": "Mozambique",
        "iso": "MOZ",
        "flag": "🇲🇿",
        "region": "Afrique de l'Est",
        "coast": "IND",
        "lat": -19.83,
        "lon": 34.84,
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "thc_source": "Cornelder de Moçambique / Beira — Tariff 2024",
    },
    "MZMPM": {
        "name": "Maputo",
        "country": "Mozambique",
        "iso": "MOZ",
        "flag": "🇲🇿",
        "region": "Afrique de l'Est",
        "coast": "IND",
        "lat": -25.97,
        "lon": 32.57,
        "teu_usd": 195,
        "feu_usd": 290,
        "feu_hc_usd": 310,
        "thc_source": "MPDC Maputo Port Development Company — Tariff 2024",
    },
    # ===================== AFRIQUE AUSTRALE =====================
    "ZADUR": {
        "name": "Durban",
        "country": "Afrique du Sud",
        "iso": "ZAF",
        "flag": "🇿🇦",
        "region": "Afrique Australe",
        "coast": "IND",
        "lat": -29.87,
        "lon": 31.03,
        "teu_usd": 220,
        "feu_usd": 330,
        "feu_hc_usd": 355,
        "thc_source": "Transnet National Ports Authority — Tariff 2024/25",
    },
    "ZARCB": {
        "name": "Richards Bay",
        "country": "Afrique du Sud",
        "iso": "ZAF",
        "flag": "🇿🇦",
        "region": "Afrique Australe",
        "coast": "IND",
        "lat": -28.80,
        "lon": 32.08,
        "teu_usd": 215,
        "feu_usd": 325,
        "feu_hc_usd": 348,
        "thc_source": "Transnet National Ports Authority — Tariff 2024/25",
    },
    "ZAPLZ": {
        "name": "Port Elizabeth",
        "country": "Afrique du Sud",
        "iso": "ZAF",
        "flag": "🇿🇦",
        "region": "Afrique Australe",
        "coast": "IND",
        "lat": -33.96,
        "lon": 25.61,
        "teu_usd": 215,
        "feu_usd": 325,
        "feu_hc_usd": 348,
        "thc_source": "Transnet National Ports Authority — Tariff 2024/25",
    },
    "ZACPT": {
        "name": "Cape Town",
        "country": "Afrique du Sud",
        "iso": "ZAF",
        "flag": "🇿🇦",
        "region": "Afrique Australe",
        "coast": "ATL",
        "lat": -33.91,
        "lon": 18.43,
        "teu_usd": 210,
        "feu_usd": 315,
        "feu_hc_usd": 338,
        "thc_source": "Transnet National Ports Authority — Tariff 2024/25",
    },
    "NAWVB": {
        "name": "Walvis Bay",
        "country": "Namibie",
        "iso": "NAM",
        "flag": "🇳🇦",
        "region": "Afrique Australe",
        "coast": "ATL",
        "lat": -22.95,
        "lon": 14.50,
        "teu_usd": 185,
        "feu_usd": 275,
        "feu_hc_usd": 295,
        "thc_source": "Namport Namibian Ports Authority — Tariff 2024",
    },
    # ===================== ÎLES DE L'OCÉAN INDIEN =====================
    "MUPLU": {
        "name": "Port Louis",
        "country": "Maurice",
        "iso": "MUS",
        "flag": "🇲🇺",
        "region": "Océan Indien",
        "coast": "IND",
        "lat": -20.16,
        "lon": 57.50,
        "teu_usd": 190,
        "feu_usd": 280,
        "feu_hc_usd": 300,
        "thc_source": "MPA Mauritius Ports Authority — Tariff 2024",
    },
    "MGTMM": {
        "name": "Toamasina",
        "country": "Madagascar",
        "iso": "MDG",
        "flag": "🇲🇬",
        "region": "Océan Indien",
        "coast": "IND",
        "lat": -18.16,
        "lon": 49.41,
        "teu_usd": 190,
        "feu_usd": 280,
        "feu_hc_usd": 300,
        "thc_source": "MICTSL Toamasina — Tariff 2024",
    },
    "KMYVA": {
        "name": "Moroni",
        "country": "Comores",
        "iso": "COM",
        "flag": "🇰🇲",
        "region": "Océan Indien",
        "coast": "IND",
        "lat": -11.70,
        "lon": 43.26,
        "teu_usd": 190,
        "feu_usd": 280,
        "feu_hc_usd": 300,
        "thc_source": "Port de Moroni — Tariff 2024",
    },
    "SCVIC": {
        "name": "Victoria",
        "country": "Seychelles",
        "iso": "SYC",
        "flag": "🇸🇨",
        "region": "Océan Indien",
        "coast": "IND",
        "lat": -4.62,
        "lon": 55.45,
        "teu_usd": 190,
        "feu_usd": 280,
        "feu_hc_usd": 300,
        "thc_source": "Seychelles Ports Authority — Tariff 2024",
    },
}

# Points de passage maritimes obligés (lat, lon)
_WAYPOINTS = {
    "GIB": (35.95, -5.60),  # Détroit de Gibraltar (MED ↔ ATL)
    "SUEZ": (30.50, 32.35),  # Canal de Suez (MED ↔ RED)
    "BAB": (12.60, 43.40),  # Bab-el-Mandeb (RED ↔ IND)
    "CAPE": (-34.83, 19.50),  # Cap de Bonne-Espérance / Agulhas (ATL ↔ IND)
}

# Chaînes de points de passage selon la paire de façades (les listes multiples
# représentent des itinéraires alternatifs ; on retient le plus court).
_COAST_ROUTING = {
    frozenset(["MED", "ATL"]): [["GIB"]],
    frozenset(["MED", "RED"]): [["SUEZ"]],
    frozenset(["RED", "IND"]): [["BAB"]],
    frozenset(["ATL", "RED"]): [["GIB", "SUEZ"], ["CAPE", "BAB"]],
    frozenset(["MED", "IND"]): [["SUEZ", "BAB"], ["GIB", "CAPE"]],
    frozenset(["ATL", "IND"]): [["CAPE"], ["GIB", "SUEZ", "BAB"]],
}


def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance great-circle en milles nautiques."""
    r_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    km = 2 * r_km * asin(sqrt(a))
    return km / 1.852  # km → milles nautiques


def _sea_distance_nm(a: str, b: str) -> int:
    """Distance maritime réaliste entre deux ports via les points de passage obligés."""
    pa, pb = PORTS[a], PORTS[b]
    coast_a, coast_b = pa["coast"], pb["coast"]

    def chain_distance(chain: List[str]) -> float:
        pts = [(pa["lat"], pa["lon"])] + [_WAYPOINTS[w] for w in chain] + [(pb["lat"], pb["lon"])]
        return sum(_haversine_nm(*pts[i], *pts[i + 1]) for i in range(len(pts) - 1))

    if coast_a == coast_b:
        best = chain_distance([])
    else:
        chains = _COAST_ROUTING[frozenset([coast_a, coast_b])]
        best = min(chain_distance(c) for c in chains)

    # Facteur de routage côtier (les navires ne suivent pas la ligne droite stricte)
    return int(round(best * 1.07))


def _round5(x: float) -> int:
    return int(round(x / 5.0) * 5)


def _carriers_for(a: str, b: str) -> List[str]:
    regions = {PORTS[a]["region"], PORTS[b]["region"]}
    if regions & {"Afrique de l'Est", "Océan Indien", "Mer Rouge"} and not (
        regions & {"Afrique de l'Ouest", "Afrique Centrale"}
    ):
        return ["MSC", "Maersk", "CMA CGM", "PIL"]
    if regions <= {"Afrique Australe", "Océan Indien", "Afrique de l'Est"}:
        return ["Maersk", "MSC", "CMA CGM", "Safmarine"]
    if regions <= {"Afrique de l'Ouest", "Afrique Centrale"}:
        return ["CMA CGM", "MSC", "Maersk", "Grimaldi"]
    return ["MSC", "Maersk", "CMA CGM"]


# ------------------------------------------------------------------
# Calibrage 2026 du fret maritime (USD par EVP / 20', fret + surcharges
# courantes, hors THC).
#
# Le modèle 2024 (175 USD + 0,255 USD/mille) sous-estimait fortement le coût
# FIXE par boîte (escales, repositionnement des vides, équipement, surcharges) :
# Tanger Med→Alger ressortait à 290 USD/20' quand Marseille→Alger (distance
# comparable) se traite à 1 200 USD. Deux points de calage 2026 :
#   - Marseille→Alger, 434 milles : 1 200 USD/20' fret + surcharges (devis
#     transmis par des professionnels, novembre 2026), import Algérie ;
#   - Douala→Algésiras/Tanger Med, 2 247 milles : fret de base Maersk
#     1 295 USD/20' + ≈ 200 USD de surcharges (carburant, PSS) ≈ 1 500 USD.
# Résolution : coût fixe ≈ 900 USD/EVP, coût variable ≈ 0,265 USD/mille (la
# pente 2024 était juste, seul le coût fixe était faux).
# ------------------------------------------------------------------
_FIXED_TEU_USD = 900
_PER_NM_TEU_USD = 0.265
_LEGACY_FIXED_TEU_USD = 175  # modèle 2024, sert à actualiser les benchmarks
_LEGACY_PER_NM_TEU_USD = 0.255
_FEU_RATIO = 1.5
_FEU_HC_RATIO = 1.62

# Prime de marché à l'IMPORT par pays de destination (multiplicateur du fret).
# Algérie : +18 % par rapport aux voisins maghrébins sur les grilles FAK MSC
# Asie→Afrique du Nord 2026 (5 300 USD/20' Algérie contre 4 500 Casablanca),
# cohérent avec le devis Marseille→Alger. Causes citées : attente portuaire,
# retour des conteneurs vides à la charge des armateurs, concurrence réduite.
_DEST_MARKET_FACTOR = {"DZA": 1.18}

# Conteneur frigorifique (reefer) — hypothèses de pratique de marché, non
# calibrées sur un devis : le fret reefer vaut ≈ 1,4 à 2 fois le fret sec
# (surcharges d'urgence 2026 : ×1,3 à ×1,4 ; équipement, énergie, slots
# branchés). On retient ×1,6. 20' RF dérivé du 20' sec, 40' RH du 40' HC.
_REEFER_FREIGHT_RATIO = 1.6
_REEFER_THC_RATIO = 1.5  # branchement + surveillance au terminal

# Marchandises dangereuses (IMDG) — surcharge armateur par conteneur
# (Hapag-Lloyd 2026 : 200 USD classe 9, 250 USD classe 4.2 ; d'autres lignes
# vont bien au-delà) et majoration des THC pour la manutention DG.
_DG_SURCHARGE_USD = {"teu": 250, "feu": 400, "feu_hc": 400, "teu_rf": 250, "feu_rf": 400}
_DG_THC_RATIO = 1.5

CONTAINER_TYPES = ("teu", "feu", "feu_hc", "teu_rf", "feu_rf")

# Transbordement : hubs africains et coût du passage au hub.
_HUBS = ["MAPTM", "EGPSD", "TGLFW", "ZADUR", "MUPLU", "DJJIB"]
_TS_FEE_TEU_USD = 150  # manutention au hub (déchargement + rechargement), hypothèse
_TS_DWELL_DAYS = (3, 7)  # attente de la correspondance au hub, hypothèse

# Paires de régions reliées par des services directs (lignes côtières).
_DIRECT_REGION_PAIRS = {
    frozenset(p)
    for p in [
        ("Afrique de l'Ouest", "Afrique Centrale"),
        ("Afrique de l'Ouest", "Afrique Australe"),
        ("Afrique Centrale", "Afrique Australe"),
        ("Afrique de l'Est", "Afrique Australe"),
        ("Afrique de l'Est", "Océan Indien"),
        ("Afrique Australe", "Océan Indien"),
        ("Afrique de l'Est", "Mer Rouge"),
    ]
}
# Pays du Nord dotés de lignes directes au-delà de la Méditerranée.
_DIRECT_COUNTRY_REGIONS = {
    "MAR": {"Afrique de l'Ouest", "Afrique Centrale"},
    "EGY": {"Mer Rouge", "Afrique de l'Est"},
}


def _teu_rate(dist_nm: float) -> float:
    return _FIXED_TEU_USD + _PER_NM_TEU_USD * dist_nm


def _rates_from_teu(teu: float) -> Dict[str, int]:
    return {
        "teu_usd": _round5(teu),
        "feu_usd": _round5(teu * _FEU_RATIO),
        "feu_hc_usd": _round5(teu * _FEU_HC_RATIO),
    }


def _transit(dist_nm: float):
    tmin = max(2, int(round(dist_nm / 470.0)) + 1)
    tmax = max(tmin + 2, int(round(dist_nm / 320.0)) + 2)
    return tmin, tmax


def _has_direct_service(a: str, b: str) -> bool:
    """Vrai si un service direct (sans transbordement) relie couramment les deux ports."""
    if a in _HUBS or b in _HUBS:
        return True
    pa, pb = PORTS[a], PORTS[b]
    if pa["region"] == pb["region"]:
        return True
    if frozenset([pa["region"], pb["region"]]) in _DIRECT_REGION_PAIRS:
        return True
    return pb["region"] in _DIRECT_COUNTRY_REGIONS.get(pa["iso"], set()) or pa[
        "region"
    ] in _DIRECT_COUNTRY_REGIONS.get(pb["iso"], set())


def _best_hub(a: str, b: str):
    """Hub minimisant la distance totale origine→hub→destination."""
    return min(
        ((h, _sea_distance_nm(a, h), _sea_distance_nm(h, b)) for h in _HUBS if h not in (a, b)),
        key=lambda t: t[1] + t[2],
    )


def _model_route(a: str, b: str) -> Dict[str, Any]:
    """Génère une route modélisée (modèle distance-coût recalibré 2026) entre deux ports."""
    transshipment = None
    if _has_direct_service(a, b):
        dist = _sea_distance_nm(a, b)
        teu = _teu_rate(dist)
        transit_min, transit_max = _transit(dist)
        notes = "Tarif estimé par modèle recalibré 2026 (±15 %)."
    else:
        hub, d1, d2 = _best_hub(a, b)
        dist = d1 + d2
        teu = _teu_rate(dist) + _TS_FEE_TEU_USD
        transit_min, transit_max = _transit(dist)
        transit_min += _TS_DWELL_DAYS[0]
        transit_max += _TS_DWELL_DAYS[1]
        transshipment = {
            "hub_locode": hub,
            "hub_port": PORTS[hub]["name"],
            "leg1_nm": d1,
            "leg2_nm": d2,
            "hub_fee_teu_usd": _TS_FEE_TEU_USD,
            "dwell_days": list(_TS_DWELL_DAYS),
        }
        notes = (
            f"Pas de service direct : transbordement à {PORTS[hub]['name']} "
            f"(+{_TS_FEE_TEU_USD} USD/EVP de manutention au hub, "
            f"+{_TS_DWELL_DAYS[0]} à {_TS_DWELL_DAYS[1]} jours de correspondance). "
            "Tarif estimé par modèle recalibré 2026 (±15 %)."
        )
    if dist < 800:
        freq = "Hebdomadaire (feeder)"
    elif dist < 2500:
        freq = "Hebdomadaire"
    else:
        freq = "Bimensuelle"
    pa, pb = PORTS[a], PORTS[b]
    return {
        "route_id": f"{a}-{b}",
        "origin_locode": a,
        "destination_locode": b,
        "origin_port": pa["name"],
        "destination_port": pb["name"],
        "origin_country": pa["iso"],
        "destination_country": pb["iso"],
        "origin_region": pa["region"],
        "destination_region": pb["region"],
        "distance_nm": dist,
        "transit_days_min": transit_min,
        "transit_days_max": transit_max,
        **_rates_from_teu(teu),
        "carriers": _carriers_for(a, b),
        "frequency": freq,
        "transshipment": transshipment,
        "source": (
            "Modèle distance-coût recalibré 2026 (900 USD/EVP + 0,265 USD/mille) — calage : "
            "Marseille→Alger 1 200 USD/20' (professionnels, 2026), Maersk Douala→Algésiras "
            "1 295 USD/20' ; pente UNCTAD MRTS 2024 / Drewry 2024"
        ),
        "notes": notes,
        "rate_basis": "modele",
        "is_modeled": True,
    }


# ------------------------------------------------------------------
# Routes BENCHMARK — tarifs PUBLIÉS des armateurs (valeurs autoritaires)
# Unit: USD par conteneur (fret maritime, hors THC)
# ------------------------------------------------------------------
BENCHMARK_ROUTES: List[Dict[str, Any]] = [
    {
        "route_id": "MAPTM-SNDKR",
        "origin_locode": "MAPTM",
        "destination_locode": "SNDKR",
        "distance_nm": 1460,
        "transit_days_min": 5,
        "transit_days_max": 8,
        "teu_usd": 480,
        "feu_usd": 720,
        "feu_hc_usd": 780,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "Hebdomadaire",
        "source": "CMA CGM West Africa Rate Card Q4-2024; UNCTAD MRTS 2024 p.87",
        "notes": "Service pendulaire Dakar–Méditerranée, escale directe",
    },
    {
        "route_id": "MAPTM-CIABJ",
        "origin_locode": "MAPTM",
        "destination_locode": "CIABJ",
        "distance_nm": 3250,
        "transit_days_min": 9,
        "transit_days_max": 13,
        "teu_usd": 780,
        "feu_usd": 1150,
        "feu_hc_usd": 1240,
        "carriers": ["CMA CGM", "MSC", "Maersk"],
        "frequency": "Hebdomadaire",
        "source": "Maersk West Africa Rate Guide 2024; Drewry Container Insight Q3-2024",
        "notes": "Via transbordement Dakar ou escale pendulaire directe",
    },
    {
        "route_id": "MAPTM-GHTEM",
        "origin_locode": "MAPTM",
        "destination_locode": "GHTEM",
        "distance_nm": 3680,
        "transit_days_min": 10,
        "transit_days_max": 14,
        "teu_usd": 850,
        "feu_usd": 1260,
        "feu_hc_usd": 1360,
        "carriers": ["CMA CGM", "MSC", "Maersk", "Hapag-Lloyd"],
        "frequency": "Hebdomadaire",
        "source": "Hapag-Lloyd West Africa Rate Card 2024; UNCTAD MRTS 2024",
        "notes": "Service direct ou via Abidjan",
    },
    {
        "route_id": "MAPTM-NGAPP",
        "origin_locode": "MAPTM",
        "destination_locode": "NGAPP",
        "distance_nm": 4050,
        "transit_days_min": 11,
        "transit_days_max": 16,
        "teu_usd": 1100,
        "feu_usd": 1650,
        "feu_hc_usd": 1780,
        "carriers": ["CMA CGM", "MSC", "Maersk", "Hapag-Lloyd"],
        "frequency": "Hebdomadaire",
        "source": "MSC Nigeria Rate Bulletin Q4-2024; Drewry Nigeria Benchmark 2024",
        "notes": "Surcharge congestion (PSS) +$200/TEU possible à Lagos",
    },
    {
        "route_id": "MACAS-CIABJ",
        "origin_locode": "MACAS",
        "destination_locode": "CIABJ",
        "distance_nm": 3100,
        "transit_days_min": 8,
        "transit_days_max": 12,
        "teu_usd": 720,
        "feu_usd": 1080,
        "feu_hc_usd": 1165,
        "carriers": ["CMA CGM", "Grimaldi", "Delmas"],
        "frequency": "Bimensuelle",
        "source": "CMA CGM Maroc–Afrique de l'Ouest 2024; ANP Morocco Statistics",
        "notes": "Destination CEDEAO ; certificat d'origine peut réduire les droits",
    },
    {
        "route_id": "MACAS-NGAPP",
        "origin_locode": "MACAS",
        "destination_locode": "NGAPP",
        "distance_nm": 3900,
        "transit_days_min": 11,
        "transit_days_max": 15,
        "teu_usd": 980,
        "feu_usd": 1470,
        "feu_hc_usd": 1590,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "Hebdomadaire",
        "source": "Drewry West Africa Benchmark Q3-2024",
        "notes": "Tarif équivalent via Tanger Med ±5%",
    },
    {
        "route_id": "EGPSD-KEMBA",
        "origin_locode": "EGPSD",
        "destination_locode": "KEMBA",
        "distance_nm": 3100,
        "transit_days_min": 9,
        "transit_days_max": 13,
        "teu_usd": 720,
        "feu_usd": 1060,
        "feu_hc_usd": 1140,
        "carriers": ["MSC", "Maersk", "CMA CGM", "Evergreen"],
        "frequency": "Hebdomadaire",
        "source": "Maersk East Africa Rate Guide 2024; UNCTAD MRTS 2024 p.92",
        "notes": "Via canal de Suez — surcharge Suez incluse dans le tarif",
    },
    {
        "route_id": "EGPSD-TZDAR",
        "origin_locode": "EGPSD",
        "destination_locode": "TZDAR",
        "distance_nm": 3350,
        "transit_days_min": 10,
        "transit_days_max": 14,
        "teu_usd": 800,
        "feu_usd": 1180,
        "feu_hc_usd": 1270,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Hebdomadaire",
        "source": "MSC East Africa Rate Bulletin 2024",
        "notes": "Rotation EACS (East Africa Coastal Service)",
    },
    {
        "route_id": "EGPSD-ZADUR",
        "origin_locode": "EGPSD",
        "destination_locode": "ZADUR",
        "distance_nm": 5200,
        "transit_days_min": 14,
        "transit_days_max": 19,
        "teu_usd": 1350,
        "feu_usd": 2000,
        "feu_hc_usd": 2160,
        "carriers": ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd"],
        "frequency": "Hebdomadaire",
        "source": "Hapag-Lloyd South Africa Rate Card 2024; Drewry Q4-2024",
        "notes": "Option Cap de Bonne-Espérance ; via Suez plus rapide",
    },
    {
        "route_id": "MAPTM-KEMBA",
        "origin_locode": "MAPTM",
        "destination_locode": "KEMBA",
        "distance_nm": 7400,
        "transit_days_min": 18,
        "transit_days_max": 24,
        "teu_usd": 1850,
        "feu_usd": 2750,
        "feu_hc_usd": 2960,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Bimensuelle",
        "source": "CMA CGM Africa Med–East Rate Card 2024; UNCTAD MRTS 2024",
        "notes": "Via canal de Suez ; routage Cap +7 jours",
    },
    {
        "route_id": "MAPTM-ZADUR",
        "origin_locode": "MAPTM",
        "destination_locode": "ZADUR",
        "distance_nm": 9200,
        "transit_days_min": 22,
        "transit_days_max": 28,
        "teu_usd": 2600,
        "feu_usd": 3850,
        "feu_hc_usd": 4150,
        "carriers": ["MSC", "Maersk", "CMA CGM"],
        "frequency": "Hebdomadaire",
        "source": "Drewry Container Freight Rate Insight Africa 2024; MSC South Africa Rate Card Q4-2024",
        "notes": "Via Cap de Bonne-Espérance ; une des plus longues routes intra-africaines",
    },
    {
        "route_id": "SNDKR-CIABJ",
        "origin_locode": "SNDKR",
        "destination_locode": "CIABJ",
        "distance_nm": 1380,
        "transit_days_min": 4,
        "transit_days_max": 7,
        "teu_usd": 420,
        "feu_usd": 640,
        "feu_hc_usd": 690,
        "carriers": ["CMA CGM", "Grimaldi", "Delmas"],
        "frequency": "Hebdomadaire",
        "source": "CMA CGM West Africa Regional Rate Card 2024; World Bank LPI 2023",
        "notes": "Feeder short-sea ; fiabilité de transit élevée",
    },
    {
        "route_id": "SNDKR-GHTEM",
        "origin_locode": "SNDKR",
        "destination_locode": "GHTEM",
        "distance_nm": 1760,
        "transit_days_min": 5,
        "transit_days_max": 9,
        "teu_usd": 520,
        "feu_usd": 780,
        "feu_hc_usd": 840,
        "carriers": ["CMA CGM", "MSC", "Maersk"],
        "frequency": "Hebdomadaire",
        "source": "MSC West Africa rate bulletin 2024; Drewry Q3-2024",
        "notes": "Escale directe ou via Abidjan",
    },
    {
        "route_id": "SNDKR-NGAPP",
        "origin_locode": "SNDKR",
        "destination_locode": "NGAPP",
        "distance_nm": 2580,
        "transit_days_min": 7,
        "transit_days_max": 11,
        "teu_usd": 720,
        "feu_usd": 1070,
        "feu_hc_usd": 1155,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Hebdomadaire",
        "source": "Drewry Nigeria freight benchmark 2024",
        "notes": "Surcharge congestion à Apapa +$100-200/TEU",
    },
    {
        "route_id": "CIABJ-GHTEM",
        "origin_locode": "CIABJ",
        "destination_locode": "GHTEM",
        "distance_nm": 380,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 195,
        "feu_usd": 295,
        "feu_hc_usd": 318,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "2× hebdomadaire",
        "source": "CMA CGM West Africa coastal feeder tariff 2024; UNCTAD short-sea survey",
        "notes": "Feeder très court ; plus haute fréquence côtière en Afrique de l'Ouest",
    },
    {
        "route_id": "CIABJ-NGAPP",
        "origin_locode": "CIABJ",
        "destination_locode": "NGAPP",
        "distance_nm": 910,
        "transit_days_min": 3,
        "transit_days_max": 6,
        "teu_usd": 380,
        "feu_usd": 570,
        "feu_hc_usd": 615,
        "carriers": ["MSC", "CMA CGM", "Grimaldi", "Maersk"],
        "frequency": "Hebdomadaire",
        "source": "MSC Nigeria rate bulletin 2024; Drewry West Africa Q3-2024",
        "notes": "Surcharge congestion à Lagos possible (+$150-250/TEU)",
    },
    {
        "route_id": "GHTEM-NGAPP",
        "origin_locode": "GHTEM",
        "destination_locode": "NGAPP",
        "distance_nm": 540,
        "transit_days_min": 2,
        "transit_days_max": 5,
        "teu_usd": 255,
        "feu_usd": 385,
        "feu_hc_usd": 415,
        "carriers": ["MSC", "CMA CGM", "Maersk"],
        "frequency": "Hebdomadaire",
        "source": "Ghana Ports & Harbours Authority regional report 2024",
        "notes": "Feeder côtier ; alternative au transport routier Ghana–Nigeria",
    },
    {
        "route_id": "NGAPP-CMDLA",
        "origin_locode": "NGAPP",
        "destination_locode": "CMDLA",
        "distance_nm": 820,
        "transit_days_min": 3,
        "transit_days_max": 6,
        "teu_usd": 380,
        "feu_usd": 570,
        "feu_hc_usd": 615,
        "carriers": ["CMA CGM", "MSC", "Delmas"],
        "frequency": "Hebdomadaire",
        "source": "CMA CGM Gulf of Guinea rate card 2024",
        "notes": "Service short-sea Golfe de Guinée",
    },
    {
        "route_id": "CMDLA-CGPNR",
        "origin_locode": "CMDLA",
        "destination_locode": "CGPNR",
        "distance_nm": 740,
        "transit_days_min": 3,
        "transit_days_max": 5,
        "teu_usd": 340,
        "feu_usd": 510,
        "feu_hc_usd": 550,
        "carriers": ["CMA CGM", "MSC", "Bolloré"],
        "frequency": "Hebdomadaire",
        "source": "CMA CGM Central Africa coastal tariff 2024; CEMAC port statistics",
        "notes": "Feeder short-sea Afrique Centrale",
    },
    {
        "route_id": "CGPNR-AOLAD",
        "origin_locode": "CGPNR",
        "destination_locode": "AOLAD",
        "distance_nm": 550,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 290,
        "feu_usd": 435,
        "feu_hc_usd": 470,
        "carriers": ["MSC", "CMA CGM", "Safmarine"],
        "frequency": "Bimensuelle",
        "source": "Drewry Angola freight benchmark 2024",
        "notes": "Corridor court Angola–Congo ; feeder régulier",
    },
    {
        "route_id": "DJJIB-KEMBA",
        "origin_locode": "DJJIB",
        "destination_locode": "KEMBA",
        "distance_nm": 1180,
        "transit_days_min": 4,
        "transit_days_max": 7,
        "teu_usd": 360,
        "feu_usd": 535,
        "feu_hc_usd": 578,
        "carriers": ["MSC", "Maersk", "CMA CGM", "DP World"],
        "frequency": "Hebdomadaire",
        "source": "Maersk East Africa Rate Guide 2024; Kenya Ports Authority bulletin",
        "notes": "Corridor Corne de l'Afrique ; Djibouti hub clé",
    },
    {
        "route_id": "KEMBA-TZDAR",
        "origin_locode": "KEMBA",
        "destination_locode": "TZDAR",
        "distance_nm": 520,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 260,
        "feu_usd": 390,
        "feu_hc_usd": 420,
        "carriers": ["MSC", "Maersk", "CMA CGM"],
        "frequency": "Hebdomadaire",
        "source": "Tanzania Ports Authority — Short-sea survey 2024; Drewry East Africa Q3-2024",
        "notes": "Feeder côtier Afrique de l'Est ; ligne Mombasa–Dar courante",
    },
    {
        "route_id": "TZDAR-MZMPM",
        "origin_locode": "TZDAR",
        "destination_locode": "MZMPM",
        "distance_nm": 1850,
        "transit_days_min": 5,
        "transit_days_max": 9,
        "teu_usd": 520,
        "feu_usd": 780,
        "feu_hc_usd": 840,
        "carriers": ["MSC", "Maersk", "CMA CGM"],
        "frequency": "Bimensuelle",
        "source": "Drewry Southern/East Africa benchmark 2024",
        "notes": "Corridor Est–Sud ; transit du canal du Mozambique",
    },
    {
        "route_id": "KEMBA-MUPLU",
        "origin_locode": "KEMBA",
        "destination_locode": "MUPLU",
        "distance_nm": 2260,
        "transit_days_min": 7,
        "transit_days_max": 11,
        "teu_usd": 580,
        "feu_usd": 865,
        "feu_hc_usd": 935,
        "carriers": ["MSC", "CMA CGM", "Maersk", "X-Press Feeders"],
        "frequency": "Hebdomadaire",
        "source": "MSC Indian Ocean rate card 2024; Mauritius Port Authority data",
        "notes": "Corridor îles de l'océan Indien ; bonne connectivité via hub Maurice",
    },
    {
        "route_id": "ZADUR-ZACPT",
        "origin_locode": "ZADUR",
        "destination_locode": "ZACPT",
        "distance_nm": 870,
        "transit_days_min": 3,
        "transit_days_max": 5,
        "teu_usd": 300,
        "feu_usd": 450,
        "feu_hc_usd": 485,
        "carriers": ["Safmarine", "Transnet"],
        "frequency": "3× hebdomadaire",
        "source": "Transnet TNPA coastal tariff 2024; Safmarine South Africa coastal guide",
        "notes": "Cabotage domestique Afrique du Sud ; règles de cabotage applicables",
    },
    {
        "route_id": "ZADUR-MZMPM",
        "origin_locode": "ZADUR",
        "destination_locode": "MZMPM",
        "distance_nm": 440,
        "transit_days_min": 2,
        "transit_days_max": 4,
        "teu_usd": 240,
        "feu_usd": 360,
        "feu_hc_usd": 388,
        "carriers": ["Safmarine", "MSC", "CMA CGM"],
        "frequency": "Hebdomadaire",
        "source": "MPDC Maputo Port tariff bulletin 2024; Transnet TNPA data",
        "notes": "Durban–Maputo souvent combiné avec escale Beira",
    },
    {
        "route_id": "ZADUR-KEMBA",
        "origin_locode": "ZADUR",
        "destination_locode": "KEMBA",
        "distance_nm": 2650,
        "transit_days_min": 7,
        "transit_days_max": 11,
        "teu_usd": 900,
        "feu_usd": 1340,
        "feu_hc_usd": 1445,
        "carriers": ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd"],
        "frequency": "Hebdomadaire",
        "source": "Maersk East-Southern Africa Rate Guide 2024; Drewry Q4-2024",
        "notes": "Corridor majeur Sud–Est ; rotation SAGCS",
    },
    {
        "route_id": "ZADUR-NAWVB",
        "origin_locode": "ZADUR",
        "destination_locode": "NAWVB",
        "distance_nm": 1430,
        "transit_days_min": 5,
        "transit_days_max": 8,
        "teu_usd": 530,
        "feu_usd": 795,
        "feu_hc_usd": 858,
        "carriers": ["Safmarine", "MSC", "CMA CGM"],
        "frequency": "Bimensuelle",
        "source": "Namport Walvis Bay rate circular 2024; Drewry Southern Africa 2024",
        "notes": "Corridor Namibie ; Walvis Bay hub de transbordement SADC",
    },
    {
        "route_id": "NAWVB-NGAPP",
        "origin_locode": "NAWVB",
        "destination_locode": "NGAPP",
        "distance_nm": 3450,
        "transit_days_min": 10,
        "transit_days_max": 14,
        "teu_usd": 980,
        "feu_usd": 1470,
        "feu_hc_usd": 1586,
        "carriers": ["Maersk", "MSC", "CMA CGM"],
        "frequency": "Hebdomadaire",
        "source": "Drewry West–Southern Africa cross-trade 2024; Namport bulletin",
        "notes": "Commerce transversal Ouest–Sud ; Walvis Bay hub régional croissant",
    },
    {
        "route_id": "EGALY-ZADUR",
        "origin_locode": "EGALY",
        "destination_locode": "ZADUR",
        "distance_nm": 5150,
        "transit_days_min": 14,
        "transit_days_max": 18,
        "teu_usd": 1320,
        "feu_usd": 1960,
        "feu_hc_usd": 2115,
        "carriers": ["Maersk", "MSC", "CMA CGM"],
        "frequency": "Hebdomadaire",
        "source": "Hapag-Lloyd Egypt–South Africa rate card 2024; Drewry Q4-2024",
        "notes": "Via Suez ou Cap de Bonne-Espérance selon l'armateur",
    },
    {
        "route_id": "DZALG-NGAPP",
        "origin_locode": "DZALG",
        "destination_locode": "NGAPP",
        "distance_nm": 4100,
        "transit_days_min": 12,
        "transit_days_max": 17,
        "teu_usd": 1050,
        "feu_usd": 1575,
        "feu_hc_usd": 1700,
        "carriers": ["CMA CGM", "MSC", "Grimaldi"],
        "frequency": "Bimensuelle",
        "source": "EPAL Algeria port statistics 2024; Drewry West Africa Q3-2024",
        "notes": "Via Tanger Med ou direct ; service direct peu fréquent",
    },
    {
        "route_id": "TNRAD-KEMBA",
        "origin_locode": "TNRAD",
        "destination_locode": "KEMBA",
        "distance_nm": 3800,
        "transit_days_min": 11,
        "transit_days_max": 16,
        "teu_usd": 980,
        "feu_usd": 1450,
        "feu_hc_usd": 1565,
        "carriers": ["CMA CGM", "MSC", "Maersk"],
        "frequency": "Bimensuelle",
        "source": "OMMP Tunisia port statistics 2024; UNCTAD MRTS 2024",
        "notes": "Via hub de transbordement Port Saïd",
    },
]

BENCHMARK_ROUTES.extend(
    [
        {
            "route_id": "MACAS-SNDKR",
            "origin_locode": "MACAS",
            "destination_locode": "SNDKR",
            "distance_nm": 1520,
            "transit_days_min": 5,
            "transit_days_max": 8,
            "teu_usd": 510,
            "feu_usd": 760,
            "feu_hc_usd": 820,
            "carriers": ["CMA CGM", "MSC", "Grimaldi"],
            "frequency": "Weekly",
            "source": "CMA CGM Maroc–Afrique de l'Ouest 2024; Drewry West Africa short-sea benchmark 2024",
            "notes": "Direct Morocco–Senegal short-sea service with stable weekly rotations",
        },
        {
            "route_id": "MACAS-GHTEM",
            "origin_locode": "MACAS",
            "destination_locode": "GHTEM",
            "distance_nm": 3500,
            "transit_days_min": 10,
            "transit_days_max": 14,
            "teu_usd": 835,
            "feu_usd": 1245,
            "feu_hc_usd": 1340,
            "carriers": ["CMA CGM", "MSC", "Maersk"],
            "frequency": "Weekly",
            "source": "MSC West Africa rate bulletin 2024; Drewry Container Insight Q4-2024",
            "notes": "Often routed via Dakar or Abidjan with competitive Morocco–Ghana transit times",
        },
        {
            "route_id": "EGALY-KEMBA",
            "origin_locode": "EGALY",
            "destination_locode": "KEMBA",
            "distance_nm": 3180,
            "transit_days_min": 9,
            "transit_days_max": 13,
            "teu_usd": 745,
            "feu_usd": 1100,
            "feu_hc_usd": 1185,
            "carriers": ["MSC", "Maersk", "CMA CGM"],
            "frequency": "Weekly",
            "source": "Maersk East Africa Rate Guide 2024; Alexandria Port Authority shipping bulletin",
            "notes": "Alexandria competes with Port Saïd as a North Africa gateway into East Africa",
        },
        {
            "route_id": "EGALY-TZDAR",
            "origin_locode": "EGALY",
            "destination_locode": "TZDAR",
            "distance_nm": 3430,
            "transit_days_min": 10,
            "transit_days_max": 14,
            "teu_usd": 820,
            "feu_usd": 1215,
            "feu_hc_usd": 1310,
            "carriers": ["MSC", "CMA CGM", "Maersk"],
            "frequency": "Weekly",
            "source": "MSC East Africa rate bulletin 2024; UNCTAD MRTS 2024",
            "notes": "North Africa–Tanzania lane usually routed through Suez and East Africa coastal loops",
        },
        {
            "route_id": "SNDKR-CMDLA",
            "origin_locode": "SNDKR",
            "destination_locode": "CMDLA",
            "distance_nm": 1840,
            "transit_days_min": 5,
            "transit_days_max": 8,
            "teu_usd": 560,
            "feu_usd": 840,
            "feu_hc_usd": 905,
            "carriers": ["CMA CGM", "MSC", "Delmas"],
            "frequency": "Weekly",
            "source": "CMA CGM Gulf of Guinea rate card 2024; Drewry Central Africa coastal benchmark 2024",
            "notes": "Useful West-to-Central Africa feeder alternative to long-haul road corridors",
        },
        {
            "route_id": "CIABJ-CMDLA",
            "origin_locode": "CIABJ",
            "destination_locode": "CMDLA",
            "distance_nm": 920,
            "transit_days_min": 3,
            "transit_days_max": 6,
            "teu_usd": 405,
            "feu_usd": 610,
            "feu_hc_usd": 658,
            "carriers": ["MSC", "CMA CGM", "Maersk"],
            "frequency": "Weekly",
            "source": "MSC West & Central Africa rate bulletin 2024; UNCTAD short-sea survey",
            "notes": "Frequently quoted as a feeder via Tema or direct Gulf of Guinea string",
        },
        {
            "route_id": "GHTEM-CMDLA",
            "origin_locode": "GHTEM",
            "destination_locode": "CMDLA",
            "distance_nm": 780,
            "transit_days_min": 3,
            "transit_days_max": 5,
            "teu_usd": 350,
            "feu_usd": 525,
            "feu_hc_usd": 566,
            "carriers": ["MSC", "CMA CGM", "Grimaldi"],
            "frequency": "Weekly",
            "source": "Ghana Ports regional shipping bulletin 2024; Drewry Gulf of Guinea benchmark 2024",
            "notes": "Well-used Tema–Cameroon coastal corridor for consumer goods and project cargo",
        },
        {
            "route_id": "CMDLA-AOLAD",
            "origin_locode": "CMDLA",
            "destination_locode": "AOLAD",
            "distance_nm": 1240,
            "transit_days_min": 4,
            "transit_days_max": 7,
            "teu_usd": 470,
            "feu_usd": 705,
            "feu_hc_usd": 761,
            "carriers": ["CMA CGM", "MSC", "Bolloré"],
            "frequency": "Weekly",
            "source": "CMA CGM Central Africa coastal tariff 2024; Angola corridor shipping benchmark 2024",
            "notes": "Central Africa corridor with regular calls linking Cameroon and Angola",
        },
        {
            "route_id": "DJJIB-TZDAR",
            "origin_locode": "DJJIB",
            "destination_locode": "TZDAR",
            "distance_nm": 1520,
            "transit_days_min": 5,
            "transit_days_max": 8,
            "teu_usd": 430,
            "feu_usd": 645,
            "feu_hc_usd": 697,
            "carriers": ["MSC", "Maersk", "CMA CGM"],
            "frequency": "Weekly",
            "source": "Maersk East Africa feeder guide 2024; Tanzania Ports Authority coastal survey",
            "notes": "Horn of Africa to Tanzania feeder frequently used for transshipment from Asia-Europe loops",
        },
        {
            "route_id": "TZDAR-ZADUR",
            "origin_locode": "TZDAR",
            "destination_locode": "ZADUR",
            "distance_nm": 1680,
            "transit_days_min": 5,
            "transit_days_max": 8,
            "teu_usd": 560,
            "feu_usd": 840,
            "feu_hc_usd": 907,
            "carriers": ["MSC", "Maersk", "CMA CGM", "Hapag-Lloyd"],
            "frequency": "Weekly",
            "source": "Drewry East-Southern Africa benchmark 2024; Maersk South Africa trade guide",
            "notes": "Important East–Southern Africa lane for manufactured imports and reefer exports",
        },
        {
            "route_id": "MZMPM-ZACPT",
            "origin_locode": "MZMPM",
            "destination_locode": "ZACPT",
            "distance_nm": 1320,
            "transit_days_min": 4,
            "transit_days_max": 7,
            "teu_usd": 430,
            "feu_usd": 645,
            "feu_hc_usd": 697,
            "carriers": ["Safmarine", "MSC", "CMA CGM"],
            "frequency": "Weekly",
            "source": "Transnet TNPA coastal guide 2024; MPDC Maputo shipping circular 2024",
            "notes": "Southern Africa coastal connection between Mozambique and Western Cape distribution hubs",
        },
        {
            "route_id": "MUPLU-ZADUR",
            "origin_locode": "MUPLU",
            "destination_locode": "ZADUR",
            "distance_nm": 1540,
            "transit_days_min": 5,
            "transit_days_max": 8,
            "teu_usd": 470,
            "feu_usd": 705,
            "feu_hc_usd": 761,
            "carriers": ["MSC", "CMA CGM", "Maersk", "X-Press Feeders"],
            "frequency": "Weekly",
            "source": "MSC Indian Ocean rate card 2024; Mauritius Port Authority shipping statistics",
            "notes": "Strong Indian Ocean connection linking Mauritius with South Africa distribution centers",
        },
    ]
)


def _enrich_benchmark(r: Dict[str, Any]) -> Dict[str, Any]:
    """Complète une route benchmark et l'actualise au niveau de marché 2026.

    Les benchmarks sont des tarifs 2024 : on conserve leur écart propre à la
    ligne (congestion, concurrence) en les multipliant par le rapport entre le
    modèle recalibré 2026 et le modèle 2024 à la même distance.
    """
    a, b = r["origin_locode"], r["destination_locode"]
    pa, pb = PORTS[a], PORTS[b]
    d = r["distance_nm"]
    ratio = _teu_rate(d) / (_LEGACY_FIXED_TEU_USD + _LEGACY_PER_NM_TEU_USD * d)
    out = dict(r)
    out.update(
        {
            "origin_port": pa["name"],
            "destination_port": pb["name"],
            "origin_country": pa["iso"],
            "destination_country": pb["iso"],
            "origin_region": pa["region"],
            "destination_region": pb["region"],
            "published_2024": {k: r[k] for k in ("teu_usd", "feu_usd", "feu_hc_usd")},
            "teu_usd": _round5(r["teu_usd"] * ratio),
            "feu_usd": _round5(r["feu_usd"] * ratio),
            "feu_hc_usd": _round5(r["feu_hc_usd"] * ratio),
            "transshipment": None,
            "source": r["source"] + " — actualisé au niveau de marché 2026",
            "rate_basis": "benchmark_actualise",
            "is_modeled": True,
        }
    )
    return out


# ------------------------------------------------------------------
# Construction de la matrice complète (benchmark + modèle), mise en cache
# ------------------------------------------------------------------
def _build_route_matrix():
    benchmark_index = {
        frozenset([r["origin_locode"], r["destination_locode"]]): _enrich_benchmark(r)
        for r in BENCHMARK_ROUTES
    }
    locodes = list(PORTS.keys())
    index: Dict[frozenset, Dict[str, Any]] = {}
    for i in range(len(locodes)):
        for j in range(i + 1, len(locodes)):
            a, b = locodes[i], locodes[j]
            key = frozenset([a, b])
            index[key] = benchmark_index.get(key) or _model_route(a, b)
    return index


def _orient(route: Dict[str, Any], origin: str) -> Dict[str, Any]:
    """Retourne la route orientée avec ``origin`` comme port de départ."""
    if route["origin_locode"] == origin:
        return dict(route)
    rev = dict(route)
    rev["origin_locode"], rev["destination_locode"] = (
        route["destination_locode"],
        route["origin_locode"],
    )
    rev["origin_port"], rev["destination_port"] = route["destination_port"], route["origin_port"]
    rev["origin_country"], rev["destination_country"] = (
        route["destination_country"],
        route["origin_country"],
    )
    rev["origin_region"], rev["destination_region"] = (
        route["destination_region"],
        route["origin_region"],
    )
    rev["route_id"] = f'{route["origin_locode"]}-{route["destination_locode"]}_REV'
    if route.get("transshipment"):
        ts = dict(route["transshipment"])
        ts["leg1_nm"], ts["leg2_nm"] = ts["leg2_nm"], ts["leg1_nm"]
        rev["transshipment"] = ts
    return rev


def _priced(route: Dict[str, Any], origin: str) -> Dict[str, Any]:
    """Route orientée + prime de marché du pays de destination + tarifs reefer."""
    out = _orient(route, origin)
    factor = _DEST_MARKET_FACTOR.get(out["destination_country"], 1.0)
    out["market_factor"] = factor
    if factor != 1.0:
        for k in ("teu_usd", "feu_usd", "feu_hc_usd"):
            out[k] = _round5(out[k] * factor)
        out["notes"] = (
            f"{out.get('notes', '')} Prime marché import {out['destination_country']} "
            f"×{factor:.2f} (attente portuaire, retour des vides).".strip()
        )
    out["teu_rf_usd"] = _round5(out["teu_usd"] * _REEFER_FREIGHT_RATIO)
    out["feu_rf_usd"] = _round5(out["feu_hc_usd"] * _REEFER_FREIGHT_RATIO)
    return out


_ROUTE_INDEX = _build_route_matrix()
_ORIENTED: Dict[tuple, Dict[str, Any]] = {}
for _key, _route in _ROUTE_INDEX.items():
    _a, _b = _route["origin_locode"], _route["destination_locode"]
    _ORIENTED[(_a, _b)] = _priced(_route, _a)
    _ORIENTED[(_b, _a)] = _priced(_route, _b)
_ALL_ROUTES = sorted(
    (_ORIENTED[(r["origin_locode"], r["destination_locode"])] for r in _ROUTE_INDEX.values()),
    key=lambda r: (r["origin_region"], r["origin_port"], r["destination_port"]),
)
SHIPPING_ROUTES = BENCHMARK_ROUTES


# ------------------------------------------------------------------
# API publique (signatures inchangées pour routes/logistics.py)
# ------------------------------------------------------------------
def get_all_shipping_routes() -> List[Dict[str, Any]]:
    """Retourne toutes les routes port-à-port (une entrée par paire)."""
    return _ALL_ROUTES


def get_routes_from_port(origin_locode: str) -> List[Dict[str, Any]]:
    """Retourne toutes les routes touchant un port donné, orientées depuis ce port."""
    origin_locode = origin_locode.upper()
    if origin_locode not in PORTS:
        return []
    out = [r for (o, _d), r in _ORIENTED.items() if o == origin_locode]
    out.sort(key=lambda r: r["distance_nm"])
    return out


def get_route_between(origin_locode: str, destination_locode: str) -> Optional[Dict[str, Any]]:
    """Retourne la route entre deux ports (orientée origine→destination)."""
    return _ORIENTED.get((origin_locode.upper(), destination_locode.upper()))


@lru_cache(maxsize=1)
def _port_thc_map() -> Dict[str, Dict[str, Any]]:
    out = {}
    for locode, p in PORTS.items():
        out[locode] = {
            "port_id": f'{p["iso"]}-{locode}',
            "port_name": p["name"],
            "country": p["country"],
            "teu_usd": p["teu_usd"],
            "feu_usd": p["feu_usd"],
            "feu_hc_usd": p["feu_hc_usd"],
            "teu_rf_usd": _round5(p["teu_usd"] * _REEFER_THC_RATIO),
            "feu_rf_usd": _round5(p["feu_hc_usd"] * _REEFER_THC_RATIO),
            "source": p["thc_source"],
            "reefer_source": f"Estimation : THC sec ×{_REEFER_THC_RATIO} (branchement, surveillance)",
        }
    return out


def get_port_thc(locode: str) -> Optional[Dict[str, Any]]:
    """Retourne les Terminal Handling Charges d'un port (UN LOCODE)."""
    return _port_thc_map().get(locode.upper())


def get_all_port_thc() -> Dict[str, Dict[str, Any]]:
    """Retourne les THC de tous les ports."""
    return _port_thc_map()


PORT_THC = _port_thc_map()


def get_fee_ports() -> List[Dict[str, Any]]:
    """Retourne la liste des ports sélectionnables (pour le frontend)."""
    return [
        {
            "locode": locode,
            "name": p["name"],
            "country": p["country"],
            "iso": p["iso"],
            "flag": p["flag"],
            "region": p["region"],
        }
        for locode, p in sorted(PORTS.items(), key=lambda kv: (kv[1]["region"], kv[1]["name"]))
    ]


def get_total_cost(
    origin_locode: str,
    destination_locode: str,
    container_type: str = "teu",
    dangerous: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Calcule le coût tout compris (fret maritime + THC origine + THC destination)
    pour une paire de ports et un type de conteneur (sec, high cube ou reefer),
    avec en option la surcharge marchandises dangereuses (IMDG).
    """
    route = get_route_between(origin_locode, destination_locode)
    if not route:
        return None

    ctype = container_type.lower()
    rate_key = f"{ctype}_usd"
    if ctype not in CONTAINER_TYPES or rate_key not in route:
        return None

    ocean_freight = route[rate_key]
    origin_thc_data = get_port_thc(origin_locode)
    destination_thc_data = get_port_thc(destination_locode)
    origin_thc = origin_thc_data.get(rate_key, 0) if origin_thc_data else 0
    destination_thc = destination_thc_data.get(rate_key, 0) if destination_thc_data else 0

    dg_surcharge = 0
    if dangerous:
        dg_surcharge = _DG_SURCHARGE_USD[ctype]
        origin_thc = _round5(origin_thc * _DG_THC_RATIO)
        destination_thc = _round5(destination_thc * _DG_THC_RATIO)
    total = ocean_freight + dg_surcharge + origin_thc + destination_thc

    disclaimer = (
        "Estimation au niveau de marché 2026 : fret + surcharges courantes, calée sur des devis "
        "réels (Marseille→Alger, Douala→Algésiras). Les tarifs réels varient ±15 % selon "
        "l'armateur, la saison (surcharges de haute saison) et le délai de réservation. "
        "Hors : pré/post-acheminement terrestre, droits de douane, assurance, frais "
        "documentaires, surestaries."
    )
    if ctype in ("teu_rf", "feu_rf"):
        disclaimer += (
            f" Reefer : fret sec ×{_REEFER_FREIGHT_RATIO} et THC ×{_REEFER_THC_RATIO} "
            "(hypothèses de marché, hors branchement prolongé)."
        )
    if dangerous:
        disclaimer += (
            f" Marchandises dangereuses : surcharge IMDG de {dg_surcharge} USD et THC "
            f"×{_DG_THC_RATIO} (hypothèses) ; acceptation soumise à l'armateur selon la "
            "classe (classes 1 et 7 souvent refusées), déclaration DGD obligatoire."
        )

    return {
        "route_id": route["route_id"],
        "origin_locode": origin_locode.upper(),
        "destination_locode": destination_locode.upper(),
        "origin_port": route["origin_port"],
        "destination_port": route["destination_port"],
        "origin_country": route["origin_country"],
        "destination_country": route["destination_country"],
        "container_type": ctype.upper(),
        "dangerous": dangerous,
        "distance_nm": route["distance_nm"],
        "transit_days_min": route["transit_days_min"],
        "transit_days_max": route["transit_days_max"],
        "ocean_freight_usd": ocean_freight,
        "dg_surcharge_usd": dg_surcharge,
        "origin_thc_usd": origin_thc,
        "destination_thc_usd": destination_thc,
        "total_cost_usd": total,
        "transshipment": route.get("transshipment"),
        "market_factor": route.get("market_factor", 1.0),
        "carriers": route["carriers"],
        "frequency": route["frequency"],
        "source": route["source"],
        "notes": route.get("notes", ""),
        "rate_basis": route.get("rate_basis"),
        "is_modeled": route.get("is_modeled", False),
        "data_year": 2026,
        "currency": "USD",
        "disclaimer": disclaimer,
    }
