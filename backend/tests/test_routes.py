from unittest.mock import patch

from app.fpl_client import FPLClientError
from tests.fixtures import FAKE_BOOTSTRAP, FAKE_FIXTURES


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


@patch("app.routes.refresh_all_data")
def test_refresh_success(mock_refresh, client):
    mock_refresh.return_value = {
        "gameweek": 6, "players_updated": 2, "fixtures_updated": 1, "predictions_created": 2,
    }
    resp = client.post("/api/refresh")
    assert resp.status_code == 200
    assert resp.get_json()["gameweek"] == 6


@patch("app.routes.refresh_all_data")
def test_refresh_handles_fpl_api_failure(mock_refresh, client):
    mock_refresh.side_effect = FPLClientError("FPL API is down")
    resp = client.post("/api/refresh")
    assert resp.status_code == 502
    assert "FPL API is down" in resp.get_json()["error"]


@patch("app.ingestion.fetch_fixtures", return_value=FAKE_FIXTURES)
@patch("app.ingestion.fetch_bootstrap_data", return_value=FAKE_BOOTSTRAP)
def test_players_and_predictions_endpoints_after_real_refresh(mock_bootstrap, mock_fixtures, client):
    refresh_resp = client.post("/api/refresh")
    assert refresh_resp.status_code == 200

    players_resp = client.get("/api/players")
    assert players_resp.status_code == 200
    assert len(players_resp.get_json()) == 2

    predictions_resp = client.get("/api/predictions")
    assert predictions_resp.status_code == 200
    predictions = predictions_resp.get_json()
    assert len(predictions) == 2
    # sorted descending by predicted_points
    assert predictions[0]["predicted_points"] >= predictions[1]["predicted_points"]


@patch("app.ingestion.fetch_fixtures", return_value=FAKE_FIXTURES)
@patch("app.ingestion.fetch_bootstrap_data", return_value=FAKE_BOOTSTRAP)
def test_players_filter_by_position(mock_bootstrap, mock_fixtures, client):
    client.post("/api/refresh")
    resp = client.get("/api/players?position=fwd")
    players = resp.get_json()
    assert len(players) == 1
    assert players[0]["position"] == "FWD"


@patch("app.ingestion.fetch_fixtures", return_value=FAKE_FIXTURES)
@patch("app.ingestion.fetch_bootstrap_data", return_value=FAKE_BOOTSTRAP)
def test_predictions_filtered_by_gameweek(mock_bootstrap, mock_fixtures, client):
    client.post("/api/refresh")
    resp = client.get("/api/predictions?gameweek=6")
    assert len(resp.get_json()) == 2

    resp_empty = client.get("/api/predictions?gameweek=99")
    assert resp_empty.get_json() == []


def test_predictions_empty_before_any_refresh(client):
    resp = client.get("/api/predictions")
    assert resp.status_code == 200
    assert resp.get_json() == []
