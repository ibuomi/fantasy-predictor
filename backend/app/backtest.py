"""
Backtests the heuristic match prediction model against the historical
matches already stored (from football-data.co.uk), so you get real accuracy
numbers without waiting for future gameweeks to be played.

Uses the same walk-forward feature rows as the model trainer
(historical_features.py) — see that module's docstring for the method.
This means the heuristic's backtest numbers here and a trained model's
numbers (train_model.py) are directly, fairly comparable: same rows, same
train/test boundary concerns, same targets.
"""

from .historical_features import build_feature_rows
from .team_stats import MIN_MATCHES_FOR_CONFIDENCE


def _avg(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def run_backtest() -> dict:
    rows = build_feature_rows()

    if not rows:
        return {
            "matches_evaluated": 0,
            "note": (
                f"Not enough historical data yet — each team needs at least "
                f"{MIN_MATCHES_FOR_CONFIDENCE} prior home and away matches on "
                f"record before backtesting can begin. Load more seasons via "
                f"/api/refresh-matches with a different `season` param."
            ),
        }

    goal_errors_home, goal_errors_away = [], []
    corner_errors_home, corner_errors_away = [], []
    card_errors_home, card_errors_away = [], []
    outcomes_correct = 0

    for row in rows:
        home_attack_ratio, away_defense_ratio, away_attack_ratio, home_defense_ratio = row["features"]

        expected_home_goals = home_attack_ratio * away_defense_ratio * row["league_avg_home"]
        expected_away_goals = away_attack_ratio * home_defense_ratio * row["league_avg_away"]

        goal_errors_home.append(abs(expected_home_goals - row["target_home_goals"]))
        goal_errors_away.append(abs(expected_away_goals - row["target_away_goals"]))
        corner_errors_home.append(abs(row["expected_home_corners"] - row["target_home_corners"]))
        corner_errors_away.append(abs(row["expected_away_corners"] - row["target_away_corners"]))
        card_errors_home.append(abs(row["expected_home_cards"] - row["target_home_cards"]))
        card_errors_away.append(abs(row["expected_away_cards"] - row["target_away_cards"]))

        predicted_outcome = _outcome(expected_home_goals, expected_away_goals)
        actual_outcome = _outcome(row["target_home_goals"], row["target_away_goals"])
        if predicted_outcome == actual_outcome:
            outcomes_correct += 1

    return {
        "matches_evaluated": len(rows),
        "goals_mae": {"home": round(_avg(goal_errors_home), 2), "away": round(_avg(goal_errors_away), 2)},
        "corners_mae": {"home": round(_avg(corner_errors_home), 2), "away": round(_avg(corner_errors_away), 2)},
        "yellow_cards_mae": {"home": round(_avg(card_errors_home), 2), "away": round(_avg(card_errors_away), 2)},
        "outcome_accuracy": round(outcomes_correct / len(rows), 3),
    }


def _outcome(home_goals: float, away_goals: float) -> str:
    if home_goals > away_goals:
        return "H"
    if home_goals < away_goals:
        return "A"
    return "D"
