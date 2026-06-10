from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from .config import settings
from .live_api import LiveApiProviderError, normalize_generic_payload, normalize_team_name
from .repository import build_state


FINAL_STATUS_NAMES = {
    "STATUS_FINAL",
    "STATUS_FULL_TIME",
    "STATUS_FINAL_PEN",
    "STATUS_FINAL_AET",
    "FINAL",
    "FT",
    "FULL TIME",
    "FINISHED",
}


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_final_status(status: Any) -> bool:
    if not status:
        return False
    text = str(status).strip().upper().replace("_", " ")
    return text in {name.replace("_", " ") for name in FINAL_STATUS_NAMES}


def known_team_match(fixture: dict[str, Any]) -> bool:
    teams = {fixture.get("homeTeam"), fixture.get("awayTeam")}
    if not all(isinstance(team, str) and team.strip() for team in teams):
        return False
    blocked = ("TBD", "Best Third-Place", "Group ", "Second-Place", "Winner")
    return not any(any(token in team for token in blocked) for team in teams)


def fixture_is_final(fixture: dict[str, Any]) -> bool:
    return is_final_status(fixture.get("status"))


def eligible_postmatch_fixtures(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now(ZoneInfo(settings.timezone))
    cutoff = current - timedelta(minutes=settings.post_match_delay_minutes)
    state = build_state()
    fixtures = state["fixtures"] + state["knockoutFixtures"]

    eligible = []
    for fixture in fixtures:
        if not known_team_match(fixture) or fixture_is_final(fixture):
            continue
        kickoff = parse_datetime(fixture["kickoffSast"])
        if kickoff <= cutoff:
            eligible.append(fixture)
    return eligible


def eligible_score_fixtures(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now(ZoneInfo(settings.timezone))
    state = build_state()
    fixtures = state["fixtures"] + state["knockoutFixtures"]

    eligible = []
    for fixture in fixtures:
        if not known_team_match(fixture) or fixture_is_final(fixture):
            continue
        kickoff = parse_datetime(fixture["kickoffSast"])
        starts_at = kickoff - timedelta(minutes=settings.score_poll_start_minutes_before_kickoff)
        live_window_ends = kickoff + timedelta(minutes=settings.score_poll_end_minutes_after_kickoff)
        postmatch_retry_starts = kickoff + timedelta(minutes=settings.post_match_delay_minutes)
        if starts_at <= current <= live_window_ends or current >= postmatch_retry_starts:
            eligible.append(fixture)
    return eligible


def fallback_scoreboard_url(date_key: str) -> str:
    template = settings.fallback_scores_url_template
    if "{date}" in template:
        return template.format(date=date_key)
    separator = "&" if "?" in template else "?"
    return f"{template}{separator}dates={date_key}"


def espn_date_key(fixture: dict[str, Any]) -> str:
    return parse_datetime(fixture["kickoffEt"]).strftime("%Y%m%d")


def pick_competitor(competitors: list[dict[str, Any]], side: str) -> dict[str, Any] | None:
    for competitor in competitors:
        if competitor.get("homeAway") == side:
            return competitor
    if side == "home" and competitors:
        return competitors[0]
    if side == "away" and len(competitors) > 1:
        return competitors[1]
    return None


def team_name(competitor: dict[str, Any] | None) -> str:
    if not competitor:
        return ""
    team = competitor.get("team") or {}
    return normalize_team_name(team.get("displayName") or team.get("name") or "")


def normalize_espn_status(status: dict[str, Any]) -> tuple[str, str | None, str | None, str | None]:
    status_type = status.get("type") or {}
    name = status_type.get("name")
    state = status_type.get("state")
    description = status_type.get("shortDetail") or status_type.get("description") or status_type.get("detail")
    display_clock = status.get("displayClock")
    completed = bool(status_type.get("completed")) or is_final_status(name)

    if completed or state == "post":
        return "finished", display_clock, description, state
    if state == "in":
        text = " ".join(str(value or "") for value in (name, description)).lower()
        if "half" in text and "time" in text:
            return "halftime", display_clock, description, state
        return "live", display_clock, description, state
    return "scheduled", display_clock, description, state


def normalize_espn_scoreboard(payload: dict[str, Any], final_only: bool = True) -> list[dict[str, Any]]:
    rows = []
    for event in payload.get("events", []):
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        competition = competitions[0]
        status = competition.get("status") or event.get("status") or {}
        normalized_status, display_clock, status_detail, status_state = normalize_espn_status(status)
        if final_only and normalized_status != "finished":
            continue

        competitors = competition.get("competitors") or []
        home = pick_competitor(competitors, "home")
        away = pick_competitor(competitors, "away")
        rows.append(
            {
                "id": event.get("id") or competition.get("id"),
                "homeTeam": team_name(home),
                "awayTeam": team_name(away),
                "homeScore": int_or_none(home.get("score") if home else None),
                "awayScore": int_or_none(away.get("score") if away else None),
                "status": normalized_status,
                "displayClock": display_clock,
                "statusDetail": status_detail,
                "statusState": status_state,
            }
        )

    return normalize_generic_payload({"response": rows})


async def fetch_espn_updates_for_dates(date_keys: list[str], final_only: bool = True) -> list[dict[str, Any]]:
    updates = []
    headers = {"User-Agent": "Bocat World Cup dashboard/1.0"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client:
        for date_key in date_keys:
            response = await client.get(fallback_scoreboard_url(date_key))
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise LiveApiProviderError(
                    f"Post-match source HTTP {exc.response.status_code}: {exc.response.text[:300]}"
                ) from exc
            updates.extend(normalize_espn_scoreboard(response.json(), final_only=final_only))
    return updates


async def fetch_score_updates(now: datetime | None = None) -> dict[str, Any]:
    if settings.fallback_scores_provider != "espn":
        raise LiveApiProviderError(f"Unsupported fallback score provider: {settings.fallback_scores_provider}")

    eligible = eligible_score_fixtures(now)
    eligible_ids = {fixture["id"] for fixture in eligible}
    date_keys = sorted({espn_date_key(fixture) for fixture in eligible})
    updates = await fetch_espn_updates_for_dates(date_keys, final_only=False) if date_keys else []
    updates = [
        update
        for update in updates
        if update["id"] in eligible_ids and update.get("homeScore") is not None and update.get("awayScore") is not None
        and update.get("status") in {"live", "halftime", "finished"}
    ]

    return {
        "source": "espn-scoreboard",
        "eligibleFixtures": len(eligible),
        "checkedDates": date_keys,
        "updatedFixtures": len(updates),
        "finalFixtures": sum(1 for update in updates if update.get("status") == "finished"),
        "liveFixtures": sum(1 for update in updates if update.get("status") in {"live", "halftime"}),
        "updates": updates,
    }


async def fetch_postmatch_updates(now: datetime | None = None) -> dict[str, Any]:
    if settings.fallback_scores_provider != "espn":
        raise LiveApiProviderError(f"Unsupported fallback score provider: {settings.fallback_scores_provider}")

    eligible = eligible_postmatch_fixtures(now)
    eligible_ids = {fixture["id"] for fixture in eligible}
    date_keys = sorted({espn_date_key(fixture) for fixture in eligible})
    updates = await fetch_espn_updates_for_dates(date_keys, final_only=True) if date_keys else []
    updates = [
        update
        for update in updates
        if update["id"] in eligible_ids and update.get("homeScore") is not None and update.get("awayScore") is not None
    ]

    return {
        "source": "espn-postmatch",
        "eligibleFixtures": len(eligible),
        "checkedDates": date_keys,
        "updatedFixtures": len(updates),
        "finalFixtures": len(updates),
        "liveFixtures": 0,
        "updates": updates,
    }
