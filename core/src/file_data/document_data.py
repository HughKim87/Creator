"""Strict Markdown-owned project data and deterministic JSON artifact views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any
import unicodedata
from urllib.parse import urlsplit
from uuid import UUID

from .store import ConcurrentWriteError, ExpectationMismatchError, InputContractError


DATA_MARKER = re.compile(
    r"^<!-- project-data:v1 kind=(?P<kind>[a-z-]+) key=(?P<key>[a-z0-9-]+) -->$"
)
ARTIFACT_MARKER = re.compile(
    r"^<!-- project-artifact:v1 path=(?P<path>[^ ]+) verify=json-semantic -->$"
)
KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE_PATTERN = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<tail>.*)$")
UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PROTECTED_SEGMENTS = frozenset({".git", ".obsidian", "backup", "inputs", "outputs"})
COMMON_FIELDS = frozenset({"key", "kind", "status", "source_refs", "payload"})
WORK_FIELDS = frozenset(
    {
        "desired_outcome",
        "authorized_actions",
        "excluded_scope",
        "input_refs",
        "protection_boundaries",
        "required_decisions",
        "verification_levels",
        "completed_items",
        "blockers",
        "next_action",
        "evidence_refs",
        "checkpoints",
    }
)
KNOWLEDGE_FIELDS = frozenset(
    {
        "statement",
        "classification",
        "scope",
        "verification_status",
        "verified_by",
        "replaces_legacy_ids",
    }
)
DECISION_FIELDS = frozenset(
    {
        "problem",
        "requirements",
        "options",
        "selected_option",
        "rationale",
        "impacts",
        "requires_user_approval",
        "approval_kind",
        "approved_by",
        "decided_at",
        "replaces_legacy_id",
    }
)
WORK_STATUSES = frozenset({"requested", "in_progress", "failed", "blocked", "completed"})
KNOWLEDGE_STATUSES = frozenset({"candidate", "current"})
KNOWLEDGE_CLASSES = frozenset({"fact", "inference", "procedure", "constraint"})
VERIFICATION_STATUSES = frozenset({"candidate", "verified"})
APPROVAL_KINDS = frozenset({"user", "standing_policy", "agent_in_scope"})

ARTIFACT_OWNERS: dict[str, str] = {
    "core/schemas/common-record-v1.schema.json": "core/docs/FILE_DATA_CONTRACT.md",
    "core/schemas/work-request-payload-v1.schema.json": "core/docs/WORK_STATE_CONTRACT.md",
    "core/schemas/work-event-payload-v1.schema.json": "core/docs/WORK_STATE_CONTRACT.md",
    "core/schemas/work-state-payload-v1.schema.json": "core/docs/WORK_STATE_CONTRACT.md",
    "core/schemas/source-payload-v1.schema.json": "core/docs/KNOWLEDGE_TYPES_CONTRACT.md",
    "core/schemas/knowledge-payload-v1.schema.json": "core/docs/KNOWLEDGE_TYPES_CONTRACT.md",
    "core/schemas/decision-payload-v1.schema.json": "core/docs/KNOWLEDGE_TYPES_CONTRACT.md",
    "core/schemas/failure-knowledge-payload-v1.schema.json": (
        "core/docs/KNOWLEDGE_TYPES_CONTRACT.md"
    ),
    "core/schemas/lifecycle-event-payload-v1.schema.json": (
        "core/docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md"
    ),
    "core/schemas/lifecycle-state-payload-v1.schema.json": (
        "core/docs/KNOWLEDGE_LIFECYCLE_CONTRACT.md"
    ),
    "core/schemas/context-package-v1.schema.json": "core/docs/CONTEXT_PACKAGE_CONTRACT.md",
    "extension/schemas/youtube-evidence-request-v1.schema.json": (
        "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md"
    ),
    "extension/schemas/youtube-evidence-pack-v1.schema.json": (
        "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md"
    ),
    ".obsidian/app.json": "core/docs/obsidian/OBSIDIAN_REVIEW_CONTRACT.md",
    "extension/examples/youtube/foundation-evidence.request.json": (
        "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md"
    ),
    "core/tests/fixtures/file_data/valid/neutral-record.json": "core/docs/FILE_DATA_CONTRACT.md",
    "core/tests/fixtures/file_data/invalid/missing-field.json": "core/docs/FILE_DATA_CONTRACT.md",
    "core/tests/fixtures/file_data/invalid/tampered-content.json": (
        "core/docs/FILE_DATA_CONTRACT.md"
    ),
    "core/tests/fixtures/file_data/invalid/wrong-id.json": "core/docs/FILE_DATA_CONTRACT.md",
    "core/tests/fixtures/file_data/invalid/wrong-version.json": "core/docs/FILE_DATA_CONTRACT.md",
}


class DocumentDataError(InputContractError):
    """A Markdown-owned data or artifact contract is invalid."""

    kind = "document_data_error"


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DocumentDataError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode_json(raw: str, label: str) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise DocumentDataError(f"{label} contains non-finite number: {value}")

    try:
        value = json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise DocumentDataError(f"{label} is invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise DocumentDataError(f"{label} must be a JSON object")
    return value


def _nonempty(value: Any, field: str, maximum: int | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DocumentDataError(f"{field} must be a non-empty string")
    rendered = value.strip()
    if rendered != value:
        raise DocumentDataError(f"{field} must not have leading or trailing whitespace")
    if maximum is not None and len(rendered) > maximum:
        raise DocumentDataError(f"{field} must be at most {maximum} characters")
    return rendered


def _string_list(
    value: Any,
    field: str,
    *,
    require_nonempty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        raise DocumentDataError(f"{field} must be a list")
    rendered = [_nonempty(item, field) for item in value]
    if require_nonempty and not rendered:
        raise DocumentDataError(f"{field} must not be empty")
    if len(set(rendered)) != len(rendered):
        raise DocumentDataError(f"{field} must not contain duplicates")
    return rendered


def _utc(value: Any, field: str) -> str:
    rendered = _nonempty(value, field)
    if UTC_PATTERN.fullmatch(rendered) is None:
        raise DocumentDataError(f"{field} must be UTC RFC3339 seconds with Z")
    try:
        datetime.fromisoformat(rendered.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DocumentDataError(f"{field} is not a real timestamp") from exc
    return rendered


def _uuid_or_none(value: Any, field: str) -> str | None:
    if value is None:
        return None
    rendered = _nonempty(value, field)
    try:
        parsed = UUID(rendered)
    except ValueError as exc:
        raise DocumentDataError(f"{field} must be a UUID or null") from exc
    if str(parsed) != rendered:
        raise DocumentDataError(f"{field} must be a lowercase canonical UUID")
    return rendered


def _markdown_files(root: Path) -> list[Path]:
    paths: list[Path] = []

    def visit(directory: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            raise DocumentDataError(f"cannot scan active document directory: {directory}") from exc
        for entry in entries:
            if entry.name in PROTECTED_SEGMENTS:
                continue
            if entry.is_symlink():
                continue
            path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                visit(path)
            elif entry.is_file(follow_symlinks=False) and path.suffix.lower() == ".md":
                paths.append(path)

    visit(root)
    return sorted(paths, key=lambda item: item.relative_to(root).as_posix())


def _read_markdown(path: Path) -> str:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise DocumentDataError(f"document is not strict UTF-8: {path}") from exc
    if "\x00" in text:
        raise DocumentDataError(f"document contains NUL: {path}")
    return text


def _block_candidates(text: str) -> list[tuple[int, re.Match[str]]]:
    """Return marker lines outside CommonMark fenced and indented code."""

    candidates: list[tuple[int, re.Match[str]]] = []
    active_character: str | None = None
    active_length = 0
    lines = text.splitlines()
    for index, line in enumerate(lines):
        fence = FENCE_PATTERN.fullmatch(line)
        if active_character is not None:
            if fence is not None:
                token = fence.group("fence")
                if (
                    token[0] == active_character
                    and len(token) >= active_length
                    and not fence.group("tail").strip()
                ):
                    active_character = None
                    active_length = 0
            continue
        if fence is not None:
            token = fence.group("fence")
            if token[0] == "`" and "`" in fence.group("tail"):
                fence = None
            else:
                active_character = token[0]
                active_length = len(token)
                continue
        if line.startswith(("    ", "\t")):
            continue
        marker = DATA_MARKER.fullmatch(line) or ARTIFACT_MARKER.fullmatch(line)
        if marker is not None:
            candidates.append((index, marker))
        elif line.startswith(("<!-- project-data:v1", "<!-- project-artifact:v1")):
            raise DocumentDataError(f"malformed project marker at line {index + 1}")
    return candidates


def _extract_blocks(
    text: str,
    marker_pattern: re.Pattern[str],
    closing_marker: str,
) -> list[tuple[re.Match[str], str]]:
    lines = text.splitlines()
    markers = {
        index: marker
        for index, marker in _block_candidates(text)
        if marker.re is marker_pattern
    }
    blocks: list[tuple[re.Match[str], str]] = []
    for index, marker in markers.items():
        if index + 3 >= len(lines) or lines[index + 1] != "```json":
            raise DocumentDataError(f"marker at line {index + 1} must be followed by ```json")
        try:
            fence_end = lines.index("```", index + 2)
        except ValueError as exc:
            raise DocumentDataError(f"JSON fence opened at line {index + 2} is not closed") from exc
        if fence_end + 1 >= len(lines) or lines[fence_end + 1] != closing_marker:
            raise DocumentDataError(
                f"JSON block at line {index + 1} must end with {closing_marker}"
            )
        blocks.append((marker, "\n".join(lines[index + 2 : fence_end])))
    return blocks


def _canonical_hash(value: Mapping[str, Any]) -> str:
    rendered = json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(rendered).hexdigest()


def _data_block_content_span(text: str, key: str) -> tuple[int, int]:
    """Return the JSON-content span for one exact project-data key."""

    lines = text.splitlines(keepends=True)
    plain = [line.rstrip("\r\n") for line in lines]
    matches: list[tuple[int, int]] = []
    for index, marker in _block_candidates(text):
        if marker.re is not DATA_MARKER or marker.group("key") != key:
            continue
        if index + 3 >= len(plain) or plain[index + 1] != "```json":
            raise DocumentDataError(f"marker at line {index + 1} must be followed by ```json")
        try:
            fence_end = plain.index("```", index + 2)
        except ValueError as exc:
            raise DocumentDataError(
                f"JSON fence opened at line {index + 2} is not closed"
            ) from exc
        if fence_end + 1 >= len(plain) or plain[fence_end + 1] != "<!-- /project-data -->":
            raise DocumentDataError(
                f"JSON block at line {index + 1} must end with <!-- /project-data -->"
            )
        matches.append(
            (
                sum(len(line) for line in lines[: index + 2]),
                sum(len(line) for line in lines[:fence_end]),
            )
        )
    if len(matches) != 1:
        raise DocumentDataError(
            f"expected exactly one project-data block for {key}, found {len(matches)}"
        )
    return matches[0]


class DocumentDataService:
    """Read and validate active ``project-data:v1`` blocks from Markdown owners."""

    def __init__(self, project_root: Path | str) -> None:
        root = Path(project_root)
        try:
            self.root = root.resolve(strict=True)
        except FileNotFoundError as exc:
            raise DocumentDataError("project root does not exist") from exc
        if not self.root.is_dir():
            raise DocumentDataError("project root must be a directory")

    def _source_ref(self, value: Any, field: str) -> str:
        rendered = _nonempty(value, field)
        if unicodedata.normalize("NFC", rendered) != rendered:
            raise DocumentDataError(f"{field} must use Unicode NFC")
        parsed = urlsplit(rendered)
        if parsed.scheme:
            if parsed.scheme != "https" or not parsed.netloc:
                raise DocumentDataError(f"{field} web references must use https")
            return rendered
        if "\\" in rendered or rendered.startswith("/"):
            raise DocumentDataError(f"{field} must be a normalized project-relative Markdown ref")
        path_text = rendered.split("#", 1)[0]
        path = PurePosixPath(path_text)
        if (
            not path.parts
            or any(part in {"", ".", ".."} or part in PROTECTED_SEGMENTS for part in path.parts)
            or path.suffix.lower() != ".md"
        ):
            raise DocumentDataError(f"{field} is outside the approved Markdown boundary")
        target = self.root.joinpath(*path.parts)
        if not target.is_file():
            raise DocumentDataError(f"{field} does not exist: {rendered}")
        return rendered

    def _owner_allowed(self, kind: str, relative: str) -> bool:
        path = PurePosixPath(relative)
        if kind == "work":
            return relative == "SESSION_HANDOFF.md"
        if kind == "knowledge":
            return (
                len(path.parts) >= 3
                and path.parts[:2] == ("core", "docs")
                or len(path.parts) >= 3
                and path.parts[:2] == ("extension", "docs")
            )
        if kind == "decision":
            return (
                len(path.parts) >= 3
                and path.parts[:2] == ("core", "docs")
                or len(path.parts) >= 3
                and path.parts[:2] == ("extension", "docs")
            )
        return False

    def _validate_work(self, block: Mapping[str, Any]) -> None:
        payload = block["payload"]
        if not isinstance(payload, Mapping) or set(payload) != WORK_FIELDS:
            raise DocumentDataError(f"work payload must contain exactly: {sorted(WORK_FIELDS)}")
        _nonempty(payload["desired_outcome"], "payload.desired_outcome")
        for field in (
            "authorized_actions",
            "excluded_scope",
            "input_refs",
            "protection_boundaries",
            "required_decisions",
            "verification_levels",
            "completed_items",
            "blockers",
            "evidence_refs",
        ):
            _string_list(payload[field], f"payload.{field}")
        next_action = payload["next_action"]
        if next_action is not None:
            _nonempty(next_action, "payload.next_action")
        status = block["status"]
        if status == "blocked" and not payload["blockers"]:
            raise DocumentDataError("blocked work requires at least one blocker")
        if status == "in_progress" and next_action is None:
            raise DocumentDataError("in_progress work requires next_action")
        if status == "completed" and next_action is not None:
            raise DocumentDataError("completed work requires next_action null")
        checkpoints = payload["checkpoints"]
        if not isinstance(checkpoints, list):
            raise DocumentDataError("payload.checkpoints must be a list")
        for checkpoint in checkpoints:
            fields = {"at", "actor", "summary", "evidence_refs"}
            if not isinstance(checkpoint, Mapping) or set(checkpoint) != fields:
                raise DocumentDataError(f"checkpoint must contain exactly: {sorted(fields)}")
            _utc(checkpoint["at"], "checkpoint.at")
            _nonempty(checkpoint["actor"], "checkpoint.actor")
            _nonempty(checkpoint["summary"], "checkpoint.summary")
            _string_list(checkpoint["evidence_refs"], "checkpoint.evidence_refs")

    def _validate_knowledge(self, block: Mapping[str, Any]) -> None:
        payload = block["payload"]
        if not isinstance(payload, Mapping) or set(payload) != KNOWLEDGE_FIELDS:
            raise DocumentDataError(
                f"knowledge payload must contain exactly: {sorted(KNOWLEDGE_FIELDS)}"
            )
        statement = _nonempty(payload["statement"], "payload.statement", 500)
        if "\n" in statement or "\r" in statement:
            raise DocumentDataError("payload.statement must be one line")
        if payload["classification"] not in KNOWLEDGE_CLASSES:
            raise DocumentDataError("payload.classification is invalid")
        _nonempty(payload["scope"], "payload.scope")
        verification = payload["verification_status"]
        if verification not in VERIFICATION_STATUSES:
            raise DocumentDataError("payload.verification_status is invalid")
        if verification == "verified":
            _nonempty(payload["verified_by"], "payload.verified_by")
        elif payload["verified_by"] is not None:
            raise DocumentDataError("candidate knowledge requires verified_by null")
        replacements = _string_list(
            payload["replaces_legacy_ids"],
            "payload.replaces_legacy_ids",
        )
        for index, replacement in enumerate(replacements):
            if _uuid_or_none(replacement, f"payload.replaces_legacy_ids[{index}]") is None:
                raise DocumentDataError("knowledge replacement IDs must be UUIDs")

    def _validate_decision(self, block: Mapping[str, Any]) -> None:
        payload = block["payload"]
        if not isinstance(payload, Mapping) or set(payload) != DECISION_FIELDS:
            raise DocumentDataError(
                f"decision payload must contain exactly: {sorted(DECISION_FIELDS)}"
            )
        _nonempty(payload["problem"], "payload.problem")
        _string_list(payload["requirements"], "payload.requirements", require_nonempty=True)
        _nonempty(payload["rationale"], "payload.rationale")
        _string_list(payload["impacts"], "payload.impacts", require_nonempty=True)
        options = payload["options"]
        if not isinstance(options, list) or len(options) < 2:
            raise DocumentDataError("payload.options must contain at least two options")
        labels: list[str] = []
        for option in options:
            if not isinstance(option, Mapping) or set(option) != {"label", "description"}:
                raise DocumentDataError("each option must contain label and description")
            labels.append(_nonempty(option["label"], "option.label"))
            _nonempty(option["description"], "option.description")
        if len(set(labels)) != len(labels):
            raise DocumentDataError("option labels must be unique")
        if payload["selected_option"] not in labels:
            raise DocumentDataError("payload.selected_option must name an option label")
        if not isinstance(payload["requires_user_approval"], bool):
            raise DocumentDataError("payload.requires_user_approval must be boolean")
        approval = payload["approval_kind"]
        if approval not in APPROVAL_KINDS:
            raise DocumentDataError("payload.approval_kind is invalid")
        if payload["requires_user_approval"] and approval not in {"user", "standing_policy"}:
            raise DocumentDataError("user-required decision needs user or standing_policy approval")
        _nonempty(payload["approved_by"], "payload.approved_by")
        _utc(payload["decided_at"], "payload.decided_at")
        _uuid_or_none(payload["replaces_legacy_id"], "payload.replaces_legacy_id")

    def _validate_block(
        self,
        block: dict[str, Any],
        *,
        marker_kind: str,
        marker_key: str,
        owner: str,
    ) -> dict[str, Any]:
        if set(block) != COMMON_FIELDS:
            raise DocumentDataError(f"project-data block must contain exactly: {sorted(COMMON_FIELDS)}")
        key = _nonempty(block["key"], "key", 100)
        kind = _nonempty(block["kind"], "kind")
        if KEY_PATTERN.fullmatch(key) is None or key != marker_key or kind != marker_kind:
            raise DocumentDataError("marker kind/key and JSON kind/key must match valid slugs")
        if not self._owner_allowed(kind, owner):
            raise DocumentDataError(f"{kind} block is not allowed in owner: {owner}")
        source_refs = _string_list(
            block["source_refs"],
            "source_refs",
        )
        for index, ref in enumerate(source_refs):
            self._source_ref(ref, f"source_refs[{index}]")
        if kind == "work":
            if block["status"] not in WORK_STATUSES:
                raise DocumentDataError("work status is invalid")
            self._validate_work(block)
        elif kind == "knowledge":
            if block["status"] not in KNOWLEDGE_STATUSES:
                raise DocumentDataError("knowledge status is invalid")
            self._validate_knowledge(block)
        elif kind == "decision":
            if block["status"] != "current":
                raise DocumentDataError("decision status must be current")
            self._validate_decision(block)
        else:
            raise DocumentDataError(f"unknown project-data kind: {kind}")
        return {**block, "owner": owner}

    def list_blocks(self) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        keys: set[str] = set()
        for path in _markdown_files(self.root):
            owner = path.relative_to(self.root).as_posix()
            text = _read_markdown(path)
            for marker, raw in _extract_blocks(text, DATA_MARKER, "<!-- /project-data -->"):
                block = self._validate_block(
                    _decode_json(raw, f"{owner} project-data"),
                    marker_kind=marker.group("kind"),
                    marker_key=marker.group("key"),
                    owner=owner,
                )
                if block["key"] in keys:
                    raise DocumentDataError(f"duplicate project-data key: {block['key']}")
                keys.add(block["key"])
                blocks.append(block)
        return sorted(blocks, key=lambda item: item["key"])

    def validate(self) -> dict[str, Any]:
        blocks = self.list_blocks()
        counts: dict[str, int] = {}
        for block in blocks:
            counts[block["kind"]] = counts.get(block["kind"], 0) + 1
        return {"blocks": len(blocks), "counts_by_kind": dict(sorted(counts.items()))}

    def get_block(self, key: str) -> dict[str, Any]:
        rendered = _nonempty(key, "key")
        for block in self.list_blocks():
            if block["key"] == rendered:
                return block
        raise DocumentDataError(f"project-data key not found: {rendered}")


class DocumentWorkService:
    """Atomically checkpoint the single active Markdown-owned work block."""

    HANDOFF_REF = "SESSION_HANDOFF.md"

    def __init__(self, project_root: Path | str) -> None:
        self.document_data = DocumentDataService(project_root)
        self.root = self.document_data.root
        self.target = self.root / self.HANDOFF_REF
        self.lock = self.root / f".{self.target.name}.lock"

    @staticmethod
    def _without_owner(block: Mapping[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in block.items() if key != "owner"}

    def get_work(self) -> dict[str, Any]:
        work = [
            block for block in self.document_data.list_blocks() if block["kind"] == "work"
        ]
        if len(work) != 1:
            raise DocumentDataError(
                f"expected exactly one active work block, found {len(work)}"
            )
        block = work[0]
        return {**block, "block_hash": _canonical_hash(self._without_owner(block))}

    def _validate_checkpoint_refs(self, refs: Sequence[str]) -> list[str]:
        rendered = _string_list(refs, "checkpoint.evidence_refs", require_nonempty=True)
        for index, ref in enumerate(rendered):
            self.document_data._source_ref(ref, f"checkpoint.evidence_refs[{index}]")
        return rendered

    def checkpoint(
        self,
        *,
        expected_hash: str,
        actor: str,
        summary: str,
        evidence_refs: Sequence[str],
        completed_items: Sequence[str] = (),
        next_action: str,
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        expected = _nonempty(expected_hash, "expected_hash")
        rendered_actor = _nonempty(actor, "actor")
        rendered_summary = _nonempty(summary, "summary")
        rendered_next = _nonempty(next_action, "next_action")
        rendered_evidence = self._validate_checkpoint_refs(evidence_refs)
        rendered_completed = _string_list(list(completed_items), "completed_items")
        current_time = timestamp or datetime.now(UTC)
        if current_time.tzinfo is None or current_time.utcoffset() is None:
            raise DocumentDataError("timestamp must be timezone-aware")
        rendered_time = current_time.astimezone(UTC).replace(microsecond=0).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        descriptor: int | None = None
        temporary: Path | None = None
        lock_acquired = False
        try:
            try:
                descriptor = os.open(
                    self.lock,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
            except FileExistsError as exc:
                raise ConcurrentWriteError(
                    f"document work lock already exists: {self.lock.name}"
                ) from exc
            os.close(descriptor)
            descriptor = None
            lock_acquired = True

            current = self.get_work()
            if current["block_hash"] != expected:
                raise ExpectationMismatchError(
                    f"expected work hash {expected}, found {current['block_hash']}"
                )
            updated = json.loads(
                json.dumps(self._without_owner(current), ensure_ascii=False, allow_nan=False)
            )
            updated.pop("block_hash", None)
            payload = updated["payload"]
            for item in rendered_completed:
                if item not in payload["completed_items"]:
                    payload["completed_items"].append(item)
            payload["next_action"] = rendered_next
            payload["checkpoints"].append(
                {
                    "at": rendered_time,
                    "actor": rendered_actor,
                    "summary": rendered_summary,
                    "evidence_refs": rendered_evidence,
                }
            )
            updated["status"] = "in_progress"
            validated = self.document_data._validate_block(
                updated,
                marker_kind="work",
                marker_key=updated["key"],
                owner=self.HANDOFF_REF,
            )

            original = _read_markdown(self.target)
            start, end = _data_block_content_span(original, updated["key"])
            rendered_json = json.dumps(
                updated,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            replacement = original[:start] + rendered_json + "\n" + original[end:]
            raw = replacement.encode("utf-8")
            file_descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.target.name}.",
                suffix=".tmp",
                dir=self.target.parent,
            )
            temporary = Path(temporary_name)
            with os.fdopen(file_descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())

            temporary_text = _read_markdown(temporary)
            temporary_start, temporary_end = _data_block_content_span(
                temporary_text, updated["key"]
            )
            temporary_block = _decode_json(
                temporary_text[temporary_start:temporary_end],
                f"{self.HANDOFF_REF} temporary work",
            )
            self.document_data._validate_block(
                temporary_block,
                marker_kind="work",
                marker_key=updated["key"],
                owner=self.HANDOFF_REF,
            )
            if temporary_block != self._without_owner(validated):
                raise DocumentDataError("temporary work block differs before replace")

            os.replace(temporary, self.target)
            temporary = None
            reread = self.get_work()
            expected_updated_hash = _canonical_hash(updated)
            if reread["block_hash"] != expected_updated_hash:
                raise DocumentDataError("document work post-write verification failed")
            return reread
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if lock_acquired:
                self.lock.unlink(missing_ok=True)


class ArtifactService:
    """Check and rebuild exact JSON artifacts from Markdown owner blocks."""

    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root).resolve(strict=True)

    def has_blocks(self) -> bool:
        return any(
            "<!-- project-artifact:v1 " in _read_markdown(path)
            for path in _markdown_files(self.root)
        )

    def _blocks(self) -> dict[str, dict[str, Any]]:
        blocks: dict[str, dict[str, Any]] = {}
        for path in _markdown_files(self.root):
            owner = path.relative_to(self.root).as_posix()
            text = _read_markdown(path)
            for marker, raw in _extract_blocks(
                text, ARTIFACT_MARKER, "<!-- /project-artifact -->"
            ):
                target = marker.group("path")
                if target not in ARTIFACT_OWNERS:
                    raise DocumentDataError(f"artifact target is not approved: {target}")
                if ARTIFACT_OWNERS[target] != owner:
                    raise DocumentDataError(
                        f"artifact target {target} must be owned by {ARTIFACT_OWNERS[target]}"
                    )
                if target in blocks:
                    raise DocumentDataError(f"duplicate artifact target: {target}")
                blocks[target] = _decode_json(raw, f"{owner} artifact {target}")
        missing = sorted(set(ARTIFACT_OWNERS) - set(blocks))
        if missing:
            raise DocumentDataError("missing artifact blocks: " + ", ".join(missing))
        return blocks

    def check(self) -> dict[str, Any]:
        blocks = self._blocks()
        drift: list[str] = []
        for target, expected in sorted(blocks.items()):
            path = self.root / Path(target)
            if not path.is_file():
                drift.append(target)
                continue
            actual = _decode_json(_read_markdown(path), target)
            if actual != expected:
                drift.append(target)
        if drift:
            raise DocumentDataError("artifact semantic drift: " + ", ".join(drift))
        return {"artifacts": len(blocks), "drift": []}

    def rebuild(self, target: str) -> dict[str, Any]:
        blocks = self._blocks()
        if target not in blocks:
            raise DocumentDataError(f"artifact target is not approved: {target}")
        path = self.root / Path(target)
        if not path.parent.is_dir():
            raise DocumentDataError(f"artifact parent does not exist: {target}")
        rendered = (
            json.dumps(blocks[target], ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n"
        ).encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(rendered)
                stream.flush()
                os.fsync(stream.fileno())
            if _decode_json(temporary.read_text(encoding="utf-8"), target) != blocks[target]:
                raise DocumentDataError(f"artifact temporary verification failed: {target}")
            os.replace(temporary, path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        digest = hashlib.sha256(rendered).hexdigest()
        return {"target": target, "sha256": digest, "bytes": len(rendered)}
