from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

ET = ZoneInfo("America/New_York")
SAST = ZoneInfo("Africa/Johannesburg")


PLAYERS = [
    {"id": "onke", "name": "Onke", "color": "#0EA5E9"},
    {"id": "jarvis", "name": "Jarvis", "color": "#F97316"},
    {"id": "ndalo", "name": "Ndalo", "color": "#8B5CF6"},
    {"id": "asiphe", "name": "Asiphe", "color": "#22C55E"},
    {"id": "sandile", "name": "Sandile", "color": "#EF4444"},
    {"id": "mudi", "name": "Mudi", "color": "#14B8A6"},
    {"id": "tadhg", "name": "Tadhg", "color": "#EAB308"},
    {"id": "ayanda", "name": "Ayanda", "color": "#EC4899"},
    {"id": "mandla", "name": "Mandla", "color": "#6366F1"},
    {"id": "tmak", "name": "Tmak", "color": "#84CC16"},
    {"id": "magz", "name": "Magz", "color": "#06B6D4"},
    {"id": "inathi", "name": "Inathi", "color": "#F43F5E"},
]

ASSIGNMENTS = {
    "Onke": ["Germany", "Korea Republic", "Senegal", "South Africa"],
    "Jarvis": ["England", "Austria", "Norway", "Mexico"],
    "Ndalo": ["Netherlands", "Panama", "Japan", "Cape Verde"],
    "Asiphe": ["France", "New Zealand", "Iran", "Jordan"],
    "Sandile": ["Portugal", "Sweden", "Ghana", "Congo DR"],
    "Mudi": ["Argentina", "Ivory Coast", "Australia", "Qatar"],
    "Tadhg": ["Spain", "Ecuador", "Switzerland", "Tunisia"],
    "Ayanda": ["Brazil", "Bosnia & Herzegovina", "Iraq", "United States"],
    "Mandla": ["Belgium", "Türkiye", "Czechia", "Scotland"],
    "Tmak": ["Morocco", "Saudi Arabia", "Algeria", "Paraguay"],
    "Magz": ["Croatia", "Haiti", "Uruguay", "Curaçao"],
    "Inathi": ["Colombia", "Canada", "Uzbekistan", "Egypt"],
}

TOP_12_WORLD_CUP_TEAMS = [
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
]

