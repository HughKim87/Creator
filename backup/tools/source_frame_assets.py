#!/usr/bin/env python3
"""Reuse or extract video frames keyed by immutable source time."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "asset_id",
    "source_id",
    "source_path",
    "source_size",
    "source_mtime_ns",
    "source_fps",
    "source_time_seconds",
    "source_end_seconds",
    "source_frame",
    "width",
    "kind",
    "precision",
    "candidate_ids",
    "bit_ids",
    "tags",
    "path",
    "sha256",
    "status",
    "notes",
]
SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
FORBIDDEN_OUTPUT_PARTS = {"temp", "tmp", "backup", "backups"}


def parse_time(value: str) -> float:
    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")
    parts = text.split(":")
    if len(parts) > 3:
        raise ValueError(f"invalid timestamp: {value}")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value}") from exc
    if any(number < 0 for number in numbers):
        raise ValueError(f"negative timestamp: {value}")
    if len(numbers) == 3:
        hours, minutes, seconds = numbers
    elif len(numbers) == 2:
        hours, minutes, seconds = 0.0, numbers[0], numbers[1]
    else:
        hours, minutes, seconds = 0.0, 0.0, numbers[0]
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"invalid timestamp component: {value}")
    return hours * 3600 + minutes * 60 + seconds


def sample_times(start: float, end: float, count: int) -> list[float]:
    if count < 1:
        raise ValueError("count must be at least 1")
    if end <= start:
        raise ValueError("end must be greater than start")
    if count == 1:
        return [round((start + end) / 2, 3)]
    step = (end - start) / (count - 1)
    return [round(start + index * step, 3) for index in range(count)]


def requested_times(args: argparse.Namespace) -> list[float]:
    points: list[float] = []
    if args.timestamps:
        points.extend(parse_time(item) for item in args.timestamps.split(",") if item.strip())
    if args.start is not None or args.end is not None:
        if args.start is None or args.end is None:
            raise ValueError("--start and --end must be used together")
        points.extend(sample_times(parse_time(args.start), parse_time(args.end), args.count))
    if not points:
        raise ValueError("provide --timestamps or --start/--end")
    return sorted({round(point, 3) for point in points})


def resolve_project_path(value: str, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the project: {path}") from exc
    if any(part.lower() in FORBIDDEN_OUTPUT_PARTS for part in relative.parts):
        raise ValueError(f"{label} cannot use a temporary or backup path: {relative}")
    return path


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def find_tool(name: str) -> str:
    exe = name + (".exe" if sys.platform == "win32" else "")
    bundled = ROOT / "tools" / "ffmpeg" / "bin" / exe
    if bundled.exists():
        return str(bundled)
    located = shutil.which(name)
    if located:
        return located
    raise RuntimeError(f"required tool not found: {name}")


def probe_source(source: Path) -> dict[str, float | int]:
    command = [
        find_tool("ffprobe"),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,r_frame_rate,width,height:format=duration",
        "-of",
        "json",
        str(source),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError("source has no video stream")
    stream = streams[0]
    rate_text = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1"
    fps = float(Fraction(rate_text))
    duration = float((payload.get("format") or {}).get("duration") or 0)
    if fps <= 0 or duration <= 0:
        raise RuntimeError("source FPS or duration is invalid")
    return {
        "fps": fps,
        "duration": duration,
        "width": int(stream.get("width") or 0),
        "height": int(stream.get("height") or 0),
    }


def load_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"unexpected manifest columns: {reader.fieldnames}")
        return list(reader)


def validate_source_identity(
    rows: list[dict[str, str]],
    *,
    source_id: str,
    source_size: int,
    source_mtime_ns: int,
) -> None:
    current = [row for row in rows if row.get("status") == "current"]
    fingerprint_ids = {
        row.get("source_id", "")
        for row in current
        if int(row.get("source_size") or -1) == source_size
        and int(row.get("source_mtime_ns") or -1) == source_mtime_ns
    }
    fingerprint_ids.discard("")
    if fingerprint_ids and fingerprint_ids != {source_id}:
        existing = ", ".join(sorted(fingerprint_ids))
        raise ValueError(
            f"source fingerprint is already registered as {existing}; reuse that source_id"
        )

    id_fingerprints = {
        (int(row.get("source_size") or -1), int(row.get("source_mtime_ns") or -1))
        for row in current
        if row.get("source_id") == source_id
    }
    if id_fingerprints and (source_size, source_mtime_ns) not in id_fingerprints:
        raise ValueError(
            f"source_id {source_id} belongs to a different source fingerprint; "
            "use a new ID or supersede the old source explicitly"
        )


def find_reusable(
    rows: list[dict[str, str]],
    *,
    source_id: str,
    source_size: int,
    source_mtime_ns: int,
    source_time: float,
    width: int,
) -> dict[str, str] | None:
    target_ms = round(source_time * 1000)
    matches = []
    for row in rows:
        if row.get("kind") != "source_frame" or row.get("status") != "current":
            continue
        if row.get("source_id") != source_id:
            continue
        if int(row.get("source_size") or -1) != source_size:
            continue
        if int(row.get("source_mtime_ns") or -1) != source_mtime_ns:
            continue
        if round(float(row.get("source_time_seconds") or -1) * 1000) != target_ms:
            continue
        if int(row.get("width") or 0) < width:
            continue
        asset_path = ROOT / row["path"]
        if asset_path.exists():
            matches.append(row)
    return min(matches, key=lambda row: int(row["width"])) if matches else None


def canonical_name(source_time: float, source_frame: int, width: int) -> str:
    milliseconds = round(source_time * 1000)
    return f"src_t{milliseconds:010d}_f{source_frame:09d}_w{width}.jpg"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_jpeg(path: Path) -> None:
    if not path.exists() or path.stat().st_size < 4:
        raise RuntimeError(f"frame output is missing or empty: {path}")
    data = path.read_bytes()
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise RuntimeError(f"frame output is not a complete JPEG: {path}")


def append_manifest(path: Path, records: list[dict[str, str]]) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    mode = "a" if exists else "x"
    with path.open(mode, encoding="utf-8-sig" if not exists else "utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, quoting=csv.QUOTE_ALL)
        if not exists:
            writer.writeheader()
        writer.writerows(records)
    if b"\x00" in path.read_bytes():
        raise RuntimeError(f"manifest contains a NUL byte: {path}")


def extract_frame(source: Path, output: Path, source_time: float, width: int) -> None:
    command = [
        find_tool("ffmpeg"),
        "-hide_banner",
        "-loglevel",
        "error",
        "-n",
        "-ss",
        f"{source_time:.3f}",
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-vf",
        f"scale={width}:-2",
        "-q:v",
        "3",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        if output.exists():
            output.unlink()
        raise RuntimeError(f"ffmpeg failed at {source_time:.3f}s: {result.stderr.strip()}")
    try:
        verify_jpeg(output)
    except Exception:
        if output.exists():
            output.unlink()
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Original video path inside the project")
    parser.add_argument("--source-id", required=True, help="Stable ASCII source identifier")
    parser.add_argument("--timestamps", help="Comma-separated absolute source timestamps")
    parser.add_argument("--start", help="Absolute source range start")
    parser.add_argument("--end", help="Absolute source range end")
    parser.add_argument("--count", type=int, default=12, help="Even samples for --start/--end")
    parser.add_argument("--width", type=int, default=1024, help="Requested frame width")
    parser.add_argument("--asset-root", required=True, help="Durable source asset directory")
    parser.add_argument("--manifest", required=True, help="Shared source asset CSV")
    return parser


def run(args: argparse.Namespace) -> dict[str, object]:
    if not SOURCE_ID_RE.fullmatch(args.source_id):
        raise ValueError("--source-id must contain only ASCII letters, numbers, underscore, or hyphen")
    if args.width < 64:
        raise ValueError("--width must be at least 64")

    source = resolve_project_path(args.source, "source")
    asset_root = resolve_project_path(args.asset_root, "asset root")
    manifest = resolve_project_path(args.manifest, "manifest")
    if not source.is_file():
        raise ValueError(f"source does not exist: {source}")
    if manifest.suffix.lower() != ".csv":
        raise ValueError("manifest must be a CSV file")

    points = requested_times(args)
    probe = probe_source(source)
    fps = float(probe["fps"])
    duration = float(probe["duration"])
    for point in points:
        if point < 0 or point >= duration:
            raise ValueError(f"source timestamp outside duration: {point:.3f}s >= {duration:.3f}s")

    stat = source.stat()
    rows = load_manifest(manifest)
    validate_source_identity(
        rows,
        source_id=args.source_id,
        source_size=stat.st_size,
        source_mtime_ns=stat.st_mtime_ns,
    )
    frames_dir = asset_root / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    created_records: list[dict[str, str]] = []
    result_frames: list[dict[str, object]] = []
    reused = 0
    created = 0

    for point in points:
        existing = find_reusable(
            rows + created_records,
            source_id=args.source_id,
            source_size=stat.st_size,
            source_mtime_ns=stat.st_mtime_ns,
            source_time=point,
            width=args.width,
        )
        if existing:
            reused += 1
            result_frames.append(
                {
                    "asset_id": existing["asset_id"],
                    "source_time_seconds": float(existing["source_time_seconds"]),
                    "source_frame": int(existing["source_frame"]),
                    "width": int(existing["width"]),
                    "path": existing["path"],
                    "reused": True,
                }
            )
            continue

        source_frame = round(point * fps)
        output = frames_dir / canonical_name(point, source_frame, args.width)
        asset_id = f"{args.source_id}_t{round(point * 1000):010d}_w{args.width}"
        output_existed = output.exists()
        if output_existed:
            verify_jpeg(output)
            reused += 1
        else:
            extract_frame(source, output, point, args.width)
            created += 1
        record = {
            "asset_id": asset_id,
            "source_id": args.source_id,
            "source_path": relative_path(source),
            "source_size": str(stat.st_size),
            "source_mtime_ns": str(stat.st_mtime_ns),
            "source_fps": f"{fps:.6f}",
            "source_time_seconds": f"{point:.3f}",
            "source_end_seconds": f"{point:.3f}",
            "source_frame": str(source_frame),
            "width": str(args.width),
            "kind": "source_frame",
            "precision": "exact_frame",
            "candidate_ids": "",
            "bit_ids": "",
            "tags": "",
            "path": relative_path(output),
            "sha256": sha256_file(output),
            "status": "current",
            "notes": "",
        }
        created_records.append(record)
        result_frames.append(
            {
                "asset_id": asset_id,
                "source_time_seconds": point,
                "source_frame": source_frame,
                "width": args.width,
                "path": record["path"],
                "reused": output_existed,
            }
        )

    append_manifest(manifest, created_records)
    return {
        "source_id": args.source_id,
        "requested": len(points),
        "reused": reused,
        "created": created,
        "registered": len(created_records),
        "manifest": relative_path(manifest),
        "frames": result_frames,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run(args)
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
