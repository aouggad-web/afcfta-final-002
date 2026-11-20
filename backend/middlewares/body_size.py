import json
import os


class BodySizeLimitMiddleware:
    """Rejette toute requête dont le corps dépasse une borne, avant que la route
    ne le traite.

    Audit DoS (17/11/2026) : aucune limite n'existait. FastAPI bufferise le
    corps entier avant Pydantic, donc un corps de dizaines de Mo (ou une rafale
    de tels corps) épuisait la mémoire du worker unique — un POST anonyme de
    20 Mo passait en 1,4 s. Les plafonds par champ ne protègent pas, le corps
    étant déjà lu.

    Deux chemins :
    - **`Content-Length` déclaré, sans `Transfer-Encoding: chunked`** : refus 413
      immédiat au-delà de la borne, sans lire le corps (cas de tous les
      navigateurs et clients HTTP usuels). On ne fait confiance au cadrage par
      longueur que si aucun cadrage « chunked » ne le contredit : avec les deux
      en-têtes, le serveur HTTP décode en chunked (h11 donne priorité au
      Transfer-Encoding), et faire confiance au Content-Length laisserait passer
      un corps réel non borné (revue Codex 20/11/2026).
    - **sinon (chunked, ou sans `Content-Length`)** : le corps est compté et mis
      en tampon, borné, AVANT d'appeler la route ; au dépassement, 413 et la
      route n'est **jamais** invoquée (synthétiser un « fin de corps » tronqué
      ferait exécuter la route sur un préfixe valide — effet de bord ; revue
      Codex 18/11/2026).

    Après avoir rejoué le corps tamponné, on délègue au **vrai** `receive()` :
    les notifications de déconnexion doivent refléter l'état réel de la
    connexion, sinon un `http.disconnect` synthétique annulerait à tort une
    réponse en flux (téléchargement ZIP tronqué ; revue Codex 20/11/2026).

    Middleware ASGI pur. Défense en profondeur : le relais en frontal
    (Cloudflare) doit aussi plafonner la taille du corps.
    """

    def __init__(self, app, max_bytes: "int | None" = None):
        self.app = app
        if max_bytes is None:
            try:
                max_bytes = int(os.environ.get("MAX_REQUEST_BODY_BYTES", str(1024 * 1024)))
            except ValueError:
                max_bytes = 1024 * 1024
        self.max_bytes = max(1, max_bytes)

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        declaree = None
        chunked = False
        for nom, valeur in scope.get("headers") or []:
            cle = nom.lower()
            if cle == b"content-length":
                try:
                    declaree = int(valeur)
                except ValueError:
                    await self._refus(send)
                    return
            elif cle == b"transfer-encoding" and b"chunked" in valeur.lower():
                chunked = True

        if declaree is not None and not chunked:
            if declaree > self.max_bytes:
                await self._refus(send)
                return
            # Longueur déclarée, dans la borne, sans cadrage « chunked » qui la
            # contredise : le serveur ASGI borne le corps, on laisse passer en
            # flux sans tamponner.
            await self.app(scope, receive, send)
            return

        # Corps au cadrage non fiable (chunked, ou sans Content-Length) : on
        # compte les octets réels et on tamponne, borné, AVANT d'appeler la
        # route. Au dépassement, la route n'est pas invoquée — aucun effet de
        # bord.
        messages = []
        total = 0
        while True:
            message = await receive()
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    await self._refus(send)
                    return
                messages.append(message)
                if not message.get("more_body", False):
                    break
            else:
                # http.disconnect ou autre : on arrête de lire et on transmet.
                messages.append(message)
                break

        index = 0

        async def receive_tampon():
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            # Corps tamponné épuisé : déléguer au vrai receive, pour que les
            # vraies déconnexions parviennent à la route (une réponse en flux
            # écoute http.disconnect ; un disconnect synthétique l'annulerait).
            return await receive()

        await self.app(scope, receive_tampon, send)

    async def _refus(self, send):
        corps = json.dumps({"detail": "Request body too large."}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(corps)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": corps})
