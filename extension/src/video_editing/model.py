from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


TIMELINE_VERSION = 1
TIMELINE_FIELDS = frozenset(
    {"timeline_version", "timeline_id", "source", "sequence", "semantic_gate"}
)
SOURCE_FIELDS = frozenset({"id", "path", "total_frames", "frame_rate", "video", "audio"})
SEQUENCE_FIELDS = frozenset({"name", "video_clips", "audio_clips"})
SEMANTIC_GATE_FIELDS = frozenset({"status", "reviewed_by", "notes"})
CLIP_FIELDS = frozenset(
    {
        "id",
        "track",
        "source_id",
        "source_in",
        "source_out",
        "frames",
        "timeline_start",
        "timeline_end",
        "gap_before",
        "source_order_exception",
        "edit_role",
        "edit_reason",
    }
)
EDIT_ROLES = frozenset(
    {"information", "action", "reaction", "transition", "atmosphere", "speech", "event"}
)
SEMANTIC_STATUSES = frozenset({"pending", "passed", "failed"})
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CLIP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class TimelineValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _object(value: Any, fields: frozenset[str], name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise TimelineValidationError(
            "invalid_fields",
            f"{name} must contain exactly: {sorted(fields)}",
        )
    return value


def _text(value: Any, name: str, *, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TimelineValidationError("invalid_fields", f"{name} must be a string")
    rendered = value.strip()
    if not allow_empty and not rendered:
        raise TimelineValidationError("invalid_fields", f"{name} must not be empty")
    if len(rendered) > maximum:
        raise TimelineValidationError(
            "invalid_fields",
            f"{name} must be at most {maximum} characters",
        )
    return rendered


def _integer(value: Any, name: str, *, minimum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise TimelineValidationError(
            "invalid_fields",
            f"{name} must be an integer >= {minimum}",
        )
    return value


def _slug(value: Any, name: str) -> str:
    rendered = _text(value, name, maximum=80)
    if not SLUG_PATTERN.fullmatch(rendered):
        raise TimelineValidationError(
            "invalid_fields",
            f"{name} must be a lowercase ASCII slug",
        )
    return rendered


def _source(value: Any) -> dict[str, Any]:
    source = _object(value, SOURCE_FIELDS, "source")
    frame_rate = _object(
        source["frame_rate"],
        frozenset({"numerator", "denominator"}),
        "source.frame_rate",
    )
    video = _object(source["video"], frozenset({"width", "height"}), "source.video")
    audio = _object(
        source["audio"],
        frozenset({"sample_rate", "channels"}),
        "source.audio",
    )
    return {
        "id": _slug(source["id"], "source.id"),
        "path": _text(source["path"], "source.path", maximum=1000),
        "total_frames": _integer(source["total_frames"], "source.total_frames", minimum=1),
        "frame_rate": {
            "numerator": _integer(
                frame_rate["numerator"],
                "source.frame_rate.numerator",
                minimum=1,
            ),
            "denominator": _integer(
                frame_rate["denominator"],
                "source.frame_rate.denominator",
                minimum=1,
            ),
        },
        "video": {
            "width": _integer(video["width"], "source.video.width", minimum=1),
            "height": _integer(video["height"], "source.video.height", minimum=1),
        },
        "audio": {
            "sample_rate": _integer(
                audio["sample_rate"],
                "source.audio.sample_rate",
                minimum=1,
            ),
            "channels": _integer(
                audio["channels"],
                "source.audio.channels",
                minimum=1,
            ),
        },
    }


def _semantic_gate(value: Any) -> dict[str, Any]:
    gate = _object(value, SEMANTIC_GATE_FIELDS, "semantic_gate")
    status = _text(gate["status"], "semantic_gate.status", maximum=20)
    if status not in SEMANTIC_STATUSES:
        raise TimelineValidationError(
            "invalid_fields",
            f"semantic_gate.status must be one of: {sorted(SEMANTIC_STATUSES)}",
        )
    reviewed_by = gate["reviewed_by"]
    if reviewed_by is not None:
        reviewed_by = _text(reviewed_by, "semantic_gate.reviewed_by", maximum=200)
    if status == "passed" and reviewed_by is None:
        raise TimelineValidationError(
            "invalid_fields",
            "passed semantic_gate requires reviewed_by",
        )
    return {
        "status": status,
        "reviewed_by": reviewed_by,
        "notes": _text(
            gate["notes"],
            "semantic_gate.notes",
            maximum=500,
            allow_empty=True,
        ),
    }


def _clip(
    value: Any,
    *,
    index: int,
    expected_track: str,
    source_id: str,
    total_frames: int,
) -> dict[str, Any]:
    name = f"sequence.{expected_track}_clips[{index}]"
    clip = _object(value, CLIP_FIELDS, name)
    clip_id = _text(clip["id"], f"{name}.id", maximum=100)
    if not CLIP_ID_PATTERN.fullmatch(clip_id):
        raise TimelineValidationError(
            "invalid_fields",
            f"{name}.id has invalid characters",
        )
    track = _text(clip["track"], f"{name}.track", maximum=10)
    if track != expected_track:
        raise TimelineValidationError(
            "invalid_fields",
            f"{name}.track must be {expected_track}",
        )
    clip_source_id = _slug(clip["source_id"], f"{name}.source_id")
    if clip_source_id != source_id:
        raise TimelineValidationError(
            "source_lineage",
            f"{name}.source_id must match source.id",
        )
    source_in = _integer(clip["source_in"], f"{name}.source_in", minimum=0)
    source_out = _integer(clip["source_out"], f"{name}.source_out", minimum=1)
    frames = _integer(clip["frames"], f"{name}.frames", minimum=1)
    timeline_start = _integer(
        clip["timeline_start"],
        f"{name}.timeline_start",
        minimum=0,
    )
    timeline_end = _integer(
        clip["timeline_end"],
        f"{name}.timeline_end",
        minimum=1,
    )
    gap_before = _integer(clip["gap_before"], f"{name}.gap_before", minimum=0)
    if source_in >= source_out or timeline_start >= timeline_end:
        raise TimelineValidationError(
            "invalid_frame_range",
            f"{name} must have increasing source and timeline ranges",
        )
    if frames != source_out - source_in or frames != timeline_end - timeline_start:
        raise TimelineValidationError(
            "length_mismatch",
            f"{name} frame equations do not match",
        )
    if source_out > total_frames:
        raise TimelineValidationError(
            "source_bounds",
            f"{name}.source_out exceeds source.total_frames",
        )
    source_order_exception = clip["source_order_exception"]
    if not isinstance(source_order_exception, bool):
        raise TimelineValidationError(
            "invalid_fields",
            f"{name}.source_order_exception must be boolean",
        )
    edit_role = _text(clip["edit_role"], f"{name}.edit_role", maximum=20)
    if edit_role not in EDIT_ROLES:
        raise TimelineValidationError(
            "invalid_fields",
            f"{name}.edit_role must be one of: {sorted(EDIT_ROLES)}",
        )
    return {
        "id": clip_id,
        "track": track,
        "source_id": clip_source_id,
        "source_in": source_in,
        "source_out": source_out,
        "frames": frames,
        "timeline_start": timeline_start,
        "timeline_end": timeline_end,
        "gap_before": gap_before,
        "source_order_exception": source_order_exception,
        "edit_role": edit_role,
        "edit_reason": _text(clip["edit_reason"], f"{name}.edit_reason", maximum=500),
    }


def _continuity(clips: list[dict[str, Any]], track: str) -> None:
    previous_end = 0
    previous_source_out: int | None = None
    for index, clip in enumerate(clips):
        if track == "video" and clip["gap_before"] != 0:
            raise TimelineValidationError(
                "video_gap",
                f"video clip {clip['id']} must have gap_before=0",
            )
        expected_start = previous_end + (clip["gap_before"] if track == "audio" else 0)
        if clip["timeline_start"] != expected_start:
            raise TimelineValidationError(
                f"{track}_continuity",
                f"{track} clip {clip['id']} must start at {expected_start}",
            )
        if (
            previous_source_out is not None
            and clip["source_in"] < previous_source_out
            and not clip["source_order_exception"]
        ):
            raise TimelineValidationError(
                "undeclared_source_order",
                f"{track} clip {clip['id']} reverses source order without an exception",
            )
        previous_end = clip["timeline_end"]
        previous_source_out = clip["source_out"]


def validate_timeline(value: Mapping[str, Any]) -> dict[str, Any]:
    timeline = _object(value, TIMELINE_FIELDS, "timeline")
    if timeline["timeline_version"] != TIMELINE_VERSION:
        raise TimelineValidationError(
            "invalid_fields",
            f"timeline_version must be {TIMELINE_VERSION}",
        )
    source = _source(timeline["source"])
    sequence_value = _object(timeline["sequence"], SEQUENCE_FIELDS, "sequence")
    normalized: dict[str, Any] = {
        "timeline_version": TIMELINE_VERSION,
        "timeline_id": _slug(timeline["timeline_id"], "timeline_id"),
        "source": source,
        "sequence": {
            "name": _text(sequence_value["name"], "sequence.name", maximum=200),
            "video_clips": [],
            "audio_clips": [],
        },
        "semantic_gate": _semantic_gate(timeline["semantic_gate"]),
    }
    seen_ids: set[str] = set()
    for track in ("video", "audio"):
        key = f"{track}_clips"
        raw_clips = sequence_value[key]
        if not isinstance(raw_clips, list) or not raw_clips:
            raise TimelineValidationError(
                "invalid_fields",
                f"sequence.{key} must be a non-empty list",
            )
        clips = [
            _clip(
                item,
                index=index,
                expected_track=track,
                source_id=source["id"],
                total_frames=source["total_frames"],
            )
            for index, item in enumerate(raw_clips)
        ]
        for clip in clips:
            if clip["id"] in seen_ids:
                raise TimelineValidationError(
                    "duplicate_clip_id",
                    f"duplicate clip id: {clip['id']}",
                )
            seen_ids.add(clip["id"])
        _continuity(clips, track)
        normalized["sequence"][key] = clips
    video_end = normalized["sequence"]["video_clips"][-1]["timeline_end"]
    audio_end = normalized["sequence"]["audio_clips"][-1]["timeline_end"]
    if video_end != audio_end:
        raise TimelineValidationError(
            "av_total_mismatch",
            f"video total {video_end} != audio total {audio_end}",
        )
    return normalized


def inspect_timeline(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        timeline = validate_timeline(value)
    except TimelineValidationError as exc:
        report: dict[str, Any] = {
            "ok": False,
            "errors": [{"code": exc.code, "message": str(exc)}],
        }
    else:
        report = {
            "ok": True,
            "timeline_id": timeline["timeline_id"],
            "source_id": timeline["source"]["id"],
            "video_clips": len(timeline["sequence"]["video_clips"]),
            "audio_clips": len(timeline["sequence"]["audio_clips"]),
            "total_frames": timeline["sequence"]["video_clips"][-1]["timeline_end"],
            "audio_gap_frames": sum(
                clip["gap_before"] for clip in timeline["sequence"]["audio_clips"]
            ),
            "checks": [
                "clip_identity",
                "frame_ranges",
                "length_equations",
                "video_continuity",
                "audio_continuity",
                "av_total",
                "source_bounds",
                "source_order",
                "source_lineage",
            ],
        }
    report["fingerprint"] = "sha256:" + hashlib.sha256(
        _canonical(report).encode("utf-8")
    ).hexdigest()
    return report
