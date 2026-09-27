import requests

from .fpl_client import BASE_URL, TIMEOUT, FPLClientError


def fetch_entry_picks(entry_id: int, gameweek: int) -> dict:
    """Fetches one manager's squad for a given gameweek. This is a public
    FPL endpoint — no login needed, same data the FPL website itself shows
    on a manager's public team page. Returns the raw picks list (each with
    an 'element' player id and an 'is_captain' flag)."""
    url = f"{BASE_URL}/entry/{entry_id}/event/{gameweek}/picks/"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 404:
            raise FPLClientError(
                f"No squad found for entry {entry_id} in gameweek {gameweek} — "
                f"check the entry ID (it's the number in the URL when you view "
                f"'My Team' on the FPL website) and that gameweek has started."
            )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise FPLClientError(f"Failed to fetch FPL entry {entry_id}: {exc}") from exc


def parse_picks(picks_data: dict) -> list[dict]:
    """Extracts just what we need from the picks response: which player ids
    are in the squad, who's captain, and who's vice-captain."""
    picks = []
    for pick in picks_data.get("picks", []):
        picks.append({
            "player_id": pick["element"],
            "is_captain": pick.get("is_captain", False),
            "is_vice_captain": pick.get("is_vice_captain", False),
            "position_in_squad": pick.get("position"),  # 1-15; 1-11 are starters
        })
    return picks
