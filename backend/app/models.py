from datetime import datetime, timezone
from . import db
from .team_crest import crest_url

POSITION_MAP = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)  # FPL's own element id
    first_name = db.Column(db.String(100), nullable=False)
    second_name = db.Column(db.String(100), nullable=False)
    team_name = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.Integer, nullable=False)
    team_code = db.Column(db.Integer)  # used to build the official crest image URL
    position = db.Column(db.String(10), nullable=False)  # GK/DEF/MID/FWD
    now_cost = db.Column(db.Float, nullable=False)  # in millions, e.g. 8.5
    total_points = db.Column(db.Integer, default=0)
    points_per_game = db.Column(db.Float, default=0.0)
    form = db.Column(db.Float, default=0.0)  # FPL's own rolling-form metric
    minutes = db.Column(db.Integer, default=0)
    selected_by_percent = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": f"{self.first_name} {self.second_name}",
            "team": self.team_name,
            "team_crest": crest_url(self.team_code),
            "position": self.position,
            "now_cost": self.now_cost,
            "total_points": self.total_points,
            "points_per_game": self.points_per_game,
            "form": self.form,
            "minutes": self.minutes,
            "selected_by_percent": self.selected_by_percent,
        }


class Fixture(db.Model):
    __tablename__ = "fixtures"

    id = db.Column(db.Integer, primary_key=True)  # FPL's own fixture id
    gameweek = db.Column(db.Integer, nullable=False, index=True)
    team_h_id = db.Column(db.Integer, nullable=False)
    team_a_id = db.Column(db.Integer, nullable=False)
    team_h_name = db.Column(db.String(100), nullable=False)
    team_a_name = db.Column(db.String(100), nullable=False)
    team_h_code = db.Column(db.Integer)
    team_a_code = db.Column(db.Integer)
    team_h_difficulty = db.Column(db.Integer, nullable=False)  # FPL's 1 (easy) - 5 (hard) rating
    team_a_difficulty = db.Column(db.Integer, nullable=False)
    kickoff_time = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "gameweek": self.gameweek,
            "home_team": self.team_h_name,
            "away_team": self.team_a_name,
            "home_crest": crest_url(self.team_h_code),
            "away_crest": crest_url(self.team_a_code),
            "home_difficulty": self.team_h_difficulty,
            "away_difficulty": self.team_a_difficulty,
            "kickoff_time": self.kickoff_time,
        }


class Match(db.Model):
    """A single historical match result, imported from football-data.co.uk.
    Team names here are stored in FPL's naming convention (see
    team_name_map.py) so they can be joined against Player/Fixture directly."""
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    home_team = db.Column(db.String(100), nullable=False, index=True)
    away_team = db.Column(db.String(100), nullable=False, index=True)
    home_goals = db.Column(db.Integer, nullable=False)
    away_goals = db.Column(db.Integer, nullable=False)
    home_corners = db.Column(db.Integer)
    away_corners = db.Column(db.Integer)
    home_yellow = db.Column(db.Integer)
    away_yellow = db.Column(db.Integer)
    home_red = db.Column(db.Integer)
    away_red = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint("date", "home_team", "away_team", name="uix_match_unique"),
    )


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    gameweek = db.Column(db.Integer, nullable=False, index=True)
    predicted_points = db.Column(db.Float, nullable=False)
    opponent_team = db.Column(db.String(100))
    fixture_difficulty = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    player = db.relationship("Player")

    def to_dict(self):
        return {
            "id": self.id,
            "player_id": self.player_id,
            "player_name": f"{self.player.first_name} {self.player.second_name}" if self.player else None,
            "team": self.player.team_name if self.player else None,
            "team_crest": crest_url(self.player.team_code) if self.player else None,
            "position": self.player.position if self.player else None,
            "gameweek": self.gameweek,
            "predicted_points": self.predicted_points,
            "opponent_team": self.opponent_team,
            "fixture_difficulty": self.fixture_difficulty,
        }
