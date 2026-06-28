"""
Agrégateur d'actualités économiques africaines
Sources: Agence Ecofin, Reuters Africa, AllAfrica
Mise à jour: Une fois par jour
"""

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import feedparser

# Configuration des flux RSS
# Chaque source pan-africaine couvre tout le continent ; les sources "pays" utilisent
# des requêtes Google News ciblées avec des opérateurs site: sur des médias économiques
# locaux de premier plan, afin de garantir une couverture par pays sans dépendre de flux
# RSS directs (souvent absents ou instables sur les sites de presse africains).
RSS_FEEDS = {
    "allafrica_en": {
        "name": "AllAfrica",
        "feeds": {
            "business": "https://allafrica.com/tools/headlines/rdf/business/headlines.rdf",
            "trade": "https://allafrica.com/tools/headlines/rdf/trade/headlines.rdf",
            "banking": "https://allafrica.com/tools/headlines/rdf/banking/headlines.rdf",
        },
        "language": "en",
        "logo": "📰",
    },
    "allafrica_fr": {
        "name": "AllAfrica (FR)",
        "feeds": {
            "business": "https://fr.allafrica.com/tools/headlines/rdf/business/headlines.rdf",
        },
        "language": "fr",
        "logo": "📰",
    },
    "google_news_africa": {
        "name": "Google News (Reuters, AFP, etc.)",
        "feeds": {
            "business_en": "https://news.google.com/rss/search?q=africa+economy+business&hl=en",
            "economie_fr": "https://news.google.com/rss/search?q=afrique+%C3%A9conomie&hl=fr",
        },
        "language": "multi",
        "logo": "🌐",
    },
    # Médias panafricains de référence (premier plan)
    "agence_ecofin": {
        "name": "Agence Ecofin",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:agenceecofin.com&hl=fr",
        },
        "language": "fr",
        "logo": "📰",
    },
    "the_africa_report": {
        "name": "The Africa Report",
        "feeds": {
            "business": "https://news.google.com/rss/search?q=site:theafricareport.com&hl=fr",
        },
        "language": "multi",
        "logo": "🌍",
    },
    "african_business": {
        "name": "African Business / APA News",
        "feeds": {
            "business": "https://news.google.com/rss/search?q=site:african.business+OR+site:apanews.net&hl=en",
        },
        "language": "en",
        "logo": "🌍",
    },
    # PRIORITÉ ALGÉRIE - Flux dédiés
    "google_news_algeria": {
        "name": "Algérie Économie",
        "country": "DZA",
        "feeds": {
            "economie_dz": "https://news.google.com/rss/search?q=alg%C3%A9rie+%C3%A9conomie+investissement&hl=fr",
            "industry_dz": "https://news.google.com/rss/search?q=algeria+industry+manufacturing&hl=en",
        },
        "language": "multi",
        "logo": "🇩🇿",
        "priority": True,
    },
    "algeria_local": {
        "name": "APS / El Watan / Liberté / TSA",
        "country": "DZA",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:aps.dz+OR+site:elwatan.com+OR+site:liberte-algerie.com+OR+site:tsa-algerie.com&hl=fr",
        },
        "language": "fr",
        "logo": "🇩🇿",
        "priority": True,
    },
    # Afrique du Nord
    "morocco_local": {
        "name": "Médias24 / La Vie Éco",
        "country": "MAR",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:medias24.com+OR+site:lavieeco.com&hl=fr",
        },
        "language": "fr",
        "logo": "🇲🇦",
    },
    "tunisia_local": {
        "name": "African Manager / WMC",
        "country": "TUN",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:africanmanager.com+OR+site:webmanagercenter.com&hl=fr",
        },
        "language": "fr",
        "logo": "🇹🇳",
    },
    "egypt_local": {
        "name": "Daily News Egypt / Ahram Online",
        "country": "EGY",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:dailynewsegypt.com+OR+site:english.ahram.org.eg&hl=en",
        },
        "language": "en",
        "logo": "🇪🇬",
    },
    # Afrique de l'Ouest
    "nigeria_local": {
        "name": "BusinessDay / Vanguard Nigeria",
        "country": "NGA",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:businessday.ng+OR+site:vanguardngr.com&hl=en",
        },
        "language": "en",
        "logo": "🇳🇬",
    },
    "ghana_local": {
        "name": "MyJoyOnline / Joy Business",
        "country": "GHA",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:myjoyonline.com+ghana+economy&hl=en",
        },
        "language": "en",
        "logo": "🇬🇭",
    },
    "cote_ivoire_local": {
        "name": "Fraternité Matin / Abidjan.net",
        "country": "CIV",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:fratmat.info+OR+site:abidjan.net+%C3%A9conomie&hl=fr",
        },
        "language": "fr",
        "logo": "🇨🇮",
    },
    "senegal_local": {
        "name": "Le Soleil / APS Sénégal",
        "country": "SEN",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:lesoleil.sn+OR+site:aps.sn+%C3%A9conomie&hl=fr",
        },
        "language": "fr",
        "logo": "🇸🇳",
    },
    # Afrique Centrale
    "cameroon_local": {
        "name": "Investir au Cameroun / Cameroon Tribune",
        "country": "CMR",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:investiraucameroun.com+OR+site:cameroon-tribune.cm&hl=fr",
        },
        "language": "fr",
        "logo": "🇨🇲",
    },
    "drc_local": {
        "name": "Actualite.cd",
        "country": "COD",
        "feeds": {
            "economie": "https://news.google.com/rss/search?q=site:actualite.cd+%C3%A9conomie&hl=fr",
        },
        "language": "fr",
        "logo": "🇨🇩",
    },
    # Afrique de l'Est
    "kenya_local": {
        "name": "Business Daily Africa",
        "country": "KEN",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:businessdailyafrica.com&hl=en",
        },
        "language": "en",
        "logo": "🇰🇪",
    },
    "ethiopia_local": {
        "name": "Addis Fortune / The Reporter Ethiopia",
        "country": "ETH",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:addisfortune.news+OR+site:thereporterethiopia.com&hl=en",
        },
        "language": "en",
        "logo": "🇪🇹",
    },
    "rwanda_local": {
        "name": "The New Times Rwanda",
        "country": "RWA",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:newtimes.co.rw+economy&hl=en",
        },
        "language": "en",
        "logo": "🇷🇼",
    },
    # Afrique Australe
    "south_africa_local": {
        "name": "BusinessTech / Moneyweb",
        "country": "ZAF",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:businesstech.co.za+OR+site:moneyweb.co.za&hl=en",
        },
        "language": "en",
        "logo": "🇿🇦",
    },
    "angola_local": {
        "name": "Jornal de Angola",
        "country": "AGO",
        "feeds": {
            "economia": "https://news.google.com/rss/search?q=site:jornaldeangola.ao+economia&hl=pt",
        },
        "language": "pt",
        "logo": "🇦🇴",
    },
    "mozambique_local": {
        "name": "Club of Mozambique",
        "country": "MOZ",
        "feeds": {
            "economy": "https://news.google.com/rss/search?q=site:clubofmozambique.com+economy&hl=en",
        },
        "language": "en",
        "logo": "🇲🇿",
    },
}

