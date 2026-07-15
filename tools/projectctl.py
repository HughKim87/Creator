#!/usr/bin/env python3
"""Shared project session control for file-based AI agents."""
from __future__ import annotations

import argparse
import json
import locale
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable


SCHEMA_VERSION = 1
STATE_RELATIVE = Path("outputs/AGENT_CONTROL.json")
HANDOFF_RELATIVE = Path("outputs/SESSION_HANDOFF.md")
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
SOURCE_ID_RE = re.compile(r"source_id:\s*`?([A-Za-z0-9_.-]+)`?")


class ProjectCtlError(RuntimeError):
    """Raised when a control-state operation is unsafe or invalid."""


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_state() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "handoff_path": HANDOFF_RELATIVE.as_posix(),
        "active_task": None,
        "last_completed": None,
        "updated_at": None,
    }


def _validate_task(task: object, completed: bool = False) -> None:
    if task is None:
        return
    if not isinstance(task, dict):
        raise ProjectCtlError("task state must be an object or null")
    required = {"id", "title", "agent", "session", "started_at", "base_commit"}
    if completed:
        required |= {"finished_at", "summary", "verification"}
    missing = sorted(required - set(task))
    if missing:
        raise ProjectCtlError(f"task state is missing fields: {', '.join(missing)}")
    if not isinstance(task["id"], str) or not TASK_ID_RE.fullmatch(task["id"]):
        raise ProjectCtlError("task id must be an ASCII slug of at most 64 characters")
    for field in ("title", "agent", "started_at"):
        if not isinstance(task[field], str) or not task[field].strip():
            raise ProjectCtlError(f"task field '{field}' must be a non-empty string")
    if task["session"] is not None and not isinstance(task["session"], str):
        raise ProjectCtlError("task session must be a string or null")
    if task["base_commit"] is not None and not isinstance(task["base_commit"], str):
        raise ProjectCtlError("task base_commit must be a string or null")
    if completed:
        if not isinstance(task["finished_at"], str) or not task["finished_at"]:
            raise ProjectCtlError("completed task must have finished_at")
        if not isinstance(task["summary"], str):
            raise ProjectCtlError("completed task summary must be a string")
        verification = task["verification"]
        if not isinstance(verification, dict) or verification.get("ok") is not True:
            raise ProjectCtlError("completed task must have a successful verification receipt")


def validate_state(state: object) -> dict:
    if not isinstance(state, dict):
        raise ProjectCtlError("control state must be a JSON object")
    required = {"schema_version", "handoff_path", "active_task", "last_completed", "updated_at"}
    missing = sorted(required - set(state))
    if missing:
        raise ProjectCtlError(f"control state is missing fields: {', '.join(missing)}")
    if state["schema_version"] != SCHEMA_VERSION:
        raise ProjectCtlError(
            f"unsupported control-state version: {state['schema_version']} (expected {SCHEMA_VERSION})"
        )
    if state["handoff_path"] != HANDOFF_RELATIVE.as_posix():
        raise ProjectCtlError("handoff_path must point to outputs/SESSION_HANDOFF.md")
    if state["updated_at"] is not None and not isinstance(state["updated_at"], str):
        raise ProjectCtlError("updated_at must be a string or null")
    _validate_task(state["active_task"])
    _validate_task(state["last_completed"], completed=True)
    return state


def load_state(root: Path) -> tuple[dict, bool]:
    path = root / STATE_RELATIVE
    if not path.exists():
        return default_state(), False
    try:
        state = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectCtlError(f"cannot read {STATE_RELATIVE.as_posix()}: {exc}") from exc
    return validate_state(state), True


def write_state(root: Path, state: dict) -> None:
    validate_state(state)
    path = root / STATE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".agent-control-",
            suffix=".json",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _git(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    command = ["git", "-c", f"safe.directory={root.as_posix()}", *args]
    return subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def git_head(root: Path) -> str | None:
    try:
        result = _git(root, "rev-parse", "--short", "HEAD")
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def git_status_count(root: Path) -> tuple[bool | None, int | None]:
    try:
        result = _git(root, "status", "--short")
    except (OSError, subprocess.SubprocessError):
        return None, None
    if result.returncode != 0:
        return None, None
    count = len([line for line in result.stdout.splitlines() if line.strip()])
    return count > 0, count


def read_source_id(root: Path, handoff_path: str) -> str | None:
    path = root / handoff_path
    if not path.exists():
        return None
    try:
        match = SOURCE_ID_RE.search(path.read_text(encoding="utf-8-sig"))
    except OSError:
        return None
    return match.group(1) if match else None


def snapshot(root: Path) -> dict:
    state, state_exists = load_state(root)
    dirty, change_count = git_status_count(root)
    handoff_path = state["handoff_path"]
    return {
        "schema_version": SCHEMA_VERSION,
        "state_file": STATE_RELATIVE.as_posix(),
        "state_exists": state_exists,
        "active_task": state["active_task"],
        "last_completed": state["last_completed"],
        "handoff": {
            "path": handoff_path,
            "exists": (root / handoff_path).exists(),
            "source_id": read_source_id(root, handoff_path),
        },
        "git": {
            "head": git_head(root),
            "dirty": dirty,
            "change_count": change_count,
        },
    }


def render_context(data: dict) -> str:
    active = data["active_task"]
    completed = data["last_completed"]
    handoff = data["handoff"]
    git = data["git"]
    lines = [
        "PROJECT CONTROL CONTEXT",
        f"- control state: {'initialized' if data['state_exists'] else 'absent (read-only default)' }",
        f"- active task: {active['id'] + ' / ' + active['agent'] if active else 'none'}",
        f"- last completed: {completed['id'] if completed else 'none'}",
        f"- handoff: {handoff['path']} ({'present' if handoff['exists'] else 'missing'})",
        f"- source_id: {handoff['source_id'] or 'none'}",
        f"- git: head={git['head'] or 'unknown'}, dirty={git['dirty']}, entries={git['change_count']}",
        "- load next: SESSION_HANDOFF.md, then the routed output handoff",
    ]
    return "\n".join(lines)


def start_task(
    root: Path,
    task_id: str,
    title: str,
    agent: str,
    session: str | None = None,
) -> tuple[dict, bool]:
    if not TASK_ID_RE.fullmatch(task_id):
        raise ProjectCtlError("--task must be an ASCII slug of at most 64 characters")
    if not title.strip() or not agent.strip():
        raise ProjectCtlError("--title and --agent must not be empty")
    state, _ = load_state(root)
    active = state["active_task"]
    if active is not None:
        if active["id"] == task_id and active["agent"] == agent:
            return state, False
        raise ProjectCtlError(
            f"active task conflict: {active['id']} is already owned by {active['agent']}"
        )
    state["active_task"] = {
        "id": task_id,
        "title": title.strip(),
        "agent": agent.strip(),
        "session": session.strip() if session and session.strip() else None,
        "started_at": timestamp(),
        "base_commit": git_head(root),
    }
    state["updated_at"] = timestamp()
    write_state(root, state)
    return state, True


def _run_check(root: Path, name: str, command: list[str], timeout: int = 300) -> dict:
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        combined = "\n".join(
            part.strip()
            for part in (_decode_output(result.stdout), _decode_output(result.stderr))
            if part.strip()
        )
        detail = combined[-2000:] if combined else "no output"
        return {"name": name, "ok": result.returncode == 0, "returncode": result.returncode, "detail": detail}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"name": name, "ok": False, "returncode": None, "detail": str(exc)}


