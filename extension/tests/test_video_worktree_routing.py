from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "coordinate-video-production"
    / "scripts"
    / "check_worktree.py"
)
SKILL = SCRIPT.parent.parent / "SKILL.md"
SPEC = importlib.util.spec_from_file_location("check_worktree", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VideoWorktreeRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="video-worktree-route-")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.main = self.workspace / "main"
        self.target = self.workspace / "ainotebook"
        self.main.mkdir()
        self.target.mkdir()
        self.route = self.workspace / "route.json"
        self.route.write_text(
            json.dumps(
                {
                    "schema_version": "video-worktree-route-v1",
                    "expected_branch": "codex/ainotebook",
                }
            ),
            encoding="utf-8",
        )

    def _git(self, root: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return str(root)
        if args == ("branch", "--show-current"):
            return "codex/ainotebook" if root == self.target else "main"
        if args == ("worktree", "list", "--porcelain"):
            return (
                f"worktree {self.main}\n"
                "HEAD 1111111\n"
                "branch refs/heads/main\n\n"
                f"worktree {self.target}\n"
                "HEAD 2222222\n"
                "branch refs/heads/codex/ainotebook\n"
            )
        raise AssertionError(args)

    def test_route_file_supplies_expected_branch(self) -> None:
        self.assertEqual(
            MODULE.load_expected_branch(self.route),
            "codex/ainotebook",
        )

    def test_main_is_invalid_and_reports_target_worktree(self) -> None:
        with patch.object(MODULE, "_git", side_effect=self._git):
            result = MODULE.inspect_worktree(self.main, route_path=self.route)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(Path(result["expected_root"]), self.target.resolve())
        self.assertTrue(
            any("worktree mismatch" in error for error in result["errors"])
        )
        self.assertTrue(any("branch mismatch" in error for error in result["errors"]))

    def test_configured_worktree_and_branch_are_valid(self) -> None:
        with patch.object(MODULE, "_git", side_effect=self._git):
            result = MODULE.inspect_worktree(self.target, route_path=self.route)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["expected_branch"], "codex/ainotebook")

    def test_missing_configured_branch_never_falls_back_to_main(self) -> None:
        def missing_branch_git(root: Path, *args: str) -> str:
            if args == ("worktree", "list", "--porcelain"):
                return (
                    f"worktree {self.main}\n"
                    "HEAD 1111111\n"
                    "branch refs/heads/main\n"
                )
            return self._git(root, *args)

        with patch.object(MODULE, "_git", side_effect=missing_branch_git):
            result = MODULE.inspect_worktree(self.main, route_path=self.route)
        self.assertEqual(result["status"], "invalid")
        self.assertIsNone(result["expected_root"])
        self.assertTrue(
            any("no worktree found" in error for error in result["errors"])
        )

    def test_skill_forbids_current_branch_and_unrelated_handoff_fallbacks(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("현재 브랜치를 기대값으로 채우지 않는다", text)
        self.assertIn("`main`으로 대체하지 않는다", text)
        self.assertIn("비-NotebookLM 작업", text)
        self.assertIn("expected_root", text)


if __name__ == "__main__":
    unittest.main()
