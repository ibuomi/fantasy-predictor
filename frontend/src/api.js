const BASE = "/api";

async function handle(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Request failed with status ${res.status}`);
  }
  return data;
}

export async function refreshData() {
  const res = await fetch(`${BASE}/refresh`, { method: "POST" });
  return handle(res);
}

export async function getPredictions({ gameweek, position } = {}) {
  const params = new URLSearchParams();
  if (gameweek) params.set("gameweek", gameweek);
  if (position) params.set("position", position);
  const res = await fetch(`${BASE}/predictions?${params.toString()}`);
  return handle(res);
}

export async function getPlayers({ position } = {}) {
  const params = new URLSearchParams();
  if (position) params.set("position", position);
  const res = await fetch(`${BASE}/players?${params.toString()}`);
  return handle(res);
}
