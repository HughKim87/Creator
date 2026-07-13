#!/usr/bin/env python3
"""Register existing source-timeline assets in the shared manifest."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

try:
    from source_frame_assets import (
        SOURCE_ID_RE,
        append_manifest,
        load_manifest,
        probe_source,
        relative_path,
        resolve_project_path,
        sha256_file,
        validate_source_identity,
    )
except ModuleNotFoundError:
    from tools.source_frame_assets import (
        SOURCE_ID_RE,
        append_manifest,
        load_manifest,
        probe_source,
        relative_path,
        resolve_project_path,
        sha256_file,
        validate_source_identity,
    )


CATALOG_FIELDS = [
    "asset_id",
    "source_id",
    "source_path",
    "source_time_seconds",
    "source_end_seconds",
    "width",
    "kind",
    "precision",
    "candidate_ids",
    "bit_ids",
    "tags",
    "path",
    "status",
    "notes",
]


def hash_asset(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise ValueError(f"asset directory is empty: {path}")
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(item).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_catalog(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CATALOG_FIELDS:
            raise ValueError(f"unexpected catalog columns: {reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise ValueError("catalog is empty")
    return rows


def register(catalog: Path, manifest: Path) -> dict[str, object]:
    catalog_rows = read_catalog(catalog)
    manifest_rows = load_manifest(manifest)
    known_ids = {row["asset_id"] for row in manifest_rows}
    known_paths = {row["path"] for row in manifest_rows}
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    source_cache: dict[Path, tuple[dict[str, float | int], object]] = {}
    records: list[dict[str, str]] = []

    for row in catalog_rows:
        asset_id = row["asset_id"].strip()
        source_id = row["source_id"].strip()
        if not asset_id:
            raise ValueError("catalog row has an empty asset_id")
        if not SOURCE_ID_RE.fullmatch(source_id):
            raise ValueError(f"invalid source_id for {asset_id}: {source_id}")
        if asset_id in known_ids or asset_id in seen_ids:
            raise ValueError(f"duplicate asset_id: {asset_id}")

        source = resolve_project_path(row["source_path"], "source")
        asset = resolve_project_path(row["path"], "asset")
        if not source.is_file():
            raise ValueError(f"source does not exist: {source}")
        if not asset.exists():
            raise ValueError(f"asset does not exist: {asset}")
        asset_path = relative_path(asset)
        if asset_path in known_paths or asset_path in seen_paths:
            raise ValueError(f"duplicate asset path: {asset_path}")

        if source not in source_cache:
            source_cache[source] = (probe_source(source), source.stat())
        probe, stat = source_cache[source]
        fps = float(probe["fps"])
        duration = float(probe["duration"])
        validate_source_identity(
            manifest_rows + records,
            source_id=source_id,
            source_size=stat.st_size,
            source_mtime_ns=stat.st_mtime_ns,
        )
        start = float(row["source_time_seconds"])
        end = float(row["source_end_seconds"] or start)
        if start < 0 or end < start or end > duration + 0.001:
            raise ValueError(f"invalid source range for {asset_id}: {start}..{end}")

        precision = row["precision"].strip()
        source_frame = str(round(start * fps)) if precision == "exact_frame" else ""
        record = {
            "asset_id": asset_id,
            "source_id": source_id,
            "source_path": relative_path(source),
            "source_size": str(stat.st_size),
            "source_mtime_ns": str(stat.st_mtime_ns),
            "source_fps": f"{fps:.6f}",
            "source_time_seconds": f"{start:.3f}",
            "source_end_seconds": f"{end:.3f}",
            "source_frame": source_frame,
            "width": row["width"].strip(),
            "kind": row["kind"].strip(),
            "precision": precision,
            "candidate_ids": row["candidate_ids"].strip(),
            "bit_ids": row["bit_ids"].strip(),
            "tags": row["tags"].strip(),
            "path": asset_path,
            "sha256": hash_asset(asset),
            "status": row["status"].strip() or "current",
            "notes": row["notes"].strip(),
        }
        records.append(record)
        seen_ids.add(asset_id)
        seen_paths.add(asset_path)

    append_manifest(manifest, records)
    return {
        "catalog": relative_path(catalog),
        "manifest": relative_path(manifest),
        "registered": len(records),
        "sources": len(source_cache),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, help="Existing-asset catalog CSV")
    parser.add_argument("--manifest", required=True, help="Shared source asset CSV")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        catalog = resolve_project_path(args.catalog, "catalog")
        manifest = resolve_project_path(args.manifest, "manifest")
        if not catalog.is_file():
            raise ValueError(f"catalog does not exist: {catalog}")
        if manifest.suffix.lower() != ".csv":
            raise ValueError("manifest must be a CSV file")
        print(json.dumps(register(catalog, manifest), ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
