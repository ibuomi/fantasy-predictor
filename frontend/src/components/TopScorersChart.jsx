import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function TopScorersChart({ predictions }) {
  const top10 = [...predictions]
    .sort((a, b) => b.predicted_points - a.predicted_points)
    .slice(0, 10)
    .map((p) => ({ name: p.player_name.split(" ").slice(-1)[0], points: p.predicted_points }));

  if (top10.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={top10} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="points" fill="#1a1a1a" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
