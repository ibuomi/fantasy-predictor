from app import db
from app.models import Match
from app.backtest import run_backtest


def test_backtest_reports_no_data_note_when_insufficient(app):
    with app.app_context():
        result = run_backtest()
        assert result["matches_evaluated"] == 0
        assert "note" in result


def _seed_consistent_pattern(app):
    """5 meetings of the same fixture, always the same 2-0 home win, with
    identical corners/cards each time. Deterministic enough that once the
    model has 3 prior matches for each side, its prediction should exactly
    match this pattern — useful for asserting precise backtest output."""
    with app.app_context():
        for i in range(5):
            db.session.add(Match(
                date=f"2024-01-{i+1:02d}", home_team="Arsenal", away_team="Chelsea",
                home_goals=2, away_goals=0,
                home_corners=6, away_corners=3,
                home_yellow=1, away_yellow=2,
            ))
        db.session.commit()


def test_backtest_evaluates_once_enough_prior_history_exists(app):
    _seed_consistent_pattern(app)
    with app.app_context():
        result = run_backtest()
        # Matches 1-3 build up history; matches 4 and 5 have enough prior
        # data (3 each) to actually be evaluated.
        assert result["matches_evaluated"] == 2


def test_backtest_perfect_pattern_yields_perfect_outcome_accuracy(app):
    _seed_consistent_pattern(app)
    with app.app_context():
        result = run_backtest()
        assert result["outcome_accuracy"] == 1.0


def test_backtest_low_error_on_consistent_historical_pattern(app):
    _seed_consistent_pattern(app)
    with app.app_context():
        result = run_backtest()
        assert result["goals_mae"]["home"] < 0.5
        assert result["corners_mae"]["home"] == 0.0
        assert result["yellow_cards_mae"]["away"] == 0.0
