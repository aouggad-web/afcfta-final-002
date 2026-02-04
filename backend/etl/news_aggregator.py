"""
Agrégateur d'actualités économiques africaines
Sources: Agence Ecofin, Reuters Africa, AllAfrica
Mise à jour: Une fois par jour
"""

import feedparser
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
import hashlib

# Configuration des flux RSS
RSS_FEEDS = {
    "allafrica_en": {
        "name": "AllAfrica",
        "feeds": {
            "business": "https://allafrica.com/tools/headlines/rdf/business/headlines.rdf",
            "trade": "https://allafrica.com/tools/headlines/rdf/trade/headlines.rdf",
            "banking": "https://allafrica.com/tools/headlines/rdf/banking/headlines.rdf",
        },
        "language": "en",
        "logo": "📰"
    },
    "allafrica_fr": {
        "name": "AllAfrica (FR)",
        "feeds": {
            "business": "https://fr.allafrica.com/tools/headlines/rdf/business/headlines.rdf",
        },
        "language": "fr",
        "logo": "📰"
    },
    "google_news_africa": {
        "name": "Google News (Reuters, AFP, etc.)",
        "feeds": {
            "business_en": "https://news.google.com/rss/search?q=africa+economy+business&hl=en",
            "economie_fr": "https://news.google.com/rss/search?q=afrique+%C3%A9conomie&hl=fr",
        },
        "language": "multi",
        "logo": "🌐"
    },
    # PRIORITÉ ALGÉRIE - Flux dédiés
    "google_news_algeria": {
        "name": "Algérie Économie",
        "feeds": {
            "economie_dz": "https://news.google.com/rss/search?q=alg%C3%A9rie+%C3%A9conomie+investissement&hl=fr",
            "industry_dz": "https://news.google.com/rss/search?q=algeria+industry+manufacturing&hl=en",
        },
        "language": "multi",
        "logo": "🇩🇿",
        "priority": True
    }
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
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
        "link": "https://www.aps.dz/economie"
    }
]

# Mapping des pays africains pour la détection de région - SAHARA OCCIDENTAL AJOUTÉ
REGION_KEYWORDS = {
    "Afrique du Nord": ["algérie", "algeria", "maroc", "morocco", "tunisie", "tunisia", "egypte", "egypt", "libye", "libya", "mauritanie", "mauritania", "sahara occidental", "western sahara", "rasd", "sahrawi"],
    "Afrique de l'Ouest": ["sénégal", "senegal", "côte d'ivoire", "ivory coast", "ghana", "nigeria", "mali", "burkina", "niger", "bénin", "benin", "togo", "guinée", "guinea", "liberia", "sierra leone", "gambie", "gambia", "cedeao", "ecowas", "uemoa"],
    "Afrique Centrale": ["cameroun", "cameroon", "gabon", "congo", "rdc", "drc", "tchad", "chad", "centrafrique", "car", "guinée équatoriale", "equatorial guinea", "cemac"],
    "Afrique de l'Est": ["kenya", "tanzanie", "tanzania", "ethiopie", "ethiopia", "ouganda", "uganda", "rwanda", "burundi", "somalie", "somalia", "djibouti", "erythrée", "eritrea", "soudan", "sudan", "eac"],
    "Afrique Australe": ["afrique du sud", "south africa", "angola", "mozambique", "zambie", "zambia", "zimbabwe", "botswana", "namibie", "namibia", "malawi", "madagascar", "maurice", "mauritius", "sadc"]
}

CATEGORY_KEYWORDS = {
    "Finance": ["banque", "bank", "finance", "fmi", "imf", "bourse", "stock", "investissement", "investment", "crédit", "credit", "monnaie", "currency", "dette", "debt"],
    "Commerce": ["commerce", "trade", "export", "import", "zlecaf", "afcfta", "douane", "customs", "tarif", "tariff"],
    "Énergie": ["énergie", "energy", "électricité", "electricity", "pétrole", "oil", "gaz", "gas", "solaire", "solar", "renouvelable", "renewable"],
    "Agriculture": ["agriculture", "agro", "céréales", "cereals", "cacao", "café", "coffee", "coton", "cotton", "élevage", "livestock"],
    "Mines": ["mines", "mining", "or", "gold", "fer", "iron", "diamant", "diamond", "phosphate", "cuivre", "copper"],
    "Télécoms": ["télécom", "telecom", "mobile", "internet", "numérique", "digital", "tech", "startup"],
    "Infrastructure": ["infrastructure", "port", "aéroport", "airport", "route", "road", "rail", "chemin de fer", "construction"]
}

