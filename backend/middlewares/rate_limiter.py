import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 10,
        exempt_paths: list | None = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.exempt_paths = exempt_paths or ["/api/health", "/api/"]
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
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
        if any(path.startswith(p) for p in self.exempt_paths):
            return await call_next(request)

        now = time.time()
        self._cleanup_old_entries(now)

        client_ip = self._get_client_ip(request)
        bucket_key = f"{client_ip}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"

        self._buckets[bucket_key] = [
            t for t in self._buckets[bucket_key] if t > now - 60
        ]

        if len(self._buckets[bucket_key]) >= self.requests_per_minute:
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
        remaining = self.requests_per_minute - len(self._buckets[bucket_key])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        return response