def _decode_output(data: bytes) -> str:
    encodings = ["utf-8", locale.getpreferredencoding(False), "cp949"]
    for encoding in dict.fromkeys(encodings):
        try:
            return data.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("utf-8", errors="backslashreplace")


def verify_project(root: Path) -> dict:
    git_prefix = ["git", "-c", f"safe.directory={root.as_posix()}"]
    checks = [
        _run_check(root, "doccheck", [sys.executable, str(root / "tools/doccheck/check_docs.py")]),
        _run_check(
            root,
            "workflow_gate",
            [sys.executable, str(root / "tools/workflow_gate.py"), "audit"],
        ),
        _run_check(
            root,
            "unit_tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        ),
        _run_check(root, "git_diff_check", [*git_prefix, "diff", "--check"]),
        _run_check(root, "git_cached_diff_check", [*git_prefix, "diff", "--cached", "--check"]),
    ]
    return {
        "ok": all(check["ok"] for check in checks),
        "checked_at": timestamp(),
        "checks": checks,
    }


def finish_task(
    root: Path,
    task_id: str,
    summary: str,
    verify: Callable[[Path], dict] = verify_project,
) -> tuple[dict | None, dict]:
    state, _ = load_state(root)
    active = state["active_task"]
    if active is None:
        raise ProjectCtlError("there is no active task to finish")
    if active["id"] != task_id:
        raise ProjectCtlError(f"active task is {active['id']}, not {task_id}")
    verification = verify(root)
    if verification.get("ok") is not True:
        return None, verification
    completed = dict(active)
    completed.update(
        {
            "finished_at": timestamp(),
            "summary": summary.strip(),
            "verification": {
                "ok": True,
                "checked_at": verification.get("checked_at"),
                "checks": [check.get("name") for check in verification.get("checks", [])],
            },
        }
    )
    state["active_task"] = None
    state["last_completed"] = completed
    state["updated_at"] = timestamp()
    write_state(root, state)
    return state, verification


def _print_json(value: object) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    encoding = sys.stdout.encoding or "utf-8"
    encoded = payload.encode(encoding, errors="backslashreplace")
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(encoded.decode(encoding))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Common session state and verification commands for all project agents."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help=argparse.SUPPRESS,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status", help="Show current control state without writing.")
    status.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    context = commands.add_parser("context", help="Show the compact cross-agent startup context.")
    context.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    start = commands.add_parser("start", help="Claim one active project task.")
    start.add_argument("--task", required=True, help="Stable ASCII task slug.")
    start.add_argument("--title", required=True, help="Short task title.")
    start.add_argument("--agent", required=True, help="Agent name, for example codex or claude.")
    start.add_argument("--session", help="Optional client session identifier.")

    commands.add_parser("verify", help="Run shared documentation, test, and diff checks.")

    finish = commands.add_parser("finish", help="Finish the active task only after verification passes.")
    finish.add_argument("--task", required=True, help="Active task slug.")
    finish.add_argument("--summary", default="", help="Short completion summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command in {"status", "context"}:
            data = snapshot(root)
            if args.json or args.command == "status":
                _print_json(data)
            else:
                print(render_context(data))
            return 0
        if args.command == "start":
            state, created = start_task(root, args.task, args.title, args.agent, args.session)
            _print_json({"ok": True, "started": created, "active_task": state["active_task"]})
            return 0
        if args.command == "verify":
            result = verify_project(root)
            _print_json(result)
            return 0 if result["ok"] else 1
        if args.command == "finish":
            state, verification = finish_task(root, args.task, args.summary)
            if state is None:
                _print_json({"ok": False, "reason": "verification_failed", "verification": verification})
                return 1
            _print_json({"ok": True, "finished": state["last_completed"], "verification": verification})
            return 0
    except ProjectCtlError as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
