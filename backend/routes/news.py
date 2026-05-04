"""
News routes - African economic news from various sources
"""
from fastapi import APIRouter, Query
from typing import Optional
import logging

from etl.news_aggregator import get_news, get_news_by_region, get_news_by_category, ALGERIA_STRUCTURAL_PROJECTS

router = APIRouter(prefix="/news")

@router.get("")
async def get_economic_news(
    force_refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
    region: Optional[str] = Query(None, description="Filtrer par région (ex: Afrique du Nord)"),
    category: Optional[str] = Query(None, description="Filtrer par catégorie (ex: Finance, Commerce)"),
    country: Optional[str] = Query(None, description="Filtrer par pays ISO3 (ex: DZA pour Algérie)")
):
    """
    Récupérer les actualités économiques africaines
    Sources: Agence Ecofin, AllAfrica, Google News
    PRIORITÉ: Algérie et projets structurants
    Mise à jour: Une fois par jour (ou force_refresh=true)
    """
    try:
        news_data = await get_news(force_refresh=force_refresh)
        articles = news_data.get("articles", [])
        
        # Filtrer par pays si spécifié
        if country:
            country_upper = country.upper()
            articles = [a for a in articles if (
                a.get("country") == country_upper or
                country.lower() in a.get("title", "").lower() or
                (country_upper == "DZA" and ("algérie" in a.get("title", "").lower() or "algeria" in a.get("title", "").lower()))
            )]
        
        # Filtrer par région si spécifié
        if region:
            articles = [a for a in articles if a.get("region", "").lower() == region.lower()]
        
        # Filtrer par catégorie si spécifié
        if category:
            articles = [a for a in articles if a.get("category", "").lower() == category.lower()]
        
        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            "source": news_data.get("source"),
            "total_articles": len(articles),
            "articles": articles,
            "filters_applied": {
                "region": region,
                "category": category,
                "country": country
            },
            "priority_country": "DZA"
        }
    except Exception as e:
        logging.error(f"Erreur récupération actualités: {e}")
        return {
            "success": False,
            "error": str(e),
            "articles": []
        }


@router.get("/algeria/projects")
async def get_algeria_structural_projects(
    status: Optional[str] = Query(None, description="Filtrer par statut (OPÉRATIONNEL, EN CONSTRUCTION, EN ÉTUDE)")
):
    """
    Récupérer les projets structurants algériens
    
    Projets majeurs en cours ou opérationnels:
    - Gara Djebilet (fer) - $6B
    - Phosphates Tébessa - $7B
    - Port El Hamdania - $3.3B
    - Complexe sidérurgique Bellara - $2B
    - Et plus...
    """
    projects = ALGERIA_STRUCTURAL_PROJECTS.copy()
    
    if status:
        projects = [p for p in projects if status.upper() in p["status"].upper()]
    
    # Stats
    total_investment = sum(p["investment_musd"] for p in projects)
    operational = len([p for p in projects if "OPÉRATIONNEL" in p["status"]])
    in_construction = len([p for p in projects if "CONSTRUCTION" in p["status"]])
    
    return {
        "success": True,
        "country": "DZA",
        "country_name": "Algérie",
        "total_projects": len(projects),
        "total_investment_musd": total_investment,
        "stats": {
            "operational": operational,
            "in_construction": in_construction,
            "in_study": len(projects) - operational - in_construction
        },
        "projects": projects
    }


@router.get("/by-region")
async def get_news_grouped_by_region(force_refresh: bool = Query(False)):
    """Récupérer les actualités groupées par région africaine"""
    try:
        news_data = await get_news(force_refresh=force_refresh)
        articles = news_data.get("articles", [])
        by_region = get_news_by_region(articles)
        region_counts = {region: len(arts) for region, arts in by_region.items()}
        
        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            "regions": list(by_region.keys()),
            "region_counts": region_counts,
            "articles_by_region": by_region
        }
    except Exception as e:
        logging.error(f"Erreur récupération news par région: {e}")
        return {"success": False, "error": str(e)}


@router.get("/by-category")
async def get_news_grouped_by_category(force_refresh: bool = Query(False)):
    """Récupérer les actualités groupées par catégorie économique"""
    try:
        news_data = await get_news(force_refresh=force_refresh)
        articles = news_data.get("articles", [])
        by_category = get_news_by_category(articles)
        category_counts = {cat: len(arts) for cat, arts in by_category.items()}
        
        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            "categories": list(by_category.keys()),
            "category_counts": category_counts,
            "articles_by_category": by_category
        }
    except Exception as e:
        logging.error(f"Erreur récupération news par catégorie: {e}")
        return {"success": False, "error": str(e)}
