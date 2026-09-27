import requests

BASE_URL = "https://fantasy.premierleague.com/api"
TIMEOUT = 10

POSITION_MAP = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


class FPLClientError(Exception):
    """Raised when the FPL API is unreachable or returns something unusable."""


def fetch_bootstrap_data() -> dict:
    """Fetches the main FPL dataset: all players, all teams, and all gameweeks
    (called 'events' in FPL's API). This one endpoint has almost everything
    we need except fixtures, which come from a separate endpoint below."""
    try:
        resp = requests.get(f"{BASE_URL}/bootstrap-static/", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise FPLClientError(f"Failed to fetch FPL bootstrap data: {exc}") from exc


def fetch_fixtures(gameweek: int | None = None) -> list[dict]:
    """Fetches fixtures, optionally filtered to a single gameweek."""
    params = {"event": gameweek} if gameweek else {}
    try:
        resp = requests.get(f"{BASE_URL}/fixtures/", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise FPLClientError(f"Failed to fetch FPL fixtures: {exc}") from exc


def get_current_or_next_gameweek(bootstrap_data: dict) -> int:
    """FPL marks exactly one 'event' (gameweek) as is_current, and one as
    is_next. We predict for the next gameweek if there is one, otherwise
    fall back to the current one (e.g. during the close season)."""
    events = bootstrap_data.get("events", [])
    for event in events:
        if event.get("is_next"):
            return event["id"]
    for event in events:
        if event.get("is_current"):
            return event["id"]
    raise FPLClientError("Could not determine current/next gameweek from FPL data")


def build_team_lookup(bootstrap_data: dict) -> dict:
    """Maps FPL's numeric team id -> {name, code}. 'code' is a separate id
    FPL uses for image assets (crests) — not the same as 'id'."""
    return {
        team["id"]: {"name": team["name"], "code": team.get("code")}
        for team in bootstrap_data.get("teams", [])
    }


def parse_players(bootstrap_data: dict, team_lookup: dict) -> list[dict]:
    """Turns FPL's raw 'elements' list into the fields our Player model needs."""
    players = []
    for el in bootstrap_data.get("elements", []):
        team = team_lookup.get(el["team"], {})
        players.append({
            "id": el["id"],
            "first_name": el.get("first_name", ""),
            "second_name": el.get("second_name", ""),
            "team_id": el["team"],
            "team_name": team.get("name", "Unknown"),
            "team_code": team.get("code"),
            "position": POSITION_MAP.get(el.get("element_type"), "UNK"),
            "now_cost": el.get("now_cost", 0) / 10,  # FPL stores cost as tenths of a million
            "total_points": el.get("total_points", 0),
            "points_per_game": float(el.get("points_per_game", 0) or 0),
            "form": float(el.get("form", 0) or 0),
            "minutes": el.get("minutes", 0),
            "selected_by_percent": float(el.get("selected_by_percent", 0) or 0),
        })
    return players


def parse_fixtures(raw_fixtures: list[dict], team_lookup: dict) -> list[dict]:
    """Turns FPL's raw fixture list into the fields our Fixture model needs.
    Skips fixtures that don't have a gameweek assigned yet (FPL sometimes
    returns fixtures with event=None before the schedule is finalized)."""
    fixtures = []
    for fx in raw_fixtures:
        if fx.get("event") is None:
            continue
        home = team_lookup.get(fx["team_h"], {})
        away = team_lookup.get(fx["team_a"], {})
        fixtures.append({
            "id": fx["id"],
            "gameweek": fx["event"],
            "team_h_id": fx["team_h"],
            "team_a_id": fx["team_a"],
            "team_h_name": home.get("name", "Unknown"),
            "team_a_name": away.get("name", "Unknown"),
            "team_h_code": home.get("code"),
            "team_a_code": away.get("code"),
            "team_h_difficulty": fx.get("team_h_difficulty", 3),
            "team_a_difficulty": fx.get("team_a_difficulty", 3),
            "kickoff_time": fx.get("kickoff_time"),
        })
    return fixtures
