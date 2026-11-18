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
    - **`Content-Length` déclaré** : refus 413 immédiat au-delà de la borne,
      sans lire le corps (cas de tous les navigateurs et clients HTTP usuels).
    - **sans `Content-Length` (corps « chunked »)** : le corps est mis en
      tampon, borné, AVANT d'appeler la route ; au dépassement, 413 et la route
      n'est **jamais** invoquée. Revue Codex (18/11/2026) : synthétiser un
      « fin de corps » tronqué faisait exécuter la route sur un préfixe valide
      (effet de bord, p. ex. insertion d'un message), le 413 ne remplaçant que
      la réponse après coup.

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
        for nom, valeur in scope.get("headers") or []:
            if nom == b"content-length":
                try:
                    declaree = int(valeur)
                except ValueError:
                    await self._refus(send)
                    return
                break

        if declaree is not None:
            if declaree > self.max_bytes:
                await self._refus(send)
                return
            # Longueur déclarée et dans la borne : le serveur ASGI borne le corps
            # à cette longueur, on laisse passer en flux sans tamponner.
            await self.app(scope, receive, send)
            return

        # Sans Content-Length : tamponner le corps, borné, AVANT d'appeler la
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
            return {"type": "http.disconnect"}

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