GROUPS = {
    "A": ["Mexico", "South Africa", "Korea Republic", "Czechia"],
    "B": ["Canada", "Bosnia & Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Türkiye"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Congo DR", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# FOX Sports published the group-stage dates/times in ET. The app converts these
# to South African time and keeps the original source metadata for auditing.
GROUP_FIXTURES_ET = [
    (1, "A", "2026-06-11", "15:00", "South Africa", "Mexico", "Mexico City Stadium"),
    (2, "A", "2026-06-11", "22:00", "Korea Republic", "Czechia", "Guadalajara Stadium"),
    (3, "B", "2026-06-12", "15:00", "Canada", "Bosnia & Herzegovina", "Toronto Stadium"),
    (4, "D", "2026-06-12", "21:00", "United States", "Paraguay", "Los Angeles Stadium"),
    (5, "B", "2026-06-13", "15:00", "Qatar", "Switzerland", "San Francisco Bay Stadium"),
    (6, "C", "2026-06-13", "18:00", "Brazil", "Morocco", "New York New Jersey Stadium"),
    (7, "C", "2026-06-13", "21:00", "Haiti", "Scotland", "Boston Stadium"),
    (8, "D", "2026-06-14", "00:00", "Australia", "Türkiye", "BC Place Vancouver"),
    (9, "E", "2026-06-14", "13:00", "Germany", "Curaçao", "Houston Stadium"),
    (10, "F", "2026-06-14", "16:00", "Netherlands", "Japan", "Dallas Stadium"),
    (11, "E", "2026-06-14", "19:00", "Ivory Coast", "Ecuador", "Philadelphia Stadium"),
    (12, "F", "2026-06-14", "22:00", "Tunisia", "Sweden", "Monterrey Stadium"),
    (13, "H", "2026-06-15", "12:00", "Spain", "Cape Verde", "Atlanta Stadium"),
    (14, "G", "2026-06-15", "15:00", "Belgium", "Egypt", "Seattle Stadium"),
    (15, "H", "2026-06-15", "18:00", "Saudi Arabia", "Uruguay", "Miami Stadium"),
    (16, "G", "2026-06-15", "21:00", "Iran", "New Zealand", "Los Angeles Stadium"),
    (17, "I", "2026-06-16", "15:00", "France", "Senegal", "New York New Jersey Stadium"),
    (18, "I", "2026-06-16", "18:00", "Iraq", "Norway", "Boston Stadium"),
    (19, "J", "2026-06-16", "21:00", "Argentina", "Algeria", "Kansas City Stadium"),
    (20, "J", "2026-06-17", "00:00", "Austria", "Jordan", "San Francisco Bay Stadium"),
    (21, "K", "2026-06-17", "13:00", "Portugal", "Congo DR", "Houston Stadium"),
    (22, "L", "2026-06-17", "16:00", "England", "Croatia", "Dallas Stadium"),
    (23, "L", "2026-06-17", "19:00", "Ghana", "Panama", "Toronto Stadium"),
    (24, "K", "2026-06-17", "22:00", "Uzbekistan", "Colombia", "Mexico City Stadium"),
    (25, "A", "2026-06-18", "12:00", "Czechia", "South Africa", "Atlanta Stadium"),
    (26, "B", "2026-06-18", "15:00", "Switzerland", "Bosnia & Herzegovina", "Los Angeles Stadium"),
    (27, "B", "2026-06-18", "18:00", "Canada", "Qatar", "BC Place Vancouver"),
    (28, "A", "2026-06-18", "21:00", "Mexico", "Korea Republic", "Guadalajara Stadium"),
    (29, "D", "2026-06-19", "15:00", "United States", "Australia", "Seattle Stadium"),
    (30, "C", "2026-06-19", "15:00", "Scotland", "Morocco", "Boston Stadium"),
    (31, "C", "2026-06-19", "21:00", "Brazil", "Haiti", "Philadelphia Stadium"),
    (32, "D", "2026-06-20", "00:00", "Türkiye", "Paraguay", "San Francisco Bay Stadium"),
    (33, "F", "2026-06-20", "13:00", "Netherlands", "Sweden", "Houston Stadium"),
    (34, "E", "2026-06-20", "16:00", "Germany", "Ivory Coast", "Toronto Stadium"),
    (35, "E", "2026-06-20", "20:00", "Ecuador", "Curaçao", "Kansas City Stadium"),
    (36, "F", "2026-06-21", "00:00", "Tunisia", "Japan", "Monterrey Stadium"),
    (37, "H", "2026-06-21", "12:00", "Spain", "Saudi Arabia", "Atlanta Stadium"),
    (38, "G", "2026-06-21", "15:00", "Belgium", "Iran", "Los Angeles Stadium"),
    (39, "H", "2026-06-21", "18:00", "Uruguay", "Cape Verde", "Miami Stadium"),
    (40, "G", "2026-06-21", "21:00", "New Zealand", "Egypt", "BC Place Vancouver"),
    (41, "J", "2026-06-22", "13:00", "Argentina", "Austria", "Dallas Stadium"),
    (42, "I", "2026-06-22", "17:00", "France", "Iraq", "Philadelphia Stadium"),
    (43, "I", "2026-06-22", "20:00", "Norway", "Senegal", "New York New Jersey Stadium"),
    (44, "J", "2026-06-22", "23:00", "Jordan", "Algeria", "San Francisco Bay Stadium"),
    (45, "K", "2026-06-23", "13:00", "Portugal", "Uzbekistan", "Houston Stadium"),
    (46, "L", "2026-06-23", "16:00", "England", "Ghana", "Boston Stadium"),
    (47, "L", "2026-06-23", "19:00", "Panama", "Croatia", "Toronto Stadium"),
    (48, "K", "2026-06-23", "22:00", "Colombia", "Congo DR", "Guadalajara Stadium"),
    (49, "B", "2026-06-24", "15:00", "Switzerland", "Canada", "BC Place Vancouver"),
    (50, "B", "2026-06-24", "15:00", "Bosnia & Herzegovina", "Qatar", "Seattle Stadium"),
    (51, "C", "2026-06-24", "18:00", "Brazil", "Scotland", "Miami Stadium"),
    (52, "C", "2026-06-24", "18:00", "Morocco", "Haiti", "Atlanta Stadium"),
    (53, "A", "2026-06-24", "21:00", "Mexico", "Czechia", "Mexico City Stadium"),
    (54, "A", "2026-06-24", "21:00", "Korea Republic", "South Africa", "Monterrey Stadium"),
    (55, "E", "2026-06-25", "16:00", "Ecuador", "Germany", "New York New Jersey Stadium"),
    (56, "E", "2026-06-25", "16:00", "Curaçao", "Ivory Coast", "Philadelphia Stadium"),
    (57, "F", "2026-06-25", "19:00", "Tunisia", "Netherlands", "Kansas City Stadium"),
    (58, "F", "2026-06-25", "19:00", "Japan", "Sweden", "Dallas Stadium"),
    (59, "D", "2026-06-25", "22:00", "United States", "Türkiye", "Los Angeles Stadium"),
    (60, "D", "2026-06-25", "22:00", "Paraguay", "Australia", "San Francisco Bay Stadium"),
    (61, "I", "2026-06-26", "15:00", "Norway", "France", "Boston Stadium"),
    (62, "I", "2026-06-26", "15:00", "Senegal", "Iraq", "Toronto Stadium"),
    (63, "H", "2026-06-26", "20:00", "Uruguay", "Spain", "Guadalajara Stadium"),
    (64, "H", "2026-06-26", "20:00", "Cape Verde", "Saudi Arabia", "Houston Stadium"),
    (65, "G", "2026-06-26", "23:00", "New Zealand", "Belgium", "BC Place Vancouver"),
    (66, "G", "2026-06-26", "23:00", "Egypt", "Iran", "Seattle Stadium"),
    (67, "L", "2026-06-27", "17:00", "Panama", "England", "New York New Jersey Stadium"),
    (68, "L", "2026-06-27", "17:00", "Croatia", "Ghana", "Philadelphia Stadium"),
    (69, "K", "2026-06-27", "19:30", "Colombia", "Portugal", "Miami Stadium"),
    (70, "K", "2026-06-27", "19:30", "Congo DR", "Uzbekistan", "Atlanta Stadium"),
    (71, "J", "2026-06-27", "22:00", "Argentina", "Jordan", "Dallas Stadium"),
    (72, "J", "2026-06-27", "22:00", "Algeria", "Austria", "Kansas City Stadium"),
]

KNOCKOUT_FIXTURES_ET = [
    (73, "Round of 32", "2026-06-28", "15:00", "South Africa", "Canada", "SoFi Stadium"),
    (74, "Round of 32", "2026-06-29", "13:00", "Brazil", "Japan", "NRG Stadium"),
    (75, "Round of 32", "2026-06-29", "16:30", "Germany", "Paraguay", "Gillette Stadium"),
    (76, "Round of 32", "2026-06-29", "21:00", "Netherlands", "Morocco", "Estadio BBVA"),
    (77, "Round of 32", "2026-06-30", "13:00", "Ivory Coast", "Norway", "AT&T Stadium"),
    (78, "Round of 32", "2026-06-30", "17:00", "France", "Sweden", "MetLife Stadium"),
    (79, "Round of 32", "2026-06-30", "21:00", "Mexico", "Ecuador", "Estadio Banorte"),
    (80, "Round of 32", "2026-07-01", "12:00", "England", "Congo DR", "Mercedes-Benz Stadium"),
    (81, "Round of 32", "2026-07-01", "16:00", "Belgium", "Senegal", "Lumen Field"),
    (82, "Round of 32", "2026-07-01", "20:00", "United States", "Bosnia & Herzegovina", "Levi's Stadium"),
    (83, "Round of 32", "2026-07-02", "15:00", "Spain", "Austria", "SoFi Stadium"),
    (84, "Round of 32", "2026-07-02", "19:00", "Portugal", "Croatia", "BMO Field"),
    (85, "Round of 32", "2026-07-02", "23:00", "Switzerland", "Algeria", "BC Place"),
    (86, "Round of 32", "2026-07-03", "14:00", "Australia", "Egypt", "AT&T Stadium"),
    (87, "Round of 32", "2026-07-03", "18:00", "Argentina", "Cape Verde", "Hard Rock Stadium"),
    (88, "Round of 32", "2026-07-03", "21:30", "Colombia", "Ghana", "GEHA Field at Arrowhead Stadium"),
    (89, "Round of 16", "2026-07-04", "13:00", "Canada", "Round of 32 Match 76 Winner", "NRG Stadium"),
    (90, "Round of 16", "2026-07-04", "17:00", "Round of 32 Match 74 Winner", "Round of 32 Match 77 Winner", "Lincoln Financial Field"),
    (91, "Round of 16", "2026-07-05", "16:00", "TBD", "TBD", "New York New Jersey Stadium"),
    (92, "Round of 16", "2026-07-05", "20:00", "TBD", "TBD", "Mexico City Stadium"),
    (93, "Round of 16", "2026-07-06", "15:00", "TBD", "TBD", "Dallas Stadium"),
    (94, "Round of 16", "2026-07-06", "20:00", "TBD", "TBD", "Seattle Stadium"),
    (95, "Round of 16", "2026-07-07", "12:00", "TBD", "TBD", "Atlanta Stadium"),
    (96, "Round of 16", "2026-07-07", "16:00", "TBD", "TBD", "BC Place Vancouver"),
    (97, "Quarterfinal", "2026-07-09", "16:00", "TBD", "TBD", "Boston Stadium"),
    (98, "Quarterfinal", "2026-07-10", "15:00", "TBD", "TBD", "Los Angeles Stadium"),
    (99, "Quarterfinal", "2026-07-11", "17:00", "TBD", "TBD", "Miami Stadium"),
    (100, "Quarterfinal", "2026-07-11", "21:00", "TBD", "TBD", "Kansas City Stadium"),
    (101, "Semifinal", "2026-07-14", "15:00", "TBD", "TBD", "Dallas Stadium"),
    (102, "Semifinal", "2026-07-15", "15:00", "TBD", "TBD", "Atlanta Stadium"),
    (103, "Final", "2026-07-19", "15:00", "TBD", "TBD", "New York New Jersey Stadium"),
]

POINTS_BY_STAGE = {
    "group": 0,
    "round_of_32": 1,
    "round_of_16": 2,
    "quarterfinal": 3,
    "semifinal": 4,
    "final": 5,
}


def write_json(filename: str, payload: object) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def owner_lookup() -> dict[str, dict[str, str]]:
    players_by_name = {player["name"]: player for player in PLAYERS}
    owners = {}
    for player_name, teams in ASSIGNMENTS.items():
        player = players_by_name[player_name]
        for team in teams:
            owners[team] = {
                "playerId": player["id"],
                "playerName": player["name"],
                "color": player["color"],
            }
    return owners


def to_fixture(number: int, stage: str, date: str, time_et: str, home: str, away: str, venue: str) -> dict:
    dt_et = datetime.fromisoformat(f"{date}T{time_et}:00").replace(tzinfo=ET)
    dt_sast = dt_et.astimezone(SAST)
    owners = owner_lookup()
    home_owner = owners.get(home)
    away_owner = owners.get(away)
    return {
        "id": f"m{number:03d}",
        "matchNumber": number,
        "stage": "Group Stage" if len(stage) == 1 else stage,
        "group": stage if len(stage) == 1 else None,
        "homeTeam": home,
        "awayTeam": away,
        "homeOwner": home_owner,
        "awayOwner": away_owner,
        "playerMatchup": f"{home_owner['playerName']} vs {away_owner['playerName']}" if home_owner and away_owner else "TBD",
        "venue": venue,
        "kickoffEt": dt_et.isoformat(),
        "kickoffSast": dt_sast.isoformat(),
        "dateSast": dt_sast.strftime("%A %d/%m/%Y"),
        "timeSast": dt_sast.strftime("%H:%M"),
        "status": "scheduled",
        "homeScore": None,
        "awayScore": None,
    }


def build() -> None:
    owners = owner_lookup()
    assigned_teams = [team for teams in ASSIGNMENTS.values() for team in teams]
    all_group_teams = [team for teams in GROUPS.values() for team in teams]

    if sorted(assigned_teams) != sorted(all_group_teams):
        missing = sorted(set(all_group_teams) - set(assigned_teams))
        extra = sorted(set(assigned_teams) - set(all_group_teams))
        raise RuntimeError(f"Assignments must cover all World Cup teams once. Missing={missing}; extra={extra}")

    fixtures = [
        to_fixture(number, group, date, time_et, home, away, venue)
        for number, group, date, time_et, home, away, venue in GROUP_FIXTURES_ET
    ]
    knockout_fixtures = [
        to_fixture(number, stage, date, time_et, home, away, venue)
        for number, stage, date, time_et, home, away, venue in KNOCKOUT_FIXTURES_ET
    ]

    teams = [
        {
            "name": team,
            "group": group,
            "owner": owners[team],
            "stageReached": "group",
            "points": POINTS_BY_STAGE["group"],
        }
        for group, group_teams in GROUPS.items()
        for team in group_teams
    ]

    write_json(
        "players.json",
        [
            {
                **player,
                "teams": ASSIGNMENTS[player["name"]],
                "topTeam": ASSIGNMENTS[player["name"]][0],
            }
            for player in PLAYERS
        ],
    )
    write_json("teams.json", teams)
    write_json(
        "groups.json",
        [{"group": group, "teams": teams} for group, teams in GROUPS.items()],
    )
    write_json("fixtures.json", fixtures)
    write_json("knockout_fixtures.json", knockout_fixtures)
    write_json(
        "scoring.json",
        {
            "timezone": "Africa/Johannesburg",
            "groupStageCompleteAtSast": "2026-06-28T06:00:00+02:00",
            "pointsByStage": POINTS_BY_STAGE,
            "notes": [
                "Round of 32 qualification awards 1 point.",
                "Round of 16 qualification awards 2 points.",
                "Quarterfinal qualification awards 3 points.",
                "Semifinal qualification awards 4 points.",
                "Final qualification awards 5 points.",
            ],
            "sources": [
                {
                    "label": "FIFA Scores & Fixtures",
                    "url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures",
                },
                {
                    "label": "FOX Sports 2026 World Cup schedule",
                    "url": "https://www.foxsports.com/stories/soccer/2026-world-cup-schedule-all-games-dates-matchups-how-watch",
                },
            ],
        },
    )
    write_json(
        "live_state.json",
        {
            "lastUpdated": None,
            "provider": None,
            "fixtures": [],
            "advancements": {},
        },
    )


if __name__ == "__main__":
    build()
