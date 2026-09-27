from unittest.mock import patch

from app import db
from app.models import Fixture
from app.match_data_client import MatchDataError
from tests.match_fixtures import FAKE_MATCH_CSV


@patch("app.routes.refresh_historical_matches")
def test_refresh_matches_success(mock_refresh, client):
    mock_refresh.return_value = {
        "season": "2425", "division": "E0", "matches_parsed": 5, "matches_added": 5,
    }
    resp = client.post("/api/refresh-matches")
    assert resp.status_code == 200
    assert resp.get_json()["matches_added"] == 5


@patch("app.routes.refresh_historical_matches")
def test_refresh_matches_handles_failure(mock_refresh, client):
    mock_refresh.side_effect = MatchDataError("source unreachable")
    resp = client.post("/api/refresh-matches")
    assert resp.status_code == 502
    assert "source unreachable" in resp.get_json()["error"]


@patch("app.ingestion.fetch_season_csv", return_value=FAKE_MATCH_CSV)
def test_refresh_matches_end_to_end_with_real_ingestion(mock_fetch, app, client):
    resp = client.post("/api/refresh-matches?season=2425&division=E0")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["matches_added"] == 5

    # calling it again shouldn't duplicate rows
    resp2 = client.post("/api/refresh-matches?season=2425&division=E0")
    assert resp2.get_json()["matches_added"] == 0


@patch("app.ingestion.fetch_season_csv", return_value=FAKE_MATCH_CSV)
def test_match_predictions_uses_stored_fixtures(mock_fetch, app, client):
    client.post("/api/refresh-matches")

    with app.app_context():
        db.session.add(Fixture(
            id=1, gameweek=7, team_h_id=1, team_a_id=2,
            team_h_name="Arsenal", team_a_name="Chelsea",
            team_h_difficulty=3, team_a_difficulty=3,
        ))
        db.session.commit()

    resp = client.get("/api/match-predictions?gameweek=7")
    assert resp.status_code == 200
    predictions = resp.get_json()
    assert len(predictions) == 1
    assert predictions[0]["home_team"] == "Arsenal"
    assert "predicted_scoreline" in predictions[0]


def test_match_predictions_empty_with_no_fixtures(client):
    resp = client.get("/api/match-predictions?gameweek=999")
    assert resp.get_json() == []
