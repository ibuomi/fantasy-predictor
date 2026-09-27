import os
import tempfile

from app import db
from app.models import Match
from app.train_model import train_and_evaluate, train_and_save, load_trained_models


def _seed_learnable_pattern(app, n=40):
    """A pattern with real, learnable structure (not just a constant), so
    there's something for a model to actually learn beyond the heuristic:
    Team 'Home' alternates between two very different away opponents whose
    strength genuinely differs, across enough matches for both the 80/20
    split and the MIN_MATCHES_FOR_CONFIDENCE threshold to be satisfied."""
    with app.app_context():
        for i in range(n):
            opponent = "Weak" if i % 2 == 0 else "Strong"
            home_goals = 3 if opponent == "Weak" else 1
            away_goals = 0 if opponent == "Weak" else 2
            db.session.add(Match(
                date=f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
                home_team="Home", away_team=opponent,
                home_goals=home_goals, away_goals=away_goals,
                home_corners=6, away_corners=3, home_yellow=1, away_yellow=2,
            ))
            # also give the opponents some home matches so they clear the
            # MIN_MATCHES_FOR_CONFIDENCE threshold as a home team elsewhere
            db.session.add(Match(
                date=f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
                home_team=opponent, away_team="Filler",
                home_goals=1, away_goals=1,
                home_corners=5, away_corners=5, home_yellow=2, away_yellow=2,
            ))
        db.session.commit()


def test_train_and_evaluate_reports_not_enough_data_when_sparse(app):
    with app.app_context():
        result = train_and_evaluate()
        assert result["trained"] is False


def test_train_and_evaluate_returns_comparable_mae_structure(app):
    _seed_learnable_pattern(app)
    with app.app_context():
        result = train_and_evaluate()
        assert result["trained"] is True
        assert "home" in result["heuristic_mae"]
        assert "home" in result["trained_model_mae"]
        assert result["test_matches"] > 0


def test_train_and_save_only_saves_when_improved(app):
    _seed_learnable_pattern(app)
    with tempfile.TemporaryDirectory() as tmp_dir:
        with app.app_context():
            result = train_and_save(model_dir=tmp_dir)
            if result["saved"]:
                assert os.path.exists(os.path.join(tmp_dir, "home_goals_model.joblib"))
                assert os.path.exists(os.path.join(tmp_dir, "away_goals_model.joblib"))
            else:
                assert not os.path.exists(os.path.join(tmp_dir, "home_goals_model.joblib"))


def test_load_trained_models_returns_none_when_absent():
    with tempfile.TemporaryDirectory() as tmp_dir:
        home_model, away_model = load_trained_models(model_dir=tmp_dir)
        assert home_model is None
        assert away_model is None


def test_load_trained_models_returns_models_when_present(app):
    _seed_learnable_pattern(app)
    with tempfile.TemporaryDirectory() as tmp_dir:
        with app.app_context():
            result = train_and_evaluate()
            assert result["trained"] is True
            import joblib
            joblib.dump(result["home_model"], os.path.join(tmp_dir, "home_goals_model.joblib"))
            joblib.dump(result["away_model"], os.path.join(tmp_dir, "away_goals_model.joblib"))

        home_model, away_model = load_trained_models(model_dir=tmp_dir)
        assert home_model is not None
        assert away_model is not None
        assert home_model.predict([[1.0, 1.0, 1.0, 1.0]]) is not None
