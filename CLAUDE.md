# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Architecture

```
Browser
  |
  |  GET /                 (index.html + /public/app.js)
  |  GET /api/random-plan
  v
Vercel (FastAPI — api/main.py)
  |
  |  SELECT ... ORDER BY RANDOM() LIMIT 1  (via in-memory cache)
  v
Turso (hosted libsql / SQLite)
  ^
  |  INSERT OR UPDATE plans
  |
GitHub Actions (cron 03:00 UTC)
  |
  v
scraper/scraper.py + scraper/parsers.py
```

**Key rule:** The frontend (`public/app.js`) never talks to the database directly. All DB access goes through the API.

```
random-plan/
├── api/
│   ├── main.py        FastAPI app — routes, rate limiting (slowapi), static mount
│   ├── database.py    Async Turso client, fetch_all_active_plans(), fetch_plan_by_id()
│   └── cache.py       In-memory plan cache (TTL-based, avoids per-request DB hits)
├── scraper/
│   ├── scraper.py     Entry point — iterates SOURCES, calls parsers, upserts to DB
│   └── parsers.py     One parser function per source site (BeautifulSoup)
├── tests/
│   └── test_api.py    pytest — covers 200, 404, 429 (rate limit) scenarios
├── public/
│   └── app.js         Vanilla JS — fetch /api/random-plan, render, error state
├── index.html         Single-page UI (Tailwind CSS via CDN)
├── seed.py            One-off: creates plans table + inserts 5 mock rows
├── vercel.json        Rewrites /api/* to api/main.py
└── .github/workflows/scraper.yml   Daily cron (03:00 UTC) + manual dispatch
```

---

## How to Run Locally

### 1. Set up environment

```bash
cd /Users/sergiogutierrez/Documents/Projects/random-plan
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure env vars

```bash
cp .env.example .env
# Edit .env and fill in:
# TURSO_DATABASE_URL=libsql://random-plan-<your-org>.turso.io
# TURSO_AUTH_TOKEN=<token>
```

### 3. Start the dev server

```bash
uvicorn api.main:app --reload
```

Open `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

---

## Required Environment Variables

| Variable | Description |
|---|---|
| `TURSO_DATABASE_URL` | `libsql://` connection URL for the Turso database |
| `TURSO_AUTH_TOKEN` | Auth token — generate with `turso db tokens create random-plan` |

In production (Vercel and GitHub Actions), these must be set as environment variables / secrets in each platform — they are NOT read from `.env` in production.

---

## API Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/random-plan` | Random active plan (optional `?category=` filter). Rate limited: 10/min. |
| `GET` | `/api/categories` | Sorted list of distinct categories from active plans |
| `GET` | `/api/plans/{id}` | Single plan by ID (404 if not found). Rate limited: 30/min. |
| `GET` | `/api/health` | DB connectivity check + uptime |

---

## Tests

Tests mock the database layer — no live Turso connection needed.

```bash
source .venv/bin/activate
pytest
pytest -v   # verbose output
```

Covers: HTTP 200 (valid plan), HTTP 404 (no active plans), HTTP 429 (rate limit on 11th request).

---

## Deployment

**Vercel** — manual only. Pushing to `main` does not deploy (no auto-deploy, by choice for now):

```bash
vercel --prod   # production deploy
```

`vercel.json` rewrites all `/api/*` requests to `api/main.py`. Static files are served by Vercel's CDN.

Set env vars in Vercel dashboard or via CLI:

```bash
vercel env add TURSO_DATABASE_URL
vercel env add TURSO_AUTH_TOKEN
```

---

## Scraper

Runs daily at 03:00 UTC via GitHub Actions (`.github/workflows/scraper.yml`). Can also be triggered manually from the GitHub Actions UI.

- Upsert key: `source_url` — re-running is always idempotent, no duplicates.
- Each plan has `is_active = 1` by default. Set to `0` to hide from API without deleting.
- To run locally: `python -m scraper.scraper`
- To add a new source: add a parser function to `scraper/parsers.py`, register it in the `SOURCES` list in `scraper/scraper.py`.

---

## Skill Routing

| Request | Skill | Why |
|---------|-------|-----|
| "Test the API / verify scraper / check UI on Vercel" | `/qa` | Headless browser QA. Test API routes, UI, Vercel deployment. |
| "Review code before merge" | `/review` | Multi-pass code review: architecture, style, security. |
| "Design system audit / polish UI / check responsive" | `/design-review` | Visual quality, accessibility, responsive design. |
| "Ready to ship — deploy to Vercel + verify canary" | `/land-and-deploy` | Merge → deploy → monitor (Vercel + GitHub Actions). |
| "Final release checklist — merge & push" | `/ship` | Merge, CHANGELOG, version bump, push to main. |

When the user requests something matching the left column, invoke the skill immediately. Don't wait for approval.

## Notes

- CORS is wildcard (`*`) — this is intentional for a public read-only API.
- The API uses an in-memory cache (`api/cache.py`) to avoid a Turso round-trip on every request.
- Rate limiting is handled by `slowapi` using the real client IP (trusts `X-Forwarded-For` leftmost address only).
- Categories: `Event`, `Food`, `Outdoor`, `Oddity` — keep consistent across parsers.
