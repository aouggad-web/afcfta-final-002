import logging
import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Chemins exemptés — comparaison EXACTE, jamais par préfixe.
#
# Un préfixe "/api/" exempterait toute l'application, puisque chaque route est
# montée sous ce préfixe : c'est le défaut qui neutralisait silencieusement ce
# middleware. La comparaison exacte évite que la liste se remette à tout couvrir.
DEFAULT_EXEMPT_PATHS = frozenset(
    {
        "/api/",  # index de l'API
        "/api/health",  # sondes de disponibilité (monitoring, orchestrateur)
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        # Webhooks de paiement : les prestataires livrent en rafale et rejouent
        # ce qui échoue. Un 429 ici ferait perdre des événements de paiement —
        # ils sont authentifiés par signature, pas par volume.
        "/api/billing/webhook",
        "/api/billing/chargily/webhook",
    }
)

# Endpoints où la force brute est le risque réel : quota par IP nettement plus
# serré. On ne vise que l'authentification proprement dite — /auth/me est appelé
# à chaque chargement de page par l'interface et doit rester sur le quota normal.
SENSITIVE_AUTH_PATHS = frozenset({"/api/auth/login", "/api/auth/register"})


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        logger.warning("%s invalide, valeur par défaut %s utilisée", name, default)
        return default


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int | None = None,
        burst_limit: int | None = None,
        exempt_paths: list | None = None,
        auth_requests_per_minute: int | None = None,
    ):
        super().__init__(app)
        # Réglages pilotables par l'environnement : si le quota s'avère trop
        # serré en production, on l'ajuste (ou on coupe) sans redéployer.
        self.enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.requests_per_minute = (
            requests_per_minute
            if requests_per_minute is not None
            else _env_int("RATE_LIMIT_PER_MINUTE", 120)
        )
        self.burst_limit = (
            burst_limit if burst_limit is not None else _env_int("RATE_LIMIT_BURST", 20)
        )
        self.auth_requests_per_minute = (
            auth_requests_per_minute
            if auth_requests_per_minute is not None
            else _env_int("RATE_LIMIT_AUTH_PER_MINUTE", 10)
        )
        self.exempt_paths = frozenset(exempt_paths) if exempt_paths else DEFAULT_EXEMPT_PATHS
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

        if not self.enabled:
            logger.warning("Rate limiting DÉSACTIVÉ (RATE_LIMIT_ENABLED=false)")
        else:
            logger.info(
                "Rate limiting actif : %s req/min, rafale %s, auth %s req/min",
                self.requests_per_minute,
                self.burst_limit,
                self.auth_requests_per_minute,
            )

    def _get_client_ip(self, request: Request) -> str:
        """Adresse servant de clé de compteur.

        Délègue à `geo_service.client_ip`, qui tient compte du nombre de relais
        en frontal (TRUSTED_PROXY_HOPS). Prendre naïvement la dernière entrée de
        X-Forwarded-For derrière plusieurs relais renverrait une adresse
        d'infrastructure identique pour tout le monde : l'ensemble des visiteurs
        partagerait alors un seul quota, et un utilisateur actif suffirait à
        bloquer tous les autres.
        """
        try:
            from services import geo_service

            resolved = geo_service.client_ip(request)
            if resolved:
                return resolved
        except Exception:  # pragma: no cover - le limiteur ne doit jamais casser
            logger.debug("Résolution d'IP déléguée indisponible, repli local", exc_info=True)

        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[-1].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _cleanup_old_entries(self, now: float):
        if now - self._last_cleanup < 60:
            return
        cutoff = now - 60
        keys_to_delete = []
        for key, timestamps in self._buckets.items():
            self._buckets[key] = [t for t in timestamps if t > cutoff]
            if not self._buckets[key]:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self._buckets[key]
        self._last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Comparaison exacte : un préfixe rendrait le middleware inopérant.
        if not self.enabled or path in self.exempt_paths:
            return await call_next(request)

        now = time.time()
        self._cleanup_old_entries(now)

        client_ip = self._get_client_ip(request)
        is_sensitive_auth = path in SENSITIVE_AUTH_PATHS
        limit = self.auth_requests_per_minute if is_sensitive_auth else self.requests_per_minute

        # Les endpoints d'authentification ont leur propre compteur : sinon un
        # quota partagé avec le reste de la section laisserait passer les
        # tentatives de connexion tant que le trafic normal reste faible.
        if is_sensitive_auth:
            bucket_key = f"{client_ip}:auth-sensitive"
        else:
            segments = path.split("/")
            bucket_key = f"{client_ip}:{segments[2] if len(segments) > 2 else 'root'}"

        self._buckets[bucket_key] = [t for t in self._buckets[bucket_key] if t > now - 60]

        if len(self._buckets[bucket_key]) >= limit:
            retry_after = int(60 - (now - self._buckets[bucket_key][0]))
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(max(1, retry_after))},
            )

        recent = [t for t in self._buckets[bucket_key] if t > now - 1]
        if len(recent) >= self.burst_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Request burst limit exceeded. Slow down."},
                headers={"Retry-After": "1"},
            )

        self._buckets[bucket_key].append(now)

        response = await call_next(request)
        remaining = limit - len(self._buckets[bucket_key])
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        return response
