from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.database import fetch_random_plan

ROOT = Path(__file__).parent.parent

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Random Plan API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


app.mount("/public", StaticFiles(directory=ROOT / "public"), name="public")

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(ROOT / "index.html")


@app.get("/api/random-plan")
@limiter.limit("10/minute")
async def random_plan(request: Request):
    plan = await fetch_random_plan()
    if plan is None:
        return JSONResponse(status_code=404, content={"detail": "No active plans found."})
    return plan
