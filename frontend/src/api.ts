export type Owner = {
  playerId: string;
  playerName: string;
  color: string;
};

export type Player = {
  id: string;
  name: string;
  color: string;
  teams: string[];
  topTeam: string;
};

export type Team = {
  name: string;
  group: string;
  owner: Owner;
  stageReached: string;
  points: number;
};

export type Fixture = {
  id: string;
  matchNumber: number;
  stage: string;
  group: string | null;
  homeTeam: string;
  awayTeam: string;
  homeOwner: Owner | null;
  awayOwner: Owner | null;
  playerMatchup: string;
  venue: string;
  kickoffSast: string;
  dateSast: string;
  timeSast: string;
  status: string;
  displayClock?: string | null;
  statusDetail?: string | null;
  statusState?: string | null;
  homeScore: number | null;
  awayScore: number | null;
};

export type LeaderboardRow = {
  rank: number;
  playerId: string;
  name: string;
  color: string;
  teams: string[];
  points: number;
  stageCounts: Record<string, number>;
};

export type Group = {
  group: string;
  teams: string[];
};

export type AppState = {
  players: Player[];
  teams: Team[];
  groups: Group[];
  fixtures: Fixture[];
  knockoutFixtures: Fixture[];
  leaderboard: LeaderboardRow[];
  scoring: {
    timezone: string;
    groupStageCompleteAtSast: string;
    pointsByStage: Record<string, number>;
    notes: string[];
    sources: { label: string; url: string }[];
  };
  lastUpdated: string | null;
  provider: string | null;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function fetchState(): Promise<AppState> {
  const response = await fetch(`${API_BASE}/api/state`);
  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }
  return response.json();
}

export async function syncLive(): Promise<AppState> {
  const response = await fetch(`${API_BASE}/api/live/sync`, { method: "POST" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Live sync failed" }));
    throw new Error(error.detail ?? "Live sync failed");
  }
  const payload = await response.json();
  return payload.state;
}
