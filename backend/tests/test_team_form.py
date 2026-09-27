from app import db
from app.models import Match
from app.team_form import get_team_form


def _seed(app):
    with app.app_context():
        db.session.add_all([
            Match(date="2024-01-01", home_team="Arsenal", away_team="Chelsea", home_goals=2, away_goals=1),  # W
            Match(date="2024-01-08", home_team="Everton", away_team="Arsenal", home_goals=1, away_goals=1),  # D (away)
            Match(date="2024-01-15", home_team="Arsenal", away_team="Spurs", home_goals=0, away_goals=2),    # L
        ])
        db.session.commit()


def test_get_team_form_orders_most_recent_first(app):
    _seed(app)
    with app.app_context():
        form = get_team_form("Arsenal")
        assert [f["result"] for f in form] == ["L", "D", "W"]


def test_get_team_form_computes_result_from_teams_perspective(app):
    _seed(app)
    with app.app_context():
        form = get_team_form("Arsenal")
        draw_entry = next(f for f in form if f["opponent"] == "Everton")
        assert draw_entry["was_home"] is False
        assert draw_entry["goals_for"] == 1
        assert draw_entry["goals_against"] == 1


def test_get_team_form_respects_limit(app):
    _seed(app)
    with app.app_context():
        form = get_team_form("Arsenal", limit=2)
        assert len(form) == 2


def test_get_team_form_empty_for_unknown_team(app):
    with app.app_context():
        assert get_team_form("Nonexistent FC") == []
