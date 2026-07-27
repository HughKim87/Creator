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
    {
        "information",
        "action",
        "reaction",
        "transition",
        "atmosphere",
        "speech",
        "event",
        "unclassified",
    }
)
SEMANTIC_STATUSES = frozenset({"pending", "passed", "failed"})
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CLIP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ISSUE_FIELDS = ("code", "message", "track", "clip_id", "index")


class TimelineValidationError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        issues: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.issues = issues or [
            {
                "code": code,
                "message": message,
                "track": None,
                "clip_id": None,
                "index": None,
            }
        ]


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class _Collector:
    def __init__(self) -> None:
        self.issues: list[dict[str, Any]] = []

    def add(
        self,
        code: str,
        message: str,
        *,
        track: str | None = None,
        clip_id: str | None = None,
        index: int | None = None,
    ) -> None:
        self.issues.append(
            {
                "code": code,
                "message": message,
                "track": track,
                "clip_id": clip_id,
                "index": index,
            }
        )

    def object(
        self,
        value: Any,
        fields: frozenset[str],
        name: str,
        **context: Any,
    ) -> Mapping[str, Any] | None:
        if not isinstance(value, Mapping):
            self.add(
                "invalid_fields",
                f"{name} must contain exactly: {sorted(fields)}",
                **context,
            )
            return None
        if set(value) != fields:
            self.add(
                "invalid_fields",
                f"{name} must contain exactly: {sorted(fields)}",
                **context,
            )
        return value

    def text(
        self,
        value: Any,
        name: str,
        *,
        maximum: int,
        allow_empty: bool = False,
        pattern: re.Pattern[str] | None = None,
        pattern_message: str | None = None,
        **context: Any,
    ) -> str | None:
        if not isinstance(value, str):
            self.add("invalid_fields", f"{name} must be a string", **context)
            return None
        rendered = value.strip()
        if not allow_empty and not rendered:
            self.add("invalid_fields", f"{name} must not be empty", **context)
            return None
        if len(rendered) > maximum:
            self.add(
                "invalid_fields",
                f"{name} must be at most {maximum} characters",
                **context,
            )
            return None
        if pattern is not None and not pattern.fullmatch(rendered):
            self.add(
                "invalid_fields",
                pattern_message or f"{name} has an invalid format",
                **context,
            )
            return None
        return rendered

    def integer(
        self,
        value: Any,
        name: str,
        *,
        minimum: int,
        **context: Any,
    ) -> int | None:
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            self.add(
                "invalid_fields",
                f"{name} must be an integer >= {minimum}",
                **context,
            )
            return None
        return value


def _value(mapping: Mapping[str, Any] | None, key: str) -> Any:
    if mapping is None or key not in mapping:
        return None
    return mapping[key]


def _source(
    value: Any,
    collector: _Collector,
) -> dict[str, Any | None]:
    source = collector.object(value, SOURCE_FIELDS, "source")
    frame_rate = collector.object(
        _value(source, "frame_rate"),
        frozenset({"numerator", "denominator"}),
        "source.frame_rate",
    )
    video = collector.object(
        _value(source, "video"),
        frozenset({"width", "height"}),
        "source.video",
    )
    audio = collector.object(
        _value(source, "audio"),
        frozenset({"sample_rate", "channels"}),
        "source.audio",
    )
    source_id = collector.text(
        _value(source, "id"),
        "source.id",
        maximum=80,
        pattern=SLUG_PATTERN,
        pattern_message="source.id must be a lowercase ASCII slug",
    )
    return {
        "id": source_id,
        "path": collector.text(_value(source, "path"), "source.path", maximum=1000),
        "total_frames": collector.integer(
            _value(source, "total_frames"),
            "source.total_frames",
            minimum=1,
        ),
        "frame_rate": {
            "numerator": collector.integer(
                _value(frame_rate, "numerator"),
                "source.frame_rate.numerator",
                minimum=1,
            ),
            "denominator": collector.integer(
                _value(frame_rate, "denominator"),
                "source.frame_rate.denominator",
                minimum=1,
            ),
        },
        "video": {
            "width": collector.integer(
                _value(video, "width"),
                "source.video.width",
                minimum=1,
            ),
            "height": collector.integer(
                _value(video, "height"),
                "source.video.height",
                minimum=1,
            ),
        },
        "audio": {
            "sample_rate": collector.integer(
                _value(audio, "sample_rate"),
                "source.audio.sample_rate",
                minimum=1,
            ),
            "channels": collector.integer(
                _value(audio, "channels"),
                "source.audio.channels",
                minimum=1,
            ),
        },
    }


