from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.main import app

MOCK_PLAN = {
    "id": "abc-123",
    "title": "Underground Jazz at Babel",
    "description": "Free-entry jazz jams every Thursday after 20:00.",
    "category": "Event",
    "maps_url": "https://maps.google.com/?q=Babel+Malmö",
    "source_url": "https://example.com/babel-jazz",
    "event_date": "2026-04-24T20:00:00",
    "created_at": "2026-04-19T10:00:00+00:00",
    "image_url": None,
    "neighborhood": "Möllevången",
    "duration_minutes": 120,
    "price_range": "FREE",
    "tips": "Arrive before 20:00 if you want a seat.",
}


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter storage between tests to avoid bleed-over."""
    yield
    storage = getattr(app.state.limiter, "_storage", None)
    if storage is not None:
        # limits.MemoryStorage stores counts in an internal dict
        internal = getattr(storage, "_storage", None)
        if isinstance(internal, dict):
            internal.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_random_plan_returns_200(client):
    with patch("api.main.get_cached_plans", new=AsyncMock(return_value=[MOCK_PLAN])):
        response = await client.get("/api/random-plan")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == MOCK_PLAN["title"]
    assert data["category"] == MOCK_PLAN["category"]


@pytest.mark.asyncio
async def test_random_plan_returns_404_when_empty(client):
    with patch("api.main.get_cached_plans", new=AsyncMock(return_value=[])):
        response = await client.get("/api/random-plan")
    assert response.status_code == 404
    assert response.json()["detail"] == "No active plans found."


@pytest.mark.asyncio
async def test_rate_limit_enforced(client):
    with patch("api.main.get_cached_plans", new=AsyncMock(return_value=[MOCK_PLAN])):
        responses = [await client.get("/api/random-plan") for _ in range(11)]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, "Rate limit (10/min) should have triggered a 429"
