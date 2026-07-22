"""Stage 04 work request, event replay, and current work snapshot."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from .record import RecordValidationError
from .store import (
    ExpectationMismatchError,
    InputContractError,
    RecordIOError,
    RecordNotFoundError,
    RecordStore,
)


WORK_RECORD_TYPES = frozenset({"example", "work_state"})
WORK_STREAMS = frozenset({"example_events", "work_events"})
WORK_STATUSES = frozenset({"requested", "in_progress", "completed", "failed", "blocked"})
EVENT_OUTCOMES = frozenset({"success", "failure", "blocked", "rejected"})
EXPECTED_OUTCOME_BY_STATUS = {
    "requested": "success",
    "in_progress": "success",
    "completed": "success",
    "failed": "failure",
    "blocked": "blocked",
}
ALLOWED_TRANSITIONS = {
    "requested": frozenset({"in_progress", "failed", "blocked"}),
    "in_progress": frozenset({"in_progress", "completed", "failed", "blocked"}),
    "failed": frozenset({"in_progress", "blocked"}),
    "blocked": frozenset({"in_progress", "failed"}),
    "completed": frozenset(),
}
REQUEST_FIELDS = frozenset(
    {
        "desired_outcome",
        "authorized_actions",
        "excluded_scope",
        "input_refs",
        "protection_boundaries",
        "required_decisions",
        "verification_levels",
    }
)
EVENT_FIELDS = frozenset(
    {
        "work_id",
        "actor",
        "action",
        "outcome",
        "from_status",
        "to_status",
        "request",
        "completed_items",
        "blockers",
        "next_action",
        "related_record_ids",
        "evidence_refs",
    }
)


class InvalidTransitionError(InputContractError):
    kind = "invalid_transition"


class ProjectionPendingError(RecordIOError):
    kind = "projection_pending"
    recoverable = True


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise InputContractError(f"{field} must be a list of non-empty strings")
    return list(value)


def _string_sequence(value: Any, field: str) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise InputContractError(f"{field} must be a sequence of non-empty strings")
    return _string_list(list(value), field)


def validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping) or set(request) != REQUEST_FIELDS:
        raise InputContractError(f"request must contain exactly: {sorted(REQUEST_FIELDS)}")
    desired = request["desired_outcome"]
    if not isinstance(desired, str) or not desired.strip():
        raise InputContractError("desired_outcome must be a non-empty string")
    normalized = {"desired_outcome": desired}
    for field in REQUEST_FIELDS - {"desired_outcome"}:
        normalized[field] = _string_list(request[field], field)
    return normalized


def _validate_work_id(work_id: str) -> None:
    try:
        parsed = UUID(work_id)
    except (ValueError, AttributeError) as exc:
        raise InputContractError("work_id must be a lowercase canonical UUIDv4") from exc
    if parsed.version != 4 or str(parsed) != work_id:
        raise InputContractError("work_id must be a lowercase canonical UUIDv4")


def _event_payload(
    *,
    work_id: str,
    actor: str,
    action: str,
    outcome: str,
    from_status: str | None,
    to_status: str | None,
    request: Mapping[str, Any] | None = None,
    completed_items: Sequence[str] = (),
    blockers: Sequence[str] = (),
    next_action: str | None = None,
    related_record_ids: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    _validate_work_id(work_id)
    if not isinstance(actor, str) or not actor.strip():
        raise InputContractError("actor must be a non-empty string")
    if not isinstance(action, str) or not action.strip():
        raise InputContractError("action must be a non-empty string")
    if outcome not in EVENT_OUTCOMES:
        raise InputContractError(f"unsupported event outcome: {outcome}")
    if from_status is not None and from_status not in WORK_STATUSES:
        raise InputContractError("invalid from_status")
    if to_status is not None and to_status not in WORK_STATUSES:
        raise InputContractError("invalid to_status")
    if next_action is not None and (not isinstance(next_action, str) or not next_action.strip()):
        raise InputContractError("next_action must be null or a non-empty string")
    normalized_completed = _string_sequence(completed_items, "completed_items")
    normalized_blockers = _string_sequence(blockers, "blockers")
    normalized_related = _string_sequence(related_record_ids, "related_record_ids")
    normalized_evidence = _string_sequence(evidence_refs, "evidence_refs")
    return {
        "work_id": work_id,
        "actor": actor,
        "action": action,
        "outcome": outcome,
        "from_status": from_status,
        "to_status": to_status,
        "request": dict(request) if request is not None else None,
        "completed_items": normalized_completed,
        "blockers": normalized_blockers,
        "next_action": next_action,
        "related_record_ids": normalized_related,
        "evidence_refs": normalized_evidence,
    }


def validate_event_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != EVENT_FIELDS:
        raise RecordValidationError(
            "work_event_payload",
            f"Work event payload must contain exactly: {sorted(EVENT_FIELDS)}",
        )
    try:
        request = payload["request"]
        normalized_request = None if request is None else validate_request(request)
        return _event_payload(
            work_id=payload["work_id"],
            actor=payload["actor"],
            action=payload["action"],
            outcome=payload["outcome"],
            from_status=payload["from_status"],
            to_status=payload["to_status"],
            request=normalized_request,
            completed_items=payload["completed_items"],
            blockers=payload["blockers"],
            next_action=payload["next_action"],
            related_record_ids=payload["related_record_ids"],
            evidence_refs=payload["evidence_refs"],
        )
    except (InputContractError, TypeError) as exc:
        raise RecordValidationError("work_event_payload", str(exc)) from exc


def project_work_state(events: Sequence[Mapping[str, Any]], work_id: str) -> dict[str, Any]:
    """Replay validated work events into one bounded current-state payload."""

    _validate_work_id(work_id)
    matching = [event for event in events if event["payload"].get("work_id") == work_id]
    if not matching:
        raise RecordNotFoundError(f"Work events not found: {work_id}")
    first = matching[0]
    payload = validate_event_payload(first["payload"])
    if payload.get("action") != "requested" or payload.get("from_status") is not None:
        raise RecordValidationError("work_event_order", "First work event must be requested from null.")
    if payload.get("to_status") != "requested" or payload.get("outcome") != "success":
        raise RecordValidationError("work_event_order", "Initial request event must succeed into requested.")
    if payload.get("next_action") is None:
        raise RecordValidationError("work_event_payload", "Initial request event must name a next action.")
    request = validate_request(payload.get("request"))
    state: dict[str, Any] = {
        "work_id": work_id,
        "request": request,
        "status": "requested",
        "completed_items": [],
        "blockers": [],
        "next_action": payload.get("next_action"),
        "related_record_ids": [],
        "evidence_refs": [],
        "last_event_id": first["id"],
    }
    for event in matching[1:]:
        item = validate_event_payload(event["payload"])
        if item.get("request") is not None:
            raise RecordValidationError("work_request_mutation", "Only the first event may contain request data.")
        if item.get("from_status") != state["status"]:
            raise RecordValidationError("work_event_order", "Event from_status does not match replay state.")
        target = item.get("to_status")
        if item.get("outcome") != "rejected":
            if target not in ALLOWED_TRANSITIONS[state["status"]]:
                raise RecordValidationError("invalid_transition", f"Invalid transition: {state['status']} -> {target}")
            if item["outcome"] != EXPECTED_OUTCOME_BY_STATUS[target]:
                raise RecordValidationError("work_event_outcome", "Outcome does not match target status.")
            state["status"] = target
        elif target is not None:
            raise RecordValidationError("rejected_transition", "Rejected events cannot change status.")
        else:
            state["last_event_id"] = event["id"]
            continue
        for field in ("completed_items", "related_record_ids", "evidence_refs"):
            for value in _string_list(item.get(field), field):
                if value not in state[field]:
                    state[field].append(value)
        state["blockers"] = _string_list(item.get("blockers"), "blockers")
        state["next_action"] = item.get("next_action")
        state["last_event_id"] = event["id"]
    if state["status"] == "blocked" and not state["blockers"]:
        raise RecordValidationError("missing_blocker", "Blocked work must name at least one blocker.")
    if state["status"] == "completed" and state["next_action"] is not None:
        raise RecordValidationError("completed_next_action", "Completed work cannot keep a next action.")
    return state


class WorkStateService:
    def __init__(self, project_root: str) -> None:
        self.store = RecordStore(
            project_root,
            approved_record_types=WORK_RECORD_TYPES,
            approved_streams=WORK_STREAMS,
        )

    def initialize(self) -> dict[str, str]:
        return self.store.initialize()

    def _events(self) -> tuple[list[dict[str, Any]], str]:
        return self.store.list_events("work_events")

    def create_work(
        self,
        request: Mapping[str, Any],
        *,
        actor: str,
        next_action: str,
        work_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        normalized = validate_request(request)
        identifier = work_id or str(uuid4())
        _validate_work_id(identifier)
        events, stream_hash = self._events()
        if any(event["payload"].get("work_id") == identifier for event in events):
            raise ExpectationMismatchError(f"Work already exists: {identifier}")
        event = self.store.append_event(
            "work_events",
            _event_payload(
                work_id=identifier,
                actor=actor,
                action="requested",
                outcome="success",
                from_status=None,
                to_status="requested",
                request=normalized,
                next_action=next_action,
            ),
            expected_stream_hash=stream_hash,
            timestamp=timestamp,
        )
        try:
            return self.rebuild_snapshot(identifier, expected_last_event_id=event["event"]["id"])
        except Exception as exc:
            raise ProjectionPendingError(
                f"Work request event was committed but snapshot rebuild is pending: {identifier}"
            ) from exc

    def get_state(self, work_id: str) -> dict[str, Any]:
        _validate_work_id(work_id)
        return self.store.get_record(work_id)

    def transition(
        self,
        work_id: str,
        *,
        expected_state_hash: str,
        actor: str,
        to_status: str | None,
        outcome: str,
        action: str,
        completed_items: Sequence[str] = (),
        blockers: Sequence[str] = (),
        next_action: str | None = None,
        related_record_ids: Sequence[str] = (),
        evidence_refs: Sequence[str] = (),
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        current = self.get_state(work_id)
        if current["content_hash"] != expected_state_hash:
            raise ExpectationMismatchError("Current work state hash differs from the expected value.")
        event_timestamp = timestamp or datetime.now(UTC)
        if event_timestamp.tzinfo is None or event_timestamp.utcoffset() is None:
            raise InputContractError("timestamp must be timezone-aware")
        current_time = datetime.strptime(current["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        if event_timestamp.astimezone(UTC).replace(microsecond=0) < current_time:
            raise InvalidTransitionError("Work event timestamp cannot precede the current state timestamp.")
        status = current["payload"]["status"]
        if outcome != "rejected" and to_status not in ALLOWED_TRANSITIONS[status]:
            raise InvalidTransitionError(f"Invalid transition: {status} -> {to_status}")
        if outcome != "rejected" and outcome != EXPECTED_OUTCOME_BY_STATUS[to_status]:
            raise InvalidTransitionError("Outcome does not match target status.")
        if outcome == "rejected" and to_status is not None:
            raise InvalidTransitionError("Rejected event cannot change status.")
        if to_status == "blocked" and not blockers:
            raise InvalidTransitionError("Blocked work must name at least one blocker.")
        if to_status == "completed" and next_action is not None:
            raise InvalidTransitionError("Completed work cannot keep a next action.")
        events, stream_hash = self._events()
        appended = self.store.append_event(
            "work_events",
            _event_payload(
                work_id=work_id,
                actor=actor,
                action=action,
                outcome=outcome,
                from_status=status,
                to_status=to_status,
                completed_items=completed_items,
                blockers=blockers,
                next_action=next_action,
                related_record_ids=related_record_ids,
                evidence_refs=evidence_refs,
            ),
            expected_stream_hash=stream_hash,
            timestamp=event_timestamp,
        )
        try:
            return self.rebuild_snapshot(work_id, expected_last_event_id=appended["event"]["id"])
        except Exception as exc:
            raise ProjectionPendingError(
                f"Work transition event was committed but snapshot rebuild is pending: {work_id}"
            ) from exc

    def rebuild_snapshot(self, work_id: str, *, expected_last_event_id: str | None = None) -> dict[str, Any]:
        events, _ = self._events()
        state_payload = project_work_state(events, work_id)
        if expected_last_event_id is not None and state_payload["last_event_id"] != expected_last_event_id:
            raise ProjectionPendingError("A newer work event appeared before snapshot rebuild.")
        try:
            current = self.store.get_record(work_id)
        except RecordNotFoundError:
            created = next(event["created_at"] for event in events if event["payload"].get("work_id") == work_id)
            timestamp = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            return self.store.create_record(
                "work_state",
                state_payload,
                record_id=work_id,
                timestamp=timestamp,
            )
        last_created = next(
            event["created_at"] for event in reversed(events) if event["payload"].get("work_id") == work_id
        )
        updated_at = datetime.strptime(last_created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        return self.store.update_record(
            work_id,
            state_payload,
            expected_content_hash=current["content_hash"],
            timestamp=updated_at,
        )
