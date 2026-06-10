from __future__ import annotations

from typing import Any

import httpx

from .config import settings
from .repository import load_static


class LiveApiNotConfigured(RuntimeError):
    pass


class LiveApiProviderError(RuntimeError):
    pass


def normalize_team_name(name: str) -> str:
    normalized = " ".join(name.replace("-", " ").split())
    aliases = {
        "South Korea": "Korea Republic",
        "USA": "United States",
        "United States of America": "United States",
        "Bosnia": "Bosnia & Herzegovina",
        "Bosnia Herzegovina": "Bosnia & Herzegovina",
        "Bosnia and Herzegovina": "Bosnia & Herzegovina",
        "Czech Republic": "Czechia",
        "Cote d'Ivoire": "Ivory Coast",
        "Côte d'Ivoire": "Ivory Coast",
        "DR Congo": "Congo DR",
        "Curacao": "Cura\u00e7ao",
        "Curaçao": "Cura\u00e7ao",
        "Turkey": "T\u00fcrkiye",
        "Turkiye": "T\u00fcrkiye",
        "Türkiye": "T\u00fcrkiye",
    }
    return aliases.get(normalized, normalized)


def fixture_index() -> dict[tuple[str, str], tuple[dict[str, Any], bool]]:
    static = load_static()
    fixtures = static["fixtures"] + static["knockoutFixtures"]
    index = {}
    for fixture in fixtures:
        home = normalize_team_name(fixture["homeTeam"])
        away = normalize_team_name(fixture["awayTeam"])
        index[(home, away)] = (fixture, False)
        index[(away, home)] = (fixture, True)
    return index


def read_score(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        cursor: Any = payload
        for key in path:
            if not isinstance(cursor, dict) or key not in cursor:
                cursor = None
                break
            cursor = cursor[key]
        if cursor is not None:
            return cursor
    return None


def normalize_generic_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and payload.get("errors"):
        raise LiveApiProviderError(f"Live provider error: {payload['errors']}")

    if isinstance(payload, dict):
        rows = payload.get("fixtures") or payload.get("matches") or payload.get("response") or payload.get("data") or []
    else:
        rows = payload

    updates = []
    index = fixture_index()
    for row in rows:
        home = normalize_team_name(
            read_score(row, ("homeTeam",), ("home", "name"), ("teams", "home", "name")) or ""
        )
        away = normalize_team_name(
            read_score(row, ("awayTeam",), ("away", "name"), ("teams", "away", "name")) or ""
        )
        if not home or not away:
            continue
        match = index.get((home, away))
        if not match:
            continue
        fixture, swap_scores = match

        home_score = read_score(row, ("homeScore",), ("score", "fulltime", "home"), ("goals", "home"))
        away_score = read_score(row, ("awayScore",), ("score", "fulltime", "away"), ("goals", "away"))
        if swap_scores:
            home_score, away_score = away_score, home_score
        status = read_score(row, ("status",), ("fixture", "status", "short"), ("fixture", "status", "long"))
        provider_id = read_score(row, ("fixture", "id"), ("id",))
        update = {
            "id": fixture["id"],
            "providerFixtureId": provider_id,
            "homeScore": home_score,
            "awayScore": away_score,
            "status": status or fixture["status"],
        }
        for field in ("displayClock", "statusDetail", "statusState"):
            value = row.get(field)
            if value is not None:
                update[field] = value
        updates.append(update)
    return updates


def live_api_url() -> str:
    url = settings.live_matches_api_url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    if settings.live_matches_provider == "api-football" and "?" not in url:
        url = url.rstrip("/") + "/fixtures?league=1&season=2026&timezone=Africa/Johannesburg"
    return url


def live_api_headers() -> dict[str, str]:
    headers = {}
    if settings.live_matches_api_key:
        headers[settings.live_matches_api_key_header] = settings.live_matches_api_key

    for header in settings.live_matches_extra_headers.replace("\n", ";").split(";"):
        if not header.strip() or "=" not in header:
            continue
        name, value = header.split("=", 1)
        if name.strip() and value.strip():
            headers[name.strip()] = value.strip()

    return headers


async def fetch_live_updates() -> list[dict[str, Any]]:
    url = live_api_url()
    if not url:
        raise LiveApiNotConfigured("Set LIVE_MATCHES_API_URL and LIVE_MATCHES_API_KEY to enable live sync.")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=live_api_headers())
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                detail: Any = exc.response.json()
            except ValueError:
                detail = exc.response.text[:500]
            raise LiveApiProviderError(f"Live provider HTTP {exc.response.status_code}: {detail}") from exc
        return normalize_generic_payload(response.json())
