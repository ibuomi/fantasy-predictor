"""
Prediction model, v1: a weighted heuristic, not a trained ML model.

predicted_points = (0.5 * points_per_game + 0.5 * recent_form) * difficulty_multiplier

- points_per_game and form both come directly from the FPL API (form is FPL's
  own rolling average over a player's last few gameweeks). Averaging the two
  balances "how good are they all season" against "are they hot right now."
- difficulty_multiplier scales the estimate based on how hard the upcoming
  fixture is, using FPL's own 1 (easiest) - 5 (hardest) difficulty rating:
    FDR 1 -> x1.4      FDR 3 -> x1.2      FDR 5 -> x1.0
  i.e. an easy fixture boosts the estimate, a hard one dampens it.

This is intentionally simple and honestly labeled as a heuristic rather than
a trained model — it's easy to explain, easy to sanity-check, and a natural
"v2" is to replace this function with a scikit-learn regression model trained
on historical gameweek results (see README).
"""

DIFFICULTY_MULTIPLIERS = {
    1: 1.4,
    2: 1.3,
    3: 1.2,
    4: 1.1,
    5: 1.0,
}


def predict_points(points_per_game: float, form: float, fixture_difficulty: int) -> float:
    multiplier = DIFFICULTY_MULTIPLIERS.get(fixture_difficulty, 1.2)
    raw = (0.5 * points_per_game + 0.5 * form) * multiplier
    return round(max(raw, 0.0), 2)
