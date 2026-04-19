"""
Main scraper script — run daily by GitHub Actions.
Fetches pages, parses them, and upserts results into Turso.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

import httpx
import libsql_client
from dotenv import load_dotenv

from scraper.parsers import parse_malmo_blog

load_dotenv()

SOURCES = [
    {
        "url": "https://www.visitmalmo.com/see-do/whats-on/",
        "parser": parse_malmo_blog,
    },
]

UPSERT_SQL = """
INSERT INTO plans (id, title, description, category, maps_url, source_url, event_date, created_at, is_active)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
ON CONFLICT(source_url) DO UPDATE SET
    title       = excluded.title,
    description = excluded.description,
    category    = excluded.category,
    maps_url    = excluded.maps_url,
    event_date  = excluded.event_date,
    is_active   = 1;
"""


async def upsert_plan(client: libsql_client.Client, plan: dict):
    now = datetime.now(timezone.utc).isoformat()
    await client.execute(
        UPSERT_SQL,
        [
            plan["id"],  # parsers always provide an id; no fallback needed
            plan["title"],
            plan["description"],
            plan["category"],
            plan["maps_url"],
            plan["source_url"],
            plan.get("event_date"),
            now,
        ],
    )


async def run_scraper():
    async with libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    ) as db_client:
        async with httpx.AsyncClient(timeout=15) as http_client:
            for source in SOURCES:
                try:
                    response = await http_client.get(source["url"])
                    response.raise_for_status()
                    plans = source["parser"](response.text)
                    for plan in plans:
                        await upsert_plan(db_client, plan)
                    print(f"Upserted {len(plans)} plans from {source['url']}")
                except Exception as e:
                    print(f"ERROR scraping {source['url']}: {e}")


if __name__ == "__main__":
    asyncio.run(run_scraper())
