from app.match_data_client import parse_matches_csv
from app.team_name_map import to_fpl_name
from tests.match_fixtures import FAKE_MATCH_CSV


def test_to_fpl_name_translates_known_mismatches():
    assert to_fpl_name("Man United") == "Man Utd"
    assert to_fpl_name("Tottenham") == "Spurs"


def test_to_fpl_name_passes_through_unknown_names():
    assert to_fpl_name("Arsenal") == "Arsenal"
    assert to_fpl_name("Some Future Promoted Club") == "Some Future Promoted Club"


def test_parse_matches_csv_translates_team_names():
    matches = parse_matches_csv(FAKE_MATCH_CSV)
    assert len(matches) == 5
    # "Man United" in the raw CSV should come out as "Man Utd" (FPL's name)
    man_utd_match = next(m for m in matches if m["away_team"] == "Man Utd")
    assert man_utd_match["home_team"] == "Arsenal"
    assert man_utd_match["home_goals"] == 1
    assert man_utd_match["away_goals"] == 1


def test_parse_matches_csv_reads_corners_and_cards():
    matches = parse_matches_csv(FAKE_MATCH_CSV)
    first = matches[0]
    assert first["home_corners"] == 7
    assert first["away_corners"] == 4
    assert first["home_yellow"] == 1
    assert first["away_yellow"] == 2


def test_parse_matches_csv_handles_missing_optional_fields():
    csv_text = "Date,HomeTeam,AwayTeam,FTHG,FTAG\n01/01/25,Arsenal,Chelsea,1,0\n"
    matches = parse_matches_csv(csv_text)
    assert len(matches) == 1
    assert matches[0]["home_corners"] is None
