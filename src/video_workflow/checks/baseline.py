from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from video_workflow.checks.execution import run_process
from video_workflow.checks.repository import git_tracked_paths, has_forbidden_segment

ALLOWED_ROLES = frozenset({"code", "test", "contract", "doc"})
MANIFEST_PATH = Path("docs/rebuild/stage-00/BACKUP_MANIFEST.json")


@dataclass(frozen=True)
class BaselineCheck:
    code: str
    ok: bool
    message: str


def _safe_manifest_path(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or has_forbidden_segment(normalized):
        return None
    return normalized


def _load_manifest(root: Path) -> tuple[list[dict[str, object]], BaselineCheck]:
    path = root / MANIFEST_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [], BaselineCheck("manifest_parse", False, type(exc).__name__)
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        return [], BaselineCheck("manifest_parse", False, "schema_version must be 2")
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        return [], BaselineCheck("manifest_parse", False, "files must be a non-empty list")
    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in files:
        if not isinstance(raw, dict):
            return [], BaselineCheck("manifest_parse", False, "invalid file entry")
        item = dict(raw)
        relative = _safe_manifest_path(item.get("path"))
        role = item.get("role")
        digest = item.get("sha256")
        if (
            relative is None
            or role not in ALLOWED_ROLES
            or not isinstance(digest, str)
            or len(digest) != 64
            or relative in seen
        ):
            return [], BaselineCheck("manifest_parse", False, "unsafe or duplicate entry")
        seen.add(relative)
        item["path"] = relative
        entries.append(item)
    return entries, BaselineCheck("manifest_parse", True, f"valid entries: {len(entries)}")


def _tracked_manifest_check(root: Path, entries: list[dict[str, object]]) -> BaselineCheck:
    tracked, result = git_tracked_paths(root)
    if result.returncode != 0:
        return BaselineCheck("manifest_tracked_set", False, result.stderr.strip())
    actual = {
        path.replace("\\", "/")
        for path in tracked
        if path.replace("\\", "/").startswith("backup/") and not has_forbidden_segment(path)
    }
    expected = {f"backup/{entry['path']}" for entry in entries}
    if actual != expected:
        return BaselineCheck(
            "manifest_tracked_set",
            False,
            f"expected {len(expected)}, actual {len(actual)}",
        )
    return BaselineCheck("manifest_tracked_set", True, f"matched: {len(expected)}")


def _hash_check(root: Path, entries: list[dict[str, object]]) -> BaselineCheck:
    backup_root = (root / "backup").resolve()
    mismatches = 0
    for entry in entries:
        candidate = (backup_root / str(entry["path"])).resolve()
        if backup_root != candidate and backup_root not in candidate.parents:
            return BaselineCheck("manifest_hashes", False, "path escaped backup root")
        try:
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except OSError:
            mismatches += 1
            continue
        if digest != entry["sha256"]:
            mismatches += 1
    if mismatches:
        return BaselineCheck("manifest_hashes", False, f"mismatches: {mismatches}")
    return BaselineCheck("manifest_hashes", True, f"matched: {len(entries)}")


def _git_unchanged_check(root: Path) -> BaselineCheck:
    commands = (
        [
            "git",
            "-c",
            f"safe.directory={root.as_posix()}",
            "diff",
            "--quiet",
            "HEAD",
            "--",
            "backup",
        ],
        [
            "git",
            "-c",
            f"safe.directory={root.as_posix()}",
            "diff",
            "--cached",
            "--quiet",
            "HEAD",
            "--",
            "backup",
        ],
    )
    for argv in commands:
        result = run_process(argv, cwd=root, timeout=30)
        if result.returncode != 0:
            return BaselineCheck("backup_git_unchanged", False, f"git exit {result.returncode}")
    return BaselineCheck("backup_git_unchanged", True, "worktree and index unchanged")


def run_baseline(root: Path) -> tuple[BaselineCheck, ...]:
    resolved = root.resolve()
    entries, parse = _load_manifest(resolved)
    if not parse.ok:
        return (parse,)
    return (
        parse,
        _tracked_manifest_check(resolved, entries),
        _hash_check(resolved, entries),
        _git_unchanged_check(resolved),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checks = run_baseline(args.root)
    ok = all(check.ok for check in checks)
    if args.json:
        payload = {"ok": ok, "checks": [asdict(check) for check in checks]}
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for check in checks:
            print(f"{check.code}: {'PASS' if check.ok else 'FAIL'} - {check.message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
