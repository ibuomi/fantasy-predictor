"""
FPL's API and football-data.co.uk name most Premier League clubs identically
("Arsenal", "Chelsea", "Liverpool", ...) but disagree on a handful. This map
covers the well-known mismatches for recent seasons.

LIMITATION: this list needs a small update each season when a newly promoted
club's football-data.co.uk name doesn't match what FPL calls them — check
new entries against a fresh CSV download if predictions are missing for a
promoted side.
"""

# football-data.co.uk name -> FPL name
FOOTBALL_DATA_TO_FPL = {
    "Man United": "Man Utd",
    "Man City": "Man City",
    "Tottenham": "Spurs",
    "Nott'm Forest": "Nott'm Forest",
    "Newcastle": "Newcastle",
    "Wolves": "Wolves",
    "Sheffield United": "Sheffield Utd",
}


def to_fpl_name(football_data_name: str) -> str:
    """Converts a football-data.co.uk team name to FPL's naming, falling back
    to the original name unchanged if there's no known mismatch."""
    return FOOTBALL_DATA_TO_FPL.get(football_data_name, football_data_name)
