#!/usr/bin/env python3
"""Regression tests for verify_sleeper_keepers.py on fake fixtures."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "verify_sleeper_keepers.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "harbor-mini" / "keeper_manifest.json"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_sleeper_keepers_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifySleeperKeepersTests(unittest.TestCase):
    def run_main(self, argv, fetch=None):
        module = load_module()
        output = io.StringIO()
        patches = [
            patch.object(sys, "argv", [str(SCRIPT), *argv]),
            contextlib.redirect_stdout(output),
        ]
        if fetch is not None:
            patches.append(patch.object(module, "fetch_picks", side_effect=fetch))
        with patches[0], patches[1]:
            if fetch is not None:
                with patches[2]:
                    code = module.main()
            else:
                code = module.main()
        return code, json.loads(output.getvalue())

    def test_offline_manifest_computes_snake_cells(self):
        code, result = self.run_main([str(FIXTURE), "--teams", "4"])
        self.assertEqual(0, code)
        self.assertTrue(result["ok"])
        self.assertEqual(2, result["keeper_count"])
        labels = {row["cell_label"] for row in result["checks"]}
        # Harbor Cats slot 2 / round 4 even: within = 4+1-2 = 3 → 4.3 overall 15
        # Salt Wren slot 1 / round 3 odd: within = 1 → 3.1 overall 9
        self.assertEqual({"4.3", "3.1"}, labels)
        harbor = next(row for row in result["checks"] if row["player_id"] == "fake-k1")
        self.assertEqual(15, harbor["overall_pick"])

    def test_live_ledger_mismatch_fails_closed(self):
        def fake_fetch(_draft_id):
            return [
                {"pick_no": 15, "player_id": "wrong", "draft_slot": 2, "round": 4},
                {"pick_no": 9, "player_id": "fake-k2", "draft_slot": 1, "round": 3},
            ]

        code, result = self.run_main(
            [str(FIXTURE), "--teams", "4", "--draft-id", "draft-harbor-mini"],
            fetch=fake_fetch,
        )
        self.assertEqual(1, code)
        self.assertFalse(result["ok"])
        self.assertTrue(any("player_id=" in error for error in result["errors"]))

    def test_duplicate_ids_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    [
                        {"slot": 1, "round": 1, "player_id": "dup", "name": "A"},
                        {"slot": 2, "round": 1, "player_id": "dup", "name": "B"},
                    ]
                )
            )
            code, result = self.run_main([str(path), "--teams", "4"])
        self.assertEqual(1, code)
        self.assertIn("duplicate expected keeper player ID", result["errors"])


if __name__ == "__main__":
    unittest.main()
