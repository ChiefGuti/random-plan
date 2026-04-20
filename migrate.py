"""
One-off migration script to add new columns to the plans table.
Run with: python migrate.py
"""
import asyncio
import os

import libsql_client
from dotenv import load_dotenv

load_dotenv()

MIGRATIONS = [
    ("image_url",         "ALTER TABLE plans ADD COLUMN image_url TEXT;"),
    ("neighborhood",      "ALTER TABLE plans ADD COLUMN neighborhood TEXT;"),
    ("duration_minutes",  "ALTER TABLE plans ADD COLUMN duration_minutes INTEGER;"),
    ("price_range",       "ALTER TABLE plans ADD COLUMN price_range TEXT DEFAULT 'FREE';"),
    ("tips",              "ALTER TABLE plans ADD COLUMN tips TEXT;"),
    ("updated_at",        "ALTER TABLE plans ADD COLUMN updated_at TEXT;"),
]


async def migrate():
    async with libsql_client.create_client(
        url=os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    ) as client:
        for column, sql in MIGRATIONS:
            try:
                await client.execute(sql)
                print(f"✓ Added: {column}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"⊘ Skipped: {column} (already exists)")
                else:
                    raise


if __name__ == "__main__":
    asyncio.run(migrate())
