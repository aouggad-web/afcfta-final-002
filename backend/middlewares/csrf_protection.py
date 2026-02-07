import secrets
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

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
            "/api/",
        ]

    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            token = request.cookies.get(CSRF_COOKIE)
            if not token:
                token = secrets.token_urlsafe(32)
                response.set_cookie(
                    CSRF_COOKIE,
                    token,
                    httponly=False,
                    samesite="strict",
                    secure=False,
                    max_age=3600,
                )
            response.headers[CSRF_HEADER] = token
            return response

        path = request.url.path
        if any(path.startswith(p) for p in self.exempt_paths):
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
