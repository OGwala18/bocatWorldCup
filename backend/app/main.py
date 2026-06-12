from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .live_api import LiveApiNotConfigured, LiveApiProviderError, fetch_live_updates
from .post_match import fetch_postmatch_updates, fetch_score_updates
from .qualification import fetch_qualification_updates
from .repository import build_state, upsert_live_fixtures, update_advancements


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("bocat.api")

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

score_poll_task: asyncio.Task[None] | None = None
daily_standings_task: asyncio.Task[None] | None = None


@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed method=%s path=%s origin=%s",
            request.method,
            request.url.path,
            request.headers.get("origin", "-"),
        )
        raise

    if request.url.path.startswith("/api"):
        duration_ms = round((time.perf_counter() - started_at) * 1000)
        logger.info(
            "Request complete method=%s path=%s status=%s duration_ms=%s origin=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request.headers.get("origin", "-"),
        )
    return response


async def run_scoreboard_poll() -> dict[str, Any]:
    result = await fetch_score_updates()
    updates = result["updates"]
    if updates:
        upsert_live_fixtures(updates, provider=result["source"])
    qualification_error = None
    try:
        qualification_result = await fetch_qualification_updates()
    except LiveApiProviderError as exc:
        qualification_result = {"source": "espn-standings", "advancements": {}}
        qualification_error = str(exc)
    advancements = qualification_result["advancements"]
    if advancements:
        update_advancements(advancements, provider=qualification_result["source"])
    result["qualifiedTeams"] = len(advancements)
    result["qualificationError"] = qualification_error
    logger.info(
        "Score poll complete source=%s updated=%s eligible=%s checked_dates=%s live=%s final=%s qualified=%s qualification_error=%s",
        result.get("source"),
        result.get("updatedFixtures"),
        result.get("eligibleFixtures"),
        len(result.get("checkedDates", [])),
        result.get("liveFixtures"),
        result.get("finalFixtures"),
        result["qualifiedTeams"],
        qualification_error or "-",
    )
    return result


async def score_poll_loop() -> None:
    while True:
        try:
            await run_scoreboard_poll()
        except Exception as exc:
            logger.exception("Score poll failed: %s", exc)
        await asyncio.sleep(max(settings.score_poll_interval_minutes, 1) * 60)


def daily_sync_target(now: datetime) -> datetime:
    try:
        hour_text, minute_text = settings.daily_standings_sync_time.split(":", maxsplit=1)
        hour = int(hour_text)
        minute = int(minute_text)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Daily sync time is out of range")
    except (TypeError, ValueError):
        hour = 8
        minute = 0

    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


async def daily_standings_sync_loop() -> None:
    timezone = ZoneInfo(settings.timezone)
    while True:
        now = datetime.now(timezone)
        target = daily_sync_target(now)
        wait_seconds = max((target - now).total_seconds(), 1)
        logger.info(
            "Daily group standings sync scheduled target=%s wait_seconds=%s",
            target.isoformat(),
            round(wait_seconds),
        )
        await asyncio.sleep(wait_seconds)
        try:
            result = await run_scoreboard_poll()
            state = build_state()
            logger.info(
                "Daily group standings sync complete updated=%s final=%s live=%s groups=%s",
                result["updatedFixtures"],
                result["finalFixtures"],
                result["liveFixtures"],
                len(state["groupStandings"]),
            )
        except Exception as exc:
            logger.exception("Daily group standings sync failed: %s", exc)
        await asyncio.sleep(60)


@app.on_event("startup")
async def start_score_polling() -> None:
    global score_poll_task, daily_standings_task
    logger.info(
        "Starting Bocat API timezone=%s cors_origins=%s score_polling=%s poll_interval_minutes=%s daily_standings_sync=%s daily_standings_time=%s live_provider=%s live_api_configured=%s fallback_provider=%s state_path=%s",
        settings.timezone,
        settings.cors_origins,
        settings.enable_score_polling,
        settings.score_poll_interval_minutes,
        settings.enable_daily_standings_sync,
        settings.daily_standings_sync_time,
        settings.live_matches_provider,
        bool(settings.live_matches_api_url and settings.live_matches_api_key),
        settings.fallback_scores_provider,
        settings.live_state_path,
    )
    if settings.enable_score_polling and score_poll_task is None:
        score_poll_task = asyncio.create_task(score_poll_loop())
        logger.info("Background score polling started")
    if settings.enable_daily_standings_sync and daily_standings_task is None:
        daily_standings_task = asyncio.create_task(daily_standings_sync_loop())
        logger.info("Daily group standings sync started")


@app.on_event("shutdown")
async def stop_score_polling() -> None:
    global score_poll_task, daily_standings_task
    if score_poll_task is not None:
        score_poll_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await score_poll_task
        score_poll_task = None
        logger.info("Background score polling stopped")
    if daily_standings_task is not None:
        daily_standings_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await daily_standings_task
        daily_standings_task = None
        logger.info("Daily group standings sync stopped")


class FixtureResult(BaseModel):
    id: str
    homeScore: int | None = None
    awayScore: int | None = None
    status: str = "finished"


class AdvancementUpdate(BaseModel):
    team: str
    stageReached: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timezone": settings.timezone}


