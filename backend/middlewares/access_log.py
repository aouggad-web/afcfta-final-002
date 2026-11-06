"""Une ligne de journal par requête, sans donnée personnelle (point 17 de l'audit).

Remplace la ligne d'accès d'uvicorn, coupée dans log_redaction.py parce
qu'elle écrivait l'adresse IP et la query string en clair. Exemple :

    2026-11-06T11:03:51.090Z [INFO] middlewares.access_log rid=fe22323554f8ea98:
    m=GET p=/api/consultation/{iso3}/sous-positions/{hs6} s=200 ms=41 b=1239

- ``p`` est le gabarit de la route quand la requête atteint le routeur. Pour
  une requête refusée avant (403 CSRF, 429, preflight CORS) ou sans route
  (404, repli de l'application React), c'est le chemin demandé, masqué puis
  encodé et tronqué à 200 caractères : on voit ainsi les balayages ;
- ni adresse IP, ni query string, ni en-tête, ni corps, ni identité ;
- ``ms`` s'arrête au dernier octet de la réponse : une tâche de fond lancée
  ensuite (envoi d'e-mail) n'est pas comptée ;
- ``b`` compte les octets émis sous ce middleware : la page 500 d'une
  exception, écrite plus haut par Starlette, n'y figure pas ;
- ``err`` nomme la classe d'une exception, levée avant ou après la réponse
  (tâche de fond, flux interrompu, requête annulée) ; la ligne passe alors en
  WARNING ;
- ``rid`` est repris par toutes les lignes écrites pendant la requête,
  trace d'une erreur 500 comprise ;
- /api/health n'est écrite qu'en erreur : chaque page l'appelle pour son
  jeton CSRF.

ASGI pur, et ajouté en dernier dans server.py : il voit les réponses des
autres middlewares (429 du limiteur, 403 CSRF, refus CORS) comme celles des
routes.
"""

import logging
import secrets
import time
from urllib.parse import quote

from log_redaction import redact, request_id

logger = logging.getLogger(__name__)

# Route attrape-tout de server.py : son gabarit ne dirait rien du chemin demandé.
_SANS_GABARIT = {"/{full_path:path}"}
_SANTE = "/api/health"


def _chemin(scope) -> str:
    # Gabarit complet, préfixe des routeurs inclus compris : FastAPI le range
    # dans son contexte de route effective ; route.path n'en garde que la fin.
    # Les versions antérieures de FastAPI n'ont que route.path, déjà complet.
    contexte = (scope.get("fastapi") or {}).get("effective_route_context")
    gabarit = getattr(contexte, "path", None) or getattr(scope.get("route"), "path", None)
    if gabarit and gabarit not in _SANS_GABARIT:
        return gabarit
    # Masqué avant d'être coupé : une coupe au milieu d'une adresse e-mail
    # l'empêcherait d'être reconnue.
    return quote(redact(scope.get("path", "")), safe="/@*")[:200]


class AccessLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id.set(secrets.token_hex(8))
        debut = time.perf_counter()
        # 500 tant qu'aucune réponse n'est partie : c'est ce que le client
        # recevra si l'application lève une exception.
        etat = {"statut": 500, "octets": 0, "fin": None}

        async def envoyer(message):
            if message["type"] == "http.response.start":
                etat["statut"] = message["status"]
            elif message["type"] == "http.response.body":
                etat["octets"] += len(message.get("body", b""))
                if not message.get("more_body", False):
                    etat["fin"] = time.perf_counter()
            await send(message)

        erreur = None
        try:
            await self.app(scope, receive, envoyer)
        except BaseException as exc:  # CancelledError compris : requête annulée
            erreur = type(exc).__name__
            raise
        finally:
            statut = etat["statut"]
            if erreur or not (scope.get("path") == _SANTE and statut < 400):
                fin = etat["fin"] or time.perf_counter()
                duree = int((fin - debut) * 1000)
                ligne = "m=%s p=%s s=%d ms=%d b=%d"
                args = [scope.get("method", "-"), _chemin(scope), statut, duree, etat["octets"]]
                if erreur:
                    ligne += " err=%s"
                    args.append(erreur)
                grave = statut >= 500 or erreur
                logger.log(logging.WARNING if grave else logging.INFO, ligne, *args)
