#!/usr/bin/env python3
"""Session preflight: validate required files, scan roots, Python, Git, and
projectctl context. Cross-platform replacement for project_preflight.ps1."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "PROJECT_BOOTSTRAP.md",
    "docs/INDEX.md",
    "PROJECT_RULES.md",
    "docs/WORKFLOW_CONTRACT.json",
    "tools/projectctl.bat",
    "tools/run_python.bat",
    "tools/git_project.bat",
]
CANDIDATE_SCAN_ROOTS = [
    "docs",
    "inputs",
    "outputs",
    "planning_research",
    "skills",
    "tests",
    "tools",
]


def run_capture(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )
    return proc.returncode, proc.stdout.strip()


def git_root() -> str:
    if os.name == "nt":
        code, out = run_capture(
            ["cmd.exe", "/d", "/s", "/c", "call tools\\git_project.bat rev-parse --show-toplevel"]
        )
        if code == 0:
            return out
    code, out = run_capture(["git", "rev-parse", "--show-toplevel"])
    if code != 0:
        raise RuntimeError("Git root resolution failed.")
    return out


def control_context() -> list[str]:
    code, out = run_capture(
        [sys.executable, str(ROOT / "tools" / "projectctl.py"), "context"]
    )
    if code != 0:
        raise RuntimeError("projectctl context failed.")
    return out.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    args = parser.parse_args()

    missing_required = [f for f in REQUIRED_FILES if not (ROOT / f).exists()]
    scan_roots = [d for d in CANDIDATE_SCAN_ROOTS if (ROOT / d).exists()]
    skipped_scan_roots = [d for d in CANDIDATE_SCAN_ROOTS if not (ROOT / d).exists()]

    result = {
        "ok": not missing_required,
        "root": str(ROOT),
        "missing_required": missing_required,
        "scan_roots": scan_roots,
        "skipped_scan_roots": skipped_scan_roots,
        "python_executable": Path(sys.executable).as_posix(),
        "git_root": git_root(),
        "control_context": control_context(),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PROJECT PREFLIGHT")
        print(f"- ok: {result['ok']}")
        print(f"- root: {result['root']}")
        print(f"- scan roots: {', '.join(result['scan_roots'])}")
        print(f"- skipped scan roots: {', '.join(result['skipped_scan_roots'])}")
        print(f"- python: {result['python_executable']}")
        print(f"- git root: {result['git_root']}")
        if missing_required:
            print(f"- missing required: {', '.join(missing_required)}")
        for line in result["control_context"]:
            print(line)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
