from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .edit_contract import fingerprint_source_manifest, validate_edit_contract
from .model import validate_timeline
from .timeline_v2 import TimelineV2Error, _parse_time_range, validate_timeline_v2


class TimelineMigrationError(ValueError):
    pass


def _normalized_time(raw: str, unit: str, numerator: int, denominator: int) -> int:
    try:
        start, end = _parse_time_range(
            raw,
            unit,
            {"numerator": numerator, "denominator": denominator},
        )
    except (KeyError, ValueError) as exc:
        raise TimelineMigrationError(
            f"legacy time reference requires canonical explicit time: {raw!r} ({unit})"
        ) from exc
    if start != end:
        raise TimelineMigrationError(
            "legacy migration accepts point references only; ranges require fresh v2 review"
        )
    return start


def _overlapping_ids(
    clips: list[Mapping[str, Any]], source_in: int, source_out: int
) -> list[str]:
    return [
        str(clip["id"])
        for clip in clips
        if clip["source_in"] < source_out and source_in < clip["source_out"]
    ]


def _split_clips_at_event_boundaries(
    clips: list[Mapping[str, Any]],
    events: list[Mapping[str, Any]],
    used_ids: set[str],
) -> list[dict[str, Any]]:
    """Split retained legacy clips so one clip can have exactly one event owner."""
    event_boundaries = sorted(
        {
            int(boundary)
            for event in events
            for boundary in (event["source_in"], event["source_out"])
        }
    )
    result: list[dict[str, Any]] = []
    for clip in clips:
        boundaries = [
            int(clip["source_in"]),
            *(
                boundary
                for boundary in event_boundaries
                if clip["source_in"] < boundary < clip["source_out"]
            ),
            int(clip["source_out"]),
        ]
        if len(boundaries) == 2:
            result.append(deepcopy(dict(clip)))
            continue
        for part, (source_in, source_out) in enumerate(
            zip(boundaries, boundaries[1:]), start=1
        ):
            base_id = f"{clip['id']}.m{part}"
            clip_id = base_id
            suffix = 1
            while clip_id in used_ids:
                suffix += 1
                clip_id = f"{base_id}.{suffix}"
            used_ids.add(clip_id)
            segment = deepcopy(dict(clip))
            segment["id"] = clip_id
            segment["source_in"] = source_in
            segment["source_out"] = source_out
            segment["frames"] = source_out - source_in
            segment["timeline_start"] = (
                int(clip["timeline_start"]) + source_in - int(clip["source_in"])
            )
            segment["timeline_end"] = segment["timeline_start"] + segment["frames"]
            segment["gap_before"] = int(clip["gap_before"]) if part == 1 else 0
            segment["edit_reason"] = (
                f"{clip['edit_reason']} Legacy migration split this retained clip "
                "at an event boundary; fresh v2 review is required."
            )
            result.append(segment)
    return result


