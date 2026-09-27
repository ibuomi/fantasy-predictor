"""
Trains a gradient-boosted regression model to predict match goals, as the
"v2" upgrade path the README promises for the heuristic model — and, just
as importantly, evaluates it against the heuristic on the same held-out
matches so the comparison is honest rather than assumed.

Scope: this trains goals only (home goals, away goals), not corners or
cards. Goals is where a trained model has the clearest room to improve on
the simple ratio heuristic (more nonlinear interactions between attack and
defense strength); corners and cards are noisier signals where the extra
model complexity is less likely to pay off, so the heuristic is left as-is
for those — a deliberate scope decision, not an oversight.

Usage (from backend/, with the app's venv active and some historical match
data already loaded via /api/refresh-matches):
    python -m app.train_model
This prints a before/after MAE comparison and, if the trained model doesn't
make things worse, saves it to backend/models/*.joblib. match_prediction.py
automatically picks up a saved model file if one exists, and falls back to
the heuristic if not.
"""

import os
import joblib
from sklearn.ensemble import GradientBoostingRegressor

from .historical_features import build_feature_rows

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
HOME_MODEL_PATH = os.path.join(MODEL_DIR, "home_goals_model.joblib")
AWAY_MODEL_PATH = os.path.join(MODEL_DIR, "away_goals_model.joblib")

# Chronological train/test split (not random) — a random split would leak
# "future" matches into training, which would flatter both models equally
# but especially the trained one, since gradient boosting is good at
# memorizing. An 80/20 chronological split keeps the comparison honest.
TRAIN_FRACTION = 0.8


def _mae(predictions: list, actuals: list) -> float:
    errors = [abs(p - a) for p, a in zip(predictions, actuals)]
    return sum(errors) / len(errors) if errors else 0.0


def train_and_evaluate(rows: list[dict] | None = None) -> dict:
    """Trains the models and returns a comparison dict. Doesn't touch disk —
    see train_and_save() for the version that persists the trained models."""
    if rows is None:
        rows = build_feature_rows()

    split_index = int(len(rows) * TRAIN_FRACTION)
    train_rows, test_rows = rows[:split_index], rows[split_index:]

    if len(train_rows) < 20 or len(test_rows) < 5:
        return {
            "trained": False,
            "reason": (
                f"Not enough historical rows to train/test reliably "
                f"({len(rows)} available; need at least 25). Load more "
                f"seasons via /api/refresh-matches."
            ),
        }

    X_train = [r["features"] for r in train_rows]
    X_test = [r["features"] for r in test_rows]

    home_model = GradientBoostingRegressor(random_state=42, n_estimators=100, max_depth=2)
    away_model = GradientBoostingRegressor(random_state=42, n_estimators=100, max_depth=2)
    home_model.fit(X_train, [r["target_home_goals"] for r in train_rows])
    away_model.fit(X_train, [r["target_away_goals"] for r in train_rows])

    trained_home_preds = home_model.predict(X_test)
    trained_away_preds = away_model.predict(X_test)

    heuristic_home_preds = [r["features"][0] * r["features"][1] * r["league_avg_home"] for r in test_rows]
    heuristic_away_preds = [r["features"][2] * r["features"][3] * r["league_avg_away"] for r in test_rows]

    actual_home = [r["target_home_goals"] for r in test_rows]
    actual_away = [r["target_away_goals"] for r in test_rows]

    return {
        "trained": True,
        "test_matches": len(test_rows),
        "heuristic_mae": {
            "home": round(_mae(heuristic_home_preds, actual_home), 3),
            "away": round(_mae(heuristic_away_preds, actual_away), 3),
        },
        "trained_model_mae": {
            "home": round(_mae(list(trained_home_preds), actual_home), 3),
            "away": round(_mae(list(trained_away_preds), actual_away), 3),
        },
        "home_model": home_model,
        "away_model": away_model,
    }


def train_and_save(model_dir: str = MODEL_DIR) -> dict:
    """Trains, evaluates, and — only if the trained model isn't worse than
    the heuristic on both home and away goals — saves it to disk. Returns
    the same comparison dict as train_and_evaluate(), plus 'saved': bool."""
    result = train_and_evaluate()
    if not result["trained"]:
        return {**result, "saved": False}

    improved = (
        result["trained_model_mae"]["home"] <= result["heuristic_mae"]["home"]
        and result["trained_model_mae"]["away"] <= result["heuristic_mae"]["away"]
    )

    if improved:
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(result["home_model"], os.path.join(model_dir, "home_goals_model.joblib"))
        joblib.dump(result["away_model"], os.path.join(model_dir, "away_goals_model.joblib"))

    summary = {k: v for k, v in result.items() if k not in ("home_model", "away_model")}
    summary["saved"] = improved
    return summary


def load_trained_models(model_dir: str = MODEL_DIR):
    """Returns (home_model, away_model) if both trained model files exist,
    else (None, None). Used by match_prediction.py to decide whether to use
    the trained model or fall back to the heuristic."""
    home_path = os.path.join(model_dir, "home_goals_model.joblib")
    away_path = os.path.join(model_dir, "away_goals_model.joblib")
    if os.path.exists(home_path) and os.path.exists(away_path):
        return joblib.load(home_path), joblib.load(away_path)
    return None, None


if __name__ == "__main__":
    from . import create_app  # imported here, not at module level, to avoid a
    # circular import: match_prediction.py imports this module for
    # load_trained_models(), and match_prediction is itself imported by
    # routes.py during create_app()'s own initialization.
    app = create_app()
    with app.app_context():
        result = train_and_save()

    print("\n=== Model training result ===")
    if not result.get("trained"):
        print(result["reason"])
    else:
        print(f"Test matches: {result['test_matches']}")
        print(f"Heuristic MAE   — home: {result['heuristic_mae']['home']}, away: {result['heuristic_mae']['away']}")
        print(f"Trained MAE     — home: {result['trained_model_mae']['home']}, away: {result['trained_model_mae']['away']}")
        if result["saved"]:
            print(f"\nTrained model improved on the heuristic — saved to {MODEL_DIR}/")
        else:
            print("\nTrained model did NOT improve on the heuristic on this data — not saved. "
                  "The app will keep using the heuristic. This can happen with limited "
                  "historical data; try loading more seasons and re-running.")
