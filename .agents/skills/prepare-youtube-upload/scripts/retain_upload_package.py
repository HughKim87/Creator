#!/usr/bin/env python3
"""Plan or apply a safe cleanup that retains a complete YouTube upload package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ARTIFACT_KEYS = ("video", "thumbnail", "captions", "title_thumbnail_package")


def _resolve_inside(base: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    candidate = (base / value).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"{field} escapes the package directory") from exc
    if not candidate.is_file() or candidate.stat().st_size == 0:
        raise ValueError(f"{field} not found or empty: {candidate}")
    return candidate


def _load_package(package_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read package: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("package root must be an object")
    if value.get("schema_version") != "youtube-manual-upload-v1":
        raise ValueError("schema_version must be youtube-manual-upload-v1")
    return value


def build_plan(package: Path, guide: Path | None = None) -> dict[str, Any]:
    package_path = package.resolve()
    if not package_path.is_file():
        raise ValueError(f"package not found: {package_path}")
    base = package_path.parent
    data = _load_package(package_path)
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("artifacts must be an object")
    keep: set[Path] = {package_path}
    for key in ARTIFACT_KEYS:
        keep.add(_resolve_inside(base, artifacts.get(key), f"artifacts.{key}"))

    preparation = data.get("preparation")
    if not isinstance(preparation, dict):
        raise ValueError("preparation must be an object")
    keep_files = preparation.get("keep_files", [])
    if not isinstance(keep_files, list):
        raise ValueError("preparation.keep_files must be a list")
    for index, value in enumerate(keep_files):
        keep.add(_resolve_inside(base, value, f"preparation.keep_files[{index}]"))

    guide_path = (guide or package_path.with_name("YOUTUBE-MANUAL-UPLOAD.md")).resolve()
    try:
        guide_path.relative_to(base)
    except ValueError as exc:
        raise ValueError("guide escapes the package directory") from exc
    if guide_path.is_file():
        keep.add(guide_path)

    deletable = sorted(
        path.resolve()
        for path in base.iterdir()
        if path.is_file() and not path.is_symlink() and path.resolve() not in keep
    )
    return {
        "status": "ready",
        "target": str(base),
        "keep": sorted(str(path) for path in keep),
        "delete": [str(path) for path in deletable],
        "external_actions": "none",
    }


def apply_plan(plan: dict[str, Any]) -> dict[str, Any]:
    deleted = []
    for raw_path in plan["delete"]:
        path = Path(raw_path).resolve()
        target = Path(plan["target"]).resolve()
        if path.parent != target or not path.is_file() or path.is_symlink():
            raise ValueError(f"refusing unsafe cleanup target: {path}")
        path.unlink()
        deleted.append(str(path))
    plan = dict(plan)
    plan["deleted"] = deleted
    plan["external_actions"] = "local_file_cleanup"
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--guide", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete only the files in the generated cleanup plan",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = build_plan(args.package, args.guide)
        if args.apply:
            plan = apply_plan(plan)
        else:
            plan["mode"] = "dry_run"
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "invalid", "errors": [str(exc)], "external_actions": "none"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
