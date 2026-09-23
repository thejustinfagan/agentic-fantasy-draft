#!/usr/bin/env python3
"""Bounded, deterministic live-draft preflight.

This replaces LLM-driven repository discovery and repeated browser probing during
real-draft initiation. It performs read-only local/API checks and emits one JSON
object. Exit 0 means the state gates passed; exit 2 means fail closed.

Identity and paths come from environment or CLI only:

  LEAGUE_DATA_DIR   local artifact directory (doctrine + CSVs)
  LEAGUE_ID         Sleeper league id
  DRAFT_ID          Sleeper draft id
  TEAM_NAME         displayed team or owner label to resolve
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

REQUIRED_FILES = {
    "playbook": "DOCTRINE.md",
    "board": "player_board.csv",
    "tiers": "position_tiers.csv",
    "rookies": "rookie_option_board.csv",
    "controls": "hard_avoid.csv",
    "keepers": "keeper_cells.csv",
    "ownership": "pick_ownership.csv",
    "order": "draft_order.csv",
}

STATE_MISMATCH = "STATE MISMATCH — NO DRAFT AUTHORIZATION"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value: object, default: int = 10**9) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def pick_number(slot: int, round_no: int, teams: int) -> int:
    within = slot if round_no % 2 else teams + 1 - slot
    return (round_no - 1) * teams + within


def fetch(url: str) -> object:
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(
        f"{url}{sep}_={time.time_ns()}",
        headers={
            "User-Agent": "Grok-Bot-Live-Preflight/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def git_value(repo: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL, timeout=5
        ).strip()
    except Exception:
        return None


def live_owner_by_cell(
    slot_to_roster: dict[int, int], traded: list[dict], rounds: int
) -> dict[int, int]:
    trades: dict[tuple[int, int], int] = {}
    for row in traded:
        rnd = number(row.get("round"), -1)
        original = number(row.get("roster_id"), -1)
        owner = number(row.get("owner_id"), -1)
        if rnd > 0 and original > 0 and owner > 0:
            trades[(rnd, original)] = owner
    owners: dict[int, int] = {}
    for rnd in range(1, rounds + 1):
        for slot, original in slot_to_roster.items():
            owners[pick_number(slot, rnd, len(slot_to_roster))] = trades.get(
                (rnd, original), original
            )
    return owners


def is_keeper_pick(row: dict) -> bool:
    if row.get("is_keeper") is True:
        return True
    metadata = row.get("metadata") or {}
    return metadata.get("is_keeper") in {True, "true", "1", 1}


def env_or_cli(cli_value: str | None, env_name: str) -> str:
    return (cli_value or os.environ.get(env_name) or "").strip()


def row_labels(row: dict[str, str]) -> set[str]:
    labels = set()
    for key in ("team_name", "owner_name", "team_label", "team"):
        value = (row.get(key) or "").strip()
        if value:
            labels.add(value.casefold())
    return labels


def label_matches(row: dict[str, str], team_name: str) -> bool:
    return team_name.casefold() in row_labels(row)


def aliases_for_team(team_row: dict[str, str], team_name: str) -> set[str]:
    aliases = row_labels(team_row)
    aliases.add(team_name.casefold())
    return aliases


def keeper_belongs_to_team(row: dict[str, str], aliases: set[str]) -> bool:
    return bool(row_labels(row) & aliases)


def resolve_team(order: list[dict[str, str]], team_name: str) -> dict[str, str] | None:
    matches = [row for row in order if label_matches(row, team_name)]
    if len(matches) == 1:
        return matches[0]
    return None


def block_payload(blockers: list[dict[str, object]], **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "preflight": "BLOCK",
        "authorization": STATE_MISMATCH,
        "blockers": blockers,
    }
    payload.update(extra)
    return payload


def emit(payload: dict[str, object]) -> int:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if payload.get("preflight") == "PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", help="Local league artifact directory (or LEAGUE_DATA_DIR)")
    parser.add_argument("--draft-id", help="Sleeper draft id (or DRAFT_ID)")
    parser.add_argument("--league-id", help="Sleeper league id (or LEAGUE_ID)")
    parser.add_argument("--team-name", help="Team or owner label (or TEAM_NAME)")
    parser.add_argument("--roster-id", type=int, help="Override roster id after label resolution")
    parser.add_argument("--expected-slot", type=int, help="Optional live slot that must match")
    args = parser.parse_args()

    started = time.monotonic()
    data_dir = env_or_cli(str(args.data_dir) if args.data_dir else None, "LEAGUE_DATA_DIR")
    draft_id = env_or_cli(args.draft_id, "DRAFT_ID")
    league_id = env_or_cli(args.league_id, "LEAGUE_ID")
    team_name = env_or_cli(args.team_name, "TEAM_NAME")

    blockers: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []

    missing_identity = [
        name
        for name, value in (
            ("LEAGUE_DATA_DIR", data_dir),
            ("DRAFT_ID", draft_id),
            ("LEAGUE_ID", league_id),
            ("TEAM_NAME", team_name),
        )
        if not value
    ]
    if missing_identity:
        return emit(
            block_payload(
                [{"code": "MISSING_IDENTITY", "fields": missing_identity}],
                elapsed_seconds=round(time.monotonic() - started, 3),
            )
        )

    repo = Path(data_dir).expanduser().resolve()
    paths = {name: repo / rel for name, rel in REQUIRED_FILES.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        return emit(block_payload([{"code": "MISSING_ARTIFACTS", "paths": missing}]))

    try:
        board = csv_rows(paths["board"])
        tiers = csv_rows(paths["tiers"])
        rookies = csv_rows(paths["rookies"])
        controls = csv_rows(paths["controls"])
        keepers = csv_rows(paths["keepers"])
        ownership = csv_rows(paths["ownership"])
        order = csv_rows(paths["order"])
    except Exception as exc:
        return emit(block_payload([{"code": "ARTIFACT_PARSE_FAILED", "error": str(exc)}]))

    team_row = resolve_team(order, team_name)
    if team_row is None:
        return emit(
            block_payload(
                [
                    {
                        "code": "TEAM_IDENTITY_UNRESOLVED",
                        "team_name": team_name,
                        "known_labels": sorted(
                            {
                                (row.get(key) or "").strip()
                                for row in order
                                for key in ("team_name", "owner_name", "team_label", "team")
                                if (row.get(key) or "").strip()
                            }
                        ),
                    }
                ]
            )
        )

    roster_id = args.roster_id if args.roster_id is not None else number(team_row.get("roster_id"), -1)
    team_owner_id = str(team_row.get("owner_id") or "")
    if roster_id < 1 or not team_owner_id:
        return emit(
            block_payload(
                [
                    {
                        "code": "TEAM_IDENTITY_INCOMPLETE",
                        "roster_id": roster_id,
                        "owner_id": team_owner_id,
                    }
                ]
            )
        )

    team_aliases = aliases_for_team(team_row, team_name)
    team_keepers = {
        row.get("sleeper_id", "").strip(): number(row.get("keeper_round"), -1)
        for row in keepers
        if keeper_belongs_to_team(row, team_aliases) and row.get("sleeper_id", "").strip()
    }

    board_ids = [row.get("sleeper_id", "").strip() for row in board]
    keeper_ids = [row.get("sleeper_id", "").strip() for row in keepers]
    if not board_ids or "" in board_ids or len(board_ids) != len(set(board_ids)):
        blockers.append({"code": "BOARD_ID_INTEGRITY", "rows": len(board_ids), "unique": len(set(board_ids))})
    if not keeper_ids or "" in keeper_ids or len(keeper_ids) != len(set(keeper_ids)):
        blockers.append({"code": "KEEPER_ID_INTEGRITY", "rows": len(keeper_ids), "unique": len(set(keeper_ids))})

    urls = {
        "draft": f"https://api.sleeper.app/v1/draft/{draft_id}",
        "picks": f"https://api.sleeper.app/v1/draft/{draft_id}/picks",
        "traded": f"https://api.sleeper.app/v1/draft/{draft_id}/traded_picks",
        "league": f"https://api.sleeper.app/v1/league/{league_id}",
        "rosters": f"https://api.sleeper.app/v1/league/{league_id}/rosters",
    }
    api: dict[str, object] = {}
    api_errors: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:
        futures = {pool.submit(fetch, url): name for name, url in urls.items()}
        for future, name in [(item, futures[item]) for item in futures]:
            try:
                api[name] = future.result()
            except Exception as exc:
                api_errors[name] = f"{type(exc).__name__}: {exc}"
    if api_errors:
        return emit(
            block_payload(
                [{"code": "SLEEPER_API_UNAVAILABLE", "endpoints": api_errors}],
                elapsed_seconds=round(time.monotonic() - started, 3),
            )
        )

    draft = api["draft"]
    picks = api["picks"]
    traded = api["traded"]
    league = api["league"]
    rosters = api["rosters"]
    assert isinstance(draft, dict) and isinstance(picks, list)
    assert isinstance(traded, list) and isinstance(league, dict) and isinstance(rosters, list)

    settings = draft.get("settings") or {}
    status = draft.get("status")
    teams = number(settings.get("teams"), -1)
    rounds = number(settings.get("rounds"), -1)
    if teams < 2 or rounds < 1:
        blockers.append({"code": "FORMAT_UNREADABLE", "teams": teams, "rounds": rounds})
        teams = max(teams, 2)
        rounds = max(rounds, 1)

    pick_ids = [number(row.get("pick_no"), -1) for row in ownership]
    expected_cells = teams * rounds
    if (
        len(ownership) != expected_cells
        or len(set(pick_ids)) != len(pick_ids)
        or min(pick_ids, default=-1) != 1
        or max(pick_ids, default=-1) != expected_cells
    ):
        blockers.append(
            {
                "code": "OWNERSHIP_INTEGRITY",
                "rows": len(ownership),
                "unique_picks": len(set(pick_ids)),
                "expected_cells": expected_cells,
            }
        )
    wrong_draft_rows = sum(1 for row in ownership if row.get("draft_id") != draft_id)
    if wrong_draft_rows:
        blockers.append({"code": "OWNERSHIP_WRONG_DRAFT", "rows": wrong_draft_rows})

    if draft.get("draft_id") != draft_id or draft.get("league_id") != league_id:
        blockers.append(
            {
                "code": "DRAFT_IDENTITY_MISMATCH",
                "draft_id": draft.get("draft_id"),
                "league_id": draft.get("league_id"),
            }
        )
    if league.get("league_id") != league_id or league.get("draft_id") != draft_id:
        blockers.append({"code": "LEAGUE_IDENTITY_MISMATCH", "league_draft_id": league.get("draft_id")})
    if status not in {"pre_draft", "drafting", "paused"}:
        blockers.append({"code": "DRAFT_STATUS_INVALID", "status": status})

    draft_order = draft.get("draft_order")
    slot_map_raw = draft.get("slot_to_roster_id") or {}
    slot_to_roster = {number(slot, -1): number(roster, -1) for slot, roster in slot_map_raw.items()}
    slot_to_roster = {slot: roster for slot, roster in slot_to_roster.items() if slot > 0 and roster > 0}
    if not isinstance(draft_order, dict) or not draft_order:
        blockers.append({"code": "FINAL_DRAFT_ORDER_UNSET", "draft_order": draft_order})
    if len(slot_to_roster) != teams or len(set(slot_to_roster.values())) != teams:
        blockers.append({"code": "SLOT_MAP_INVALID", "slot_map": slot_map_raw})

    roster_row = next((row for row in rosters if number(row.get("roster_id"), -1) == roster_id), None)
    if not roster_row or str(roster_row.get("owner_id")) != team_owner_id:
        blockers.append({"code": "TEAM_IDENTITY_MISMATCH", "roster": roster_row, "expected_owner_id": team_owner_id})

    api_keeper_ids = {
        str(player_id)
        for row in rosters
        for player_id in (row.get("keepers") or [])
    }
    local_keeper_ids = set(keeper_ids)
    if api_keeper_ids != local_keeper_ids:
        blockers.append(
            {
                "code": "KEEPER_SET_MISMATCH",
                "api_minus_local": sorted(api_keeper_ids - local_keeper_ids),
                "local_minus_api": sorted(local_keeper_ids - api_keeper_ids),
            }
        )
    team_api_keepers = {str(value) for value in ((roster_row or {}).get("keepers") or [])}
    if team_api_keepers != set(team_keepers):
        blockers.append(
            {
                "code": "TEAM_KEEPER_MISMATCH",
                "api": sorted(team_api_keepers),
                "expected": sorted(team_keepers),
            }
        )

    expected_keeper_cells: dict[int, str] = {}
    keeper_mapping_errors: list[str] = []
    roster_to_slot = {roster: slot for slot, roster in slot_to_roster.items()}
    observed_team_slot = roster_to_slot.get(roster_id)
    if args.expected_slot is not None and observed_team_slot != args.expected_slot:
        blockers.append(
            {
                "code": "EXPECTED_SLOT_NOT_LIVE",
                "expected": args.expected_slot,
                "observed": observed_team_slot,
                "final_order_set": bool(isinstance(draft_order, dict) and draft_order),
            }
        )

    label_to_roster = {}
    for row in order:
        rid = number(row.get("roster_id"), -1)
        if rid < 1:
            continue
        for key in ("team_name", "owner_name", "team_label", "team"):
            label = (row.get(key) or "").strip()
            if label:
                label_to_roster[label.casefold()] = rid

    for row in keepers:
        roster_for_keeper = label_to_roster.get((row.get("team_label") or row.get("team_name") or "").strip().casefold())
        slot = roster_to_slot.get(roster_for_keeper) if roster_for_keeper else None
        rnd = number(row.get("keeper_round"), -1)
        if not slot or rnd < 1:
            keeper_mapping_errors.append(row.get("keeper_name", "unknown"))
            continue
        expected_keeper_cells[pick_number(slot, rnd, teams)] = row.get("sleeper_id", "")
    if keeper_mapping_errors:
        blockers.append({"code": "KEEPER_CELL_MAPPING_FAILED", "players": keeper_mapping_errors})

    preloaded = {number(row.get("pick_no"), -1): str(row.get("player_id")) for row in picks if is_keeper_pick(row)}
    if status == "pre_draft" and len(preloaded) != len(keepers):
        warnings.append(
            {
                "code": "KEEPER_CELLS_PENDING_DRAFT_START",
                "expected": len(keepers),
                "observed": len(preloaded),
                "note": "Keepers populate when the draft begins; verify exact cells within 20 seconds of the drafting transition.",
            }
        )
    if preloaded and preloaded != expected_keeper_cells:
        blockers.append(
            {
                "code": "KEEPER_CELL_MISMATCH",
                "missing_or_wrong": {
                    str(cell): player_id
                    for cell, player_id in expected_keeper_cells.items()
                    if preloaded.get(cell) != player_id
                },
                "unexpected": {
                    str(cell): player_id
                    for cell, player_id in preloaded.items()
                    if expected_keeper_cells.get(cell) != player_id
                },
            }
        )

    artifact_owned = sorted(
        number(row.get("pick_no"), -1)
        for row in ownership
        if number(row.get("current_roster_id"), -1) == roster_id
    )
    live_owned: list[int] = []
    if len(slot_to_roster) == teams:
        owner_by_pick = live_owner_by_cell(slot_to_roster, traded, rounds)
        live_owned = sorted(pick_no for pick_no, owner in owner_by_pick.items() if owner == roster_id)
        if artifact_owned != live_owned:
            blockers.append({"code": "OWNED_PICK_MISMATCH", "artifact": artifact_owned, "live": live_owned})

    team_slot = roster_to_slot.get(roster_id)
    team_keeper_cells = {
        pick_number(team_slot, rnd, teams) for rnd in team_keepers.values()
    } if team_slot else set()
    team_live_picks = [pick for pick in live_owned if pick not in team_keeper_cells]
    expected_live_count = max(0, (rounds if team_slot else 0) - len(team_keepers))
    if live_owned and len(team_live_picks) != expected_live_count:
        blockers.append(
            {
                "code": "TEAM_LIVE_PICK_COUNT",
                "count": len(team_live_picks),
                "expected": expected_live_count,
                "picks": team_live_picks,
            }
        )

    drafted_ids = {str(row.get("player_id")) for row in picks if row.get("player_id") is not None}
    picked_numbers = {number(row.get("pick_no"), -1) for row in picks}
    current_pick = next((pick for pick in range(1, teams * rounds + 1) if pick not in picked_numbers), None)
    current_round = ((current_pick - 1) // teams + 1) if current_pick else rounds

    controls_blocked = {row.get("sleeper_id", "") for row in controls if row.get("sleeper_id")}
    rookie_by_id = {row.get("sleeper_id", ""): row for row in rookies}
    safe: list[dict[str, object]] = []
    manual_nearby: list[dict[str, object]] = []
    for row in sorted(board, key=lambda item: (number(item.get("available_rank")), number(item.get("pool_rank")))):
        player_id = row.get("sleeper_id", "")
        availability = (row.get("availability") or "").upper()
        rookie = rookie_by_id.get(player_id)
        rookie_block = bool(rookie) and (rookie.get("auto_eligible") or "").lower() != "true"
        too_early = bool(rookie) and number(rookie.get("target_earliest_round"), 0) > current_round
        blocked = availability != "AVAILABLE" or player_id in controls_blocked or rookie_block or too_early
        if player_id in drafted_ids or player_id in api_keeper_ids:
            continue
        item = {
            "name": row.get("player_name"),
            "position": row.get("position"),
            "team": row.get("team"),
            "id": player_id,
            "rank": number(row.get("available_rank"), number(row.get("pool_rank"))),
        }
        if blocked:
            if availability == "MANUAL" and len(manual_nearby) < 5:
                manual_nearby.append(item)
            continue
        if len(safe) < 12:
            safe.append(item)

    dirty = (git_value(repo, "status", "--short") or "").splitlines()
    if dirty:
        warnings.append({"code": "LOCAL_REPO_DIRTY", "paths": dirty})

    status_counts = Counter((row.get("availability") or "UNKNOWN") for row in board)
    result: dict[str, object] = {
        "preflight": "PASS" if not blockers else "BLOCK",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "draft": {
            "id": draft_id,
            "status": status,
            "slot": team_slot,
            "current_pick": current_pick,
            "pick_count": len(picks),
            "start_time": draft.get("start_time"),
        },
        "team": {
            "name": team_name,
            "roster_id": roster_id,
            "owned_cells": live_owned,
            "live_selection_cells": team_live_picks,
            "keepers": sorted(team_api_keepers),
        },
        "artifacts": {
            "repo": str(repo),
            "head": git_value(repo, "rev-parse", "HEAD"),
            "board_rows": len(board),
            "tier_rows": len(tiers),
            "keeper_rows": len(keepers),
            "ownership_rows": len(ownership),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "queue_preview": safe,
        "manual_nearby": manual_nearby,
        "warnings": warnings,
        "blockers": blockers,
    }
    if blockers:
        result["authorization"] = STATE_MISMATCH
    return emit(result)


if __name__ == "__main__":
    sys.exit(main())