# Cache des actualités
NEWS_CACHE_FILE = "/app/backend/data/news_cache.json"
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
        "gestion_publique": "Gouvernance"
    }
    
    if feed_category and feed_category.lower() in category_map:
        return category_map[feed_category.lower()]
    
    # Sinon, détecter par mots-clés
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    
    return "Économie"  # Défaut


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
    return text[:max_length].rsplit(' ', 1)[0] + "..."


async def fetch_feed(session: aiohttp.ClientSession, url: str, source_name: str, category: str) -> List[Dict]:
    """Récupérer et parser un flux RSS"""
    articles = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                
                for entry in feed.entries[:10]:  # Limiter à 10 articles par feed
                    title = entry.get('title', '')
                    summary = entry.get('summary', entry.get('description', ''))
                    link = entry.get('link', '')
                    pub_date = entry.get('published', entry.get('updated', ''))
                    
                    # Nettoyer le résumé (enlever HTML et décoder entités)
                    import re
                    import html
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = html.unescape(summary)
                    summary = truncate_text(summary, 250)
                    
                    # Nettoyer le titre aussi
                    title = html.unescape(title)
                    
                    # Détecter région et catégorie
                    full_text = f"{title} {summary}"
                    region = detect_region(full_text)
                    detected_category = detect_category(full_text, category)
                    
                    articles.append({
                        "id": generate_article_id(title, source_name),
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": source_name,
                        "category": detected_category,
                        "region": region,
                        "published_at": parse_date(pub_date).isoformat() if pub_date else datetime.now().isoformat(),
                        "fetched_at": datetime.now().isoformat()
                    })
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
                tasks.append(fetch_feed(
                    session, 
                    url, 
                    source_config["name"], 
                    category
                ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
    
    # Ajouter les projets structurants algériens comme actualités
    for project in ALGERIA_STRUCTURAL_PROJECTS:
        all_articles.append({
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
            "priority": True
        })
    
    # Dédupliquer par titre similaire
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        title_key = article["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    # Trier: Priorité Algérie d'abord, puis par date
    def sort_key(article):
        is_algeria = (
            "algérie" in article.get("title", "").lower() or
            "algeria" in article.get("title", "").lower() or
            article.get("country") == "DZA" or
            article.get("priority", False)
        )
        # Priority: Algeria first (0), then others (1), then by date
        priority = 0 if is_algeria else 1
        return (priority, article.get("published_at", ""))
    
    unique_articles.sort(key=sort_key, reverse=False)
    # Reverse the date part but keep Algeria priority
    unique_articles.sort(key=lambda x: (
        0 if ("algérie" in x.get("title", "").lower() or 
              "algeria" in x.get("title", "").lower() or 
              x.get("country") == "DZA" or 
              x.get("priority", False)) else 1,
        x.get("published_at", "")
    ), reverse=True)
    
    return unique_articles[:100]  # Limiter à 100 articles


def load_cache() -> Dict:
    """Charger le cache depuis le fichier"""
    global NEWS_CACHE
    try:
        if os.path.exists(NEWS_CACHE_FILE):
            with open(NEWS_CACHE_FILE, 'r', encoding='utf-8') as f:
                NEWS_CACHE = json.load(f)
    except Exception as e:
        print(f"Erreur chargement cache: {e}")
        NEWS_CACHE = {"last_update": None, "articles": []}
    return NEWS_CACHE


def save_cache(articles: List[Dict]):
    """Sauvegarder le cache dans un fichier"""
    global NEWS_CACHE
    NEWS_CACHE = {
        "last_update": datetime.now().isoformat(),
        "articles": articles
    }
    try:
        os.makedirs(os.path.dirname(NEWS_CACHE_FILE), exist_ok=True)
        with open(NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
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
        return {
            "last_update": datetime.now().isoformat(),
            "articles": articles,
            "source": "fresh"
        }
    else:
        cache = load_cache()
        return {
            "last_update": cache.get("last_update"),
            "articles": cache.get("articles", []),
            "source": "cache"
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
    for article in result['articles'][:5]:
        print(f"- [{article['region']}] [{article['category']}] {article['title'][:60]}...")
