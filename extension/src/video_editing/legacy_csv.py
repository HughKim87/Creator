from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .model import TimelineValidationError, validate_timeline


LEGACY_CSV_COLUMNS = (
    "idx",
    "track",
    "name",
    "src_in",
    "src_out",
    "frames",
    "tl_start",
    "tl_end",
    "gap_before",
)
INTEGER_COLUMNS = (
    "idx",
    "src_in",
    "src_out",
    "frames",
    "tl_start",
    "tl_end",
    "gap_before",
)
SEMANTIC_REVIEW_REASON = "Legacy CSV import requires explicit semantic review."


class LegacyCsvError(ValueError):
    def __init__(self, message: str, issues: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.issues = issues


def _issue(
    code: str,
    message: str,
    *,
    track: str | None = None,
    clip_id: str | None = None,
    index: int | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "track": track,
        "clip_id": clip_id,
        "index": index,
    }


def _read_rows(
    path: Path | str,
    *,
    expected_track: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    csv_path = Path(path)
    try:
        raw = csv_path.read_bytes().decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        return [], [
            _issue(
                "csv_encoding",
                f"{expected_track} CSV must be strict UTF-8",
                track=expected_track,
            )
        ]
    except OSError:
        return [], [
            _issue(
                "csv_read",
                f"cannot read {expected_track} CSV: {csv_path}",
                track=expected_track,
            )
        ]

    reader = csv.reader(io.StringIO(raw, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return [], [
            _issue(
                "csv_columns",
                f"{expected_track} CSV is empty",
                track=expected_track,
            )
        ]
    if tuple(header) != LEGACY_CSV_COLUMNS:
        return [], [
            _issue(
                "csv_columns",
                f"{expected_track} CSV columns must be exactly: "
                f"{list(LEGACY_CSV_COLUMNS)}",
                track=expected_track,
            )
        ]

    rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    seen_indices: set[int] = set()
    for row_offset, cells in enumerate(reader):
        row_number = row_offset + 2
        if len(cells) != len(LEGACY_CSV_COLUMNS):
            issues.append(
                _issue(
                    "csv_row_fields",
                    f"{expected_track} CSV row {row_number} must contain "
                    f"{len(LEGACY_CSV_COLUMNS)} fields",
                    track=expected_track,
                    index=row_offset,
                )
            )
            continue
        raw_row = dict(zip(LEGACY_CSV_COLUMNS, cells, strict=True))
        clip_id = raw_row["name"].strip() or None
        context = {
            "track": expected_track,
            "clip_id": clip_id,
            "index": row_offset,
        }
        converted: dict[str, int] = {}
        for column in INTEGER_COLUMNS:
            raw_value = raw_row[column].strip()
            minimum = 1 if column in {"idx", "src_out", "frames", "tl_end"} else 0
            try:
                parsed = int(raw_value)
            except ValueError:
                parsed = minimum - 1
            if str(parsed) != raw_value or parsed < minimum:
                issues.append(
                    _issue(
                        "csv_integer",
                        f"{expected_track} CSV row {row_number} column {column} "
                        f"must be an integer >= {minimum}",
                        **context,
                    )
                )
            else:
                converted[column] = parsed
        if "idx" in converted:
            if converted["idx"] in seen_indices:
                issues.append(
                    _issue(
                        "duplicate_csv_index",
                        f"duplicate {expected_track} CSV idx: {converted['idx']}",
                        **context,
                    )
                )
            else:
                seen_indices.add(converted["idx"])
        if raw_row["track"].strip() != expected_track:
            issues.append(
                _issue(
                    "csv_track",
                    f"{expected_track} CSV row {row_number} track must be "
                    f"{expected_track}",
                    **context,
                )
            )
        if clip_id is None:
            issues.append(
                _issue(
                    "csv_name",
                    f"{expected_track} CSV row {row_number} name must not be empty",
                    **context,
                )
            )
        if (
            len(converted) == len(INTEGER_COLUMNS)
            and raw_row["track"].strip() == expected_track
            and clip_id is not None
        ):
            rows.append(
                {
                    "idx": converted["idx"],
                    "track": expected_track,
                    "name": clip_id,
                    "source_in": converted["src_in"],
                    "source_out": converted["src_out"],
                    "frames": converted["frames"],
                    "timeline_start": converted["tl_start"],
                    "timeline_end": converted["tl_end"],
                    "gap_before": converted["gap_before"],
                }
            )
    if not rows and not issues:
        issues.append(
            _issue(
                "csv_rows",
                f"{expected_track} CSV must contain at least one data row",
                track=expected_track,
            )
        )
    return rows, issues


def import_legacy_csv(
    video_csv: Path | str,
    audio_csv: Path | str,
    *,
    timeline_id: str,
    sequence_name: str,
    source_id: str,
    source_path: str,
    source_total_frames: int,
    frame_rate_numerator: int,
    frame_rate_denominator: int,
    width: int,
    height: int,
    sample_rate: int,
    channels: int,
    source_order_exceptions: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    video_rows, video_issues = _read_rows(video_csv, expected_track="video")
    audio_rows, audio_issues = _read_rows(audio_csv, expected_track="audio")
    issues = video_issues + audio_issues
    known_ids = {row["name"] for row in video_rows + audio_rows}
    unknown_exceptions = sorted(source_order_exceptions - known_ids)
    if unknown_exceptions:
        issues.append(
            _issue(
                "unknown_source_order_exception",
                f"unknown source order exception clip ids: {unknown_exceptions}",
            )
        )
    if issues:
        raise LegacyCsvError(issues[0]["message"], issues)

    def clips(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "id": row["name"],
                "track": row["track"],
                "source_id": source_id,
                "source_in": row["source_in"],
                "source_out": row["source_out"],
                "frames": row["frames"],
                "timeline_start": row["timeline_start"],
                "timeline_end": row["timeline_end"],
                "gap_before": row["gap_before"],
                "source_order_exception": row["name"] in source_order_exceptions,
                "edit_role": "unclassified",
                "edit_reason": SEMANTIC_REVIEW_REASON,
            }
            for row in rows
        ]

    timeline = {
        "timeline_version": 1,
        "timeline_id": timeline_id,
        "source": {
            "id": source_id,
            "path": source_path,
            "total_frames": source_total_frames,
            "frame_rate": {
                "numerator": frame_rate_numerator,
                "denominator": frame_rate_denominator,
            },
            "video": {"width": width, "height": height},
            "audio": {"sample_rate": sample_rate, "channels": channels},
        },
        "sequence": {
            "name": sequence_name,
            "video_clips": clips(video_rows),
            "audio_clips": clips(audio_rows),
        },
        "semantic_gate": {
            "status": "pending",
            "reviewed_by": None,
            "notes": SEMANTIC_REVIEW_REASON,
        },
    }
    try:
        return validate_timeline(timeline)
    except TimelineValidationError as exc:
        raise LegacyCsvError(exc.issues[0]["message"], exc.issues) from exc


def _render_timeline(timeline: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            timeline,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def write_legacy_timeline(
    video_csv: Path | str,
    audio_csv: Path | str,
    output_path: Path | str,
    **metadata: Any,
) -> dict[str, Any]:
    target = Path(output_path)
    if not target.parent.is_dir():
        issue = _issue(
            "output_directory",
            f"output directory does not exist: {target.parent}",
        )
        raise LegacyCsvError(issue["message"], [issue])
    if target.exists():
        issue = _issue("output_exists", f"output already exists: {target}")
        raise LegacyCsvError(issue["message"], [issue])
    timeline = import_legacy_csv(video_csv, audio_csv, **metadata)
    rendered = _render_timeline(timeline)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            issue = _issue("output_exists", f"output already exists: {target}")
            raise LegacyCsvError(issue["message"], [issue]) from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "output": str(target),
        "bytes": len(rendered),
        "sha256": hashlib.sha256(rendered).hexdigest(),
        "timeline_id": timeline["timeline_id"],
        "semantic_gate": timeline["semantic_gate"]["status"],
    }