# Projets structurants algériens - Mise à jour Février 2025
ALGERIA_STRUCTURAL_PROJECTS = [
    {
        "id": "gara-djebilet",
        "title": "Projet Gara Djebilet - Mine de fer",
        "summary": "Exploitation du gisement de fer de Gara Djebilet à Tindouf. Production prévue: 50 millions tonnes/an. Partenariat Algérie-Chine. Phase 1 opérationnelle depuis 2024.",
        "category": "Mines",
        "region": "Afrique du Nord",
        "status": "OPÉRATIONNEL",
        "investment_musd": 6000,
        "source": "Ministère de l'Industrie Algérien",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "phosphate-tebessa",
        "title": "Complexe phosphate intégré de Tébessa",
        "summary": "Exploitation des phosphates de Bled El Hadba et production d'engrais. Capacité: 10 millions tonnes/an de minerai, 5.4 millions tonnes d'engrais. Joint-venture avec la Chine.",
        "category": "Mines",
        "region": "Afrique du Nord",
        "status": "EN CONSTRUCTION",
        "investment_musd": 7000,
        "source": "ASMIDAL/Sonatrach",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "port-el-hamdania",
        "title": "Port en eaux profondes d'El Hamdania (Cherchell)",
        "summary": "Méga-port commercial et logistique à Cherchell. Capacité: 6.5 millions de conteneurs EVP/an. Hub méditerranéen majeur. Travaux en cours.",
        "category": "Infrastructure",
        "region": "Afrique du Nord",
        "status": "EN CONSTRUCTION",
        "investment_musd": 3300,
        "source": "Ministère des Transports",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "autoroute-transsaharienne",
        "title": "Autoroute Transsaharienne Alger-Lagos",
        "summary": "Section algérienne de l'autoroute Trans-saharienne reliant Alger à Lagos (Nigeria). 2500 km en Algérie. Segment In Guezzam opérationnel.",
        "category": "Infrastructure",
        "region": "Afrique du Nord",
        "status": "PARTIELLEMENT OPÉRATIONNEL",
        "investment_musd": 2500,
        "source": "Direction des Travaux Publics",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "usine-fiat-oran",
        "title": "Usine automobile FIAT à Oran (Tafraoui)",
        "summary": "Usine d'assemblage et de production de véhicules FIAT. Capacité: 60,000 véhicules/an. Opérationnelle depuis 2023 avec modèles Fiat 500 et Doblo.",
        "category": "Industrie",
        "region": "Afrique du Nord",
        "status": "OPÉRATIONNEL",
        "investment_musd": 200,
        "source": "Stellantis Algeria",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "raffinerie-hassi-messaoud",
        "title": "Raffinerie de Hassi Messaoud",
        "summary": "Nouvelle raffinerie de pétrole à Hassi Messaoud. Capacité de traitement: 5 millions tonnes/an. Réduit les importations de carburants.",
        "category": "Énergie",
        "region": "Afrique du Nord",
        "status": "OPÉRATIONNEL",
        "investment_musd": 3500,
        "source": "Sonatrach",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "centrale-solaire-djanet",
        "title": "Parc solaire de Djanet (1 GW)",
        "summary": "Centrale solaire photovoltaïque de grande envergure dans le sud algérien. Programme Tafouk1. Première phase 1GW opérationnelle.",
        "category": "Énergie",
        "region": "Afrique du Nord",
        "status": "OPÉRATIONNEL",
        "investment_musd": 800,
        "source": "SKTM/Sonelgaz",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "gazoduc-nigeria-algerie",
        "title": "Gazoduc Trans-Saharien (TSGP) Nigeria-Algérie",
        "summary": "Pipeline de gaz naturel reliant le Nigeria à l'Algérie puis l'Europe via la Méditerranée. 4,128 km. Accord signé, études en cours.",
        "category": "Énergie",
        "region": "Afrique du Nord",
        "status": "EN ÉTUDE",
        "investment_musd": 13000,
        "source": "Sonatrach/NNPC",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "complexe-acier-bellara",
        "title": "Complexe sidérurgique de Bellara (Jijel)",
        "summary": "Aciérie intégrée à Bellara, Jijel. Capacité: 4 millions tonnes d'acier/an. Joint-venture Algérie-Qatar. Pleinement opérationnel.",
        "category": "Industrie",
        "region": "Afrique du Nord",
        "status": "OPÉRATIONNEL",
        "investment_musd": 2000,
        "source": "Algerian Qatari Steel (AQS)",
        "link": "https://www.aps.dz/economie",
    },
    {
        "id": "zone-franche-belloua",
        "title": "Zone franche commerciale de Belloua",
        "summary": "Plateforme logistique et zone franche aux frontières avec le Mali et le Niger. Hub pour le commerce transsaharien sous la ZLECAf.",
        "category": "Commerce",
        "region": "Afrique du Nord",
        "status": "EN DÉVELOPPEMENT",
        "investment_musd": 500,
        "source": "Ministère du Commerce",
        "link": "https://www.aps.dz/economie",
    },
]

