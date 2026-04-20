import time
from collections.abc import Awaitable, Callable

# Process-level in-memory cache. Resets on worker restart and is not shared
# across multiple Uvicorn workers. Sufficient for a single-process deployment.
_cache: list[dict] = []
_cache_ts: float = 0.0
CACHE_TTL = 3600  # 1 hour


async def get_cached_plans(fetch_fn: Callable[[], Awaitable[list[dict]]]) -> list[dict]:
    """Return cached plans, refreshing from fetch_fn when the TTL has expired."""
    global _cache, _cache_ts
    if not _cache or (time.monotonic() - _cache_ts) > CACHE_TTL:
        _cache = await fetch_fn()
        _cache_ts = time.monotonic()
    return _cache
