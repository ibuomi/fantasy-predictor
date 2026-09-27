from app import db
from app.models import Match
from app.head_to_head import get_head_to_head


def _seed(app):
    with app.app_context():
        db.session.add_all([
            Match(date="2023-01-01", home_team="Arsenal", away_team="Chelsea", home_goals=2, away_goals=1),
            Match(date="2023-06-01", home_team="Chelsea", away_team="Arsenal", home_goals=0, away_goals=3),
            Match(date="2024-01-01", home_team="Arsenal", away_team="Spurs", home_goals=1, away_goals=1),  # unrelated
        ])
        db.session.commit()


def test_get_head_to_head_finds_both_directions(app):
    _seed(app)
    with app.app_context():
        results = get_head_to_head("Arsenal", "Chelsea")
        assert len(results) == 2
        # most recent first
        assert results[0]["date"] == "2023-06-01"


def test_get_head_to_head_ignores_unrelated_matches(app):
    _seed(app)
    with app.app_context():
        results = get_head_to_head("Arsenal", "Chelsea")
        teams_involved = {r["home_team"] for r in results} | {r["away_team"] for r in results}
        assert "Spurs" not in teams_involved


def test_get_head_to_head_respects_limit(app):
    _seed(app)
    with app.app_context():
        results = get_head_to_head("Arsenal", "Chelsea", limit=1)
        assert len(results) == 1


def test_get_head_to_head_empty_when_never_played(app):
    with app.app_context():
        assert get_head_to_head("Burnley", "Luton") == []
