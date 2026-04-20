"""
One-off script to create the plans table and populate it with 5 mock Malmö plans.
Run with: python seed.py
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

import libsql_client
from dotenv import load_dotenv

load_dotenv()

MOCK_PLANS = [
    {
        "id": str(uuid.uuid4()),
        "title": "Fika at Lilla Kafferosteriet",
        "description": "A tiny roastery in Möllevången that roasts its own beans. Grab a single-origin pour-over and watch the neighbourhood wake up.",
        "category": "Food",
        "maps_url": "https://maps.google.com/?q=Lilla+Kafferosteriet+Malmö",
        "source_url": "https://example.com/lilla-kafferosteriet",
        "event_date": None,
        "is_active": 1,
        "neighborhood": "Möllevången",
        "duration_minutes": 45,
        "price_range": "BUDGET",
        "tips": "Try the single-origin Ethiopian — they roast it in-house.",
        "image_url": None,
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Secret Rooftop at Malmö Live",
        "description": "The concert hall's public terrace offers a panoramic view of the Öresund strait — completely free and almost always empty on weekday afternoons.",
        "category": "Oddity",
        "maps_url": "https://maps.google.com/?q=Malmö+Live+Konserthus",
        "source_url": "https://example.com/malmo-live-rooftop",
        "event_date": None,
        "is_active": 1,
        "neighborhood": "Centrum",
        "duration_minutes": 30,
        "price_range": "FREE",
        "tips": "Weekday afternoons are almost always empty.",
        "image_url": None,
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Underground Jazz at Babel",
        "description": "Babel hosts free-entry jazz jams every Thursday. Show up after 20:00 for the improvisational sets.",
        "category": "Event",
        "maps_url": "https://maps.google.com/?q=Babel+Malmö",
        "source_url": "https://example.com/babel-jazz-thursday",
        "event_date": "2026-04-24T20:00:00",
        "is_active": 1,
        "neighborhood": "Möllevången",
        "duration_minutes": 120,
        "price_range": "FREE",
        "tips": "Arrive before 20:00 if you want a seat — it fills up fast.",
        "image_url": None,
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Vintage Hunt at Möllan Loppis",
        "description": "Möllevångstorget's weekend flea market is a goldmine of 70s furniture and vinyl. Arrive early before dealers cherry-pick the good stuff.",
        "category": "Oddity",
        "maps_url": "https://maps.google.com/?q=Möllevångstorget+Malmö",
        "source_url": "https://example.com/mollan-loppis",
        "event_date": None,
        "is_active": 1,
        "neighborhood": "Möllevången",
        "duration_minutes": 90,
        "price_range": "BUDGET",
        "tips": "Bring cash — most vendors skip Swish. Arrive early.",
        "image_url": None,
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Sunset Walk on Ribersborg Beach",
        "description": "A 3 km stretch of open beach with a historic cold-bath house at the end. Best visited at golden hour when the Öresund bridge lights up.",
        "category": "Outdoor",
        "maps_url": "https://maps.google.com/?q=Ribersborg+Beach+Malmö",
        "source_url": "https://example.com/ribersborg-beach",
        "event_date": None,
        "is_active": 1,
        "neighborhood": "Västra Hamnen",
        "duration_minutes": 60,
        "price_range": "FREE",
        "tips": "Walk all the way to Kallbadhuset at the far end — worth it.",
        "image_url": None,
    },
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS plans (
    id               TEXT PRIMARY KEY,
    title            TEXT NOT NULL,
    description      TEXT NOT NULL,
    category         TEXT NOT NULL,
    maps_url         TEXT NOT NULL,
    source_url       TEXT NOT NULL UNIQUE,
    event_date       TEXT,
    created_at       TEXT NOT NULL,
    is_active        INTEGER NOT NULL DEFAULT 1,
    image_url        TEXT,
    neighborhood     TEXT,
    duration_minutes INTEGER,
    price_range      TEXT DEFAULT 'FREE',
    tips             TEXT,
    updated_at       TEXT
);
"""


async def seed():
    async with libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    ) as client:
        await client.execute(CREATE_TABLE_SQL)
        print("Table ready.")

        now = datetime.now(timezone.utc).isoformat()
        for plan in MOCK_PLANS:
            await client.execute(
                """
                INSERT OR IGNORE INTO plans
                    (id, title, description, category, maps_url, source_url,
                     event_date, created_at, is_active,
                     image_url, neighborhood, duration_minutes, price_range, tips, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    plan["id"], plan["title"], plan["description"],
                    plan["category"], plan["maps_url"], plan["source_url"],
                    plan["event_date"], now, plan["is_active"],
                    plan["image_url"], plan["neighborhood"], plan["duration_minutes"],
                    plan["price_range"], plan["tips"], now,
                ],
            )
            print(f"  Inserted: {plan['title']}")

        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
