import logging
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_HTTPS = os.environ.get("HTTPS_ENABLED", "false").lower() == "true"

logger = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_HEADER = "X-CSRF-Token"
CSRF_COOKIE = "csrf_token"


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_paths: list | None = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/api/docs",
            "/api/openapi.json",
            "/api/redoc",
            "/api/health",
            "/api/calculate-tariff",
            "/api/tariff-data",
            "/api/crawl",
            "/api/crawled-data",
            "/api/hs-codes",
            "/api/hs6",
            "/api/",
        ]

    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            token = request.cookies.get(CSRF_COOKIE)
            if not token:
                token = secrets.token_urlsafe(32)
                # SameSite=None (not Strict): this app can be viewed inside the
                # Emergent preview iframe, where the top-level document is a
                # different site (app.emergent.sh) — a Strict/Lax cookie would
                # never reach our own origin's fetches in that nested context.
                # Safe here because double-submit CSRF protection relies on
                # same-origin JS being the only reader/writer of this cookie
                # and header, not on SameSite blocking cross-site sending.
                # SameSite=None requires Secure, hence tied to _HTTPS.
                response.set_cookie(
                    CSRF_COOKIE,
                    token,
                    httponly=False,
                    samesite="none" if _HTTPS else "lax",
                    secure=_HTTPS,
                    max_age=3600,
                )
            response.headers[CSRF_HEADER] = token
            return response

        raw_path = request.url.path
        path = raw_path
        if not path.startswith("/"):
            parts = raw_path.split("/api/", 1)
            if len(parts) > 1:
                path = "/api/" + parts[1]
            else:
                path = "/" + raw_path.split("/", 1)[-1] if "/" in raw_path else raw_path

        if path in self.exempt_paths:
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE)
        header_token = request.headers.get(CSRF_HEADER)

        if not cookie_token or not header_token:
            logger.warning(f"CSRF: missing token for {request.method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"},
            )

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF: token mismatch for {request.method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token invalid"},
            )

        return await call_next(request)
