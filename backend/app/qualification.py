from __future__ import annotations

from typing import Any

import httpx

from .config import settings
from .live_api import LiveApiProviderError, normalize_team_name


def stat_value(entry: dict[str, Any], name: str) -> float:
    for stat in entry.get("stats", []):
        if stat.get("name") == name:
            try:
                return float(stat.get("value") or 0)
            except (TypeError, ValueError):
                return 0
    return 0


def parse_espn_qualified(payload: dict[str, Any]) -> dict[str, str]:
    advancements: dict[str, str] = {}
    for group in payload.get("children", []):
        standings = group.get("standings") or {}
        for entry in standings.get("entries", []):
            if stat_value(entry, "advanced") <= 0:
                continue
            team = entry.get("team") or {}
            team_name = normalize_team_name(team.get("displayName") or team.get("name") or "")
            if team_name:
                advancements[team_name] = "round_of_32"
    return advancements


async def fetch_qualification_updates() -> dict[str, Any]:
    if not settings.qualification_standings_url:
        return {"source": "espn-standings", "advancements": {}}

    headers = {"User-Agent": "Bocat World Cup dashboard/1.0"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client:
        response = await client.get(settings.qualification_standings_url)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LiveApiProviderError(
                f"Qualification source HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc

    return {
        "source": "espn-standings",
        "advancements": parse_espn_qualified(response.json()),
    }
