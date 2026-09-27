"""
Builds the same walk-forward engineered features used by both the heuristic
backtest (backtest.py) and the trained-model trainer (train_model.py) — kept
in one place so the two can be compared on identical footing, and so a
trained model sees the same feature definitions at training time as at
prediction time (see match_prediction.py).

Each row's features are computed using ONLY matches strictly before that
row's date (the standard walk-forward / expanding-window approach), so
there's no leakage of future information into a "historical" prediction.
"""

from .models import Match
from .team_stats import MIN_MATCHES_FOR_CONFIDENCE


def _avg(values: list) -> float:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0


def _ratio(value: float, baseline: float) -> float:
    return value / baseline if baseline else 1.0


def build_feature_rows() -> list[dict]:
    """Returns one dict per historical match that had enough prior data,
    each with a 'features' vector (fixed order — see FEATURE_NAMES) and the
    actual results as targets."""
    matches = Match.query.order_by(Match.date.asc()).all()

    home_history, away_history = {}, {}
    league_home_goals, league_away_goals = [], []
    rows = []

    for m in matches:
        home_prior = home_history.get(m.home_team, [])
        away_prior = away_history.get(m.away_team, [])

        enough_data = (
            len(home_prior) >= MIN_MATCHES_FOR_CONFIDENCE
            and len(away_prior) >= MIN_MATCHES_FOR_CONFIDENCE
            and league_home_goals and league_away_goals
        )

        if enough_data:
            league_avg_home = _avg(league_home_goals)
            league_avg_away = _avg(league_away_goals)

            home_attack_ratio = _ratio(_avg([h["goals_for"] for h in home_prior]), league_avg_home)
            away_defense_ratio = _ratio(_avg([a["goals_against"] for a in away_prior]), league_avg_away)
            away_attack_ratio = _ratio(_avg([a["goals_for"] for a in away_prior]), league_avg_away)
            home_defense_ratio = _ratio(_avg([h["goals_against"] for h in home_prior]), league_avg_home)

            rows.append({
                "date": m.date,
                "home_team": m.home_team,
                "away_team": m.away_team,
                "features": [home_attack_ratio, away_defense_ratio, away_attack_ratio, home_defense_ratio],
                "league_avg_home": league_avg_home,
                "league_avg_away": league_avg_away,
                "expected_home_corners": (_avg([h["corners_for"] for h in home_prior]) + _avg([a["corners_against"] for a in away_prior])) / 2,
                "expected_away_corners": (_avg([a["corners_for"] for a in away_prior]) + _avg([h["corners_against"] for h in home_prior])) / 2,
                "expected_home_cards": _avg([h["yellow"] for h in home_prior]),
                "expected_away_cards": _avg([a["yellow"] for a in away_prior]),
                "target_home_goals": m.home_goals,
                "target_away_goals": m.away_goals,
                "target_home_corners": m.home_corners or 0,
                "target_away_corners": m.away_corners or 0,
                "target_home_cards": m.home_yellow or 0,
                "target_away_cards": m.away_yellow or 0,
            })

        home_history.setdefault(m.home_team, []).append({
            "goals_for": m.home_goals, "goals_against": m.away_goals,
            "corners_for": m.home_corners, "corners_against": m.away_corners,
            "yellow": m.home_yellow,
        })
        away_history.setdefault(m.away_team, []).append({
            "goals_for": m.away_goals, "goals_against": m.home_goals,
            "corners_for": m.away_corners, "corners_against": m.home_corners,
            "yellow": m.away_yellow,
        })
        league_home_goals.append(m.home_goals)
        league_away_goals.append(m.away_goals)

    return rows


FEATURE_NAMES = ["home_attack_ratio", "away_defense_ratio", "away_attack_ratio", "home_defense_ratio"]
