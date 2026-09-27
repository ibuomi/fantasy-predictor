from app.fpl_client import (
    build_team_lookup,
    parse_players,
    parse_fixtures,
    get_current_or_next_gameweek,
)
from tests.fixtures import FAKE_BOOTSTRAP, FAKE_FIXTURES


def test_get_current_or_next_gameweek_prefers_next():
    assert get_current_or_next_gameweek(FAKE_BOOTSTRAP) == 6


def test_get_current_or_next_gameweek_falls_back_to_current():
    data = {"events": [{"id": 5, "is_current": True, "is_next": False}]}
    assert get_current_or_next_gameweek(data) == 5


def test_build_team_lookup():
    lookup = build_team_lookup(FAKE_BOOTSTRAP)
    assert lookup == {1: {"name": "Arsenal", "code": 3}, 2: {"name": "Chelsea", "code": 8}}


def test_parse_players_converts_cost_and_numeric_strings():
    lookup = build_team_lookup(FAKE_BOOTSTRAP)
    players = parse_players(FAKE_BOOTSTRAP, lookup)
    havertz = next(p for p in players if p["id"] == 101)

    assert havertz["team_name"] == "Arsenal"
    assert havertz["team_code"] == 3
    assert havertz["position"] == "FWD"
    assert havertz["now_cost"] == 7.8  # 78 tenths -> 7.8 million
    assert havertz["form"] == 6.2       # string "6.2" -> float


def test_parse_fixtures_skips_unscheduled_and_maps_team_names():
    lookup = build_team_lookup(FAKE_BOOTSTRAP)
    raw = FAKE_FIXTURES + [{"id": 999, "event": None, "team_h": 1, "team_a": 2}]
    fixtures = parse_fixtures(raw, lookup)

    assert len(fixtures) == 1  # the event=None one was skipped
    assert fixtures[0]["team_h_name"] == "Arsenal"
    assert fixtures[0]["team_a_name"] == "Chelsea"
