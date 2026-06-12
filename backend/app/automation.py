from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime

from .live_api import LiveApiNotConfigured, LiveApiProviderError, fetch_live_updates
from .post_match import fetch_postmatch_updates, fetch_score_updates, parse_datetime
from .qualification import fetch_qualification_updates
from .repository import build_state, update_advancements, upsert_live_fixtures


async def sync_live() -> int:
    try:
        updates = await fetch_live_updates()
    except (LiveApiNotConfigured, LiveApiProviderError) as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 0
    upsert_live_fixtures(updates, provider="automation")
    print(json.dumps({"ok": True, "updatedFixtures": len(updates)}))
    return len(updates)


async def sync_postmatch(now: datetime | None = None, dry_run: bool = False) -> int:
    try:
        result = await fetch_postmatch_updates(now=now)
    except LiveApiProviderError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 0

    updates = result["updates"]
    if updates and not dry_run:
        upsert_live_fixtures(updates, provider=result["source"])

    print(
        json.dumps(
            {
                "ok": True,
                "source": result["source"],
                "eligibleFixtures": result["eligibleFixtures"],
                "checkedDates": result["checkedDates"],
                "updatedFixtures": len(updates),
                "dryRun": dry_run,
            }
        )
    )
    return len(updates)


async def sync_scores(now: datetime | None = None, dry_run: bool = False) -> int:
    try:
        result = await fetch_score_updates(now=now)
    except LiveApiProviderError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 0

    updates = result["updates"]
    if updates and not dry_run:
        upsert_live_fixtures(updates, provider=result["source"])
    try:
        qualification_result = await fetch_qualification_updates()
    except LiveApiProviderError as exc:
        qualification_result = {"source": "espn-standings", "advancements": {}, "error": str(exc)}

    advancements = qualification_result["advancements"]
    if advancements and not dry_run:
        update_advancements(advancements, provider=qualification_result["source"])

    print(
        json.dumps(
            {
                "ok": True,
                "source": result["source"],
                "eligibleFixtures": result["eligibleFixtures"],
                "checkedDates": result["checkedDates"],
                "updatedFixtures": len(updates),
                "liveFixtures": result["liveFixtures"],
                "finalFixtures": result["finalFixtures"],
                "qualifiedTeams": len(advancements),
                "qualificationError": qualification_result.get("error"),
                "dryRun": dry_run,
            }
        )
    )
    return len(updates)


def print_state() -> None:
    state = build_state()
    print(
        json.dumps(
            {
                "lastUpdated": state["lastUpdated"],
                "leaderboard": state["leaderboard"],
                "groupStandings": state["groupStandings"],
                "groupStageCompleteAtSast": state["scoring"]["groupStageCompleteAtSast"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Bocat live data automation")
    parser.add_argument(
        "command",
        choices=["sync-live", "sync-scores", "sync-standings", "sync-postmatch", "state"],
        help="Automation command to run",
    )
    parser.add_argument("--now", help="Override current time for post-match checks, ISO format.")
    parser.add_argument("--dry-run", action="store_true", help="Report post-match updates without writing live_state.json.")
    args = parser.parse_args()

    if args.command == "sync-live":
        asyncio.run(sync_live())
    elif args.command in {"sync-scores", "sync-standings"}:
        asyncio.run(sync_scores(parse_datetime(args.now) if args.now else None, dry_run=args.dry_run))
    elif args.command == "sync-postmatch":
        asyncio.run(sync_postmatch(parse_datetime(args.now) if args.now else None, dry_run=args.dry_run))
    elif args.command == "state":
        print_state()


if __name__ == "__main__":
    main()
