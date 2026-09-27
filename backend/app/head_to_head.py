from sqlalchemy import or_, and_
from .models import Match


def get_head_to_head(team_a: str, team_b: str, limit: int = 5) -> list[dict]:
    """Returns the most recent meetings between two teams, most recent first.
    Each entry is from a neutral perspective (just states who was home/away),
    not from either team's point of view specifically."""
    matches = (
        Match.query.filter(
            or_(
                and_(Match.home_team == team_a, Match.away_team == team_b),
                and_(Match.home_team == team_b, Match.away_team == team_a),
            )
        )
        .order_by(Match.date.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "date": m.date,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_goals": m.home_goals,
            "away_goals": m.away_goals,
        }
        for m in matches
    ]
