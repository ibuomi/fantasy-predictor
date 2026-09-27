"""
Team crest images, sourced from the Premier League's own public image CDN
(the same one the official app and website use) — not scraped from any
private endpoint, just a URL built from data the FPL API already gives us.

FPL's bootstrap-static response includes a 'code' field per team (distinct
from its 'id'), which is what these image URLs are keyed on.
"""

CREST_BASE = "https://resources.premierleague.com/premierleague/badges/50"


def crest_url(team_code) -> str | None:
    if not team_code:
        return None
    return f"{CREST_BASE}/t{team_code}.png"
