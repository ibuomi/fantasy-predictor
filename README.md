# Fantasy Predictor

Predicts fantasy football points for the upcoming Premier League gameweek, using live data from the official Fantasy Premier League (FPL) public API.

## What it does
1. Pulls every player's stats and the upcoming gameweek's fixtures from the FPL API
2. Combines each player's season-long output (points per game) with their recent form and how hard their next fixture is, into a predicted-points score
3. **Also predicts match scores, corners, and yellow cards** for the same fixtures, using historical results from a second, independent data source (football-data.co.uk)
4. Reports **win/draw/away probabilities and the top 3 likely scorelines** for each fixture, via a real Poisson model — not just one guessed score
5. Lets you **backtest** the match model against every historical match already loaded, for real accuracy numbers without waiting for future gameweeks
6. Can **train a real regression model** on your historical data and use it instead of the heuristic — but only if it actually measurably beats the heuristic first
7. Shows **head-to-head history and recent form** for both teams in a fixture
8. Has a **"My Team" mode** — paste your real FPL team ID and see fantasy predictions filtered to just your squad, with your captain's points doubled
9. Shows real official Premier League team crests throughout the UI
10. Serves it all through a REST API and a React dashboard with three tabs: Fantasy Points, Match Predictions, and My Team

## Two data sources, two separate models
This app deliberately pulls from **two unrelated data sources** and runs **two separate prediction models**, not one model doing everything:

| | Fantasy Points | Match Predictions |
|---|---|---|
| Data source | FPL public API (player stats, live) | football-data.co.uk (historical match results) |
| What it predicts | A player's fantasy points next gameweek | Final score, corners, yellow cards for a fixture |
| Model | Weighted heuristic: `0.5×points_per_game + 0.5×form`, scaled by fixture difficulty | Attack/defense-strength Poisson-style model for score; blended historical averages for corners; team's own historical average for cards |

They're joined together only at the very end, through the *fixture list* — both models predict outcomes for the same upcoming gameweek's matches, just using completely different inputs.

## Team crests: real, official — and deliberately not scraped
Team badges throughout the UI come from the Premier League's own public image CDN (`resources.premierleague.com`), built from a `code` field the FPL API already returns per team.

**What this app does *not* do:** scrape the official Premier League app or website directly. The app doesn't expose a stable public API — what most hobby projects hitting it are actually calling is an undocumented internal endpoint (`footballapi.pulselive.com`) that isn't meant for outside use and can change or start blocking requests with no notice. Rather than build something on that foundation, this app gets real official assets (crests) through data it already has a legitimate, stable source for, and sticks to `football-data.co.uk` (a long-standing, widely-used free dataset) for historical stats. If you want richer official data later (live scores, standings), that would mean taking on the pulselive endpoint's instability deliberately — worth deciding with eyes open rather than defaulting into it.

## Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, SQLite, `requests`, `scipy` (Poisson model), `scikit-learn` + `joblib` (optional trained model)
- **Frontend:** React (Vite), Recharts
- **CI:** GitHub Actions (`.github/workflows/tests.yml`) — runs the full backend test suite and a frontend build on every push
- **Deployment:** Dockerfile + `docker-compose.yml` + a Render Blueprint (`render.yaml`)

## Setup

### The easy way: one command
```bash
./start.sh        # Mac/Linux
```
```powershell
.\start.ps1       # Windows (PowerShell)
```
This creates the Python virtual environment, installs both backend and frontend dependencies, builds the frontend, and starts the server — all in one go, one process, one port. Re-running it is safe (it skips steps already done) and rebuilds the frontend each time, so it picks up any frontend code changes automatically.

Once it's running, open **`http://localhost:5000`** — the UI and the API are both served from that single address, no second terminal window needed.

If PowerShell blocks the script from running:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### The manual way (if you want to understand or customize each step)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cd ../frontend
npm install
npm run build

cd ../backend
python run.py
```
No API key needed anywhere — both the FPL API and football-data.co.uk are public.

**Editing the frontend?** Run `npm run dev` in `frontend/` instead of `npm run build` for hot-reload during development (serves at `http://localhost:5173`, proxying `/api` to the Flask backend — see `vite.config.js`). Switch back to `npm run build` (or just re-run `start.sh`/`start.ps1`) when you're done, so Flask serves the latest version again.

### First run
Open the app (`http://localhost:5000`) and go to the **Fantasy Points** tab, click **"Refresh data"** — this pulls the latest players/fixtures from the FPL API and generates fantasy-point predictions.

Then switch to the **Match Predictions** tab: click **"Load historical data"** once (downloads a season of past Premier League results from football-data.co.uk — a few hundred KB, takes a couple seconds), then **"Refresh fixtures"** to pull the upcoming gameweek's matchups. Predicted scores, corners, and cards will appear for each fixture.

