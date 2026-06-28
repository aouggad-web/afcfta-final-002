"""
News routes - African economic news from various sources
"""

import logging
from typing import Optional

from etl.news_aggregator import (
    ALGERIA_STRUCTURAL_PROJECTS,
    COUNTRY_NAME_KEYWORDS,
    balance_articles_by_country,
    get_country_of_the_week,
    get_news,
    get_news_by_category,
    get_news_by_region,
)
from fastapi import APIRouter, Query

router = APIRouter(prefix="/news")


@router.get("")
async def get_economic_news(
    force_refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
    region: Optional[str] = Query(None, description="Filtrer par région (ex: Afrique du Nord)"),
    category: Optional[str] = Query(
        None, description="Filtrer par catégorie (ex: Finance, Commerce)"
    ),
    country: Optional[str] = Query(
        None, description="Filtrer par pays ISO3 (ex: DZA pour Algérie)"
    ),
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

        # Filtrer par pays si spécifié (tag source fiable + repli sur le nom du pays dans le titre)
        if country:
            country_upper = country.upper()
            name_keywords = COUNTRY_NAME_KEYWORDS.get(country_upper, [])
            articles = [
                a
                for a in articles
                if (
                    a.get("country") == country_upper
                    or any(kw in a.get("title", "").lower() for kw in name_keywords)
                )
            ]

        # Filtrer par région si spécifié
        if region:
            articles = [a for a in articles if a.get("region", "").lower() == region.lower()]

        # Filtrer par catégorie si spécifié
        if category:
            articles = [a for a in articles if a.get("category", "").lower() == category.lower()]

        # Équilibre éditorial: limiter le nombre de dépêches par pays pour éviter
        # qu'un seul pays ne domine le fil principal (sauf filtrage explicite par pays)
        if not country:
            articles = balance_articles_by_country(articles)

        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            "source": news_data.get("source"),
            "total_articles": len(articles),
            "articles": articles,
            "filters_applied": {"region": region, "category": category, "country": country},
            "priority_country": "DZA",
        }
    except Exception as e:
        logging.error(f"Erreur récupération actualités: {e}")
        return {"success": False, "error": str(e), "articles": []}


@router.get("/algeria/projects")
async def get_algeria_structural_projects(
    status: Optional[str] = Query(
        None, description="Filtrer par statut (OPÉRATIONNEL, EN CONSTRUCTION, EN ÉTUDE)"
    )
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
            "in_study": len(projects) - operational - in_construction,
        },
        "projects": projects,
    }


@router.get("/country-of-the-week")
async def get_country_of_the_week_route(force_refresh: bool = Query(False)):
    """
    Récupérer le "pays de la semaine" mis en avant dans le dashboard

    Rotation hebdomadaire (basée sur le numéro de semaine ISO) parmi les pays
    disposant d'une source dédiée. Met en avant les dépêches à forte valeur
    éditoriale (statistiques, opportunités, développement) pour ce pays,
    afin de faire ressortir ses points forts et ses perspectives.
    """
    try:
        news_data = await get_news(force_refresh=force_refresh)
        articles = news_data.get("articles", [])
        spotlight = get_country_of_the_week(articles)

        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            **spotlight,
        }
    except Exception as e:
        logging.error(f"Erreur récupération pays de la semaine: {e}")
        return {"success": False, "error": str(e)}


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
            "articles_by_region": by_region,
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
            "articles_by_category": by_category,
        }
    except Exception as e:
        logging.error(f"Erreur récupération news par catégorie: {e}")
        return {"success": False, "error": str(e)}
