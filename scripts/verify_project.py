from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> None:
    players = load("players.json")
    teams = load("teams.json")
    fixtures = load("fixtures.json")
    scoring = load("scoring.json")
    top_teams = {
        "France",
        "Spain",
        "Argentina",
        "England",
        "Portugal",
        "Brazil",
        "Netherlands",
        "Morocco",
        "Belgium",
        "Germany",
        "Croatia",
        "Colombia",
    }

    assigned = [team for player in players for team in player["teams"]]
    assert len(players) == 12, f"Expected 12 players, found {len(players)}"
    assert len(assigned) == 48, f"Expected 48 assigned slots, found {len(assigned)}"
    assert len(set(assigned)) == 48, "Assigned teams must be unique"
    assert sorted(assigned) == sorted(team["name"] for team in teams), "Assignments must match team list"
    assert all(player["teams"][0] in top_teams for player in players), "First team must be a top-12 team"

    non_top_slots = [team for player in players for team in player["teams"][1:]]
    assert not (set(non_top_slots) & top_teams), "Top-12 teams must not appear in non-top slots"

    first = fixtures[0]
    assert first["homeTeam"] == "South Africa"
    assert first["awayTeam"] == "Mexico"
    assert first["playerMatchup"] == "Onke vs Jarvis"
    assert first["dateSast"] == "Thursday 11/06/2026"
    assert scoring["timezone"] == "Africa/Johannesburg"

    print(
        {
            "players": len(players),
            "assignedTeams": len(assigned),
            "fixtures": len(fixtures),
            "firstFixture": f"{first['homeTeam']} vs {first['awayTeam']} ({first['playerMatchup']})",
            "timezone": scoring["timezone"],
        }
    )


if __name__ == "__main__":
    main()
