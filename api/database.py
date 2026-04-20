import os

import libsql_client
from dotenv import load_dotenv

load_dotenv()


def get_db_client() -> libsql_client.Client:
    return libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )


async def fetch_all_active_plans() -> list[dict]:
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


async def fetch_random_plan() -> dict | None:
    async with get_db_client() as client:
        result = await client.execute(
            """
            SELECT id, title, description, category, maps_url, source_url,
                   event_date, created_at,
                   image_url, neighborhood, duration_minutes, price_range, tips
            FROM plans
            WHERE is_active = 1
            ORDER BY RANDOM()
            LIMIT 1
            """
        )
        if not result.rows:
            return None
        row = result.rows[0]
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "category": row[3],
            "maps_url": row[4],
            "source_url": row[5],
            "event_date": row[6],
            "created_at": row[7],
            "image_url": row[8],
            "neighborhood": row[9],
            "duration_minutes": row[10],
            "price_range": row[11],
            "tips": row[12],
        }


async def fetch_plan_by_id(plan_id: str) -> dict | None:
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
