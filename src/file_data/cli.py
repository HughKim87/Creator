"""Structured command-line interface for the approved RecordStore entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .record import RecordValidationError, UnsafePathError
from .store import InputContractError, RecordIOError, RecordStore
from .work_state import EVENT_OUTCOMES, WORK_STATUSES, WorkStateService
from .knowledge import (
    KNOWLEDGE_CLASSES,
    KNOWLEDGE_VERIFICATION_STATUSES,
    SOURCE_EVIDENCE_ROLES,
    SOURCE_KINDS,
    SOURCE_VERIFICATION_STATUSES,
    KnowledgeService,
)
from .lifecycle import APPROVAL_KINDS, LIFECYCLE_STATES, TARGET_TYPES, LifecycleService
from .context import ContextService


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


def _json_input(inline: dict[str, Any] | None, use_stdin: bool) -> dict[str, Any]:
    if use_stdin:
        return _payload(sys.stdin.read())
    if inline is None:
        raise InputContractError("one JSON input source is required")
    return inline


def _emit(value: dict[str, Any], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()


def _configure_utf8_stdio() -> None:
    reconfigure_input = getattr(sys.stdin, "reconfigure", None)
    if reconfigure_input is not None:
        reconfigure_input(encoding="utf-8", errors="strict")
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
    create_payload = create.add_mutually_exclusive_group(required=True)
    create_payload.add_argument("--payload-json", type=_payload)
    create_payload.add_argument("--payload-stdin", action="store_true")
    create.add_argument("--id", dest="record_id")

    get = commands.add_parser("get", help="read one record by UUID")
    get.add_argument("--id", required=True, dest="record_id")

    listing = commands.add_parser("list", help="list validated records of one approved type")
    listing.add_argument("--type", required=True, dest="record_type")

    update = commands.add_parser("update", help="replace payload when the expected content hash matches")
    update.add_argument("--id", required=True, dest="record_id")
    update_payload = update.add_mutually_exclusive_group(required=True)
    update_payload.add_argument("--payload-json", type=_payload)
    update_payload.add_argument("--payload-stdin", action="store_true")
    update.add_argument("--expected-hash", required=True)

    append = commands.add_parser("append", help="append one event through an atomic JSONL rewrite")
    append.add_argument("--stream", required=True)
    append_payload = append.add_mutually_exclusive_group(required=True)
    append_payload.add_argument("--payload-json", type=_payload)
    append_payload.add_argument("--payload-stdin", action="store_true")
    append.add_argument("--expected-stream-hash")
    append.add_argument("--id", dest="event_id")

    event_list = commands.add_parser("list-events", help="read and validate one approved JSONL stream")
    event_list.add_argument("--stream", required=True)

    work_create = commands.add_parser("work-create", help="append a work request and build its snapshot")
    work_request = work_create.add_mutually_exclusive_group(required=True)
    work_request.add_argument("--request-json", type=_payload)
    work_request.add_argument("--request-stdin", action="store_true")
    work_create.add_argument("--actor", required=True)
    work_create.add_argument("--next-action", required=True)
    work_create.add_argument("--id", dest="work_id")

    work_show = commands.add_parser("work-show", help="read one validated work snapshot")
    work_show.add_argument("--id", required=True, dest="work_id")

    work_transition = commands.add_parser("work-transition", help="append and project one work transition")
    work_transition.add_argument("--id", required=True, dest="work_id")
    work_transition.add_argument("--expected-hash", required=True)
    work_transition.add_argument("--actor", required=True)
    work_transition.add_argument("--action", required=True)
    work_transition.add_argument("--outcome", required=True, choices=sorted(EVENT_OUTCOMES))
    work_transition.add_argument("--to-status", choices=sorted(WORK_STATUSES))
    work_transition.add_argument("--completed-item", action="append", default=[])
    work_transition.add_argument("--blocker", action="append", default=[])
    work_transition.add_argument("--next-action")
    work_transition.add_argument("--related-id", action="append", default=[])
    work_transition.add_argument("--evidence", action="append", default=[])

    work_rebuild = commands.add_parser("work-rebuild", help="rebuild a work snapshot from canonical events")
    work_rebuild.add_argument("--id", required=True, dest="work_id")

    source_create = commands.add_parser("source-create", help="create one explicit source record")
    source_create.add_argument("--kind", required=True, choices=sorted(SOURCE_KINDS), dest="source_kind")
    source_create.add_argument("--locator", required=True)
    source_create.add_argument("--role", required=True, choices=sorted(SOURCE_EVIDENCE_ROLES), dest="evidence_role")
    source_create.add_argument("--verification-status", choices=sorted(SOURCE_VERIFICATION_STATUSES))
    source_create.add_argument("--version-or-hash")
    source_create.add_argument("--id", dest="record_id")

    source_show = commands.add_parser("source-show", help="read and verify one source record")
    source_show.add_argument("--id", required=True, dest="record_id")
    commands.add_parser("source-list", help="list and verify source records")
    source_verify = commands.add_parser("source-verify", help="verify one source locator and integrity")
    source_verify.add_argument("--id", required=True, dest="record_id")

    knowledge_create = commands.add_parser("knowledge-create", help="create one explicit knowledge claim")
    knowledge_create.add_argument("--statement", required=True)
    knowledge_create.add_argument("--classification", required=True, choices=sorted(KNOWLEDGE_CLASSES))
    knowledge_create.add_argument("--scope", required=True)
    knowledge_create.add_argument("--source-id", action="append", required=True, dest="source_ids")
    knowledge_create.add_argument(
        "--verification-status", required=True, choices=sorted(KNOWLEDGE_VERIFICATION_STATUSES)
    )
    knowledge_create.add_argument("--verified-by")
    knowledge_create.add_argument("--id", dest="record_id")
    knowledge_show = commands.add_parser("knowledge-show", help="read one validated knowledge claim")
    knowledge_show.add_argument("--id", required=True, dest="record_id")
    commands.add_parser("knowledge-list", help="list validated knowledge claims")

    decision_create = commands.add_parser("decision-create", help="create one explicit decision record")
    decision_input = decision_create.add_mutually_exclusive_group(required=True)
    decision_input.add_argument("--payload-json", type=_payload)
    decision_input.add_argument("--payload-stdin", action="store_true")
    decision_create.add_argument("--id", dest="record_id")
    decision_show = commands.add_parser("decision-show", help="read one validated decision record")
    decision_show.add_argument("--id", required=True, dest="record_id")
    commands.add_parser("decision-list", help="list validated decision records")

    failure_import = commands.add_parser("failure-import", help="project one resolved failure Markdown document")
    failure_import.add_argument("--doc", required=True, dest="canonical_doc_ref")
    failure_import.add_argument("--projected-by", required=True)
    failure_import.add_argument("--id", dest="record_id")
    failure_import.add_argument("--source-id")
    failure_show = commands.add_parser("failure-show", help="read one hash-verified failure projection")
    failure_show.add_argument("--id", required=True, dest="record_id")
    commands.add_parser("failure-list", help="list hash-verified failure projections")

    lifecycle_register = commands.add_parser("lifecycle-register", help="register one record lifecycle")
    lifecycle_register.add_argument("--id", required=True, dest="target_id")
    lifecycle_register.add_argument("--state", required=True, choices=["candidate", "current"])
    lifecycle_register.add_argument("--actor", required=True)
    lifecycle_register.add_argument("--approval-kind", required=True, choices=sorted(APPROVAL_KINDS))
    lifecycle_register.add_argument("--reason", required=True)
    lifecycle_register.add_argument("--source-id", action="append", default=[])
    lifecycle_register.add_argument("--decision-id")
    lifecycle_register_existing = commands.add_parser(
        "lifecycle-register-existing", help="register every unregistered Stage 05 knowledge record"
    )
    lifecycle_register_existing.add_argument("--actor", required=True)
    lifecycle_register_existing.add_argument(
        "--approval-kind", required=True, choices=["user", "standing_policy"]
    )
    lifecycle_show = commands.add_parser("lifecycle-show", help="show one lifecycle snapshot")
    lifecycle_show.add_argument("--id", required=True, dest="target_id")
    lifecycle_list = commands.add_parser("lifecycle-list", help="list lifecycle snapshots")
    lifecycle_list.add_argument("--state", choices=sorted(LIFECYCLE_STATES))
    lifecycle_list.add_argument("--type", choices=sorted(TARGET_TYPES), dest="target_type")
    lifecycle_current = commands.add_parser("lifecycle-current", help="list current base records")
    lifecycle_current.add_argument("--type", choices=sorted(TARGET_TYPES), dest="target_type")
    lifecycle_history = commands.add_parser("lifecycle-history", help="show append-only lifecycle events")
    lifecycle_history.add_argument("--id", required=True, dest="target_id")
    lifecycle_transition = commands.add_parser("lifecycle-transition", help="append one lifecycle transition")
    lifecycle_transition.add_argument("--id", required=True, dest="target_id")
    lifecycle_transition.add_argument("--expected-hash", required=True)
    lifecycle_transition.add_argument(
        "--action",
        required=True,
        choices=["request_review", "approve_current", "declare_conflict", "supersede", "reject", "retire"],
    )
    lifecycle_transition.add_argument("--actor", required=True)
    lifecycle_transition.add_argument("--approval-kind", required=True, choices=sorted(APPROVAL_KINDS))
    lifecycle_transition.add_argument("--reason", required=True)
    lifecycle_transition.add_argument("--source-id", action="append", default=[])
    lifecycle_transition.add_argument("--related-id", action="append", default=[])
    lifecycle_transition.add_argument("--replacement-id")
    lifecycle_transition.add_argument("--decision-id")
    lifecycle_rebuild = commands.add_parser("lifecycle-rebuild", help="rebuild one lifecycle snapshot")
    lifecycle_rebuild.add_argument("--id", required=True, dest="target_id")
    lifecycle_audit = commands.add_parser("lifecycle-audit", help="trigger reviews from current local drift")
    lifecycle_audit.add_argument("--actor", required=True)
    lifecycle_refresh = commands.add_parser(
        "lifecycle-refresh-failure", help="replace one stale failure projection without deleting history"
    )
    lifecycle_refresh.add_argument("--id", required=True, dest="target_id")
    lifecycle_refresh.add_argument("--actor", required=True)
    lifecycle_refresh.add_argument(
        "--approval-kind", required=True, choices=["user", "standing_policy"]
    )
    lifecycle_refresh.add_argument("--reason", required=True)

    context_build = commands.add_parser("context-build", help="build one non-persistent context package")
    context_request = context_build.add_mutually_exclusive_group(required=True)
    context_request.add_argument("--request-json", type=_payload)
    context_request.add_argument("--request-stdin", action="store_true")
    context_search = commands.add_parser("context-search", help="find current records by plain substring")
    context_search.add_argument("--text", required=True)
    context_search.add_argument("--type", choices=sorted(TARGET_TYPES), dest="record_type")
    context_search.add_argument("--scope")
    context_search.add_argument("--role", choices=sorted(SOURCE_EVIDENCE_ROLES), dest="evidence_role")
    context_filter = commands.add_parser("context-filter", help="filter lifecycle records by existing fields")
    context_filter.add_argument("--state", choices=sorted(LIFECYCLE_STATES))
    context_filter.add_argument("--type", choices=sorted(TARGET_TYPES), dest="record_type")
    context_filter.add_argument("--scope")
    context_filter.add_argument("--role", choices=sorted(SOURCE_EVIDENCE_ROLES), dest="evidence_role")
    context_baseline = commands.add_parser("context-baseline", help="measure exact active document refs")
    context_baseline.add_argument("--document", action="append", required=True, dest="documents")
    return parser


def _run(namespace: argparse.Namespace) -> dict[str, Any]:
    if namespace.command.startswith("context-"):
        context = ContextService(namespace.root)
        if namespace.command == "context-build":
            return {
                "package": context.build_package(
                    _json_input(namespace.request_json, namespace.request_stdin)
                )
            }
        filters = {
            key: value
            for key, value in {
                "record_type": getattr(namespace, "record_type", None),
                "state": getattr(namespace, "state", None),
                "scope": getattr(namespace, "scope", None),
                "evidence_role": getattr(namespace, "evidence_role", None),
            }.items()
            if value is not None
        }
        if namespace.command == "context-search":
            matches = context.search(namespace.text, filters)
            return {"matches": matches, "count": len(matches)}
        if namespace.command == "context-filter":
            records = context.filter_records(filters)
            return {"records": records, "count": len(records)}
        if namespace.command == "context-baseline":
            return context.measure_documents(namespace.documents)
        raise InputContractError(f"Unknown context command: {namespace.command}")
    if namespace.command.startswith("lifecycle-"):
        lifecycle = LifecycleService(namespace.root)
        if namespace.command == "lifecycle-register":
            return {
                "state": lifecycle.register(
                    namespace.target_id,
                    initial_state=namespace.state,
                    actor=namespace.actor,
                    approval_kind=namespace.approval_kind,
                    reason=namespace.reason,
                    source_ids=namespace.source_id,
                    decision_id=namespace.decision_id,
                )
            }
        if namespace.command == "lifecycle-register-existing":
            states = lifecycle.register_existing(
                actor=namespace.actor, approval_kind=namespace.approval_kind
            )
            return {"states": states, "count": len(states)}
        if namespace.command == "lifecycle-show":
            return lifecycle.get_record(namespace.target_id)
        if namespace.command == "lifecycle-list":
            states = lifecycle.list_states(state=namespace.state, target_type=namespace.target_type)
            return {"states": states, "count": len(states)}
        if namespace.command == "lifecycle-current":
            records = lifecycle.current_records(target_type=namespace.target_type)
            return {"records": records, "count": len(records)}
        if namespace.command == "lifecycle-history":
            events = lifecycle.history(namespace.target_id)
            return {"events": events, "count": len(events)}
        if namespace.command == "lifecycle-transition":
            return {
                "state": lifecycle.transition(
                    namespace.target_id,
                    expected_state_hash=namespace.expected_hash,
                    action=namespace.action,
                    actor=namespace.actor,
                    approval_kind=namespace.approval_kind,
                    reason=namespace.reason,
                    source_ids=namespace.source_id,
                    related_target_ids=namespace.related_id,
                    replacement_id=namespace.replacement_id,
                    decision_id=namespace.decision_id,
                )
            }
        if namespace.command == "lifecycle-rebuild":
            return {"state": lifecycle.rebuild_snapshot(namespace.target_id)}
        if namespace.command == "lifecycle-audit":
            findings = lifecycle.audit(actor=namespace.actor)
            return {"findings": findings, "count": len(findings)}
        if namespace.command == "lifecycle-refresh-failure":
            return lifecycle.refresh_failure_projection(
                namespace.target_id,
                actor=namespace.actor,
                approval_kind=namespace.approval_kind,
                reason=namespace.reason,
            )
        raise InputContractError(f"Unknown lifecycle command: {namespace.command}")
    if namespace.command.startswith("failure-"):
        knowledge = KnowledgeService(namespace.root)
        if namespace.command == "failure-import":
            return knowledge.import_failure_knowledge(
                namespace.canonical_doc_ref,
                projected_by=namespace.projected_by,
                record_id=namespace.record_id,
                source_id=namespace.source_id,
            )
        if namespace.command == "failure-show":
            return {"record": knowledge.get_failure_knowledge(namespace.record_id)}
        if namespace.command == "failure-list":
            records = knowledge.list_failure_knowledge()
            return {"records": records, "count": len(records)}
        raise InputContractError(f"Unknown failure command: {namespace.command}")
    if namespace.command.startswith("decision-"):
        knowledge = KnowledgeService(namespace.root)
        if namespace.command == "decision-create":
            record = knowledge.create_decision(
                _json_input(namespace.payload_json, namespace.payload_stdin),
                record_id=namespace.record_id,
            )
            return {"record": record, "path": f"data/records/{record['id']}.json"}
        if namespace.command == "decision-show":
            return {"record": knowledge.get_decision(namespace.record_id)}
        if namespace.command == "decision-list":
            records = knowledge.list_decisions()
            return {"records": records, "count": len(records)}
        raise InputContractError(f"Unknown decision command: {namespace.command}")
    if namespace.command.startswith("knowledge-"):
        knowledge = KnowledgeService(namespace.root)
        if namespace.command == "knowledge-create":
            record = knowledge.create_knowledge(
                statement=namespace.statement,
                classification=namespace.classification,
                scope=namespace.scope,
                source_ids=namespace.source_ids,
                verification_status=namespace.verification_status,
                verified_by=namespace.verified_by,
                record_id=namespace.record_id,
            )
            return {"record": record, "path": f"data/records/{record['id']}.json"}
        if namespace.command == "knowledge-show":
            return {"record": knowledge.get_knowledge(namespace.record_id)}
        if namespace.command == "knowledge-list":
            records = knowledge.list_knowledge()
            return {"records": records, "count": len(records)}
        raise InputContractError(f"Unknown knowledge command: {namespace.command}")
    if namespace.command.startswith("source-"):
        knowledge = KnowledgeService(namespace.root)
        if namespace.command == "source-create":
            record = knowledge.create_source(
                source_kind=namespace.source_kind,
                locator=namespace.locator,
                evidence_role=namespace.evidence_role,
                verification_status=namespace.verification_status,
                version_or_hash=namespace.version_or_hash,
                record_id=namespace.record_id,
            )
            return {"record": record, "path": f"data/records/{record['id']}.json"}
        if namespace.command == "source-show":
            return {"record": knowledge.get_source(namespace.record_id)}
        if namespace.command == "source-list":
            records = knowledge.list_sources()
            return {"records": records, "count": len(records)}
        if namespace.command == "source-verify":
            return knowledge.verify_source(namespace.record_id)
        raise InputContractError(f"Unknown source command: {namespace.command}")
    if namespace.command.startswith("work-"):
        work = WorkStateService(namespace.root)
        if namespace.command == "work-create":
            state = work.create_work(
                _json_input(namespace.request_json, namespace.request_stdin),
                actor=namespace.actor,
                next_action=namespace.next_action,
                work_id=namespace.work_id,
            )
            return {"state": state, "path": f"data/records/{state['id']}.json"}
        if namespace.command == "work-show":
            return {"state": work.get_state(namespace.work_id)}
        if namespace.command == "work-transition":
            state = work.transition(
                namespace.work_id,
                expected_state_hash=namespace.expected_hash,
                actor=namespace.actor,
                action=namespace.action,
                outcome=namespace.outcome,
                to_status=namespace.to_status,
                completed_items=namespace.completed_item,
                blockers=namespace.blocker,
                next_action=namespace.next_action,
                related_record_ids=namespace.related_id,
                evidence_refs=namespace.evidence,
            )
            return {"state": state}
        if namespace.command == "work-rebuild":
            return {"state": work.rebuild_snapshot(namespace.work_id)}
        raise InputContractError(f"Unknown work command: {namespace.command}")
    store = RecordStore(namespace.root)
    if namespace.command == "init":
        return store.initialize()
    if namespace.command == "create":
        record = store.create_record(
            namespace.record_type,
            _json_input(namespace.payload_json, namespace.payload_stdin),
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
            _json_input(namespace.payload_json, namespace.payload_stdin),
            expected_content_hash=namespace.expected_hash,
        )
        return {"record": record}
    if namespace.command == "append":
        return store.append_event(
            namespace.stream,
            _json_input(namespace.payload_json, namespace.payload_stdin),
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
