"""
Unit tests for scraper/parsers.py.
Uses fake HTML that matches the placeholder selectors in parse_malmo_blog.
When the real visitmalmo.com structure is confirmed, update the HTML fixtures
and selectors together.
"""
from scraper.parsers import parse_malmo_blog

VALID_CARD_HTML = """
<html><body>
  <div class="event-card">
    <h2 class="event-title">Jazz Night at Babel</h2>
    <p class="event-description">Free-entry jazz jams every Thursday after 20:00.</p>
    <a href="https://www.visitmalmo.com/events/jazz-night">More info</a>
    <span class="event-date">2026-05-01</span>
  </div>
</body></html>
"""

RELATIVE_URL_HTML = """
<html><body>
  <div class="event-card">
    <h2 class="event-title">Street Food Festival</h2>
    <p class="event-description">Dozens of food trucks at Stortorget.</p>
    <a href="/events/street-food">More info</a>
  </div>
</body></html>
"""

MISSING_TITLE_HTML = """
<html><body>
  <div class="event-card">
    <p class="event-description">An event with no title.</p>
    <a href="https://www.visitmalmo.com/events/no-title">More info</a>
  </div>
</body></html>
"""

MISSING_LINK_HTML = """
<html><body>
  <div class="event-card">
    <h2 class="event-title">Linkless Event</h2>
    <p class="event-description">An event with no link.</p>
  </div>
</body></html>
"""

NO_CARDS_HTML = """
<html><body>
  <p>No events here.</p>
</body></html>
"""


def test_extracts_valid_card():
    plans = parse_malmo_blog(VALID_CARD_HTML)
    assert len(plans) == 1
    p = plans[0]
    assert p["title"] == "Jazz Night at Babel"
    assert p["description"] == "Free-entry jazz jams every Thursday after 20:00."
    assert p["category"] == "Event"
    assert p["source_url"] == "https://www.visitmalmo.com/events/jazz-night"
    assert p["event_date"] == "2026-05-01"
    assert "id" in p
    assert p["maps_url"].startswith("https://maps.google.com")


def test_source_url_is_absolute_for_relative_href():
    plans = parse_malmo_blog(RELATIVE_URL_HTML)
    assert len(plans) == 1
    assert plans[0]["source_url"].startswith("https://")
    assert plans[0]["source_url"] == "https://www.visitmalmo.com/events/street-food"


def test_skips_card_missing_title():
    plans = parse_malmo_blog(MISSING_TITLE_HTML)
    assert plans == []


def test_skips_card_missing_link():
    plans = parse_malmo_blog(MISSING_LINK_HTML)
    assert plans == []


def test_returns_empty_list_when_no_cards():
    plans = parse_malmo_blog(NO_CARDS_HTML)
    assert plans == []


def test_description_truncated_to_300_chars():
    long_desc = "A" * 400
    html = f"""
    <html><body>
      <div class="event-card">
        <h2 class="event-title">Long Desc Event</h2>
        <p class="event-description">{long_desc}</p>
        <a href="https://www.visitmalmo.com/events/long">More info</a>
      </div>
    </body></html>
    """
    plans = parse_malmo_blog(html)
    assert len(plans) == 1
    assert len(plans[0]["description"]) == 300
