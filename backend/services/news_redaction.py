"""Rédaction des actualités : validation préalable par le rédacteur en chef.

Décision de l'exploitant (07/11/2026) : aucune dépêche collectée n'est
affichée sans son accord. La collecte automatique (etl/news_aggregator.py)
remplit une file « à valider » ; le compte admin, connecté, publie, écarte,
masque, épingle à la une (7 jours) ou ajoute un article à la main, et peut
bloquer une source ou un mot.

Les décisions vivent dans MongoDB, pas dans backend/data/news_cache.json
que chaque synchronisation efface :
- `news_redaction` : un document par article décidé (`_id` = id de l'article),
  avec une copie de l'article, pour qu'il reste affiché même sorti de la
  collecte du jour ;
- `news_regles` : les sources et mots bloqués.

Sans base (développement, tests), le fil reste automatique, comme avant.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

DUREE_EPINGLE = timedelta(days=7)
MAX_PUBLIES = 100

STATUTS = ("publie", "ecarte", "masque")


def _maintenant() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Mongo rend des dates naïves (UTC) : les rendre comparables."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _epingle_active(doc: Dict, maintenant: datetime) -> bool:
    fin = _aware(doc.get("epingle_jusqua"))
    return fin is not None and fin > maintenant


def _correspond(regle: Dict, article: Dict) -> bool:
    valeur = (regle.get("valeur") or "").strip().lower()
    if not valeur:
        return False
    if regle.get("type") == "source":
        return (article.get("source") or "").strip().lower() == valeur
    texte = f"{article.get('title') or ''} {article.get('summary') or ''}"
    return re.search(rf"(?<!\w){re.escape(valeur)}(?!\w)", texte, re.IGNORECASE) is not None


def bloque(regles: List[Dict], article: Dict) -> bool:
    """Un article ajouté à la main n'est jamais bloqué : le rédacteur l'a choisi."""
    if article.get("manuel"):
        return False
    return any(_correspond(r, article) for r in regles)


async def _regles(db) -> List[Dict]:
    return await db.news_regles.find({}).to_list(length=None)


async def _decisions(db, filtre: Optional[Dict] = None) -> List[Dict]:
    return await db.news_redaction.find(filtre or {}).to_list(length=None)


async def _illustres(db) -> set:
    from services.news_images import ids_illustres

    return await ids_illustres(db)


def _illustrer(article: Dict, illustres: set) -> Dict:
    article["has_image"] = article.get("id") in illustres
    return article


def _vue(doc: Dict, maintenant: datetime) -> Dict:
    """Article tel qu'affiché : la copie, plus l'état d'épingle."""
    article = dict(doc.get("article") or {})
    article["id"] = doc["_id"]
    epingle = _epingle_active(doc, maintenant)
    article["pinned"] = epingle
    if epingle:
        article["pinned_until"] = _aware(doc["epingle_jusqua"]).isoformat()
        article["pin_order"] = doc.get("ordre_une", 0)
    return article


def _ordre_public(articles: List[Dict]) -> List[Dict]:
    """Épinglés d'abord (dans l'ordre choisi), puis les autres par date."""
    articles = sorted(articles, key=lambda a: a.get("published_at") or "", reverse=True)
    return sorted(articles, key=lambda a: (0, a.get("pin_order", 0)) if a["pinned"] else (1, 0))


async def articles_publics(db) -> List[Dict]:
    """Le fil affiché aux visiteurs : les articles publiés, hors règles de blocage."""
    maintenant = _maintenant()
    regles = await _regles(db)
    illustres = await _illustres(db)
    publies = [
        _illustrer(_vue(d, maintenant), illustres)
        for d in await _decisions(db, {"statut": "publie"})
        if not bloque(regles, d.get("article") or {})
    ]
    return _ordre_public(publies)[:MAX_PUBLIES]


async def etat_redaction(db, collectes: List[Dict]) -> Dict:
    """Tout ce que voit le rédacteur : file à valider, publiés, masqués,
    écartés et règles. La file reprend les articles de la dernière collecte
    qui n'ont encore aucune décision et qu'aucune règle ne bloque."""
    maintenant = _maintenant()
    regles = await _regles(db)
    decisions = await _decisions(db)
    decides = {d["_id"] for d in decisions}
    illustres = await _illustres(db)
    # Un article écarté puis rétabli garde sa copie (statut « a_valider ») :
    # il revient dans la file même s'il a quitté la collecte du jour.
    a_valider = [
        _illustrer(_vue(d, maintenant), illustres)
        for d in decisions
        if d.get("statut") == "a_valider" and not bloque(regles, d.get("article") or {})
    ] + [
        _illustrer(dict(a), illustres)
        for a in collectes
        if a.get("id") not in decides and not bloque(regles, a)
    ]
    par_statut = {s: [] for s in STATUTS}
    for d in decisions:
        if d.get("statut") in par_statut:
            vue = _vue(d, maintenant)
            vue["bloque"] = bloque(regles, d.get("article") or {})
            vue["manuel"] = bool((d.get("article") or {}).get("manuel"))
            _illustrer(vue, illustres)
            par_statut[d["statut"]].append(vue)
    return {
        "a_valider": a_valider,
        "publies": _ordre_public(par_statut["publie"]),
        "masques": par_statut["masque"],
        "ecartes": par_statut["ecarte"],
        "regles": [
            {"id": str(r["_id"]), "type": r.get("type"), "valeur": r.get("valeur")} for r in regles
        ],
    }


