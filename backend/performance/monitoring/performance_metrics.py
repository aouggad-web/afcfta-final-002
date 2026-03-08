"""
AfCFTA Platform - Performance Monitoring Service
=================================================
Tracks query times, cache hit/miss rates, and slow-query alerts.
"""

import time
import logging
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# Maximum number of slow-query records to keep in memory
MAX_SLOW_QUERY_HISTORY = 200

# Threshold in seconds to classify a query as slow
SLOW_QUERY_THRESHOLD_S = 0.5


class PerformanceMetrics:
    """
    In-process performance metrics collector.

    Tracks:
    - Cache hit / miss counts per operation
    - Query latency histograms (p50 / p95 / p99)
    - Slow-query log
    """

    def __init__(self) -> None:
        self._hits: Dict[str, int] = defaultdict(int)
        self._misses: Dict[str, int] = defaultdict(int)
        self._latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._slow_queries: deque = deque(maxlen=MAX_SLOW_QUERY_HISTORY)
        self._started_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Cache tracking
    # ------------------------------------------------------------------

    def record_cache_hit(self, operation: str) -> None:
        self._hits[operation] += 1

    def record_cache_miss(self, operation: str) -> None:
        self._misses[operation] += 1

    def cache_hit_rate(self, operation: str) -> float:
        total = self._hits[operation] + self._misses[operation]
        return self._hits[operation] / total if total else 0.0

    # ------------------------------------------------------------------
    # Latency tracking
    # ------------------------------------------------------------------

    def record_latency(self, operation: str, duration_s: float) -> None:
        self._latencies[operation].append(duration_s)
        if duration_s >= SLOW_QUERY_THRESHOLD_S:
            self._slow_queries.append(
                {
                    "operation": operation,
                    "duration_s": round(duration_s, 4),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def percentile(self, operation: str, pct: float) -> Optional[float]:
        data = sorted(self._latencies[operation])
        if not data:
            return None
        idx = int(len(data) * pct / 100)
        return round(data[min(idx, len(data) - 1)], 4)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        ops = set(list(self._hits.keys()) + list(self._misses.keys()) + list(self._latencies.keys()))
        op_stats = {}
        for op in ops:
            op_stats[op] = {
                "cache_hits": self._hits[op],
                "cache_misses": self._misses[op],
                "hit_rate_pct": round(self.cache_hit_rate(op) * 100, 1),
                "p50_s": self.percentile(op, 50),
                "p95_s": self.percentile(op, 95),
                "p99_s": self.percentile(op, 99),
                "sample_count": len(self._latencies[op]),
            }
        return {
            "uptime_seconds": (datetime.now(timezone.utc) - self._started_at).total_seconds(),
            "slow_queries_count": len(self._slow_queries),
            "recent_slow_queries": list(self._slow_queries)[-10:],
            "operations": op_stats,
        }

    def slow_queries(self) -> list:
        return list(self._slow_queries)


# Global singleton
_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    global _metrics
    if _metrics is None:
        _metrics = PerformanceMetrics()
    return _metrics


# ------------------------------------------------------------------
# Decorator
# ------------------------------------------------------------------

def track_performance(operation: str):
    """
    Decorator that records latency for any sync or async function.

    Usage::

        @track_performance("tariff_lookup")
        async def get_tariff(country, hs_code):
            ...
    """
    def decorator(func: Callable) -> Callable:
        if _is_coroutine(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    get_metrics().record_latency(operation, time.perf_counter() - start)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    get_metrics().record_latency(operation, time.perf_counter() - start)
            return sync_wrapper
    return decorator


def _is_coroutine(func: Callable) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(func)