# Mapping des pays africains pour la détection de région - SAHARA OCCIDENTAL AJOUTÉ
REGION_KEYWORDS = {
    "Afrique du Nord": [
        "algérie",
        "algeria",
        "maroc",
        "morocco",
        "tunisie",
        "tunisia",
        "egypte",
        "egypt",
        "libye",
        "libya",
        "mauritanie",
        "mauritania",
        "sahara occidental",
        "western sahara",
        "rasd",
        "sahrawi",
    ],
    "Afrique de l'Ouest": [
        "sénégal",
        "senegal",
        "côte d'ivoire",
        "ivory coast",
        "ghana",
        "nigeria",
        "mali",
        "burkina",
        "niger",
        "bénin",
        "benin",
        "togo",
        "guinée",
        "guinea",
        "liberia",
        "sierra leone",
        "gambie",
        "gambia",
        "cedeao",
        "ecowas",
        "uemoa",
    ],
    "Afrique Centrale": [
        "cameroun",
        "cameroon",
        "gabon",
        "congo",
        "rdc",
        "drc",
        "tchad",
        "chad",
        "centrafrique",
        "car",
        "guinée équatoriale",
        "equatorial guinea",
        "cemac",
    ],
    "Afrique de l'Est": [
        "kenya",
        "tanzanie",
        "tanzania",
        "ethiopie",
        "ethiopia",
        "ouganda",
        "uganda",
        "rwanda",
        "burundi",
        "somalie",
        "somalia",
        "djibouti",
        "erythrée",
        "eritrea",
        "soudan",
        "sudan",
        "eac",
    ],
    "Afrique Australe": [
        "afrique du sud",
        "south africa",
        "angola",
        "mozambique",
        "zambie",
        "zambia",
        "zimbabwe",
        "botswana",
        "namibie",
        "namibia",
        "malawi",
        "madagascar",
        "maurice",
        "mauritius",
        "sadc",
    ],
}

