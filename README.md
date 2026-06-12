# Bocat World Cup Dashboard

Live-ish friends leaderboard for the 2026 World Cup, using South African time.

## What Is Included

- Fixed 12-player team draw from `Downloads/worldcup teams.jpeg`, 4 teams per player, all 48 World Cup teams used once.
- Top 12 World-Cup-qualified teams are fixed and excluded from the random pool.
- Group fixtures with player matchups such as `South Africa vs Mexico (Onke vs Jarvis)`.
- Color-coded player ownership across assignments and group tables.
- FastAPI backend that computes standings, advancement points, and leaderboard.
- TypeScript React frontend for fixtures, groups, player teams, and leaderboard.
- Live match API adapter configured through environment variables.
- No-key ESPN scoreboard fallback for live-ish scores during matches and final results after matches.

## Scoring

- Round of 32: 1 point
- Round of 16: 2 points
- Quarterfinals: 3 points
- Semifinals: 4 points
- Final: 5 points

The group-stage checkpoint is `2026-06-28 06:00 SAST`, which gives a buffer after the final group fixtures on June 27 in ET.

## Run Locally

Backend:

```powershell
cd C:\Users\GwalaOA\source\repos\bocatWorldCup
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd C:\Users\GwalaOA\source\repos\bocatWorldCup\frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Deploy

This project has two deployable parts:

- Netlify hosts the React frontend in `frontend/`.
- A Python web host, such as Render, hosts the FastAPI backend.

Netlify is configured by `netlify.toml`:

```text
Base directory: frontend
Build command: npm ci && npm run build
Publish directory: frontend/dist
```

This is a Vite app, not a Next.js app. If the Netlify UI has `@netlify/plugin-nextjs` installed, either remove that plugin from the Netlify site settings or keep `NETLIFY_NEXT_PLUGIN_SKIP=true` set so the plugin does not fail the deploy after the Vite build succeeds.

The frontend must know the backend URL. In Netlify, set:

```text
VITE_API_BASE=https://your-backend-url
```

Then redeploy the Netlify site. If `VITE_API_BASE` is missing, the frontend will try to call `/api/state` on the Netlify domain, which will fail because Netlify is not running the FastAPI backend.

If Netlify shows `Unexpected token '<', "<!doctype "... is not valid JSON`, the frontend is receiving Netlify's `index.html` page instead of JSON from the API. Set `VITE_API_BASE` to the deployed backend URL, confirm `/api/state` is being requested from that backend domain in the browser Network tab, and redeploy the Netlify frontend.

The frontend logs API diagnostics to the browser console with the `[Bocat API]` and `[Bocat App]` prefixes. To reduce browser logging later, set this in Netlify:

```text
VITE_DEBUG_API=false
```

Render is configured by `render.yaml`. After the backend is deployed, update these environment values in Render:

```text
CORS_ORIGINS=https://bocatworldcup.netlify.app,http://localhost:5173,http://127.0.0.1:5173
LIVE_MATCHES_API_KEY=your_key_if_you_have_one
```

If you created the Render service manually instead of from `render.yaml`, use these settings:

```text
Runtime: Python 3
Build command: pip install -r requirements.txt
Start command: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

The root `requirements.txt` points Render to `backend/requirements.txt`, and `.python-version` pins the service to Python 3.12.8.

After Render is healthy, set Netlify's frontend API variable to:

```text
VITE_API_BASE=https://bocatworldcup.onrender.com
```

The ESPN scoreboard fallback does not need an API key. The paid football API key is optional and currently only useful if the provider account has 2026 World Cup access.

## Live API

Copy `.env.example` to `.env` and fill in the provider endpoint/key. The current adapter accepts common football API response shapes and maps results back to the local fixture list.

```powershell
LIVE_MATCHES_API_URL=https://your-provider.example/fixtures
LIVE_MATCHES_API_KEY=your-key
LIVE_MATCHES_API_KEY_HEADER=x-apisports-key
```

If the paid live API is unavailable, the backend falls back to ESPN's public FIFA World Cup scoreboard JSON. For the closest practical live-ish results, schedule this every 10 minutes during the tournament:

```powershell
python -m backend.app.automation sync-scores
```

The score poller checks known fixtures from kickoff until `SCORE_POLL_END_MINUTES_AFTER_KICKOFF`, updates in-game scores when ESPN exposes them, and only awards advancement points after a fixture is final. It also keeps retrying old unfinished matches after `POST_MATCH_DELAY_MINUTES` until ESPN marks them completed.

When `ENABLE_SCORE_POLLING=true`, the FastAPI backend also runs the same score poller in the background every `SCORE_POLL_INTERVAL_MINUTES` while the backend process is alive.

Qualification points are mapped per player-owned team. If all four of a player's teams reach the Round of 32, that player gets 4 points. The app awards top-two group qualification as soon as an individual group has all six fixtures final, and it also pulls ESPN's explicit `advanced` standings stat so already-qualified teams can be credited before the full group stage is complete.

Useful local tests:

```powershell
python -m backend.app.automation sync-scores --dry-run --now 2026-06-11T21:05:00+02:00
python -m backend.app.automation sync-postmatch --dry-run --now 2026-06-12T00:30:00+02:00
```

Manual test updates can be sent to:

```text
POST /api/admin/results
```

with a JSON body like:

```json
[
  { "id": "m001", "homeScore": 2, "awayScore": 1, "status": "finished" }
]
```

## Data

Source files live under `data/`. Regenerate them with:

```powershell
python scripts\build_data.py
```

The Excel dashboard copy is saved in Downloads:

```text
C:\Users\GwalaOA\Downloads\bocat World Cup - dashboard.xlsx
```
