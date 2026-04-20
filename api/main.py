import logging
import random as _random
import time as _time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.cache import get_cached_plans
from api.database import fetch_all_active_plans, fetch_plan_by_id, get_db_client

ROOT = Path(__file__).parent.parent

logger = logging.getLogger("random-plan")

_start_time = _time.time()


def get_real_ip(request: Request) -> str:
    """Extract the originating client IP, trusting X-Forwarded-For only for the
    first (leftmost) address to prevent spoofing by the client."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


limiter = Limiter(key_func=get_real_ip)

app = FastAPI(title="Random Plan API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Public read-only API — wildcard CORS is intentional
    allow_methods=["GET"],
    allow_headers=["*"],
)


app.mount("/public", StaticFiles(directory=ROOT / "public"), name="public")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(ROOT / "index.html")


@app.get("/api/random-plan")
@limiter.limit("10/minute")
async def random_plan(request: Request, category: Optional[str] = None):
    """Return a random active plan, optionally filtered by category."""
    try:
        plans = await get_cached_plans(fetch_all_active_plans)
    except Exception as exc:
        logger.exception("Database fetch failed: %s", exc)
        return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable."})
    if category:
        plans = [p for p in plans if p["category"].lower() == category.lower()]
    if not plans:
        return JSONResponse(status_code=404, content={"detail": "No active plans found."})
    return _random.choice(plans)


@app.get("/api/categories")
async def list_categories():
    """Return a sorted list of all distinct categories among active plans."""
    try:
        plans = await get_cached_plans(fetch_all_active_plans)
    except Exception as exc:
        logger.exception("Database fetch failed: %s", exc)
        return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable."})
    return sorted({p["category"] for p in plans})


@app.get("/api/plans/{plan_id}")
@limiter.limit("30/minute")
async def get_plan(request: Request, plan_id: str):
    """Return a single active plan by ID, or 404 if not found."""
    plan = await fetch_plan_by_id(plan_id)
    if not plan:
        return JSONResponse(status_code=404, content={"detail": "Plan not found."})
    return plan


@app.get("/api/health", include_in_schema=False)
async def health():
    try:
        client = get_db_client()
        await client.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "uptime_seconds": round(_time.time() - _start_time),
    }
