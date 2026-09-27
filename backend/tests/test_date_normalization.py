from app.match_data_client import _normalize_date, parse_matches_csv


def test_normalize_date_two_digit_year():
    assert _normalize_date("15/08/24") == "2024-08-15"


def test_normalize_date_four_digit_year():
    assert _normalize_date("15/08/2024") == "2024-08-15"


def test_normalize_date_unparseable_falls_back_unchanged():
    assert _normalize_date("not-a-date") == "not-a-date"


def test_parse_matches_csv_sorts_chronologically_after_normalization():
    # Deliberately out of order in the raw CSV, and spanning a month
    # boundary, which is exactly the case naive string-sorting gets wrong.
    csv_text = (
        "Date,HomeTeam,AwayTeam,FTHG,FTAG\n"
        "05/09/24,Arsenal,Chelsea,1,0\n"
        "12/08/24,Chelsea,Arsenal,2,2\n"
    )
    matches = parse_matches_csv(csv_text)
    dates = sorted(m["date"] for m in matches)
    assert dates == ["2024-08-12", "2024-09-05"]
