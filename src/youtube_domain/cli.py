from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from file_data import ContextError, ContextLimitError

from .service import YouTubeDomainError, YouTubeEvidenceService


class DomainArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise YouTubeDomainError(message)


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise YouTubeDomainError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, object_pairs_hook=_strict_object)
    except json.JSONDecodeError as exc:
        raise YouTubeDomainError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise YouTubeDomainError("request JSON must be an object")
    return value


def _parser() -> DomainArgumentParser:
    parser = DomainArgumentParser(prog="python -m youtube_domain")
    parser.add_argument("--root", default=".", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    evidence = commands.add_parser("evidence-pack", help="build one non-persistent YouTube evidence pack")
    source = evidence.add_mutually_exclusive_group(required=True)
    source.add_argument("--request-json")
    source.add_argument("--request-stdin", action="store_true")
    return parser


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    target = sys.stderr if error else sys.stdout
    target.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    try:
        namespace = _parser().parse_args(argv)
        raw = sys.stdin.read() if namespace.request_stdin else namespace.request_json
        request = _decode(raw)
        pack = YouTubeEvidenceService(namespace.root).build_pack(request)
        _emit({"ok": True, "result": {"pack": pack}})
        return 0
    except ContextLimitError as exc:
        _emit({"ok": False, "error": {"kind": "context_limit", "message": str(exc)}}, error=True)
        return 3
    except (YouTubeDomainError, ContextError) as exc:
        _emit({"ok": False, "error": {"kind": "input_error", "message": str(exc)}}, error=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
