"""Structured command-line interface for the approved RecordStore entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .record import RecordValidationError, UnsafePathError
from .store import InputContractError, RecordIOError, RecordStore


class RecordArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InputContractError(message)


def _payload(value: str) -> dict[str, Any]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise InputContractError(f"payload is not valid JSON: {exc.msg}") from exc
    if not isinstance(decoded, dict):
        raise InputContractError("payload must be a JSON object")
    return decoded


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="strict", newline="\n")


def _parser() -> RecordArgumentParser:
    parser = RecordArgumentParser(prog="python -m file_data")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="existing project root")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="create approved data/records and data/events directories")

    create = commands.add_parser("create", help="create one approved neutral record")
    create.add_argument("--type", required=True, dest="record_type")
    create.add_argument("--payload-json", required=True, type=_payload)
    create.add_argument("--id", dest="record_id")

    get = commands.add_parser("get", help="read one record by UUID")
    get.add_argument("--id", required=True, dest="record_id")

    listing = commands.add_parser("list", help="list validated records of one approved type")
    listing.add_argument("--type", required=True, dest="record_type")

    update = commands.add_parser("update", help="replace payload when the expected content hash matches")
    update.add_argument("--id", required=True, dest="record_id")
    update.add_argument("--payload-json", required=True, type=_payload)
    update.add_argument("--expected-hash", required=True)

    append = commands.add_parser("append", help="append one event through an atomic JSONL rewrite")
    append.add_argument("--stream", required=True)
    append.add_argument("--payload-json", required=True, type=_payload)
    append.add_argument("--expected-stream-hash")
    append.add_argument("--id", dest="event_id")

    event_list = commands.add_parser("list-events", help="read and validate one approved JSONL stream")
    event_list.add_argument("--stream", required=True)
    return parser


def _run(namespace: argparse.Namespace) -> dict[str, Any]:
    store = RecordStore(namespace.root)
    if namespace.command == "init":
        return store.initialize()
    if namespace.command == "create":
        record = store.create_record(
            namespace.record_type,
            namespace.payload_json,
            record_id=namespace.record_id,
        )
        return {
            "record": record,
            "path": f"data/records/{record['id']}.json",
        }
    if namespace.command == "get":
        return {"record": store.get_record(namespace.record_id)}
    if namespace.command == "list":
        records = store.list_records(namespace.record_type)
        return {"records": records, "count": len(records)}
    if namespace.command == "update":
        record = store.update_record(
            namespace.record_id,
            namespace.payload_json,
            expected_content_hash=namespace.expected_hash,
        )
        return {"record": record}
    if namespace.command == "append":
        return store.append_event(
            namespace.stream,
            namespace.payload_json,
            expected_stream_hash=namespace.expected_stream_hash,
            event_id=namespace.event_id,
        )
    if namespace.command == "list-events":
        events, content_hash = store.list_events(namespace.stream)
        return {"events": events, "count": len(events), "stream_hash": content_hash}
    raise InputContractError(f"Unknown command: {namespace.command}")


def _error_payload(kind: str, message: str, recoverable: bool) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "kind": kind,
            "message": message,
            "recoverable": recoverable,
        },
    }


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    try:
        namespace = _parser().parse_args(argv)
        result = _run(namespace)
    except RecordIOError as exc:
        _emit(_error_payload(exc.kind, str(exc), exc.recoverable), error=True)
        return exc.exit_status
    except RecordValidationError as exc:
        _emit(_error_payload("validation_failure", f"{exc.code}: {exc}", False), error=True)
        return 5
    except UnsafePathError as exc:
        _emit(_error_payload("path_safety", str(exc), False), error=True)
        return 6
    except FileNotFoundError as exc:
        _emit(_error_payload("not_found", str(exc), False), error=True)
        return 3
    except OSError as exc:
        _emit(_error_payload("io_failure", str(exc), False), error=True)
        return 7
    except Exception as exc:
        _emit(_error_payload("internal_error", str(exc), False), error=True)
        return 8
    _emit({"ok": True, "result": result})
    return 0
