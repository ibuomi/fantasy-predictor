from app.scoreline_probability import compute_outcome_probabilities, most_likely_scorelines


def test_outcome_probabilities_sum_to_roughly_one():
    probs = compute_outcome_probabilities(1.5, 1.2)
    total = probs["home_win"] + probs["draw"] + probs["away_win"]
    assert abs(total - 1.0) < 0.01


def test_stronger_home_side_favored_to_win():
    probs = compute_outcome_probabilities(2.5, 0.5)
    assert probs["home_win"] > probs["away_win"]
    assert probs["home_win"] > probs["draw"]


def test_evenly_matched_sides_give_closer_probabilities():
    probs = compute_outcome_probabilities(1.3, 1.3)
    assert abs(probs["home_win"] - probs["away_win"]) < 0.05


def test_most_likely_scorelines_returns_requested_count():
    scorelines = most_likely_scorelines(1.5, 1.0, top_n=3)
    assert len(scorelines) == 3
    # sorted descending by probability
    assert scorelines[0]["probability"] >= scorelines[1]["probability"] >= scorelines[2]["probability"]


def test_most_likely_scorelines_have_valid_score_format():
    scorelines = most_likely_scorelines(1.2, 0.8)
    for s in scorelines:
        assert "-" in s["score"]
        home, away = s["score"].split("-")
        assert home.isdigit() and away.isdigit()
