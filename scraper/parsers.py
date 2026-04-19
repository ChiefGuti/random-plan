"""
HTML extraction logic — one function per source site.
Each parser takes raw HTML and returns a list of Plan dicts.
"""
import uuid
from bs4 import BeautifulSoup


def parse_malmo_blog(html: str) -> list[dict]:
    """
    Example parser for a Malmö events listing page.
    Adapt selectors to the real site structure as needed.
    """
    soup = BeautifulSoup(html, "html.parser")
    plans = []

    for card in soup.select(".event-card"):
        title_el = card.select_one(".event-title")
        desc_el = card.select_one(".event-description")
        link_el = card.select_one("a[href]")
        date_el = card.select_one(".event-date")

        if not (title_el and desc_el and link_el):
            continue

        source_url = link_el["href"]
        if not source_url.startswith("http"):
            source_url = "https://www.visitmalmo.com" + source_url

        plans.append(
            {
                "id": str(uuid.uuid4()),
                "title": title_el.get_text(strip=True),
                "description": desc_el.get_text(strip=True)[:300],
                "category": "Event",
                "maps_url": f"https://maps.google.com/?q={title_el.get_text(strip=True)}+Malmö",
                "source_url": source_url,
                "event_date": date_el.get_text(strip=True) if date_el else None,
            }
        )

    return plans
