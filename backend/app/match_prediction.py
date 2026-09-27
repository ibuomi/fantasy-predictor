"""
Match prediction, v1: an explainable statistical model, not trained ML —
same philosophy as the fantasy points heuristic elsewhere in this app.

SCORE — a simplified attack/defense "strength" model (the standard
introductory approach to football score prediction, sometimes called a
simplified Dixon-Coles model):
    home_attack_strength = home_team's avg home goals scored / league avg home goals
    away_defense_weakness = away_team's avg away goals conceded / league avg away goals
    expected_home_goals = home_attack_strength * away_defense_weakness * league_avg_home_goals
(and the mirror image for expected away goals). This says: "score more than
a team's attack strength alone if the opponent's defense is worse than
average, score less if the opponent's defense is better than average."

CORNERS — simpler blended average, no ratio/strength scaling:
    predicted_home_corners = (home team's avg corners won at home
                               + away team's avg corners conceded away) / 2

YELLOW CARDS — simplest of the three: each team's own historical average,
not blended with the opponent. Real card counts depend heavily on referee
assignment and foul-drawing tendency, neither of which this free dataset
captures, so blending would create false precision. This is a deliberate,
documented scope cut — worth being upfront about if asked.
"""

from .team_stats import get_team_home_stats, get_team_away_stats, get_league_averages, has_enough_data


def predict_match(home_team: str, away_team: str) -> dict:
    home_stats = get_team_home_stats(home_team)
    away_stats = get_team_away_stats(away_team)
    league = get_league_averages()

    home_attack_strength = _ratio(home_stats["avg_goals_scored"], league["avg_home_goals"])
    away_defense_weakness = _ratio(away_stats["avg_goals_conceded"], league["avg_away_goals"])
    expected_home_goals = round(home_attack_strength * away_defense_weakness * league["avg_home_goals"], 2)

    away_attack_strength = _ratio(away_stats["avg_goals_scored"], league["avg_away_goals"])
    home_defense_weakness = _ratio(home_stats["avg_goals_conceded"], league["avg_home_goals"])
    expected_away_goals = round(away_attack_strength * home_defense_weakness * league["avg_away_goals"], 2)

    predicted_home_corners = round((home_stats["avg_corners_for"] + away_stats["avg_corners_against"]) / 2, 1)
    predicted_away_corners = round((away_stats["avg_corners_for"] + home_stats["avg_corners_against"]) / 2, 1)

    return {
        "home_team": home_team,
        "away_team": away_team,
        "expected_home_goals": expected_home_goals,
        "expected_away_goals": expected_away_goals,
        "predicted_scoreline": f"{round(expected_home_goals)}-{round(expected_away_goals)}",
        "predicted_home_corners": predicted_home_corners,
        "predicted_away_corners": predicted_away_corners,
        "predicted_home_yellow_cards": home_stats["avg_yellow_cards"],
        "predicted_away_yellow_cards": away_stats["avg_yellow_cards"],
        "low_confidence": not has_enough_data(home_stats, away_stats),
        "home_matches_on_record": home_stats["matches_played"],
        "away_matches_on_record": away_stats["matches_played"],
    }


def _ratio(value: float, baseline: float) -> float:
    """Avoids division-by-zero for a team with no recorded matches yet."""
    return value / baseline if baseline else 1.0
