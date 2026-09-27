FAKE_BOOTSTRAP = {
    "events": [
        {"id": 5, "is_current": True, "is_next": False},
        {"id": 6, "is_current": False, "is_next": True},
    ],
    "teams": [
        {"id": 1, "name": "Arsenal"},
        {"id": 2, "name": "Chelsea"},
    ],
    "elements": [
        {
            "id": 101, "first_name": "Kai", "second_name": "Havertz",
            "team": 1, "element_type": 4, "now_cost": 78,
            "total_points": 60, "points_per_game": "5.0", "form": "6.2",
            "minutes": 900, "selected_by_percent": "15.3",
        },
        {
            "id": 102, "first_name": "Cole", "second_name": "Palmer",
            "team": 2, "element_type": 3, "now_cost": 65,
            "total_points": 80, "points_per_game": "7.1", "form": "8.0",
            "minutes": 950, "selected_by_percent": "40.0",
        },
    ],
}

FAKE_FIXTURES = [
    {
        "id": 501, "event": 6, "team_h": 1, "team_a": 2,
        "team_h_difficulty": 3, "team_a_difficulty": 4,
        "kickoff_time": "2026-10-04T14:00:00Z",
    },
]
