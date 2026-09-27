from app.prediction import predict_points


def test_easy_fixture_boosts_prediction():
    easy = predict_points(points_per_game=5.0, form=5.0, fixture_difficulty=1)
    hard = predict_points(points_per_game=5.0, form=5.0, fixture_difficulty=5)
    assert easy > hard


def test_predict_points_formula():
    # (0.5*6 + 0.5*4) * multiplier(fdr=3 -> 1.2) = 5 * 1.2 = 6.0
    result = predict_points(points_per_game=6.0, form=4.0, fixture_difficulty=3)
    assert result == 6.0


def test_predict_points_never_negative():
    result = predict_points(points_per_game=0.0, form=0.0, fixture_difficulty=5)
    assert result == 0.0


def test_unknown_difficulty_falls_back_to_default_multiplier():
    result = predict_points(points_per_game=4.0, form=4.0, fixture_difficulty=99)
    assert result == 4.8  # falls back to the fdr=3 multiplier (1.2)
