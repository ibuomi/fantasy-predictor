from unittest.mock import patch

from app import db
from app.models import Player, Fixture, Prediction
from app.ingestion import refresh_all_data
from tests.fixtures import FAKE_BOOTSTRAP, FAKE_FIXTURES


@patch("app.ingestion.fetch_fixtures", return_value=FAKE_FIXTURES)
@patch("app.ingestion.fetch_bootstrap_data", return_value=FAKE_BOOTSTRAP)
def test_refresh_populates_players_fixtures_and_predictions(mock_bootstrap, mock_fixtures, app):
    with app.app_context():
        summary = refresh_all_data()

        assert summary["gameweek"] == 6
        assert summary["players_updated"] == 2
        assert summary["fixtures_updated"] == 1
        assert summary["predictions_created"] == 2  # both players' teams play that gameweek

        assert Player.query.count() == 2
        assert Fixture.query.count() == 1
        assert Prediction.query.count() == 2

        palmer_prediction = Prediction.query.join(Player).filter(Player.second_name == "Palmer").first()
        assert palmer_prediction.opponent_team == "Arsenal"
        assert palmer_prediction.fixture_difficulty == 4  # Chelsea is the away team


@patch("app.ingestion.fetch_fixtures", return_value=FAKE_FIXTURES)
@patch("app.ingestion.fetch_bootstrap_data", return_value=FAKE_BOOTSTRAP)
def test_refresh_is_idempotent(mock_bootstrap, mock_fixtures, app):
    """Running refresh twice shouldn't create duplicate predictions."""
    with app.app_context():
        refresh_all_data()
        refresh_all_data()
        assert Prediction.query.count() == 2
        assert Player.query.count() == 2  # upserted, not duplicated
