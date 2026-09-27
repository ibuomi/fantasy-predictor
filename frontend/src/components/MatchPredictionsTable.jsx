export default function MatchPredictionsTable({ predictions }) {
  if (predictions.length === 0) {
    return (
      <div className="empty-state">
        No match predictions yet. Click "Load historical data" once (it downloads a
        season of past results), then "Refresh data" to pull fixtures, and predictions
        will appear here.
      </div>
    );
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Fixture</th>
          <th>Predicted score</th>
          <th>Predicted corners</th>
          <th>Predicted yellow cards</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        {predictions.map((p, i) => (
          <tr key={i}>
            <td>{p.home_team} vs {p.away_team}</td>
            <td><strong>{p.predicted_scoreline}</strong>
              <div className="muted-small">(xG {p.expected_home_goals} - {p.expected_away_goals})</div>
            </td>
            <td>{p.predicted_home_corners} - {p.predicted_away_corners}</td>
            <td>{p.predicted_home_yellow_cards} - {p.predicted_away_yellow_cards}</td>
            <td>
              {p.low_confidence ? (
                <span className="badge low-confidence">Low data</span>
              ) : (
                <span className="badge high-confidence">Good data</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