def migrate_legacy_v1(
    timeline_value: Mapping[str, Any],
    contract_value: Mapping[str, Any],
    *,
    timeline_id: str,
    source_content_sha256: str,
    source_byte_size: int,
    delivery_output_path: str,
    checked_at: str,
) -> dict[str, Any]:
    timeline = validate_timeline(timeline_value)
    validate_edit_contract(
        contract_value,
        purpose=None,
        timeline_id=timeline["timeline_id"],
        expected_source_manifest_hash=fingerprint_source_manifest(timeline["source"]),
    )
    if any(
        clip["edit_role"] == "unclassified"
        for track in ("video_clips", "audio_clips")
        for clip in timeline["sequence"][track]
    ):
        raise TimelineMigrationError(
            "legacy unclassified clips require editorial classification before v2 migration"
        )
    frame_rate = timeline["source"]["frame_rate"]
    sequence = deepcopy(timeline["sequence"])
    used_clip_ids = {
        str(clip["id"])
        for track in ("video_clips", "audio_clips")
        for clip in sequence[track]
    }
    for track in ("video_clips", "audio_clips"):
        sequence[track] = _split_clips_at_event_boundaries(
            sequence[track],
            contract_value["events"],
            used_clip_ids,
        )
    time_references = []
    for reference in contract_value["time_references"]:
        frame = _normalized_time(
            reference["raw"],
            reference["unit"],
            frame_rate["numerator"],
            frame_rate["denominator"],
        )
        time_references.append(
            {
                "id": reference["id"],
                "raw": reference["raw"],
                "coordinate_system": reference["coordinate_system"],
                "unit": reference["unit"],
                "start_frame": frame,
                "end_frame": frame,
                "scope": reference["scope"],
                "confirmed_by": reference["confirmed_by"],
                "correction_evidence": "migrated from explicit legacy confirmation; re-review required",
            }
        )

    events = []
    for order, event in enumerate(contract_value["events"]):
        video_ids = _overlapping_ids(
            sequence["video_clips"], event["source_in"], event["source_out"]
        )
        if not video_ids:
            raise TimelineMigrationError(
                f"legacy event has no retained visual clip: {event['id']}"
            )
        events.append(
            {
                "id": event["id"],
                "role": event["role"],
                "video_clip_ids": video_ids,
                "audio_clip_ids": _overlapping_ids(
                    sequence["audio_clips"],
                    event["source_in"],
                    event["source_out"],
                ),
                "source_in": event["source_in"],
                "source_out": event["source_out"],
                "depends_on": deepcopy(event["depends_on"]),
                "timeline_order": order,
                "continuity_reason": event["continuity_reason"],
            }
        )

    microbeats = []
    clip_event_owners: dict[tuple[str, str], str] = {}
    for event in events:
        for clip_id in event["video_clip_ids"]:
            clip_event_owners[("video", clip_id)] = event["id"]
        for clip_id in event["audio_clip_ids"]:
            clip_event_owners[("audio", clip_id)] = event["id"]
    for track in ("video_clips", "audio_clips"):
        key = "video_clip_ids" if track == "video_clips" else "audio_clip_ids"
        other = "audio_clip_ids" if key == "video_clip_ids" else "video_clip_ids"
        media_scope = "video" if track == "video_clips" else "audio"
        for clip in sequence[track]:
            event_id = clip_event_owners.get((media_scope, clip["id"]))
            if event_id is None:
                raise TimelineMigrationError(
                    f"legacy retained clip has no exact event owner: {clip['id']}"
                )
            microbeats.append(
                {
                    "id": f"legacy-{clip['id']}",
                    "event_id": event_id,
                    "decision": "keep",
                    "media_scope": media_scope,
                    "purpose": "legacy retained clip; editorial purpose and boundary require re-review",
                    key: [clip["id"]],
                    other: [],
                    "source_in": clip["source_in"],
                    "source_out": clip["source_out"],
                    "boundary_review": "pending",
                }
            )
    event_order = {event["id"]: event["timeline_order"] for event in events}
    clip_timeline_start = {
        clip["id"]: clip["timeline_start"]
        for track in ("video_clips", "audio_clips")
        for clip in sequence[track]
    }
    microbeats.sort(
        key=lambda beat: (
            event_order[beat["event_id"]],
            min(
                clip_timeline_start[clip_id]
                for clip_id in beat["video_clip_ids"] + beat["audio_clip_ids"]
            ),
            0 if beat["media_scope"] == "video" else 1,
            beat["id"],
        )
    )

    def preservation(entry: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": entry["id"],
            "scope": "legacy scope requires exact clip review",
            "clip_ids": [],
            "evidence": "migrated legacy preservation flag; re-review required",
            "preserved": False,
        }

    defects = [
        {
            "id": item["id"],
            "scope": item["source_anchor"],
            "clip_ids": [],
            "status": "pending",
            "evidence": (
                f"legacy evidence: {item['evidence']}; "
                "migration reset requires fresh v2 review"
            ),
            "approved_by": None,
        }
        for item in contract_value["feedback"]["defects"]
    ]
    source_manifest = {
        **deepcopy(timeline["source"]),
        "content_sha256": source_content_sha256,
        "byte_size": source_byte_size,
    }
    migrated = {
        "timeline_version": 2,
        "timeline_id": timeline_id,
        "workflow_profile": "calibration",
        "source_manifest": source_manifest,
        "sequence": sequence,
        "editorial_evidence": {
            "time_references": time_references,
            "events": events,
            "microbeats": microbeats,
            "feedback": {
                "baseline_payload_fingerprint": None,
                "positive_locks": [
                    preservation(item)
                    for item in contract_value["feedback"]["positive_locks"]
                ],
                "defects": defects,
                "untouched": [
                    preservation(item)
                    for item in contract_value["feedback"]["untouched"]
                ],
            },
        },
        "revision": {
            "status": "working_candidate",
            "supersedes": timeline["timeline_id"],
            "checked_at": checked_at,
            "state_owner_id": timeline_id,
        },
        "approval": {
            "calibration": {
                "required": True,
                "status": "pending",
                "artifact_id": None,
                "approved_payload_fingerprint": None,
                "approved_by": None,
                "approval_evidence": None,
                "checked_at": None,
            },
            "decisions": [],
        },
        "validation": {
            "reviewed_editorial_fingerprint": None,
            "reviewer": None,
            "passes": {
                name: {
                    "status": "not_run",
                    "method": None,
                    "reviewer": None,
                    "checked_at": None,
                    "evidence": None,
                }
                for name in ("causal_space", "tempo_repetition", "av_boundary")
            },
            "semantic_status": "not_run",
        },
        "delivery": {
            "artifact_id": timeline_id,
            "output_path": delivery_output_path,
            "profile": "premiere-cs6-v4",
            "overwrite": False,
        },
    }
    try:
        validate_timeline_v2(migrated)
    except TimelineV2Error as exc:
        raise TimelineMigrationError(str(exc)) from exc
    return migrated


def write_migrated_v2(value: Mapping[str, Any], destination: Path | str) -> dict[str, Any]:
    target = Path(destination)
    if not target.parent.is_dir():
        raise TimelineMigrationError(f"destination directory does not exist: {target.parent}")
    rendered = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
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
            raise TimelineMigrationError(f"destination already exists: {target}") from exc
        except OSError as exc:
            raise TimelineMigrationError(
                "filesystem cannot provide atomic no-clobber migration output"
            ) from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return {"output": str(target), "bytes": len(rendered), "status": "pending"}
