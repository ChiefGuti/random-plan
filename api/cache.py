import time

_cache: list[dict] = []
_cache_ts: float = 0.0
CACHE_TTL = 3600  # 1 hour

async def get_cached_plans(fetch_fn) -> list[dict]:
    global _cache, _cache_ts
    if not _cache or (time.monotonic() - _cache_ts) > CACHE_TTL:
        _cache = await fetch_fn()
        _cache_ts = time.monotonic()
    return _cache
