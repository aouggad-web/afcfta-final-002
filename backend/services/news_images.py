"""Illustrations des actualités : copie, sur notre serveur, de l'image
d'aperçu de l'article d'origine (décision de l'exploitant du 07/11/2026).

Le téléchargement n'a lieu qu'à la demande du rédacteur en chef (compte
admin), depuis la file de rédaction. C'est le seul appel sortant vers un hôte
variable : il est borné contre la falsification de requête côté serveur (SSRF) :
- http ou https seulement, ports 80 et 443 ;
- chaque adresse résolue doit être publique (`is_global`), y compris après une
  redirection (3 au plus) : le résolveur d'aiohttp refuse les autres, et la
  connexion part vers l'adresse vérifiée, sans seconde résolution ;
- 10 s au total, 1 Mo au plus pour la page comme pour l'image ;
- l'image n'est gardée que si ses premiers octets sont ceux d'un JPEG, d'un
  PNG ou d'un WebP (jamais de SVG, qui peut porter du script).

Les visiteurs ne contactent aucun site tiers : l'image est servie par notre
API, et seulement pour un article publié.
"""

import html
import ipaddress
import re
import socket
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp.abc import AbstractResolver
from aiohttp.resolver import DefaultResolver

TAILLE_MAX = 1024 * 1024
DELAI_S = 10
REDIRECTIONS_MAX = 3
_PORTS = {None, 80, 443}
_AGENT = "Mozilla/5.0 (compatible; AfCFTA-Intelligence/1.0; +illustrations)"


class ImageRefusee(Exception):
    """Lien, hôte, taille ou format refusé : message affichable au rédacteur."""


def _adresse_publique(adresse: str) -> bool:
    try:
        return ipaddress.ip_address(adresse).is_global
    except ValueError:
        return False


class _ResolveurPublic(AbstractResolver):
    """Ne rend que des adresses publiques ; aucune → refus de connexion."""

    def __init__(self):
        self._defaut = DefaultResolver()

    async def resolve(self, host, port=0, family=socket.AF_UNSPEC):
        resultats = await self._defaut.resolve(host, port, family)
        publics = [r for r in resultats if _adresse_publique(r["host"])]
        if not publics or len(publics) != len(resultats):
            raise OSError(f"hôte non public refusé : {host}")
        return publics

    async def close(self):
        await self._defaut.close()


def verifier_lien(url: str) -> str:
    """Contrôle de forme, avant toute connexion."""
    morceaux = urlparse((url or "").strip())
    if morceaux.scheme not in ("http", "https") or not morceaux.hostname:
        raise ImageRefusee("lien http ou https attendu")
    try:
        port = morceaux.port
    except ValueError:
        raise ImageRefusee("port invalide")
    if port not in _PORTS:
        raise ImageRefusee("seuls les ports 80 et 443 sont autorisés")
    try:
        if not ipaddress.ip_address(morceaux.hostname).is_global:
            raise ImageRefusee("adresse non publique refusée")
    except ValueError:
        pass  # nom d'hôte : vérifié par le résolveur à la connexion
    return morceaux.geturl()


async def _lire(session, url: str) -> Tuple[bytes, str, str]:
    """GET borné, redirections suivies une à une (chacune revérifiée)."""
    for _ in range(REDIRECTIONS_MAX + 1):
        url = verifier_lien(url)
        async with session.get(url, allow_redirects=False) as reponse:
            if reponse.status in (301, 302, 303, 307, 308):
                cible = reponse.headers.get("Location")
                if not cible:
                    raise ImageRefusee("redirection sans destination")
                url = urljoin(url, cible)
                continue
            if reponse.status != 200:
                raise ImageRefusee(f"réponse {reponse.status}")
            corps = bytearray()
            async for morceau in reponse.content.iter_chunked(65536):
                corps.extend(morceau)
                if len(corps) > TAILLE_MAX:
                    raise ImageRefusee("plus de 1 Mo")
            return bytes(corps), reponse.headers.get("Content-Type", ""), str(reponse.url)
    raise ImageRefusee("trop de redirections")


def _session():
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(resolver=_ResolveurPublic(), limit=2),
        timeout=aiohttp.ClientTimeout(total=DELAI_S),
        headers={"User-Agent": _AGENT},
        trust_env=False,
    )


_META = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_ATTR = re.compile(r"""([a-zA-Z:_-]+)\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""")
_CLES_IMAGE = ("og:image:secure_url", "og:image", "og:image:url", "twitter:image")


def image_dans_la_page(page: str, url_page: str) -> Optional[str]:
    """L'image d'aperçu déclarée par la page (Open Graph, puis Twitter)."""
    trouvees = {}
    for balise in _META.findall(page):
        attributs = {
            nom.lower(): html.unescape(valeur.strip("\"'")) for nom, valeur in _ATTR.findall(balise)
        }
        cle = (attributs.get("property") or attributs.get("name") or "").lower()
        if cle in _CLES_IMAGE and attributs.get("content") and cle not in trouvees:
            trouvees[cle] = attributs["content"].strip()
    for cle in _CLES_IMAGE:
        if cle in trouvees:
            lien = urljoin(url_page, trouvees[cle])
            if urlparse(lien).scheme in ("http", "https"):
                return lien
    return None


def type_image(donnees: bytes) -> Optional[str]:
    if donnees.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if donnees.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(donnees) >= 12 and donnees[:4] == b"RIFF" and donnees[8:12] == b"WEBP":
        return "image/webp"
    return None


async def recuperer(lien_article: Optional[str] = None, lien_image: Optional[str] = None) -> Dict:
    """Télécharge l'image : celle donnée par le rédacteur, sinon l'image
    d'aperçu de la page de l'article. Lève ImageRefusee."""
    try:
        async with _session() as session:
            if not lien_image:
                page, _, url_finale = await _lire(session, lien_article or "")
                lien_image = image_dans_la_page(page.decode("utf-8", "replace"), url_finale)
                if not lien_image:
                    raise ImageRefusee("aucune image d'aperçu dans la page")
            donnees, _, _ = await _lire(session, lien_image)
    except ImageRefusee:
        raise
    except (aiohttp.ClientError, OSError, TimeoutError) as e:
        raise ImageRefusee(f"site injoignable ({type(e).__name__})")
    mime = type_image(donnees)
    if mime is None:
        raise ImageRefusee("format refusé (JPEG, PNG ou WebP seulement)")
    return {"type": mime, "donnees": donnees, "origine": lien_image}


async def enregistrer(db, article_id: str, image: Dict, redacteur: Dict) -> None:
    await db.news_images.update_one(
        {"_id": article_id},
        {
            "$set": {
                **image,
                "recupere_le": datetime.now(timezone.utc),
                "recupere_par": redacteur.get("email") or "",
            }
        },
        upsert=True,
    )


async def retirer(db, article_id: str) -> None:
    await db.news_images.delete_one({"_id": article_id})


async def ids_illustres(db) -> set:
    docs = await db.news_images.find({}, {"_id": 1}).to_list(length=None)
    return {d["_id"] for d in docs}
