#!/usr/bin/env python3
"""Regression tests for live_preflight.py on fake Harbor Cats fixtures."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "live_preflight.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "harbor-mini"

LEAGUE_ID = "league-harbor-mini"
DRAFT_ID = "draft-harbor-mini"


def load_module():
    spec = importlib.util.spec_from_file_location("live_preflight_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def passing_api(url: str):
    if url.startswith("https://api.sleeper.app/v1/draft/") and url.endswith("/picks"):
        return []
    if url.startswith("https://api.sleeper.app/v1/draft/") and url.endswith("/traded_picks"):
        return []
    if "/league/" in url and url.endswith("/rosters"):
        return [
            {"roster_id": 1, "owner_id": "user-harbor", "keepers": ["fake-k1"]},
            {"roster_id": 2, "owner_id": "user-salt", "keepers": ["fake-k2"]},
            {"roster_id": 3, "owner_id": "user-pine", "keepers": []},
            {"roster_id": 4, "owner_id": "user-red", "keepers": []},
        ]
    if "/league/" in url:
        return {"league_id": LEAGUE_ID, "draft_id": DRAFT_ID}
    return {
        "draft_id": DRAFT_ID,
        "league_id": LEAGUE_ID,
        "status": "pre_draft",
        "settings": {"teams": 4, "rounds": 4},
        "draft_order": {
            "user-salt": 1,
            "user-harbor": 2,
            "user-pine": 3,
            "user-red": 4,
        },
        "slot_to_roster_id": {"1": 2, "2": 1, "3": 3, "4": 4},
        "start_time": None,
    }


class LivePreflightTests(unittest.TestCase):
    def run_main(self, argv, fetch=passing_api, extra_env=None):
        module = load_module()
        output = io.StringIO()
        env = {
            "LEAGUE_DATA_DIR": str(FIXTURE),
            "LEAGUE_ID": LEAGUE_ID,
            "DRAFT_ID": DRAFT_ID,
            "TEAM_NAME": "Harbor Cats",
        }
        if extra_env:
            env.update(extra_env)
        with (
            patch.object(sys, "argv", [str(SCRIPT), *argv]),
            patch.object(module, "fetch", side_effect=fetch),
            patch.dict("os.environ", env, clear=False),
            contextlib.redirect_stdout(output),
        ):
            code = module.main()
        return code, json.loads(output.getvalue())

    def test_pass_on_fake_fixtures_and_pre_draft_keeper_warning(self):
        code, result = self.run_main([])
        self.assertEqual(0, code, result)
        self.assertEqual("PASS", result["preflight"])
        self.assertEqual(2, result["draft"]["slot"])
        self.assertEqual([2, 7, 10, 15], result["team"]["owned_cells"])
        self.assertEqual([2, 7, 10], result["team"]["live_selection_cells"])
        self.assertEqual(["fake-k1"], result["team"]["keepers"])
        warning_codes = {row["code"] for row in result["warnings"]}
        self.assertIn("KEEPER_CELLS_PENDING_DRAFT_START", warning_codes)
        queue_ids = [row["id"] for row in result["queue_preview"]]
        self.assertIn("fake-1001", queue_ids)
        self.assertNotIn("fake-k1", queue_ids)
        self.assertNotIn("fake-1004", queue_ids)  # hard avoid
        self.assertNotIn("fake-1005", queue_ids)  # MANUAL

    def test_cli_overrides_env(self):
        code, result = self.run_main(
            [
                "--data-dir", str(FIXTURE),
                "--league-id", LEAGUE_ID,
                "--draft-id", DRAFT_ID,
                "--team-name", "Cole Voss",
                "--expected-slot", "2",
            ],
            extra_env={"TEAM_NAME": "Not A Team"},
        )
        self.assertEqual(0, code, result)
        self.assertEqual("PASS", result["preflight"])

    def test_identity_mismatch_fails_closed(self):
        def bad_identity(url: str):
            payload = passing_api(url)
            if isinstance(payload, dict) and payload.get("draft_id") == DRAFT_ID and "settings" in payload:
                payload = dict(payload)
                payload["league_id"] = "wrong-league"
            return payload

        code, result = self.run_main([], fetch=bad_identity)
        self.assertEqual(2, code)
        self.assertEqual("BLOCK", result["preflight"])
        self.assertEqual("STATE MISMATCH — NO DRAFT AUTHORIZATION", result["authorization"])
        self.assertTrue(any(row["code"] == "DRAFT_IDENTITY_MISMATCH" for row in result["blockers"]))

    def test_missing_env_fails_closed(self):
        code, result = self.run_main([], extra_env={"TEAM_NAME": ""})
        self.assertEqual(2, code)
        self.assertEqual("BLOCK", result["preflight"])
        self.assertEqual("STATE MISMATCH — NO DRAFT AUTHORIZATION", result["authorization"])
        self.assertEqual("MISSING_IDENTITY", result["blockers"][0]["code"])

    def test_keeper_cell_mismatch_after_start_fails_closed(self):
        def drafting_wrong_keepers(url: str):
            payload = passing_api(url)
            if url.endswith("/picks"):
                return [
                    {
                        "pick_no": 15,
                        "player_id": "wrong-keeper",
                        "is_keeper": True,
                    }
                ]
            if isinstance(payload, dict) and "settings" in payload:
                payload = dict(payload)
                payload["status"] = "drafting"
            return payload

        code, result = self.run_main([], fetch=drafting_wrong_keepers)
        self.assertEqual(2, code)
        self.assertEqual("BLOCK", result["preflight"])
        self.assertTrue(any(row["code"] == "KEEPER_CELL_MISMATCH" for row in result["blockers"]))


if __name__ == "__main__":
    unittest.main()
