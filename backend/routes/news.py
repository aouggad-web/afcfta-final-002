"""
News routes - African economic news from various sources
"""

import logging
from typing import List, Literal, Optional
from urllib.parse import urlparse

from auth import get_db
from bson import ObjectId
from bson.errors import InvalidId
from entitlement_guard import get_optional_subscriber
from etl.news_aggregator import (
    ALGERIA_STRUCTURAL_PROJECTS,
    balance_articles_by_country,
    detect_country_in_title,
    get_country_of_the_week,
    get_news,
    get_news_by_category,
    get_news_by_region,
)
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator
from services import news_images as images
from services import news_redaction as redaction

router = APIRouter(prefix="/news")


async def _articles_affiches(news_data: dict) -> tuple:
    """Validation préalable (décision du 07/11/2026) : avec une base, seuls les
    articles publiés par le rédacteur sont affichés ; sans base (développement,
    tests), le fil reste automatique. Rend (articles, mode)."""
    db = get_db()
    if db is None:
        return news_data.get("articles", []), "automatique"
    return await redaction.articles_publics(db), "redaction"


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
        articles, mode = await _articles_affiches(news_data)

        # Filtrer par pays si spécifié (tag source fiable + repli sur la détection du
        # nom du pays dans le titre, par mots entiers avec priorité à la correspondance
        # la plus longue pour éviter les faux positifs entre noms composés, ex:
        # « Niger »/« Nigeria », « Sudan »/« South Sudan », « Guinea »/« Guinea-Bissau »)
        if country:
            country_upper = country.upper()
            articles = [
                a
                for a in articles
                if (
                    a.get("country") == country_upper
                    or detect_country_in_title(a.get("title", "")) == country_upper
                )
            ]

        # Filtrer par région si spécifié
        if region:
            articles = [a for a in articles if a.get("region", "").lower() == region.lower()]

        # Filtrer par catégorie si spécifié
        if category:
            articles = [a for a in articles if a.get("category", "").lower() == category.lower()]

        # Équilibre éditorial: limiter le nombre de dépêches par pays pour éviter
        # qu'un seul pays ne domine le fil principal (sauf filtrage explicite par pays).
        # En mode rédaction, le rédacteur a choisi chaque article : rien n'est retiré.
        if not country and mode == "automatique":
            articles = balance_articles_by_country(articles)

        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            "source": news_data.get("source"),
            "total_articles": len(articles),
            "articles": articles,
            "filters_applied": {"region": region, "category": category, "country": country},
            "priority_country": "DZA",
            "mode": mode,
        }
    except Exception as e:
        logging.error(f"Erreur récupération actualités: {e}", exc_info=True)
        return {"success": False, "error": "Internal server error", "articles": []}


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
        articles, _ = await _articles_affiches(news_data)
        spotlight = get_country_of_the_week(articles)

        return {
            "success": True,
            "last_update": news_data.get("last_update"),
            **spotlight,
        }
    except Exception as e:
        logging.error(f"Erreur récupération pays de la semaine: {e}", exc_info=True)
        return {"success": False, "error": "Internal server error"}


@router.get("/by-region")
async def get_news_grouped_by_region(force_refresh: bool = Query(False)):
    """Récupérer les actualités groupées par région africaine"""
    try:
        news_data = await get_news(force_refresh=force_refresh)
        articles, _ = await _articles_affiches(news_data)
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
        logging.error(f"Erreur récupération news par région: {e}", exc_info=True)
        return {"success": False, "error": "Internal server error"}


@router.get("/by-category")
async def get_news_grouped_by_category(force_refresh: bool = Query(False)):
    """Récupérer les actualités groupées par catégorie économique"""
    try:
        news_data = await get_news(force_refresh=force_refresh)
        articles, _ = await _articles_affiches(news_data)
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
        logging.error(f"Erreur récupération news par catégorie: {e}", exc_info=True)
        return {"success": False, "error": "Internal server error"}


# ── Rédaction (rédacteur en chef) ────────────────────────────────────────────
# Réservée à la session du compte admin (rôle admin), jamais à une clé API.
# Les requêtes qui modifient passent par le middleware CSRF (cookie + en-tête).


async def require_redacteur(request: Request) -> dict:
    user = await get_optional_subscriber(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "redaction_reservee", "message": "Réservé au rédacteur en chef."},
        )
    if get_db() is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="no_db")
    return user