CATEGORY_KEYWORDS = {
    "Finance": [
        "banque",
        "bank",
        "finance",
        "fmi",
        "imf",
        "bourse",
        "stock",
        "investissement",
        "investment",
        "crédit",
        "credit",
        "monnaie",
        "currency",
        "dette",
        "debt",
    ],
    "Commerce": [
        "commerce",
        "trade",
        "export",
        "import",
        "zlecaf",
        "afcfta",
        "douane",
        "customs",
        "tarif",
        "tariff",
    ],
    "Énergie": [
        "énergie",
        "energy",
        "électricité",
        "electricity",
        "pétrole",
        "oil",
        "gaz",
        "gas",
        "solaire",
        "solar",
        "renouvelable",
        "renewable",
    ],
    "Agriculture": [
        "agriculture",
        "agro",
        "céréales",
        "cereals",
        "cacao",
        "café",
        "coffee",
        "coton",
        "cotton",
        "élevage",
        "livestock",
    ],
    "Mines": [
        "mines",
        "mining",
        "or",
        "gold",
        "fer",
        "iron",
        "diamant",
        "diamond",
        "phosphate",
        "cuivre",
        "copper",
    ],
    "Télécoms": [
        "télécom",
        "telecom",
        "mobile",
        "internet",
        "numérique",
        "digital",
        "tech",
        "startup",
    ],
    "Infrastructure": [
        "infrastructure",
        "port",
        "aéroport",
        "airport",
        "route",
        "road",
        "rail",
        "chemin de fer",
        "construction",
    ],
}

