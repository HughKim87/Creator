#!/usr/bin/env python3
"""Verify that video workflow work is running in the intended Git worktree."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any


DEFAULT_ROUTE = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "worktree-routing.json"
)


HOST_PATH_MAP_ENV = "CREATOR_HOST_PATH_MAP"


def to_host_path(path: Path) -> str:
    """Return the path as the host OS records it.

    Agents that run inside a mounted VM (for example Claude) set
    ``CREATOR_HOST_PATH_MAP=<local_prefix>=<host_prefix>`` so that job records
    keep the same root text as agents running directly on the host (Codex).
    Without the variable the local path is returned unchanged.
    """
    text = str(path)
    mapping = os.environ.get(HOST_PATH_MAP_ENV, "")
    local_prefix, separator, host_prefix = mapping.partition("=")
    if not separator or not local_prefix or not host_prefix:
        return text
    local_prefix = local_prefix.replace('\\', '/').rstrip("/")
    normalized = text.replace('\\', '/')
    if normalized == local_prefix:
        return host_prefix.rstrip('/\\')
    local_prefix += '/'
    if not normalized.startswith(local_prefix):
        return text
    remainder = normalized[len(local_prefix):]
    if "\\" in host_prefix:
        remainder = remainder.replace("/", "\\")
        host_prefix = host_prefix.rstrip("\\") + "\\"
    else:
        host_prefix = host_prefix.rstrip("/") + "/"
    return host_prefix + remainder


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


def load_expected_branch(route_path: Path = DEFAULT_ROUTE) -> str:
    data = json.loads(route_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "video-worktree-route-v1":
        raise ValueError("route schema_version must be video-worktree-route-v1")
    branch = data.get("expected_branch")
    if not isinstance(branch, str) or not branch.strip():
        raise ValueError("route expected_branch must be non-empty text")
    return branch.strip()


def parse_worktree_list(output: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in [*output.splitlines(), ""]:
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key in {"worktree", "branch"} and value:
            current[key] = value
    return entries


def locate_branch_worktree(root: Path, expected_branch: str) -> Path | None:
    expected_ref = f"refs/heads/{expected_branch}"
    entries = parse_worktree_list(_git(root, "worktree", "list", "--porcelain"))
    for entry in entries:
        if entry.get("branch") == expected_ref and entry.get("worktree"):
            return Path(entry["worktree"]).resolve()
    return None


def inspect_worktree(
    root: Path,
    expected_branch: str | None = None,
    *,
    route_path: Path = DEFAULT_ROUTE,
) -> dict[str, Any]:
    requested_root = root.resolve()
    errors: list[str] = []
    try:
        routed_branch = expected_branch or load_expected_branch(route_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "invalid",
            "root": str(requested_root),
            "git_root": None,
            "branch": None,
            "expected_branch": expected_branch,
            "expected_root": None,
            "route": str(route_path.resolve()),
            "errors": [f"cannot load worktree route: {exc}"],
        }

    try:
        git_root = Path(_git(requested_root, "rev-parse", "--show-toplevel")).resolve()
        branch = _git(requested_root, "branch", "--show-current")
        expected_root = locate_branch_worktree(requested_root, routed_branch)
    except (OSError, RuntimeError) as exc:
        return {
            "status": "invalid",
            "root": str(requested_root),
            "git_root": None,
            "branch": None,
            "expected_branch": routed_branch,
            "expected_root": None,
            "route": str(route_path.resolve()),
            "errors": [str(exc)],
        }

    if git_root != requested_root:
        errors.append(f"git root mismatch: expected {requested_root}, got {git_root}")
    if not branch:
        errors.append("detached HEAD is not allowed for video workflow work")
    if expected_root is None:
        errors.append(f"no worktree found for expected branch {routed_branch}")
    elif requested_root != expected_root:
        errors.append(
            f"worktree mismatch: expected {expected_root}, got {requested_root}"
        )
    if branch != routed_branch:
        errors.append(f"branch mismatch: expected {routed_branch}, got {branch}")

    return {
        "status": "valid" if not errors else "invalid",
        "root": to_host_path(requested_root),
        "local_root": str(requested_root),
        "git_root": to_host_path(git_root),
        "branch": branch,
        "expected_branch": routed_branch,
        "expected_root": to_host_path(expected_root) if expected_root else None,
        "expected_local_root": str(expected_root) if expected_root else None,
        "route": str(route_path.resolve()),
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--expected-branch",
        help="Explicit user override; otherwise use the committed route.",
    )
    parser.add_argument("--route", type=Path, default=DEFAULT_ROUTE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = inspect_worktree(
        args.root,
        args.expected_branch,
        route_path=args.route.resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
