from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4

from .knowledge import (
    KNOWLEDGE_RECORD_TYPES,
    KnowledgeService,
    SourceIntegrityError,
)
from .store import ExpectationMismatchError, InputContractError, RecordStore


LIFECYCLE_RECORD_TYPES = frozenset(KNOWLEDGE_RECORD_TYPES | {"lifecycle_state"})
LIFECYCLE_STREAMS = frozenset({"example_events", "work_events", "lifecycle_events"})
TARGET_TYPES = frozenset({"source", "knowledge", "decision", "failure_knowledge"})
LIFECYCLE_STATES = frozenset(
    {"candidate", "current", "review_required", "superseded", "rejected", "retired"}
)
TERMINAL_STATES = frozenset({"superseded", "rejected", "retired"})
APPROVAL_KINDS = frozenset({"agent_in_scope", "user", "standing_policy"})
CURRENT_APPROVAL_KINDS = frozenset({"user", "standing_policy"})
ACTIONS = frozenset(
    {"register", "request_review", "approve_current", "declare_conflict", "supersede", "reject", "retire"}
)
EVENT_FIELDS = frozenset(
    {
        "target_id",
        "target_type",
        "actor",
        "action",
        "from_state",
        "to_state",
        "reason",
        "approval_kind",
        "source_ids",
        "related_target_ids",
        "replacement_id",
        "decision_id",
    }
)
STATE_FIELDS = frozenset(
    {
        "target_id",
        "target_type",
        "state",
        "revision",
        "last_event_id",
        "conflict_ids",
        "superseded_by",
        "last_reason",
        "last_actor",
        "last_approval_kind",
        "last_source_ids",
        "last_decision_id",
    }
)


class LifecycleError(InputContractError):
    pass


class InvalidLifecycleTransition(LifecycleError):
    pass


class LifecycleProjectionPending(LifecycleError):
    pass


def _non_empty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LifecycleError(f"{field} must be a non-empty string")
    return value.strip()


def _uuid(value: Any, field: str) -> str:
    rendered = _non_empty(value, field)
    try:
        parsed = UUID(rendered)
    except (ValueError, AttributeError) as exc:
        raise LifecycleError(f"{field} must be a UUID") from exc
    if parsed.version != 4 or str(parsed) != rendered:
        raise LifecycleError(f"{field} must be a lowercase UUIDv4")
    return rendered


def _uuid_list(values: Any, field: str) -> list[str]:
    if not isinstance(values, list):
        raise LifecycleError(f"{field} must be a list")
    normalized = [_uuid(value, field) for value in values]
    if len(normalized) != len(set(normalized)):
        raise LifecycleError(f"{field} must not contain duplicates")
    return normalized