# Mots-clés pour la priorisation éditoriale: dépêches à plus forte valeur stratégique
# (statistiques chiffrées, opportunités d'affaires, projets de développement, événements)
CONTENT_PRIORITY_KEYWORDS = {
    "statistics": {
        "keywords": [
            "croissance",
            "growth",
            "pib",
            "gdp",
            "taux",
            "rate",
            "%",
            "milliard",
            "billion",
            "million",
            "statistique",
            "statistics",
            "données",
            "data",
            "rapport annuel",
            "annual report",
            "indice",
            "index",
            "classement",
            "ranking",
            "prévisions",
            "forecast",
        ],
    },
    "opportunities": {
        "keywords": [
            "opportunité",
            "opportunity",
            "appel d'offres",
            "tender",
            "investissement",
            "investment",
            "partenariat",
            "partnership",
            "accord commercial",
            "trade deal",
            "contrat",
            "contract",
            "financement",
            "funding",
            "joint-venture",
            "joint venture",
            "marché public",
        ],
    },
    "development": {
        "keywords": [
            "développement",
            "development",
            "projet structurant",
            "infrastructure",
            "usine",
            "factory",
            "plant",
            "zone industrielle",
            "industrial zone",
            "zone franche",
            "free zone",
            "corridor",
            "chemin de fer",
            "railway",
            "barrage",
            "dam",
            "énergie renouvelable",
            "renewable energy",
            "transition énergétique",
        ],
    },
    "events": {
        "keywords": [
            "sommet",
            "summit",
            "forum",
            "conférence",
            "conference",
            "salon",
            "exposition",
            "exhibition",
            "sommet de l'ua",
            "au summit",
            "sommet zlecaf",
            "afcfta summit",
            "réunion ministérielle",
            "ministerial meeting",
            "assemblée générale",
            "general assembly",
        ],
    },
}

# Cache des actualités
NEWS_CACHE_FILE = str(Path(__file__).parent.parent / "data" / "news_cache.json")
NEWS_CACHE: Dict = {"last_update": None, "articles": []}


def detect_region(text: str) -> str:
    """Détecter la région africaine mentionnée dans le texte"""
    text_lower = text.lower()
    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return region
    return "Afrique"  # Défaut si aucune région détectée


def detect_category(text: str, feed_category: str = "") -> str:
    """Détecter la catégorie de l'article"""
    text_lower = text.lower()

    # Priorité au feed_category si disponible
    category_map = {
        "finance": "Finance",
        "banking": "Finance",
        "stock": "Finance",
        "trade": "Commerce",
        "business": "Économie",
        "economy": "Économie",
        "agriculture": "Agriculture",
        "agro": "Agriculture",
        "energie": "Énergie",
        "electricite": "Énergie",
        "hydrocarbures": "Énergie",
        "mines": "Mines",
        "telecom": "Télécoms",
        "tic": "Télécoms",
        "gestion_publique": "Gouvernance",
    }

    if feed_category and feed_category.lower() in category_map:
        return category_map[feed_category.lower()]

    # Sinon, détecter par mots-clés
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    return "Économie"  # Défaut


# Mapping pays (ISO3) -> région, utilisé comme repli quand la source est dédiée à un pays
# mais que le texte de l'article ne mentionne pas explicitement son nom.
COUNTRY_REGION_MAP = {
    "DZA": "Afrique du Nord",
    "MAR": "Afrique du Nord",
    "TUN": "Afrique du Nord",
    "EGY": "Afrique du Nord",
    "LBY": "Afrique du Nord",
    "MRT": "Afrique du Nord",
    "NGA": "Afrique de l'Ouest",
    "GHA": "Afrique de l'Ouest",
    "CIV": "Afrique de l'Ouest",
    "SEN": "Afrique de l'Ouest",
    "CMR": "Afrique Centrale",
    "COD": "Afrique Centrale",
    "GAB": "Afrique Centrale",
    "KEN": "Afrique de l'Est",
    "ETH": "Afrique de l'Est",
    "RWA": "Afrique de l'Est",
    "TZA": "Afrique de l'Est",
    "ZAF": "Afrique Australe",
    "AGO": "Afrique Australe",
    "MOZ": "Afrique Australe",
}


