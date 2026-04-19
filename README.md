# Random Plan — Malmö

A single-page web app that surfaces a random hidden-gem activity in Malmö, Sweden with one button press. Activities are scraped daily from local event and tourism sites and stored in a hosted SQLite database. The API serves one random active plan per request.

**Live stack:** FastAPI · Turso (libsql) · Vanilla JS · Tailwind CSS · Vercel · GitHub Actions

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Prerequisites](#prerequisites)
5. [Local Setup](#local-setup)
6. [Running Tests](#running-tests)
7. [Scraper — How It Works and How to Extend It](#scraper)
8. [Deployment](#deployment)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Future Enhancements](#future-enhancements)

---

## What It Does

Visitors land on a minimal dark-mode page and click **"Give Me a Plan"**. The frontend calls `GET /api/random-plan`, which picks one row at random from the `plans` table where `is_active = 1`. The result shows:

- A category badge (e.g. `EVENT`, `FOOD`, `OUTDOOR`, `ODDITY`)
- Title and short description
- A direct link to Google Maps
- A source URL back to the original listing

A GitHub Actions cron job runs the scraper every day at 03:00 UTC. It fetches configured source pages, parses them with BeautifulSoup, and upserts new or updated plans into the Turso database. Plans already in the database are updated in place (keyed on `source_url`); no duplicates are created.

**Who it is for:** anyone who wants a spontaneous, local activity in Malmö without scrolling social media or tourism aggregators.

---

## Architecture

```
Browser
  |
  |  GET /                       (index.html + /public/app.js)
  |  GET /api/random-plan
  v
Vercel (FastAPI — api/main.py)
  |
  |  SELECT ... ORDER BY RANDOM() LIMIT 1
  v
Turso (hosted libsql / SQLite)
  ^
  |  INSERT OR UPDATE plans
  |
GitHub Actions (cron 03:00 UTC)
  |
  |  httpx GET source pages
  v
Scraper (scraper/scraper.py + scraper/parsers.py)
```

The frontend never talks to the database directly. The scraper runs as a standalone Python process inside GitHub Actions and writes directly to Turso using the same `libsql_client` library the API uses.

---

## Directory Structure

```
random-plan/
├── api/
│   ├── main.py          # FastAPI app — one route, rate limiting, static file mount
│   └── database.py      # Async Turso client, fetch_random_plan() query
├── scraper/
│   ├── scraper.py       # Entry point — fetches pages, calls parsers, upserts to DB
│   └── parsers.py       # One parser function per source site
├── tests/
│   └── test_api.py      # pytest tests for 200, 404, and rate-limit (429) responses
├── public/
│   └── app.js           # Vanilla JS — fetch, render, error handling, loading state
├── index.html           # Single-page UI (Tailwind CSS via CDN)
├── seed.py              # One-off script: creates the plans table + inserts 5 mock rows
├── requirements.txt     # Python dependencies (pinned versions)
├── vercel.json          # Rewrites all /api/* traffic to api/main.py
├── .env.example         # Template for required environment variables
└── .github/
    └── workflows/
        └── scraper.yml  # Daily cron job (03:00 UTC) + manual dispatch
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Runtime for API, scraper, and tests |
| pip | bundled with Python | Package installation |
| Turso CLI | latest | Create and manage the hosted database |
| Vercel CLI | latest | Deploy and manage the Vercel project |
| Git | any | Version control and GitHub Actions trigger |

Install the Turso CLI:

```bash
curl -sSfL https://get.tur.so/install.sh | bash
```

Install the Vercel CLI:

```bash
npm install -g vercel
```

---

## Local Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/<your-org>/random-plan.git
cd random-plan
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the Turso database

```bash
turso auth login
turso db create random-plan
turso db show random-plan          # note the URL shown as "URL"
turso db tokens create random-plan # copy the token printed
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in the two values:

```
TURSO_DATABASE_URL=libsql://random-plan-<your-org>.turso.io
TURSO_AUTH_TOKEN=<token from step 3>
```

### 5. Create the table and seed mock data

```bash
python seed.py
```

Expected output:

```
Table ready.
  Inserted: Fika at Lilla Kafferosteriet
  Inserted: Secret Rooftop at Malmö Live
  Inserted: Underground Jazz at Babel
  Inserted: Vintage Hunt at Möllan Loppis
  Inserted: Sunset Walk on Ribersborg Beach
Seed complete.
```

`seed.py` uses `INSERT OR IGNORE`, so it is safe to run more than once — duplicate rows are silently skipped.

### 6. Start the development server

```bash
uvicorn api.main:app --reload
```

Open `http://localhost:8000` in your browser and click **"Give Me a Plan"**.

The API docs (auto-generated by FastAPI) are available at `http://localhost:8000/docs`.

---

## Running Tests

Tests mock the database layer entirely — no live Turso connection is needed.

```bash
pytest
```

The test suite covers three scenarios:

| Test | What it verifies |
|------|-----------------|
| `test_random_plan_returns_200` | A valid plan in the DB returns HTTP 200 with correct fields |
| `test_random_plan_returns_404_when_empty` | No active plans returns HTTP 404 with a descriptive message |
| `test_rate_limit_enforced` | The 11th request within one minute returns HTTP 429 |

To see verbose output:

```bash
pytest -v
```

---

## Scraper

### How it works

`scraper/scraper.py` is the entry point. It iterates over a `SOURCES` list. Each entry contains a URL and a parser function. For each source:

1. `httpx` fetches the page with a 15-second timeout.
2. The parser function receives the raw HTML and returns a list of plan dicts.
3. Each plan is upserted into the `plans` table using an `INSERT ... ON CONFLICT(source_url) DO UPDATE` statement, so re-running the scraper is idempotent.

The scraper is triggered automatically by the GitHub Actions workflow (`.github/workflows/scraper.yml`) at 03:00 UTC every day. It can also be triggered manually from the GitHub Actions UI ("workflow_dispatch").

To run the scraper locally:

```bash
python -m scraper.scraper
```

### How to add a new parser

**Step 1.** Add a new function in `scraper/parsers.py`. The function must accept one argument (`html: str`) and return a list of dicts. Each dict must contain these keys:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | str | Yes | A UUID (call `str(uuid.uuid4())`) |
| `title` | str | Yes | Short display name for the activity |
| `description` | str | Yes | One or two sentences, max ~300 characters |
| `category` | str | Yes | One of: `Event`, `Food`, `Outdoor`, `Oddity` |
| `maps_url` | str | Yes | Full Google Maps URL for the location |
| `source_url` | str | Yes | Canonical URL of the original listing (used as upsert key) |
| `event_date` | str or None | No | ISO 8601 datetime string, or `None` for permanent spots |

Example skeleton:

```python
# scraper/parsers.py

def parse_my_new_source(html: str) -> list[dict]:
    import uuid
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    plans = []

    for card in soup.select(".your-css-selector"):
        title = card.select_one(".title").get_text(strip=True)
        desc  = card.select_one(".description").get_text(strip=True)[:300]
        link  = card.select_one("a")["href"]
        if not link.startswith("http"):
            link = "https://your-source-domain.com" + link

        plans.append({
            "id":          str(uuid.uuid4()),
            "title":       title,
            "description": desc,
            "category":    "Event",          # adjust as appropriate
            "maps_url":    f"https://maps.google.com/?q={title}+Malmö",
            "source_url":  link,
            "event_date":  None,
        })

    return plans
```

**Step 2.** Register the new source in `scraper/scraper.py`:

```python
from scraper.parsers import parse_malmo_blog, parse_my_new_source

SOURCES = [
    {
        "url": "https://www.visitmalmo.com/see-do/whats-on/",
        "parser": parse_malmo_blog,
    },
    {
        "url": "https://your-new-source.com/events/",
        "parser": parse_my_new_source,
    },
]
```

**Step 3.** Test locally:

```bash
python -m scraper.scraper
```

If the source page returns an error or the selectors match nothing, the scraper prints an `ERROR` line for that source and continues with the rest — it will not crash.

---

## Deployment

### Vercel

The project is deployed as a serverless FastAPI app on Vercel. `vercel.json` rewrites all `/api/*` requests to `api/main.py`. Static files (`index.html`, `public/app.js`) are served directly by Vercel's CDN.

```bash
vercel login
vercel                   # follow the prompts for first-time setup
```

Set the required environment variables in the Vercel dashboard under **Project > Settings > Environment Variables**, or via the CLI:

```bash
vercel env add TURSO_DATABASE_URL
vercel env add TURSO_AUTH_TOKEN
```

Deploy to production:

```bash
vercel --prod
```

### GitHub Actions secrets

The daily scraper workflow reads credentials from GitHub repository secrets. Add them at **GitHub > Repository > Settings > Secrets and variables > Actions > New repository secret**:

| Secret name | Value |
|-------------|-------|
| `TURSO_DATABASE_URL` | The `libsql://` URL of your Turso database |
| `TURSO_AUTH_TOKEN` | The auth token created with `turso db tokens create` |

Once the secrets are set, the scraper will run automatically every day at 03:00 UTC. To trigger it immediately, go to **Actions > Daily Scraper > Run workflow**.

---

## Environment Variables Reference

| Variable | Description | Example value |
|----------|-------------|---------------|
| `TURSO_DATABASE_URL` | The `libsql://` connection URL for your Turso database. Found via `turso db show <name>`. | `libsql://random-plan-acme.turso.io` |
| `TURSO_AUTH_TOKEN` | Authentication token for the Turso database. Generated with `turso db tokens create <name>`. | `eyJhbGciOiJF...` |

Both variables are required at runtime for the API and the scraper. Locally they are loaded from `.env` via `python-dotenv`. In production (Vercel and GitHub Actions) they must be set as environment variables or secrets in the respective platform.

---

## Future Enhancements

| Enhancement | Description |
|-------------|-------------|
| Geospatial filtering | Add `latitude` and `longitude` columns to `plans`. Let the frontend request the user's location and call `GET /api/random-plan?lat=55.60&lon=13.00&radius=2` to return only plans within a given radius. |
| Vibe toggles | Add filter buttons on the UI (e.g. "Outdoor only", "Free only", "Tonight"). Pass them as query parameters and extend the SQL `WHERE` clause accordingly. |
| Dead-link checker | A second GitHub Actions workflow (weekly) that iterates over all `source_url` values, sends a HEAD request to each, and sets `is_active = 0` for any that return 4xx or 5xx. Prevents broken plans from reaching users. |
| Additional parsers | Extend `SOURCES` in `scraper/scraper.py` with parsers for Malmö Stad's event calendar, Foursquare, or local blogs. Each new source only requires one new function in `scraper/parsers.py`. |
| Admin endpoint | A password-protected `POST /api/plans` endpoint to manually add one-off plans without running a scraper. |

---

*Last updated: April 19, 2026*
