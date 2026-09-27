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

export async function getHeadToHead(teamA, teamB, limit = 5) {
  const res = await fetch(`${BASE}/head-to-head?team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}&limit=${limit}`);
  return handle(res);
}

export async function getTeamForm(team, limit = 5) {
  const res = await fetch(`${BASE}/team-form?team=${encodeURIComponent(team)}&limit=${limit}`);
  return handle(res);
}

export async function getBacktest() {
  const res = await fetch(`${BASE}/backtest`);
  return handle(res);
}

export async function getMyTeam(entryId, gameweek) {
  const params = new URLSearchParams({ entry_id: entryId });
  if (gameweek) params.set("gameweek", gameweek);
  const res = await fetch(`${BASE}/my-team?${params.toString()}`);
  return handle(res);
}