# Mots-clés (FR/EN) associés au nom de chaque pays, utilisés comme repli pour le
# filtrage par pays quand un article n'est pas tagué avec son code ISO3 (ex: articles
# panafricains mentionnant un pays dans leur titre).
COUNTRY_NAME_KEYWORDS = {
    "DZA": ["algérie", "algeria", "algérien", "algerian"],
    "MAR": ["maroc", "morocco", "marocain", "moroccan"],
    "TUN": ["tunisie", "tunisia", "tunisien", "tunisian"],
    "EGY": ["égypte", "egypt", "égyptien", "egyptian"],
    "NGA": ["nigéria", "nigeria", "nigérian", "nigerian"],
    "GHA": ["ghana", "ghanéen", "ghanaian"],
    "CIV": ["côte d'ivoire", "ivory coast", "ivoirien", "ivorian"],
    "SEN": ["sénégal", "senegal", "sénégalais", "senegalese"],
    "CMR": ["cameroun", "cameroon", "camerounais"],
    "COD": ["congo", "rdc", "drc", "congolais", "congolese"],
    "KEN": ["kenya", "kényan", "kenyan"],
    "ETH": ["éthiopie", "ethiopia", "éthiopien", "ethiopian"],
    "RWA": ["rwanda", "rwandais", "rwandan"],
    "ZAF": ["afrique du sud", "south africa", "sud-africain", "south african"],
    "AGO": ["angola", "angolais", "angolan"],
    "MOZ": ["mozambique", "mozambicain"],
}

# Noms d'affichage (FR/EN) et drapeau pour chaque pays disposant d'une source dédiée,
# utilisés pour le "pays de la semaine" mis en avant dans le dashboard.
COUNTRY_DISPLAY_NAMES = {
    "DZA": ("Algérie", "Algeria", "🇩🇿"),
    "MAR": ("Maroc", "Morocco", "🇲🇦"),
    "TUN": ("Tunisie", "Tunisia", "🇹🇳"),
    "EGY": ("Égypte", "Egypt", "🇪🇬"),
    "NGA": ("Nigéria", "Nigeria", "🇳🇬"),
    "GHA": ("Ghana", "Ghana", "🇬🇭"),
    "CIV": ("Côte d'Ivoire", "Côte d'Ivoire", "🇨🇮"),
    "SEN": ("Sénégal", "Senegal", "🇸🇳"),
    "CMR": ("Cameroun", "Cameroon", "🇨🇲"),
    "COD": ("RD Congo", "DR Congo", "🇨🇩"),
    "KEN": ("Kenya", "Kenya", "🇰🇪"),
    "ETH": ("Éthiopie", "Ethiopia", "🇪🇹"),
    "RWA": ("Rwanda", "Rwanda", "🇷🇼"),
    "ZAF": ("Afrique du Sud", "South Africa", "🇿🇦"),
    "AGO": ("Angola", "Angola", "🇦🇴"),
    "MOZ": ("Mozambique", "Mozambique", "🇲🇿"),
}

# Liste de rotation pour le "pays de la semaine" (ordre fixe, indexé par numéro de semaine ISO)
COUNTRY_OF_WEEK_ROTATION = list(COUNTRY_DISPLAY_NAMES.keys())


def region_from_country(country: str, text: str) -> str:
    """Région d'une source dédiée à un pays, avec repli sur la détection par mots-clés"""
    mapped = COUNTRY_REGION_MAP.get(country)
    if mapped:
        return mapped
    return detect_region(text)


def detect_content_tags(text: str) -> List[str]:
    """Détecter les signaux à forte valeur éditoriale (stats, opportunités, dev, événements)"""
    text_lower = text.lower()
    tags = []
    for tag, config in CONTENT_PRIORITY_KEYWORDS.items():
        for keyword in config["keywords"]:
            if keyword == "%":
                pattern = re.escape(keyword)
            else:
                pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text_lower):
                tags.append(tag)
                break
    return tags


def parse_date(date_str: str) -> datetime:
    """Parser différents formats de date"""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return datetime.now()


def generate_article_id(title: str, source: str) -> str:
    """Générer un ID unique pour l'article"""
    return hashlib.md5(f"{title}:{source}".encode()).hexdigest()[:12]


def truncate_text(text: str, max_length: int = 200) -> str:
    """Tronquer le texte avec ellipsis"""
    if not text:
        return ""
    # Décoder les entités HTML
    import html

    text = html.unescape(text)
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