@app.get("/api/state")
def state() -> dict[str, Any]:
    return build_state()


@app.get("/api/fixtures")
def fixtures() -> dict[str, Any]:
    current = build_state()
    return {
        "fixtures": current["fixtures"],
        "knockoutFixtures": current["knockoutFixtures"],
        "lastUpdated": current["lastUpdated"],
    }


@app.get("/api/leaderboard")
def leaderboard() -> dict[str, Any]:
    current = build_state()
    return {"leaderboard": current["leaderboard"], "teams": current["teams"], "lastUpdated": current["lastUpdated"]}


@app.get("/api/group-standings")
def group_standings() -> dict[str, Any]:
    current = build_state()
    return {
        "groupStandings": current["groupStandings"],
        "lastUpdated": current["lastUpdated"],
        "provider": current["provider"],
    }


@app.post("/api/live/sync")
async def sync_live() -> dict[str, Any]:
    logger.info(
        "Manual live sync requested provider=%s live_api_configured=%s",
        settings.live_matches_provider,
        bool(settings.live_matches_api_url and settings.live_matches_api_key),
    )
    try:
        updates = await fetch_live_updates()
    except (LiveApiNotConfigured, LiveApiProviderError) as exc:
        logger.warning("Live API unavailable, using scoreboard fallback: %s", exc)
        return await sync_scoreboard_fallback(str(exc))
    upsert_live_fixtures(updates, provider=settings.live_matches_provider)
    qualification_error = None
    try:
        qualification_result = await fetch_qualification_updates()
    except LiveApiProviderError as exc:
        qualification_result = {"source": "espn-standings", "advancements": {}}
        qualification_error = str(exc)
    if qualification_result["advancements"]:
        update_advancements(qualification_result["advancements"], provider=qualification_result["source"])
    logger.info(
        "Manual live sync complete mode=live updated=%s qualified=%s qualification_error=%s",
        len(updates),
        len(qualification_result["advancements"]),
        qualification_error or "-",
    )
    return {
        "mode": "live",
        "updatedFixtures": len(updates),
        "qualifiedTeams": len(qualification_result["advancements"]),
        "qualificationError": qualification_error,
        "state": build_state(),
    }


async def sync_scoreboard_fallback(live_error: str | None = None) -> dict[str, Any]:
    try:
        result = await run_scoreboard_poll()
    except LiveApiProviderError as exc:
        detail = f"{live_error}; ESPN scoreboard fallback failed: {exc}" if live_error else str(exc)
        logger.exception("Scoreboard fallback failed: %s", detail)
        raise HTTPException(status_code=502, detail=detail) from exc

    logger.info(
        "Scoreboard fallback complete mode=%s updated=%s eligible=%s checked_dates=%s live=%s final=%s qualified=%s live_error=%s qualification_error=%s",
        "scoreboard-fallback" if live_error else "scoreboard",
        result["updatedFixtures"],
        result["eligibleFixtures"],
        len(result["checkedDates"]),
        result["liveFixtures"],
        result["finalFixtures"],
        result["qualifiedTeams"],
        live_error or "-",
        result["qualificationError"] or "-",
    )
    return {
        "mode": "scoreboard-fallback" if live_error else "scoreboard",
        "liveError": live_error,
        "updatedFixtures": result["updatedFixtures"],
        "eligibleFixtures": result["eligibleFixtures"],
        "checkedDates": result["checkedDates"],
        "liveFixtures": result["liveFixtures"],
        "finalFixtures": result["finalFixtures"],
        "qualifiedTeams": result["qualifiedTeams"],
        "qualificationError": result["qualificationError"],
        "state": build_state(),
    }


@app.post("/api/live/sync-scores")
async def sync_scores() -> dict[str, Any]:
    return await sync_scoreboard_fallback()


@app.post("/api/live/sync-postmatch")
async def sync_postmatch() -> dict[str, Any]:
    try:
        result = await fetch_postmatch_updates()
    except LiveApiProviderError as exc:
        logger.exception("Postmatch sync failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    updates = result["updates"]
    if updates:
        upsert_live_fixtures(updates, provider=result["source"])

    logger.info(
        "Postmatch sync complete source=%s updated=%s eligible=%s checked_dates=%s",
        result["source"],
        len(updates),
        result["eligibleFixtures"],
        len(result["checkedDates"]),
    )
    return {
        "mode": "postmatch",
        "updatedFixtures": len(updates),
        "eligibleFixtures": result["eligibleFixtures"],
        "checkedDates": result["checkedDates"],
        "state": build_state(),
    }


@app.post("/api/admin/results")
def record_results(results: list[FixtureResult]) -> dict[str, Any]:
    updates = [result.model_dump(exclude_none=True) for result in results]
    upsert_live_fixtures(updates, provider="manual")
    logger.info("Manual fixture results recorded count=%s", len(updates))
    return {"updatedFixtures": len(updates), "state": build_state()}


@app.post("/api/admin/advancements")
def record_advancements(updates: list[AdvancementUpdate]) -> dict[str, Any]:
    update_advancements({row.team: row.stageReached for row in updates}, provider="manual")
    logger.info("Manual advancement updates recorded count=%s", len(updates))
    return {"updatedTeams": len(updates), "state": build_state()}
