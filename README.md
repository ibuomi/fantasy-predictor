# Fantasy Predictor

Predicts fantasy football points for the upcoming Premier League gameweek, using live data from the official Fantasy Premier League (FPL) public API.

## What it does
1. Pulls every player's stats and the upcoming gameweek's fixtures from the FPL API
2. Combines each player's season-long output (points per game) with their recent form and how hard their next fixture is, into a predicted-points score
3. **Also predicts match scores, corners, and yellow cards** for the same fixtures, using historical results from a second, independent data source (football-data.co.uk)
4. Serves it all through a REST API and a React dashboard with two tabs: Fantasy Points and Match Predictions

## Two data sources, two separate models
This app deliberately pulls from **two unrelated data sources** and runs **two separate prediction models**, not one model doing everything:

| | Fantasy Points | Match Predictions |
|---|---|---|
| Data source | FPL public API (player stats, live) | football-data.co.uk (historical match results) |
| What it predicts | A player's fantasy points next gameweek | Final score, corners, yellow cards for a fixture |
| Model | Weighted heuristic: `0.5×points_per_game + 0.5×form`, scaled by fixture difficulty | Attack/defense-strength Poisson-style model for score; blended historical averages for corners; team's own historical average for cards |

They're joined together only at the very end, through the *fixture list* — both models predict outcomes for the same upcoming gameweek's matches, just using completely different inputs.

## Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, SQLite, `requests`
- **Frontend:** React (Vite), Recharts

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
Runs at `http://localhost:5000`. No API key needed — the FPL endpoint is public.

### Frontend
In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Runs at `http://localhost:5173` and proxies `/api` requests to the Flask backend (see `vite.config.js`).

### First run
Open the app and go to the **Fantasy Points** tab, click **"Refresh data"** — this pulls the latest players/fixtures from the FPL API and generates fantasy-point predictions.

Then switch to the **Match Predictions** tab: click **"Load historical data"** once (downloads a season of past Premier League results from football-data.co.uk — a few hundred KB, takes a couple seconds), then **"Refresh fixtures"** to pull the upcoming gameweek's matchups. Predicted scores, corners, and cards will appear for each fixture.

## API
| Endpoint | Method | Description |
|---|---|---|
| `/api/refresh` | POST | Pulls latest FPL data, regenerates fantasy-point predictions for the next gameweek |
| `/api/players` | GET | List players. Query params: `position`, `team`, `sort` (`points`\|`form`\|`cost`) |
| `/api/predictions` | GET | List fantasy-point predictions. Query params: `gameweek`, `position`, `limit` |
| `/api/fixtures` | GET | List fixtures. Query param: `gameweek` |
| `/api/refresh-matches` | POST | Downloads a season of historical match stats. Query params: `season` (e.g. `2425`), `division` (default `E0`) |
| `/api/match-predictions` | GET | Predicted score/corners/cards per fixture. Query param: `gameweek` |

## Running tests
```bash
cd backend
pytest tests/ -v
```
37 tests across seven files, split cleanly along the two data pipelines:
- `test_fpl_client.py`, `test_prediction.py`, `test_ingestion.py`, `test_routes.py` — the fantasy-points pipeline
- `test_match_data_client.py`, `test_team_stats.py`, `test_match_prediction.py`, `test_match_routes.py` — the match-predictions pipeline

Both external data sources (the FPL API and football-data.co.uk) are mocked in every test using realistic sample response data, so the suite is fast, deterministic, and doesn't depend on live data or the season currently being active.

## Design notes: the prediction models are heuristics, not trained ML — on purpose

**Fantasy points:**
`predicted_points = (0.5 * points_per_game + 0.5 * recent_form) * fixture_difficulty_multiplier`

**Match score** (a simplified attack/defense-strength model — the standard introductory approach to football score prediction):
```
home_attack_strength   = home team's avg home goals scored / league avg home goals
away_defense_weakness  = away team's avg away goals conceded / league avg away goals
expected_home_goals    = home_attack_strength * away_defense_weakness * league_avg_home_goals
```
(mirrored for the away side). This says: score more than your attack strength alone would suggest if the opponent's defense is worse than average, less if it's better than average.

**Corners:** a simpler blended average — a team's own corners-won rate averaged with the opponent's corners-conceded rate. No strength/ratio scaling, deliberately, since corners data is noisier and a simpler model is easier to defend.

**Yellow cards:** the simplest of the three — each team's own historical average, *not* blended with the opponent. Real card counts depend heavily on referee assignment and foul-drawing tendency, neither of which this free dataset captures, so blending would create false precision rather than real signal. This is a deliberate, documented scope cut worth raising if asked about it directly.

All three are deliberately simple:
- Each is explainable in one or two sentences, which matters if you're asked to defend it in an interview
- Each is easy to sanity-check by hand against a few real fixtures
- The honest "v2" for any of them is a model trained on historical data with more features (e.g. gradient-boosted regression using rolling multi-week form, head-to-head history, referee tendencies) — and because each model lives in its own file (`prediction.py`, `match_prediction.py`), upgrading one doesn't require touching the data pipeline or API around it

## Other design notes
- **A confidence flag, not a silent guess.** Every match prediction includes `low_confidence: true` when either team has fewer than 3 historical matches on record (e.g. a newly promoted side early in the season) — rather than quietly returning a number computed from almost nothing.
- **Two independent team-naming conventions, bridged explicitly.** FPL and football-data.co.uk don't always agree on team names ("Man Utd" vs "Man United", "Spurs" vs "Tottenham") — `team_name_map.py` translates between them, and is called out in its own docstring as needing a small update each season when a newly promoted club's name doesn't match.
- **Refresh is idempotent** for both pipelines. Re-running `/api/refresh` or `/api/refresh-matches` doesn't create duplicate rows — players/fixtures are upserted by FPL id, matches are keyed on `(date, home_team, away_team)`, and fantasy predictions for a gameweek are deleted and regenerated each time.
- **Both external clients are isolated from Flask** (`fpl_client.py` and `match_data_client.py` have zero Flask imports), which is what makes it possible to unit-test all the parsing logic completely separately from the web layer.
- **No historical archive of predictions.** The database holds a rolling snapshot, not every gameweek's predictions all season — keeping the schema small. Tracking predicted-vs-actual accuracy over time is a natural next feature.

## Possible extensions
- Track predicted vs. actual results after each gameweek to report real accuracy (MAE for goals, corners; a confusion matrix for match outcome)
- Swap either heuristic for a trained regression model
- "My team" mode: paste your FPL squad and see fantasy predictions for just your 15 players
- Referee-level card tendency data, if a source for it can be found, to make the cards model less naive
- Historical trends per team (last 10 matches) as a form chart
