from unittest.mock import patch

from app import db
from app.models import Match, Player, Prediction
from tests.fixtures import FAKE_BOOTSTRAP, FAKE_FIXTURES


def test_head_to_head_requires_both_teams(client):
    resp = client.get("/api/head-to-head?team_a=Arsenal")
    assert resp.status_code == 400


def test_head_to_head_returns_matches(app, client):
    with app.app_context():
        db.session.add(Match(date="2024-01-01", home_team="Arsenal", away_team="Chelsea", home_goals=1, away_goals=1))
        db.session.commit()
    resp = client.get("/api/head-to-head?team_a=Arsenal&team_b=Chelsea")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_team_form_requires_team(client):
    resp = client.get("/api/team-form")
    assert resp.status_code == 400


def test_team_form_returns_results(app, client):
    with app.app_context():
        db.session.add(Match(date="2024-01-01", home_team="Arsenal", away_team="Chelsea", home_goals=2, away_goals=0))
        db.session.commit()
    resp = client.get("/api/team-form?team=Arsenal")
    assert resp.status_code == 200
    assert resp.get_json()[0]["result"] == "W"


def test_backtest_route_returns_note_when_no_data(client):
    resp = client.get("/api/backtest")
    assert resp.status_code == 200
    assert resp.get_json()["matches_evaluated"] == 0


@patch("app.routes.fetch_entry_picks")
def test_my_team_requires_entry_id(mock_fetch, client):
    resp = client.get("/api/my-team")
    assert resp.status_code == 400
    mock_fetch.assert_not_called()


@patch("app.ingestion.fetch_fixtures", return_value=FAKE_FIXTURES)
@patch("app.ingestion.fetch_bootstrap_data", return_value=FAKE_BOOTSTRAP)
@patch("app.routes.fetch_entry_picks")
def test_my_team_filters_to_squad_and_doubles_captain(mock_fetch, mock_bootstrap, mock_fixtures, app, client):
    # Populate real predictions via the normal refresh flow first
    client.post("/api/refresh")

    with app.app_context():
        player_ids = [p.id for p in Player.query.all()]
    mock_fetch.return_value = {
        "picks": [
            {"element": player_ids[0], "position": 1, "is_captain": True, "is_vice_captain": False},
        ]
    }

    resp = client.get("/api/my-team?entry_id=555")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["players"]) == 1
    assert body["players"][0]["is_captain"] is True
    assert body["players"][0]["effective_points"] == body["players"][0]["predicted_points"] * 2


def test_my_team_requires_predictions_to_exist_first(client):
    resp = client.get("/api/my-team?entry_id=555")
    assert resp.status_code == 400
