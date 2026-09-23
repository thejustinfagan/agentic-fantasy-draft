#!/usr/bin/env python3
"""Wake Grok Bot only when an owned Sleeper draft pick is on clock."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request


def fetch(url: str):
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(
        f"{url}{sep}_={time.time_ns()}",
        headers={
            "User-Agent": "Grok-Bot-Sleeper-Draft-Watcher/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def env_or_cli(cli_value: str | None, env_name: str) -> str:
    return (cli_value or os.environ.get(env_name) or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft-id", help="Sleeper draft id (or DRAFT_ID)")
    parser.add_argument("--owned-picks", required=True)
    parser.add_argument("--teams", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=14)
    parser.add_argument("--interval", type=float, default=0.75)
    parser.add_argument("--timeout", type=float, default=7200)
    parser.add_argument("--event-label", default="USER_ON_CLOCK")
    parser.add_argument(
        "--resume-after-pick",
        type=int,
        help="Do not monitor a later turn until this pick is recorded.",
    )
    parser.add_argument(
        "--expected-player-id",
        help="With --resume-after-pick, fail closed if a different player was recorded.",
    )
    args = parser.parse_args()

    draft_id = env_or_cli(args.draft_id, "DRAFT_ID")
    if not draft_id:
        print("STATE_MISMATCH " + json.dumps({"reason": "missing DRAFT_ID"}), flush=True)
        return 2

    if not args.event_label or not args.event_label.replace("_", "").isalnum():
        print("STATE_MISMATCH " + json.dumps({"reason": "invalid event label"}), flush=True)
        return 2

    owned = {int(value) for value in args.owned_picks.split(",") if value.strip()}
    if not owned:
        print("STATE_MISMATCH " + json.dumps({"reason": "no owned picks supplied"}), flush=True)
        return 2
    if args.resume_after_pick is not None and args.resume_after_pick < 1:
        print("STATE_MISMATCH " + json.dumps({"reason": "invalid resume pick"}), flush=True)
        return 2
    if args.expected_player_id and args.resume_after_pick is None:
        print(
            "STATE_MISMATCH "
            + json.dumps({"reason": "expected player requires resume pick"}),
            flush=True,
        )
        return 2

    base = f"https://api.sleeper.app/v1/draft/{draft_id}"
    deadline = time.monotonic() + args.timeout
    failures = 0
    resume_pending = args.resume_after_pick
    while time.monotonic() < deadline:
        try:
            draft = fetch(base)
            picks = fetch(base + "/picks")
            failures = 0
        except Exception as exc:
            failures += 1
            if failures >= 5:
                print(
                    "STATE_MISMATCH "
                    + json.dumps({"reason": "Sleeper API unavailable", "error": str(exc)}),
                    flush=True,
                )
                return 3
            time.sleep(args.interval)
            continue

        status = draft.get("status")
        if status == "complete":
            print(
                "DRAFT_COMPLETE "
                + json.dumps({"draft_id": draft_id, "pick_count": len(picks)}),
                flush=True,
            )
            return 0
        if status not in {"pre_draft", "drafting", "paused"}:
            print(
                "STATE_MISMATCH "
                + json.dumps({"reason": "unexpected draft status", "status": status}),
                flush=True,
            )
            return 4
        if status != "drafting":
            time.sleep(args.interval)
            continue

        if resume_pending is not None:
            recorded = next(
                (pick for pick in picks if int(pick.get("pick_no", -1)) == resume_pending),
                None,
            )
            if recorded is None:
                time.sleep(args.interval)
                continue
            actual_player_id = str(recorded.get("player_id") or "")
            if args.expected_player_id and actual_player_id != str(args.expected_player_id):
                print(
                    "STATE_MISMATCH "
                    + json.dumps(
                        {
                            "reason": "recorded player differs",
                            "draft_id": draft_id,
                            "pick_no": resume_pending,
                            "expected_player_id": str(args.expected_player_id),
                            "actual_player_id": actual_player_id,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
                return 6
            resume_pending = None

        picked = {int(p["pick_no"]) for p in picks if p.get("pick_no") is not None}
        total = args.teams * args.rounds
        current = next((number for number in range(1, total + 1) if number not in picked), None)
        if current is None:
            time.sleep(args.interval)
            continue
        if current in owned:
            print(
                f"{args.event_label} "
                + json.dumps(
                    {
                        "draft_id": draft_id,
                        "pick_no": current,
                        "pick_count": len(picks),
                        "status": status,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0
        time.sleep(args.interval)

    print(
        "STATE_MISMATCH "
        + json.dumps({"reason": "watcher timeout", "draft_id": draft_id}),
        flush=True,
    )
    return 5


if __name__ == "__main__":
    sys.exit(main())
