from unittest.mock import patch, MagicMock

from app.fpl_team import fetch_entry_picks, parse_picks
from app.fpl_client import FPLClientError

FAKE_PICKS_RESPONSE = {
    "picks": [
        {"element": 101, "position": 1, "is_captain": False, "is_vice_captain": False},
        {"element": 102, "position": 2, "is_captain": True, "is_vice_captain": False},
        {"element": 103, "position": 3, "is_captain": False, "is_vice_captain": True},
    ]
}


def test_parse_picks_extracts_captain():
    picks = parse_picks(FAKE_PICKS_RESPONSE)
    assert len(picks) == 3
    captain = next(p for p in picks if p["is_captain"])
    assert captain["player_id"] == 102


@patch("app.fpl_team.requests.get")
def test_fetch_entry_picks_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = FAKE_PICKS_RESPONSE
    mock_get.return_value = mock_response

    result = fetch_entry_picks(12345, 7)
    assert result == FAKE_PICKS_RESPONSE


@patch("app.fpl_team.requests.get")
def test_fetch_entry_picks_404_gives_helpful_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    try:
        fetch_entry_picks(99999999, 7)
        assert False, "expected FPLClientError"
    except FPLClientError as exc:
        assert "entry ID" in str(exc)
