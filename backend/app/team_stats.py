from .models import Match

# A team needs at least this many home (or away) matches on record before we
# trust its average — otherwise we fall back to a league-wide average and
# flag the prediction as low-confidence. Guards against one freak result
# (e.g. a single 5-0 win) dominating a newly-promoted team's "average."
MIN_MATCHES_FOR_CONFIDENCE = 3


def _safe_avg(values: list) -> float:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else 0.0


def get_team_home_stats(team_name: str) -> dict:
    matches = Match.query.filter_by(home_team=team_name).all()
    return {
        "matches_played": len(matches),
        "avg_goals_scored": _safe_avg([m.home_goals for m in matches]),
        "avg_goals_conceded": _safe_avg([m.away_goals for m in matches]),
        "avg_corners_for": _safe_avg([m.home_corners for m in matches]),
        "avg_corners_against": _safe_avg([m.away_corners for m in matches]),
        "avg_yellow_cards": _safe_avg([m.home_yellow for m in matches]),
    }


def get_team_away_stats(team_name: str) -> dict:
    matches = Match.query.filter_by(away_team=team_name).all()
    return {
        "matches_played": len(matches),
        "avg_goals_scored": _safe_avg([m.away_goals for m in matches]),
        "avg_goals_conceded": _safe_avg([m.home_goals for m in matches]),
        "avg_corners_for": _safe_avg([m.away_corners for m in matches]),
        "avg_corners_against": _safe_avg([m.home_corners for m in matches]),
        "avg_yellow_cards": _safe_avg([m.away_yellow for m in matches]),
    }


def get_league_averages() -> dict:
    """League-wide averages, used both as a fallback for data-poor teams and
    as the normalizing baseline in the attack/defense strength model."""
    all_matches = Match.query.all()
    return {
        "avg_home_goals": _safe_avg([m.home_goals for m in all_matches]) or 1.0,
        "avg_away_goals": _safe_avg([m.away_goals for m in all_matches]) or 1.0,
    }


def has_enough_data(team_home_stats: dict, team_away_stats: dict) -> bool:
    return (
        team_home_stats["matches_played"] >= MIN_MATCHES_FOR_CONFIDENCE
        and team_away_stats["matches_played"] >= MIN_MATCHES_FOR_CONFIDENCE
    )
