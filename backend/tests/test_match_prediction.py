from app import db
from app.models import Match
from app.match_prediction import predict_match, _ratio


def test_ratio_handles_zero_baseline():
    assert _ratio(2.0, 0) == 1.0


def test_ratio_normal_case():
    assert _ratio(2.0, 1.0) == 2.0


def _seed_rich_history(app):
    """Gives both Arsenal and Chelsea enough matches to clear the
    confidence threshold and produce a meaningfully different prediction
    than a data-poor team would."""
    with app.app_context():
        for i in range(4):
            db.session.add(Match(
                date=str(i), home_team="Arsenal", away_team="Chelsea",
                home_goals=3, away_goals=0, home_corners=8, away_corners=3,
                home_yellow=1, away_yellow=2,
            ))
        for i in range(4, 8):
            db.session.add(Match(
                date=str(i), home_team="Chelsea", away_team="Arsenal",
                home_goals=0, away_goals=3, home_corners=3, away_corners=8,
                home_yellow=2, away_yellow=1,
            ))
        db.session.commit()


def test_predict_match_favors_stronger_attacking_team(app):
    _seed_rich_history(app)
    with app.app_context():
        result = predict_match("Arsenal", "Chelsea")
        assert result["expected_home_goals"] > result["expected_away_goals"]
        assert result["low_confidence"] is False


def test_predict_match_flags_low_confidence_with_sparse_data(app):
    with app.app_context():
        db.session.add(Match(
            date="1", home_team="Arsenal", away_team="Chelsea",
            home_goals=1, away_goals=1, home_corners=5, away_corners=5,
            home_yellow=1, away_yellow=1,
        ))
        db.session.commit()

        result = predict_match("Arsenal", "Chelsea")
        assert result["low_confidence"] is True


def test_predict_match_includes_all_expected_fields(app):
    _seed_rich_history(app)
    with app.app_context():
        result = predict_match("Arsenal", "Chelsea")
        expected_keys = {
            "home_team", "away_team", "expected_home_goals", "expected_away_goals",
            "predicted_scoreline", "predicted_home_corners", "predicted_away_corners",
            "predicted_home_yellow_cards", "predicted_away_yellow_cards",
            "low_confidence", "home_matches_on_record", "away_matches_on_record",
        }
        assert expected_keys.issubset(result.keys())