def _trace(redacteur: Dict) -> Dict:
    return {"decide_le": _maintenant(), "decide_par": redacteur.get("email") or ""}


async def decider(db, article_id: str, action: str, collectes: List[Dict], redacteur: Dict):
    """publier / ecarter (file) ; masquer (publié) ; retablir (masqué → publié,
    écarté → file). Rend False si l'article est introuvable."""
    doc = await db.news_redaction.find_one({"_id": article_id})
    if action == "retablir":
        if doc is None:
            return False
        if doc.get("statut") == "ecarte":
            await db.news_redaction.update_one(
                {"_id": article_id}, {"$set": {"statut": "a_valider", **_trace(redacteur)}}
            )
        else:
            await db.news_redaction.update_one(
                {"_id": article_id}, {"$set": {"statut": "publie", **_trace(redacteur)}}
            )
        return True
    statut = {"publier": "publie", "ecarter": "ecarte", "masquer": "masque"}[action]
    if doc is None:
        article = next((a for a in collectes if a.get("id") == article_id), None)
        if article is None:
            return False
        copie = {k: v for k, v in article.items() if k != "id"}
        await db.news_redaction.update_one(
            {"_id": article_id},
            {"$set": {"statut": statut, "article": copie, **_trace(redacteur)}},
            upsert=True,
        )
        return True
    maj = {"statut": statut, **_trace(redacteur)}
    unset = {}
    if statut != "publie":
        unset = {"epingle_jusqua": "", "ordre_une": ""}
    await db.news_redaction.update_one(
        {"_id": article_id}, {"$set": maj, **({"$unset": unset} if unset else {})}
    )
    return True


async def publier_tout(db, collectes: List[Dict], redacteur: Dict) -> int:
    """Publie d'un coup toute la file à valider (utile au premier jour)."""
    file = (await etat_redaction(db, collectes))["a_valider"]
    for article in file:
        await decider(db, article["id"], "publier", collectes, redacteur)
    return len(file)


async def epingler(db, article_id: str, collectes: List[Dict], redacteur: Dict) -> bool:
    """Épingle à la une pour 7 jours, en dernière position ; publie l'article
    s'il ne l'était pas."""
    doc = await db.news_redaction.find_one({"_id": article_id})
    if doc is None or doc.get("statut") != "publie":
        if not await decider(db, article_id, "publier", collectes, redacteur):
            return False
    maintenant = _maintenant()
    ordres = [
        d.get("ordre_une", 0)
        for d in await _decisions(db)
        if d.get("statut") == "publie" and _epingle_active(d, maintenant) and d["_id"] != article_id
    ]
    await db.news_redaction.update_one(
        {"_id": article_id},
        {
            "$set": {
                "epingle_jusqua": maintenant + DUREE_EPINGLE,
                "ordre_une": max(ordres, default=-1) + 1,
                **_trace(redacteur),
            }
        },
    )
    return True


async def desepingler(db, article_id: str) -> bool:
    doc = await db.news_redaction.find_one({"_id": article_id})
    if doc is None:
        return False
    await db.news_redaction.update_one(
        {"_id": article_id}, {"$unset": {"epingle_jusqua": "", "ordre_une": ""}}
    )
    return True


async def ordonner_une(db, ids: List[str]) -> None:
    """Fixe l'ordre des articles épinglés (les ids absents gardent le leur)."""
    for rang, article_id in enumerate(ids):
        await db.news_redaction.update_one(
            {"_id": article_id, "epingle_jusqua": {"$exists": True}},
            {"$set": {"ordre_une": rang}},
        )


async def ajouter_manuel(db, champs: Dict, redacteur: Dict) -> str:
    """Publie un article écrit à la main ; `champs` est déjà validé par la route."""
    from etl.news_aggregator import (
        detect_category,
        detect_content_tags,
        detect_country_in_title,
        detect_region,
        region_from_country,
    )

    texte = f"{champs['title']} {champs.get('summary') or ''}"
    pays = champs.get("country") or detect_country_in_title(champs["title"])
    maintenant = _maintenant()
    article = {
        "title": champs["title"],
        "summary": champs.get("summary") or "",
        "link": champs["link"],
        "source": champs["source"],
        "category": champs.get("category") or detect_category(texte),
        "region": region_from_country(pays, texte) if pays else detect_region(texte),
        "country": pays,
        "priority": False,
        "content_tags": detect_content_tags(texte),
        "content_priority": False,
        "published_at": maintenant.replace(tzinfo=None).isoformat(),
        "fetched_at": maintenant.replace(tzinfo=None).isoformat(),
        "manuel": True,
    }
    article_id = f"m{uuid.uuid4().hex[:11]}"
    await db.news_redaction.insert_one(
        {"_id": article_id, "statut": "publie", "article": article, **_trace(redacteur)}
    )
    return article_id


async def ajouter_regle(db, type_regle: str, valeur: str, redacteur: Dict) -> None:
    valeur = valeur.strip()
    if await db.news_regles.find_one({"type": type_regle, "valeur": valeur}):
        return
    await db.news_regles.insert_one(
        {
            "type": type_regle,
            "valeur": valeur,
            "cree_le": _maintenant(),
            "cree_par": redacteur.get("email") or "",
        }
    )


async def retirer_regle(db, regle_id) -> bool:
    resultat = await db.news_regles.delete_one({"_id": regle_id})
    return bool(getattr(resultat, "deleted_count", 0))
