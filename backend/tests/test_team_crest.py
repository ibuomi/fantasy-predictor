from app.team_crest import crest_url


def test_crest_url_builds_expected_pattern():
    assert crest_url(3) == "https://resources.premierleague.com/premierleague/badges/50/t3.png"


def test_crest_url_handles_missing_code():
    assert crest_url(None) is None
    assert crest_url(0) is None
