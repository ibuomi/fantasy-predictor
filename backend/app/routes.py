from flask import Blueprint, jsonify, request

from .models import Player, Prediction, Fixture
from .ingestion import refresh_all_data, refresh_historical_matches
from .fpl_client import FPLClientError
from .match_data_client import MatchDataError
from .match_prediction import predict_match
from .team_crest import crest_url

bp = Blueprint("main", __name__)


@bp.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/api/refresh")
def refresh():
    """Pulls fresh data from the FPL API and regenerates predictions.
    Call this first before /api/players or /api/predictions will return anything."""
    try:
        summary = refresh_all_data()
    except FPLClientError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(summary), 200


@bp.get("/api/players")
def list_players():
    """Optional query params: position=GK|DEF|MID|FWD, team=<name>, sort=points|form|cost"""
    query = Player.query

    position = request.args.get("position")
    if position:
        query = query.filter_by(position=position.upper())

    team = request.args.get("team")
    if team:
        query = query.filter(Player.team_name.ilike(f"%{team}%"))

    sort = request.args.get("sort", "points")
    sort_map = {
        "points": Player.total_points.desc(),
        "form": Player.form.desc(),
        "cost": Player.now_cost.desc(),
    }
    query = query.order_by(sort_map.get(sort, Player.total_points.desc()))

    players = query.all()
    return jsonify([p.to_dict() for p in players])


@bp.get("/api/predictions")
def list_predictions():
    """Optional query params: gameweek=<int> (defaults to the most recent one
    stored), position=GK|DEF|MID|FWD, limit=<int>"""
    gameweek = request.args.get("gameweek", type=int)
    if gameweek is None:
        latest = Prediction.query.order_by(Prediction.gameweek.desc()).first()
        if latest is None:
            return jsonify([])
        gameweek = latest.gameweek

    query = Prediction.query.filter_by(gameweek=gameweek)

    position = request.args.get("position")
    if position:
        query = query.join(Prediction.player).filter(Player.position == position.upper())

    query = query.order_by(Prediction.predicted_points.desc())

    limit = request.args.get("limit", type=int)
    if limit:
        query = query.limit(limit)

    predictions = query.all()
    return jsonify([p.to_dict() for p in predictions])


@bp.get("/api/fixtures")
def list_fixtures():
    gameweek = request.args.get("gameweek", type=int)
    query = Fixture.query
    if gameweek:
        query = query.filter_by(gameweek=gameweek)
    fixtures = query.order_by(Fixture.gameweek).all()
    return jsonify([f.to_dict() for f in fixtures])


@bp.post("/api/refresh-matches")
def refresh_matches():
    """Downloads a season of historical match stats (goals, corners, cards)
    from football-data.co.uk. Query params: season (e.g. '2425'), division
    (default 'E0' for the Premier League)."""
    season = request.args.get("season", "2425")
    division = request.args.get("division", "E0")
    try:
        summary = refresh_historical_matches(season=season, division=division)
    except MatchDataError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(summary), 200


@bp.get("/api/match-predictions")
def match_predictions():
    """Predicted score, corners, and yellow cards for every fixture in a
    gameweek, based on each team's historical stats. Query params: gameweek
    (defaults to the earliest gameweek currently stored in Fixture)."""
    gameweek = request.args.get("gameweek", type=int)
    if gameweek is None:
        first_fixture = Fixture.query.order_by(Fixture.gameweek).first()
        if first_fixture is None:
            return jsonify([])
        gameweek = first_fixture.gameweek

    fixtures = Fixture.query.filter_by(gameweek=gameweek).all()
    predictions = []
    for fx in fixtures:
        pred = predict_match(fx.team_h_name, fx.team_a_name)
        pred["home_crest"] = crest_url(fx.team_h_code)
        pred["away_crest"] = crest_url(fx.team_a_code)
        predictions.append(pred)
    return jsonify(predictions)
