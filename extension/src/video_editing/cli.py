from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .model import TimelineValidationError, inspect_timeline
from .premiere_xml import PremiereXmlError, write_premiere_xml


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
    return parser


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    target = sys.stderr if error else sys.stdout
    target.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    try:
        namespace = _parser().parse_args(argv)
        timeline = _read_timeline(namespace.timeline_json)
        if namespace.command == "validate":
            report = inspect_timeline(timeline)
            _emit(report, error=not report["ok"])
            return 0 if report["ok"] else 2
        result = write_premiere_xml(
            timeline,
            namespace.output,
            overwrite=namespace.overwrite,
        )
        _emit({"ok": True, "result": result})
        return 0
    except (PremiereXmlError, TimelineValidationError) as exc:
        kind = exc.code if isinstance(exc, TimelineValidationError) else "xml_error"
        _emit({"ok": False, "error": {"kind": kind, "message": str(exc)}}, error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
