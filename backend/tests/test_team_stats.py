from app import db
from app.models import Match
from app.team_stats import get_team_home_stats, get_team_away_stats, get_league_averages, has_enough_data


def _seed_matches(app):
    with app.app_context():
        db.session.add_all([
            Match(date="1", home_team="Arsenal", away_team="Chelsea",
                  home_goals=2, away_goals=1, home_corners=7, away_corners=4,
                  home_yellow=1, away_yellow=2),
            Match(date="2", home_team="Arsenal", away_team="Spurs",
                  home_goals=3, away_goals=0, home_corners=9, away_corners=3,
                  home_yellow=1, away_yellow=1),
            Match(date="3", home_team="Arsenal", away_team="Man Utd",
                  home_goals=1, away_goals=1, home_corners=5, away_corners=6,
                  home_yellow=2, away_yellow=3),
            Match(date="4", home_team="Chelsea", away_team="Arsenal",
                  home_goals=0, away_goals=2, home_corners=3, away_corners=8,
                  home_yellow=3, away_yellow=2),
        ])
        db.session.commit()


def test_get_team_home_stats(app):
    _seed_matches(app)
    with app.app_context():
        stats = get_team_home_stats("Arsenal")
        assert stats["matches_played"] == 3
        assert stats["avg_goals_scored"] == 2.0  # (2+3+1)/3
        assert stats["avg_goals_conceded"] == round((1 + 0 + 1) / 3, 2)


def test_get_team_away_stats(app):
    _seed_matches(app)
    with app.app_context():
        stats = get_team_away_stats("Arsenal")
        assert stats["matches_played"] == 1
        assert stats["avg_goals_scored"] == 2.0
        assert stats["avg_goals_conceded"] == 0.0


def test_get_league_averages(app):
    _seed_matches(app)
    with app.app_context():
        league = get_league_averages()
        assert league["avg_home_goals"] > 0
        assert league["avg_away_goals"] > 0


def test_has_enough_data_respects_minimum_threshold(app):
    _seed_matches(app)
    with app.app_context():
        home_stats = get_team_home_stats("Arsenal")   # 3 matches
        away_stats = get_team_away_stats("Arsenal")    # 1 match
        assert has_enough_data(home_stats, home_stats) is True
        assert has_enough_data(home_stats, away_stats) is False
