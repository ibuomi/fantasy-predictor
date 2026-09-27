from sqlalchemy import or_
from .models import Match


def get_team_form(team_name: str, limit: int = 5) -> list[dict]:
    """Returns a team's last N matches (home or away), most recent first,
    with the result from that team's own perspective (W/D/L + goal
    difference) so the frontend can render a simple form strip."""
    matches = (
        Match.query.filter(or_(Match.home_team == team_name, Match.away_team == team_name))
        .order_by(Match.date.desc())
        .limit(limit)
        .all()
    )

    form = []
    for m in matches:
        is_home = m.home_team == team_name
        goals_for = m.home_goals if is_home else m.away_goals
        goals_against = m.away_goals if is_home else m.home_goals

        if goals_for > goals_against:
            result = "W"
        elif goals_for < goals_against:
            result = "L"
        else:
            result = "D"

        form.append({
            "date": m.date,
            "opponent": m.away_team if is_home else m.home_team,
            "was_home": is_home,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "result": result,
        })

    return form
