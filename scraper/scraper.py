"""
Main scraper script — run daily by GitHub Actions.
Fetches pages, parses them, and upserts results into Turso.
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx
import libsql_client
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from scraper.parsers import parse_malmo_blog

load_dotenv()

SOURCES = [
    {
        "url": "https://www.visitmalmo.com/see-do/whats-on/",
        "parser": parse_malmo_blog,
    },
]

UPSERT_SQL = """
INSERT INTO plans (id, title, description, category, maps_url, source_url, event_date, created_at, is_active,
                   image_url, neighborhood, duration_minutes, price_range, tips, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
ON CONFLICT(source_url) DO UPDATE SET
    title            = excluded.title,
    description      = excluded.description,
    category         = excluded.category,
    maps_url         = excluded.maps_url,
    event_date       = excluded.event_date,
    image_url        = excluded.image_url,
    neighborhood     = excluded.neighborhood,
    duration_minutes = excluded.duration_minutes,
    price_range      = excluded.price_range,
    tips             = excluded.tips,
    updated_at       = excluded.updated_at,
    is_active        = 1;
"""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; RandomPlanBot/1.0; +https://github.com/ChiefGuti/random-plan)"
    )
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    reraise=True,
)
async def fetch_with_retry(http_client: httpx.AsyncClient, url: str) -> httpx.Response:
    response = await http_client.get(url, headers=HEADERS)
    response.raise_for_status()
    return response


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
            plan.get("image_url"),
            plan.get("neighborhood"),
            plan.get("duration_minutes"),
            plan.get("price_range"),
            plan.get("tips"),
            plan.get("updated_at", now),
        ],
    )


async def expire_past_events(client: libsql_client.Client):
    """Set is_active=0 for events whose event_date has passed."""
    now = datetime.now(timezone.utc).isoformat()
    await client.execute(
        """
        UPDATE plans
        SET is_active = 0
        WHERE event_date IS NOT NULL
          AND event_date < ?
          AND is_active = 1
        """,
        [now],
    )
    print("Expired past events.")


async def run_scraper():
    async with libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    ) as db_client:
        async with httpx.AsyncClient(timeout=15) as http_client:
            for source in SOURCES:
                try:
                    response = await fetch_with_retry(http_client, source["url"])
                    plans = source["parser"](response.text)
                    for plan in plans:
                        await upsert_plan(db_client, plan)
                    print(f"Upserted {len(plans)} plans from {source['url']}")
                except Exception as e:
                    print(f"ERROR scraping {source['url']}: {e}")

        await expire_past_events(db_client)


if __name__ == "__main__":
    asyncio.run(run_scraper())
