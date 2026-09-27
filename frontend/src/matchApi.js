const BASE = "/api";

async function handle(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Request failed with status ${res.status}`);
  }
  return data;
}

export async function refreshMatches(season = "2425", division = "E0") {
  const res = await fetch(`${BASE}/refresh-matches?season=${season}&division=${division}`, {
    method: "POST",
  });
  return handle(res);
}

export async function getMatchPredictions(gameweek) {
  const params = gameweek ? `?gameweek=${gameweek}` : "";
  const res = await fetch(`${BASE}/match-predictions${params}`);
  return handle(res);
}
