#!/usr/bin/env python3
"""Verify that video workflow work is running in the intended Git worktree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def inspect_worktree(root: Path, expected_branch: str | None = None) -> dict[str, Any]:
    requested_root = root.resolve()
    errors: list[str] = []
    try:
        git_root = Path(_git(requested_root, "rev-parse", "--show-toplevel")).resolve()
        branch = _git(requested_root, "branch", "--show-current")
    except (OSError, RuntimeError) as exc:
        return {
            "status": "invalid",
            "root": str(requested_root),
            "git_root": None,
            "branch": None,
            "expected_branch": expected_branch,
            "errors": [str(exc)],
        }

    if git_root != requested_root:
        errors.append(f"git root mismatch: expected {requested_root}, got {git_root}")
    if not branch:
        errors.append("detached HEAD is not allowed for video workflow work")
    if expected_branch and branch != expected_branch:
        errors.append(f"branch mismatch: expected {expected_branch}, got {branch}")

    return {
        "status": "valid" if not errors else "invalid",
        "root": str(requested_root),
        "git_root": str(git_root),
        "branch": branch,
        "expected_branch": expected_branch,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--expected-branch")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = inspect_worktree(args.root, args.expected_branch)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
