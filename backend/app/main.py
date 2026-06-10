from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .live_api import LiveApiNotConfigured, LiveApiProviderError, fetch_live_updates
from .post_match import fetch_postmatch_updates, fetch_score_updates
from .qualification import fetch_qualification_updates
from .repository import build_state, upsert_live_fixtures, update_advancements


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

score_poll_task: asyncio.Task[None] | None = None


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
    return result


async def score_poll_loop() -> None:
    while True:
        try:
            await run_scoreboard_poll()
        except Exception as exc:
            print(f"Score poll failed: {exc}")
        await asyncio.sleep(max(settings.score_poll_interval_minutes, 1) * 60)


@app.on_event("startup")
async def start_score_polling() -> None:
    global score_poll_task
    if settings.enable_score_polling and score_poll_task is None:
        score_poll_task = asyncio.create_task(score_poll_loop())


@app.on_event("shutdown")
async def stop_score_polling() -> None:
    global score_poll_task
    if score_poll_task is not None:
        score_poll_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await score_poll_task
        score_poll_task = None


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


@app.post("/api/live/sync")
async def sync_live() -> dict[str, Any]:
    try:
        updates = await fetch_live_updates()
    except (LiveApiNotConfigured, LiveApiProviderError) as exc:
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
        raise HTTPException(status_code=502, detail=detail) from exc

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
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    updates = result["updates"]
    if updates:
        upsert_live_fixtures(updates, provider=result["source"])

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
    return {"updatedFixtures": len(updates), "state": build_state()}


@app.post("/api/admin/advancements")
def record_advancements(updates: list[AdvancementUpdate]) -> dict[str, Any]:
    update_advancements({row.team: row.stageReached for row in updates}, provider="manual")
    return {"updatedTeams": len(updates), "state": build_state()}
