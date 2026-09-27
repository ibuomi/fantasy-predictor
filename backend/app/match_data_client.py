import csv
import io
import requests

from .team_name_map import to_fpl_name

BASE_URL = "https://www.football-data.co.uk/mmz4281"
TIMEOUT = 15

# Optional int fields: older seasons and some rows omit corners/cards data,
# so we parse defensively rather than assuming every column is always present.
OPTIONAL_INT_FIELDS = {
    "home_corners": "HC", "away_corners": "AC",
    "home_yellow": "HY", "away_yellow": "AY",
    "home_red": "HR", "away_red": "AR",
}


class MatchDataError(Exception):
    """Raised when the historical match data can't be fetched or parsed."""


def fetch_season_csv(season: str = "2425", division: str = "E0") -> str:
    """Downloads one season's raw CSV text. `season` is football-data.co.uk's
    format, e.g. '2425' for the 2024-25 season. `division` is 'E0' for the
    Premier League (their code for the English top flight)."""
    url = f"{BASE_URL}/{season}/{division}.csv"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        raise MatchDataError(f"Failed to fetch historical match data from {url}: {exc}") from exc


def parse_matches_csv(csv_text: str) -> list[dict]:
    """Parses football-data.co.uk's CSV format into our Match model's fields.
    Skips any row missing a required field (goals or team names) rather than
    crashing the whole import over one malformed row."""
    reader = csv.DictReader(io.StringIO(csv_text))
    matches = []

    for row in reader:
        try:
            home_team = to_fpl_name(row["HomeTeam"].strip())
            away_team = to_fpl_name(row["AwayTeam"].strip())
            match = {
                "date": row.get("Date", "").strip(),
                "home_team": home_team,
                "away_team": away_team,
                "home_goals": int(row["FTHG"]),
                "away_goals": int(row["FTAG"]),
            }
        except (KeyError, ValueError):
            continue  # malformed row (e.g. a blank trailing line) — skip it

        for field_name, csv_column in OPTIONAL_INT_FIELDS.items():
            raw_value = row.get(csv_column, "")
            match[field_name] = int(raw_value) if raw_value not in ("", None) else None

        matches.append(match)

    return matches
