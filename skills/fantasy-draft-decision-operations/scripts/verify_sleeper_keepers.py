#!/usr/bin/env python3
"""Verify exact keeper coordinates for an untraded Sleeper snake mock.

Manifest JSON shape:

[
  {"slot": 2, "round": 4, "player_id": "fake-k1", "name": "Reed Calder"}
]

With --draft-id (or DRAFT_ID), the script cache-busts Sleeper's public picks
endpoint and checks pick number, draft slot, round, and exact player ID. For
traded picks, use the authoritative ownership artifact instead of this snake
formula.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path


def coordinate(teams: int, slot: int, round_no: int) -> dict:
    if teams < 2 or not 1 <= slot <= teams or round_no < 1:
        raise ValueError(f"invalid coordinate: teams={teams} slot={slot} round={round_no}")
    within = slot if round_no % 2 else teams + 1 - slot
    overall = (round_no - 1) * teams + within
    return {
        "slot": slot,
        "round": round_no,
        "within_round": within,
        "overall_pick": overall,
        "cell_label": f"{round_no}.{within}",
    }


def fetch_picks(draft_id: str) -> list[dict]:
    stamp = int(time.time() * 1000)
    url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks?_={stamp}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Grok-Bot-Keeper-Cell-Verifier/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--teams", type=int, default=12)
    parser.add_argument("--draft-id", help="Sleeper draft id (or DRAFT_ID)")
    args = parser.parse_args()

    draft_id = (args.draft_id or os.environ.get("DRAFT_ID") or "").strip()

    manifest = json.loads(args.manifest.read_text())
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("manifest must be a non-empty JSON list")

    expected = []
    for row in manifest:
        item = coordinate(args.teams, int(row["slot"]), int(row["round"]))
        item.update(
            player_id=str(row["player_id"]),
            name=row.get("name", ""),
        )
        expected.append(item)

    pick_numbers = [item["overall_pick"] for item in expected]
    player_ids = [item["player_id"] for item in expected]
    errors = []
    if len(set(pick_numbers)) != len(pick_numbers):
        errors.append("duplicate expected keeper pick")
    if len(set(player_ids)) != len(player_ids):
        errors.append("duplicate expected keeper player ID")

    checks = []
    if draft_id:
        actual = {int(pick["pick_no"]): pick for pick in fetch_picks(draft_id)}
        for item in expected:
            pick = actual.get(item["overall_pick"])
            mismatch = []
            if pick is None:
                mismatch.append("missing pick")
            else:
                if str(pick.get("player_id")) != item["player_id"]:
                    mismatch.append(f"player_id={pick.get('player_id')}")
                if int(pick.get("draft_slot") or -1) != item["slot"]:
                    mismatch.append(f"draft_slot={pick.get('draft_slot')}")
                if int(pick.get("round") or -1) != item["round"]:
                    mismatch.append(f"round={pick.get('round')}")
            checks.append({**item, "ok": not mismatch, "mismatch": mismatch})
            errors.extend(f"{item['cell_label']}: {problem}" for problem in mismatch)
    else:
        checks = [{**item, "ok": True, "mismatch": []} for item in expected]

    result = {
        "ok": not errors,
        "teams": args.teams,
        "keeper_count": len(expected),
        "checks": checks,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