def _semantic_gate(value: Any, collector: _Collector) -> dict[str, Any | None]:
    gate = collector.object(value, SEMANTIC_GATE_FIELDS, "semantic_gate")
    status = collector.text(
        _value(gate, "status"),
        "semantic_gate.status",
        maximum=20,
    )
    if status is not None and status not in SEMANTIC_STATUSES:
        collector.add(
            "invalid_fields",
            f"semantic_gate.status must be one of: {sorted(SEMANTIC_STATUSES)}",
        )
        status = None
    reviewed_by_value = _value(gate, "reviewed_by")
    reviewed_by = None
    if reviewed_by_value is not None:
        reviewed_by = collector.text(
            reviewed_by_value,
            "semantic_gate.reviewed_by",
            maximum=200,
        )
    if status == "passed" and reviewed_by is None:
        collector.add(
            "invalid_fields",
            "passed semantic_gate requires reviewed_by",
        )
    return {
        "status": status,
        "reviewed_by": reviewed_by,
        "notes": collector.text(
            _value(gate, "notes"),
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
    source_id: str | None,
    total_frames: int | None,
    collector: _Collector,
) -> dict[str, Any | None]:
    name = f"sequence.{expected_track}_clips[{index}]"
    context = {"track": expected_track, "index": index}
    clip = collector.object(value, CLIP_FIELDS, name, **context)
    raw_id = _value(clip, "id")
    clip_id = collector.text(
        raw_id,
        f"{name}.id",
        maximum=100,
        pattern=CLIP_ID_PATTERN,
        pattern_message=f"{name}.id has invalid characters",
        **context,
    )
    clip_context = {"track": expected_track, "clip_id": clip_id, "index": index}
    track = collector.text(
        _value(clip, "track"),
        f"{name}.track",
        maximum=10,
        **clip_context,
    )
    if track is not None and track != expected_track:
        collector.add(
            "invalid_fields",
            f"{name}.track must be {expected_track}",
            **clip_context,
        )
        track = None
    clip_source_id = collector.text(
        _value(clip, "source_id"),
        f"{name}.source_id",
        maximum=80,
        pattern=SLUG_PATTERN,
        pattern_message=f"{name}.source_id must be a lowercase ASCII slug",
        **clip_context,
    )
    if (
        clip_source_id is not None
        and source_id is not None
        and clip_source_id != source_id
    ):
        collector.add(
            "source_lineage",
            f"{name}.source_id must match source.id",
            **clip_context,
        )
    source_in = collector.integer(
        _value(clip, "source_in"),
        f"{name}.source_in",
        minimum=0,
        **clip_context,
    )
    source_out = collector.integer(
        _value(clip, "source_out"),
        f"{name}.source_out",
        minimum=1,
        **clip_context,
    )
    frames = collector.integer(
        _value(clip, "frames"),
        f"{name}.frames",
        minimum=1,
        **clip_context,
    )
    timeline_start = collector.integer(
        _value(clip, "timeline_start"),
        f"{name}.timeline_start",
        minimum=0,
        **clip_context,
    )
    timeline_end = collector.integer(
        _value(clip, "timeline_end"),
        f"{name}.timeline_end",
        minimum=1,
        **clip_context,
    )
    gap_before = collector.integer(
        _value(clip, "gap_before"),
        f"{name}.gap_before",
        minimum=0,
        **clip_context,
    )
    if (
        source_in is not None
        and source_out is not None
        and timeline_start is not None
        and timeline_end is not None
        and (source_in >= source_out or timeline_start >= timeline_end)
    ):
        collector.add(
            "invalid_frame_range",
            f"{name} must have increasing source and timeline ranges",
            **clip_context,
        )
    elif (
        source_in is not None
        and source_out is not None
        and frames is not None
        and timeline_start is not None
        and timeline_end is not None
        and (
            frames != source_out - source_in
            or frames != timeline_end - timeline_start
        )
    ):
        collector.add(
            "length_mismatch",
            f"{name} frame equations do not match",
            **clip_context,
        )
    if (
        source_out is not None
        and total_frames is not None
        and source_out > total_frames
    ):
        collector.add(
            "source_bounds",
            f"{name}.source_out exceeds source.total_frames",
            **clip_context,
        )
    source_order_exception = _value(clip, "source_order_exception")
    if not isinstance(source_order_exception, bool):
        collector.add(
            "invalid_fields",
            f"{name}.source_order_exception must be boolean",
            **clip_context,
        )
        source_order_exception = None
    edit_role = collector.text(
        _value(clip, "edit_role"),
        f"{name}.edit_role",
        maximum=20,
        **clip_context,
    )
    if edit_role is not None and edit_role not in EDIT_ROLES:
        collector.add(
            "invalid_fields",
            f"{name}.edit_role must be one of: {sorted(EDIT_ROLES)}",
            **clip_context,
        )
        edit_role = None
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
        "edit_reason": collector.text(
            _value(clip, "edit_reason"),
            f"{name}.edit_reason",
            maximum=500,
            **clip_context,
        ),
    }


