from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .model import TimelineValidationError, validate_timeline


TIMELINE_V2_VERSION = 2
TIMELINE_V2_FIELDS = frozenset(
    {
        "timeline_version",
        "timeline_id",
        "workflow_profile",
        "source_manifest",
        "sequence",
        "editorial_evidence",
        "revision",
        "approval",
        "validation",
        "delivery",
    }
)
SOURCE_MANIFEST_FIELDS = frozenset(
    {
        "id",
        "path",
        "total_frames",
        "frame_rate",
        "video",
        "audio",
        "content_sha256",
        "byte_size",
    }
)
EDITORIAL_EVIDENCE_FIELDS = frozenset(
    {"time_references", "events", "microbeats", "feedback"}
)
TIME_REFERENCE_FIELDS = frozenset(
    {
        "id",
        "raw",
        "coordinate_system",
        "unit",
        "start_frame",
        "end_frame",
        "scope",
        "confirmed_by",
        "correction_evidence",
    }
)
EVENT_FIELDS = frozenset(
    {
        "id",
        "role",
        "video_clip_ids",
        "audio_clip_ids",
        "source_in",
        "source_out",
        "depends_on",
        "timeline_order",
        "continuity_reason",
    }
)
MICROBEAT_FIELDS = frozenset(
    {
        "id",
        "event_id",
        "decision",
        "media_scope",
        "purpose",
        "video_clip_ids",
        "audio_clip_ids",
        "source_in",
        "source_out",
        "boundary_review",
    }
)
FEEDBACK_FIELDS = frozenset(
    {"baseline_payload_fingerprint", "positive_locks", "defects", "untouched"}
)
PRESERVATION_FIELDS = frozenset(
    {"id", "scope", "clip_ids", "evidence", "preserved"}
)
DEFECT_FIELDS = frozenset(
    {"id", "scope", "clip_ids", "status", "evidence", "approved_by"}
)
REVISION_FIELDS = frozenset(
    {"status", "supersedes", "checked_at", "state_owner_id"}
)
APPROVAL_FIELDS = frozenset({"calibration", "decisions"})
CALIBRATION_FIELDS = frozenset(
    {
        "required",
        "status",
        "artifact_id",
        "approved_payload_fingerprint",
        "approved_by",
        "approval_evidence",
        "checked_at",
    }
)
DECISION_FIELDS = frozenset(
    {
        "id",
        "artifact_id",
        "approved_scope",
        "source_manifest_hash",
        "decision",
        "invalidated_by",
        "approved_by",
        "checked_at",
        "reviewed_editorial_fingerprint",
    }
)
VALIDATION_FIELDS = frozenset(
    {"reviewed_editorial_fingerprint", "reviewer", "passes", "semantic_status"}
)
VALIDATION_PASS_NAMES = ("causal_space", "tempo_repetition", "av_boundary")
VALIDATION_PASS_FIELDS = frozenset(
    {"status", "method", "reviewer", "checked_at", "evidence"}
)
DELIVERY_FIELDS = frozenset(
    {"artifact_id", "output_path", "profile", "overwrite"}
)

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RFC3339_PATTERN = re.compile(
    r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?"
    r"(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)
CLIP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TIME_POINT_PATTERNS = {
    "frames": re.compile(r"^\d+$"),
    "seconds": re.compile(r"^\d+(?:\.\d+)?$"),
    "timecode": re.compile(
        r"^(?:\d{2}:[0-5]\d:[0-5]\d(?:\.\d+)?|\d{2}:[0-5]\d:[0-5]\d:\d{2})$"
    ),
}
WORKFLOW_PROFILES = frozenset(
    {"new_full_edit", "calibration", "approved_delta", "format_regeneration"}
)
MAX_REFERENCE_PAYLOADS = 64
REVISION_STATUSES = frozenset(
    {"working_candidate", "current", "approved", "use_prohibited", "historical"}
)
WHOLE_REVISION_SCOPE = "entire_revision"
EVENT_ROLES = frozenset(
    {
        "setup",
        "cause",
        "discovery",
        "action",
        "attempt",
        "reaction",
        "escape",
        "result",
        "transition",
        "state_change",
        "atmosphere",
    }
)
ROLES_REQUIRING_CAUSE = frozenset(
    {"action", "attempt", "reaction", "escape", "result", "transition", "state_change"}
)
CAUSAL_ROLES = frozenset(
    {"setup", "cause", "discovery", "action", "attempt", "reaction", "escape", "result", "state_change"}
)
PAYLOAD_FINGERPRINT_FIELDS = (
    "timeline_version",
    "timeline_id",
    "workflow_profile",
    "source_manifest",
    "sequence",
    "editorial_evidence",
    "revision",
)
EDITORIAL_FINGERPRINT_FIELDS = (
    "timeline_version",
    "source_manifest",
    "sequence",
    "editorial_evidence",
)
EVENT_VIDEO_ROLE_COMPATIBILITY = {
    "setup": frozenset({"information", "speech", "event", "atmosphere"}),
    "cause": frozenset({"information", "speech", "action", "event", "atmosphere"}),
    "discovery": frozenset({"information", "speech", "action", "reaction", "event", "atmosphere"}),
    "action": frozenset({"information", "speech", "action", "event"}),
    "attempt": frozenset({"information", "speech", "action", "event"}),
    "reaction": frozenset({"information", "speech", "reaction", "action", "event"}),
    "escape": frozenset({"speech", "reaction", "action", "event"}),
    "result": frozenset({"information", "speech", "reaction", "event"}),
    "state_change": frozenset({"information", "speech", "reaction", "transition", "event"}),
    "transition": frozenset({"information", "speech", "transition", "action", "atmosphere"}),
    "atmosphere": frozenset({"information", "atmosphere"}),
}


class TimelineV2Error(ValueError):
    def __init__(self, issues: list[dict[str, str]]) -> None:
        self.issues = issues
        self.code = issues[0]["code"] if issues else "invalid_timeline_v2"
        super().__init__(issues[0]["message"] if issues else "invalid timeline v2")


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_fingerprint(value: Mapping[str, Any]) -> str:
    payload = {key: deepcopy(value.get(key)) for key in PAYLOAD_FINGERPRINT_FIELDS}
    return "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest()


def task_payload_fingerprint(value: Mapping[str, Any]) -> str:
    payload = {
        "payload_fingerprint": payload_fingerprint(value),
        "approval": deepcopy(value.get("approval")),
        "validation": deepcopy(value.get("validation")),
    }
    return "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest()


def editorial_fingerprint(value: Mapping[str, Any]) -> str:
    payload = {key: deepcopy(value.get(key)) for key in EDITORIAL_FINGERPRINT_FIELDS}
    evidence = payload.get("editorial_evidence")
    if isinstance(evidence, dict):
        feedback = evidence.get("feedback")
        if isinstance(feedback, dict):
            feedback["baseline_payload_fingerprint"] = None
    return "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest()


def delivery_fingerprint(value: Mapping[str, Any]) -> str:
    payload = {
        "task_payload_fingerprint": task_payload_fingerprint(value),
        "delivery": deepcopy(value.get("delivery")),
    }
    return "sha256:" + hashlib.sha256(_canonical(payload)).hexdigest()


def _latest_active_whole_revision_approval_time(
    value: Mapping[str, Any],
) -> datetime | None:
    approval = value.get("approval")
    decisions = approval.get("decisions") if isinstance(approval, Mapping) else None
    if not isinstance(decisions, list):
        return None
    timeline_id = value.get("timeline_id")
    source = value.get("source_manifest")
    if not isinstance(source, Mapping):
        return None
    source_hash = source_manifest_fingerprint(source)
    editorial_hash = editorial_fingerprint(value)
    candidates: list[tuple[datetime, str, tuple[Any, ...], str, str]] = []
    for decision in decisions:
        if (
            not isinstance(decision, Mapping)
            or decision.get("artifact_id") != timeline_id
            or decision.get("source_manifest_hash") != source_hash
            or decision.get("reviewed_editorial_fingerprint") != editorial_hash
            or not isinstance(decision.get("checked_at"), str)
        ):
            continue
        try:
            checked_at = datetime.fromisoformat(
                decision["checked_at"].replace("Z", "+00:00")
            )
        except ValueError:
            continue
        if checked_at.tzinfo is None or checked_at.utcoffset() is None:
            continue
        invalidated = decision.get("invalidated_by")
        candidates.append(
            (
                checked_at,
                str(decision.get("decision")),
                tuple(invalidated) if isinstance(invalidated, list) else (),
                str(decision.get("approved_by")),
                str(decision.get("approved_scope")),
            )
        )
    if not candidates:
        return None
    latest_time = max(candidate[0] for candidate in candidates)
    latest_states = {
        candidate[1:] for candidate in candidates if candidate[0] == latest_time
    }
    if latest_states != {
        ("approved", (), "user", WHOLE_REVISION_SCOPE)
    }:
        return None
    return latest_time


def source_manifest_fingerprint(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _parse_timestamp(
    value: Any,
    collector: "_Collector",
    path: str,
    *,
    nullable: bool = False,
) -> datetime | None:
    rendered = collector.text(value, path, nullable=nullable)
    if rendered is None:
        return None
    if RFC3339_PATTERN.fullmatch(rendered) is None:
        collector.add(
            "invalid_timestamp",
            "timestamp must use RFC 3339 date-time syntax with an explicit timezone",
            path,
        )
        return None
    try:
        parsed = datetime.fromisoformat(rendered.replace("Z", "+00:00"))
    except ValueError:
        collector.add(
            "invalid_timestamp",
            "timestamp must be RFC 3339 with an explicit timezone",
            path,
        )
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        collector.add(
            "invalid_timestamp",
            "timestamp must include an explicit timezone",
            path,
        )
        return None
    return parsed


def _round_frames(seconds: Decimal, numerator: int, denominator: int) -> int:
    frames = seconds * Decimal(numerator) / Decimal(denominator)
    return int(frames.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _parse_time_point(
    raw: str,
    unit: str,
    frame_rate: Mapping[str, Any],
) -> int:
    pattern = TIME_POINT_PATTERNS[unit]
    if pattern.fullmatch(raw) is None:
        raise ValueError("raw time does not match its declared unit")
    numerator = frame_rate.get("numerator")
    denominator = frame_rate.get("denominator")
    if (
        not isinstance(numerator, int)
        or isinstance(numerator, bool)
        or numerator <= 0
        or not isinstance(denominator, int)
        or isinstance(denominator, bool)
        or denominator <= 0
    ):
        raise ValueError("frame rate is not valid")
    if unit == "frames":
        return int(raw)
    if unit == "seconds":
        try:
            return _round_frames(Decimal(raw), numerator, denominator)
        except InvalidOperation as exc:
            raise ValueError("seconds value is not numeric") from exc
    if "." in raw:
        hours_text, minutes_text, seconds_text = raw.split(":", 2)
        seconds = (
            Decimal(int(hours_text) * 3600 + int(minutes_text) * 60)
            + Decimal(seconds_text)
        )
        return _round_frames(seconds, numerator, denominator)
    hours_text, minutes_text, seconds_text, frames_text = raw.split(":")
    if numerator % denominator != 0:
        raise ValueError(
            "fractional frame rates require seconds or frames; colon timecode is ambiguous"
        )
    frame = int(frames_text)
    nominal_timebase = max(1, round(numerator / denominator))
    if frame >= nominal_timebase:
        raise ValueError(
            f"timecode frame field must be below nominal timebase {nominal_timebase}"
        )
    whole_seconds = (
        int(hours_text) * 3600 + int(minutes_text) * 60 + int(seconds_text)
    )
    return _round_frames(Decimal(whole_seconds), numerator, denominator) + frame


def _parse_time_range(
    raw: str,
    unit: str,
    frame_rate: Mapping[str, Any],
) -> tuple[int, int]:
    points = raw.split("..")
    if len(points) not in {1, 2} or any(not point for point in points):
        raise ValueError("range time must use START..END")
    start = _parse_time_point(points[0], unit, frame_rate)
    end = start if len(points) == 1 else _parse_time_point(points[1], unit, frame_rate)
    if len(points) == 1 and start != end:
        raise ValueError("point time must normalize to one frame")
    return start, end


def _intervals_are_contiguous(intervals: list[tuple[int, int]]) -> bool:
    if not intervals:
        return False
    ordered = sorted(intervals)
    current_end = ordered[0][1]
    for start, end in ordered[1:]:
        if start > current_end:
            return False
        current_end = max(current_end, end)
    return True


def _clip_signature(clip: Mapping[str, Any]) -> bytes:
    return _canonical(
        {
            key: clip.get(key)
            for key in (
                "track",
                "source_id",
                "source_in",
                "source_out",
                "frames",
                "gap_before",
                "source_order_exception",
                "edit_role",
                "edit_reason",
            )
        }
    )


def _clip_evidence_signature(value: Mapping[str, Any], clip_id: str) -> bytes:
    evidence = value.get("editorial_evidence")
    if not isinstance(evidence, Mapping):
        return _canonical({})
    events = [
        item
        for item in evidence.get("events", [])
        if isinstance(item, Mapping)
        and clip_id
        in list(item.get("video_clip_ids", [])) + list(item.get("audio_clip_ids", []))
    ]
    microbeats = [
        item
        for item in evidence.get("microbeats", [])
        if isinstance(item, Mapping)
        and clip_id
        in list(item.get("video_clip_ids", [])) + list(item.get("audio_clip_ids", []))
    ]
    return _canonical({"events": events, "microbeats": microbeats})


def _latest_review_time(value: Mapping[str, Any]) -> datetime | None:
    validation = value.get("validation")
    if not isinstance(validation, Mapping):
        return None
    passes = validation.get("passes")
    if not isinstance(passes, Mapping):
        return None
    parsed: list[datetime] = []
    for record in passes.values():
        if not isinstance(record, Mapping) or not isinstance(record.get("checked_at"), str):
            continue
        try:
            item = datetime.fromisoformat(record["checked_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if item.tzinfo is not None and item.utcoffset() is not None:
            parsed.append(item)
    return max(parsed, default=None)


class _Collector:
    def __init__(self) -> None:
        self.issues: list[dict[str, str]] = []

    def add(self, code: str, message: str, path: str) -> None:
        self.issues.append({"code": code, "message": message, "path": path})

    def object(self, value: Any, fields: frozenset[str], path: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            self.add("invalid_v2_fields", f"{path} must be an object", path)
            return {}
        if set(value) != fields:
            self.add(
                "invalid_v2_fields",
                f"{path} must contain exactly: {sorted(fields)}",
                path,
            )
        return value

    def items(self, value: Any, path: str, *, nonempty: bool = False) -> list[Any]:
        if not isinstance(value, list) or (nonempty and not value):
            qualifier = "a non-empty list" if nonempty else "a list"
            self.add("invalid_v2_fields", f"{path} must be {qualifier}", path)
            return []
        return value

    def text(
        self,
        value: Any,
        path: str,
        *,
        nullable: bool = False,
        pattern: re.Pattern[str] | None = None,
    ) -> str | None:
        if value is None and nullable:
            return None
        if not isinstance(value, str) or not value.strip():
            self.add("invalid_v2_fields", f"{path} must be a non-empty string", path)
            return None
        rendered = value.strip()
        if pattern is not None and pattern.fullmatch(rendered) is None:
            self.add("invalid_v2_fields", f"{path} has an invalid format", path)
            return None
        return rendered

    def integer(self, value: Any, path: str, minimum: int = 0) -> int | None:
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            self.add(
                "invalid_v2_fields",
                f"{path} must be an integer >= {minimum}",
                path,
            )
            return None
        return value

    def boolean(self, value: Any, path: str) -> bool | None:
        if not isinstance(value, bool):
            self.add("invalid_v2_fields", f"{path} must be boolean", path)
            return None
        return value

    def enum(self, value: Any, allowed: frozenset[str], path: str) -> str | None:
        rendered = self.text(value, path)
        if rendered is not None and rendered not in allowed:
            self.add(
                "invalid_v2_fields",
                f"{path} must be one of: {sorted(allowed)}",
                path,
            )
            return None
        return rendered


def _value(value: Mapping[str, Any], key: str) -> Any:
    return value.get(key)


def _validate_source_and_sequence(
    value: Mapping[str, Any], collector: _Collector
) -> tuple[Mapping[str, Any], Mapping[str, Any], dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    source = collector.object(
        _value(value, "source_manifest"), SOURCE_MANIFEST_FIELDS, "source_manifest"
    )
    collector.text(_value(source, "content_sha256"), "source_manifest.content_sha256", pattern=SHA256_PATTERN)
    collector.integer(_value(source, "byte_size"), "source_manifest.byte_size", 1)
    sequence = _value(value, "sequence")
    legacy_source = {
        key: deepcopy(_value(source, key))
        for key in ("id", "path", "total_frames", "frame_rate", "video", "audio")
    }
    legacy = {
        "timeline_version": 1,
        "timeline_id": _value(value, "timeline_id"),
        "source": legacy_source,
        "sequence": deepcopy(sequence),
        "semantic_gate": {"status": "pending", "reviewed_by": None, "notes": "v2"},
    }
    try:
        normalized = validate_timeline(legacy)
    except TimelineValidationError as exc:
        for issue in exc.issues:
            location = "sequence"
            if issue.get("track") is not None:
                location += f".{issue['track']}_clips"
            collector.add(issue["code"], issue["message"], location)
        normalized_sequence: Mapping[str, Any] = sequence if isinstance(sequence, Mapping) else {}
    else:
        normalized_sequence = normalized["sequence"]

    video = {
        clip["id"]: clip
        for clip in normalized_sequence.get("video_clips", [])
        if isinstance(clip, Mapping) and isinstance(clip.get("id"), str)
    }
    audio = {
        clip["id"]: clip
        for clip in normalized_sequence.get("audio_clips", [])
        if isinstance(clip, Mapping) and isinstance(clip.get("id"), str)
    }
    for track_name, clips in (("video", video), ("audio", audio)):
        for clip_id, clip in clips.items():
            if clip.get("edit_role") == "unclassified":
                collector.add(
                    "unclassified_clip",
                    "v2 delivery requires every retained clip to have an editorial role",
                    f"sequence.{track_name}_clips.{clip_id}.edit_role",
                )
    return source, normalized_sequence, video, audio


def _validate_time_references(
    value: Any,
    collector: _Collector,
    *,
    source_total_frames: int | None,
    timeline_total_frames: int | None,
    frame_rate: Mapping[str, Any],
) -> None:
    seen: set[str] = set()
    for index, raw in enumerate(collector.items(value, "editorial_evidence.time_references")):
        path = f"editorial_evidence.time_references[{index}]"
        item = collector.object(raw, TIME_REFERENCE_FIELDS, path)
        identifier = collector.text(_value(item, "id"), f"{path}.id")
        rendered = collector.text(_value(item, "raw"), f"{path}.raw")
        coordinate = collector.enum(
            _value(item, "coordinate_system"), frozenset({"source", "timeline"}), f"{path}.coordinate_system"
        )
        unit = collector.enum(
            _value(item, "unit"), frozenset(TIME_POINT_PATTERNS), f"{path}.unit"
        )
        start = collector.integer(_value(item, "start_frame"), f"{path}.start_frame")
        end = collector.integer(_value(item, "end_frame"), f"{path}.end_frame")
        collector.text(_value(item, "scope"), f"{path}.scope")
        collector.enum(
            _value(item, "confirmed_by"),
            frozenset({"user", "conversation_correction"}),
            f"{path}.confirmed_by",
        )
        collector.text(_value(item, "correction_evidence"), f"{path}.correction_evidence")
        if rendered is not None and unit is not None:
            try:
                parsed_start, parsed_end = _parse_time_range(
                    rendered, unit, frame_rate
                )
            except ValueError as exc:
                collector.add(
                    "time_reference_parse_error",
                    str(exc),
                    f"{path}.raw",
                )
            else:
                if start != parsed_start or end != parsed_end:
                    collector.add(
                        "time_reference_frame_mismatch",
                        "raw time must normalize exactly to start_frame and end_frame",
                        path,
                    )
        if start is not None and end is not None and start > end:
            collector.add("invalid_time_range", "normalized time range must increase", path)
        bound = (
            source_total_frames
            if coordinate == "source"
            else timeline_total_frames
            if coordinate == "timeline"
            else None
        )
        if end is not None and bound is not None and end > bound:
            collector.add(
                "time_reference_coordinate_bounds",
                f"normalized time exceeds {coordinate} bounds",
                path,
            )
        if identifier is not None:
            if identifier in seen:
                collector.add("duplicate_reference_id", f"duplicate time reference: {identifier}", path)
            seen.add(identifier)


def _clip_ids(
    value: Any,
    collector: _Collector,
    path: str,
    known: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    result: list[str] = []
    for index, raw in enumerate(collector.items(value, path)):
        item_path = f"{path}[{index}]"
        clip_id = collector.text(raw, item_path, pattern=CLIP_ID_PATTERN)
        if clip_id is not None:
            if clip_id not in known:
                collector.add("unknown_clip_reference", f"unknown clip id: {clip_id}", item_path)
            if clip_id in result:
                collector.add("duplicate_clip_reference", f"duplicate clip id: {clip_id}", item_path)
            result.append(clip_id)
    return result


def _validate_events(
    value: Any,
    collector: _Collector,
    *,
    total_frames: int | None,
    video: Mapping[str, Mapping[str, Any]],
    audio: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, str], dict[str, tuple[int, int]], dict[str, int]]:
    seen: dict[str, tuple[str | None, int | None]] = {}
    clip_owners: dict[str, str] = {}
    coverage: Counter[str] = Counter()
    event_ranges: dict[str, tuple[int, int]] = {}
    event_orders: dict[str, int] = {}
    video_positions = {
        clip_id: index
        for index, (clip_id, _clip) in enumerate(
            sorted(video.items(), key=lambda item: item[1]["timeline_start"])
        )
    }
    audio_positions = {
        clip_id: index
        for index, (clip_id, _clip) in enumerate(
            sorted(audio.items(), key=lambda item: item[1]["timeline_start"])
        )
    }
    previous_track_end = {"video": -1, "audio": -1}
    previous_order: int | None = None
    previous_clip_start: int | None = None
    for index, raw in enumerate(collector.items(value, "editorial_evidence.events", nonempty=True)):
        path = f"editorial_evidence.events[{index}]"
        event = collector.object(raw, EVENT_FIELDS, path)
        identifier = collector.text(_value(event, "id"), f"{path}.id")
        role = collector.enum(_value(event, "role"), EVENT_ROLES, f"{path}.role")
        video_ids = _clip_ids(_value(event, "video_clip_ids"), collector, f"{path}.video_clip_ids", video)
        audio_ids = _clip_ids(_value(event, "audio_clip_ids"), collector, f"{path}.audio_clip_ids", audio)
        if not video_ids:
            collector.add(
                "event_without_visual_anchor",
                "each event requires at least one retained video clip",
                f"{path}.video_clip_ids",
            )
        source_in = collector.integer(_value(event, "source_in"), f"{path}.source_in")
        source_out = collector.integer(_value(event, "source_out"), f"{path}.source_out", 1)
        order = collector.integer(_value(event, "timeline_order"), f"{path}.timeline_order")
        reason = collector.text(
            _value(event, "continuity_reason"), f"{path}.continuity_reason", nullable=True
        )
        if source_in is not None and source_out is not None and source_in >= source_out:
            collector.add("invalid_event_range", "event source range must increase", path)
        if source_out is not None and total_frames is not None and source_out > total_frames:
            collector.add("event_source_bounds", "event source range exceeds the source", path)
        if previous_order is not None and order is not None and order <= previous_order:
            collector.add("event_order", "events must be listed in strict final timeline order", f"{path}.timeline_order")
        if order is not None and order != index:
            collector.add(
                "event_order",
                "timeline_order must equal the event's zero-based final sequence position",
                f"{path}.timeline_order",
            )
        if order is not None:
            previous_order = order
        referenced_clips = [
            clip
            for clip_id in video_ids + audio_ids
            if (clip := (video.get(clip_id) or audio.get(clip_id))) is not None
        ]
        actual_start = min(
            (clip["timeline_start"] for clip in referenced_clips), default=None
        )
        if (
            previous_clip_start is not None
            and actual_start is not None
            and actual_start < previous_clip_start
        ):
            collector.add(
                "event_clip_order",
                "event order conflicts with referenced clips in the final sequence",
                path,
            )
        if actual_start is not None:
            previous_clip_start = actual_start
        if referenced_clips and source_in is not None and source_out is not None:
            envelope_in = min(clip["source_in"] for clip in referenced_clips)
            envelope_out = max(clip["source_out"] for clip in referenced_clips)
            if source_in != envelope_in or source_out != envelope_out:
                collector.add(
                    "event_envelope_mismatch",
                    "event source range must equal the exact referenced clip envelope",
                    path,
                )
        for clip_id in video_ids + audio_ids:
            clip = video.get(clip_id) or audio.get(clip_id)
            if (
                clip is not None
                and source_in is not None
                and source_out is not None
                and not (
                    source_in <= clip["source_in"]
                    and clip["source_out"] <= source_out
                )
            ):
                collector.add(
                    "event_clip_not_contained",
                    f"event range must fully contain referenced clip: {clip_id}",
                    path,
                )
            coverage[clip_id] += 1
            if identifier is not None:
                clip_owners[clip_id] = identifier
        for track, positions_by_id, clip_ids in (
            ("video", video_positions, video_ids),
            ("audio", audio_positions, audio_ids),
        ):
            positions = sorted(
                positions_by_id[clip_id]
                for clip_id in clip_ids
                if clip_id in positions_by_id
            )
            if positions and positions != list(range(positions[0], positions[-1] + 1)):
                collector.add(
                    "event_timeline_discontinuity",
                    f"one event cannot skip a retained {track} clip in final timeline order",
                    path,
                )
            if positions and positions[0] <= previous_track_end[track]:
                collector.add(
                    "event_clip_order",
                    f"event ownership interleaves on the {track} track",
                    path,
                )
            if positions:
                previous_track_end[track] = positions[-1]
        if role is not None:
            allowed_roles = EVENT_VIDEO_ROLE_COMPATIBILITY[role]
            for clip_id in video_ids:
                clip = video.get(clip_id)
                if clip is not None and clip.get("edit_role") not in allowed_roles:
                    collector.add(
                        "event_role_mismatch",
                        f"{role} cannot own video clip {clip_id} with role {clip.get('edit_role')}",
                        path,
                    )
        dependencies = collector.items(_value(event, "depends_on"), f"{path}.depends_on")
        causal: list[str] = []
        for dep_index, dep_raw in enumerate(dependencies):
            dep_path = f"{path}.depends_on[{dep_index}]"
            dependency = collector.text(dep_raw, dep_path)
            if dependency is None:
                continue
            if dependency not in seen:
                collector.add("invalid_event_dependency", "dependency must refer to an earlier event", dep_path)
            else:
                dep_role, dep_order = seen[dependency]
                if dep_order is not None and order is not None and dep_order >= order:
                    collector.add("invalid_event_dependency", "dependency must precede the event", dep_path)
                if dep_role in CAUSAL_ROLES:
                    causal.append(dependency)
        if role in ROLES_REQUIRING_CAUSE and not causal:
            collector.add(
                "missing_cause_anchor",
                f"{role} requires an earlier retained cause or state anchor",
                f"{path}.depends_on",
            )
        if role in {"transition", "state_change"} and reason is None:
            collector.add(
                "missing_continuity_reason",
                "transition and state changes require a continuity reason",
                f"{path}.continuity_reason",
            )
        if identifier is not None:
            if identifier in seen:
                collector.add("duplicate_event_id", f"duplicate event id: {identifier}", path)
            seen[identifier] = (role, order)
            if source_in is not None and source_out is not None:
                event_ranges[identifier] = (source_in, source_out)
            if order is not None:
                event_orders[identifier] = order
    for track, known in (("video", video), ("audio", audio)):
        for clip_id in known:
            count = coverage[clip_id]
            if count != 1:
                collector.add(
                    "event_clip_coverage",
                    f"retained {track} clip {clip_id} must belong to exactly one event; found {count}",
                    f"sequence.{track}_clips.{clip_id}",
                )
    return clip_owners, event_ranges, event_orders


def _validate_microbeats(
    value: Any,
    collector: _Collector,
    *,
    purpose: str | None,
    total_frames: int | None,
    video: Mapping[str, Mapping[str, Any]],
    audio: Mapping[str, Mapping[str, Any]],
    event_owners: Mapping[str, str],
    event_ranges: Mapping[str, tuple[int, int]],
    event_orders: Mapping[str, int],
) -> None:
    used_video: Counter[str] = Counter()
    used_audio: Counter[str] = Counter()
    seen: set[str] = set()
    retained_intervals: dict[str, list[tuple[int, int]]] = {
        "video": [],
        "audio": [],
    }
    removed: list[tuple[str, str | None, int | None, int | None, str]] = []
    previous_track_timeline_start: dict[str, int | None] = {
        "video": None,
        "audio": None,
    }
    previous_event_order: int | None = None
    video_positions = {
        clip_id: index
        for index, (clip_id, _clip) in enumerate(
            sorted(video.items(), key=lambda item: item[1]["timeline_start"])
        )
    }
    audio_positions = {
        clip_id: index
        for index, (clip_id, _clip) in enumerate(
            sorted(audio.items(), key=lambda item: item[1]["timeline_start"])
        )
    }
    for index, raw in enumerate(collector.items(value, "editorial_evidence.microbeats", nonempty=True)):
        path = f"editorial_evidence.microbeats[{index}]"
        beat = collector.object(raw, MICROBEAT_FIELDS, path)
        identifier = collector.text(_value(beat, "id"), f"{path}.id")
        event_id = collector.text(_value(beat, "event_id"), f"{path}.event_id")
        decision = collector.enum(
            _value(beat, "decision"), frozenset({"keep", "compress", "remove"}), f"{path}.decision"
        )
        media_scope = collector.enum(
            _value(beat, "media_scope"),
            frozenset({"video", "audio", "both"}),
            f"{path}.media_scope",
        )
        collector.text(_value(beat, "purpose"), f"{path}.purpose")
        video_ids = _clip_ids(_value(beat, "video_clip_ids"), collector, f"{path}.video_clip_ids", video)
        audio_ids = _clip_ids(_value(beat, "audio_clip_ids"), collector, f"{path}.audio_clip_ids", audio)
        source_in = collector.integer(_value(beat, "source_in"), f"{path}.source_in")
        source_out = collector.integer(_value(beat, "source_out"), f"{path}.source_out", 1)
        boundary = collector.enum(
            _value(beat, "boundary_review"), frozenset({"pending", "passed", "failed"}), f"{path}.boundary_review"
        )
        if source_in is not None and source_out is not None and source_in >= source_out:
            collector.add("invalid_microbeat_range", "microbeat source range must increase", path)
        if source_out is not None and total_frames is not None and source_out > total_frames:
            collector.add("microbeat_source_bounds", "microbeat source range exceeds the source", path)
        if decision == "remove" and (video_ids or audio_ids):
            collector.add(
                "removed_microbeat_retained",
                "a removed microbeat cannot reference retained sequence clips",
                path,
            )
        if decision in {"keep", "compress"} and not (video_ids or audio_ids):
            collector.add(
                "retained_microbeat_without_clip",
                "a retained microbeat must reference its final sequence clips",
                path,
            )
        actual_scope = (
            "both"
            if video_ids and audio_ids
            else "video"
            if video_ids
            else "audio"
            if audio_ids
            else media_scope
        )
        if decision != "remove" and media_scope is not None and media_scope != actual_scope:
            collector.add(
                "microbeat_media_scope_mismatch",
                "media_scope must match the referenced clip tracks",
                f"{path}.media_scope",
            )
        if event_id is not None and event_id not in event_ranges:
            collector.add(
                "unknown_event_reference",
                f"unknown event id: {event_id}",
                f"{path}.event_id",
            )
        event_order = event_orders.get(event_id or "")
        if (
            previous_event_order is not None
            and event_order is not None
            and event_order < previous_event_order
        ):
            collector.add(
                "microbeat_event_order",
                "microbeats cannot return to an earlier event",
                path,
            )
        if event_order is not None:
            previous_event_order = event_order
        referenced_clips = [
            clip
            for clip_id in video_ids + audio_ids
            if (clip := (video.get(clip_id) or audio.get(clip_id))) is not None
        ]
        if referenced_clips and source_in is not None and source_out is not None:
            envelope_in = min(clip["source_in"] for clip in referenced_clips)
            envelope_out = max(clip["source_out"] for clip in referenced_clips)
            if source_in != envelope_in or source_out != envelope_out:
                collector.add(
                    "microbeat_envelope_mismatch",
                    "microbeat source range must equal the exact referenced clip envelope",
                    path,
                )
        for clip_id in video_ids + audio_ids:
            clip = video.get(clip_id) or audio.get(clip_id)
            if (
                clip is not None
                and source_in is not None
                and source_out is not None
                and not (
                    source_in <= clip["source_in"]
                    and clip["source_out"] <= source_out
                )
            ):
                collector.add(
                    "microbeat_clip_not_contained",
                    f"microbeat range must fully contain referenced clip: {clip_id}",
                    path,
                )
            if event_id is not None and event_owners.get(clip_id) != event_id:
                collector.add(
                    "microbeat_event_mismatch",
                    f"clip {clip_id} is not owned by event {event_id}",
                    path,
                )
        for positions, clip_ids, track in (
            (video_positions, video_ids, "video"),
            (audio_positions, audio_ids, "audio"),
        ):
            indices = sorted(positions[clip_id] for clip_id in clip_ids if clip_id in positions)
            if indices and indices != list(range(indices[0], indices[-1] + 1)):
                collector.add(
                    "microbeat_timeline_discontinuity",
                    f"one microbeat cannot skip a retained {track} clip",
                    path,
                )
        for track, clip_ids, known in (
            ("video", video_ids, video),
            ("audio", audio_ids, audio),
        ):
            actual_timeline_start = min(
                (
                    known[clip_id]["timeline_start"]
                    for clip_id in clip_ids
                    if clip_id in known
                ),
                default=None,
            )
            previous_start = previous_track_timeline_start[track]
            if (
                previous_start is not None
                and actual_timeline_start is not None
                and actual_timeline_start < previous_start
            ):
                collector.add(
                    "microbeat_timeline_order",
                    f"retained {track} microbeats must follow final timeline order",
                    path,
                )
            if actual_timeline_start is not None:
                previous_track_timeline_start[track] = actual_timeline_start
        intervals = [
            (clip["source_in"], clip["source_out"])
            for clip in referenced_clips
        ]
        primary_intervals = [
            (video[clip_id]["source_in"], video[clip_id]["source_out"])
            for clip_id in video_ids
            if clip_id in video
        ] or [
            (audio[clip_id]["source_in"], audio[clip_id]["source_out"])
            for clip_id in audio_ids
            if clip_id in audio
        ]
        if decision == "keep" and intervals and not _intervals_are_contiguous(intervals):
            collector.add(
                "microbeat_source_discontinuity",
                "keep microbeat cannot bridge a removed source interval",
                path,
            )
        if decision == "compress" and primary_intervals and _intervals_are_contiguous(primary_intervals):
            collector.add(
                "compress_without_reduction",
                "compress microbeat must contain an actual removed source interval",
                path,
            )
        if decision == "remove":
            removed.append((media_scope or "both", event_id, source_in, source_out, path))
        else:
            retained_intervals["video"].extend(
                (video[clip_id]["source_in"], video[clip_id]["source_out"])
                for clip_id in video_ids
                if clip_id in video
            )
            retained_intervals["audio"].extend(
                (audio[clip_id]["source_in"], audio[clip_id]["source_out"])
                for clip_id in audio_ids
                if clip_id in audio
            )
        if purpose == "premiere_xml" and boundary != "passed":
            collector.add(
                "microbeat_review_incomplete",
                "every retained or removed microbeat needs a passed boundary review before export",
                f"{path}.boundary_review",
            )
        used_video.update(video_ids)
        used_audio.update(audio_ids)
        if identifier is not None:
            if identifier in seen:
                collector.add("duplicate_microbeat_id", f"duplicate microbeat id: {identifier}", path)
            seen.add(identifier)
    for track, known, used in (("video", video, used_video), ("audio", audio, used_audio)):
        for clip_id in known:
            count = used[clip_id]
            if count != 1:
                collector.add(
                    "microbeat_clip_coverage",
                    f"retained {track} clip {clip_id} must belong to exactly one microbeat; found {count}",
                    f"sequence.{track}_clips.{clip_id}",
                )
    for media_scope, event_id, source_in, source_out, path in removed:
        if source_in is None or source_out is None:
            continue
        event_range = event_ranges.get(event_id or "")
        if event_range is not None and not (
            event_range[0] <= source_in and source_out <= event_range[1]
        ):
            collector.add(
                "removed_range_outside_event",
                "removed microbeat must stay inside its event source envelope",
                path,
            )
        tracks = ("video", "audio") if media_scope == "both" else (media_scope,)
        for track in tracks:
            if any(
                retained_in < source_out and source_in < retained_out
                for retained_in, retained_out in retained_intervals[track]
            ):
                collector.add(
                    "removed_range_conflict",
                    f"removed {track} range overlaps a retained clip",
                    path,
                )


def _validate_feedback(
    value: Any,
    collector: _Collector,
    *,
    workflow_profile: str | None,
    revision_status: str | None,
    known_clips: Mapping[str, Mapping[str, Any]],
    purpose: str | None,
    current_payload: Mapping[str, Any],
    current_source_hash: str,
    revision_supersedes: str | None,
    revision_checked_at: datetime | None,
    baseline_reference: Mapping[str, Any] | None,
) -> None:
    feedback = collector.object(value, FEEDBACK_FIELDS, "editorial_evidence.feedback")
    baseline = _value(feedback, "baseline_payload_fingerprint")
    if baseline is not None:
        collector.text(
            baseline,
            "editorial_evidence.feedback.baseline_payload_fingerprint",
            pattern=SHA256_PATTERN,
        )
    baseline_required = workflow_profile in {"approved_delta", "format_regeneration"}
    if baseline_required and baseline is None:
        collector.add(
            "missing_feedback_baseline",
            f"{workflow_profile} requires the exact baseline payload fingerprint",
            "editorial_evidence.feedback.baseline_payload_fingerprint",
        )
    baseline_clips: dict[str, Mapping[str, Any]] = {}
    changed_ids: set[str] = set()
    if purpose == "premiere_xml" and baseline_required and baseline_reference is None:
        collector.add(
            "baseline_reference_required",
            f"{workflow_profile} export requires the actual baseline v2 payload",
            "editorial_evidence.feedback.baseline_payload_fingerprint",
        )
    if baseline_reference is not None:
        if baseline != task_payload_fingerprint(baseline_reference):
            collector.add(
                "baseline_fingerprint_mismatch",
                "baseline reference state does not match baseline_payload_fingerprint",
                "editorial_evidence.feedback.baseline_payload_fingerprint",
            )
        reference_source = baseline_reference.get("source_manifest")
        if not isinstance(reference_source, Mapping) or source_manifest_fingerprint(
            reference_source
        ) != current_source_hash:
            collector.add(
                "baseline_source_mismatch",
                "baseline and current payload must use the same source manifest",
                "editorial_evidence.feedback.baseline_payload_fingerprint",
            )
        reference_revision = baseline_reference.get("revision")
        if not isinstance(reference_revision, Mapping) or reference_revision.get(
            "status"
        ) not in {"current", "approved"}:
            collector.add(
                "baseline_not_approved",
                "baseline reference must be a current or approved revision",
                "editorial_evidence.feedback.baseline_payload_fingerprint",
            )
        baseline_approval_time = _latest_active_whole_revision_approval_time(
            baseline_reference
        )
        if baseline_approval_time is None:
            collector.add(
                "baseline_approval_missing",
                "baseline requires a latest active whole-revision user approval",
                "editorial_evidence.feedback.baseline_payload_fingerprint",
            )
        elif (
            revision_checked_at is not None
            and revision_checked_at < baseline_approval_time
        ):
            collector.add(
                "baseline_precedes_revision",
                "the new revision cannot predate the exact baseline approval",
                "revision.checked_at",
            )
        if revision_supersedes != baseline_reference.get("timeline_id"):
            collector.add(
                "revision_supersedes_mismatch",
                "current revision must supersede the exact baseline timeline",
                "revision.supersedes",
            )
        if workflow_profile == "format_regeneration" and editorial_fingerprint(
            current_payload
        ) != editorial_fingerprint(baseline_reference):
            collector.add(
                "format_regeneration_editorial_change",
                "format regeneration cannot change editorial content",
                "workflow_profile",
            )
        reference_sequence = baseline_reference.get("sequence")
        if isinstance(reference_sequence, Mapping):
            for track in ("video_clips", "audio_clips"):
                for clip in reference_sequence.get(track, []):
                    if isinstance(clip, Mapping) and isinstance(clip.get("id"), str):
                        baseline_clips[clip["id"]] = clip
        changed_ids.update(set(baseline_clips) ^ set(known_clips))
        for clip_id in set(baseline_clips) & set(known_clips):
            if _clip_signature(baseline_clips[clip_id]) != _clip_signature(
                known_clips[clip_id]
            ) or _clip_evidence_signature(
                baseline_reference, clip_id
            ) != _clip_evidence_signature(current_payload, clip_id):
                changed_ids.add(clip_id)
        for track in ("video_clips", "audio_clips"):
            baseline_order = [
                clip["id"]
                for clip in baseline_reference["sequence"][track]
                if clip["id"] in known_clips
            ]
            current_order = [
                clip["id"]
                for clip in current_payload["sequence"][track]
                if clip["id"] in baseline_clips
            ]
            if baseline_order != current_order:
                changed_ids.update(baseline_order)
                changed_ids.update(current_order)
    comparison_clips = {**baseline_clips, **known_clips}
    preservation_entries: dict[str, dict[str, tuple[str, ...]]] = {
        "positive_locks": {},
        "untouched": {},
    }
    for collection_name in ("positive_locks", "untouched"):
        entries = collector.items(_value(feedback, collection_name), f"editorial_evidence.feedback.{collection_name}")
        seen_entry_ids: set[str] = set()
        for index, raw in enumerate(entries):
            path = f"editorial_evidence.feedback.{collection_name}[{index}]"
            entry = collector.object(raw, PRESERVATION_FIELDS, path)
            collector.text(_value(entry, "scope"), f"{path}.scope")
            entry_id = collector.text(_value(entry, "id"), f"{path}.id")
            clip_ids = _clip_ids(
                _value(entry, "clip_ids"),
                collector,
                f"{path}.clip_ids",
                comparison_clips,
            )
            if baseline_required and not clip_ids:
                collector.add(
                    "empty_preservation_scope",
                    f"{collection_name} must identify exact baseline clips",
                    f"{path}.clip_ids",
                )
            if entry_id is not None:
                if entry_id in seen_entry_ids:
                    collector.add(
                        "duplicate_feedback_id",
                        f"duplicate {collection_name} id: {entry_id}",
                        f"{path}.id",
                    )
                seen_entry_ids.add(entry_id)
                preservation_entries[collection_name][entry_id] = tuple(clip_ids)
            collector.text(_value(entry, "evidence"), f"{path}.evidence")
            preserved = collector.boolean(_value(entry, "preserved"), f"{path}.preserved")
            if purpose == "premiere_xml" and preserved is not True:
                collector.add(
                    "feedback_regression",
                    f"{collection_name} must be preserved before export",
                    path,
                )
            if baseline_reference is not None:
                for clip_id in clip_ids:
                    if clip_id not in baseline_clips or clip_id not in known_clips:
                        collector.add(
                            f"{collection_name.rstrip('s')}_diff",
                            f"protected clip {clip_id} must exist in baseline and current payload",
                            path,
                        )
                    elif _clip_signature(
                        baseline_clips[clip_id]
                    ) != _clip_signature(known_clips[clip_id]) or _clip_evidence_signature(
                        baseline_reference, clip_id
                    ) != _clip_evidence_signature(current_payload, clip_id):
                        collector.add(
                            f"{collection_name.rstrip('s')}_diff",
                            f"protected clip {clip_id} changed from the approved baseline",
                            path,
                        )
    if baseline_reference is not None:
        reference_feedback = baseline_reference["editorial_evidence"]["feedback"]
        for collection_name in ("positive_locks", "untouched"):
            current_entries = preservation_entries[collection_name]
            for entry in reference_feedback[collection_name]:
                entry_id = entry["id"]
                if entry_id not in current_entries or tuple(entry["clip_ids"]) != current_entries[entry_id]:
                    collector.add(
                        "feedback_lock_missing",
                        f"baseline {collection_name} entry {entry_id} must be carried forward",
                        f"editorial_evidence.feedback.{collection_name}",
                    )
    defects = collector.items(_value(feedback, "defects"), "editorial_evidence.feedback.defects")
    defect_clip_ids: set[str] = set()
    resolved_defects: list[tuple[str, set[str]]] = []
    seen_defect_ids: set[str] = set()
    current_defects: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(defects):
        path = f"editorial_evidence.feedback.defects[{index}]"
        defect = collector.object(raw, DEFECT_FIELDS, path)
        defect_id = collector.text(_value(defect, "id"), f"{path}.id")
        if defect_id is not None:
            if defect_id in seen_defect_ids:
                collector.add(
                    "duplicate_feedback_id",
                    f"duplicate defect id: {defect_id}",
                    f"{path}.id",
                )
            seen_defect_ids.add(defect_id)
        collector.text(_value(defect, "scope"), f"{path}.scope")
        clip_ids = _clip_ids(
            _value(defect, "clip_ids"),
            collector,
            f"{path}.clip_ids",
            comparison_clips,
        )
        defect_clip_ids.update(clip_ids)
        status = collector.enum(
            _value(defect, "status"),
            frozenset({"pending", "resolved", "approved_defer", "unreproduced"}),
            f"{path}.status",
        )
        collector.text(_value(defect, "evidence"), f"{path}.evidence")
        approved_by = collector.text(
            _value(defect, "approved_by"), f"{path}.approved_by", nullable=True
        )
        if status in {"approved_defer", "unreproduced"} and approved_by != "user":
            collector.add("unresolved_defect", "deferred defects require explicit user approval", path)
        if status in {"pending", "resolved"} and approved_by is not None:
            collector.add(
                "stale_defect_approval",
                "pending or resolved defects cannot retain defer approval",
                f"{path}.approved_by",
            )
        if status == "pending" and purpose == "premiere_xml":
            collector.add("unresolved_defect", "pending defects block XML export", path)
        if status == "pending" and revision_status in {"current", "approved"}:
            collector.add(
                "unresolved_defect",
                "current or approved revisions cannot retain pending defects",
                path,
            )
        if status == "resolved":
            resolved_defects.append((path, set(clip_ids)))
        if defect_id is not None and status is not None:
            current_defects[defect_id] = {
                "scope": _value(defect, "scope"),
                "clip_ids": tuple(clip_ids),
                "status": status,
                "approved_by": approved_by,
            }
    if baseline_reference is not None:
        reference_feedback = baseline_reference["editorial_evidence"]["feedback"]
        for reference_defect in reference_feedback["defects"]:
            if reference_defect["status"] not in {
                "pending",
                "approved_defer",
                "unreproduced",
            }:
                continue
            defect_id = reference_defect["id"]
            current_defect = current_defects.get(defect_id)
            if current_defect is None:
                collector.add(
                    "feedback_defect_missing",
                    f"baseline unresolved defect {defect_id} must be carried forward or resolved",
                    "editorial_evidence.feedback.defects",
                )
                continue
            if (
                current_defect["scope"] != reference_defect["scope"]
                or current_defect["clip_ids"]
                != tuple(reference_defect["clip_ids"])
            ):
                collector.add(
                    "feedback_defect_scope_mismatch",
                    f"baseline defect {defect_id} changed ownership scope",
                    "editorial_evidence.feedback.defects",
                )
            if (
                reference_defect["status"] in {"approved_defer", "unreproduced"}
                and current_defect["status"]
                not in {reference_defect["status"], "pending", "resolved"}
            ):
                collector.add(
                    "feedback_defect_state_mismatch",
                    f"baseline user decision for defect {defect_id} was replaced without a valid transition",
                    "editorial_evidence.feedback.defects",
                )
    if baseline_reference is not None and workflow_profile == "approved_delta":
        unscoped = changed_ids - defect_clip_ids
        if unscoped:
            collector.add(
                "feedback_unscoped_delta",
                f"baseline changes are not owned by a defect: {sorted(unscoped)}",
                "editorial_evidence.feedback.defects",
            )
        for path, clip_ids in resolved_defects:
            if not clip_ids or not (clip_ids & changed_ids):
                collector.add(
                    "resolved_defect_without_delta",
                    "a resolved defect must identify an actual baseline change",
                    path,
                )


def _validate_revision(
    value: Any,
    collector: _Collector,
    timeline_id: str | None,
    purpose: str | None,
) -> tuple[str | None, str | None, datetime | None]:
    revision = collector.object(value, REVISION_FIELDS, "revision")
    status = collector.enum(_value(revision, "status"), REVISION_STATUSES, "revision.status")
    supersedes = collector.text(
        _value(revision, "supersedes"), "revision.supersedes", nullable=True
    )
    checked_at = _parse_timestamp(
        _value(revision, "checked_at"), collector, "revision.checked_at"
    )
    owner = collector.text(_value(revision, "state_owner_id"), "revision.state_owner_id")
    if owner is not None and timeline_id is not None and owner != timeline_id:
        collector.add(
            "state_owner_conflict",
            "revision.state_owner_id must identify this exact timeline payload",
            "revision.state_owner_id",
        )
    if purpose == "premiere_xml" and status in {"use_prohibited", "historical"}:
        collector.add("invalid_source_revision", "prohibited or historical revisions cannot be exported", "revision.status")
    return status, supersedes, checked_at


def _validate_approval(
    value: Any,
    collector: _Collector,
    *,
    workflow_profile: str | None,
    revision_status: str | None,
    timeline_id: str | None,
    source_hash: str,
    current_payload_fingerprint: str,
    current_editorial_fingerprint: str,
    current_review_completed_at: datetime | None,
    validation_status: str | None,
    revision_checked_at: datetime | None,
    calibration_reference: Mapping[str, Any] | None,
    purpose: str | None,
) -> None:
    approval = collector.object(value, APPROVAL_FIELDS, "approval")
    calibration = collector.object(_value(approval, "calibration"), CALIBRATION_FIELDS, "approval.calibration")
    required = collector.boolean(_value(calibration, "required"), "approval.calibration.required")
    status = collector.enum(
        _value(calibration, "status"),
        frozenset({"pending", "approved", "rejected", "not_required"}),
        "approval.calibration.status",
    )
    artifact_id = collector.text(_value(calibration, "artifact_id"), "approval.calibration.artifact_id", nullable=True)
    approved_fingerprint = collector.text(
        _value(calibration, "approved_payload_fingerprint"),
        "approval.calibration.approved_payload_fingerprint",
        nullable=True,
        pattern=SHA256_PATTERN,
    )
    approved_by = collector.text(_value(calibration, "approved_by"), "approval.calibration.approved_by", nullable=True)
    evidence = collector.text(
        _value(calibration, "approval_evidence"), "approval.calibration.approval_evidence", nullable=True
    )
    calibration_checked_at = _parse_timestamp(
        _value(calibration, "checked_at"),
        collector,
        "approval.calibration.checked_at",
        nullable=True,
    )
    if required is False and status != "not_required":
        collector.add("invalid_calibration_state", "non-required calibration must be not_required", "approval.calibration")
    if required is True and status == "not_required":
        collector.add("invalid_calibration_state", "required calibration cannot be not_required", "approval.calibration")
    if status in {"approved", "not_required"} and (
        approved_by != "user"
        or artifact_id is None
        or approved_fingerprint is None
        or evidence is None
        or calibration_checked_at is None
    ):
        collector.add(
            "calibration_approval_missing",
            "approved or waived calibration requires an exact user-approved reference",
            "approval.calibration",
        )
    if status in {"pending", "rejected"} and any(
        item is not None
        for item in (
            artifact_id,
            approved_fingerprint,
            approved_by,
            evidence,
            calibration_checked_at,
        )
    ):
        collector.add("stale_calibration_approval", "pending or rejected calibration cannot retain approval evidence", "approval.calibration")
    if status == "approved" and workflow_profile == "calibration":
        if artifact_id != timeline_id or approved_fingerprint != current_payload_fingerprint:
            collector.add(
                "calibration_reference_mismatch",
                "approved calibration must identify this exact calibration payload",
                "approval.calibration",
            )
        if revision_status != "approved":
            collector.add(
                "calibration_reference_not_approved",
                "approved calibration must also be an approved revision",
                "revision.status",
            )
        if (
            calibration_checked_at is not None
            and current_review_completed_at is not None
            and calibration_checked_at < current_review_completed_at
        ):
            collector.add(
                "approval_precedes_review",
                "calibration approval cannot predate its semantic review",
                "approval.calibration.checked_at",
            )
    if (
        purpose == "premiere_xml"
        and workflow_profile in {"new_full_edit", "approved_delta"}
        and required is True
        and status != "approved"
    ):
        collector.add("calibration_not_approved", "full editing is blocked until calibration is user-approved", "approval.calibration.status")
    if purpose == "premiere_xml" and status == "rejected":
        collector.add("calibration_rejected", "rejected calibration cannot be reused", "approval.calibration.status")
    if (
        purpose == "premiere_xml"
        and workflow_profile in {"new_full_edit", "approved_delta"}
        and (
            required is True
            and status == "approved"
            or required is False
            and status == "not_required"
        )
    ):
        if calibration_reference is None:
            collector.add(
                "calibration_reference_required",
                "full edit export requires the actual approved calibration or grammar reference",
                "approval.calibration.approved_payload_fingerprint",
            )
        else:
            reference_source = calibration_reference.get("source_manifest")
            reference_validation = calibration_reference.get("validation")
            reference_revision = calibration_reference.get("revision")
            reference_calibration = calibration_reference.get("approval", {}).get(
                "calibration"
            )
            if (
                calibration_reference.get("workflow_profile") != "calibration"
                or calibration_reference.get("timeline_id") != artifact_id
                or task_payload_fingerprint(calibration_reference)
                != approved_fingerprint
            ):
                collector.add(
                    "calibration_reference_mismatch",
                    "calibration reference must match the exact approved calibration artifact",
                    "approval.calibration",
                )
            if not isinstance(reference_source, Mapping) or source_manifest_fingerprint(
                reference_source
            ) != source_hash:
                collector.add(
                    "calibration_source_mismatch",
                    "calibration and full edit must use the same source manifest",
                    "approval.calibration",
                )
            if (
                not isinstance(reference_revision, Mapping)
                or reference_revision.get("status") != "approved"
                or not isinstance(reference_validation, Mapping)
                or reference_validation.get("semantic_status") != "passed"
                or reference_validation.get("reviewed_editorial_fingerprint")
                != editorial_fingerprint(calibration_reference)
                or not isinstance(reference_calibration, Mapping)
                or reference_calibration.get("status") != "approved"
                or reference_calibration.get("artifact_id")
                != calibration_reference.get("timeline_id")
                or reference_calibration.get("approved_payload_fingerprint")
                != payload_fingerprint(calibration_reference)
            ):
                collector.add(
                    "calibration_reference_not_approved",
                    "calibration reference must carry exact semantic and user approval",
                    "approval.calibration",
                )
            reference_approval_time: datetime | None = None
            if isinstance(reference_calibration, Mapping) and isinstance(
                reference_calibration.get("checked_at"), str
            ):
                try:
                    reference_approval_time = datetime.fromisoformat(
                        reference_calibration["checked_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    reference_approval_time = None
            if (
                reference_approval_time is not None
                and calibration_checked_at != reference_approval_time
            ):
                collector.add(
                    "calibration_reference_mismatch",
                    "calibration binding time must equal the referenced user approval time",
                    "approval.calibration.checked_at",
                )
            if (
                reference_approval_time is not None
                and revision_checked_at is not None
                and revision_checked_at < reference_approval_time
            ):
                collector.add(
                    "calibration_precedes_revision",
                    "full edit revision must be created after the referenced calibration approval",
                    "revision.checked_at",
                )
            reference_reviewed_at = _latest_review_time(calibration_reference)
            if (
                calibration_checked_at is not None
                and reference_reviewed_at is not None
                and calibration_checked_at < reference_reviewed_at
            ):
                collector.add(
                    "approval_precedes_review",
                    "calibration approval cannot predate referenced semantic review",
                    "approval.calibration.checked_at",
                )

    decision_candidates: list[
        tuple[datetime, int, str, tuple[str, ...], str | None, str | None]
    ] = []
    seen_decision_ids: set[str] = set()
    for index, raw in enumerate(collector.items(_value(approval, "decisions"), "approval.decisions")):
        path = f"approval.decisions[{index}]"
        decision = collector.object(raw, DECISION_FIELDS, path)
        decision_id = collector.text(_value(decision, "id"), f"{path}.id")
        if decision_id is not None:
            if decision_id in seen_decision_ids:
                collector.add(
                    "duplicate_approval_id",
                    f"duplicate approval decision id: {decision_id}",
                    f"{path}.id",
                )
            seen_decision_ids.add(decision_id)
        decision_artifact = collector.text(_value(decision, "artifact_id"), f"{path}.artifact_id")
        decision_scope = collector.enum(
            _value(decision, "approved_scope"),
            frozenset({WHOLE_REVISION_SCOPE}),
            f"{path}.approved_scope",
        )
        decision_source = collector.text(
            _value(decision, "source_manifest_hash"), f"{path}.source_manifest_hash", pattern=SHA256_PATTERN
        )
        disposition = collector.enum(
            _value(decision, "decision"), frozenset({"approved", "rejected", "superseded"}), f"{path}.decision"
        )
        invalidated = collector.items(_value(decision, "invalidated_by"), f"{path}.invalidated_by")
        normalized_invalidated: list[str] = []
        for invalidation_index, invalidation in enumerate(invalidated):
            normalized = collector.text(
                invalidation, f"{path}.invalidated_by[{invalidation_index}]"
            )
            if normalized is not None:
                if normalized in normalized_invalidated:
                    collector.add(
                        "duplicate_invalidation",
                        f"duplicate invalidation id: {normalized}",
                        f"{path}.invalidated_by[{invalidation_index}]",
                    )
                normalized_invalidated.append(normalized)
        decision_approver = collector.text(_value(decision, "approved_by"), f"{path}.approved_by")
        decision_checked_at = _parse_timestamp(
            _value(decision, "checked_at"), collector, f"{path}.checked_at"
        )
        reviewed = collector.text(
            _value(decision, "reviewed_editorial_fingerprint"),
            f"{path}.reviewed_editorial_fingerprint",
            pattern=SHA256_PATTERN,
        )
        if disposition == "approved" and decision_approver != "user":
            collector.add("invalid_user_approval", "approved decisions must be owned by the user", path)
        if disposition == "rejected" and decision_approver != "user":
            collector.add("invalid_user_rejection", "rejected decisions must be owned by the user", path)
        if decision_source is not None and decision_source != source_hash:
            collector.add("approval_source_mismatch", "approval source manifest does not match this payload", path)
        if (
            disposition == "approved"
            and decision_checked_at is not None
            and current_review_completed_at is not None
            and decision_checked_at < current_review_completed_at
        ):
            collector.add(
                "approval_precedes_review",
                "user approval cannot predate semantic review",
                f"{path}.checked_at",
            )
        if (
            disposition is not None
            and decision_checked_at is not None
            and decision_artifact == timeline_id
            and decision_source == source_hash
            and reviewed == current_editorial_fingerprint
        ):
            decision_candidates.append((
                decision_checked_at,
                index,
                disposition,
                tuple(normalized_invalidated),
                decision_approver,
                decision_scope,
            ))
    latest_decision: (
        tuple[datetime, int, str, tuple[str, ...], str | None, str | None] | None
    ) = None
    if decision_candidates:
        latest_time = max(candidate[0] for candidate in decision_candidates)
        tied = [candidate for candidate in decision_candidates if candidate[0] == latest_time]
        tied_states = {
            (candidate[2], candidate[3], candidate[4], candidate[5])
            for candidate in tied
        }
        if len(tied_states) != 1:
            collector.add(
                "approval_decision_conflict",
                "conflicting exact user decisions share the latest timestamp",
                "approval.decisions",
            )
        else:
            latest_decision = max(tied, key=lambda candidate: candidate[1])
    active_decision = bool(
        latest_decision is not None
        and latest_decision[2] == "approved"
        and not latest_decision[3]
        and latest_decision[4] == "user"
        and latest_decision[5] == WHOLE_REVISION_SCOPE
        and (
            current_review_completed_at is None
            or latest_decision[0] >= current_review_completed_at
        )
    )
    if (
        status == "approved"
        and workflow_profile == "calibration"
        and active_decision
        and calibration_checked_at != latest_decision[0]
    ):
        collector.add(
            "calibration_decision_time_mismatch",
            "calibration approval time must equal the latest whole-revision user approval",
            "approval.calibration.checked_at",
        )
    if (
        latest_decision is not None
        and latest_decision[2] == "approved"
        and latest_decision[3]
        and purpose == "premiere_xml"
    ):
        collector.add(
            "approval_invalidated",
            "an invalidated approval cannot authorize XML export",
            "approval.decisions",
        )
    if latest_decision is not None and latest_decision[2] == "rejected":
        if revision_status != "use_prohibited":
            collector.add(
                "rejected_revision_state_mismatch",
                "the latest user rejection requires revision.status=use_prohibited",
                "revision.status",
            )
        if purpose == "premiere_xml":
            collector.add(
                "user_rejected_revision",
                "the latest user decision rejects this exact editorial payload",
                "approval.decisions",
            )
    if latest_decision is not None and latest_decision[2] == "superseded":
        if revision_status != "historical":
            collector.add(
                "superseded_revision_state_mismatch",
                "the latest superseded decision requires revision.status=historical",
                "revision.status",
            )
        if purpose == "premiere_xml":
            collector.add(
                "superseded_revision",
                "a superseded editorial payload cannot be exported",
                "approval.decisions",
            )
    if revision_status in {"current", "approved"} and not active_decision:
        collector.add(
            "approval_payload_mismatch",
            "current or approved revision requires an active user decision for this exact editorial payload",
            "approval.decisions",
        )
    if revision_status in {"current", "approved"} and validation_status != "passed":
        collector.add(
            "approval_without_semantic_pass",
            "current or approved revision requires passed semantic validation",
            "validation.semantic_status",
        )


def _validate_validation(
    value: Any,
    collector: _Collector,
    *,
    current_editorial_fingerprint: str,
    revision_checked_at: datetime | None,
    workflow_profile: str | None,
    purpose: str | None,
) -> datetime | None:
    validation = collector.object(value, VALIDATION_FIELDS, "validation")
    reviewed = collector.text(
        _value(validation, "reviewed_editorial_fingerprint"),
        "validation.reviewed_editorial_fingerprint",
        nullable=True,
        pattern=SHA256_PATTERN,
    )
    reviewer = collector.text(_value(validation, "reviewer"), "validation.reviewer", nullable=True)
    status = collector.enum(
        _value(validation, "semantic_status"),
        frozenset({"not_run", "passed", "failed"}),
        "validation.semantic_status",
    )
    passes = collector.object(
        _value(validation, "passes"), frozenset(VALIDATION_PASS_NAMES), "validation.passes"
    )
    pass_statuses: list[str | None] = []
    pass_times: list[datetime] = []
    for name in VALIDATION_PASS_NAMES:
        path = f"validation.passes.{name}"
        record = collector.object(_value(passes, name), VALIDATION_PASS_FIELDS, path)
        pass_status = collector.enum(
            _value(record, "status"), frozenset({"not_run", "passed", "failed", "not_applicable"}), f"{path}.status"
        )
        method = collector.text(_value(record, "method"), f"{path}.method", nullable=True)
        pass_reviewer = collector.text(_value(record, "reviewer"), f"{path}.reviewer", nullable=True)
        checked_at = _parse_timestamp(
            _value(record, "checked_at"), collector, f"{path}.checked_at", nullable=True
        )
        evidence = collector.text(_value(record, "evidence"), f"{path}.evidence", nullable=True)
        if pass_status in {"passed", "failed"} and any(
            item is None for item in (method, pass_reviewer, checked_at, evidence)
        ):
            collector.add(
                "missing_review_evidence",
                "completed review needs method, reviewer, time, and evidence",
                path,
            )
        if pass_status in {"not_run", "not_applicable"} and any(
            item is not None for item in (method, pass_reviewer, checked_at, evidence)
        ):
            collector.add(
                "stale_review_evidence",
                "an unexecuted review cannot retain review evidence",
                path,
            )
        if pass_status in {"passed", "failed"} and reviewer is not None and pass_reviewer != reviewer:
            collector.add("reviewer_mismatch", "every semantic pass must use the validation reviewer", f"{path}.reviewer")
        if checked_at is not None:
            pass_times.append(checked_at)
            if (
                workflow_profile != "format_regeneration"
                and revision_checked_at is not None
                and checked_at < revision_checked_at
            ):
                collector.add(
                    "review_precedes_revision",
                    "semantic review cannot predate the editorial revision",
                    f"{path}.checked_at",
                )
        pass_statuses.append(pass_status)
    if status == "passed":
        if reviewed != current_editorial_fingerprint:
            collector.add(
                "stale_semantic_review",
                "semantic review fingerprint must match the current editorial payload",
                "validation.reviewed_editorial_fingerprint",
            )
        if reviewer is None or any(item != "passed" for item in pass_statuses):
            collector.add(
                "semantic_gate_incomplete",
                "semantic status can pass only after all three reviews pass under one reviewer",
                "validation.semantic_status",
            )
    elif status == "failed":
        if reviewed != current_editorial_fingerprint or reviewer is None:
            collector.add(
                "stale_semantic_review",
                "failed validation must identify the exact editorial payload and reviewer",
                "validation.reviewed_editorial_fingerprint",
            )
        if "failed" not in pass_statuses:
            collector.add(
                "semantic_gate_incomplete",
                "failed semantic status requires at least one failed review pass",
                "validation.semantic_status",
            )
    else:
        if reviewed is not None or reviewer is not None or any(
            item != "not_run" for item in pass_statuses
        ):
            collector.add(
                "stale_semantic_review",
                "not-run validation cannot retain review results",
                "validation",
            )
    if purpose == "premiere_xml" and status != "passed":
        collector.add("semantic_gate_incomplete", "Premiere XML export requires passed semantic validation", "validation.semantic_status")
    return max(pass_times, default=None)


def _validate_delivery(value: Any, collector: _Collector, timeline_id: str | None) -> None:
    delivery = collector.object(value, DELIVERY_FIELDS, "delivery")
    artifact = collector.text(_value(delivery, "artifact_id"), "delivery.artifact_id")
    output = collector.text(_value(delivery, "output_path"), "delivery.output_path")
    profile = collector.enum(
        _value(delivery, "profile"), frozenset({"premiere-cs6-v4"}), "delivery.profile"
    )
    overwrite = collector.boolean(_value(delivery, "overwrite"), "delivery.overwrite")
    if artifact is not None and timeline_id is not None and artifact != timeline_id:
        collector.add("delivery_artifact_mismatch", "delivery artifact must identify this exact timeline", "delivery.artifact_id")
    if output is not None and Path(output).suffix.lower() != ".xml":
        collector.add("invalid_delivery_path", "delivery output must end in .xml", "delivery.output_path")
    if profile is not None and profile != "premiere-cs6-v4":
        collector.add("invalid_delivery_profile", "v2 delivery profile is fixed by the payload", "delivery.profile")
    if overwrite is not False:
        collector.add("overwrite_forbidden", "validated delivery never overwrites an existing artifact", "delivery.overwrite")


def _reference_fingerprints(
    value: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    profile = value.get("workflow_profile")
    evidence = value.get("editorial_evidence")
    feedback = evidence.get("feedback") if isinstance(evidence, Mapping) else None
    baseline = (
        feedback.get("baseline_payload_fingerprint")
        if isinstance(feedback, Mapping)
        and profile in {"approved_delta", "format_regeneration"}
        else None
    )
    approval = value.get("approval")
    calibration = (
        approval.get("calibration") if isinstance(approval, Mapping) else None
    )
    calibration_fingerprint = (
        calibration.get("approved_payload_fingerprint")
        if isinstance(calibration, Mapping)
        and profile in {"new_full_edit", "approved_delta"}
        and calibration.get("status") in {"approved", "not_required"}
        else None
    )
    return (
        calibration_fingerprint
        if isinstance(calibration_fingerprint, str)
        else None,
        baseline if isinstance(baseline, str) else None,
    )


def _reachable_reference_tasks(
    root: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> set[str]:
    used: set[str] = set()
    visited_payloads: set[str] = set()
    pending = [root]
    while pending:
        current = pending.pop()
        payload_key = payload_fingerprint(current)
        if payload_key in visited_payloads:
            continue
        visited_payloads.add(payload_key)
        for reference_key in _reference_fingerprints(current):
            if reference_key is None:
                continue
            reference = registry.get(reference_key)
            if reference is None:
                continue
            used.add(task_payload_fingerprint(reference))
            pending.append(reference)
    return used


def _build_reference_registry(
    values: Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    registry: dict[str, Mapping[str, Any]] = {}
    payload_states: dict[str, bytes] = {}
    indexed_states: dict[str, bytes] = {}
    issues: list[dict[str, str]] = []
    for index, value in enumerate(values):
        if not isinstance(value, Mapping):
            issues.append(
                {
                    "code": "invalid_reference_payload",
                    "message": "every reference payload must be a JSON object",
                    "path": f"references[{index}]",
                }
            )
            continue
        payload_key = payload_fingerprint(value)
        task_key = task_payload_fingerprint(value)
        rendered = _canonical(value)
        if (
            payload_key in payload_states
            and payload_states[payload_key] != rendered
        ):
            issues.append(
                {
                    "code": "ambiguous_reference_payload",
                    "message": (
                        "multiple different state objects claim the same task payload fingerprint"
                    ),
                    "path": f"references[{index}]",
                }
            )
            continue
        payload_states[payload_key] = rendered
        for fingerprint in {payload_key, task_key}:
            if (
                fingerprint in indexed_states
                and indexed_states[fingerprint] != rendered
            ):
                issues.append(
                    {
                        "code": "ambiguous_reference_payload",
                        "message": (
                            "one reference fingerprint resolves to different state objects"
                        ),
                        "path": f"references[{index}]",
                    }
                )
                continue
            indexed_states[fingerprint] = rendered
            registry[fingerprint] = value
    if issues:
        raise TimelineV2Error(issues)
    return registry


def validate_timeline_v2(
    value: Mapping[str, Any],
    *,
    purpose: str | None = None,
    calibration_reference: Mapping[str, Any] | None = None,
    baseline_reference: Mapping[str, Any] | None = None,
    reference_payloads: Iterable[Mapping[str, Any]] = (),
    _reference_registry: Mapping[str, Mapping[str, Any]] | None = None,
    _reference_stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    current_reference_fingerprint = payload_fingerprint(value)
    if current_reference_fingerprint in _reference_stack:
        raise TimelineV2Error(
            [
                {
                    "code": "reference_cycle",
                    "message": "timeline reference graph contains a cycle",
                    "path": "references",
                }
            ]
        )
    if _reference_registry is None:
        explicit_references = tuple(reference_payloads)
        supplied_references: list[tuple[str, Any]] = []
        if calibration_reference is not None:
            supplied_references.append(("calibration_reference", calibration_reference))
        if baseline_reference is not None:
            supplied_references.append(("baseline_reference", baseline_reference))
        supplied_references.extend(
            (f"reference_payloads[{index}]", reference)
            for index, reference in enumerate(explicit_references)
        )
        if len(supplied_references) > MAX_REFERENCE_PAYLOADS:
            raise TimelineV2Error(
                [
                    {
                        "code": "reference_bundle_too_large",
                        "message": (
                            "reference bundle exceeds the bounded validation limit "
                            f"of {MAX_REFERENCE_PAYLOADS} payloads"
                        ),
                        "path": "references",
                    }
                ]
            )
        invalid_references = [
            {
                "code": "invalid_reference_payload",
                "message": "every supplied reference must be an exact timeline v2 object",
                "path": path,
            }
            for path, reference in supplied_references
            if not isinstance(reference, Mapping)
            or set(reference) != TIMELINE_V2_FIELDS
            or reference.get("timeline_version") != TIMELINE_V2_VERSION
        ]
        if invalid_references:
            raise TimelineV2Error(invalid_references)
        candidates: list[Mapping[str, Any]] = [value]
        if calibration_reference is not None:
            candidates.append(calibration_reference)
        if baseline_reference is not None:
            candidates.append(baseline_reference)
        candidates.extend(explicit_references)
        registry = _build_reference_registry(candidates)
        reachable_tasks = _reachable_reference_tasks(value, registry)
        unreferenced = [
            {
                "code": "unreferenced_reference_payload",
                "message": "supplied reference is not consumed by the root reference graph",
                "path": path,
            }
            for path, reference in supplied_references
            if task_payload_fingerprint(reference) not in reachable_tasks
        ]
        if unreferenced:
            raise TimelineV2Error(unreferenced)
    else:
        registry = dict(_reference_registry)
    expected_calibration, expected_baseline = _reference_fingerprints(value)
    selected_calibration = (
        calibration_reference
        if calibration_reference is not None
        else registry.get(expected_calibration)
        if expected_calibration is not None
        else None
    )
    selected_baseline = (
        baseline_reference
        if baseline_reference is not None
        else registry.get(expected_baseline)
        if expected_baseline is not None
        else None
    )
    next_stack = (*_reference_stack, current_reference_fingerprint)
    normalized_calibration = (
        validate_timeline_v2(
            selected_calibration,
            purpose="premiere_xml",
            _reference_registry=registry,
            _reference_stack=next_stack,
        )
        if selected_calibration is not None
        else None
    )
    normalized_baseline = (
        validate_timeline_v2(
            selected_baseline,
            purpose="premiere_xml",
            _reference_registry=registry,
            _reference_stack=next_stack,
        )
        if selected_baseline is not None
        else None
    )
    collector = _Collector()
    timeline = collector.object(value, TIMELINE_V2_FIELDS, "timeline")
    if _value(timeline, "timeline_version") != TIMELINE_V2_VERSION:
        collector.add("invalid_v2_fields", "timeline_version must be 2", "timeline.timeline_version")
    timeline_id = collector.text(_value(timeline, "timeline_id"), "timeline.timeline_id", pattern=SLUG_PATTERN)
    workflow_profile = collector.enum(
        _value(timeline, "workflow_profile"), WORKFLOW_PROFILES, "timeline.workflow_profile"
    )
    source, sequence, video, audio = _validate_source_and_sequence(timeline, collector)
    evidence = collector.object(
        _value(timeline, "editorial_evidence"), EDITORIAL_EVIDENCE_FIELDS, "editorial_evidence"
    )
    total_frames = _value(source, "total_frames") if isinstance(_value(source, "total_frames"), int) else None
    timeline_total_frames = max(
        (
            clip.get("timeline_end", 0)
            for track in ("video_clips", "audio_clips")
            for clip in sequence.get(track, [])
            if isinstance(clip, Mapping)
        ),
        default=0,
    )
    frame_rate = _value(source, "frame_rate")
    _validate_time_references(
        _value(evidence, "time_references"),
        collector,
        source_total_frames=total_frames,
        timeline_total_frames=timeline_total_frames,
        frame_rate=frame_rate if isinstance(frame_rate, Mapping) else {},
    )
    event_owners, event_ranges, event_orders = _validate_events(
        _value(evidence, "events"),
        collector,
        total_frames=total_frames,
        video=video,
        audio=audio,
    )
    _validate_microbeats(
        _value(evidence, "microbeats"),
        collector,
        purpose=purpose,
        total_frames=total_frames,
        video=video,
        audio=audio,
        event_owners=event_owners,
        event_ranges=event_ranges,
        event_orders=event_orders,
    )
    revision_status, revision_supersedes, revision_checked_at = _validate_revision(
        _value(timeline, "revision"), collector, timeline_id, purpose
    )
    current_payload_fingerprint = payload_fingerprint(timeline)
    current_editorial_fingerprint = editorial_fingerprint(timeline)
    source_hash = source_manifest_fingerprint(source)
    review_completed_at = _validate_validation(
        _value(timeline, "validation"),
        collector,
        current_editorial_fingerprint=current_editorial_fingerprint,
        revision_checked_at=revision_checked_at,
        workflow_profile=workflow_profile,
        purpose=purpose,
    )
    all_clips = {**video, **audio}
    _validate_feedback(
        _value(evidence, "feedback"),
        collector,
        workflow_profile=workflow_profile,
        revision_status=revision_status,
        known_clips=all_clips,
        purpose=purpose,
        current_payload=timeline,
        current_source_hash=source_hash,
        revision_supersedes=revision_supersedes,
        revision_checked_at=revision_checked_at,
        baseline_reference=normalized_baseline,
    )
    _validate_approval(
        _value(timeline, "approval"),
        collector,
        workflow_profile=workflow_profile,
        revision_status=revision_status,
        timeline_id=timeline_id,
        source_hash=source_hash,
        current_payload_fingerprint=current_payload_fingerprint,
        current_editorial_fingerprint=current_editorial_fingerprint,
        current_review_completed_at=review_completed_at,
        validation_status=(
            _value(_value(timeline, "validation"), "semantic_status")
            if isinstance(_value(timeline, "validation"), Mapping)
            else None
        ),
        revision_checked_at=revision_checked_at,
        calibration_reference=normalized_calibration,
        purpose=purpose,
    )
    _validate_delivery(_value(timeline, "delivery"), collector, timeline_id)
    if collector.issues:
        raise TimelineV2Error(collector.issues)
    return deepcopy(dict(value))


def inspect_timeline_v2(
    value: Mapping[str, Any],
    *,
    purpose: str | None = None,
    calibration_reference: Mapping[str, Any] | None = None,
    baseline_reference: Mapping[str, Any] | None = None,
    reference_payloads: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    try:
        timeline = validate_timeline_v2(
            value,
            purpose=purpose,
            calibration_reference=calibration_reference,
            baseline_reference=baseline_reference,
            reference_payloads=reference_payloads,
        )
    except TimelineV2Error as exc:
        return {
            "ok": False,
            "errors": exc.issues,
            "payload_fingerprint": payload_fingerprint(value),
            "task_payload_fingerprint": task_payload_fingerprint(value),
            "editorial_fingerprint": editorial_fingerprint(value),
            "delivery_fingerprint": delivery_fingerprint(value),
        }
    return {
        "ok": True,
        "timeline_id": timeline["timeline_id"],
        "workflow_profile": timeline["workflow_profile"],
        "payload_fingerprint": payload_fingerprint(timeline),
        "task_payload_fingerprint": task_payload_fingerprint(timeline),
        "editorial_fingerprint": editorial_fingerprint(timeline),
        "delivery_fingerprint": delivery_fingerprint(timeline),
        "source_manifest_fingerprint": source_manifest_fingerprint(
            timeline["source_manifest"]
        ),
        "video_clips": len(timeline["sequence"]["video_clips"]),
        "audio_clips": len(timeline["sequence"]["audio_clips"]),
        "semantic_status": timeline["validation"]["semantic_status"],
    }


def as_legacy_timeline(
    value: Mapping[str, Any],
    *,
    calibration_reference: Mapping[str, Any] | None = None,
    baseline_reference: Mapping[str, Any] | None = None,
    reference_payloads: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    timeline = validate_timeline_v2(
        value,
        purpose="premiere_xml",
        calibration_reference=calibration_reference,
        baseline_reference=baseline_reference,
        reference_payloads=reference_payloads,
    )
    source = timeline["source_manifest"]
    return {
        "timeline_version": 1,
        "timeline_id": timeline["timeline_id"],
        "source": {
            key: deepcopy(source[key])
            for key in ("id", "path", "total_frames", "frame_rate", "video", "audio")
        },
        "sequence": deepcopy(timeline["sequence"]),
        "semantic_gate": {
            "status": "passed",
            "reviewed_by": timeline["validation"]["reviewer"],
            "notes": f"bound to {editorial_fingerprint(timeline)}",
        },
    }
