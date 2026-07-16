#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic guardrail for agent tool calls (Claude Code hooks).

Modes:
  pretooluse  Read hook JSON from stdin. Exit 2 with a reason on stderr to
              block the tool call. Exit 0 to allow.
  stop        If tracked text files changed, run doccheck. Exit 2 with a
              summary to block stopping until docs pass. Exit 0 otherwise.

Policy source of truth is PROJECT_RULES.md (Hard Safety / File Rules).
This script enforces only the critical few, deterministically.
Fail-open by design: malformed input or missing dependencies allow the call.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# --- PreToolUse rules -------------------------------------------------------

MEDIA_EXT = r"(?:mp4|mkv|mov|avi|wav|mp3|srt)"

BASH_DENY = [
    (r"\bgit\s+commit\b[^&|;]*(--no-verify|\s-n\b)",
     "Bypassing pre-commit checks is prohibited. Commit without --no-verify."),
    (r"\bgit\s+config\b[^&|;]*hooksPath[^&|;]*(/dev/null|''|\"\")",
     "Disabling the hooks path is prohibited."),
    (r"\bgit\s+push\b", "git push is an external write. Ask the user first."),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard destroys work. Ask the user first."),
    (r"\bgit\s+clean\b[^&|;]*-\w*f", "git clean -f deletes untracked files. Ask the user first."),
    (r"\brm\s+(-\w*\s+)*-\w*r\w*f", "Recursive force delete is blocked. Ask the user first."),
    (r"(?i)\b(rm|del|erase|rmdir|rd|remove-item)\b[^&|;]*[\\/ \"']inputs[\\/]",
     "Deleting under inputs/ (original sources) is blocked."),
    (r"(?i)\b(rm|del|erase|remove-item)\b[^&|;]*\." + MEDIA_EXT + r"\b",
     "Deleting media/subtitle files is blocked. Originals must be preserved."),
    (r">\s*\"?[^&|;\"]*[\\/]inputs[\\/]",
     "Redirecting output into inputs/ (original sources) is blocked."),
    (r"(?i)(--out-dir|--output|\s-o)\s+[\"']?(?:[^&|;\"']*[\\/])?temp(?:[\\/]|[\"'\s]|$)",
     "Project temp output is prohibited. Use the durable stage output location."),
    (r"(?i)(--out-dir|--output|\s-o)\s+[\"']?[^&|;\"']*workspace[\\/]outputs(?:[\\/]|[\"'\s]|$)",
     "Duplicate workspace/outputs trees are prohibited. Use the project outputs/ directory."),
    (r"(?i)(--out-dir|--output|\s-o)\s+[\"']?(?:[^&|;\"']*[\\/])?runs(?:[\\/]|[\"'\s]|$)",
     "A separate runs/ tree is prohibited. Put input-derived files under outputs/."),
]

PATH_DENY = [
    (r"(?i)(^|[\\/])inputs[\\/]",
     "Writing under inputs/ (original sources) is blocked. Save outputs elsewhere."),
    (r"(?i)(^|[\\/])temp([\\/]|$)",
     "Writing under project temp/ is blocked. Use the durable stage output location."),
    (r"(?i)(^|[\\/])workspace[\\/]outputs([\\/]|$)",
     "Writing under workspace/outputs is blocked. Use the project outputs/ directory."),
    (r"(?i)(^|[\\/])runs([\\/]|$)",
     "Writing under runs/ is blocked. Put input-derived files under outputs/."),
    (r"(?i)(^|[\\/])backups?([\\/]|$)|\.bak(?:[_\.-]|$)",
     "Duplicate backup copies are prohibited. Use Git history and the approved original backup."),
    (r"(?i)(^|[\\/])\.env(\.|$|[\\/])", "Secrets files are off limits."),
    (r"(?i)id_rsa|(^|[\\/])\.ssh([\\/]|$)", "SSH key material is off limits."),
]


def deny(reason: str) -> None:
    sys.stderr.write("agent_guard: blocked. " + reason + "\n")
    sys.exit(2)


def check_pretooluse(payload: dict) -> None:
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if tool == "Bash":
        command = str(tool_input.get("command", ""))
        for pattern, reason in BASH_DENY:
            if re.search(pattern, command):
                deny(reason)
    elif tool in ("Write", "Edit", "NotebookEdit"):
        file_path = str(tool_input.get("file_path", ""))
        for pattern, reason in PATH_DENY:
            if re.search(pattern, file_path):
                deny(reason)
    sys.exit(0)


# --- Stop rule: docs must pass doccheck before finishing --------------------

def check_stop(payload: dict) -> None:
    if payload.get("stop_hook_active"):
        sys.exit(0)  # already continued once; avoid a blocking loop
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "-uall"], cwd=str(ROOT),
            capture_output=True, text=True, timeout=30,
        ).stdout
    except Exception:
        sys.exit(0)
    changed = [
        line for line in status.splitlines()
        if line[:2].strip() and line[3:].strip().lower().endswith((".md", ".py", ".bat"))
    ]
    if not changed:
        sys.exit(0)
    script = ROOT / "tools" / "doccheck" / "check_docs.py"
    if not script.exists():
        sys.exit(0)
    try:
        result = subprocess.run(
            [sys.executable, str(script)], cwd=str(ROOT),
            capture_output=True, text=True, timeout=120,
        )
    except Exception:
        sys.exit(0)
    if result.returncode != 0:
        tail = "\n".join((result.stdout or "").splitlines()[-15:])
        sys.stderr.write("agent_guard: doccheck failed after doc changes.\n" + tail + "\n")
        sys.exit(2)
    sys.exit(0)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "pretooluse"
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail-open on malformed input
    if not isinstance(payload, dict):
        sys.exit(0)
    if mode == "stop":
        check_stop(payload)
    else:
        check_pretooluse(payload)


if __name__ == "__main__":
    main()
