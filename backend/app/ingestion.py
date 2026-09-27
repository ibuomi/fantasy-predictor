from . import db
from .models import Player, Fixture, Prediction, Match
from .fpl_client import (
    fetch_bootstrap_data,
    fetch_fixtures,
    build_team_lookup,
    parse_players,
    parse_fixtures,
    get_current_or_next_gameweek,
)
from .prediction import predict_points
from .match_data_client import fetch_season_csv, parse_matches_csv


def refresh_all_data() -> dict:
    """Pulls the latest players + fixtures from the FPL API, stores them,
    and regenerates predictions for the upcoming gameweek. Returns a small
    summary dict so the API caller (and the frontend) can show what happened."""
    bootstrap_data = fetch_bootstrap_data()
    team_lookup = build_team_lookup(bootstrap_data)
    gameweek = get_current_or_next_gameweek(bootstrap_data)

    players_data = parse_players(bootstrap_data, team_lookup)
    _upsert_players(players_data)

    raw_fixtures = fetch_fixtures(gameweek=gameweek)
    fixtures_data = parse_fixtures(raw_fixtures, team_lookup)
    _upsert_fixtures(fixtures_data)

    predictions_created = _generate_predictions(gameweek)

    return {
        "gameweek": gameweek,
        "players_updated": len(players_data),
        "fixtures_updated": len(fixtures_data),
        "predictions_created": predictions_created,
    }


def _upsert_players(players_data: list[dict]) -> None:
    for data in players_data:
        player = db.session.get(Player, data["id"])
        if player is None:
            player = Player(id=data["id"])
            db.session.add(player)
        for key, value in data.items():
            setattr(player, key, value)
    db.session.commit()


def _upsert_fixtures(fixtures_data: list[dict]) -> None:
    for data in fixtures_data:
        fixture = db.session.get(Fixture, data["id"])
        if fixture is None:
            fixture = Fixture(id=data["id"])
            db.session.add(fixture)
        for key, value in data.items():
            setattr(fixture, key, value)
    db.session.commit()


def _generate_predictions(gameweek: int) -> int:
    """Builds a fresh set of predictions for the given gameweek, replacing
    any existing predictions for that gameweek (so re-running /api/refresh
    is safe and idempotent rather than piling up duplicates)."""
    Prediction.query.filter_by(gameweek=gameweek).delete()

    fixtures = Fixture.query.filter_by(gameweek=gameweek).all()
    # Map team_id -> (opponent_name, this_team's_difficulty) for quick lookup per player
    team_fixture_map = {}
    for fx in fixtures:
        team_fixture_map[fx.team_h_id] = (fx.team_a_name, fx.team_h_difficulty)
        team_fixture_map[fx.team_a_id] = (fx.team_h_name, fx.team_a_difficulty)

    players = Player.query.all()
    created = 0
    for player in players:
        match = team_fixture_map.get(player.team_id)
        if match is None:
            continue  # team has no fixture this gameweek (e.g. a bye week)
        opponent_name, difficulty = match

        points = predict_points(player.points_per_game, player.form, difficulty)
        db.session.add(Prediction(
            player_id=player.id,
            gameweek=gameweek,
            predicted_points=points,
            opponent_team=opponent_name,
            fixture_difficulty=difficulty,
        ))
        created += 1

    db.session.commit()
    return created


def refresh_historical_matches(season: str = "2425", division: str = "E0") -> dict:
    """Downloads one season of historical results/stats and stores any
    matches not already on record. Safe to call repeatedly — matches are
    keyed on (date, home_team, away_team), so re-running just fills in any
    new results rather than duplicating existing ones."""
    csv_text = fetch_season_csv(season=season, division=division)
    matches_data = parse_matches_csv(csv_text)

    added = 0
    for data in matches_data:
        exists = Match.query.filter_by(
            date=data["date"], home_team=data["home_team"], away_team=data["away_team"]
        ).first()
        if exists is None:
            db.session.add(Match(**data))
            added += 1

    db.session.commit()
    return {"season": season, "division": division, "matches_parsed": len(matches_data), "matches_added": added}
