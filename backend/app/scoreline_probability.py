"""
Turns a single expected-goals number for each side into a real probability
distribution over scorelines, using the standard assumption in introductory
football analytics: home and away goals are each approximately Poisson-
distributed and independent of each other. This is a simplification (real
models like Dixon-Coles add a small correlation correction for low-scoring
draws) but is the honest, standard starting point and is easy to explain.
"""

from scipy.stats import poisson

MAX_GOALS = 6  # scorelines beyond this are negligible probability and ignored


def _scoreline_matrix(expected_home_goals: float, expected_away_goals: float):
    """A (MAX_GOALS+1) x (MAX_GOALS+1) matrix where cell [h][a] is the
    probability of that exact home-away scoreline."""
    home_probs = [poisson.pmf(h, max(expected_home_goals, 0.01)) for h in range(MAX_GOALS + 1)]
    away_probs = [poisson.pmf(a, max(expected_away_goals, 0.01)) for a in range(MAX_GOALS + 1)]
    return [[home_probs[h] * away_probs[a] for a in range(MAX_GOALS + 1)] for h in range(MAX_GOALS + 1)]


def compute_outcome_probabilities(expected_home_goals: float, expected_away_goals: float) -> dict:
    """Sums the scoreline matrix into home win / draw / away win probabilities."""
    matrix = _scoreline_matrix(expected_home_goals, expected_away_goals)
    home_win = sum(matrix[h][a] for h in range(MAX_GOALS + 1) for a in range(MAX_GOALS + 1) if h > a)
    draw = sum(matrix[h][a] for h in range(MAX_GOALS + 1) for a in range(MAX_GOALS + 1) if h == a)
    away_win = sum(matrix[h][a] for h in range(MAX_GOALS + 1) for a in range(MAX_GOALS + 1) if h < a)

    total = home_win + draw + away_win  # renormalize (matrix truncates at MAX_GOALS, so this is ~1 already)
    if total == 0:
        return {"home_win": 0.0, "draw": 0.0, "away_win": 0.0}

    return {
        "home_win": round(home_win / total, 3),
        "draw": round(draw / total, 3),
        "away_win": round(away_win / total, 3),
    }


def most_likely_scorelines(expected_home_goals: float, expected_away_goals: float, top_n: int = 3) -> list[dict]:
    """The top N individual scorelines by probability, e.g. [{'score': '2-1', 'probability': 0.14}, ...]."""
    matrix = _scoreline_matrix(expected_home_goals, expected_away_goals)
    scored = [
        {"score": f"{h}-{a}", "probability": round(matrix[h][a], 3)}
        for h in range(MAX_GOALS + 1) for a in range(MAX_GOALS + 1)
    ]
    scored.sort(key=lambda x: x["probability"], reverse=True)
    return scored[:top_n]
