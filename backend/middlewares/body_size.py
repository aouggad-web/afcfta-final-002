import json
import os


class BodySizeLimitMiddleware:
    """Rejette toute requête dont le corps dépasse une borne, avant que la route
    ne le lise.

    Audit DoS (17/11/2026) : aucune limite n'existait. FastAPI bufferise le
    corps entier avant Pydantic, donc un corps de dizaines de Mo (ou une rafale
    de tels corps) épuisait la mémoire du worker unique — un POST anonyme de
    20 Mo passait en 1,4 s. Les plafonds par champ ne protègent pas, le corps
    étant déjà lu.

    Deux contrôles : le `Content-Length` déclaré (cas de tous les navigateurs et
    clients HTTP usuels), refusé sans lire le corps ; et le volume réellement
    reçu, pour qu'un envoi « chunked » sans `Content-Length` ne contourne pas la
    borne. Middleware ASGI pur, pour refermer le flux et répondre 413 avant la
    route. Défense en profondeur : le relais en frontal (Cloudflare) doit aussi
    plafonner la taille du corps.
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

        for nom, valeur in scope.get("headers") or []:
            if nom == b"content-length":
                try:
                    declaree = int(valeur)
                except ValueError:
                    await self._refus(send)
                    return
                if declaree > self.max_bytes:
                    await self._refus(send)
                    return
                break

        recu = 0
        depasse = False

        async def receive_borne():
            nonlocal recu, depasse
            if depasse:
                # Le corps a déjà dépassé : ne plus rien livrer à la route.
                return {"type": "http.request", "body": b"", "more_body": False}
            message = await receive()
            if message.get("type") == "http.request":
                recu += len(message.get("body", b""))
                if recu > self.max_bytes:
                    depasse = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        debut_envoye = False

        async def send_borne(message):
            nonlocal debut_envoye
            # Dépassement détecté en cours de lecture : on remplace la réponse de
            # la route par un 413, tant que rien n'est encore parti.
            if depasse and not debut_envoye:
                if message.get("type") == "http.response.start":
                    await self._refus(send)
                    debut_envoye = True
                return
            if depasse and debut_envoye and message.get("type") == "http.response.body":
                return
            await send(message)

        await self.app(scope, receive_borne, send_borne)

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
