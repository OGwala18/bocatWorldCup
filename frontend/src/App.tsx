import { CalendarClock, RefreshCw, Radio, Trophy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import heroUrl from "./assets/bocat-hero.png";
import { AppState, Fixture, GroupStandingRow, Team, fetchState, syncLive } from "./api";

const MATCH_PAGE_SIZE = 4;

function textColor(hex: string) {
  const raw = hex.replace("#", "");
  const r = parseInt(raw.slice(0, 2), 16);
  const g = parseInt(raw.slice(2, 4), 16);
  const b = parseInt(raw.slice(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.62 ? "#111827" : "#ffffff";
}

type OwnedTeam = Pick<Team, "name" | "owner">;

function TeamPill({ team }: { team: OwnedTeam }) {
  return (
    <span
      className="team-pill"
      style={{ backgroundColor: team.owner.color, color: textColor(team.owner.color) }}
      title={`${team.name} belongs to ${team.owner.playerName}`}
    >
      {team.name}
    </span>
  );
}

function Score({ fixture }: { fixture: Fixture }) {
  if (fixture.homeScore === null || fixture.awayScore === null) {
    return <span className="muted">vs</span>;
  }
  return (
    <span className="score">
      {fixture.homeScore} - {fixture.awayScore}
    </span>
  );
}

function statusMeta(fixture: Fixture) {
  const status = fixture.status.toLowerCase();
  if (status === "live") {
    return { label: fixture.displayClock ? `Live ${fixture.displayClock}` : "Live", tone: "live" };
  }
  if (status === "halftime") {
    return { label: "HT", tone: "live" };
  }
  if (status === "finished" || status === "final" || status === "ft") {
    return { label: "FT", tone: "final" };
  }
  return null;
}

function StatusPill({ fixture }: { fixture: Fixture }) {
  const meta = statusMeta(fixture);
  if (!meta) return null;
  return <span className={`status-pill ${meta.tone}`}>{meta.label}</span>;
}

function fixtureKickoffMs(fixture: Fixture) {
  return new Date(fixture.kickoffSast).getTime();
}

function isFinalFixture(fixture: Fixture) {
  const status = fixture.status.toLowerCase();
  return status === "finished" || status === "final" || status === "ft";
}

function isLiveFixture(fixture: Fixture) {
  const status = fixture.status.toLowerCase();
  return status === "live" || status === "halftime";
}

function StandingsTeam({ row }: { row: GroupStandingRow }) {
  return (
    <div className="standings-team">
      <TeamPill team={{ name: row.team, owner: row.owner }} />
      <span className="standings-owner">{row.owner.playerName}</span>
    </div>
  );
}

function App() {
  const [state, setState] = useState<AppState | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchView, setMatchView] = useState<"fixtures" | "results">("fixtures");
  const [matchPage, setMatchPage] = useState(0);
  const [nowMs, setNowMs] = useState(() => Date.now());

  async function load() {
    setError(null);
    setNowMs(Date.now());
    try {
      const nextState = await fetchState();
      console.info("[Bocat App] state loaded", {
        players: nextState.players.length,
        assignedTeams: nextState.teams.length,
        groupFixtures: nextState.fixtures.length,
        knockoutFixtures: nextState.knockoutFixtures.length,
        groupStandings: Object.keys(nextState.groupStandings ?? {}).length,
        provider: nextState.provider ?? "not connected",
        lastUpdated: nextState.lastUpdated,
      });
      setState(nextState);
    } catch (err) {
      console.error("[Bocat App] failed to load dashboard state", err);
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  async function onSync() {
    setSyncing(true);
    setError(null);
    try {
      console.info("[Bocat App] manual live sync started");
      const nextState = await syncLive();
      console.info("[Bocat App] manual live sync completed", {
        provider: nextState.provider ?? "not connected",
        lastUpdated: nextState.lastUpdated,
      });
      setState(nextState);
    } catch (err) {
      console.error("[Bocat App] manual live sync failed", err);
      setError(err instanceof Error ? err.message : "Live sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    setMatchPage(0);
  }, [matchView]);

  const teamByName = useMemo(() => {
    return new Map(state?.teams.map((team) => [team.name, team]) ?? []);
  }, [state]);

  const groupedStandings = useMemo(() => {
    if (!state) return [];
    return state.groups.map((group) => {
      const fallbackRows = group.teams
        .map((teamName, index) => {
          const team = teamByName.get(teamName);
          if (!team) return null;
          return {
            rank: index + 1,
            group: group.group,
            team: team.name,
            owner: team.owner,
            played: 0,
            won: 0,
            drawn: 0,
            lost: 0,
            gf: 0,
            ga: 0,
            gd: 0,
            points: 0,
            stageReached: team.stageReached,
            stagePoints: team.points,
          };
        })
        .filter(Boolean) as GroupStandingRow[];

      return {
        group: group.group,
        rows: state.groupStandings?.[group.group] ?? fallbackRows,
      };
    });
  }, [state, teamByName]);

  const sortedMatches = useMemo(() => {
    if (!state) return [];
    const all = [...state.fixtures, ...state.knockoutFixtures];
    if (matchView === "results") {
      return all
        .filter((fixture) => isFinalFixture(fixture))
        .sort((a, b) => fixtureKickoffMs(b) - fixtureKickoffMs(a));
    }

    return all
      .filter((fixture) => !isFinalFixture(fixture) && (isLiveFixture(fixture) || fixtureKickoffMs(fixture) >= nowMs))
      .sort((a, b) => fixtureKickoffMs(a) - fixtureKickoffMs(b));
  }, [state, matchView, nowMs]);

  const totalMatchPages = Math.max(1, Math.ceil(sortedMatches.length / MATCH_PAGE_SIZE));
  const activeMatchPage = Math.min(matchPage, totalMatchPages - 1);
  const visibleMatches = sortedMatches.slice(
    activeMatchPage * MATCH_PAGE_SIZE,
    activeMatchPage * MATCH_PAGE_SIZE + MATCH_PAGE_SIZE
  );

  if (loading) {
    return <main className="loading">Loading Bocat...</main>;
  }

  if (!state) {
    return (
      <main className="loading">
        <p>{error ?? "No dashboard data available."}</p>
      </main>
    );
  }

  return (
    <main>
      <section className="hero" style={{ backgroundImage: `linear-gradient(90deg, rgba(8, 20, 43, 0.92), rgba(8, 20, 43, 0.54)), url(${heroUrl})` }}>
        <div className="hero-copy">
          <span className="eyebrow">Africa/Johannesburg time</span>
          <h1>Bocat World Cup</h1>
          <p>Fixed teams, player-color groups, live fixtures, and automatic knockout scoring for the friend league.</p>
        </div>
        <div className="hero-actions">
          <button type="button" onClick={load}>
            <RefreshCw size={18} />
            Refresh
          </button>
          <button type="button" onClick={onSync} disabled={syncing}>
            <Radio size={18} />
            {syncing ? "Syncing" : "Sync Live"}
          </button>
        </div>
      </section>

      {error && <div className="notice">{error}</div>}

      <section className="summary-grid">
        <div>
          <span className="label">Players</span>
          <strong>{state.players.length}</strong>
        </div>
        <div>
          <span className="label">Assigned Teams</span>
          <strong>{state.teams.length}</strong>
        </div>
        <div>
          <span className="label">Group Stage Done</span>
          <strong>{new Date(state.scoring.groupStageCompleteAtSast).toLocaleString("en-ZA")}</strong>
        </div>
        <div>
          <span className="label">Live Source</span>
          <strong>{state.provider ?? "Not connected"}</strong>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel leaderboard">
          <div className="panel-title">
            <Trophy size={19} />
            <h2>Leaderboard</h2>
          </div>
          <div className="leaderboard-list">
            {state.leaderboard.map((row) => (
              <article className="leader-row" key={row.playerId}>
                <span className="rank">{row.rank}</span>
                <span className="avatar" style={{ backgroundColor: row.color, color: textColor(row.color) }}>
                  {row.name.slice(0, 2)}
                </span>
                <div>
                  <strong>{row.name}</strong>
                  <small>{row.teams.join(" · ")}</small>
                </div>
                <b>{row.points}</b>
              </article>
            ))}
          </div>
        </div>

        <div className="panel fixtures">
          <div className="panel-title">
            <CalendarClock size={19} />
            <h2>Fixtures & Results</h2>
          </div>
          <div className="segmented" role="tablist" aria-label="Fixture filter">
            {[
              ["fixtures", "Fixtures"],
              ["results", "Results"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={matchView === value ? "active" : ""}
                onClick={() => setMatchView(value as "fixtures" | "results")}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="fixture-list">
            {visibleMatches.length === 0 && (
              <div className="fixture-empty">
                {matchView === "fixtures" ? "No upcoming fixtures found." : "No finished results found yet."}
              </div>
            )}
            {visibleMatches.map((fixture) => (
              <article className="fixture-row" key={fixture.id}>
                <time>
                  {fixture.dateSast}
                  <span>{fixture.timeSast}</span>
                </time>
                <div className="fixture-main">
                  <strong>
                    {fixture.homeTeam} <Score fixture={fixture} /> {fixture.awayTeam}
                  </strong>
                  <small>
                    {fixture.playerMatchup}
                    <StatusPill fixture={fixture} />
                  </small>
                </div>
                <span className="fixture-stage">{fixture.group ? `Group ${fixture.group}` : fixture.stage}</span>
              </article>
            ))}
          </div>
          <div className="pagination" aria-label={`${matchView} pagination`}>
            <button type="button" onClick={() => setMatchPage((page) => Math.max(page - 1, 0))} disabled={activeMatchPage === 0}>
              Prev
            </button>
            <span>
              Page {activeMatchPage + 1} of {totalMatchPages}
            </span>
            <button
              type="button"
              onClick={() => setMatchPage((page) => Math.min(page + 1, totalMatchPages - 1))}
              disabled={activeMatchPage >= totalMatchPages - 1}
            >
              Next
            </button>
          </div>
        </div>
      </section>

      <section className="panel assignments">
        <div className="panel-title">
          <h2>Player Teams</h2>
        </div>
        <div className="assignment-grid">
          {state.players.map((player) => (
            <article key={player.id} className="player-card" style={{ borderColor: player.color }}>
              <header style={{ backgroundColor: player.color, color: textColor(player.color) }}>{player.name}</header>
              {player.teams.map((teamName) => {
                const team = teamByName.get(teamName);
                return team ? <TeamPill key={teamName} team={team} /> : null;
              })}
            </article>
          ))}
        </div>
      </section>

      <section className="panel groups">
        <div className="panel-title">
          <h2>Group Tables</h2>
        </div>
        <div className="groups-grid">
          {groupedStandings.map((group) => (
            <article className="group-card" key={group.group}>
              <h3>Group {group.group}</h3>
              <div className="standings-table">
                <div className="standings-row standings-head">
                  <span>#</span>
                  <span>Team</span>
                  <span>P</span>
                  <span>W</span>
                  <span>D</span>
                  <span>L</span>
                  <span>GD</span>
                  <span>Pts</span>
                </div>
                {group.rows.map((row) => (
                  <div className="standings-row" key={row.team}>
                    <span className="standings-rank">{row.rank}</span>
                    <StandingsTeam row={row} />
                    <span>{row.played}</span>
                    <span>{row.won}</span>
                    <span>{row.drawn}</span>
                    <span>{row.lost}</span>
                    <span>{row.gd > 0 ? `+${row.gd}` : row.gd}</span>
                    <b>{row.points}</b>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;
