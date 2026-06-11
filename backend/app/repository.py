from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DATA_DIR, settings


STAGE_POINTS = {
    "group": 0,
    "round_of_32": 1,
    "round_of_16": 2,
    "quarterfinal": 3,
    "semifinal": 4,
    "final": 5,
}

STAGE_ORDER = {stage: index for index, stage in enumerate(STAGE_POINTS)}

KNOCKOUT_WINNER_STAGE = {
    "Round of 32": "round_of_16",
    "Round of 16": "quarterfinal",
    "Quarterfinal": "semifinal",
    "Semifinal": "final",
}


FINAL_STATUSES = {"finished", "final", "ft", "full time", "status_final", "status_full_time"}


def is_final_fixture(fixture: dict[str, Any]) -> bool:
    status = str(fixture.get("status") or "").strip().lower().replace("-", "_").replace(" ", "_")
    return status in FINAL_STATUSES


def best_stage(*stages: str | None) -> str:
    known = [stage for stage in stages if stage in STAGE_ORDER]
    if not known:
        return "group"
    return max(known, key=lambda stage: STAGE_ORDER[stage])


def merge_advancements(*sources: dict[str, str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for source in sources:
        for team, stage in source.items():
            merged[team] = best_stage(merged.get(team), stage)
    return merged


def load_json(filename: str) -> Any:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def save_json(filename: str, payload: Any) -> None:
    path = DATA_DIR / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_live_state() -> dict[str, Any]:
    path = settings.live_state_path
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    default_state = load_json("live_state.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(default_state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return default_state


def save_live_state(payload: dict[str, Any]) -> None:
    path = settings.live_state_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_static() -> dict[str, Any]:
    return {
        "players": load_json("players.json"),
        "teams": load_json("teams.json"),
        "groups": load_json("groups.json"),
        "fixtures": load_json("fixtures.json"),
        "knockoutFixtures": load_json("knockout_fixtures.json"),
        "scoring": load_json("scoring.json"),
        "liveState": load_live_state(),
    }


def team_owner_map(players: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    owners = {}
    for player in players:
        for team in player["teams"]:
            owners[team] = {
                "playerId": player["id"],
                "playerName": player["name"],
                "color": player["color"],
            }
    return owners


def merge_live_fixture(base: dict[str, Any], live_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    live = live_by_id.get(base["id"], {})
    merged = {**base, **live}
    if live.get("homeScore") is not None or live.get("awayScore") is not None:
        merged["homeScore"] = live.get("homeScore")
        merged["awayScore"] = live.get("awayScore")
    return merged


def merged_fixtures() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    state = load_static()
    live_state = state["liveState"]
    live_by_id = {fixture["id"]: fixture for fixture in live_state.get("fixtures", [])}
    group_fixtures = [merge_live_fixture(fixture, live_by_id) for fixture in state["fixtures"]]
    knockout_fixtures = [merge_live_fixture(fixture, live_by_id) for fixture in state["knockoutFixtures"]]
    return group_fixtures, knockout_fixtures, live_state


def fixture_winner(fixture: dict[str, Any]) -> str | None:
    if not is_final_fixture(fixture):
        return None
    home_score = fixture.get("homeScore")
    away_score = fixture.get("awayScore")
    if home_score is None or away_score is None or home_score == away_score:
        return None
    return fixture["homeTeam"] if home_score > away_score else fixture["awayTeam"]


def compute_group_standings(fixtures: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    standings: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for fixture in fixtures:
        group = fixture["group"]
        for side in ("homeTeam", "awayTeam"):
            team = fixture[side]
            standings[group].setdefault(
                team,
                {"team": team, "played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "gd": 0, "points": 0},
            )

        home_score = fixture.get("homeScore")
        away_score = fixture.get("awayScore")
        if home_score is None or away_score is None or not is_final_fixture(fixture):
            continue

        home = standings[group][fixture["homeTeam"]]
        away = standings[group][fixture["awayTeam"]]
        home["played"] += 1
        away["played"] += 1
        home["gf"] += home_score
        home["ga"] += away_score
        away["gf"] += away_score
        away["ga"] += home_score
        home["gd"] = home["gf"] - home["ga"]
        away["gd"] = away["gf"] - away["ga"]
        if home_score > away_score:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
        elif away_score > home_score:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3
        else:
            home["drawn"] += 1
            away["drawn"] += 1
            home["points"] += 1
            away["points"] += 1

    return {
        group: sorted(rows.values(), key=lambda row: (-row["points"], -row["gd"], -row["gf"], row["team"]))
        for group, rows in standings.items()
    }


def automatic_advancements(group_fixtures: list[dict[str, Any]], knockout_fixtures: list[dict[str, Any]]) -> dict[str, str]:
    stage_by_team: dict[str, str] = {}
    standings = compute_group_standings(group_fixtures)
    completed_group_count = 0

    for group, rows in standings.items():
        group_complete = rows and all(row["played"] == 3 for row in rows)
        if group_complete:
            completed_group_count += 1
            for row in rows[:2]:
                stage_by_team[row["team"]] = "round_of_32"

    if completed_group_count == 12:
        third_place = []
        for group, rows in standings.items():
            if len(rows) >= 3:
                third_place.append({**rows[2], "group": group})
        for row in sorted(third_place, key=lambda item: (-item["points"], -item["gd"], -item["gf"], item["group"]))[:8]:
            stage_by_team[row["team"]] = "round_of_32"

    for fixture in knockout_fixtures:
        winner = fixture_winner(fixture)
        next_stage = KNOCKOUT_WINNER_STAGE.get(fixture["stage"])
        if winner and next_stage and winner not in {"TBD", "Best Third-Place"}:
            stage_by_team[winner] = best_stage(stage_by_team.get(winner), next_stage)

    return stage_by_team


def build_state() -> dict[str, Any]:
    static = load_static()
    players = static["players"]
    teams = static["teams"]
    group_fixtures, knockout_fixtures, live_state = merged_fixtures()
    computed_advancements = automatic_advancements(group_fixtures, knockout_fixtures)
    manual_advancements = live_state.get("advancements", {})
    advancements = merge_advancements(computed_advancements, manual_advancements)

    enriched_teams = []
    for team in teams:
        stage = advancements.get(team["name"], team.get("stageReached", "group"))
        enriched_teams.append(
            {
                **team,
                "stageReached": stage,
                "points": STAGE_POINTS.get(stage, 0),
            }
        )

    points_by_player = defaultdict(int)
    stage_counts = defaultdict(lambda: defaultdict(int))
    team_lookup = {team["name"]: team for team in enriched_teams}
    for player in players:
        for team_name in player["teams"]:
            team = team_lookup[team_name]
            points_by_player[player["id"]] += team["points"]
            for stage, points in STAGE_POINTS.items():
                if team["points"] >= points and points > 0:
                    stage_counts[player["id"]][stage] += 1

    leaderboard = []
    for player in players:
        leaderboard.append(
            {
                "playerId": player["id"],
                "name": player["name"],
                "color": player["color"],
                "teams": player["teams"],
                "points": points_by_player[player["id"]],
                "stageCounts": dict(stage_counts[player["id"]]),
            }
        )
    leaderboard.sort(key=lambda row: (-row["points"], row["name"]))
    for rank, row in enumerate(leaderboard, start=1):
        row["rank"] = rank

    return {
        "players": players,
        "teams": enriched_teams,
        "groups": static["groups"],
        "fixtures": group_fixtures,
        "knockoutFixtures": knockout_fixtures,
        "leaderboard": leaderboard,
        "scoring": static["scoring"],
        "lastUpdated": live_state.get("lastUpdated"),
        "provider": live_state.get("provider"),
    }


def upsert_live_fixtures(updates: list[dict[str, Any]], provider: str | None = None) -> dict[str, Any]:
    live_state = load_live_state()
    existing = {fixture["id"]: fixture for fixture in live_state.get("fixtures", [])}
    for update in updates:
        existing[update["id"]] = {**existing.get(update["id"], {}), **update}
    live_state["fixtures"] = list(existing.values())
    live_state["lastUpdated"] = datetime.now().astimezone().isoformat()
    if provider:
        live_state["provider"] = provider
    save_live_state(live_state)
    return live_state


def update_advancements(advancements: dict[str, str], provider: str | None = None) -> dict[str, Any]:
    live_state = load_live_state()
    live_state["advancements"] = merge_advancements(live_state.get("advancements", {}), advancements)
    live_state["lastUpdated"] = datetime.now().astimezone().isoformat()
    if provider:
        live_state["provider"] = provider
    save_live_state(live_state)
    return live_state
