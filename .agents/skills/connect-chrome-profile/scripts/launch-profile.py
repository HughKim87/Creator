#!/usr/bin/env python3
"""Resolve and launch the installed official Chrome runtime for one profile.

Only plugin files are inspected. The profile Preferences path is passed as an
environment string to the official launcher and is never opened by this helper.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def resolve_launcher(cache_root: Path) -> Path:
    package = cache_root / "openai-bundled" / "chrome"
    candidates = []
    if package.is_dir():
        for version in package.iterdir():
            if not version.is_dir() or not re.fullmatch(r"\d+(?:\.\d+)+", version.name):
                continue
            script = version / "scripts" / "open-chrome-window.js"
            required = ("chromium-browser-diagnostics.mjs", "extension-ids.json")
            if script.is_file() and all((script.parent / name).is_file() for name in required):
                candidates.append((tuple(map(int, version.name.split("."))), script))
    if not candidates:
        raise FileNotFoundError("official Chrome launcher unavailable in installed runtime cache")
    return max(candidates, key=lambda item: item[0])[1]


def validate_profile(profile: str) -> str:
    if not profile.strip() or profile in {".", ".."} or re.search(r'[/\\:\x00-\x1f]', profile):
        raise ValueError("profile_directory must be a single non-empty directory identifier")
    return profile


def profile_environment(profile: str, user_data_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    # Override both names so an inherited profile selection cannot win.
    preferences = str(user_data_root / validate_profile(profile) / "Preferences")
    env["CODEX_CHROME_PREFERENCES_PATH"] = preferences
    env["CODEX_CHROMIUM_PREFERENCES_PATH"] = preferences
    return env


def inspect_plan(node: str, launcher: Path, profile: str, env: dict[str, str]) -> dict:
    result = subprocess.run(
        [node, str(launcher), "--dry-run", "--json"],
        env=env, capture_output=True, text=True, encoding="utf-8", timeout=15, check=True,
    )
    plan = json.loads(result.stdout)
    if plan.get("profileDirectory") != profile or plan.get("browserFamily") != "chrome":
        raise ValueError("official launcher did not select the requested Chrome profile")
    if plan.get("dryRun") is not True:
        raise ValueError("official launcher did not return a dry-run plan")
    return plan


def launch(node: str, launcher: Path, env: dict[str, str]) -> None:
    options = {
        "env": env, "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    else:
        options["start_new_session"] = True
    # No inherited output pipes: Chrome can outlive the command. Readiness is
    # proven by the control API's launch delta, not this process returning.
    subprocess.Popen([node, str(launcher), "--json"], **options)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-directory", required=True)
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--user-data-root", type=Path)
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    try:
        profile = validate_profile(args.profile_directory)
        codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        cache_root = args.cache_root or codex_root / "plugins" / "cache"
        launcher = resolve_launcher(cache_root)
        node = shutil.which("node")
        if not node:
            raise FileNotFoundError("Node executable unavailable for official Chrome launcher")
        if args.user_data_root:
            user_data = args.user_data_root
        elif sys.platform == "win32":
            user_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Google" / "Chrome" / "User Data"
        elif sys.platform == "darwin":
            user_data = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
        else:
            user_data = Path.home() / ".config" / "google-chrome"
        env = profile_environment(profile, user_data)
        inspect_plan(node, launcher, profile, env)
        if args.launch:
            launch(node, launcher, env)
        print(json.dumps({
            "status": "launch_requested" if args.launch else "ready",
            "profileDirectory": profile,
            "runtime_version": launcher.parent.parent.name,
            "launcher": str(launcher),
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        # Error text from a launcher can contain paths or unrelated environment
        # information. Return the error category, not raw profile data.
        print(json.dumps({"status": "unavailable", "reason": "official_profile_launcher_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