async def fetch_feed(
    session: aiohttp.ClientSession,
    url: str,
    source_name: str,
    category: str,
    source_country: Optional[str] = None,
    source_priority: bool = False,
) -> List[Dict]:
    """Récupérer et parser un flux RSS"""
    articles = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=15), headers=headers
        ) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)

                for entry in feed.entries[:10]:  # Limiter à 10 articles par feed
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    link = entry.get("link", "")
                    pub_date = entry.get("published", entry.get("updated", ""))

                    # Nettoyer le résumé (enlever HTML et décoder entités)
                    import html

                    summary = re.sub(r"<[^>]+>", "", summary)
                    summary = html.unescape(summary)
                    summary = truncate_text(summary, 250)

                    # Nettoyer le titre aussi
                    title = html.unescape(title)

                    # Détecter région, catégorie et signaux éditoriaux prioritaires
                    full_text = f"{title} {summary}"
                    region = (
                        detect_region(full_text)
                        if not source_country
                        else region_from_country(source_country, full_text)
                    )
                    detected_category = detect_category(full_text, category)
                    content_tags = detect_content_tags(full_text)

                    articles.append(
                        {
                            "id": generate_article_id(title, source_name),
                            "title": title,
                            "summary": summary,
                            "link": link,
                            "source": source_name,
                            "category": detected_category,
                            "region": region,
                            "country": source_country,
                            "priority": source_priority,
                            "content_tags": content_tags,
                            "content_priority": len(content_tags) > 0,
                            "published_at": (
                                parse_date(pub_date).isoformat()
                                if pub_date
                                else datetime.now().isoformat()
                            ),
                            "fetched_at": datetime.now().isoformat(),
                        }
                    )
    except Exception as e:
        print(f"Erreur fetch {source_name}/{category}: {e}")

    return articles


