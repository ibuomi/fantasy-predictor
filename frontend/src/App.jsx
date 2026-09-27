import { useState, useEffect, useCallback } from "react";
import { refreshData, getPredictions } from "./api";
import { refreshMatches, getMatchPredictions } from "./matchApi";
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
  const [tab, setTab] = useState("fantasy"); // "fantasy" | "matches"

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
      </div>

      {tab === "fantasy" ? <FantasyTab /> : <MatchesTab />}
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
        <h3 style={{ marginTop: 0 }}>Predicted scores, corners &amp; cards</h3>
        <p className="muted-small" style={{ marginTop: -8 }}>
          Based on each team's historical home/away performance. Predictions marked
          "Low data" mean fewer than 3 recorded matches for one of the teams — treat
          those with extra skepticism.
        </p>
        {loading ? <div className="empty-state">Loading…</div> : <MatchPredictionsTable predictions={predictions} />}
      </div>
    </>
  );
}
