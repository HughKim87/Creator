"""프로젝트 검증기의 Runtime·inventory·scope·보호 경계 계약 검사."""

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
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    added = [ROOT / "core" / "src", ROOT / "core", ROOT / "extension" / "src"]
    for entry in reversed(added):
        sys.path.insert(0, str(entry))
    try:
        spec.loader.exec_module(module)
    finally:
        for _ in added:
            sys.path.pop(0)
    return module


VERIFY = load_module("project_verify_contract", "scripts/verify.py")
INVENTORY = load_module("project_test_inventory", "scripts/run_test_inventory.py")
CLONE = load_module("project_clone_conformance", "scripts/clone_conformance.py")


class VerificationPipelineTest(unittest.TestCase):
    def test_maintained_inventory_matches_current_modules(self) -> None:
        for scope, (test_root, expected) in INVENTORY.INVENTORIES.items():
            discovered = {path.name for path in test_root.glob("test_*.py")}
            self.assertEqual(discovered, expected, scope)

    def test_missing_inventory_module_is_detected(self) -> None:
        expected = set(INVENTORY.INVENTORIES["core"][1])
        missing_name = sorted(expected)[0]
        missing, unexpected = INVENTORY.inventory_drift("core", expected - {missing_name})
        self.assertEqual(missing, [missing_name])
        self.assertEqual(unexpected, [])

    def test_full_stdout_is_parsed_before_display_truncation(self) -> None:
        payload = {"ok": True, "padding": "x" * 3000}
        process = VERIFY._run(
            [sys.executable, "-c", f"import json; print(json.dumps({payload!r}))"]
        )
        self.assertLessEqual(len(process["stdout"]), 2000)
        self.assertEqual(VERIFY._parse_json(process, "long-json"), payload)

    def test_local_and_remote_scope_are_never_conflated(self) -> None:
        local = CLONE._result([{"ok": True}])
        remote = VERIFY._remote_conformance_state()
        self.assertEqual(local["scope"], "local")
        self.assertEqual(local["status"], "pass")
        self.assertEqual(remote["scope"], "remote")
        self.assertEqual(remote["status"], "not_run")
        self.assertIsNone(remote["ok"])

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
