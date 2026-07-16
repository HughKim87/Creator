from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

from video_workflow.checks.execution import ProcessResult, run_process

FORBIDDEN_SEGMENTS = frozenset({"inputs", "outputs"})


def normalize_repo_path(path: str) -> str:
    return path.replace("\\", "/")


def has_forbidden_segment(path: str) -> bool:
    parts = PurePosixPath(normalize_repo_path(path)).parts
    return any(part.lower() in FORBIDDEN_SEGMENTS for part in parts)


def forbidden_tracked_paths(paths: Iterable[str]) -> list[str]:
    return sorted(path for path in paths if has_forbidden_segment(path))


def git_tracked_paths(root: Path) -> tuple[list[str], ProcessResult]:
    injected = os.environ.get("VIDEO_WORKFLOW_TEST_TRACKED_PATH")
    if injected is not None:
        result = ProcessResult(("git", "ls-files"), 0, f"{injected}\0", "")
        return [injected], result
    result = run_process(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "-c",
            f"safe.directory={root.as_posix()}",
            "ls-files",
            "-z",
        ],
        cwd=root,
        timeout=30,
    )
    if result.returncode != 0:
        return [], result
    return [path for path in result.stdout.split("\0") if path], result


def git_root(root: Path) -> tuple[Path | None, ProcessResult]:
    result = run_process(
        [
            "git",
            "-c",
            f"safe.directory={root.resolve().as_posix()}",
            "rev-parse",
            "--show-toplevel",
        ],
        cwd=root,
        timeout=30,
    )
    if result.returncode != 0:
        return None, result
    return Path(result.stdout.strip()).resolve(), result
