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
        <div className="fixture-ticket" key={i}>
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
          </div>
        </div>
      ))}
    </div>
  );
}