def _continuity(
    clips: list[dict[str, Any | None]],
    track: str,
    collector: _Collector,
) -> None:
    previous_end: int | None = 0
    previous_source_out: int | None = None
    for index, clip in enumerate(clips):
        context = {"track": track, "clip_id": clip["id"], "index": index}
        gap_before = clip["gap_before"]
        if track == "video" and gap_before is not None and gap_before != 0:
            collector.add(
                "video_gap",
                f"video clip {clip['id']} must have gap_before=0",
                **context,
            )
        expected_start = None
        if previous_end is not None and gap_before is not None:
            expected_start = previous_end + (gap_before if track == "audio" else 0)
        if (
            expected_start is not None
            and clip["timeline_start"] is not None
            and clip["timeline_start"] != expected_start
        ):
            collector.add(
                f"{track}_continuity",
                f"{track} clip {clip['id']} must start at {expected_start}",
                **context,
            )
        if (
            previous_source_out is not None
            and clip["source_in"] is not None
            and clip["source_in"] < previous_source_out
            and clip["source_order_exception"] is False
        ):
            collector.add(
                "undeclared_source_order",
                f"{track} clip {clip['id']} reverses source order without an exception",
                **context,
            )
        previous_end = clip["timeline_end"]
        previous_source_out = clip["source_out"]


def validate_timeline(value: Mapping[str, Any]) -> dict[str, Any]:
    collector = _Collector()
    timeline = collector.object(value, TIMELINE_FIELDS, "timeline")
    version = _value(timeline, "timeline_version")
    if version != TIMELINE_VERSION:
        collector.add(
            "invalid_fields",
            f"timeline_version must be {TIMELINE_VERSION}",
        )
    source = _source(_value(timeline, "source"), collector)
    sequence_value = collector.object(
        _value(timeline, "sequence"),
        SEQUENCE_FIELDS,
        "sequence",
    )
    timeline_id = collector.text(
        _value(timeline, "timeline_id"),
        "timeline_id",
        maximum=80,
        pattern=SLUG_PATTERN,
        pattern_message="timeline_id must be a lowercase ASCII slug",
    )
    sequence_name = collector.text(
        _value(sequence_value, "name"),
        "sequence.name",
        maximum=200,
    )
    semantic_gate = _semantic_gate(_value(timeline, "semantic_gate"), collector)

    normalized_clips: dict[str, list[dict[str, Any | None]]] = {}
    seen_ids: set[str] = set()
    for track in ("video", "audio"):
        key = f"{track}_clips"
        raw_clips = _value(sequence_value, key)
        if not isinstance(raw_clips, list) or not raw_clips:
            collector.add(
                "invalid_fields",
                f"sequence.{key} must be a non-empty list",
                track=track,
            )
            normalized_clips[key] = []
            continue
        clips = [
            _clip(
                item,
                index=index,
                expected_track=track,
                source_id=source["id"],
                total_frames=source["total_frames"],
                collector=collector,
            )
            for index, item in enumerate(raw_clips)
        ]
        for index, clip in enumerate(clips):
            clip_id = clip["id"]
            if clip_id is not None and clip_id in seen_ids:
                collector.add(
                    "duplicate_clip_id",
                    f"duplicate clip id: {clip_id}",
                    track=track,
                    clip_id=clip_id,
                    index=index,
                )
            elif clip_id is not None:
                seen_ids.add(clip_id)
        _continuity(clips, track, collector)
        normalized_clips[key] = clips

    video_clips = normalized_clips["video_clips"]
    audio_clips = normalized_clips["audio_clips"]
    if video_clips and audio_clips:
        video_end = video_clips[-1]["timeline_end"]
        audio_end = audio_clips[-1]["timeline_end"]
        if (
            video_end is not None
            and audio_end is not None
            and video_end != audio_end
        ):
            collector.add(
                "av_total_mismatch",
                f"video total {video_end} != audio total {audio_end}",
            )

    if collector.issues:
        first = collector.issues[0]
        raise TimelineValidationError(
            first["code"],
            first["message"],
            issues=collector.issues,
        )
    return {
        "timeline_version": TIMELINE_VERSION,
        "timeline_id": timeline_id,
        "source": source,
        "sequence": {
            "name": sequence_name,
            "video_clips": video_clips,
            "audio_clips": audio_clips,
        },
        "semantic_gate": semantic_gate,
    }


def inspect_timeline(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        timeline = validate_timeline(value)
    except TimelineValidationError as exc:
        report: dict[str, Any] = {
            "ok": False,
            "errors": exc.issues,
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
