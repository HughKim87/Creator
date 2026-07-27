from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .legacy_csv import LegacyCsvError, write_legacy_timeline
from .model import TimelineValidationError, inspect_timeline
from .premiere_xml import PremiereXmlError, write_premiere_xml
from .subtitle import SubtitleError, clean_srt, validate_srt


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


def _read_timeline(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
        )
    except OSError as exc:
        raise PremiereXmlError(f"cannot read timeline JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PremiereXmlError(f"invalid timeline JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise PremiereXmlError("timeline JSON must be an object")
    return value


def _parser() -> VideoEditingArgumentParser:
    parser = VideoEditingArgumentParser(prog="python -m video_editing")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one video-edit timeline")
    validate.add_argument("--timeline-json", required=True, type=Path)
    generate = commands.add_parser(
        "premiere-xml",
        help="write one Premiere-compatible XML from a valid timeline",
    )
    generate.add_argument("--timeline-json", required=True, type=Path)
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument("--overwrite", action="store_true")
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
        if namespace.command == "validate":
            timeline = _read_timeline(namespace.timeline_json)
            report = inspect_timeline(timeline)
            _emit(report, error=not report["ok"])
            return 0 if report["ok"] else 2
        if namespace.command == "premiere-xml":
            timeline = _read_timeline(namespace.timeline_json)
            result = write_premiere_xml(
                timeline,
                namespace.output,
                overwrite=namespace.overwrite,
            )
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
        LegacyCsvError,
        PremiereXmlError,
        SubtitleError,
        TimelineValidationError,
    ) as exc:
        if isinstance(exc, TimelineValidationError):
            kind = exc.code
            details = {"issues": exc.issues}
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
