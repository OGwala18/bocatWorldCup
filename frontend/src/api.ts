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

export type GroupStandingRow = {
  rank: number;
  group: string;
  team: string;
  owner: Owner;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  gf: number;
  ga: number;
  gd: number;
  points: number;
  stageReached: string;
  stagePoints: number;
};

export type AppState = {
  players: Player[];
  teams: Team[];
  groups: Group[];
  groupStandings: Record<string, GroupStandingRow[]>;
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

const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/+$/, "");
const DEBUG_API = import.meta.env.VITE_DEBUG_API !== "false";

function resolveUrl(url: string) {
  if (typeof window === "undefined") return url;
  try {
    return new URL(url, window.location.origin).href;
  } catch {
    return url;
  }
}

function logApi(level: "info" | "warn" | "error", message: string, meta: Record<string, unknown>) {
  if (!DEBUG_API) return;
  console[level](`[Bocat API] ${message}`, meta);
}

logApi("info", "client config", {
  mode: import.meta.env.MODE,
  apiBase: API_BASE || "(empty - using the current website origin)",
});

if (import.meta.env.PROD && !API_BASE) {
  logApi("warn", "VITE_API_BASE is empty in production", {
    problem: "API calls will go to the Netlify frontend domain instead of the FastAPI backend.",
    fix: "Set VITE_API_BASE in Netlify to the deployed backend URL, then redeploy.",
  });
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? "GET";
  const requestUrl = `${API_BASE}${path}`;
  const resolvedRequestUrl = resolveUrl(requestUrl);
  const startedAt = performance.now();

  logApi("info", "request started", {
    method,
    path,
    url: resolvedRequestUrl,
  });

  let response: Response;
  try {
    response = await fetch(requestUrl, init);
  } catch (err) {
    logApi("error", "network request failed", {
      method,
      path,
      url: resolvedRequestUrl,
      error: err instanceof Error ? err.message : String(err),
    });
    throw new Error("Network request failed. Check the backend URL, deployment status, and CORS settings.");
  }

  const durationMs = Math.round(performance.now() - startedAt);
  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.toLowerCase().includes("application/json");
  const responseMeta = {
    method,
    path,
    url: response.url || resolvedRequestUrl,
    status: response.status,
    statusText: response.statusText,
    contentType: contentType || "(missing)",
    durationMs,
  };

  logApi(response.ok ? "info" : "warn", "response received", responseMeta);

  if (!response.ok) {
    if (isJson) {
      const error = await response.json().catch(() => ({ detail: `API error ${response.status}` }));
      logApi("error", "JSON error response", { ...responseMeta, error });
      throw new Error(error.detail ?? `API error ${response.status}`);
    }

    const body = await response.text().catch(() => "");
    logApi("error", "non-JSON error response", {
      ...responseMeta,
      returnedHtml: body.trimStart().startsWith("<"),
      preview: body.slice(0, 180),
    });
    throw new Error(
      `API error ${response.status}. Check that VITE_API_BASE points to the deployed FastAPI backend.`
    );
  }

  if (!isJson) {
    const body = await response.text().catch(() => "");
    const returnedHtml = body.trimStart().startsWith("<");
    logApi("error", "non-JSON success response", {
      ...responseMeta,
      returnedHtml,
      preview: body.slice(0, 180),
    });
    throw new Error(
      returnedHtml
        ? "Backend returned HTML instead of JSON. Set VITE_API_BASE in Netlify to your deployed FastAPI backend URL, then redeploy."
        : "Backend returned a non-JSON response."
    );
  }

  try {
    return await response.json();
  } catch (err) {
    logApi("error", "JSON parse failed", {
      ...responseMeta,
      error: err instanceof Error ? err.message : String(err),
    });
    throw new Error("Backend returned invalid JSON. Check the API response and backend logs.");
  }
}

export async function fetchState(): Promise<AppState> {
  return requestJson<AppState>("/api/state");
}

export async function syncLive(): Promise<AppState> {
  const payload = await requestJson<{ state: AppState }>("/api/live/sync", { method: "POST" });
  return payload.state;
}
