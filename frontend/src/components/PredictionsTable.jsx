export default function PredictionsTable({ predictions }) {
  if (predictions.length === 0) {
    return (
      <div className="empty-state">
        No predictions yet — click "Refresh data" above to pull the latest
        players and fixtures and generate predictions.
      </div>
    );
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Player</th>
          <th>Team</th>
          <th>Pos</th>
          <th>Opponent</th>
          <th>Difficulty</th>
          <th>Predicted pts</th>
        </tr>
      </thead>
      <tbody>
        {predictions.map((p) => (
          <tr key={p.id}>
            <td>{p.player_name}</td>
            <td>{p.team}</td>
            <td><span className={`badge ${p.position}`}>{p.position}</span></td>
            <td>{p.opponent_team}</td>
            <td>{p.fixture_difficulty}</td>
            <td><strong>{p.predicted_points}</strong></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