async def fetch_all_news() -> List[Dict]:
    """Récupérer toutes les actualités de toutes les sources"""
    all_articles = []

    async with aiohttp.ClientSession() as session:
        tasks = []

        for source_key, source_config in RSS_FEEDS.items():
            for category, url in source_config["feeds"].items():
                tasks.append(
                    fetch_feed(
                        session,
                        url,
                        source_config["name"],
                        category,
                        source_config.get("country"),
                        source_config.get("priority", False),
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)

    # Ajouter les projets structurants algériens comme actualités
    for project in ALGERIA_STRUCTURAL_PROJECTS:
        all_articles.append(
            {
                "id": f"dz-project-{project['id']}",
                "title": f"🇩🇿 {project['title']}",
                "summary": f"[{project['status']}] {project['summary']} - Investissement: ${project['investment_musd']}M USD",
                "link": project["link"],
                "source": project["source"],
                "category": project["category"],
                "region": project["region"],
                "published_at": datetime.now().isoformat(),
                "fetched_at": datetime.now().isoformat(),
                "is_structural_project": True,
                "country": "DZA",
                "priority": True,
                "content_tags": ["development", "statistics"],
                "content_priority": True,
            }
        )

    # Dédupliquer par titre similaire
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        title_key = article["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)

    # Tri éditorial: projets structurants en tête, puis dépêches à forte valeur
    # (statistiques / opportunités / développement / événements), puis le reste,
    # chaque palier étant ordonné par date décroissante.
    def sort_tier(article):
        if article.get("priority", False):
            return 0
        if article.get("content_priority", False):
            return 1
        return 2

    # Tri stable en deux passes: d'abord par date décroissante, puis par palier
    # croissant — le tri stable préserve l'ordre par date à l'intérieur d'un palier.
    unique_articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    unique_articles.sort(key=sort_tier)

    return unique_articles[:100]  # Limiter à 100 articles


def balance_articles_by_country(articles: List[Dict], max_per_country: int = 2) -> List[Dict]:
    """Limiter le nombre de dépêches par pays dans le fil principal, afin de préserver
    l'équilibre éditorial (éviter qu'un pays fortement prioritaire comme l'Algérie ne
    domine le fil au détriment des autres) et de mettre en valeur les progrès et
    opportunités d'amélioration du climat des affaires à l'échelle du continent."""
    country_counts: Dict[str, int] = {}
    balanced = []
    for article in articles:
        country = article.get("country")
        if country:
            count = country_counts.get(country, 0)
            if count >= max_per_country:
                continue
            country_counts[country] = count + 1
        balanced.append(article)
    return balanced


def get_country_of_the_week(articles: List[Dict], week_number: Optional[int] = None) -> Dict:
    """Sélectionner le "pays de la semaine" (rotation hebdomadaire) et ses dépêches les
    plus marquantes, en mettant en avant points forts et perspectives (priorité aux
    dépêches taguées développement/opportunités/statistiques)."""
    if week_number is None:
        week_number = datetime.now().isocalendar()[1]

    country = COUNTRY_OF_WEEK_ROTATION[week_number % len(COUNTRY_OF_WEEK_ROTATION)]
    name_fr, name_en, flag = COUNTRY_DISPLAY_NAMES.get(country, (country, country, "🌍"))

    country_articles = [a for a in articles if a.get("country") == country]
    highlights = [a for a in country_articles if a.get("content_priority")]
    if not highlights:
        highlights = country_articles

    return {
        "country": country,
        "country_name_fr": name_fr,
        "country_name_en": name_en,
        "flag": flag,
        "week_number": week_number,
        "highlights": highlights[:5],
    }


def load_cache() -> Dict:
    """Charger le cache depuis le fichier"""
    global NEWS_CACHE
    try:
        if os.path.exists(NEWS_CACHE_FILE):
            with open(NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
                NEWS_CACHE = json.load(f)
    except Exception as e:
        print(f"Erreur chargement cache: {e}")
        NEWS_CACHE = {"last_update": None, "articles": []}
    return NEWS_CACHE


def save_cache(articles: List[Dict]):
    """Sauvegarder le cache dans un fichier"""
    global NEWS_CACHE
    NEWS_CACHE = {"last_update": datetime.now().isoformat(), "articles": articles}
    try:
        os.makedirs(os.path.dirname(NEWS_CACHE_FILE), exist_ok=True)
        with open(NEWS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(NEWS_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde cache: {e}")


def should_refresh_cache() -> bool:
    """Vérifier si le cache doit être rafraîchi (une fois par jour)"""
    cache = load_cache()
    if not cache.get("last_update"):
        return True

    last_update = datetime.fromisoformat(cache["last_update"])
    return datetime.now() - last_update > timedelta(hours=24)


async def get_news(force_refresh: bool = False) -> Dict:
    """Obtenir les actualités (depuis cache ou fetch)"""
    if force_refresh or should_refresh_cache():
        print("Rafraîchissement des actualités...")
        articles = await fetch_all_news()
        save_cache(articles)
        return {"last_update": datetime.now().isoformat(), "articles": articles, "source": "fresh"}
    else:
        cache = load_cache()
        return {
            "last_update": cache.get("last_update"),
            "articles": cache.get("articles", []),
            "source": "cache",
        }


def get_news_by_region(articles: List[Dict]) -> Dict[str, List[Dict]]:
    """Grouper les articles par région"""
    by_region = {}
    for article in articles:
        region = article.get("region", "Afrique")
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(article)
    return by_region


def get_news_by_category(articles: List[Dict]) -> Dict[str, List[Dict]]:
    """Grouper les articles par catégorie"""
    by_category = {}
    for article in articles:
        category = article.get("category", "Économie")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(article)
    return by_category


# Pour les tests synchrones
def get_news_sync(force_refresh: bool = False) -> Dict:
    """Version synchrone de get_news"""
    return asyncio.run(get_news(force_refresh))


if __name__ == "__main__":
    # Test
    import asyncio

    result = asyncio.run(get_news(force_refresh=True))
    print(f"Récupéré {len(result['articles'])} articles")
    for article in result["articles"][:5]:
        print(f"- [{article['region']}] [{article['category']}] {article['title'][:60]}...")
