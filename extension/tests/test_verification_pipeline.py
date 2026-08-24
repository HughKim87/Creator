"""프로젝트 검증기의 Runtime·inventory·scope·보호 경계 계약 검사."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch


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

    def test_temp_runtime_failure_stops_before_cloning(self) -> None:
        failed = {
            "ok": False,
            "status": "fail",
            "failure_class": "environment",
            "reason": "Node cannot execute below the temporary clone root",
        }
        with (
            patch.object(CLONE, "_probe_temp_runtime", return_value=failed),
            patch.object(CLONE, "_clone_results") as clone_results,
            patch("builtins.print"),
        ):
            returncode = CLONE.main()
        self.assertEqual(returncode, 1)
        clone_results.assert_not_called()

    def test_bootstrap_failure_skips_dependent_verify(self) -> None:
        failed = {"ok": False, "returncode": 1}
        with (
            tempfile.TemporaryDirectory() as raw_temp,
            patch.object(CLONE, "_overlay_worktree"),
            patch.object(CLONE, "_run", return_value=failed) as run,
        ):
            result = CLONE._run_clone_checks(Path(raw_temp))
        self.assertEqual(run.call_count, 1)
        self.assertEqual(result["verify"]["status"], "not_run")
        self.assertFalse(result["ok"])

    def test_temp_runtime_probe_removes_probe_file(self) -> None:
        ready = {"ok": True, "returncode": 0}
        with tempfile.TemporaryDirectory() as raw_temp:
            temp_root = Path(raw_temp)
            with patch.object(CLONE, "_run", return_value=ready) as run:
                result = CLONE._probe_temp_runtime(temp_root)
            probe = temp_root / "node-temp-path-preflight.mjs"
            self.assertFalse(probe.exists())
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args, call(["node", str(probe)], temp_root))

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
