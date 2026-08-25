#!/usr/bin/env python3
"""Plan or apply a safe archive that leaves only user-facing upload files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any


SCHEMA_VERSIONS = {
    "youtube-manual-upload-v1",
    "youtube-manual-upload-v2",
    "youtube-manual-upload-v3",
}


def _load_package(package_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read package: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("package root must be an object")
    if value.get("schema_version") not in SCHEMA_VERSIONS:
        raise ValueError(
            f"schema_version must be one of {sorted(SCHEMA_VERSIONS)}"
        )
    return value


def _find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (
            (candidate / "PROJECT_RULES.md").is_file()
            and (candidate / "extension").is_dir()
        ):
            return candidate.resolve()
    raise ValueError("cannot locate project root from package path")


def _resolve(
    base: Path,
    root: Path,
    value: Any,
    field: str,
    *,
    require_file: bool = False,
    require_dir: bool = False,
) -> Path:
    if isinstance(value, Path):
        value = str(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field} escapes the allowed root") from exc
    if require_file and (
        not candidate.is_file() or candidate.stat().st_size == 0
    ):
        raise ValueError(f"{field} not found or empty: {candidate}")
    if require_dir and not candidate.is_dir():
        raise ValueError(f"{field} directory not found: {candidate}")
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _plain_names(value: Any, field: str) -> set[str]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{field} must contain exactly 4 filenames")
    names: set[str] = set()
    for index, item in enumerate(value):
        if (
            not isinstance(item, str)
            or not item.strip()
            or Path(item).name != item
        ):
            raise ValueError(f"{field}[{index}] must be a plain filename")
        names.add(item)
    if len(names) != 4:
        raise ValueError(f"{field} must contain 4 unique filenames")
    return names


def build_plan(package: Path, guide: Path | None = None) -> dict[str, Any]:
    package_path = package.resolve()
    if not package_path.is_file():
        raise ValueError(f"package not found: {package_path}")
    base = package_path.parent
    project_root = _find_project_root(base)
    data = _load_package(package_path)
    schema = data["schema_version"]
    artifacts = data.get("artifacts")
    preparation = data.get("preparation")
    if not isinstance(artifacts, dict):
        raise ValueError("artifacts must be an object")
    if not isinstance(preparation, dict):
        raise ValueError("preparation must be an object")

    if schema == "youtube-manual-upload-v3":
        if preparation.get("status") != "ready":
            raise ValueError("preparation.status must be ready")
        if preparation.get("youtube_actions") != "manual_by_user":
            raise ValueError(
                "preparation.youtube_actions must be manual_by_user"
            )

    if schema in {
        "youtube-manual-upload-v2",
        "youtube-manual-upload-v3",
    }:
        output_dir = _resolve(
            base,
            project_root,
            preparation.get("output_dir"),
            "preparation.output_dir",
            require_dir=True,
        )
        archive_dir = _resolve(
            base,
            project_root,
            preparation.get("archive_dir"),
            "preparation.archive_dir",
        )
        final_names = _plain_names(
            preparation.get("final_output_files"),
            "preparation.final_output_files",
        )
        guide_path = _resolve(
            base,
            project_root,
            guide if guide is not None else preparation.get("guide"),
            "preparation.guide",
            require_file=True,
        )
        for key in ("video", "thumbnail", "captions"):
            path = _resolve(
                base,
                project_root,
                artifacts.get(key),
                f"artifacts.{key}",
                require_file=True,
            )
            if path.parent != output_dir or path.name not in final_names:
                raise ValueError(
                    f"artifacts.{key} is outside the final output contract"
                )
        if schema == "youtube-manual-upload-v3":
            title_package = _resolve(
                base,
                project_root,
                artifacts.get("title_thumbnail_package"),
                "artifacts.title_thumbnail_package",
                require_file=True,
            )
            declared_hashes = data.get("artifact_hashes")
            if not isinstance(declared_hashes, dict):
                raise ValueError("artifact_hashes must be an object")
            resolved_for_hash = {
                key: _resolve(
                    base,
                    project_root,
                    artifacts.get(key),
                    f"artifacts.{key}",
                    require_file=True,
                )
                for key in ("video", "thumbnail", "captions")
            }
            resolved_for_hash["title_thumbnail_package"] = title_package
            for key, path in resolved_for_hash.items():
                declared = declared_hashes.get(key)
                if (
                    not isinstance(declared, str)
                    or len(declared) != 64
                    or declared.lower() != _sha256(path)
                ):
                    raise ValueError(f"artifact hash differs: {key}")
        if guide_path.parent != output_dir or guide_path.name not in final_names:
            raise ValueError("guide is outside the final output contract")
    else:
        output_dir = base
        archive_dir = (
            project_root
            / "extension"
            / "work"
            / output_dir.name
            / "archive"
        ).resolve()
        final_names = set()
        for key in ("video", "thumbnail", "captions"):
            path = _resolve(
                base,
                base,
                artifacts.get(key),
                f"artifacts.{key}",
                require_file=True,
            )
            final_names.add(path.name)
        guide_path = (
            guide.resolve()
            if guide
            else package_path.with_name("YOUTUBE-MANUAL-UPLOAD.md")
        )
        if (
            not guide_path.is_file()
            or guide_path.parent.resolve() != output_dir
        ):
            raise ValueError(f"guide not found in output directory: {guide_path}")
        final_names.add(guide_path.name)

    try:
        archive_dir.relative_to(output_dir)
    except ValueError:
        pass
    else:
        raise ValueError("archive directory must be outside output directory")

    unexpected_directories = sorted(
        str(path.resolve())
        for path in output_dir.iterdir()
        if path.is_dir() or path.is_symlink()
    )
    archive_items: list[dict[str, str]] = []
    for path in sorted(output_dir.iterdir()):
        if not path.is_file() or path.is_symlink() or path.name in final_names:
            continue
        destination = (archive_dir / path.name).resolve()
        if destination.exists():
            raise ValueError(f"archive destination already exists: {destination}")
        archive_items.append(
            {
                "source": str(path.resolve()),
                "destination": str(destination),
                "sha256": _sha256(path),
            }
        )

    present_names = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    missing_final = sorted(final_names - present_names)
    if missing_final:
        raise ValueError(f"missing final output files: {missing_final}")

    return {
        "status": "ready",
        "schema_version": schema,
        "output_dir": str(output_dir),
        "archive_dir": str(archive_dir),
        "keep": sorted(str(output_dir / name) for name in final_names),
        "archive": archive_items,
        "unexpected_directories": unexpected_directories,
        "external_actions": "none",
    }


def apply_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if plan["unexpected_directories"]:
        raise ValueError(
            "refusing to finalize while unexpected directories or symlinks exist"
        )
    output_dir = Path(plan["output_dir"]).resolve()
    archive_dir = Path(plan["archive_dir"]).resolve()
    archive_dir.mkdir(parents=True, exist_ok=True)
    moved: list[dict[str, str]] = []
    for item in plan["archive"]:
        source = Path(item["source"]).resolve()
        destination = Path(item["destination"]).resolve()
        if (
            source.parent != output_dir
            or not source.is_file()
            or source.is_symlink()
        ):
            raise ValueError(f"refusing unsafe archive source: {source}")
        if destination.parent != archive_dir or destination.exists():
            raise ValueError(f"refusing unsafe archive destination: {destination}")
        shutil.move(str(source), str(destination))
        moved.append(item)
    result = dict(plan)
    result["moved"] = moved
    result["external_actions"] = "local_file_archive"
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--guide", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="move planned non-final files to the separate archive directory",
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
                {
                    "status": "invalid",
                    "errors": [str(exc)],
                    "external_actions": "none",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
