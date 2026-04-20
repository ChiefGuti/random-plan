import os

import libsql_client
from dotenv import load_dotenv

load_dotenv()


def get_db_client() -> libsql_client.Client:
    """Create a new libsql client from env vars. Not pooled — one client per call."""
    return libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )


async def fetch_all_active_plans() -> list[dict]:
    """Return all is_active=1 plans. Used by the in-memory cache layer."""
    async with get_db_client() as client:
        result = await client.execute(
            "SELECT id, title, description, category, maps_url, "
            "source_url, event_date, created_at, "
            "image_url, neighborhood, duration_minutes, price_range, tips "
            "FROM plans WHERE is_active = 1"
        )
    cols = (
        "id", "title", "description", "category", "maps_url", "source_url",
        "event_date", "created_at",
        "image_url", "neighborhood", "duration_minutes", "price_range", "tips",
    )
    return [dict(zip(cols, row)) for row in result.rows]


async def fetch_plan_by_id(plan_id: str) -> dict | None:
    """Return a single active plan by primary key, or None if not found."""
    async with get_db_client() as client:
        result = await client.execute(
            "SELECT id, title, description, category, maps_url, source_url, "
            "event_date, created_at, image_url, neighborhood, duration_minutes, "
            "price_range, tips FROM plans WHERE id = ? AND is_active = 1",
            [plan_id],
        )
        if not result.rows:
            return None
        row = result.rows[0]
        cols = (
            "id", "title", "description", "category", "maps_url", "source_url",
            "event_date", "created_at", "image_url", "neighborhood",
            "duration_minutes", "price_range", "tips",
        )
        return dict(zip(cols, row))
