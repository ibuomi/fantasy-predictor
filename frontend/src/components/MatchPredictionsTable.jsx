import { useState } from "react";
import { getHeadToHead, getTeamForm } from "../matchApi";

export default function MatchPredictionsTable({ predictions }) {
  if (predictions.length === 0) {
    return (
      <div className="empty-state">
        No match predictions yet. Click "Load historical data" once (it downloads a
        season of past results), then "Refresh fixtures" to pull the upcoming
        gameweek, and predictions will appear here.
      </div>
    );
  }

  return (
    <div>
      {predictions.map((p, i) => (
        <FixtureTicket prediction={p} key={i} />
      ))}
    </div>
  );
}

function FixtureTicket({ prediction: p }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  async function toggleExpanded() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (detail) return; // already fetched once
    setLoadingDetail(true);
    try {
      const [h2h, homeForm, awayForm] = await Promise.all([
        getHeadToHead(p.home_team, p.away_team),
        getTeamForm(p.home_team),
        getTeamForm(p.away_team),
      ]);
      setDetail({ h2h, homeForm, awayForm });
    } catch {
      setDetail({ h2h: [], homeForm: [], awayForm: [] });
    } finally {
      setLoadingDetail(false);
    }
  }

  return (
    <div className="fixture-ticket">
      <button className="ticket-clickable" onClick={toggleExpanded}>
        <div className="ticket-main">
          <div className="team-side home">
            {p.home_crest && <img src={p.home_crest} alt="" className="crest-lg" />}
            <span>{p.home_team}</span>
          </div>

          <div className="scoreline">
            {p.predicted_scoreline}
            <div className="xg-note">xG {p.expected_home_goals} – {p.expected_away_goals}</div>
          </div>

          <div className="team-side away">
            {p.away_crest && <img src={p.away_crest} alt="" className="crest-lg" />}
            <span>{p.away_team}</span>
          </div>
        </div>
      </button>

      {p.outcome_probabilities && (
        <div className="odds-bar" title={`Home ${Math.round(p.outcome_probabilities.home_win * 100)}% · Draw ${Math.round(p.outcome_probabilities.draw * 100)}% · Away ${Math.round(p.outcome_probabilities.away_win * 100)}%`}>
          <div className="odds-seg home" style={{ width: `${p.outcome_probabilities.home_win * 100}%` }} />
          <div className="odds-seg draw" style={{ width: `${p.outcome_probabilities.draw * 100}%` }} />
          <div className="odds-seg away" style={{ width: `${p.outcome_probabilities.away_win * 100}%` }} />
        </div>
      )}
      <div className="odds-labels">
        <span>Home {Math.round((p.outcome_probabilities?.home_win || 0) * 100)}%</span>
        <span>Draw {Math.round((p.outcome_probabilities?.draw || 0) * 100)}%</span>
        <span>Away {Math.round((p.outcome_probabilities?.away_win || 0) * 100)}%</span>
      </div>

      <div className="stat-row">
        <span>Corners <strong>{p.predicted_home_corners} – {p.predicted_away_corners}</strong></span>
        <span>Yellow cards <strong>{p.predicted_home_yellow_cards} – {p.predicted_away_yellow_cards}</strong></span>
      </div>

      <div className="confidence-row">
        {p.low_confidence ? (
          <span className="badge low-confidence">Low data</span>
        ) : (
          <span className="badge high-confidence">Good data</span>
        )}
        {p.goals_model_source === "trained" && <span className="badge trained-model">Trained model</span>}
        <button className="expand-toggle" onClick={toggleExpanded}>
          {expanded ? "Hide details" : "Show head-to-head & form"}
        </button>
      </div>

      {expanded && (
        <div className="ticket-detail">
          {loadingDetail ? (
            <div className="muted-small">Loading…</div>
          ) : (
            <>
              <div className="detail-col">
                <h4>Likely scorelines</h4>
                <ul className="scoreline-list">
                  {(p.likely_scorelines || []).map((s, i) => (
                    <li key={i}>{s.score} <span className="muted-small">({Math.round(s.probability * 100)}%)</span></li>
                  ))}
                </ul>
              </div>
              <div className="detail-col">
                <h4>Recent form</h4>
                <FormStrip label={p.home_team} form={detail?.homeForm} />
                <FormStrip label={p.away_team} form={detail?.awayForm} />
              </div>
              <div className="detail-col">
                <h4>Head-to-head</h4>
                {detail?.h2h?.length ? (
                  <ul className="h2h-list">
                    {detail.h2h.map((m, i) => (
                      <li key={i}>{m.home_team} {m.home_goals}-{m.away_goals} {m.away_team}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="muted-small">No previous meetings on record.</span>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function FormStrip({ label, form }) {
  return (
    <div className="form-strip-row">
      <span className="muted-small">{label}</span>
      <span className="form-strip">
        {(form || []).slice().reverse().map((f, i) => (
          <span key={i} className={`form-pill ${f.result}`}>{f.result}</span>
        ))}
      </span>
    </div>
  );
}
