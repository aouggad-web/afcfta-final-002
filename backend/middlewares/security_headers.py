import os
import secrets
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def _origine_supabase() -> str:
    """Origine exacte du projet Supabase (https uniquement), que le navigateur
    joint pour l'inscription, la connexion et le renouvellement de session.
    Vide quand SUPABASE_URL n'est pas une URL https valide."""
    parties = urlsplit(os.environ.get("SUPABASE_URL", "").strip())
    if parties.scheme != "https" or not parties.hostname:
        return ""
    return f"https://{parties.netloc}"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response: Response = await call_next(request)

        connect_src = "connect-src 'self' https://api.worldbank.org https://api-v2.oec.world"
        supabase = _origine_supabase()
        if supabase:
            connect_src = f"{connect_src} {supabase}"

        csp = "; ".join(
            [
                "default-src 'self'",
                f"script-src 'self' 'nonce-{nonce}'",
                f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com",
                "img-src 'self' data: https: blob:",
                "font-src 'self' https://fonts.gstatic.com",
                connect_src,
                "frame-ancestors 'self'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        )

        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Only send HSTS when the app is configured to serve over HTTPS.
        # Sending HSTS over plain HTTP can break client access.
        if os.environ.get("HTTPS_ENABLED", "false").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
