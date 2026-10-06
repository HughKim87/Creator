from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .edit_contract import (
    EditContractError,
)
from .legacy_csv import LegacyCsvError, write_legacy_timeline
from .model import TimelineValidationError, inspect_timeline
from .migration import TimelineMigrationError, migrate_legacy_v1, write_migrated_v2
from .editorial_state import derive_omissions, validate_editorial_state, record_editorial_feedback, editorial_state_fingerprint
from .delivery import write_validated_premiere_xml, write_review_premiere_xml
from .premiere_xml import (
    PREMIERE_CS6_V4_PROFILE,
    PremiereXmlError,
)
from .subtitle import SubtitleError, clean_srt, validate_srt
from .timeline_v2 import TimelineV2Error, inspect_timeline_v2


class VideoEditingArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PremiereXmlError(message)


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PremiereXmlError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
        )
    except OSError as exc:
        raise PremiereXmlError(f"cannot read {label} JSON: {path}") from exc
    except UnicodeError as exc:
        raise PremiereXmlError(f"{label} JSON must be valid UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PremiereXmlError(f"invalid {label} JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise PremiereXmlError(f"{label} JSON must be an object")
    return value


def _parser() -> VideoEditingArgumentParser:
    parser = VideoEditingArgumentParser(prog="python -m video_editing")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one video-edit timeline")
    validate.add_argument("--timeline-json", required=True, type=Path)
    validate.add_argument("--calibration-timeline-json", type=Path)
    validate.add_argument("--baseline-timeline-json", type=Path)
    validate.add_argument("--reference-timeline-json", action="append", default=[], type=Path)
    generate = commands.add_parser(
        "premiere-xml",
        help="write one Premiere-compatible XML from a valid timeline",
    )
    generate.add_argument("--timeline-json", required=True, type=Path)
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument("--calibration-timeline-json", type=Path)
    generate.add_argument("--baseline-timeline-json", type=Path)
    generate.add_argument("--reference-timeline-json", action="append", default=[], type=Path)
    generate.add_argument(
        "--profile",
        choices=[PREMIERE_CS6_V4_PROFILE],
    )
    review = commands.add_parser("premiere-review-xml", help="write a preflight-checked candidate awaiting user playback")
    review.add_argument("--timeline-json", required=True, type=Path)
    review.add_argument("--preflight-json", required=True, type=Path)
    review.add_argument("--output", required=True, type=Path)
    review.add_argument("--profile", choices=[PREMIERE_CS6_V4_PROFILE])
    review.add_argument("--calibration-timeline-json", type=Path)
    review.add_argument("--baseline-timeline-json", type=Path)
    review.add_argument("--reference-timeline-json", action="append", default=[], type=Path)
    for command in (generate, review):
        command.add_argument("--editorial-state-json", type=Path, help="required for XML delivery")
    editorial = commands.add_parser("editorial-check", help="inspect scene anchors, omissions and feedback without reading media")
    editorial.add_argument("--timeline-json", required=True, type=Path)
    editorial.add_argument("--editorial-state-json", required=True, type=Path)
    feedback = commands.add_parser("record-feedback", help="write a new editorial state with old reviews invalidated")
    feedback.add_argument("--timeline-json", required=True, type=Path)
    feedback.add_argument("--editorial-state-json", required=True, type=Path)
    feedback.add_argument("--feedback-id", required=True)
    feedback.add_argument("--symptom", required=True)
    feedback.add_argument("--reported-by", required=True)
    feedback.add_argument("--required-anchor-id", action="append", default=[])
    feedback.add_argument("--output", required=True, type=Path)
    rule_gate = commands.add_parser(
        "rule-gate",
        help="validate the editorial decision contract before XML generation",
    )
    rule_gate.add_argument("--edit-contract-json", type=Path)
    rule_gate.add_argument("--timeline-json", required=True, type=Path)
    rule_gate.add_argument("--calibration-timeline-json", type=Path)
    rule_gate.add_argument("--baseline-timeline-json", type=Path)
    rule_gate.add_argument("--reference-timeline-json", action="append", default=[], type=Path)
    rule_gate.add_argument(
        "--purpose",
        choices=["premiere_xml"],
        default="premiere_xml",
    )
    subtitle_validate = commands.add_parser(
        "subtitle-validate",
        help="validate one strict UTF-8 SRT without changing it",
    )
    subtitle_validate.add_argument("--source", required=True, type=Path)
    subtitle_validate.add_argument("--media-end-ms", type=int)
    subtitle_clean = commands.add_parser(
        "subtitle-clean",
        help="apply only explicit timing overrides and exclusions to a new SRT",
    )
    subtitle_clean.add_argument("--source", required=True, type=Path)
    subtitle_clean.add_argument("--destination", required=True, type=Path)
    subtitle_clean.add_argument("--media-end-ms", required=True, type=int)
    subtitle_clean.add_argument("--start", action="append", default=[], metavar="CUE=MS")
    subtitle_clean.add_argument("--end", action="append", default=[], metavar="CUE=MS")
    subtitle_clean.add_argument("--exclude", action="append", default=[], type=int)
    subtitle_clean.add_argument("--overwrite", action="store_true")
    import_csv = commands.add_parser(
        "import-csv",
        help="convert validated legacy video/audio cut CSV files to a pending timeline",
    )
    import_csv.add_argument("--video-csv", required=True, type=Path)
    import_csv.add_argument("--audio-csv", required=True, type=Path)
    import_csv.add_argument("--output", required=True, type=Path)
    import_csv.add_argument("--timeline-id", required=True)
    import_csv.add_argument("--sequence-name", required=True)
    import_csv.add_argument("--source-id", required=True)
    import_csv.add_argument("--source-path", required=True)
    import_csv.add_argument("--source-total-frames", required=True, type=int)
    import_csv.add_argument("--frame-rate-numerator", required=True, type=int)
    import_csv.add_argument("--frame-rate-denominator", required=True, type=int)
    import_csv.add_argument("--width", required=True, type=int)
    import_csv.add_argument("--height", required=True, type=int)
    import_csv.add_argument("--sample-rate", required=True, type=int)
    import_csv.add_argument("--channels", required=True, type=int)
    import_csv.add_argument(
        "--source-order-exception",
        action="append",
        default=[],
        metavar="CLIP_ID",
    )
    migrate = commands.add_parser(
        "migrate-v1",
        help="convert an explicit legacy timeline and contract to a pending v2 task payload",
    )
    migrate.add_argument("--timeline-json", required=True, type=Path)
    migrate.add_argument("--edit-contract-json", required=True, type=Path)
    migrate.add_argument("--output", required=True, type=Path)
    migrate.add_argument("--timeline-id", required=True)
    migrate.add_argument("--source-content-sha256", required=True)
    migrate.add_argument("--source-byte-size", required=True, type=int)
    migrate.add_argument("--delivery-output-path", required=True)
    migrate.add_argument("--checked-at", required=True)
    return parser


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    target = sys.stderr if error else sys.stdout
    target.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def _cue_values(
    starts: list[str],
    ends: list[str],
) -> dict[int, dict[str, int]]:
    overrides: dict[int, dict[str, int]] = {}
    for field, values in (("start_ms", starts), ("end_ms", ends)):
        for raw in values:
            cue_text, separator, value_text = raw.partition("=")
            if (
                separator != "="
                or not cue_text.isdigit()
                or not value_text.isdigit()
                or int(cue_text) < 1
            ):
                raise SubtitleError(
                    f"{field} override must use CUE=MS with non-negative integers: {raw}"
                )
            cue = int(cue_text)
            if field in overrides.setdefault(cue, {}):
                raise SubtitleError(f"duplicate {field} override for cue {cue}")
            overrides[cue][field] = int(value_text)
    return overrides


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    try:
        namespace = _parser().parse_args(argv)
        if namespace.command in {"editorial-check", "record-feedback"}:
            timeline = _read_json_object(namespace.timeline_json, "timeline")
            from .timeline_v2 import validate_timeline_v2
            timeline = validate_timeline_v2(timeline)
            state = _read_json_object(namespace.editorial_state_json, "editorial state")
            if namespace.command == "editorial-check":
                omissions = derive_omissions(timeline, state)
                try:
                    result = validate_editorial_state(timeline, state)
                except PremiereXmlError as exc:
                    _emit({"ok": False, "error": {"kind": "editorial_state_error", "message": str(exc)}, "omissions": omissions}, error=True)
                    return 2
                _emit({"ok": True, "result": result, "omissions": omissions})
            else:
                state = record_editorial_feedback(timeline, state, feedback_id=namespace.feedback_id, symptom=namespace.symptom, reported_by=namespace.reported_by, required_anchor_ids=namespace.required_anchor_id)
                target = namespace.output
                if target.suffix.lower() != ".json" or not target.is_absolute():
                    raise PremiereXmlError("feedback output must be an absolute new JSON path")
                from .delivery import _write_no_clobber
                _write_no_clobber(target, json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8"))
                _emit({"ok": True, "result": {"editorial_state": str(target), "generation": state["generation"], "editorial_state_fingerprint": editorial_state_fingerprint(state), "review_status": "invalidated", "owner_action": "Use this latest state for subsequent delivery and handoff."}})
            return 0
        if namespace.command == "validate":
            timeline = _read_json_object(namespace.timeline_json, "timeline")
            if timeline.get("timeline_version") == 2:
                calibration_reference = (
                    _read_json_object(
                        namespace.calibration_timeline_json, "calibration timeline"
                    )
                    if namespace.calibration_timeline_json is not None
                    else None
                )
                baseline_reference = (
                    _read_json_object(
                        namespace.baseline_timeline_json, "baseline timeline"
                    )
                    if namespace.baseline_timeline_json is not None
                    else None
                )
                reference_payloads = tuple(
                    _read_json_object(path, "reference timeline")
                    for path in namespace.reference_timeline_json
                )
                report = inspect_timeline_v2(
                    timeline,
                    calibration_reference=calibration_reference,
                    baseline_reference=baseline_reference,
                    reference_payloads=reference_payloads,
                )
            else:
                report = inspect_timeline(timeline)
            _emit(report, error=not report["ok"])
            return 0 if report["ok"] else 2
        if namespace.command == "rule-gate":
            timeline = _read_json_object(namespace.timeline_json, "timeline")
            if timeline.get("timeline_version") == 2:
                if namespace.edit_contract_json is not None:
                    raise PremiereXmlError(
                        "timeline v2 is the single rule-gate payload; do not pass a v1 contract"
                    )
                calibration_reference = (
                    _read_json_object(
                        namespace.calibration_timeline_json, "calibration timeline"
                    )
                    if namespace.calibration_timeline_json is not None
                    else None
                )
                baseline_reference = (
                    _read_json_object(
                        namespace.baseline_timeline_json, "baseline timeline"
                    )
                    if namespace.baseline_timeline_json is not None
                    else None
                )
                reference_payloads = tuple(
                    _read_json_object(path, "reference timeline")
                    for path in namespace.reference_timeline_json
                )
                report = inspect_timeline_v2(
                    timeline,
                    purpose=namespace.purpose,
                    calibration_reference=calibration_reference,
                    baseline_reference=baseline_reference,
                    reference_payloads=reference_payloads,
                )
            else:
                raise PremiereXmlError(
                    "legacy timeline v1 cannot pass an XML rule gate; migrate it with migrate-v1 and perform fresh v2 review"
                )
            _emit(report, error=not report["ok"])
            return 0 if report["ok"] else 2
        if namespace.command in {"premiere-xml", "premiere-review-xml"}:
            timeline = _read_json_object(namespace.timeline_json, "timeline")
            if timeline.get("timeline_version") == 2:
                calibration_reference = (
                    _read_json_object(
                        namespace.calibration_timeline_json, "calibration timeline"
                    )
                    if namespace.calibration_timeline_json is not None
                    else None
                )
                baseline_reference = (
                    _read_json_object(
                        namespace.baseline_timeline_json, "baseline timeline"
                    )
                    if namespace.baseline_timeline_json is not None
                    else None
                )
                reference_payloads = tuple(
                    _read_json_object(path, "reference timeline")
                    for path in namespace.reference_timeline_json
                )
                delivery = timeline.get("delivery")
                declared_profile = (
                    delivery.get("profile") if isinstance(delivery, dict) else None
                )
                profile = namespace.profile or declared_profile
                input_paths = [namespace.timeline_json]
                if namespace.calibration_timeline_json is not None:
                    input_paths.append(namespace.calibration_timeline_json)
                if namespace.baseline_timeline_json is not None:
                    input_paths.append(namespace.baseline_timeline_json)
                input_paths.extend(namespace.reference_timeline_json)
                writer = write_validated_premiere_xml
                if namespace.editorial_state_json is None:
                    raise PremiereXmlError("XML delivery requires --editorial-state-json from the latest task owner")
                review_args = {"editorial_state": _read_json_object(namespace.editorial_state_json, "editorial state")}
                input_paths.append(namespace.editorial_state_json)
                if namespace.command == "premiere-review-xml":
                    writer = write_review_premiere_xml
                    review_args["preflight"] = _read_json_object(namespace.preflight_json, "review preflight")
                    input_paths.append(namespace.preflight_json)
                result = writer(
                    timeline,
                    namespace.output,
                    profile=profile,
                    **review_args,
                    input_paths=input_paths,
                    calibration_reference=calibration_reference,
                    baseline_reference=baseline_reference,
                    reference_payloads=reference_payloads,
                )
            else:
                raise PremiereXmlError(
                    "legacy timeline v1 cannot be delivered; migrate it with migrate-v1 and perform fresh v2 review"
                )
        elif namespace.command == "migrate-v1":
            legacy_timeline = _read_json_object(namespace.timeline_json, "timeline")
            legacy_contract = _read_json_object(
                namespace.edit_contract_json, "edit contract"
            )
            migrated = migrate_legacy_v1(
                legacy_timeline,
                legacy_contract,
                timeline_id=namespace.timeline_id,
                source_content_sha256=namespace.source_content_sha256,
                source_byte_size=namespace.source_byte_size,
                delivery_output_path=namespace.delivery_output_path,
                checked_at=namespace.checked_at,
            )
            result = write_migrated_v2(migrated, namespace.output)
        elif namespace.command == "subtitle-validate":
            result = validate_srt(
                namespace.source,
                media_end_ms=namespace.media_end_ms,
            )
        elif namespace.command == "subtitle-clean":
            result = clean_srt(
                namespace.source,
                namespace.destination,
                media_end_ms=namespace.media_end_ms,
                timestamp_overrides=_cue_values(namespace.start, namespace.end),
                excluded_indices=frozenset(namespace.exclude),
                overwrite=namespace.overwrite,
            )
        else:
            result = write_legacy_timeline(
                namespace.video_csv,
                namespace.audio_csv,
                namespace.output,
                timeline_id=namespace.timeline_id,
                sequence_name=namespace.sequence_name,
                source_id=namespace.source_id,
                source_path=namespace.source_path,
                source_total_frames=namespace.source_total_frames,
                frame_rate_numerator=namespace.frame_rate_numerator,
                frame_rate_denominator=namespace.frame_rate_denominator,
                width=namespace.width,
                height=namespace.height,
                sample_rate=namespace.sample_rate,
                channels=namespace.channels,
                source_order_exceptions=frozenset(namespace.source_order_exception),
            )
        _emit({"ok": True, "result": result})
        return 0
    except (
        EditContractError,
        LegacyCsvError,
        PremiereXmlError,
        SubtitleError,
        TimelineValidationError,
        TimelineV2Error,
        TimelineMigrationError,
    ) as exc:
        if isinstance(exc, EditContractError):
            kind = exc.code
            details = {"issues": exc.issues}
        elif isinstance(exc, TimelineValidationError):
            kind = exc.code
            details = {"issues": exc.issues}
        elif isinstance(exc, TimelineV2Error):
            kind = exc.code
            details = {"issues": exc.issues}
        elif isinstance(exc, TimelineMigrationError):
            kind = "timeline_migration_error"
            details = {}
        elif isinstance(exc, LegacyCsvError):
            kind = "legacy_csv_error"
            details = {"issues": exc.issues}
        elif isinstance(exc, SubtitleError):
            kind = "subtitle_error"
            details = {}
        else:
            kind = "xml_error"
            details = {}
        _emit(
            {
                "ok": False,
                "error": {"kind": kind, "message": str(exc), **details},
            },
            error=True,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