## API
| Endpoint | Method | Description |
|---|---|---|
| `/api/refresh` | POST | Pulls latest FPL data, regenerates fantasy-point predictions for the next gameweek |
| `/api/players` | GET | List players. Query params: `position`, `team`, `sort` (`points`\|`form`\|`cost`) |
| `/api/predictions` | GET | List fantasy-point predictions. Query params: `gameweek`, `position`, `limit` |
| `/api/fixtures` | GET | List fixtures. Query param: `gameweek` |
| `/api/refresh-matches` | POST | Downloads a season of historical match stats. Query params: `season` (e.g. `2425`), `division` (default `E0`) |
| `/api/match-predictions` | GET | Predicted score/corners/cards + win/draw/away odds + likely scorelines per fixture. Query param: `gameweek` |
| `/api/head-to-head` | GET | Recent meetings between two teams. Query params: `team_a`, `team_b` (both required), `limit` |
| `/api/team-form` | GET | A team's last N results. Query params: `team` (required), `limit` |
| `/api/backtest` | GET | Walk-forward accuracy of the match model against all stored historical matches |
| `/api/my-team` | GET | Fantasy predictions filtered to one manager's squad. Query params: `entry_id` (required — your FPL team ID), `gameweek` |

## Backtesting: real accuracy, without waiting for future gameweeks
`/api/backtest` (and the "Run backtest" button on the Match Predictions tab) walks through every historical match already loaded, in chronological order, and — for each one — predicts it using *only the data that would genuinely have been available before it was played*, then compares that prediction to what actually happened. This is a standard walk-forward / expanding-window backtest, and it's the single most valuable feature for actually knowing whether the model works, rather than just asserting it does.

It reports: matches evaluated, goals/corners/cards MAE (home and away separately), and outcome accuracy (win/draw/loss correctness). The more seasons of historical data you've loaded via `/api/refresh-matches`, the more matches get evaluated.

## Optional: training a real model instead of the heuristic
```bash
cd backend
python -m app.train_model
```
This trains a gradient-boosted regression model (scikit-learn) to predict match goals, using the same walk-forward features as the backtest — then evaluates it against the heuristic **on the same held-out matches**, so the comparison is apples-to-apples. It only saves the trained model (to `backend/models/`) if it actually beats the heuristic on both home and away goals; otherwise it tells you so and leaves the heuristic in place. If a trained model is present, `match_prediction.py` uses it automatically and every prediction reports `"goals_model_source": "trained"` or `"heuristic"` so you always know which one produced a given number.

**Scope note:** this trains goals only, not corners or cards — corners and cards are noisier signals where the extra model complexity is less likely to earn its keep. That's a documented decision in `train_model.py`'s docstring, not an oversight.

## Deployment
- **Docker (recommended, works anywhere):**
  ```bash
  docker compose up --build
  ```
  Builds the frontend and runs the whole app (API + UI) in one container at `http://localhost:5000`. The SQLite database persists across restarts in a named Docker volume.
- **Render:** the included `render.yaml` is a one-click Blueprint — push this repo to GitHub, then in Render choose "New Blueprint Instance" and point it at the repo. It builds from the same `Dockerfile`.
- Deploying is the one step in this whole project that genuinely needs your own action (a hosting account) — everything above just makes that step as close to one command as it can be.

## Running tests
```bash
cd backend
pytest tests/ -v
```
76 tests across sixteen files. Both external data sources (the FPL API and football-data.co.uk) are mocked in every test using realistic sample data, so the suite is fast, deterministic, and doesn't depend on live data or the season currently being active. The trained-model tests use synthetic in-memory data with a deliberately learnable pattern, so they don't depend on you having loaded any real historical seasons.

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
- **No historical archive of predictions.** The database holds a rolling snapshot, not every gameweek's predictions all season — keeping the schema small. (Backtesting, above, solves the "does this actually work" question a different way — by validating against the past instead of archiving the future.)
- **Single-process serving.** Flask serves the built React app (`frontend/dist`) directly at `/`, alongside the API at `/api/*`, in one process on one port (see `create_app()`'s catch-all route in `app/__init__.py`). This is why `start.sh`/`start.ps1` only need to run one server, not two — the separate `npm run dev` server is purely a development convenience for hot-reload, not something the app depends on at runtime.
- **One shared walk-forward feature builder, used twice.** `historical_features.py` computes the exact same engineered features for both the backtest and the model trainer, so a trained model sees identical feature definitions at training time and at prediction time — a subtle but important correctness detail (a model trained on one feature definition and served on a slightly different one would silently produce nonsense).
- **Dates are normalized at ingestion, not left as-is.** football-data.co.uk gives dates as `DD/MM/YY` strings; sorting those lexicographically does *not* give chronological order across month boundaries (e.g. "05/09/24" sorts before "12/08/24", which is backwards). `match_data_client.py` converts every date to ISO (`YYYY-MM-DD`) on the way in, which is what makes head-to-head history, team form, and the backtest all sort correctly with a plain string comparison.

## Possible extensions
- Referee-level card tendency data, if a source for it can be found, to make the cards model less naive
- Extend the trained-model approach to corners and cards once there's a real dataset (referee assignments, etc.) that would plausibly help
- Live in-game updates (in-progress match scores) — a materially different, more fragile problem than everything here, since it would mean depending on an undocumented, unstable endpoint rather than the two long-standing free sources this app currently uses
- A proper production database (Postgres) instead of SQLite, if this ever needs concurrent multi-user writes
