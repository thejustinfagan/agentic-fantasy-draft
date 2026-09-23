#!/usr/bin/env python3
"""Regression tests for sleeper_turn_watcher.py."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "sleeper_turn_watcher.py"


def load_watcher():
    spec = importlib.util.spec_from_file_location("sleeper_turn_watcher_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def pick(number: int, player_id: str | None = None):
    result = {"pick_no": number}
    if player_id is not None:
        result["player_id"] = player_id
    return result


class SleeperTurnWatcherTests(unittest.TestCase):
    def run_main(self, argv, fetch):
        watcher = load_watcher()
        output = io.StringIO()
        with (
            patch.object(sys, "argv", [str(SCRIPT), *argv]),
            patch.object(watcher, "fetch", side_effect=fetch),
            patch.object(watcher.time, "sleep", return_value=None),
            contextlib.redirect_stdout(output),
        ):
            code = watcher.main()
        return code, output.getvalue().strip()

    def test_uses_requested_event_label_for_current_owned_pick(self):
        def fake_fetch(url):
            if url.endswith("/picks"):
                return [pick(number) for number in range(1, 12)]
            return {"status": "drafting"}

        code, output = self.run_main(
            [
                "--draft-id", "draft-harbor-mini",
                "--owned-picks", "12,29",
                "--teams", "10",
                "--rounds", "19",
                "--interval", "0",
                "--timeout", "1",
                "--event-label", "HARBOR_CATS_ON_CLOCK",
            ],
            fake_fetch,
        )

        self.assertEqual(0, code)
        self.assertTrue(output.startswith("HARBOR_CATS_ON_CLOCK "), output)
        self.assertIn('"pick_no": 12', output)

    def test_resume_waits_for_exact_current_pick_then_monitors_next_owned_pick(self):
        pick_snapshots = iter(
            [
                [pick(number) for number in range(1, 12)],
                [*[pick(number) for number in range(1, 12)], pick(12, "fake-1008")],
                [
                    *[pick(number) for number in range(1, 12)],
                    pick(12, "fake-1008"),
                    *[pick(number) for number in range(13, 29)],
                ],
            ]
        )

        def fake_fetch(url):
            if url.endswith("/picks"):
                return next(pick_snapshots)
            return {"status": "drafting"}

        code, output = self.run_main(
            [
                "--draft-id", "draft-harbor-mini",
                "--owned-picks", "12,29",
                "--teams", "10",
                "--rounds", "19",
                "--interval", "0",
                "--timeout", "1",
                "--event-label", "HARBOR_CATS_ON_CLOCK",
                "--resume-after-pick", "12",
                "--expected-player-id", "fake-1008",
            ],
            fake_fetch,
        )

        self.assertEqual(0, code)
        self.assertTrue(output.startswith("HARBOR_CATS_ON_CLOCK "), output)
        self.assertIn('"pick_no": 29', output)

    def test_resume_fails_closed_when_recorded_player_is_wrong(self):
        recorded = [*[pick(number) for number in range(1, 12)], pick(12, "wrong-id")]

        def fake_fetch(url):
            if url.endswith("/picks"):
                return recorded
            return {"status": "drafting"}

        code, output = self.run_main(
            [
                "--draft-id", "draft-harbor-mini",
                "--owned-picks", "12,29",
                "--teams", "10",
                "--rounds", "19",
                "--interval", "0",
                "--timeout", "1",
                "--event-label", "HARBOR_CATS_ON_CLOCK",
                "--resume-after-pick", "12",
                "--expected-player-id", "fake-1008",
            ],
            fake_fetch,
        )

        self.assertEqual(6, code)
        self.assertTrue(output.startswith("STATE_MISMATCH "), output)
        self.assertIn("recorded player differs", output)

    def test_missing_draft_id_fails_closed(self):
        code, output = self.run_main(
            ["--owned-picks", "12"],
            lambda url: {"status": "drafting"},
        )
        self.assertEqual(2, code)
        self.assertTrue(output.startswith("STATE_MISMATCH "), output)


if __name__ == "__main__":
    unittest.main()