def _optional_uuid(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _uuid(value, field)


def _choice(value: Any, allowed: frozenset[str], field: str) -> str:
    rendered = _non_empty(value, field)
    if rendered not in allowed:
        raise LifecycleError(f"{field} must be one of: {sorted(allowed)}")
    return rendered


def validate_lifecycle_event_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    required = EVENT_FIELDS - {"decision_id"}
    if not isinstance(payload, Mapping) or not required <= set(payload) or not set(payload) <= EVENT_FIELDS:
        raise LifecycleError(
            f"lifecycle event payload requires {sorted(required)} and only allows {sorted(EVENT_FIELDS)}"
        )
    normalized = {
        "target_id": _uuid(payload["target_id"], "target_id"),
        "target_type": _choice(payload["target_type"], TARGET_TYPES, "target_type"),
        "actor": _non_empty(payload["actor"], "actor"),
        "action": _choice(payload["action"], ACTIONS, "action"),
        "from_state": None
        if payload["from_state"] is None
        else _choice(payload["from_state"], LIFECYCLE_STATES, "from_state"),
        "to_state": _choice(payload["to_state"], LIFECYCLE_STATES, "to_state"),
        "reason": _non_empty(payload["reason"], "reason"),
        "approval_kind": _choice(payload["approval_kind"], APPROVAL_KINDS, "approval_kind"),
        "source_ids": _uuid_list(payload["source_ids"], "source_ids"),
        "related_target_ids": _uuid_list(payload["related_target_ids"], "related_target_ids"),
        "replacement_id": _optional_uuid(payload["replacement_id"], "replacement_id"),
        "decision_id": _optional_uuid(payload.get("decision_id"), "decision_id"),
    }
    if normalized["target_id"] in normalized["related_target_ids"]:
        raise LifecycleError("related_target_ids cannot contain target_id")
    return normalized


def validate_lifecycle_state_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != STATE_FIELDS:
        raise LifecycleError(f"lifecycle state payload must contain exactly: {sorted(STATE_FIELDS)}")
    revision = payload["revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise LifecycleError("revision must be a positive integer")
    return {
        "target_id": _uuid(payload["target_id"], "target_id"),
        "target_type": _choice(payload["target_type"], TARGET_TYPES, "target_type"),
        "state": _choice(payload["state"], LIFECYCLE_STATES, "state"),
        "revision": revision,
        "last_event_id": _uuid(payload["last_event_id"], "last_event_id"),
        "conflict_ids": _uuid_list(payload["conflict_ids"], "conflict_ids"),
        "superseded_by": _optional_uuid(payload["superseded_by"], "superseded_by"),
        "last_reason": _non_empty(payload["last_reason"], "last_reason"),
        "last_actor": _non_empty(payload["last_actor"], "last_actor"),
        "last_approval_kind": _choice(
            payload["last_approval_kind"], APPROVAL_KINDS, "last_approval_kind"
        ),
        "last_source_ids": _uuid_list(payload["last_source_ids"], "last_source_ids"),
        "last_decision_id": _optional_uuid(payload["last_decision_id"], "last_decision_id"),
    }


def _transition_target(action: str, current: str | None, requested: str, replacement_id: str | None) -> str:
    if action == "register":
        if current is not None or requested not in {"candidate", "current"}:
            raise InvalidLifecycleTransition("register requires no prior state and candidate/current target")
        return requested
    if current is None:
        raise InvalidLifecycleTransition("target must be registered first")
    if current in TERMINAL_STATES:
        raise InvalidLifecycleTransition(f"terminal lifecycle state cannot transition: {current}")
    rules = {
        "request_review": ({"candidate", "current"}, "review_required"),
        "approve_current": ({"candidate", "review_required"}, "current"),
        "declare_conflict": ({"candidate", "current", "review_required"}, "review_required"),
        "supersede": ({"candidate", "current", "review_required"}, "superseded"),
        "reject": ({"candidate", "review_required"}, "rejected"),
        "retire": ({"current", "review_required"}, "retired"),
    }
    allowed, expected = rules[action]
    if current not in allowed or requested != expected:
        raise InvalidLifecycleTransition(f"invalid lifecycle transition: {current} --{action}--> {requested}")
    if action == "supersede" and replacement_id is None:
        raise InvalidLifecycleTransition("supersede requires replacement_id")
    if action != "supersede" and replacement_id is not None:
        raise InvalidLifecycleTransition("replacement_id is only valid for supersede")
    return requested


def _requires_current_approval(action: str, to_state: str) -> bool:
    return action in {"approve_current", "supersede", "reject", "retire"} or (
        action == "register" and to_state == "current"
    )


def replay_lifecycle_events(target_id: str, events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    identifier = _uuid(target_id, "target_id")
    matching = [event for event in events if event.get("payload", {}).get("target_id") == identifier]
    if not matching:
        raise LifecycleError(f"no lifecycle events for target: {identifier}")
    current: dict[str, Any] | None = None
    target_type: str | None = None
    conflict_ids: list[str] = []
    for index, event in enumerate(matching):
        payload = validate_lifecycle_event_payload(event["payload"])
        if target_type is None:
            target_type = payload["target_type"]
        elif target_type != payload["target_type"]:
            raise LifecycleError("target_type changed within lifecycle history")
        current_state = None if current is None else current["state"]
        if payload["from_state"] != current_state:
            raise InvalidLifecycleTransition("lifecycle event from_state does not match replay state")
        _transition_target(
            payload["action"], current_state, payload["to_state"], payload["replacement_id"]
        )
        if _requires_current_approval(payload["action"], payload["to_state"]):
            if payload["approval_kind"] not in CURRENT_APPROVAL_KINDS:
                raise InvalidLifecycleTransition("transition requires user or standing_policy approval")
        if payload["action"] == "declare_conflict":
            if not payload["related_target_ids"]:
                raise InvalidLifecycleTransition("declare_conflict requires related_target_ids")
            conflict_ids = list(dict.fromkeys([*conflict_ids, *payload["related_target_ids"]]))
        current = {
            "target_id": identifier,
            "target_type": payload["target_type"],
            "state": payload["to_state"],
            "revision": index + 1,
            "last_event_id": event["id"],
            "conflict_ids": conflict_ids,
            "superseded_by": payload["replacement_id"] if payload["action"] == "supersede" else None,
            "last_reason": payload["reason"],
            "last_actor": payload["actor"],
            "last_approval_kind": payload["approval_kind"],
            "last_source_ids": payload["source_ids"],
            "last_decision_id": payload["decision_id"],
        }
    assert current is not None
    return validate_lifecycle_state_payload(current)


class LifecycleService:
    def __init__(
        self,
        project_root: Path | str,
        *,
        _write_capability: object | None = None,
    ) -> None:
        self.root = Path(project_root).resolve()
        self.store = RecordStore(
            self.root,
            approved_record_types=LIFECYCLE_RECORD_TYPES,
            approved_streams=LIFECYCLE_STREAMS,
            _write_capability=_write_capability,
        )
        self.knowledge = KnowledgeService(
            self.root,
            _write_capability=_write_capability,
        )

    def initialize(self) -> dict[str, str]:
        return self.store.initialize()

    def _base_record(self, target_id: str) -> dict[str, Any]:
        record = self.store.get_record(_uuid(target_id, "target_id"))
        if record["record_type"] not in TARGET_TYPES:
            raise LifecycleError(f"unsupported lifecycle target type: {record['record_type']}")
        return record

    def _events(self) -> tuple[list[dict[str, Any]], str]:
        return self.store.list_events("lifecycle_events")

    def _state_or_none(self, target_id: str) -> dict[str, Any] | None:
        for state in self.store.list_records("lifecycle_state"):
            if state["payload"]["target_id"] == target_id:
                return state
        return None

    def get_state(self, target_id: str) -> dict[str, Any]:
        state = self._state_or_none(_uuid(target_id, "target_id"))
        if state is None:
            raise LifecycleError(f"lifecycle target is not registered: {target_id}")
        validate_lifecycle_state_payload(state["payload"])
        return state

    def get_record(self, target_id: str) -> dict[str, Any]:
        return {"record": self._base_record(target_id), "lifecycle": self.get_state(target_id)}

    def register(
        self,
        target_id: str,
        *,
        initial_state: str,
        actor: str,
        approval_kind: str,
        reason: str,
        source_ids: Sequence[str] = (),
        decision_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        base = self._base_record(target_id)
        if self._state_or_none(base["id"]) is not None:
            raise LifecycleError(f"lifecycle target is already registered: {base['id']}")
        return self._append_and_rebuild(
            base,
            expected_state_hash=None,
            action="register",
            to_state=initial_state,
            actor=actor,
            approval_kind=approval_kind,
            reason=reason,
            source_ids=source_ids,
            decision_id=decision_id,
            timestamp=timestamp,
        )

    def transition(
        self,
        target_id: str,
        *,
        expected_state_hash: str,
        action: str,
        actor: str,
        approval_kind: str,
        reason: str,
        source_ids: Sequence[str] = (),
        related_target_ids: Sequence[str] = (),
        replacement_id: str | None = None,
        decision_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(target_id)
        if state["content_hash"] != expected_state_hash:
            raise ExpectationMismatchError("Current lifecycle state hash differs from expected value.")
        action = _choice(action, ACTIONS - {"register"}, "action")
        targets = {
            "request_review": "review_required",
            "approve_current": "current",
            "declare_conflict": "review_required",
            "supersede": "superseded",
            "reject": "rejected",
            "retire": "retired",
        }
        if action == "declare_conflict":
            if not related_target_ids:
                raise InvalidLifecycleTransition("declare_conflict requires related_target_ids")
            base_type = self._base_record(target_id)["record_type"]
            for related_id in related_target_ids:
                related = self._base_record(related_id)
                if related["record_type"] != base_type:
                    raise LifecycleError("conflict targets must have the same record type")
                related_state = self.get_state(related_id)
                _transition_target(
                    "declare_conflict",
                    related_state["payload"]["state"],
                    "review_required",
                    None,
                )
        updated = self._append_and_rebuild(
            self._base_record(target_id),
            expected_state_hash=expected_state_hash,
            action=action,
            to_state=targets[action],
            actor=actor,
            approval_kind=approval_kind,
            reason=reason,
            source_ids=source_ids,
            related_target_ids=related_target_ids,
            replacement_id=replacement_id,
            decision_id=decision_id,
            timestamp=timestamp,
        )
        if action == "declare_conflict":
            for related_id in related_target_ids:
                related_state = self.get_state(related_id)
                self._append_and_rebuild(
                    self._base_record(related_id),
                    expected_state_hash=related_state["content_hash"],
                    action="declare_conflict",
                    to_state="review_required",
                    actor=actor,
                    approval_kind=approval_kind,
                    reason=reason,
                    source_ids=source_ids,
                    related_target_ids=[target_id],
                    decision_id=decision_id,
                    timestamp=timestamp,
                )
            updated = self.get_state(target_id)
        return updated

    def _append_and_rebuild(
        self,
        base: Mapping[str, Any],
        *,
        expected_state_hash: str | None,
        action: str,
        to_state: str,
        actor: str,
        approval_kind: str,
        reason: str,
        source_ids: Sequence[str] = (),
        related_target_ids: Sequence[str] = (),
        replacement_id: str | None = None,
        decision_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        existing = self._state_or_none(base["id"])
        from_state = None if existing is None else existing["payload"]["state"]
        if existing is not None and expected_state_hash != existing["content_hash"]:
            raise ExpectationMismatchError("Current lifecycle state hash differs from expected value.")
        event_timestamp = timestamp or datetime.now(UTC)
        if event_timestamp.tzinfo is None or event_timestamp.utcoffset() is None:
            raise LifecycleError("timestamp must be timezone-aware")
        event_timestamp = event_timestamp.astimezone(UTC).replace(microsecond=0)
        if existing is not None:
            current_time = datetime.strptime(existing["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            if event_timestamp < current_time:
                raise InvalidLifecycleTransition("lifecycle event timestamp cannot precede current state")
        payload = validate_lifecycle_event_payload(
            {
                "target_id": base["id"],
                "target_type": base["record_type"],
                "actor": actor,
                "action": action,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
                "approval_kind": approval_kind,
                "source_ids": list(source_ids),
                "related_target_ids": list(related_target_ids),
                "replacement_id": replacement_id,
                "decision_id": decision_id,
            }
        )
        _transition_target(action, from_state, to_state, payload["replacement_id"])
        if _requires_current_approval(action, to_state) and payload["approval_kind"] not in CURRENT_APPROVAL_KINDS:
            raise InvalidLifecycleTransition("transition requires user or standing_policy approval")
        for source_id in payload["source_ids"]:
            if self._base_record(source_id)["record_type"] != "source":
                raise LifecycleError("source_ids must reference source records")
        for related_id in payload["related_target_ids"]:
            related = self._base_record(related_id)
            if related["record_type"] != base["record_type"]:
                raise LifecycleError("conflict targets must have the same record type")
        if action == "declare_conflict" and not payload["related_target_ids"]:
            raise InvalidLifecycleTransition("declare_conflict requires related_target_ids")
        if payload["replacement_id"] is not None:
            if payload["replacement_id"] == base["id"]:
                raise InvalidLifecycleTransition("replacement cannot reference the superseded target itself")
            replacement = self._base_record(payload["replacement_id"])
            if replacement["record_type"] != base["record_type"]:
                raise LifecycleError("replacement must have the same record type")
            replacement_state = self.get_state(replacement["id"])
            if replacement_state["payload"]["state"] != "current":
                raise InvalidLifecycleTransition("replacement must be current")
        if payload["decision_id"] is not None:
            decision = self._base_record(payload["decision_id"])
            if decision["record_type"] != "decision":
                raise LifecycleError("decision_id must reference a decision record")
            if self.get_state(decision["id"])["payload"]["state"] != "current":
                raise InvalidLifecycleTransition("decision_id must reference a current decision")
        events, stream_hash = self._events()
        appended = self.store.append_event(
            "lifecycle_events", payload, expected_stream_hash=stream_hash, timestamp=event_timestamp
        )
        try:
            return self.rebuild_snapshot(base["id"], expected_last_event_id=appended["event"]["id"])
        except Exception as exc:
            raise LifecycleProjectionPending(
                f"lifecycle event committed but snapshot rebuild is pending: {base['id']}"
            ) from exc

    def rebuild_snapshot(
        self, target_id: str, *, expected_last_event_id: str | None = None
    ) -> dict[str, Any]:
        base = self._base_record(target_id)
        events, _ = self._events()
        payload = replay_lifecycle_events(base["id"], events)
        if expected_last_event_id is not None and payload["last_event_id"] != expected_last_event_id:
            raise LifecycleError("lifecycle replay did not end at expected event")
        current = self._state_or_none(base["id"])
        timestamp = next(
            datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            for event in reversed(events)
            if event["id"] == payload["last_event_id"]
        )
        if current is None:
            return self.store.create_record(
                "lifecycle_state", payload, record_id=str(uuid4()), timestamp=timestamp
            )
        return self.store.update_record(
            current["id"], payload, expected_content_hash=current["content_hash"], timestamp=timestamp
        )

    def history(self, target_id: str) -> list[dict[str, Any]]:
        identifier = _uuid(target_id, "target_id")
        events, _ = self._events()
        return [event for event in events if event["payload"].get("target_id") == identifier]

    def list_states(
        self, *, state: str | None = None, target_type: str | None = None
    ) -> list[dict[str, Any]]:
        if state is not None:
            state = _choice(state, LIFECYCLE_STATES, "state")
        if target_type is not None:
            target_type = _choice(target_type, TARGET_TYPES, "target_type")
        records = self.store.list_records("lifecycle_state")
        return [
            record
            for record in records
            if (state is None or record["payload"]["state"] == state)
            and (target_type is None or record["payload"]["target_type"] == target_type)
        ]

    def current_records(self, *, target_type: str | None = None) -> list[dict[str, Any]]:
        return [
            self._base_record(state["payload"]["target_id"])
            for state in self.list_states(state="current", target_type=target_type)
        ]

    def _recommended_initial_state(self, record: Mapping[str, Any]) -> str:
        if record["record_type"] == "source":
            return "current" if record["payload"]["verification_status"] == "verified" else "candidate"
        if record["record_type"] == "knowledge":
            return "current" if record["payload"]["verification_status"] == "verified" else "candidate"
        return "current"

    def register_existing(self, *, actor: str, approval_kind: str) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        for target_type in ("source", "knowledge", "decision", "failure_knowledge"):
            for record in self.store.list_records(target_type):
                if self._state_or_none(record["id"]) is not None:
                    continue
                initial = self._recommended_initial_state(record)
                created.append(
                    self.register(
                        record["id"],
                        initial_state=initial,
                        actor=actor,
                        approval_kind=approval_kind if initial == "current" else "agent_in_scope",
                        reason="기존 검증 상태를 보존한 최소 수명주기 등록",
                    )
                )
        return created

    def _dependency_source_ids(self, record: Mapping[str, Any]) -> list[str]:
        payload = record["payload"]
        if record["record_type"] in {"knowledge", "decision"}:
            return list(payload["source_ids"])
        return []

    def audit(self, *, actor: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        drifted_sources: set[str] = set()
        for state in self.list_states():
            if state["payload"]["state"] in TERMINAL_STATES:
                continue
            record = self._base_record(state["payload"]["target_id"])
            reason: str | None = None
            try:
                if record["record_type"] == "source":
                    locator = record["payload"]["locator"]
                    if not (
                        record["payload"]["source_kind"] == "local_document"
                        and locator.startswith("core/failures/")
                    ):
                        self.knowledge.get_source(record["id"], verify_local=True)
            except SourceIntegrityError as exc:
                reason = str(exc)
                if record["record_type"] == "source":
                    drifted_sources.add(record["id"])
            if reason is not None:
                findings.append({"target_id": record["id"], "reason": reason})
                if state["payload"]["state"] != "review_required":
                    self.transition(
                        record["id"],
                        expected_state_hash=state["content_hash"],
                        action="request_review",
                        actor=actor,
                        approval_kind="agent_in_scope",
                        reason=reason,
                    )
        for state in self.list_states():
            if state["payload"]["state"] in TERMINAL_STATES | {"review_required"}:
                continue
            record = self._base_record(state["payload"]["target_id"])
            affected = sorted(set(self._dependency_source_ids(record)) & drifted_sources)
            if affected:
                reason = "referenced source requires review: " + ", ".join(affected)
                findings.append({"target_id": record["id"], "reason": reason})
                self.transition(
                    record["id"],
                    expected_state_hash=state["content_hash"],
                    action="request_review",
                    actor=actor,
                    approval_kind="agent_in_scope",
                    reason=reason,
                    source_ids=affected,
                )
        return findings

    def refresh_failure_projection(
        self,
        old_failure_id: str,
        *,
        actor: str,
        approval_kind: str,
        reason: str,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        approval_kind = _choice(approval_kind, APPROVAL_KINDS, "approval_kind")
        if approval_kind not in CURRENT_APPROVAL_KINDS:
            raise InvalidLifecycleTransition("failure projection revision requires user or standing_policy approval")
        old_failure = self._base_record(old_failure_id)
        if old_failure["record_type"] != "failure_knowledge":
            raise LifecycleError("old_failure_id must reference failure_knowledge")
        core = self.knowledge.validate_failure_document(
            old_failure["payload"]["canonical_doc_ref"]
        )
        return {
            "failure_document": core,
            "legacy_record_id": old_failure["id"],
            "stored": False,
            "message": (
                "canonical failure Markdown is validated directly; "
                "no source, projection, lifecycle snapshot, or event was created"
            ),
        }
