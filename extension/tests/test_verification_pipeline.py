"""Creator Host 검증기의 inventory·보호 경계·출력 계약 검사."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    added = [ROOT / "extension" / "src"]
    for entry in reversed(added):
        sys.path.insert(0, str(entry))
    try:
        spec.loader.exec_module(module)
    finally:
        for _ in added:
            sys.path.pop(0)
    return module


VERIFY = load_module("creator_host_verify", "scripts/verify.py")
INVENTORY = load_module("creator_host_inventory", "scripts/run_test_inventory.py")


class VerificationPipelineTest(unittest.TestCase):
    def test_inventory_matches_current_creator_modules(self) -> None:
        discovered = {path.name for path in INVENTORY.TEST_ROOT.glob("test_*.py")}
        self.assertEqual(discovered, INVENTORY.EXPECTED)

    def test_inventory_drift_is_detected(self) -> None:
        expected = set(INVENTORY.EXPECTED)
        missing_name = sorted(expected)[0]
        missing, unexpected = INVENTORY.inventory_drift(expected - {missing_name})
        self.assertEqual(missing, [missing_name])
        self.assertEqual(unexpected, [])

    def test_full_stdout_is_parsed_before_display_truncation(self) -> None:
        payload = {"ok": True, "padding": "x" * 3000}
        process = VERIFY._run([sys.executable, "-c", f"import json; print(json.dumps({payload!r}))"])
        self.assertLessEqual(len(process["stdout"]), 2000)
        self.assertEqual(VERIFY._parse_json(process), payload)

    def test_git_snapshot_excludes_protected_paths_before_execution(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        with patch.object(VERIFY.subprocess, "run", return_value=completed) as mocked:
            snapshot = VERIFY._git_snapshot()
        command = mocked.call_args.args[0]
        self.assertTrue(snapshot["ok"])
        for pathspec in VERIFY.PROTECTED_PATHSPECS:
            self.assertIn(pathspec, command)


if __name__ == "__main__":
    unittest.main()
