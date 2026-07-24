"""Explicit long-term knowledge record types."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
from pathlib import Path
import re
from typing import Any
from uuid import UUID, uuid4

from .record import resolve_project_path
from .store import InputContractError, RecordIOError, RecordStore


KNOWLEDGE_RECORD_TYPES = frozenset(
    {"example", "work_state", "source", "knowledge", "decision", "failure_knowledge", "lifecycle_state"}
)
KNOWLEDGE_STREAMS = frozenset({"example_events", "work_events"})
SOURCE_KINDS = frozenset(
    {"local_document", "local_data", "command_result", "web_page", "user_statement"}
)
SOURCE_VERIFICATION_STATUSES = frozenset({"observed", "verified", "unavailable"})
SOURCE_EVIDENCE_ROLES = frozenset({"primary", "supporting", "contextual"})
SOURCE_FIELDS = frozenset(
    {
        "source_kind",
        "locator",
        "observed_at",
        "verification_status",
        "evidence_role",
        "version_or_hash",
    }
)
KNOWLEDGE_CLASSES = frozenset({"fact", "inference", "procedure", "constraint"})
KNOWLEDGE_VERIFICATION_STATUSES = frozenset({"candidate", "verified"})
KNOWLEDGE_FIELDS = frozenset(
    {"statement", "classification", "scope", "source_ids", "verification_status", "verified_by"}
)
DECISION_APPROVAL_KINDS = frozenset({"user", "standing_policy", "agent_in_scope"})
DECISION_FIELDS = frozenset(
    {
        "problem",
        "requirements",
        "options",
        "selected_option",
        "rationale",
        "impacts",
        "source_ids",
        "requires_user_approval",
        "approval_kind",
        "approved_by",
        "decided_at",
    }
)
DECISION_OPTION_FIELDS = frozenset({"label", "impact"})
FAILURE_KNOWLEDGE_FIELDS = frozenset(
    {
        "title",
        "canonical_doc_ref",
        "document_hash",
        "source_id",
        "symptom",
        "conditions",
        "confirmed_cause",
        "resolution",
        "verification",
        "prevention",
        "projection_status",
        "projected_by",
        "projected_at",
    }
)
UTC_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class KnowledgeRecordError(RecordIOError):
    kind = "knowledge_validation"
    exit_status = 5


class SourceIntegrityError(KnowledgeRecordError):
    kind = "source_integrity"


def _non_empty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise KnowledgeRecordError(f"{field} must be a non-empty string without NUL")
    return value


def _render_time(value: datetime | None) -> tuple[datetime, str]:
    current = value or datetime.now(UTC)
    if current.tzinfo is None or current.utcoffset() is None:
        raise InputContractError("timestamp must be timezone-aware")
    normalized = current.astimezone(UTC).replace(microsecond=0)
    return normalized, normalized.strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _uuid_list(value: Any, field: str, *, require_nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (require_nonempty and not value):
        raise KnowledgeRecordError(f"{field} must be a list of canonical UUIDv4 strings")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise KnowledgeRecordError(f"{field} must contain strings")
        try:
            parsed = UUID(item)
        except ValueError as exc:
            raise KnowledgeRecordError(f"{field} must contain canonical UUIDv4 strings") from exc
        if parsed.version != 4 or str(parsed) != item or item in normalized:
            raise KnowledgeRecordError(f"{field} must contain unique canonical UUIDv4 strings")
        normalized.append(item)
    return normalized


def _string_list(value: Any, field: str, *, require_nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (require_nonempty and not value):
        raise KnowledgeRecordError(f"{field} must be a list of non-empty strings")
    normalized = [_non_empty(item, field) for item in value]
    if len(set(normalized)) != len(normalized):
        raise KnowledgeRecordError(f"{field} must not contain duplicates")
    return normalized


def validate_source_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != SOURCE_FIELDS:
        raise KnowledgeRecordError(f"source payload must contain exactly: {sorted(SOURCE_FIELDS)}")
    source_kind = payload["source_kind"]
    status = payload["verification_status"]
    role = payload["evidence_role"]
    if source_kind not in SOURCE_KINDS:
        raise KnowledgeRecordError(f"unsupported source_kind: {source_kind}")
    if status not in SOURCE_VERIFICATION_STATUSES:
        raise KnowledgeRecordError(f"unsupported verification_status: {status}")
    if role not in SOURCE_EVIDENCE_ROLES:
        raise KnowledgeRecordError(f"unsupported evidence_role: {role}")
    locator = _non_empty(payload["locator"], "locator")
    observed_at = payload["observed_at"]
    if not isinstance(observed_at, str) or UTC_TIMESTAMP_PATTERN.fullmatch(observed_at) is None:
        raise KnowledgeRecordError("observed_at must be a UTC timestamp with second precision")
    try:
        datetime.strptime(observed_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise KnowledgeRecordError("observed_at must be a real timestamp") from exc
    version = payload["version_or_hash"]
    if version is not None:
        version = _non_empty(version, "version_or_hash")
    if source_kind in {"local_document", "local_data"}:
        if status != "verified" or not isinstance(version, str) or SHA256_PATTERN.fullmatch(version) is None:
            raise KnowledgeRecordError("local sources require verified status and a SHA-256 hash")
    if source_kind == "web_page" and not locator.startswith(("https://", "http://")):
        raise KnowledgeRecordError("web_page locator must use http or https")
    return {
        "source_kind": source_kind,
        "locator": locator,
        "observed_at": observed_at,
        "verification_status": status,
        "evidence_role": role,
        "version_or_hash": version,
    }


def validate_knowledge_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != KNOWLEDGE_FIELDS:
        raise KnowledgeRecordError(
            f"knowledge payload must contain exactly: {sorted(KNOWLEDGE_FIELDS)}"
        )
    statement = _non_empty(payload["statement"], "statement")
    if "\n" in statement or "\r" in statement or len(statement) > 500:
        raise KnowledgeRecordError("statement must be one line of at most 500 characters")
    classification = payload["classification"]
    if classification not in KNOWLEDGE_CLASSES:
        raise KnowledgeRecordError(f"unsupported classification: {classification}")
    scope = _non_empty(payload["scope"], "scope")
    source_ids = _uuid_list(payload["source_ids"], "source_ids")
    status = payload["verification_status"]
    if status not in KNOWLEDGE_VERIFICATION_STATUSES:
        raise KnowledgeRecordError(f"unsupported verification_status: {status}")
    verifier = payload["verified_by"]
    if status == "verified":
        verifier = _non_empty(verifier, "verified_by")
    elif verifier is not None:
        raise KnowledgeRecordError("candidate knowledge cannot name verified_by")
    return {
        "statement": statement,
        "classification": classification,
        "scope": scope,
        "source_ids": source_ids,
        "verification_status": status,
        "verified_by": verifier,
    }


def validate_decision_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != DECISION_FIELDS:
        raise KnowledgeRecordError(f"decision payload must contain exactly: {sorted(DECISION_FIELDS)}")
    problem = _non_empty(payload["problem"], "problem")
    requirements = _string_list(payload["requirements"], "requirements")
    raw_options = payload["options"]
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise KnowledgeRecordError("options must contain at least two choices")
    options: list[dict[str, str]] = []
    labels: list[str] = []
    for option in raw_options:
        if not isinstance(option, Mapping) or set(option) != DECISION_OPTION_FIELDS:
            raise KnowledgeRecordError("each option must contain exactly label and impact")
        label = _non_empty(option["label"], "option.label")
        impact = _non_empty(option["impact"], "option.impact")
        if label in labels:
            raise KnowledgeRecordError("option labels must be unique")
        labels.append(label)
        options.append({"label": label, "impact": impact})
    selected = _non_empty(payload["selected_option"], "selected_option")
    if selected not in labels:
        raise KnowledgeRecordError("selected_option must match one reviewed option label")
    rationale = _non_empty(payload["rationale"], "rationale")
    impacts = _string_list(payload["impacts"], "impacts")
    source_ids = _uuid_list(payload["source_ids"], "source_ids")
    requires_user = payload["requires_user_approval"]
    if not isinstance(requires_user, bool):
        raise KnowledgeRecordError("requires_user_approval must be boolean")
    approval_kind = payload["approval_kind"]
    if approval_kind not in DECISION_APPROVAL_KINDS:
        raise KnowledgeRecordError(f"unsupported approval_kind: {approval_kind}")
    if requires_user and approval_kind not in {"user", "standing_policy"}:
        raise KnowledgeRecordError("user-required decisions need user or standing_policy approval")
    approved_by = _non_empty(payload["approved_by"], "approved_by")
    decided_at = payload["decided_at"]
    if not isinstance(decided_at, str) or UTC_TIMESTAMP_PATTERN.fullmatch(decided_at) is None:
        raise KnowledgeRecordError("decided_at must be a UTC timestamp with second precision")
    try:
        datetime.strptime(decided_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise KnowledgeRecordError("decided_at must be a real timestamp") from exc
    return {
        "problem": problem,
        "requirements": requirements,
        "options": options,
        "selected_option": selected,
        "rationale": rationale,
        "impacts": impacts,
        "source_ids": source_ids,
        "requires_user_approval": requires_user,
        "approval_kind": approval_kind,
        "approved_by": approved_by,
        "decided_at": decided_at,
    }


def validate_failure_knowledge_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != FAILURE_KNOWLEDGE_FIELDS:
        raise KnowledgeRecordError(
            f"failure_knowledge payload must contain exactly: {sorted(FAILURE_KNOWLEDGE_FIELDS)}"
        )
    title = _non_empty(payload["title"], "title")
    canonical = _non_empty(payload["canonical_doc_ref"], "canonical_doc_ref")
    canonical_path = Path(canonical)
    if (
        canonical_path.parts[:1] != ("failures",)
        or len(canonical_path.parts) != 2
        or canonical_path.suffix != ".md"
        or canonical_path.name == "README.md"
    ):
        raise KnowledgeRecordError("canonical_doc_ref must be failures/<case>.md and not the index")
    document_hash = payload["document_hash"]
    if not isinstance(document_hash, str) or SHA256_PATTERN.fullmatch(document_hash) is None:
        raise KnowledgeRecordError("document_hash must be SHA-256")
    source_id = _uuid_list([payload["source_id"]], "source_id")[0]
    symptom = _non_empty(payload["symptom"], "symptom")
    conditions = _string_list(payload["conditions"], "conditions")
    cause = _non_empty(payload["confirmed_cause"], "confirmed_cause")
    resolution = _string_list(payload["resolution"], "resolution")
    verification = _string_list(payload["verification"], "verification")
    prevention = _string_list(payload["prevention"], "prevention")
    if payload["projection_status"] != "resolved":
        raise KnowledgeRecordError("only resolved failure documents can be projected")
    projected_by = _non_empty(payload["projected_by"], "projected_by")
    projected_at = payload["projected_at"]
    if not isinstance(projected_at, str) or UTC_TIMESTAMP_PATTERN.fullmatch(projected_at) is None:
        raise KnowledgeRecordError("projected_at must be a UTC timestamp with second precision")
    try:
        datetime.strptime(projected_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise KnowledgeRecordError("projected_at must be a real timestamp") from exc
    return {
        "title": title,
        "canonical_doc_ref": canonical,
        "document_hash": document_hash,
        "source_id": source_id,
        "symptom": symptom,
        "conditions": conditions,
        "confirmed_cause": cause,
        "resolution": resolution,
        "verification": verification,
        "prevention": prevention,
        "projection_status": "resolved",
        "projected_by": projected_by,
        "projected_at": projected_at,
    }


def _failure_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None or not match.group(1).strip():
        raise KnowledgeRecordError(f"failure document is missing section: {heading}")
    return match.group(1).strip()


def _section_bullets(section: str, field: str) -> list[str]:
    lines = [line.strip()[2:].strip() for line in section.splitlines() if line.strip().startswith("- ")]
    return _string_list(lines, field)


def parse_failure_document(data: bytes, canonical_doc_ref: str) -> dict[str, Any]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KnowledgeRecordError("failure document must be strict UTF-8") from exc
    if "\x00" in text:
        raise KnowledgeRecordError("failure document cannot contain NUL")
    title_match = re.search(r"^# (.+)$", text, flags=re.MULTILINE)
    status_match = re.search(r"^- 상태:\s*(.+)$", text, flags=re.MULTILINE)
    condition_match = re.search(r"^- 적용 범위:\s*(.+)$", text, flags=re.MULTILINE)
    if title_match is None or status_match is None or condition_match is None:
        raise KnowledgeRecordError("failure document is missing title, status, or scope metadata")
    if "해결" not in status_match.group(1):
        raise KnowledgeRecordError("unresolved failure documents cannot be reused")
    solution_lines = _section_bullets(_failure_section(text, "해결과 검증"), "solution evidence")
    if len(solution_lines) < 2:
        raise KnowledgeRecordError("해결과 검증 section needs resolution and verification evidence")
    return {
        "title": title_match.group(1).strip(),
        "canonical_doc_ref": canonical_doc_ref,
        "document_hash": "sha256:" + hashlib.sha256(data).hexdigest(),
        "symptom": _failure_section(text, "증상"),
        "conditions": [condition_match.group(1).strip()],
        "confirmed_cause": _failure_section(text, "확인된 원인"),
        "resolution": [solution_lines[0]],
        "verification": solution_lines[1:],
        "prevention": _section_bullets(_failure_section(text, "재사용 규칙"), "prevention"),
    }


class KnowledgeService:
    def __init__(
        self,
        project_root: Path | str,
        *,
        _write_capability: object | None = None,
    ) -> None:
        self.store = RecordStore(
            project_root,
            approved_record_types=KNOWLEDGE_RECORD_TYPES,
            approved_streams=KNOWLEDGE_STREAMS,
            _write_capability=_write_capability,
        )

    def initialize(self) -> dict[str, str]:
        return self.store.initialize()

    def create_source(
        self,
        *,
        source_kind: str,
        locator: str,
        evidence_role: str,
        verification_status: str | None = None,
        version_or_hash: str | None = None,
        record_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        normalized_time, rendered_time = _render_time(timestamp)
        locator = _non_empty(locator, "locator")
        if source_kind in {"local_document", "local_data"}:
            target = resolve_project_path(self.store.root, locator)
            if not target.is_file():
                raise KnowledgeRecordError(f"local source file does not exist: {locator}")
            actual_hash = _file_hash(target)
            if version_or_hash is not None and version_or_hash != actual_hash:
                raise SourceIntegrityError("provided source hash does not match local bytes")
            version_or_hash = actual_hash
            verification_status = "verified"
        else:
            verification_status = verification_status or "observed"
        payload = validate_source_payload(
            {
                "source_kind": source_kind,
                "locator": locator,
                "observed_at": rendered_time,
                "verification_status": verification_status,
                "evidence_role": evidence_role,
                "version_or_hash": version_or_hash,
            }
        )
        return self.store.create_record(
            "source", payload, record_id=record_id, timestamp=normalized_time
        )

    def get_source(self, record_id: str, *, verify_local: bool = False) -> dict[str, Any]:
        record = self.store.get_record(record_id)
        if record["record_type"] != "source":
            raise KnowledgeRecordError(f"record is not a source: {record_id}")
        payload = validate_source_payload(record["payload"])
        if verify_local and payload["source_kind"] in {"local_document", "local_data"}:
            target = resolve_project_path(self.store.root, payload["locator"])
            if not target.is_file() or _file_hash(target) != payload["version_or_hash"]:
                raise SourceIntegrityError(f"local source bytes changed or disappeared: {payload['locator']}")
        return record

    def list_sources(self, *, verify_local: bool = False) -> list[dict[str, Any]]:
        records = self.store.list_records("source")
        return [self.get_source(record["id"], verify_local=verify_local) for record in records]

    def verify_source(self, record_id: str) -> dict[str, Any]:
        record = self.get_source(record_id, verify_local=True)
        payload = record["payload"]
        return {
            "record_id": record_id,
            "verification_status": payload["verification_status"],
            "version_or_hash": payload["version_or_hash"],
            "integrity": "match" if payload["source_kind"] in {"local_document", "local_data"} else "not_applicable",
        }

    def _validated_sources(
        self, source_ids: list[str], *, verify_local: bool
    ) -> list[dict[str, Any]]:
        sources = [self.get_source(source_id, verify_local=verify_local) for source_id in source_ids]
        if any(source["payload"]["verification_status"] == "unavailable" for source in sources):
            raise KnowledgeRecordError("knowledge cannot reference an unavailable source")
        return sources

    def create_knowledge(
        self,
        *,
        statement: str,
        classification: str,
        scope: str,
        source_ids: list[str],
        verification_status: str,
        verified_by: str | None = None,
        record_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        payload = validate_knowledge_payload(
            {
                "statement": statement,
                "classification": classification,
                "scope": scope,
                "source_ids": source_ids,
                "verification_status": verification_status,
                "verified_by": verified_by,
            }
        )
        self._validated_sources(payload["source_ids"], verify_local=True)
        return self.store.create_record(
            "knowledge", payload, record_id=record_id, timestamp=timestamp
        )

    def get_knowledge(self, record_id: str) -> dict[str, Any]:
        record = self.store.get_record(record_id)
        if record["record_type"] != "knowledge":
            raise KnowledgeRecordError(f"record is not knowledge: {record_id}")
        payload = validate_knowledge_payload(record["payload"])
        self._validated_sources(payload["source_ids"], verify_local=False)
        return record

    def list_knowledge(self) -> list[dict[str, Any]]:
        records = self.store.list_records("knowledge")
        return [self.get_knowledge(record["id"]) for record in records]

    def create_decision(
        self,
        payload: Mapping[str, Any],
        *,
        record_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        normalized = validate_decision_payload(payload)
        self._validated_sources(normalized["source_ids"], verify_local=True)
        normalized_time, _ = _render_time(timestamp)
        decided_at = datetime.strptime(normalized["decided_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        if decided_at > normalized_time:
            raise KnowledgeRecordError("decided_at cannot be later than record creation time")
        return self.store.create_record(
            "decision", normalized, record_id=record_id, timestamp=normalized_time
        )

    def get_decision(self, record_id: str) -> dict[str, Any]:
        record = self.store.get_record(record_id)
        if record["record_type"] != "decision":
            raise KnowledgeRecordError(f"record is not a decision: {record_id}")
        payload = validate_decision_payload(record["payload"])
        self._validated_sources(payload["source_ids"], verify_local=False)
        return record

    def list_decisions(self) -> list[dict[str, Any]]:
        records = self.store.list_records("decision")
        return [self.get_decision(record["id"]) for record in records]

    def _failure_projection_core(self, canonical_doc_ref: str) -> dict[str, Any]:
        target = resolve_project_path(self.store.root, canonical_doc_ref)
        if not target.is_file():
            raise KnowledgeRecordError(f"failure document does not exist: {canonical_doc_ref}")
        return parse_failure_document(target.read_bytes(), canonical_doc_ref)

    def failure_document_refs(self) -> list[str]:
        directory = self.store.root / "failures"
        if not directory.is_dir():
            return []
        return [
            path.relative_to(self.store.root).as_posix()
            for path in sorted(directory.glob("*.md"), key=lambda item: item.name)
            if path.name != "README.md"
        ]

    def validate_failure_document(self, canonical_doc_ref: str) -> dict[str, Any]:
        return self._failure_projection_core(canonical_doc_ref)

    def list_failure_documents(self) -> list[dict[str, Any]]:
        return [self.validate_failure_document(ref) for ref in self.failure_document_refs()]

    def import_failure_knowledge(
        self,
        canonical_doc_ref: str,
        *,
        projected_by: str,
        record_id: str | None = None,
        source_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        if record_id is not None or source_id is not None:
            raise KnowledgeRecordError(
                "per-case failure projection ids are no longer accepted; validate the canonical document"
            )
        projected_by = _non_empty(projected_by, "projected_by")
        _, rendered_time = _render_time(timestamp)
        core = self.validate_failure_document(canonical_doc_ref)
        return {
            "failure_document": {
                **core,
                "status": "resolved",
                "validated_by": projected_by,
                "validated_at": rendered_time,
            },
            "stored": False,
        }

    def _import_legacy_failure_knowledge(
        self,
        canonical_doc_ref: str,
        *,
        projected_by: str,
        record_id: str | None = None,
        source_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        """Create a v1 stored projection for compatibility tests only."""
        projected_by = _non_empty(projected_by, "projected_by")
        failure_identifier = record_id or str(uuid4())
        source_identifier = source_id or str(uuid4())
        _uuid_list([failure_identifier], "record_id")
        _uuid_list([source_identifier], "source_id")
        normalized_time, rendered_time = _render_time(timestamp)
        core = self._failure_projection_core(canonical_doc_ref)
        for existing in self.store.list_records("failure_knowledge"):
            payload = validate_failure_knowledge_payload(existing["payload"])
            if payload["canonical_doc_ref"] == canonical_doc_ref:
                raise KnowledgeRecordError(f"failure document is already projected: {canonical_doc_ref}")
        matched_source: dict[str, Any] | None = None
        for existing in self.store.list_records("source"):
            payload = validate_source_payload(existing["payload"])
            if payload["locator"] == canonical_doc_ref:
                if payload["version_or_hash"] != core["document_hash"]:
                    raise SourceIntegrityError("existing source for failure document has a different hash")
                matched_source = self.get_source(existing["id"])
                break
        if matched_source is None:
            matched_source = self.create_source(
                source_kind="local_document",
                locator=canonical_doc_ref,
                evidence_role="primary",
                record_id=source_identifier,
                timestamp=normalized_time,
            )
        payload = validate_failure_knowledge_payload(
            {
                **core,
                "source_id": matched_source["id"],
                "projection_status": "resolved",
                "projected_by": projected_by,
                "projected_at": rendered_time,
            }
        )
        failure = self.store.create_record(
            "failure_knowledge", payload, record_id=failure_identifier, timestamp=normalized_time
        )
        return {"source": matched_source, "failure_knowledge": failure}

    def get_failure_knowledge(self, record_id: str) -> dict[str, Any]:
        record = self.store.get_record(record_id)
        if record["record_type"] != "failure_knowledge":
            raise KnowledgeRecordError(f"record is not failure_knowledge: {record_id}")
        payload = validate_failure_knowledge_payload(record["payload"])
        source = self.get_source(payload["source_id"], verify_local=True)
        if (
            source["payload"]["locator"] != payload["canonical_doc_ref"]
            or source["payload"]["version_or_hash"] != payload["document_hash"]
        ):
            raise SourceIntegrityError("failure projection and source record disagree")
        current = self._failure_projection_core(payload["canonical_doc_ref"])
        for field in (
            "title", "canonical_doc_ref", "document_hash", "symptom", "conditions",
            "confirmed_cause", "resolution", "verification", "prevention",
        ):
            if payload[field] != current[field]:
                raise SourceIntegrityError(f"failure projection field differs from canonical document: {field}")
        return record

    def list_failure_knowledge(self) -> list[dict[str, Any]]:
        records = self.store.list_records("failure_knowledge")
        return [self.get_failure_knowledge(record["id"]) for record in records]