_IdArticle = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class _Corps(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Decision(_Corps):
    id: str = _IdArticle
    action: Literal["publier", "ecarter", "masquer", "retablir"]


class Epingle(_Corps):
    id: str = _IdArticle
    epingler: bool = True


class OrdreUne(_Corps):
    ids: List[str] = Field(max_length=100)


class Regle(_Corps):
    type: Literal["source", "mot"]
    valeur: str = Field(min_length=2, max_length=100)


class ArticleManuel(_Corps):
    title: str = Field(min_length=3, max_length=300)
    summary: str = Field(default="", max_length=1000)
    link: str = Field(min_length=8, max_length=2000)
    source: str = Field(min_length=2, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    image: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("link")
    @classmethod
    def _lien_web(cls, valeur: str) -> str:
        # Seuls http et https : jamais javascript:, data:… dans un href public.
        valeur = valeur.strip()
        morceaux = urlparse(valeur)
        if morceaux.scheme not in ("http", "https") or not morceaux.netloc:
            raise ValueError("lien http ou https attendu")
        return valeur

    @field_validator("title", "summary", "source")
    @classmethod
    def _sans_blancs(cls, valeur: str) -> str:
        return valeur.strip()


async def _collectes() -> list:
    return (await get_news()).get("articles", [])


def _introuvable():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article_introuvable")


@router.get("/redaction")
async def lire_redaction(redacteur: dict = Depends(require_redacteur)):
    return await redaction.etat_redaction(get_db(), await _collectes())


@router.post("/redaction/decision")
async def decider_article(
    corps: Decision, taches: BackgroundTasks, redacteur: dict = Depends(require_redacteur)
):
    if not await redaction.decider(get_db(), corps.id, corps.action, await _collectes(), redacteur):
        _introuvable()
    logging.info("Rédaction : %s %s par %s", corps.action, corps.id, redacteur.get("email"))
    if corps.action in ("publier", "retablir"):
        taches.add_task(illustrer_en_arriere_plan, [corps.id], redacteur)
    return {"ok": True}


@router.post("/redaction/publier-tout")
async def publier_toute_la_file(
    taches: BackgroundTasks, redacteur: dict = Depends(require_redacteur)
):
    ids = await redaction.publier_tout(get_db(), await _collectes(), redacteur)
    logging.info("Rédaction : %d articles publiés par %s", len(ids), redacteur.get("email"))
    taches.add_task(illustrer_en_arriere_plan, ids, redacteur)
    return {"ok": True, "publies": len(ids)}


@router.post("/redaction/epingle")
async def epingler_article(
    corps: Epingle, taches: BackgroundTasks, redacteur: dict = Depends(require_redacteur)
):
    db = get_db()
    if corps.epingler:
        fait = await redaction.epingler(db, corps.id, await _collectes(), redacteur)
    else:
        fait = await redaction.desepingler(db, corps.id)
    if not fait:
        _introuvable()
    if corps.epingler:
        taches.add_task(illustrer_en_arriere_plan, [corps.id], redacteur)
    return {"ok": True}


@router.post("/redaction/une")
async def ordonner_la_une(corps: OrdreUne, redacteur: dict = Depends(require_redacteur)):
    await redaction.ordonner_une(get_db(), corps.ids)
    return {"ok": True}


@router.post("/redaction/manuel")
async def ajouter_article_manuel(
    corps: ArticleManuel, redacteur: dict = Depends(require_redacteur)
):
    champs = corps.model_dump(exclude={"image"})
    article_id = await redaction.ajouter_manuel(get_db(), champs, redacteur)
    logging.info("Rédaction : article manuel %s par %s", article_id, redacteur.get("email"))
    reponse = {"ok": True, "id": article_id}
    if corps.image:
        try:
            image = await images.recuperer(lien_image=corps.image)
            await images.enregistrer(get_db(), article_id, image, redacteur)
        except images.ImageRefusee as e:
            reponse["image_refusee"] = str(e)
    return reponse


@router.post("/redaction/regles")
async def bloquer(corps: Regle, redacteur: dict = Depends(require_redacteur)):
    await redaction.ajouter_regle(get_db(), corps.type, corps.valeur, redacteur)
    return {"ok": True}


@router.delete("/redaction/regles/{regle_id}")
async def debloquer(regle_id: str, redacteur: dict = Depends(require_redacteur)):
    try:
        oid = ObjectId(regle_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regle_introuvable")
    if not await redaction.retirer_regle(get_db(), oid):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regle_introuvable")
    return {"ok": True}


class DemandeImage(_Corps):
    id: str = _IdArticle
    url: Optional[str] = Field(default=None, max_length=2000)


class RetraitImage(_Corps):
    id: str = _IdArticle


async def _lien_article(db, article_id: str) -> Optional[str]:
    doc = await db.news_redaction.find_one({"_id": article_id})
    if doc is not None:
        return (doc.get("article") or {}).get("link")
    article = next((a for a in await _collectes() if a.get("id") == article_id), None)
    return article.get("link") if article else None


@router.post("/redaction/image")
async def chercher_image(corps: DemandeImage, redacteur: dict = Depends(require_redacteur)):
    """Copie l'image d'aperçu de l'article (ou l'image donnée par le
    rédacteur) ; il la voit dans la file avant de publier."""
    db = get_db()
    lien = await _lien_article(db, corps.id)
    if lien is None:
        _introuvable()
    try:
        image = await images.recuperer(lien_article=lien, lien_image=corps.url)
    except images.ImageRefusee as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"error": "image_refusee", "message": str(e)},
        )
    await images.enregistrer(db, corps.id, image, redacteur)
    logging.info("Rédaction : image de %s copiée par %s", corps.id, redacteur.get("email"))
    return {"ok": True}


@router.post("/redaction/image/retirer")
async def retirer_image(corps: RetraitImage, redacteur: dict = Depends(require_redacteur)):
    await images.retirer(get_db(), corps.id)
    return {"ok": True}


@router.get("/images/{article_id}")
async def servir_image(
    request: Request,
    article_id: str = Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
):
    """Image d'un article publié ; le rédacteur voit aussi celles de la file."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    doc = await db.news_redaction.find_one({"_id": article_id})
    publie = doc is not None and doc.get("statut") == "publie"
    if not publie:
        user = await get_optional_subscriber(request)
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    image = await db.news_images.find_one({"_id": article_id})
    if image is None or image.get("type") not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Response(
        content=bytes(image["donnees"]),
        media_type=image["type"],
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
            "Cache-Control": "public, max-age=3600" if publie else "private, no-store",
        },
    )


async def illustrer_en_arriere_plan(ids: List[str], redacteur: dict) -> None:
    """Décision de l'exploitant (07/11/2026) : l'image d'aperçu est cherchée
    dès la publication, après la réponse, un article après l'autre ; le
    rédacteur la retire ou la remplace s'il ne la veut pas. Un article dont
    l'image est déjà réglée (présente ou retirée), non publié ou sans image
    trouvée est laissé tel quel ; l'écriture finale ne remplace jamais un choix
    fait par le rédacteur pendant le téléchargement."""
    db = get_db()
    if db is None:
        return
    for article_id in ids:
        if await db.news_images.find_one({"_id": article_id}) is not None:
            continue
        doc = await db.news_redaction.find_one({"_id": article_id})
        if doc is None or doc.get("statut") != "publie":
            continue
        try:
            image = await images.recuperer(lien_article=(doc.get("article") or {}).get("link"))
            await images.enregistrer_si_absente(db, article_id, image, redacteur)
        except images.ImageRefusee as e:
            logging.info("Rédaction : pas d'image pour %s (%s)", article_id, e)
        except Exception:
            logging.warning(
                "Rédaction : recherche d'image en échec pour %s", article_id, exc_info=True
            )


@router.post("/redaction/images-manquantes")
async def chercher_images_manquantes(
    taches: BackgroundTasks, redacteur: dict = Depends(require_redacteur)
):
    """Cherche, en arrière-plan, l'image des articles publiés qui n'en ont pas."""
    db = get_db()
    regles = await images.ids_decides(db)
    ids = [
        d["_id"]
        for d in await db.news_redaction.find({"statut": "publie"}).to_list(length=None)
        if d["_id"] not in regles
    ]
    taches.add_task(illustrer_en_arriere_plan, ids, redacteur)
    return {"ok": True, "recherches": len(ids)}
