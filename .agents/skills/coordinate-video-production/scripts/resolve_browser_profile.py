#!/usr/bin/env python3
"""Resolve a new job's browser settings from explicit input or local defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


class ResolutionError(ValueError):
    pass


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_workflow_defaults(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResolutionError(
            f"{config_path} is not valid JSON: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise ResolutionError(f"{config_path} must contain a JSON object")
    if payload.get("schema_version") != "video-workflow-defaults-v1":
        raise ResolutionError(
            f"{config_path} schema_version must be video-workflow-defaults-v1"
        )
    return payload


def require_browser(browser: Any, source: str) -> dict[str, str]:
    if not isinstance(browser, dict):
        raise ResolutionError(f"{source} browser settings must be an object")
    profile_directory = browser.get("profile_directory")
    required_origin = browser.get("required_origin")
    if not nonempty(profile_directory):
        raise ResolutionError(f"{source} profile_directory must be non-empty")
    if not nonempty(required_origin):
        raise ResolutionError(f"{source} required_origin must be non-empty")
    profile_label = browser.get("profile_label")
    if not nonempty(profile_label):
        profile_label = profile_directory
    return {
        "surface": "chrome",
        "profile_label": profile_label,
        "profile_directory": profile_directory,
        "required_origin": required_origin,
        "connection_scope": "browser_runtime",
        "status": "needs_connection",
        "verification_method": "",
        "last_verified_at": "",
    }


def resolve_browser_profile(
    defaults: dict[str, Any],
    *,
    profile_directory: str | None = None,
    profile_label: str | None = None,
    profile_alias: str | None = None,
    required_origin: str | None = None,
) -> dict[str, Any]:
    if nonempty(profile_directory) and nonempty(profile_alias):
        raise ResolutionError(
            "provide profile_directory or profile_alias, not both"
        )

    default_browser = defaults.get("browser", {})
    if not isinstance(default_browser, dict):
        raise ResolutionError("runtime_defaults browser settings must be an object")

    if nonempty(profile_directory):
        browser = {
            **default_browser,
            "profile_directory": profile_directory.strip(),
            "profile_label": (
                profile_label.strip()
                if nonempty(profile_label)
                else profile_directory.strip()
            ),
        }
        source = "explicit_profile_directory"
    elif nonempty(profile_alias):
        aliases = defaults.get("profile_aliases")
        alias_value = (
            aliases.get(profile_alias.strip())
            if isinstance(aliases, dict)
            else None
        )
        if not isinstance(alias_value, dict):
            raise ResolutionError(
                f"unknown profile alias: {profile_alias.strip()}"
            )
        browser = {**default_browser, **alias_value}
        source = "explicit_profile_alias"
    else:
        browser = dict(default_browser)
        source = "runtime_default"

    if nonempty(required_origin):
        browser["required_origin"] = required_origin.strip()
    missing = [key for key in ("profile_directory", "required_origin") if not nonempty(browser.get(key))]
    if missing:
        return {"status": "needs_input", "source": source, "missing_fields": missing}
    browser = require_browser(browser, source)

    return {
        "status": "resolved",
        "source": source,
        "browser": browser,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("extension/.runtime/video-workflow-defaults.json"),
    )
    parser.add_argument("--profile-directory")
    parser.add_argument("--profile-label")
    parser.add_argument("--profile-alias")
    parser.add_argument("--required-origin")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        defaults = load_workflow_defaults(args.config)
        result = resolve_browser_profile(
            defaults,
            profile_directory=args.profile_directory,
            profile_label=args.profile_label,
            profile_alias=args.profile_alias,
            required_origin=args.required_origin,
        )
    except (OSError, ResolutionError) as exc:
        print(
            json.dumps(
                {"status": "invalid", "error": str(exc)},
                ensure_ascii=False,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "resolved" else 2


if __name__ == "__main__":
    sys.exit(main())
