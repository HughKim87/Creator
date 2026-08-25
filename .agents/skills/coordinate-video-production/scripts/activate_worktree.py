#!/usr/bin/env python3
"""Resolve and validate the routed worktree for the video workflow.

The calling shell cannot change the parent Codex process's current directory.
This helper therefore resolves the canonical worktree and returns it as the
active execution root so every subsequent command can target it explicitly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from check_worktree import inspect_worktree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--expected-branch",
        help="Explicit user override; otherwise use the committed route.",
    )
    parser.add_argument("--route", type=Path, default=None)
    return parser.parse_args()


def resolve_active_worktree(
    root: Path,
    expected_branch: str | None = None,
    route_path: Path | None = None,
) -> dict[str, Any]:
    source_root = root.resolve()
    probe = inspect_worktree(
        source_root,
        expected_branch,
        **({"route_path": route_path.resolve()} if route_path else {}),
    )

    if probe["status"] == "valid":
        return {
            "status": "valid",
            "redirected": False,
            "source_root": str(source_root),
            "active_root": probe["root"],
            "active_branch": probe["branch"],
            "initial_check": probe,
            "final_check": probe,
        }

    expected_root_text = probe.get("expected_root")
    if not expected_root_text:
        return {
            "status": "invalid",
            "redirected": False,
            "source_root": str(source_root),
            "active_root": None,
            "active_branch": None,
            "initial_check": probe,
            "final_check": None,
            "errors": probe.get("errors", []),
        }

    expected_root = Path(expected_root_text).resolve()
    if not expected_root.exists():
        return {
            "status": "invalid",
            "redirected": False,
            "source_root": str(source_root),
            "active_root": str(expected_root),
            "active_branch": None,
            "initial_check": probe,
            "final_check": None,
            "errors": [f"expected worktree does not exist: {expected_root}"],
        }

    final_check = inspect_worktree(
        expected_root,
        expected_branch,
        **({"route_path": route_path.resolve()} if route_path else {}),
    )
    if final_check["status"] != "valid":
        return {
            "status": "invalid",
            "redirected": True,
            "source_root": str(source_root),
            "active_root": str(expected_root),
            "active_branch": final_check.get("branch"),
            "initial_check": probe,
            "final_check": final_check,
            "errors": final_check.get("errors", []),
        }

    return {
        "status": "valid",
        "redirected": True,
        "source_root": str(source_root),
        "active_root": final_check["root"],
        "active_branch": final_check["branch"],
        "initial_check": probe,
        "final_check": final_check,
    }


def main() -> int:
    args = parse_args()
    result = resolve_active_worktree(
        args.root,
        args.expected_branch,
        args.route,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
