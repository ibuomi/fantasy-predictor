import { useState, useEffect, useCallback } from "react";
import { refreshData, getPredictions } from "./api";
import { refreshMatches, getMatchPredictions, getBacktest, getMyTeam } from "./matchApi";
import PredictionsTable from "./components/PredictionsTable";
import TopScorersChart from "./components/TopScorersChart";
import MatchPredictionsTable from "./components/MatchPredictionsTable";

const POSITIONS = [
  { value: "", label: "All positions" },
  { value: "GK", label: "Goalkeepers" },
  { value: "DEF", label: "Defenders" },
  { value: "MID", label: "Midfielders" },
  { value: "FWD", label: "Forwards" },
];

export default function App() {
  const [tab, setTab] = useState("fantasy"); // "fantasy" | "matches" | "myteam"

  return (
    <div className="container">
      <header>
        <h1>Fantasy Predictor</h1>
        <p>Fantasy points, match scores, corners, and cards — predicted from real historical data.</p>
      </header>

      <div className="tabs">
        <button className={tab === "fantasy" ? "tab active" : "tab"} onClick={() => setTab("fantasy")}>
          Fantasy Points
        </button>
        <button className={tab === "matches" ? "tab active" : "tab"} onClick={() => setTab("matches")}>
          Match Predictions
        </button>
        <button className={tab === "myteam" ? "tab active" : "tab"} onClick={() => setTab("myteam")}>
          My Team
        </button>
      </div>

      {tab === "fantasy" && <FantasyTab />}
      {tab === "matches" && <MatchesTab />}
      {tab === "myteam" && <MyTeamTab />}
    </div>
  );
}

function FantasyTab() {
  const [predictions, setPredictions] = useState([]);
  const [position, setPosition] = useState("");
  const [gameweek, setGameweek] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadPredictions = useCallback(async (pos) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPredictions({ position: pos });
      setPredictions(data);
      if (data.length > 0) setGameweek(data[0].gameweek);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPredictions(position);
  }, [position, loadPredictions]);

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      await refreshData();
      await loadPredictions(position);
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <>
      <div className="toolbar">
        <select value={position} onChange={(e) => setPosition(e.target.value)}>
          {POSITIONS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
        <button className="primary" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? "Refreshing…" : "Refresh data"}
        </button>
        {gameweek && <span className="muted-small">Gameweek {gameweek}</span>}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Top 10 predicted scorers</h3>
        <TopScorersChart predictions={predictions} />
      </div>

      <div className="card">
        {loading ? <div className="empty-state">Loading…</div> : <PredictionsTable predictions={predictions} />}
      </div>
    </>
  );
}

function MatchesTab() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [historyStatus, setHistoryStatus] = useState(null);
  const [backtest, setBacktest] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);

  const loadPredictions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMatchPredictions();
      setPredictions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPredictions();
  }, [loadPredictions]);

  async function handleLoadHistory() {
    setLoadingHistory(true);
    setError(null);
    try {
      const summary = await refreshMatches();
      setHistoryStatus(`Loaded ${summary.matches_added} new matches from the ${summary.season} season.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingHistory(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      await refreshData(); // pulls current fixtures via the FPL API
      await loadPredictions();
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshing(false);
    }
  }

  async function handleRunBacktest() {
    setBacktestLoading(true);
    try {
      const result = await getBacktest();
      setBacktest(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBacktestLoading(false);
    }
  }

  return (
    <>
      <div className="toolbar">
        <button className="primary" onClick={handleLoadHistory} disabled={loadingHistory}>
          {loadingHistory ? "Loading…" : "Load historical data"}
        </button>
        <button className="primary" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? "Refreshing…" : "Refresh fixtures"}
        </button>
      </div>

      {historyStatus && <div className="info-banner">{historyStatus}</div>}
      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Model accuracy (backtest)</h3>
          <button onClick={handleRunBacktest} disabled={backtestLoading}>
            {backtestLoading ? "Running…" : "Run backtest"}
          </button>
        </div>
        {backtest && (
          backtest.matches_evaluated === 0 ? (
            <p className="muted-small">{backtest.note}</p>
          ) : (
            <div className="backtest-grid">
              <div><span className="muted-small">Matches evaluated</span><strong>{backtest.matches_evaluated}</strong></div>
              <div><span className="muted-small">Outcome accuracy</span><strong>{Math.round(backtest.outcome_accuracy * 100)}%</strong></div>
              <div><span className="muted-small">Goals MAE</span><strong>{backtest.goals_mae.home} / {backtest.goals_mae.away}</strong></div>
              <div><span className="muted-small">Corners MAE</span><strong>{backtest.corners_mae.home} / {backtest.corners_mae.away}</strong></div>
              <div><span className="muted-small">Cards MAE</span><strong>{backtest.yellow_cards_mae.home} / {backtest.yellow_cards_mae.away}</strong></div>
            </div>
          )
        )}
        {!backtest && <p className="muted-small">Runs the model against every historical match already loaded — real accuracy, no need to wait for future gameweeks.</p>}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Predicted scores, corners &amp; cards</h3>
        <p className="muted-small" style={{ marginTop: -8 }}>
          Tap a fixture for win/draw/away odds, likely scorelines, form, and head-to-head history.
        </p>
        {loading ? <div className="empty-state">Loading…</div> : <MatchPredictionsTable predictions={predictions} />}
      </div>
    </>
  );
}

function MyTeamTab() {
  const [entryId, setEntryId] = useState("");
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleLoad(e) {
    e.preventDefault();
    if (!entryId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getMyTeam(entryId);
      setTeam(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <form onSubmit={handleLoad} className="toolbar">
        <input
          type="text"
          placeholder="Your FPL team ID (e.g. 123456)"
          value={entryId}
          onChange={(e) => setEntryId(e.target.value)}
          className="team-id-input"
        />
        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Loading…" : "Load my team"}
        </button>
      </form>

      <p className="muted-small">
        Your team ID is the number in the URL when you view "My Team" on the FPL website
        (fantasy.premierleague.com/entry/<strong>123456</strong>/event/7).
      </p>

      {error && <div className="error-banner">{error}</div>}

      {team && (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <h3 style={{ margin: 0 }}>Gameweek {team.gameweek}</h3>
            <span className="muted-small">Total predicted: <strong>{team.total_predicted_points}</strong> pts</span>
          </div>
          <table>
            <thead>
              <tr><th>Player</th><th>Team</th><th>Pos</th><th>Predicted</th><th>Effective</th></tr>
            </thead>
            <tbody>
              {team.players.map((p) => (
                <tr key={p.id}>
                  <td>{p.player_name} {p.is_captain && <span className="badge trained-model">C</span>}</td>
                  <td>
                    <span className="team-cell">
                      {p.team_crest && <img src={p.team_crest} alt="" className="crest" />}
                      {p.team}
                    </span>
                  </td>
                  <td><span className={`badge ${p.position}`}>{p.position}</span></td>
                  <td>{p.predicted_points}</td>
                  <td><strong>{p.effective_points}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
