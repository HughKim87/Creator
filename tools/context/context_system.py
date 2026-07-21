"""Deterministic task-scoped context, corpus, and lifecycle system.

This module uses only the Python standard library. Markdown and JSON/JSONL are
the canonical project artifacts; catalogs and work contexts are deterministic
views with explicit integrity policies.
"""

from __future__ import annotations

import argparse
import ast
import base64
import configparser
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import tomllib
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator
from urllib.parse import unquote


SCHEMA_VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_TOP_LEVEL = {"backup", "inputs", "outputs", ".git", ".agents", ".codex"}
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
ATOMIC_TEMP_PREFIX = ".context-system-"
ATOMIC_TEMP_SUFFIX = ".tmp"
REPOSITORY_LOCK_NAME = ".context-system.lock"
REPOSITORY_LOCK_TIMEOUT_SECONDS = 60.0
CONTEXT_ARTIFACT_PREFIXES = ("context/requests/", "context/work/", "context/payloads/")
MAX_UNIT_PROJECTION_COUNT = 5_000
MAX_UNIT_PROJECTION_BYTES = 8 * 1024 * 1024
CATALOG_PROJECTIONS = {
    "catalog/files.jsonl",
    "catalog/records.jsonl",
    "catalog/rules.jsonl",
    "catalog/units.jsonl",
}
CORPUS_JSONL_PATHS = ["knowledge/decisions.jsonl", "knowledge/items.jsonl"]
SOURCE_STORE_PATH = "knowledge/sources.jsonl"
RELATION_STORE_PATH = "knowledge/relations.jsonl"
REVIEW_STORE_PATH = "knowledge/reviews.jsonl"
REVISION_STORE_PATH = "knowledge/revisions.jsonl"
CASE_ROOT = "knowledge/cases"
BINARY_SUFFIXES = {
    ".bin", ".gif", ".jpeg", ".jpg", ".mp3", ".mp4", ".pdf", ".png", ".wav", ".webp", ".zip"
}
CONFIG_SUFFIXES = {".cfg", ".ini", ".toml", ".yaml", ".yml"}
KERNEL_RULE_IDS = [
    "rule.core.authority-order",
    "rule.core.scope-authority",
    "rule.core.backup-boundary",
    "rule.core.protected-route",
    "rule.core.minimum-access",
    "rule.core.secret-boundary",
    "rule.core.instruction-trust",
    "rule.core.external-mutation",
]
RULE_PACK_PATHS = [
    "rules/governance.md",
    "rules/version-control.md",
    "rules/documentation.md",
    "rules/provenance.md",
    "rules/knowledge.md",
    "rules/retrieval.md",
    "rules/validation.md",
]
_PROCESS_LOCKS: dict[str, threading.RLock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()
_THREAD_LOCK_STATE = threading.local()


class ContextSystemError(RuntimeError):
    """Raised when scope, contract, or integrity validation fails."""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def _process_lock_for(key: str) -> threading.RLock:
    with _PROCESS_LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault(key, threading.RLock())


def _try_lock_file(handle: Any) -> bool:
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock_file(handle: Any) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def repository_lock(
    root: Path = PROJECT_ROOT,
    timeout_seconds: float = REPOSITORY_LOCK_TIMEOUT_SECONDS,
) -> Iterator[None]:
    """Serialize context-system operations across threads and processes."""
    root = root.resolve()
    key = str(root)
    process_lock = _process_lock_for(key)
    if not process_lock.acquire(timeout=max(timeout_seconds, 0.0)):
        raise ContextSystemError(f"repository lock timeout after {timeout_seconds:.1f}s: {root}")

    held = getattr(_THREAD_LOCK_STATE, "held", set())
    if key in held:
        try:
            yield
        finally:
            process_lock.release()
        return

    handle = None
    acquired = False
    try:
        lock_path = root / "catalog" / REPOSITORY_LOCK_NAME
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + max(timeout_seconds, 0.0)
        while not (acquired := _try_lock_file(handle)):
            if time.monotonic() >= deadline:
                raise ContextSystemError(
                    f"repository lock timeout after {timeout_seconds:.1f}s: {lock_path.relative_to(root).as_posix()}"
                )
            time.sleep(0.05)
        held.add(key)
        _THREAD_LOCK_STATE.held = held
        yield
    finally:
        try:
            if acquired and handle is not None:
                held.discard(key)
                _unlock_file(handle)
        finally:
            try:
                if handle is not None:
                    handle.close()
            finally:
                process_lock.release()


def is_internal_transient_path(value: str | Path) -> bool:
    path = PurePosixPath(normalize_path(value))
    if path.name == REPOSITORY_LOCK_NAME:
        return True
    if path.name.startswith(ATOMIC_TEMP_PREFIX) and path.name.endswith(ATOMIC_TEMP_SUFFIX):
        return True
    return path.parent.as_posix() == "catalog" and path.name.startswith("tmp")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize_path(value: str | Path, root: Path = PROJECT_ROOT) -> str:
    path = Path(value)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root.resolve())
        except ValueError as exc:
            raise ContextSystemError(f"path is outside project root: {value}") from exc
    result = path.as_posix()
    while result.startswith("./"):
        result = result[2:]
    if not result or result == ".":
        raise ContextSystemError("empty project-relative path")
    return result


def assert_allowed_path(value: str | Path, root: Path = PROJECT_ROOT) -> str:
    normalized = normalize_path(value, root)
    parts = PurePosixPath(normalized).parts
    if any(part in PROTECTED_TOP_LEVEL for part in parts):
        raise ContextSystemError(f"protected path rejected before traversal: {normalized}")
    if ".." in parts:
        raise ContextSystemError(f"parent traversal rejected: {normalized}")
    return normalized


def normalize_authorized_protected_scope(value: str | Path, root: Path = PROJECT_ROOT) -> str:
    """Validate one exact task namespace below inputs/ or outputs/."""
    normalized = normalize_path(value, root)
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise ContextSystemError(f"parent traversal rejected: {normalized}")
    if len(parts) < 2 or parts[0] not in {"inputs", "outputs"}:
        raise ContextSystemError(f"protected task scope must be an exact inputs/ or outputs/ namespace: {normalized}")
    if any(part in {"backup", ".git", ".agents", ".codex"} for part in parts[1:]):
        raise ContextSystemError(f"nested protected boundary rejected: {normalized}")
    return normalized.rstrip("/")


def protected_scope_for(
    value: str | Path,
    authorized_protected_scopes: Iterable[str],
    root: Path = PROJECT_ROOT,
) -> str | None:
    normalized = normalize_path(value, root)
    path = PurePosixPath(normalized)
    for raw_scope in authorized_protected_scopes:
        scope = normalize_authorized_protected_scope(raw_scope, root)
        scope_path = PurePosixPath(scope)
        if path == scope_path or scope_path in path.parents:
            return scope
    return None


def assert_task_scoped_path(
    value: str | Path,
    root: Path = PROJECT_ROOT,
    authorized_protected_scopes: Iterable[str] = (),
) -> str:
    """Allow a protected path only inside an explicitly authorized exact task scope."""
    normalized = normalize_path(value, root)
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise ContextSystemError(f"parent traversal rejected: {normalized}")
    if parts and parts[0] in {"inputs", "outputs"}:
        if not protected_scope_for(normalized, authorized_protected_scopes, root):
            raise ContextSystemError(f"protected path is outside the authorized task namespace: {normalized}")
        return normalized
    return assert_allowed_path(normalized, root)


def iter_project_files(root: Path = PROJECT_ROOT) -> list[str]:
    """Return governed files without traversing protected directories."""
    root = root.resolve()
    results: list[str] = []
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        if relative == Path("."):
            directories[:] = sorted(
                name
                for name in directories
                if name not in PROTECTED_TOP_LEVEL and name not in IGNORED_DIRS
            )
        else:
            directories[:] = sorted(name for name in directories if name not in IGNORED_DIRS)
        for filename in sorted(filenames):
            path = current_path / filename
            if path.suffix.lower() in IGNORED_SUFFIXES:
                continue
            normalized = path.relative_to(root).as_posix()
            if is_internal_transient_path(normalized):
                continue
            assert_allowed_path(normalized, root)
            results.append(normalized)
    return sorted(results)


def read_utf8(path: Path) -> str:
    data = path.read_bytes()
    if b"\x00" in data:
        raise ContextSystemError(f"NUL byte found: {path}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContextSystemError(f"invalid UTF-8: {path}") from exc


def _replace_atomic(temporary: Path, path: Path, attempts: int = 5) -> None:
    from time import sleep

    if attempts < 1:
        raise ValueError("atomic replace attempts must be positive")
    try:
        for attempt in range(attempts):
            try:
                os.replace(temporary, path)
                return
            except PermissionError:
                if attempt == attempts - 1:
                    raise
                sleep(0.05 * (2**attempt))
    except Exception as replace_error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError as cleanup_error:
            raise ContextSystemError(
                f"atomic replace failed for {path}: {replace_error}; "
                f"temporary cleanup failed for {temporary}: {cleanup_error}"
            ) from replace_error
        raise


def write_text_atomic(path: Path, content: str) -> None:
    if "\x00" in content:
        raise ContextSystemError(f"refusing NUL content: {path}")
    content.encode("utf-8", errors="strict")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False,
        prefix=ATOMIC_TEMP_PREFIX, suffix=ATOMIC_TEMP_SUFFIX,
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    _replace_atomic(temporary, path)


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", dir=path.parent, delete=False,
        prefix=ATOMIC_TEMP_PREFIX, suffix=ATOMIC_TEMP_SUFFIX,
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    _replace_atomic(temporary, path)


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(read_utf8(path))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_utf8(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContextSystemError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ContextSystemError(f"JSONL record is not an object: {path}:{line_number}")
        records.append(value)
    return records


def write_jsonl_atomic(path: Path, records: Iterable[dict[str, Any]]) -> None:
    lines = [canonical_json(record) for record in records]
    write_text_atomic(path, "\n".join(lines) + ("\n" if lines else ""))


def ascii_slug(value: str) -> str:
    slug = value.lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9.-]+", "-", slug).strip("-.")
    return slug


def stable_slug(value: str) -> str:
    slug = ascii_slug(value)
    return slug or f"id-{sha256_text(value)[:12]}"


def file_id_for_path(path: str) -> str:
    normalized = normalize_path(path)
    without_suffix = str(PurePosixPath(normalized).with_suffix(""))
    original_parts = PurePosixPath(without_suffix).parts
    parts = [ascii_slug(part) for part in original_parts]
    usable = [part for part in parts if part]
    if len(usable) != len(parts) or any(not part.isascii() for part in original_parts):
        usable.append(f"id-{sha256_text(normalized)[:12]}")
    return "file." + ".".join(usable)


def detect_language(path: Path) -> str:
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".py"} or not path.exists():
        return "und"
    text = read_utf8(path)
    if path.suffix.lower() in {".json", ".jsonl", ".py"}:
        return "en"
    return "ko" if re.search(r"[가-힣]", text) else "en"


def classify_file(
    path: str,
    root: Path = PROJECT_ROOT,
    status: str = "active",
    existing_record: dict[str, Any] | None = None,
    authorized_protected_scopes: Iterable[str] = (),
) -> dict[str, Any]:
    normalized = assert_task_scoped_path(path, root, authorized_protected_scopes)
    task_protected = protected_scope_for(normalized, authorized_protected_scopes, root) is not None
    full_path = root / normalized
    suffix = full_path.suffix.lower()
    kind = "project_file"
    purpose = "Governed project artifact."
    owner = "project_agents"
    authority = "supporting"
    read_when = ["exact_task_route"]
    write_when = ["valid_write_contract"]
    task_tags: list[str] = []
    consumes: list[str] = []
    produces: list[str] = []
    depends_on: list[str] = []

    special: dict[str, tuple[str, str, str, str, list[str], list[str]]] = {
        "AGENTS.md": ("router", "Route mandatory startup and task context.", "project_agents", "active_router", ["conversation_start"], ["user_approved_authority_change"]),
        "PROJECT_RULES.md": ("policy", "Hold the eight-rule boot kernel.", "user", "active_policy", ["conversation_start"], ["user_approved_policy_change"]),
        "SESSION_HANDOFF.md": ("current_state", "Hold the only resumable project checkpoint.", "project_agents", "active_current_state", ["conversation_start", "task_resume"], ["task_close_with_valid_contract"]),
        "docs/agent/DOCUMENT_MAP.md": ("router_registry", "Route active maintained documents and authority.", "project_agents", "active_router", ["document_selection", "document_creation"], ["document_registry_change"]),
        "docs/agent/WORKFLOW.md": ("procedure", "Define the common project work procedure.", "project_agents", "active_procedure", ["project_task"], ["approved_procedure_change"]),
        "docs/agent/KNOWLEDGE_SYSTEM.md": ("technical_contract", "Define canonical knowledge and provenance behavior.", "project_agents", "active_contract", ["knowledge_system_change"], ["approved_contract_change"]),
        "docs/agent/CONTEXT_RETRIEVAL.md": ("technical_contract", "Define task-scoped context selection behavior.", "project_agents", "active_contract", ["context_or_retrieval_work"], ["approved_contract_change"]),
        "docs/agent/KNOWLEDGE_MAINTENANCE.md": ("technical_contract", "Define review and maintenance behavior.", "project_agents", "active_contract", ["maintenance_or_review_work"], ["approved_contract_change"]),
        "catalog/bootstrap.json": ("bootstrap_evidence", "Preserve the R-2A pre-migration inventory and 29-rule mapping.", "project_agents", "retained_evidence", ["r2a_audit"], ["never_after_bootstrap"]),
        "catalog/files.jsonl": ("file_catalog", "Canonical registry of project-governed files.", "context_system", "canonical", ["context_resolution", "validation"], ["context_system_only"]),
        "catalog/records.jsonl": ("record_projection", "Rebuildable projection of decision, knowledge, and case records.", "context_system", "derived", ["record_resolution", "validation"], ["context_system_only"]),
        "catalog/rules.jsonl": ("rule_projection", "Rebuildable projection of conditional rule records.", "context_system", "derived", ["context_resolution", "validation"], ["context_system_only"]),
        "catalog/units.jsonl": ("unit_projection", "Rebuildable projection of addressable artifact units.", "context_system", "derived", ["context_resolution", "validation"], ["context_system_only"]),
        "records/work/events.jsonl": ("event_store", "Append-only R-2A work evidence chain.", "context_system", "canonical", ["validation", "task_audit"], ["append_only_context_system"]),
        "tools/context/context_system.py": ("code", "Implement deterministic parsing, cataloging, corpus resolution, lifecycle maintenance, validation, and contract-gated writing.", "project_agents", "active_implementation", ["context_system_execution"], ["approved_implementation_change"]),
        "tests/context/test_context_system.py": ("test", "Verify context, corpus, lifecycle, recovery, and retrieval contracts.", "project_agents", "active_test", ["context_system_validation"], ["test_maintenance"]),
        REVIEW_STORE_PATH: ("review_store", "Hold append-only knowledge and source review evidence.", "context_system", "canonical", ["knowledge_review", "source_review"], ["append_only_context_system"]),
        REVISION_STORE_PATH: ("revision_store", "Hold append-only record revision history.", "context_system", "canonical", ["knowledge_review", "record_audit"], ["append_only_context_system"]),
    }
    if normalized in special:
        kind, purpose, owner, authority, read_when, write_when = special[normalized]
        if normalized == "tools/context/context_system.py":
            task_tags = ["context", "implementation", "lifecycle", "retrieval"]
        elif normalized == "tests/context/test_context_system.py":
            task_tags = ["context", "test", "validation"]
    elif normalized.startswith("rules/") and suffix == ".md":
        kind, purpose, owner, authority = "rule_pack", "Hold resolver-selected conditional project rules.", "user", "active_policy"
        read_when, write_when = ["selected_rule_predicate"], ["user_approved_policy_change"]
        task_tags = ["rules", "policy"]
    elif normalized.startswith("schemas/") and suffix == ".json":
        kind, purpose, owner, authority = "schema", "Define a machine-readable R-2A data contract.", "project_agents", "active_contract"
        read_when, write_when = ["schema_validation", "implementation_change"], ["approved_contract_change"]
        task_tags = ["schema", "validation"]
    elif normalized.startswith("context/requests/") and suffix == ".json":
        kind, purpose, owner, authority = "task_request", "Preserve an immutable structured task request.", "requester", "canonical"
        read_when, write_when = ["matching_task_resolution"], ["create_once"]
        task_tags = ["context", "request"]
    elif normalized.startswith("context/work/") and suffix == ".json":
        kind, purpose, owner, authority = "work_context", "Preserve a resolved task-scoped context and write contract.", "context_system", "derived"
        read_when, write_when = ["matching_task_execution", "validation"], ["context_system_only"]
        task_tags = ["context", "work_context"]
    elif normalized.startswith("context/payloads/") and suffix == ".json":
        kind, purpose, owner, authority = "write_fixture", "Preserve an R-2A live write-fixture payload.", "project_agents", "retained_evidence"
        read_when, write_when = ["matching_write_fixture", "r2a_audit"], ["fixture_definition"]
        task_tags = ["context", "fixture"]
    elif normalized.startswith("evaluation/retrieval/") and suffix == ".json":
        if normalized.endswith("_queries.json"):
            kind, purpose, owner, authority = "retrieval_evaluation", "Hold a fixed source-traceable retrieval evaluation set.", "project_agents", "canonical"
            read_when, write_when = ["retrieval_evaluation"], ["approved_evaluation_change"]
        else:
            kind, purpose, owner, authority = "retrieval_result", "Hold a rebuildable measured retrieval evaluation result.", "context_system", "derived"
            read_when, write_when = ["retrieval_audit"], ["context_system_only"]
        task_tags = ["retrieval", "evaluation"]
    elif normalized.startswith("evaluation/operations/") and suffix == ".json":
        if normalized.endswith("_acceptance.json"):
            kind, purpose, owner, authority = "operational_acceptance", "Hold the fixed R-5 operational acceptance scenarios and expected outcomes.", "project_agents", "canonical"
            read_when, write_when = ["operational_acceptance"], ["approved_evaluation_change"]
        else:
            kind, purpose, owner, authority = "operational_acceptance_result", "Hold rebuildable R-5 operational acceptance evidence.", "context_system", "derived"
            read_when, write_when = ["operational_acceptance_audit"], ["context_system_only"]
        task_tags = ["operations", "acceptance", "validation"]
    elif normalized.startswith("docs/reports/") or normalized.startswith("reports/"):
        kind, purpose, owner, authority = "report", "Preserve point-in-time project evidence and validation.", "project_agents", "evidence"
        read_when, write_when = ["exact_provenance_or_stage_route"], ["unique_point_in_time_evidence_with_contract"]
        task_tags = ["documentation", "report"]
    elif normalized.startswith("docs/user/") or normalized == "README.md":
        kind, purpose, owner, authority = "user_guide", "Provide maintained user-facing project guidance.", "project_agents", "maintained_projection"
        read_when, write_when = ["user_orientation"], ["guide_projection_update"]
        task_tags = ["documentation", "user_facing"]
    elif normalized.startswith("knowledge/cases/"):
        kind, purpose, owner, authority = "case", "Preserve a source-traceable problem and resolution case.", "project_agents", "canonical"
        read_when, write_when = ["exact_case_trigger"], ["authorized_case_review"]
        task_tags = ["knowledge", "case"]
    elif normalized == "knowledge/decisions.jsonl":
        kind, purpose, owner, authority = "decision_store", "Hold accepted project decisions as independent records.", "project_agents", "canonical"
        read_when, write_when = ["exact_decision_route"], ["authorized_decision_migration"]
        task_tags = ["knowledge", "decision"]
    elif normalized == "knowledge/items.jsonl":
        kind, purpose, owner, authority = "knowledge_store", "Hold verified source-traceable project knowledge.", "project_agents", "canonical"
        read_when, write_when = ["exact_knowledge_route"], ["authorized_knowledge_review"]
        task_tags = ["knowledge"]
    elif normalized == SOURCE_STORE_PATH:
        kind, purpose, owner, authority = "source_store", "Hold stable source locators and integrity observations.", "project_agents", "canonical"
        read_when, write_when = ["source_trace"], ["authorized_source_review"]
        task_tags = ["knowledge", "source", "provenance"]
    elif normalized == RELATION_STORE_PATH:
        kind, purpose, owner, authority = "relation_store", "Hold verified typed one-hop corpus relations and inactive candidates.", "project_agents", "canonical"
        read_when, write_when = ["record_one_hop"], ["authorized_relation_review"]
        task_tags = ["knowledge", "relation"]
    elif normalized.startswith("records/sessions/"):
        kind, purpose, owner, authority = "session_record", "Preserve a closed historical session record.", "project_agents", "retained_evidence"
        read_when, write_when = ["exact_history_route"], ["create_once"]
        task_tags = ["session", "history"]

    if suffix == ".md":
        unit_strategy = "markdown_heading"
        validators = ["validate.utf8", "validate.nul", "validate.markdown", "validate.links"]
    elif suffix == ".json":
        unit_strategy = "json_pointer"
        validators = ["validate.utf8", "validate.nul", "validate.json"]
    elif suffix == ".jsonl":
        unit_strategy = "whole_file" if normalized in CATALOG_PROJECTIONS else "jsonl_record_id"
        validators = ["validate.utf8", "validate.nul", "validate.jsonl"]
    elif suffix == ".py":
        unit_strategy = "test_symbol" if normalized.startswith("tests/") or full_path.name.startswith("test_") else "code_symbol"
        validators = ["validate.utf8", "validate.nul", "validate.python_compile"]
    elif suffix in CONFIG_SUFFIXES:
        unit_strategy = "key_path"
        validators = ["validate.utf8", "validate.nul", "validate.config"]
    elif suffix in BINARY_SUFFIXES:
        unit_strategy = "binary_sidecar"
        validators = ["validate.content_hash", "validate.binary_sidecar"]
    else:
        unit_strategy = "whole_file"
        validators = ["validate.content_hash"]

    if normalized.startswith(CONTEXT_ARTIFACT_PREFIXES):
        # Requests, resolved work contexts, and write payloads are exact-route
        # task evidence. One file-level unit preserves addressability without
        # recursively projecting thousands of internal JSON pointers.
        unit_strategy = "whole_file"

    relation_paths: dict[str, list[str]] = {
        "AGENTS.md": ["PROJECT_RULES.md", "SESSION_HANDOFF.md", "docs/agent/DOCUMENT_MAP.md"],
        "SESSION_HANDOFF.md": ["PROJECT_RULES.md", "docs/agent/DOCUMENT_MAP.md", "docs/agent/WORKFLOW.md"],
        "docs/agent/DOCUMENT_MAP.md": ["AGENTS.md", "PROJECT_RULES.md"],
        "docs/agent/CONTEXT_RETRIEVAL.md": ["PROJECT_RULES.md", "docs/agent/DOCUMENT_MAP.md", "docs/agent/KNOWLEDGE_SYSTEM.md", "docs/agent/KNOWLEDGE_MAINTENANCE.md"],
        "docs/agent/KNOWLEDGE_SYSTEM.md": ["PROJECT_RULES.md", "docs/agent/CONTEXT_RETRIEVAL.md", "docs/agent/KNOWLEDGE_MAINTENANCE.md"],
        "docs/agent/KNOWLEDGE_MAINTENANCE.md": ["docs/agent/KNOWLEDGE_SYSTEM.md", "docs/agent/CONTEXT_RETRIEVAL.md"],
        "catalog/bootstrap.json": ["PROJECT_RULES.md", "docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md"],
        "docs/reports/2026-07-20_R-2A_컨텍스트_시스템_구현_결과.md": [
            "docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md",
            "docs/agent/WORKFLOW.md",
            "docs/agent/DOCUMENT_MAP.md",
            "knowledge/cases/case.project.document-authority-duplication.md",
        ],
        "tools/context/context_system.py": ["catalog/files.jsonl", "catalog/records.jsonl", "catalog/rules.jsonl", "catalog/units.jsonl"],
        "tests/context/test_context_system.py": ["tools/context/context_system.py"],
    }
    depends_on = [file_id_for_path(item) for item in relation_paths.get(normalized, [])]
    if normalized.startswith("rules/"):
        depends_on = [file_id_for_path("PROJECT_RULES.md")]
    elif normalized.startswith("schemas/"):
        depends_on = [file_id_for_path("docs/agent/KNOWLEDGE_SYSTEM.md")]
    elif normalized.startswith("context/work/"):
        consumes = ["catalog/files.jsonl", "catalog/rules.jsonl", "catalog/units.jsonl"]
        produces = [normalized]

    if status == "planned":
        content_hash = None
        hash_policy = "planned"
        runtime_hash = None
        language = "ko" if normalized.startswith("docs/reports/") else "en"
    elif normalized == "catalog/files.jsonl":
        content_hash = None
        hash_policy = "catalog_runtime_hash"
        runtime_hash = None
        language = "en"
    elif normalized in {"catalog/rules.jsonl", "catalog/units.jsonl"}:
        content_hash = None
        hash_policy = "projection_runtime_hash"
        runtime_hash = sha256_file(full_path) if full_path.exists() else None
        language = "en"
    else:
        content_hash = sha256_file(full_path) if full_path.exists() else None
        hash_policy = "content_sha256" if full_path.exists() else "planned"
        runtime_hash = None
        language = detect_language(full_path)

    observed_at = now_iso()
    if existing_record and existing_record.get("status") == status:
        previous_hash = existing_record.get("content_sha256") or existing_record.get("runtime_hash")
        current_hash = content_hash or runtime_hash
        if previous_hash == current_hash:
            observed_at = existing_record.get("observed_at", observed_at)
    if task_protected:
        purpose = "Task-scoped protected artifact; never globally cataloged or indexed."
        owner = "requester"
        authority = "task_scoped_input" if normalized.startswith("inputs/") else "task_scoped_output"
        read_when = ["exact_authorized_task_scope"]
        write_when = ["same_task_write_contract_before_scope_close"]
        task_tags = sorted(set(task_tags) | {"protected", "task_scope"})
        depends_on = []
    return {
        "schema_version": SCHEMA_VERSION,
        "file_id": existing_record.get("file_id", file_id_for_path(normalized)) if existing_record else file_id_for_path(normalized),
        "path": normalized,
        "kind": kind,
        "purpose": purpose,
        "owner": owner,
        "authority": authority,
        "status": status,
        "language": language,
        "sensitivity": "protected_task" if task_protected else "public_project",
        "index_scope": "task" if task_protected else ("none" if authority in {"derived", "retained_evidence"} else "global"),
        "read_when": read_when,
        "write_when": write_when,
        "task_tags": task_tags,
        "unit_strategy": unit_strategy,
        "unit_overrides": [],
        "consumes": consumes,
        "produces": produces,
        "depends_on": depends_on,
        "validators": validators,
        "content_sha256": content_hash,
        "hash_policy": hash_policy,
        "runtime_hash": runtime_hash,
        "observed_at": observed_at,
        "moved_from": list(existing_record.get("moved_from", [])) if existing_record else [],
    }


RULE_BLOCK_PATTERN = re.compile(
    r"^## (?P<heading>rule\.[^\r\n]+)\r?\n(?P<body>.*?)(?=^## rule\.|\Z)", re.MULTILINE | re.DOTALL
)
JSON_FENCE_PATTERN = re.compile(r"```json\s*\r?\n(?P<json>.*?)\r?\n```", re.DOTALL)


def parse_rule_packs(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for relative in RULE_PACK_PATHS:
        path = root / relative
        text = read_utf8(path)
        for match in RULE_BLOCK_PATTERN.finditer(text):
            fence = JSON_FENCE_PATTERN.search(match.group("body"))
            if not fence:
                raise ContextSystemError(f"missing JSON rule block: {relative}#{match.group('heading')}")
            try:
                record = json.loads(fence.group("json"))
            except json.JSONDecodeError as exc:
                raise ContextSystemError(f"invalid rule JSON: {relative}: {exc}") from exc
            if record.get("rule_id") != match.group("heading"):
                raise ContextSystemError(f"rule heading/ID mismatch: {relative}#{match.group('heading')}")
            if record["rule_id"] in seen:
                raise ContextSystemError(f"duplicate rule ID: {record['rule_id']}")
            seen.add(record["rule_id"])
            record = dict(record)
            record["pack_path"] = relative
            records.append(record)
    return sorted(records, key=lambda item: item["rule_id"])


def build_rule_projection(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    records = parse_rule_packs(root)
    write_jsonl_atomic(root / "catalog/rules.jsonl", records)
    return records


def markdown_units(text: str, file_record: dict[str, Any]) -> list[dict[str, Any]]:
    headings: list[tuple[int, int, str]] = []
    active_fence: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            signature = (marker[0], len(marker))
            if active_fence is None:
                active_fence = signature
            elif active_fence[0] == signature[0] and signature[1] >= active_fence[1]:
                active_fence = None
            offset += len(line)
            continue
        if active_fence is None:
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*(?:\r?\n)?$", line)
            if heading:
                headings.append((offset, len(heading.group(1)), heading.group(2).strip()))
        offset += len(line)
    if not headings:
        return [whole_file_unit(text, file_record)]
    stack: list[str] = []
    used: dict[str, int] = {}
    units: list[dict[str, Any]] = []
    for index, (start, depth, title) in enumerate(headings):
        stack = stack[: depth - 1]
        stack.append(title)
        end = len(text)
        for candidate_start, candidate_depth, _ in headings[index + 1 :]:
            if candidate_depth <= depth:
                end = candidate_start
                break
        content = text[start:end].rstrip() + "\n"
        locator = "heading:" + " > ".join(stack)
        slug_path = ".".join(stable_slug(item) for item in stack)
        base = f"unit.{file_record['file_id']}.heading.{slug_path}"
        used[base] = used.get(base, 0) + 1
        unit_id = base if used[base] == 1 else f"{base}.{used[base]}"
        units.append(make_unit(file_record, unit_id, "markdown_heading", locator, title, content))
    return units


def json_pointer_units(value: Any, file_record: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    def visit(current: Any, pointer: str) -> None:
        locator = pointer or "/"
        suffix = "root" if not pointer else stable_slug(pointer.replace("/", "."))
        content = canonical_json(current)
        units.append(
            make_unit(
                file_record,
                f"unit.{file_record['file_id']}.json.{suffix}",
                "json_pointer",
                locator,
                f"JSON pointer {locator}",
                content,
            )
        )
        if isinstance(current, dict):
            for key in sorted(current):
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                visit(current[key], f"{pointer}/{escaped}")
        elif isinstance(current, list):
            for index, item in enumerate(current):
                visit(item, f"{pointer}/{index}")

    visit(value, "")
    return units


def jsonl_units(records: list[dict[str, Any]], file_record: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    id_fields = ("decision_id", "knowledge_id", "case_id", "source_id", "relation_id", "review_id", "revision_id", "file_id", "rule_id", "unit_id", "event_id", "task_id", "context_id", "id")
    seen: set[str] = set()
    for record in records:
        record_id = next((str(record[field]) for field in id_fields if record.get(field)), None)
        if not record_id:
            raise ContextSystemError(f"JSONL record lacks stable ID: {file_record['path']}")
        if record_id in seen:
            raise ContextSystemError(f"duplicate JSONL record ID {record_id}: {file_record['path']}")
        seen.add(record_id)
        units.append(
            make_unit(
                file_record,
                f"unit.{file_record['file_id']}.record.{stable_slug(record_id)}",
                "jsonl_record_id",
                f"record:{record_id}",
                record_id,
                canonical_json(record),
            )
        )
    return units


def code_symbol_units(text: str, file_record: dict[str, Any], tests_only: bool = False) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [whole_file_unit(text, file_record)]
    lines = text.splitlines(keepends=True)
    symbols: list[tuple[str, ast.AST, str]] = []

    def visit(body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = f"{prefix}.{node.name}" if prefix else node.name
                is_test = node.name.startswith("test_") or node.name.startswith("Test") or prefix.startswith("Test")
                if not tests_only or is_test:
                    locator_type = "test_symbol" if tests_only and is_test else "code_symbol"
                    symbols.append((qualified, node, locator_type))
                if isinstance(node, ast.ClassDef):
                    visit(node.body, qualified)

    visit(tree.body)
    if not symbols:
        return [whole_file_unit(text, file_record)]
    units: list[dict[str, Any]] = []
    for qualified, node, locator_type in symbols:
        start = max(getattr(node, "lineno", 1) - 1, 0)
        end = getattr(node, "end_lineno", start + 1)
        content = "".join(lines[start:end])
        units.append(
            make_unit(
                file_record,
                f"unit.{file_record['file_id']}.symbol.{stable_slug(qualified)}",
                locator_type,
                f"symbol:{qualified}",
                qualified,
                content,
            )
        )
    return units


def _config_value_units(value: Any, file_record: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    def visit(current: Any, parts: list[str]) -> None:
        if parts:
            locator = ".".join(parts)
            units.append(
                make_unit(
                    file_record,
                    f"unit.{file_record['file_id']}.key.{stable_slug(locator)}",
                    "key_path",
                    f"key:{locator}",
                    locator,
                    canonical_json(current),
                )
            )
        if isinstance(current, dict):
            for key in sorted(current):
                visit(current[key], [*parts, str(key)])
        elif isinstance(current, list):
            for index, item in enumerate(current):
                visit(item, [*parts, str(index)])

    visit(value, [])
    return units or [whole_file_unit(canonical_json(value), file_record)]


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.lstrip().startswith("-") or "\t" in raw:
            raise ContextSystemError("complex YAML requires whole-file fallback")
        match = re.match(r"^(\s*)([A-Za-z0-9_.-]+):(?:\s*(.*))?$", raw)
        if not match:
            raise ContextSystemError("unsupported YAML syntax requires whole-file fallback")
        indent = len(match.group(1))
        key = match.group(2)
        value = (match.group(3) or "").strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if key in parent:
            raise ContextSystemError(f"duplicate YAML key: {key}")
        if value:
            if value in {"true", "false"}:
                parsed: Any = value == "true"
            elif value in {"null", "~"}:
                parsed = None
            elif re.fullmatch(r"-?\d+", value):
                parsed = int(value)
            else:
                parsed = value.strip("\"'")
            parent[key] = parsed
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def config_key_units(text: str, file_record: dict[str, Any], suffix: str) -> list[dict[str, Any]]:
    try:
        if suffix == ".toml":
            value: Any = tomllib.loads(text)
        elif suffix in {".ini", ".cfg"}:
            parser = configparser.ConfigParser()
            parser.read_string(text)
            value = {section: dict(parser.items(section)) for section in parser.sections()}
            if parser.defaults():
                value["DEFAULT"] = dict(parser.defaults())
        else:
            value = _parse_simple_yaml(text)
    except (ValueError, configparser.Error, ContextSystemError, tomllib.TOMLDecodeError):
        return [whole_file_unit(text, file_record)]
    return _config_value_units(value, file_record)


def binary_sidecar_unit(root: Path, path: Path, file_record: dict[str, Any]) -> dict[str, Any]:
    sidecar = path.with_name(path.name + ".sidecar.json")
    if sidecar.exists():
        sidecar_value = load_json(sidecar)
        sidecar_relative = sidecar.relative_to(root).as_posix()
        content = canonical_json(
            {
                "binary_content_sha256": sha256_file(path),
                "sidecar_path": sidecar_relative,
                "sidecar_content_sha256": sha256_file(sidecar),
                "sidecar": sidecar_value,
            }
        )
        status = "active"
    else:
        sidecar_relative = path.relative_to(root).as_posix() + ".sidecar.json"
        content = canonical_json(
            {
                "binary_content_sha256": sha256_file(path),
                "sidecar_path": sidecar_relative,
                "sidecar_status": "missing",
            }
        )
        # A metadata-only sidecar view is still safe: it exposes the binary hash,
        # never the binary body, and clearly records that no authored sidecar exists.
        status = "active"
    return make_unit(
        file_record,
        f"unit.{file_record['file_id']}.sidecar",
        "binary_sidecar",
        f"sidecar:{sidecar_relative}",
        file_record["purpose"],
        content,
        status=status,
    )


def make_unit(
    file_record: dict[str, Any],
    unit_id: str,
    locator_type: str,
    locator: str,
    purpose: str,
    content: str,
    status: str = "active",
) -> dict[str, Any]:
    parent_hash = file_record.get("content_sha256") or file_record.get("runtime_hash")
    return {
        "schema_version": SCHEMA_VERSION,
        "unit_id": unit_id,
        "file_id": file_record["file_id"],
        "locator_type": locator_type,
        "locator": locator,
        "purpose": purpose,
        "read_when": file_record["read_when"],
        "write_when": file_record["write_when"],
        "owner": file_record["owner"],
        "validators": file_record["validators"],
        "parent_file_hash": parent_hash,
        "unit_hash": sha256_text(content),
        "task_tags": file_record["task_tags"],
        "status": status,
    }


def whole_file_unit(text: str, file_record: dict[str, Any]) -> dict[str, Any]:
    return make_unit(
        file_record,
        f"unit.{file_record['file_id']}.whole",
        "whole_file",
        file_record["file_id"],
        file_record["purpose"],
        text,
    )


def extract_units_for_file(root: Path, file_record: dict[str, Any]) -> list[dict[str, Any]]:
    if file_record["status"] != "active" or file_record["path"] in CATALOG_PROJECTIONS:
        return []
    path = root / file_record["path"]
    if not path.exists():
        # Keep sync recoverable. Validation still reports a missing active file,
        # but projection rebuild must not crash before it can produce that result.
        return []
    strategy = file_record["unit_strategy"]
    if strategy == "binary_sidecar":
        return [binary_sidecar_unit(root, path, file_record)]
    text = read_utf8(path)
    if strategy == "markdown_heading":
        return markdown_units(text, file_record)
    if strategy == "json_pointer":
        return json_pointer_units(json.loads(text), file_record)
    if strategy == "jsonl_record_id":
        return jsonl_units(load_jsonl(path), file_record)
    if strategy == "code_symbol":
        return code_symbol_units(text, file_record)
    if strategy == "test_symbol":
        return code_symbol_units(text, file_record, tests_only=True)
    if strategy == "key_path":
        return config_key_units(text, file_record, path.suffix.lower())
    return [whole_file_unit(text, file_record)]


def load_file_catalog(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    return load_jsonl(root / "catalog/files.jsonl")


def record_id(record: dict[str, Any]) -> str:
    for field in ("decision_id", "knowledge_id", "case_id", "source_id", "relation_id"):
        if record.get(field):
            return str(record[field])
    raise ContextSystemError(f"corpus record lacks stable ID: {record.get('record_kind')}")


def parse_markdown_corpus_records(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    case_root = root / CASE_ROOT
    if not case_root.exists():
        return records
    for path in sorted(case_root.glob("*.md")):
        relative = path.relative_to(root).as_posix()
        for match in JSON_FENCE_PATTERN.finditer(read_utf8(path)):
            try:
                value = json.loads(match.group("json"))
            except json.JSONDecodeError as exc:
                raise ContextSystemError(f"invalid corpus JSON: {relative}: {exc}") from exc
            if isinstance(value, dict) and value.get("record_kind") == "case":
                records.append(value)
    return records


def build_record_projection(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in CORPUS_JSONL_PATHS:
        records.extend(load_jsonl(root / relative))
    records.extend(parse_markdown_corpus_records(root))
    ids = [record_id(record) for record in records]
    if len(ids) != len(set(ids)):
        raise ContextSystemError("duplicate decision, knowledge, or case record ID")
    records = sorted(records, key=record_id)
    write_jsonl_atomic(root / "catalog/records.jsonl", records)
    return records


def build_file_catalog(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    catalog_path = root / "catalog/files.jsonl"
    existing = load_jsonl(catalog_path) if catalog_path.exists() else []
    existing_by_path = {record["path"]: record for record in existing}
    paths = iter_project_files(root)
    if "catalog/files.jsonl" not in paths:
        paths.append("catalog/files.jsonl")
    actual_paths = set(paths)
    records = [
        classify_file(path, root, "active", existing_by_path.get(path))
        for path in sorted(actual_paths)
    ]
    for record in existing:
        if is_internal_transient_path(record["path"]):
            continue
        if record["path"] in actual_paths:
            continue
        if record.get("status") in {"planned", "deleted", "moved"}:
            records.append(record)
        elif record.get("status") == "active":
            if record.get("authority") == "derived":
                # Missing derived projections are valid only while their
                # deterministic producer is rebuilding them from canonical data.
                continue
            # Missing active files are retained so validation reports an unrecorded deletion.
            records.append(record)
    records = sorted(records, key=lambda item: item["file_id"])
    self_record = next(record for record in records if record["path"] == "catalog/files.jsonl")
    self_record["runtime_hash"] = None
    self_record["runtime_hash"] = sha256_text(canonical_json(records))
    write_jsonl_atomic(catalog_path, records)
    return records


def build_unit_projection(root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    records = load_file_catalog(root)
    units: list[dict[str, Any]] = []
    for record in records:
        units.extend(extract_units_for_file(root, record))
    units = sorted(units, key=lambda item: item["unit_id"])
    write_jsonl_atomic(root / "catalog/units.jsonl", units)
    return units


def sync_catalog(root: Path = PROJECT_ROOT) -> dict[str, int]:
    with repository_lock(root):
        (root / "catalog").mkdir(parents=True, exist_ok=True)
        build_rule_projection(root)
        build_record_projection(root)
        build_file_catalog(root)
        build_unit_projection(root)
        files = build_file_catalog(root)
        return {
            "files": len([record for record in files if record["status"] == "active"]),
            "planned": len([record for record in files if record["status"] == "planned"]),
            "records": len(load_jsonl(root / "catalog/records.jsonl")),
            "rules": len(load_jsonl(root / "catalog/rules.jsonl")),
            "units": len(load_jsonl(root / "catalog/units.jsonl")),
            "unit_projection_bytes": (root / "catalog/units.jsonl").stat().st_size,
        }


def event_payload_hash(event: dict[str, Any]) -> str:
    value = dict(event)
    value.pop("event_hash", None)
    return sha256_text(canonical_json(value))


def append_event(
    root: Path,
    event_type: str,
    task_id: str | None,
    target_paths: list[str],
    before_hashes: dict[str, str | None],
    after_hashes: dict[str, str | None],
    result: str,
    details: dict[str, Any] | None = None,
    authorized_protected_scopes: Iterable[str] = (),
) -> dict[str, Any]:
    path = root / "records/work/events.jsonl"
    records = load_jsonl(path) if path.exists() else []
    sequence = len(records) + 1
    previous = records[-1]["event_hash"] if records else None
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": f"event.{event_type.replace('_', '-')}.{sequence:04d}",
        "timestamp": now_iso(),
        "event_type": event_type,
        "actor": "context_system",
        "task_id": task_id,
        "target_paths": [assert_task_scoped_path(item, root, authorized_protected_scopes) for item in target_paths],
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
        "result": result,
        "details": details or {},
        "previous_event_hash": previous,
        "event_hash": "",
    }
    event["event_hash"] = event_payload_hash(event)
    records.append(event)
    write_jsonl_atomic(path, records)
    return event


def bootstrap(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    manifest = load_json(root / "catalog/bootstrap.json")
    events_path = root / "records/work/events.jsonl"
    existing = load_jsonl(events_path) if events_path.exists() else []
    if not any(event.get("event_type") == "manual_bootstrap" for event in existing):
        append_event(
            root,
            "manual_bootstrap",
            "task.r2a.bootstrap",
            ["catalog/bootstrap.json"],
            {},
            {"catalog/bootstrap.json": sha256_file(root / "catalog/bootstrap.json")},
            "success",
            {
                "baseline_file_count": len(manifest["baseline_files"]),
                "rule_mapping_count": len(manifest["rule_mapping"]),
                "manual_boundary": "Initial tool and catalog bootstrap before the live writer fixture.",
            },
        )
    counts = sync_catalog(root)
    return {"bootstrap_id": manifest["bootstrap_id"], **counts}


def plan_file(root: Path, path: str) -> dict[str, Any]:
    normalized = assert_allowed_path(path, root)
    if (root / normalized).exists():
        raise ContextSystemError(f"cannot plan existing file: {normalized}")
    sync_catalog(root)
    records = load_file_catalog(root)
    records = [record for record in records if record["path"] != normalized]
    planned = classify_file(normalized, root, "planned")
    occupied = {record["file_id"] for record in records}
    if planned["file_id"] in occupied:
        suffix = ascii_slug(PurePosixPath(normalized).suffix.lstrip(".")) or f"id-{sha256_text(normalized)[:12]}"
        candidate = f"{planned['file_id']}.{suffix}"
        planned["file_id"] = candidate if candidate not in occupied else f"{candidate}.id-{sha256_text(normalized)[:12]}"
    records.append(planned)
    records = sorted(records, key=lambda item: item["file_id"])
    self_record = next(record for record in records if record["path"] == "catalog/files.jsonl")
    self_record["runtime_hash"] = None
    self_record["runtime_hash"] = sha256_text(canonical_json(records))
    write_jsonl_atomic(root / "catalog/files.jsonl", records)
    event = append_event(
        root,
        "catalog_sync",
        "task.r2a.bootstrap",
        [normalized],
        {normalized: None},
        {normalized: None},
        "success",
        {"status": "planned", "file_id": planned["file_id"]},
    )
    sync_catalog(root)
    return {"file_id": planned["file_id"], "path": normalized, "event_id": event["event_id"]}


def condition_matches(condition: dict[str, Any], request: dict[str, Any]) -> bool:
    actual = request.get(condition["field"])
    operation = condition["op"]
    expected = condition.get("value")
    if operation == "eq":
        return actual == expected
    if operation == "nonempty":
        return bool(actual) is bool(expected)
    if operation == "in":
        if isinstance(actual, list):
            return any(item in expected for item in actual)
        return actual in expected
    if operation == "intersects":
        actual_values = actual if isinstance(actual, list) else [actual]
        return bool(set(actual_values) & set(expected))
    raise ContextSystemError(f"unsupported predicate operation: {operation}")


def rule_matches(rule: dict[str, Any], request: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    if request["phase"] not in rule["phases"]:
        return False, {"phase": request["phase"], "allowed_phases": rule["phases"], "matched": False}
    predicate = rule["applies_when"]
    key = "any" if "any" in predicate else "all"
    results = [condition_matches(condition, request) for condition in predicate[key]]
    matched = any(results) if key == "any" else all(results)
    excluded = any(condition_matches(condition, request) for condition in rule.get("excludes_when", []))
    return matched and not excluded, {"mode": key, "condition_results": results, "excluded": excluded, "matched": matched and not excluded}


def validate_task_request(request: dict[str, Any], root: Path) -> None:
    schema = load_json(root / "schemas/task_request.schema.json")
    required = schema["required"]
    missing = [field for field in required if field not in request]
    if missing:
        raise ContextSystemError(f"task request missing fields: {missing}")
    unknown = sorted(set(request) - set(schema["properties"]))
    if unknown:
        raise ContextSystemError(f"task request has unsupported fields: {unknown}")
    allowed_actions = set(schema["properties"]["actions"]["items"]["enum"])
    if not request["actions"] or len(request["actions"]) != len(set(request["actions"])) or not set(request["actions"]) <= allowed_actions:
        raise ContextSystemError(f"task request has invalid actions: {request['actions']}")
    if request["phase"] not in schema["properties"]["phase"]["enum"]:
        raise ContextSystemError(f"task request has invalid phase: {request['phase']}")
    if not isinstance(request["context_budget"], int) or request["context_budget"] < 1:
        raise ContextSystemError("task request context_budget must be a positive integer")
    protected_scopes = [
        normalize_authorized_protected_scope(scope, root)
        for scope in request.get("authorized_protected_scopes", [])
    ]
    if len(protected_scopes) != len(set(protected_scopes)):
        raise ContextSystemError("task request has duplicate authorized protected scopes")
    for target in request["target_paths"]:
        assert_task_scoped_path(target, root, protected_scopes)
    for scope in request["include_scopes"]:
        assert_task_scoped_path(scope, root, protected_scopes)
    for scope in request["exclude_scopes"]:
        normalized = normalize_path(scope, root)
        if normalized.split("/", 1)[0] not in PROTECTED_TOP_LEVEL:
            assert_allowed_path(normalized, root)
    for prefix in request.get("metadata_filters", {}).get("path_prefixes", []):
        assert_task_scoped_path(prefix, root, protected_scopes)
    if request.get("write_payload_path"):
        assert_allowed_path(request["write_payload_path"], root)
    normalized_includes = [normalize_path(item, root).rstrip("/") for item in request["include_scopes"]]
    for scope in protected_scopes:
        if scope not in normalized_includes:
            raise ContextSystemError(f"authorized protected scope must be an exact include scope: {scope}")


def _path_in_scopes(path: str, scopes: list[str]) -> bool:
    if not scopes:
        return True
    normalized = PurePosixPath(path)
    return any(normalized == PurePosixPath(scope) or PurePosixPath(scope) in normalized.parents for scope in scopes)


def _file_matches_metadata(record: dict[str, Any], filters: dict[str, Any], scopes: list[str]) -> bool:
    if not _path_in_scopes(record["path"], scopes):
        return False
    if filters.get("kinds") and record.get("kind") not in filters["kinds"]:
        return False
    if filters.get("statuses") and record.get("status") not in filters["statuses"]:
        return False
    if filters.get("task_tags") and not set(filters["task_tags"]) & set(record.get("task_tags", [])):
        return False
    if filters.get("path_prefixes") and not any(
        record["path"] == prefix or record["path"].startswith(prefix.rstrip("/") + "/")
        for prefix in filters["path_prefixes"]
    ):
        return False
    return True


def _record_matches_metadata(record: dict[str, Any], filters: dict[str, Any]) -> bool:
    if filters.get("kinds") and record.get("record_kind") not in filters["kinds"]:
        return False
    if filters.get("statuses") and record.get("status") not in filters["statuses"]:
        return False
    if filters.get("task_tags") and not set(filters["task_tags"]) & set(record.get("task_tags", [])):
        return False
    if filters.get("retrieval_eligible") is not None and record.get("retrieval_eligible") is not filters["retrieval_eligible"]:
        return False
    return True


def _revision_hash(records: list[dict[str, Any]], volatile_fields: set[str] | None = None) -> str:
    volatile = volatile_fields or set()
    normalized = []
    for record in records:
        value = {key: item for key, item in record.items() if key not in volatile}
        if "observed_at" in volatile and value.get("path") == "catalog/files.jsonl":
            # The catalog self hash includes observation timestamps; clear it
            # when computing a logical revision that already excludes them.
            value["runtime_hash"] = None
        normalized.append(value)
    return sha256_text(canonical_json(normalized))


def selection_fingerprint_for(
    request_hash: str, revision_manifest: dict[str, str], selection_ids: dict[str, list[str]]
) -> str:
    return sha256_text(
        canonical_json(
            {
                "request_hash": request_hash,
                "revisions": revision_manifest,
                "selection_ids": selection_ids,
            }
        )
    )


def resolve_request(root: Path, request_path: str, output_path: str) -> dict[str, Any]:
    request_relative = assert_allowed_path(request_path, root)
    output_relative = assert_allowed_path(output_path, root)
    sync_catalog(root)
    request = load_json(root / request_relative)
    validate_task_request(request, root)
    request_hash = sha256_text(canonical_json(request))
    protected_scopes = [
        normalize_authorized_protected_scope(scope, root)
        for scope in request.get("authorized_protected_scopes", [])
    ]
    for event in load_jsonl(root / "records/work/events.jsonl"):
        if (
            event.get("event_type") == "protected_scope_closed"
            and event.get("task_id") == request["task_id"]
            and event.get("details", {}).get("request_hash") == request_hash
        ):
            raise ContextSystemError(f"protected task context is closed: {request['task_id']}")
    rules = load_jsonl(root / "catalog/rules.jsonl")
    files = load_file_catalog(root)
    units = load_jsonl(root / "catalog/units.jsonl")
    corpus_records = load_jsonl(root / "catalog/records.jsonl")
    source_records = load_jsonl(root / SOURCE_STORE_PATH)
    relation_records = load_jsonl(root / RELATION_STORE_PATH)
    files_by_path = {record["path"]: record for record in files}
    files_by_id = {record["file_id"]: record for record in files}
    units_by_id = {record["unit_id"]: record for record in units}
    all_units = list(units)
    task_protected_records: list[dict[str, Any]] = []
    records_by_id = {record_id(record): record for record in corpus_records + source_records}

    selected_rules: list[str] = []
    predicate_evidence: dict[str, Any] = {}
    exclusions: list[dict[str, Any]] = []
    for rule in rules:
        matched, evidence = rule_matches(rule, request)
        predicate_evidence[rule["rule_id"]] = evidence
        if matched:
            selected_rules.append(rule["rule_id"])
        else:
            exclusions.append({"kind": "rule", "id": rule["rule_id"], "reason": "predicate_not_matched"})

    selected_file_ids: dict[str, str] = {file_id_for_path("PROJECT_RULES.md"): "kernel"}
    target_records: list[dict[str, Any]] = []
    for target_path in request["target_paths"]:
        normalized = assert_task_scoped_path(target_path, root, protected_scopes)
        record = files_by_path.get(normalized)
        protected_scope = protected_scope_for(normalized, protected_scopes, root)
        if protected_scope:
            status = "active" if (root / normalized).exists() else "planned"
            if status == "planned" and "create" not in request["actions"]:
                raise ContextSystemError(f"protected target does not exist and create is not authorized: {normalized}")
            record = classify_file(
                normalized,
                root,
                status,
                authorized_protected_scopes=protected_scopes,
            )
            record["file_id"] = f"file.task-scope.{sha256_text(normalized)[:16]}"
            task_protected_records.append(record)
            files_by_path[normalized] = record
            files_by_id[record["file_id"]] = record
            if status == "active":
                task_units = extract_units_for_file(root, record)
                all_units.extend(task_units)
                units_by_id.update({unit["unit_id"]: unit for unit in task_units})
        if not record:
            raise ContextSystemError(f"target is not registered: {normalized}")
        selected_file_ids[record["file_id"]] = "exact_target"
        target_records.append(record)
    for file_id in request["target_file_ids"]:
        record = files_by_id.get(file_id)
        if not record:
            raise ContextSystemError(f"target file ID is not registered: {file_id}")
        selected_file_ids[file_id] = "exact_target_id"
        if record not in target_records:
            target_records.append(record)
    metadata_filters = request.get("metadata_filters")
    if metadata_filters:
        for record in files + task_protected_records:
            if record["status"] == "active" and _file_matches_metadata(record, metadata_filters, request["include_scopes"]):
                selected_file_ids.setdefault(record["file_id"], "metadata_match")
    for rule_id in selected_rules:
        rule = next(item for item in rules if item["rule_id"] == rule_id)
        record = files_by_path[rule["pack_path"]]
        selected_file_ids[record["file_id"]] = f"selected_rule:{rule_id}"
    dependency_queue = list(selected_file_ids)
    for file_id in dependency_queue:
        record = files_by_id.get(file_id)
        if not record:
            continue
        for dependency in record.get("depends_on", []):
            if dependency in files_by_id and dependency not in selected_file_ids:
                selected_file_ids[dependency] = f"dependency_of:{file_id}"

    selected_unit_ids: dict[str, str] = {}
    for unit_id in request["target_unit_ids"]:
        unit = units_by_id.get(unit_id)
        if not unit:
            raise ContextSystemError(f"target unit ID is not registered: {unit_id}")
        selected_unit_ids[unit_id] = "exact_target_unit"
        selected_file_ids[unit["file_id"]] = "unit_parent"
    for rule_id in selected_rules:
        rule = next(item for item in rules if item["rule_id"] == rule_id)
        file_record = files_by_path[rule["pack_path"]]
        candidates = [
            unit
            for unit in all_units
            if unit["file_id"] == file_record["file_id"] and unit["locator"].split(" > ")[-1] == f"heading:{rule_id}"
        ]
        if not candidates:
            candidates = [unit for unit in all_units if unit["file_id"] == file_record["file_id"] and rule_id in unit["locator"]]
        for unit in candidates:
            selected_unit_ids[unit["unit_id"]] = f"selected_rule:{rule_id}"

    requested_record_ids = request.get("target_record_ids", [])
    selected_record_ids: dict[str, str] = {}
    for requested_id in requested_record_ids:
        record = records_by_id.get(requested_id)
        if not record:
            raise ContextSystemError(f"target record ID is not registered: {requested_id}")
        selected_record_ids[requested_id] = "exact_target_record"
    record_filters = request.get("record_filters")
    if record_filters:
        for item_id, record in records_by_id.items():
            if _record_matches_metadata(record, record_filters):
                selected_record_ids.setdefault(item_id, "metadata_match")
    selected_relations: list[dict[str, Any]] = []
    relation_seed_ids = set(selected_record_ids)
    for relation in relation_records:
        if relation.get("status") != "active" or relation.get("review_status") != "verified" or not relation.get("retrieval_eligible"):
            continue
        source_id = relation["source_record_id"]
        target_id = relation["target_record_id"]
        if source_id in relation_seed_ids or target_id in relation_seed_ids:
            selected_relations.append(relation)
            other_id = target_id if source_id in relation_seed_ids else source_id
            if other_id in records_by_id:
                selected_record_ids.setdefault(other_id, f"one_hop:{relation['relation_id']}")
    source_selection: dict[str, str] = {}
    for selected_id in list(selected_record_ids):
        for reference in records_by_id[selected_id].get("source_refs", []):
            source_selection.setdefault(reference["source_id"], f"source_trace:{selected_id}")
    for relation in selected_relations:
        for reference in relation.get("source_refs", []):
            source_selection.setdefault(reference["source_id"], f"relation_trace:{relation['relation_id']}")
    for source_id, reason in source_selection.items():
        if source_id not in records_by_id:
            raise ContextSystemError(f"record source is not registered: {source_id}")
        selected_record_ids.setdefault(source_id, reason)

    record_manifest = {
        "records": [
            {
                "record_id": selected_id,
                "record_kind": records_by_id[selected_id]["record_kind"],
                "status": records_by_id[selected_id].get("status"),
                "selection_reason": reason,
                "record": records_by_id[selected_id],
            }
            for selected_id, reason in sorted(selected_record_ids.items())
        ],
        "relations": selected_relations,
    }
    for record in corpus_records + source_records:
        item_id = record_id(record)
        if item_id not in selected_record_ids:
            exclusions.append({"kind": "record", "id": item_id, "reason": "outside_exact_or_one_hop_scope"})
    for relation in relation_records:
        if relation not in selected_relations:
            reason = "candidate_not_active" if relation.get("status") == "candidate" else "outside_one_hop_scope"
            exclusions.append({"kind": "relation", "id": relation["relation_id"], "reason": reason})

    read_manifest: list[dict[str, Any]] = []
    for file_id, reason in sorted(selected_file_ids.items()):
        record = files_by_id[file_id]
        matching_units = [
            unit
            for unit_id, unit_reason in selected_unit_ids.items()
            if (unit := units_by_id[unit_id])["file_id"] == file_id
        ]
        read_manifest.append(
            {
                "file_id": file_id,
                "path": record["path"],
                "status": record["status"],
                "expected_hash": record.get("content_sha256") or record.get("runtime_hash"),
                "selection_reason": reason,
                "units": [
                    {
                        "unit_id": unit["unit_id"],
                        "locator": unit["locator"],
                        "unit_hash": unit["unit_hash"],
                        "selection_reason": selected_unit_ids[unit["unit_id"]],
                    }
                    for unit in matching_units
                ],
            }
        )
    for record in files:
        if record["file_id"] not in selected_file_ids and record["status"] == "active":
            exclusions.append({"kind": "file", "id": record["file_id"], "path": record["path"], "reason": "outside_exact_or_dependency_scope"})

    revision_manifest = {
        "catalog": _revision_hash(files, {"observed_at"}),
        "rules": _revision_hash(rules),
        "units": _revision_hash(units),
        "records": _revision_hash(corpus_records),
        "sources": _revision_hash(source_records),
        "relations": _revision_hash(relation_records),
    }
    if task_protected_records:
        revision_manifest["protected_task_scope"] = _revision_hash(task_protected_records, {"observed_at"})
    selection_ids = {
        "rules": sorted(selected_rules),
        "files": sorted(selected_file_ids),
        "units": sorted(selected_unit_ids),
        "records": sorted(selected_record_ids),
        "relations": sorted(record["relation_id"] for record in selected_relations),
    }
    selection_fingerprint = selection_fingerprint_for(request_hash, revision_manifest, selection_ids)

    write_contract: dict[str, Any] | None = None
    write_actions = set(request["actions"]) & {"create", "write", "move", "delete"}
    if write_actions:
        targets = []
        for record in target_records:
            if record["status"] == "planned" and not ({"create", "move"} & write_actions):
                raise ContextSystemError(f"planned target requires create or move action: {record['path']}")
            target_units = [unit for unit in all_units if unit["file_id"] == record["file_id"]]
            targets.append(
                {
                    "file_id": record["file_id"],
                    "path": record["path"],
                    "status": record["status"],
                    "before_file_hash": record.get("content_sha256"),
                    "unit_ids": [unit["unit_id"] for unit in target_units],
                    "before_unit_hashes": {unit["unit_id"]: unit["unit_hash"] for unit in target_units},
                    "owner": record["owner"],
                    "authority": record["authority"],
                    "write_when": record["write_when"],
                    "validators": record["validators"],
                }
            )
        write_contract = {
            "schema_version": SCHEMA_VERSION,
            "contract_id": f"contract.{request['task_id']}",
            "request_hash": request_hash,
            "allowed_actions": sorted(write_actions),
            "targets": targets,
            "selected_rule_ids": selected_rules,
            "validators": sorted({validator for target in targets for validator in target["validators"]}),
            "required_updates": ["catalog", "units", "event"] + (["handoff"] if "SESSION_HANDOFF.md" in request["target_paths"] else []),
        }

    context = {
        "schema_version": SCHEMA_VERSION,
        "context_id": f"context.{request['task_id']}",
        "request": request,
        "request_hash": request_hash,
        "as_of": request["as_of"],
        "revision_manifest": revision_manifest,
        "selection_ids": selection_ids,
        "selection_fingerprint": selection_fingerprint,
        "authority": {
            "user_scope": {
                "include": request["include_scopes"],
                "exclude": request["exclude_scopes"],
                "authorized_protected_scopes": protected_scopes,
            },
            "kernel_rule_ids": KERNEL_RULE_IDS,
            "selected_conditional_rule_ids": selected_rules,
            "predicate_evidence": predicate_evidence,
        },
        "read_manifest": read_manifest,
        "record_manifest": record_manifest,
        "protected_file_manifest": task_protected_records,
        "exclusions": exclusions,
        "write_contract": write_contract,
    }
    write_json_atomic(root / output_relative, context)
    append_event(
        root,
        "context_resolved",
        request["task_id"],
        [request_relative, output_relative],
        {request_relative: sha256_file(root / request_relative), output_relative: None},
        {request_relative: sha256_file(root / request_relative), output_relative: sha256_file(root / output_relative)},
        "success",
        {"selected_rules": selected_rules, "selected_files": sorted(selected_file_ids), "selected_units": sorted(selected_unit_ids), "selected_records": sorted(selected_record_ids), "selected_relations": [record["relation_id"] for record in selected_relations], "selection_fingerprint": selection_fingerprint},
    )
    sync_catalog(root)
    return context


def validate_required(record: dict[str, Any], schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    return [field for field in schema.get("required", []) if field not in record]


def validate_markdown_links(root: Path, paths: Iterable[str]) -> tuple[list[str], int]:
    errors: list[str] = []
    count = 0
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for relative in paths:
        if not relative.endswith(".md"):
            continue
        text = read_utf8(root / relative)
        for match in pattern.finditer(text):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            count += 1
            destination = ((root / relative).parent / target).resolve()
            try:
                destination_relative = destination.relative_to(root.resolve())
            except ValueError:
                errors.append(f"link escapes project: {relative} -> {target}")
                continue
            if destination_relative.parts and destination_relative.parts[0] == "backup":
                # Historical links are provenance locators, not active runtime
                # dependencies. The immutable backup tree may be absent in a clone.
                continue
            if not destination.exists():
                errors.append(f"broken local link: {relative} -> {target}")
    return errors, count


def validate_event_chain(root: Path) -> list[str]:
    errors: list[str] = []
    previous = None
    for record in load_jsonl(root / "records/work/events.jsonl"):
        missing = validate_required(record, root / "schemas/event.schema.json")
        if missing:
            errors.append(f"event missing fields {record.get('event_id')}: {missing}")
        if record.get("previous_event_hash") != previous:
            errors.append(f"event chain predecessor mismatch: {record.get('event_id')}")
        if record.get("event_hash") != event_payload_hash(record):
            errors.append(f"event hash mismatch: {record.get('event_id')}")
        previous = record.get("event_hash")
    return errors


def validate_history_chains(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    reviews = load_jsonl(root / REVIEW_STORE_PATH)
    revisions = load_jsonl(root / REVISION_STORE_PATH)
    previous = None
    for record in reviews:
        missing = validate_required(record, root / "schemas/review.schema.json")
        if missing:
            errors.append(f"review missing fields {record.get('review_id')}: {missing}")
        if record.get("previous_review_hash") != previous:
            errors.append(f"review chain predecessor mismatch: {record.get('review_id')}")
        if record.get("review_hash") != _history_hash(record, "review_hash"):
            errors.append(f"review hash mismatch: {record.get('review_id')}")
        previous = record.get("review_hash")
    previous = None
    for record in revisions:
        missing = validate_required(record, root / "schemas/revision.schema.json")
        if missing:
            errors.append(f"revision missing fields {record.get('revision_id')}: {missing}")
        if record.get("previous_revision_hash") != previous:
            errors.append(f"revision chain predecessor mismatch: {record.get('revision_id')}")
        if record.get("revision_hash") != _history_hash(record, "revision_hash"):
            errors.append(f"revision hash mismatch: {record.get('revision_id')}")
        previous = record.get("revision_hash")
    return errors, {"reviews": len(reviews), "revisions": len(revisions)}


def corpus_schema_path(root: Path, record: dict[str, Any]) -> Path:
    kind = record.get("record_kind")
    mapping = {
        "decision": "decision.schema.json",
        "knowledge": "knowledge.schema.json",
        "case": "case.schema.json",
        "source": "source.schema.json",
        "relation": "relation.schema.json",
    }
    if kind not in mapping:
        raise ContextSystemError(f"unknown corpus record kind: {kind}")
    return root / "schemas" / mapping[kind]


def validate_corpus(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    projected = load_jsonl(root / "catalog/records.jsonl")
    canonical: list[dict[str, Any]] = []
    for relative in CORPUS_JSONL_PATHS:
        canonical.extend(load_jsonl(root / relative))
    canonical.extend(parse_markdown_corpus_records(root))
    canonical = sorted(canonical, key=record_id)
    if projected != canonical:
        errors.append("record projection differs from canonical corpus")
    sources = load_jsonl(root / SOURCE_STORE_PATH)
    relations = load_jsonl(root / RELATION_STORE_PATH)
    all_records = projected + sources + relations
    ids = [record_id(record) for record in all_records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate corpus record ID")
    sources_by_id = {record["source_id"]: record for record in sources}
    endpoint_ids = {record_id(record) for record in projected + sources}
    relations_by_id = {record["relation_id"]: record for record in relations}
    allowed_relation_types = set(load_json(root / "schemas/relation.schema.json")["properties"]["relation_type"]["enum"])
    for record in all_records:
        missing = validate_required(record, corpus_schema_path(root, record))
        if missing:
            errors.append(f"{record.get('record_kind')} missing fields {record_id(record)}: {missing}")
        for reference in record.get("source_refs", []):
            if reference.get("source_id") not in sources_by_id:
                errors.append(f"dangling source reference {record_id(record)} -> {reference.get('source_id')}")
        for relation_id in record.get("relation_ids", []):
            if relation_id not in relations_by_id:
                errors.append(f"dangling relation reference {record_id(record)} -> {relation_id}")
    for source in sources:
        if source["source_type"] in {"project_document", "historical_document"}:
            locator_path = source["locator"].split("#", 1)[0]
            try:
                normalized = assert_allowed_path(locator_path, root)
            except ContextSystemError as exc:
                errors.append(str(exc))
                continue
            path = root / normalized
            if not path.exists():
                if source.get("source_type") == "project_document" and source.get("status") == "active":
                    errors.append(f"source path missing: {source['source_id']} -> {normalized}")
            else:
                actual_hash = sha256_file(path)
                if source.get("content_sha256") != actual_hash:
                    if source.get("status") != "needs_review":
                        errors.append(f"source content hash mismatch without needs_review: {source['source_id']}")
                    elif source.get("observed_content_sha256") != actual_hash:
                        errors.append(f"source observed hash is stale: {source['source_id']}")
        if source.get("status") == "historical_candidate":
            if source.get("retrieval_eligible") or source.get("authority") in {"active_policy", "active_contract"}:
                errors.append(f"historical candidate became active instruction: {source['source_id']}")
    for relation in relations:
        if relation.get("relation_type") not in allowed_relation_types:
            errors.append(f"unsupported relation type: {relation.get('relation_id')} -> {relation.get('relation_type')}")
        if relation["source_record_id"] not in endpoint_ids or relation["target_record_id"] not in endpoint_ids:
            errors.append(f"dangling relation endpoint: {relation['relation_id']}")
        if relation["status"] == "candidate" and (relation["review_status"] != "pending" or relation["retrieval_eligible"]):
            errors.append(f"unreviewed relation candidate became active: {relation['relation_id']}")

    decisions = [record for record in projected if record.get("record_kind") == "decision"]
    expected_decisions = {f"decision.r1.1.d{number:02d}" for number in range(1, 18)}
    if {record["decision_id"] for record in decisions} != expected_decisions:
        errors.append("D-01 through D-17 decision IDs are incomplete")
    for record in decisions:
        approval = record.get("approval", {})
        if record.get("status") != "accepted" or not all(approval.get(field) for field in ("approved_by", "approved_at", "evidence_source_id", "locator")):
            errors.append(f"decision is not accepted and approved: {record['decision_id']}")
        expected_legacy = "D-" + record["decision_id"].rsplit("d", 1)[1]
        if record.get("legacy_id") != expected_legacy:
            errors.append(f"decision legacy ID mismatch: {record['decision_id']}")
    verified = [record for record in projected if record.get("record_kind") == "knowledge" and record.get("status") == "verified"]
    if not any(record.get("source_refs") and all(ref["source_id"] in sources_by_id for ref in record["source_refs"]) for record in verified):
        errors.append("no verified knowledge traces to registered sources")
    cases = [record for record in projected if record.get("record_kind") == "case"]
    if not any(record.get("status") == "resolved" and record.get("symptom", {}).get("state") == "confirmed" and record.get("resolution", {}).get("state") == "resolved" and record.get("symptom", {}).get("evidence") and record.get("resolution", {}).get("evidence") for record in cases):
        errors.append("no resolved case separates confirmed symptom and resolution evidence")
    for record in [item for item in projected if item.get("record_kind") == "knowledge"]:
        if record.get("status") == "verified" and not record.get("retrieval_eligible"):
            errors.append(f"verified knowledge is not retrieval eligible: {record['knowledge_id']}")
        if record.get("status") != "verified" and record.get("retrieval_eligible"):
            errors.append(f"non-verified knowledge is retrieval eligible: {record['knowledge_id']}")
    return errors, {
        "decisions": len(decisions),
        "knowledge": len([record for record in projected if record.get("record_kind") == "knowledge"]),
        "cases": len(cases),
        "sources": len(sources),
        "relations": len(relations),
    }


def validate_project(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    manifest = load_json(root / "catalog/bootstrap.json")
    mapping = manifest["rule_mapping"]
    sources = [record["source"] for record in mapping]
    mapped_ids = [record["rule_id"] for record in mapping]
    if len(mapping) != 29 or len(set(sources)) != 29 or len(set(mapped_ids)) != 29:
        errors.append("bootstrap rule mapping is not 29 unique sources and IDs")
    if len([record for record in mapping if record["destination"] == "PROJECT_RULES.md"]) != 8:
        errors.append("kernel mapping count is not 8")
    if len([record for record in mapping if record["destination"] != "PROJECT_RULES.md"]) != 21:
        errors.append("conditional mapping count is not 21")

    kernel_text = read_utf8(root / "PROJECT_RULES.md")
    kernel_ids = re.findall(r"^## (rule\.core\.[a-z0-9.-]+)$", kernel_text, re.MULTILINE)
    if kernel_ids != KERNEL_RULE_IDS:
        errors.append(f"kernel IDs/order mismatch: {kernel_ids}")
    parsed_rules = parse_rule_packs(root)
    parsed_rule_ids = {rule["rule_id"] for rule in parsed_rules}
    if len(parsed_rules) != len(parsed_rule_ids):
        errors.append("conditional rules do not have unique IDs")
    mapped_conditional_ids = set(mapped_ids) - set(kernel_ids)
    if not mapped_conditional_ids <= parsed_rule_ids:
        errors.append("bootstrap conditional rule baseline is missing from live packs")
    projected_rules = load_jsonl(root / "catalog/rules.jsonl")
    if projected_rules != parsed_rules:
        errors.append("rule projection differs from Markdown rule packs")
    for rule in parsed_rules:
        missing = validate_required(rule, root / "schemas/rule.schema.json")
        if missing:
            errors.append(f"rule missing fields {rule['rule_id']}: {missing}")

    actual_paths = set(iter_project_files(root))
    file_records = load_file_catalog(root)
    files_by_id = {record["file_id"]: record for record in file_records}
    active_records = [record for record in file_records if record["status"] == "active"]
    active_paths = {record["path"] for record in active_records}
    orphan_paths = sorted(actual_paths - active_paths)
    missing_paths = sorted(active_paths - actual_paths)
    if orphan_paths:
        errors.append(f"orphan files: {orphan_paths}")
    if missing_paths:
        errors.append(f"catalog active files missing: {missing_paths}")
    if len(files_by_id) != len(file_records) or len(active_paths) != len(active_records):
        errors.append("duplicate file ID or active path")
    for record in file_records:
        missing = validate_required(record, root / "schemas/file.schema.json")
        if missing:
            errors.append(f"file record missing fields {record.get('file_id')}: {missing}")
        try:
            assert_allowed_path(record["path"], root)
        except ContextSystemError as exc:
            errors.append(str(exc))
        path = root / record["path"]
        if record["status"] != "active":
            continue
        if record["hash_policy"] == "content_sha256" and record["content_sha256"] != sha256_file(path):
            errors.append(f"content hash mismatch: {record['path']}")
        elif record["hash_policy"] == "projection_runtime_hash" and record.get("runtime_hash") != sha256_file(path):
            errors.append(f"projection runtime hash mismatch: {record['path']}")
    self_record = next((record for record in file_records if record["path"] == "catalog/files.jsonl"), None)
    if not self_record:
        errors.append("catalog self record missing")
    else:
        expected_runtime = self_record.get("runtime_hash")
        self_record["runtime_hash"] = None
        calculated = sha256_text(canonical_json(file_records))
        self_record["runtime_hash"] = expected_runtime
        if expected_runtime != calculated:
            errors.append("catalog runtime hash mismatch")

    unit_records = load_jsonl(root / "catalog/units.jsonl")
    unit_projection_bytes = (root / "catalog/units.jsonl").stat().st_size
    if len(unit_records) > MAX_UNIT_PROJECTION_COUNT:
        errors.append(
            f"unit projection count exceeds budget: {len(unit_records)} > {MAX_UNIT_PROJECTION_COUNT}"
        )
    if unit_projection_bytes > MAX_UNIT_PROJECTION_BYTES:
        errors.append(
            f"unit projection size exceeds budget: {unit_projection_bytes} > {MAX_UNIT_PROJECTION_BYTES}"
        )
    if len({record["unit_id"] for record in unit_records}) != len(unit_records):
        errors.append("duplicate unit ID")
    for record in unit_records:
        missing = validate_required(record, root / "schemas/unit.schema.json")
        if missing:
            errors.append(f"unit missing fields {record.get('unit_id')}: {missing}")
        parent = files_by_id.get(record["file_id"])
        if not parent:
            errors.append(f"dangling unit parent: {record['unit_id']}")
            continue
        parent_hash = parent.get("content_sha256") or parent.get("runtime_hash")
        if record["parent_file_hash"] != parent_hash:
            errors.append(f"unit parent hash mismatch: {record['unit_id']}")
    expected_units: list[dict[str, Any]] = []
    for record in file_records:
        expected_units.extend(extract_units_for_file(root, record))
    expected_units = sorted(expected_units, key=lambda item: item["unit_id"])
    if unit_records != expected_units:
        errors.append("unit projection differs from deterministic extraction")

    for schema_path in sorted((root / "schemas").glob("*.json")):
        try:
            load_json(schema_path)
        except Exception as exc:  # noqa: BLE001 - report every schema parse failure
            errors.append(f"schema parse failure {schema_path.name}: {exc}")
    for request_path in sorted((root / "context/requests").glob("*.json")) if (root / "context/requests").exists() else []:
        request = load_json(request_path)
        missing = validate_required(request, root / "schemas/task_request.schema.json")
        if missing:
            errors.append(f"task request missing fields {request_path.name}: {missing}")
        try:
            validate_task_request(request, root)
        except ContextSystemError as exc:
            errors.append(str(exc))
    for context_path in sorted((root / "context/work").glob("*.json")) if (root / "context/work").exists() else []:
        context = load_json(context_path)
        missing = validate_required(context, root / "schemas/work_context.schema.json")
        if missing:
            errors.append(f"work context missing fields {context_path.name}: {missing}")
        if context.get("request_hash") != sha256_text(canonical_json(context.get("request"))):
            errors.append(f"work context request hash mismatch: {context_path.name}")
        contract = context.get("write_contract")
        if contract:
            missing = validate_required(contract, root / "schemas/write_contract.schema.json")
            if missing:
                errors.append(f"write contract missing fields {context_path.name}: {missing}")
        selected_rule_ids = context.get("authority", {}).get("selected_conditional_rule_ids", [])
        if any(rule_id not in {rule["rule_id"] for rule in parsed_rules} for rule_id in selected_rule_ids):
            errors.append(f"work context selected a non-active instruction: {context_path.name}")
        protected_scopes = context.get("request", {}).get("authorized_protected_scopes", [])
        for record in context.get("protected_file_manifest", []):
            try:
                assert_task_scoped_path(record.get("path", ""), root, protected_scopes)
                if not protected_scope_for(record["path"], protected_scopes, root):
                    errors.append(f"work context protected manifest is outside task scope: {context_path.name}")
                if record["path"] in active_paths:
                    errors.append(f"protected task file leaked into global catalog: {record['path']}")
            except (ContextSystemError, KeyError) as exc:
                errors.append(f"invalid protected task manifest {context_path.name}: {exc}")

    retrieval_evaluations = []
    retrieval_results = []
    evaluation_root = root / "evaluation/retrieval"
    if evaluation_root.exists():
        for evaluation_path in sorted(evaluation_root.glob("*_queries.json")):
            evaluation = load_json(evaluation_path)
            missing = validate_required(evaluation, root / "schemas/retrieval_evaluation.schema.json")
            if missing:
                errors.append(f"retrieval evaluation missing fields {evaluation_path.name}: {missing}")
            query_ids = [query.get("query_id") for query in evaluation.get("queries", [])]
            if len(query_ids) != len(set(query_ids)):
                errors.append(f"duplicate retrieval query ID: {evaluation_path.name}")
            retrieval_evaluations.append(evaluation)
        for result_path in sorted(evaluation_root.glob("*_result.json")):
            result = load_json(result_path)
            missing = validate_required(result, root / "schemas/retrieval_result.schema.json")
            if missing:
                errors.append(f"retrieval result missing fields {result_path.name}: {missing}")
            source_path = result.get("source_evaluation_path")
            if source_path:
                try:
                    normalized = assert_allowed_path(source_path, root)
                    if not (root / normalized).exists() or result.get("source_evaluation_sha256") != sha256_file(root / normalized):
                        errors.append(f"retrieval result source mismatch: {result_path.name}")
                except ContextSystemError as exc:
                    errors.append(str(exc))
            if result.get("ok") and any(not query.get("passed") for query in result.get("queries", [])):
                errors.append(f"retrieval result overclaims pass: {result_path.name}")
            if result.get("logical_result_hash") != sha256_text(canonical_json(result.get("queries", []))):
                errors.append(f"retrieval result logical hash mismatch: {result_path.name}")
            retrieval_results.append(result)

    operational_evaluations = []
    operational_results = []
    operations_root = root / "evaluation/operations"
    if operations_root.exists():
        for evaluation_path in sorted(operations_root.glob("*_acceptance.json")):
            evaluation = load_json(evaluation_path)
            missing = validate_required(evaluation, root / "schemas/operational_acceptance.schema.json")
            if missing:
                errors.append(f"operational acceptance missing fields {evaluation_path.name}: {missing}")
            scenario_ids = [scenario.get("scenario_id") for scenario in evaluation.get("scenarios", [])]
            scenario_kinds = [scenario.get("scenario_kind") for scenario in evaluation.get("scenarios", [])]
            if len(scenario_ids) != 9 or len(set(scenario_ids)) != 9 or len(set(scenario_kinds)) != 9:
                errors.append(f"operational acceptance is not nine unique scenarios: {evaluation_path.name}")
            operational_evaluations.append(evaluation)
        for result_path in sorted(operations_root.glob("*_result.json")):
            result = load_json(result_path)
            missing = validate_required(result, root / "schemas/operational_acceptance_result.schema.json")
            if missing:
                errors.append(f"operational result missing fields {result_path.name}: {missing}")
            source_path = result.get("source_evaluation_path")
            if source_path:
                try:
                    normalized = assert_allowed_path(source_path, root)
                    if not (root / normalized).exists() or result.get("source_evaluation_sha256") != sha256_file(root / normalized):
                        errors.append(f"operational result source mismatch: {result_path.name}")
                except ContextSystemError as exc:
                    errors.append(str(exc))
            if result.get("ok") and any(not scenario.get("passed") for scenario in result.get("scenarios", [])):
                errors.append(f"operational result overclaims pass: {result_path.name}")
            if result.get("logical_result_hash") != sha256_text(canonical_json(result.get("scenarios", []))):
                errors.append(f"operational result logical hash mismatch: {result_path.name}")
            operational_results.append(result)

    link_errors, link_count = validate_markdown_links(root, actual_paths)
    errors.extend(link_errors)
    errors.extend(validate_event_chain(root))
    corpus_errors, corpus_counts = validate_corpus(root)
    errors.extend(corpus_errors)
    history_errors, history_counts = validate_history_chains(root)
    errors.extend(history_errors)
    for forbidden in ("backup/forbidden", "inputs/forbidden", "outputs/forbidden"):
        try:
            assert_allowed_path(forbidden, root)
            errors.append(f"protected pre-filter did not reject: {forbidden}")
        except ContextSystemError:
            pass
    return {
        "ok": not errors,
        "errors": errors,
        "counts": {
            "kernel_rules": len(kernel_ids),
            "conditional_rules": len(parsed_rules),
            "active_files": len(active_records),
            "planned_files": len([record for record in file_records if record["status"] == "planned"]),
            "units": len(unit_records),
            "unit_projection_bytes": unit_projection_bytes,
            "events": len(load_jsonl(root / "records/work/events.jsonl")),
            "retrieval_evaluations": len(retrieval_evaluations),
            "retrieval_results": len(retrieval_results),
            "operational_evaluations": len(operational_evaluations),
            "operational_results": len(operational_results),
            **history_counts,
            **corpus_counts,
            "local_links": link_count,
            "orphan_files": len(orphan_paths),
        },
    }


def render_session_summary(data: dict[str, Any]) -> str:
    required = ["session_id", "title", "date", "goal", "scope", "completed", "validation", "failures", "risks", "next_action"]
    missing = [field for field in required if field not in data]
    if missing:
        raise ContextSystemError(f"session summary data missing fields: {missing}")
    bullets = lambda values: "\n".join(f"- {value}" for value in values) if values else "- None"
    return (
        f"# {data['title']}\n\n"
        f"- Purpose: Preserve verified evidence for session `{data['session_id']}`.\n"
        "- Use when: Exact session-history review only; current state remains in `SESSION_HANDOFF.md`.\n"
        "- Owner: Project agents maintain this immutable session record.\n"
        "- Language: English.\n"
        f"- Location: `{data['path']}`.\n"
        f"- Date: {data['date']}\n\n"
        f"## Goal\n\n{data['goal']}\n\n"
        f"## Scope\n\n{bullets(data['scope'])}\n\n"
        f"## Completed work\n\n{bullets(data['completed'])}\n\n"
        f"## Validation\n\n{bullets(data['validation'])}\n\n"
        f"## Failure ledger\n\n{bullets(data['failures'])}\n\n"
        f"## Remaining risks\n\n{bullets(data['risks'])}\n\n"
        f"## First unstarted action\n\n{data['next_action']}\n"
    )


def render_handoff(data: dict[str, Any]) -> str:
    required = ["checkpoint", "approval_state", "completed", "validation", "failure_ledger", "risks", "artifacts", "next_actions", "start_prompt"]
    missing = [field for field in required if field not in data]
    if missing:
        raise ContextSystemError(f"handoff data missing fields: {missing}")
    bullets = lambda values: "\n".join(f"- {value}" for value in values) if values else "- None"
    return (
        "# Session Handoff\n\n"
        "- Purpose: Preserve the single verified resumable project checkpoint without relying on chat memory.\n"
        "- Use when: Read after the boot kernel at every session start; resume only user-authorized work.\n"
        "- Owner: Project agents verify and update this file; the user controls approval boundaries.\n"
        "- Language: English.\n"
        "- Location: Project root. Governed by [PROJECT_RULES.md](PROJECT_RULES.md), routed through [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md), and executed through [WORKFLOW.md](docs/agent/WORKFLOW.md).\n\n"
        "## Current checkpoint\n\n"
        f"{data['checkpoint']}\n\n"
        "## Approval state\n\n"
        f"{data['approval_state']}\n\n"
        "## Completed work\n\n"
        f"{bullets(data['completed'])}\n\n"
        "## Verification state\n\n"
        f"{bullets(data['validation'])}\n\n"
        "## Failure ledger\n\n"
        f"{bullets(data['failure_ledger'])}\n\n"
        "## Active risks and exclusions\n\n"
        f"{bullets(data['risks'])}\n\n"
        "## Important artifacts\n\n"
        f"{bullets(data['artifacts'])}\n\n"
        "## Next actions\n\n"
        f"{bullets(data['next_actions'])}\n\n"
        "## Backup and deduplication\n\n"
        "No ad hoc backup was created; version history is the preservation surface and `backup/` remains immutable.\n\n"
        "## Next-session start prompt\n\n"
        f"{data['start_prompt']}\n"
    )


def apply_payload_operation(root: Path, operation: dict[str, Any], current: str | None) -> str:
    mode = operation["operation"]
    if mode == "replace_file":
        content = operation.get("content")
        if content is None and "content_lines" in operation:
            content = "\n".join(operation["content_lines"])
        if content is None:
            raise ContextSystemError("replace_file requires content or content_lines")
        return content if content.endswith("\n") else content + "\n"
    if mode == "replace_text":
        if current is None:
            raise ContextSystemError("replace_text requires an existing target")
        before = operation["before"]
        if current.count(before) != 1:
            raise ContextSystemError(f"replace_text expected one match, found {current.count(before)}")
        return current.replace(before, operation["after"], 1)
    if mode == "render_session_summary":
        return render_session_summary(operation["data"])
    if mode == "render_handoff":
        return render_handoff(operation["data"])
    raise ContextSystemError(f"unsupported text operation: {mode}")


def _operation_touched_paths(
    operation: dict[str, Any],
    root: Path,
    authorized_protected_scopes: Iterable[str] = (),
) -> list[str]:
    target = assert_task_scoped_path(operation["target_path"], root, authorized_protected_scopes)
    if operation["operation"] == "move_file":
        destination = assert_task_scoped_path(operation["destination_path"], root, authorized_protected_scopes)
        source_scope = protected_scope_for(target, authorized_protected_scopes, root)
        destination_scope = protected_scope_for(destination, authorized_protected_scopes, root)
        if source_scope != destination_scope:
            raise ContextSystemError("move across a protected task boundary is rejected")
        return [target, destination]
    return [target]


def _validate_rendered_content(path: Path, content: bytes) -> None:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return
    if b"\x00" in content:
        raise ContextSystemError(f"write rejected: NUL content for {path}")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContextSystemError(f"write rejected: invalid UTF-8 for {path}") from exc
    suffix = path.suffix.lower()
    if suffix == ".md" and (text.count("```") % 2 or text.count("~~~") % 2):
        raise ContextSystemError(f"write rejected: unbalanced Markdown fence for {path}")
    if suffix == ".json":
        json.loads(text)
    elif suffix == ".jsonl":
        for line in text.splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ContextSystemError(f"write rejected: JSONL row is not an object for {path}")
    elif suffix == ".py":
        compile(text, str(path), "exec")
    elif suffix == ".toml":
        tomllib.loads(text)
    elif suffix in {".ini", ".cfg"}:
        parser = configparser.ConfigParser()
        parser.read_string(text)


def _sync_if_project(root: Path) -> None:
    if (root / "PROJECT_RULES.md").exists() and (root / "catalog/bootstrap.json").exists():
        sync_catalog(root)


def _record_write_failure(
    root: Path,
    context: dict[str, Any],
    event_type: str,
    paths: list[str],
    before_hashes: dict[str, str | None],
    result: str,
    details: dict[str, Any],
    authorized_protected_scopes: Iterable[str] = (),
) -> dict[str, Any]:
    event = append_event(
        root,
        event_type,
        context.get("request", {}).get("task_id"),
        paths,
        before_hashes,
        before_hashes,
        result,
        details,
        authorized_protected_scopes,
    )
    _sync_if_project(root)
    return event


def _update_catalog_lifecycle(
    root: Path,
    operations: list[dict[str, Any]],
    before_hashes: dict[str, str | None],
    authorized_protected_scopes: Iterable[str] = (),
) -> None:
    catalog_path = root / "catalog/files.jsonl"
    if not catalog_path.exists():
        return
    records = load_jsonl(catalog_path)
    for operation in operations:
        mode = operation["operation"]
        source = assert_task_scoped_path(operation["target_path"], root, authorized_protected_scopes)
        if protected_scope_for(source, authorized_protected_scopes, root):
            continue
        if mode == "move_file":
            destination = assert_task_scoped_path(operation["destination_path"], root, authorized_protected_scopes)
            source_record = next(record for record in records if record["path"] == source)
            moved_from = [*source_record.get("moved_from", []), source]
            records = [record for record in records if record["path"] not in {source, destination}]
            active = classify_file(destination, root, "active", source_record)
            active["moved_from"] = list(dict.fromkeys(moved_from))
            records.append(active)
        elif mode == "delete_file":
            record = next(record for record in records if record["path"] == source)
            record["status"] = "deleted"
            record["content_sha256"] = before_hashes[source]
            record["hash_policy"] = "content_sha256"
            record["runtime_hash"] = None
            record["observed_at"] = now_iso()
    records = sorted(records, key=lambda item: item["file_id"])
    self_record = next(record for record in records if record["path"] == "catalog/files.jsonl")
    self_record["runtime_hash"] = None
    self_record["runtime_hash"] = sha256_text(canonical_json(records))
    write_jsonl_atomic(catalog_path, records)


def _commit_operation(
    root: Path,
    operation: dict[str, Any],
    rendered: dict[str, bytes],
    authorized_protected_scopes: Iterable[str] = (),
) -> None:
    source = assert_task_scoped_path(operation["target_path"], root, authorized_protected_scopes)
    mode = operation["operation"]
    if mode in {"replace_file", "replace_text", "write_binary", "render_session_summary", "render_handoff"}:
        write_bytes_atomic(root / source, rendered[source])
    elif mode == "move_file":
        destination = assert_task_scoped_path(operation["destination_path"], root, authorized_protected_scopes)
        (root / destination).parent.mkdir(parents=True, exist_ok=True)
        os.replace(root / source, root / destination)
    elif mode == "delete_file":
        (root / source).unlink()
    else:
        raise ContextSystemError(f"unsupported operation: {mode}")


def write_fixture(root: Path, context_path: str, payload_path: str) -> dict[str, Any]:
    context_relative = assert_allowed_path(context_path, root)
    payload_relative = assert_allowed_path(payload_path, root)
    context = load_json(root / context_relative)
    protected_scopes = [
        normalize_authorized_protected_scope(scope, root)
        for scope in context.get("request", {}).get("authorized_protected_scopes", [])
    ]
    if protected_scopes and any(
        event.get("event_type") == "protected_scope_closed"
        and event.get("task_id") == context.get("request", {}).get("task_id")
        and event.get("details", {}).get("request_hash") == context.get("request_hash")
        for event in load_jsonl(root / "records/work/events.jsonl")
    ):
        raise ContextSystemError("write rejected: protected task context is closed")
    contract = context.get("write_contract")
    if not contract:
        raise ContextSystemError("write rejected: work context has no write contract")
    if contract.get("request_hash") != context.get("request_hash"):
        raise ContextSystemError("write rejected: contract/request hash mismatch")
    payload = load_json(root / payload_relative)
    if context["request"].get("write_payload_path") != payload_relative:
        raise ContextSystemError("write rejected: payload path is not authorized by the request")
    contract_targets = {target["path"]: target for target in contract["targets"]}
    operations = payload.get("operations", [])
    touched_paths = [
        path
        for operation in operations
        for path in _operation_touched_paths(operation, root, protected_scopes)
    ]
    if len(set(touched_paths)) != len(touched_paths):
        raise ContextSystemError("write rejected: duplicate payload target")
    if set(touched_paths) != set(contract_targets):
        raise ContextSystemError("write rejected: payload targets do not match contract targets")

    before_hashes: dict[str, str | None] = {}
    snapshots: dict[str, bytes | None] = {}
    rendered: dict[str, bytes] = {}
    try:
        retry_of = payload.get("retry_of_event_id")
        if retry_of:
            prior = next(
                (event for event in load_jsonl(root / "records/work/events.jsonl") if event.get("event_id") == retry_of),
                None,
            )
            if not prior or prior.get("result") not in {"failed", "rejected"}:
                raise ContextSystemError(f"write rejected: retry event is not a failed or rejected attempt: {retry_of}")
            if prior.get("details", {}).get("contract_id") != contract["contract_id"]:
                raise ContextSystemError(f"write rejected: retry event belongs to another contract: {retry_of}")
        catalog_by_path = {
            record["path"]: record for record in load_file_catalog(root)
        } if (root / "catalog/files.jsonl").exists() else {}
        catalog_by_path.update(
            {record["path"]: record for record in context.get("protected_file_manifest", [])}
        )
        for normalized, target in contract_targets.items():
            path = root / normalized
            exists = path.exists()
            actual_before = sha256_file(path) if exists else None
            before_hashes[normalized] = actual_before
            snapshots[normalized] = path.read_bytes() if exists else None
            if actual_before != target["before_file_hash"]:
                raise ContextSystemError(f"write rejected: before hash mismatch for {normalized}")
            if target["status"] == "planned" and exists:
                raise ContextSystemError(f"write rejected: planned target already exists {normalized}")
            if target["status"] == "active" and not exists:
                raise ContextSystemError(f"write rejected: active target is missing {normalized}")
            expected_unit_hashes = target.get("before_unit_hashes", {})
            if exists and expected_unit_hashes and normalized in catalog_by_path:
                actual_unit_hashes = {
                    unit["unit_id"]: unit["unit_hash"]
                    for unit in extract_units_for_file(root, catalog_by_path[normalized])
                }
                if actual_unit_hashes != expected_unit_hashes:
                    raise ContextSystemError(f"write rejected: before unit hash mismatch for {normalized}")
        for operation in operations:
            normalized = assert_task_scoped_path(operation["target_path"], root, protected_scopes)
            mode = operation["operation"]
            if mode == "move_file":
                if "move" not in contract["allowed_actions"]:
                    raise ContextSystemError("write rejected: move action is not authorized")
                continue
            if mode == "delete_file":
                if "delete" not in contract["allowed_actions"]:
                    raise ContextSystemError("write rejected: delete action is not authorized")
                continue
            target = contract_targets[normalized]
            required_action = "create" if target["status"] == "planned" else "write"
            if required_action not in contract["allowed_actions"]:
                raise ContextSystemError(f"write rejected: {required_action} action is not authorized for {normalized}")
            if mode == "write_binary":
                try:
                    content_bytes = base64.b64decode(operation["content_base64"], validate=True)
                except (ValueError, KeyError) as exc:
                    raise ContextSystemError(f"write rejected: invalid base64 for {normalized}") from exc
            else:
                current = snapshots[normalized].decode("utf-8") if snapshots[normalized] is not None else None
                content_bytes = apply_payload_operation(root, operation, current).encode("utf-8")
            _validate_rendered_content(root / normalized, content_bytes)
            rendered[normalized] = content_bytes
    except (ContextSystemError, json.JSONDecodeError, SyntaxError, configparser.Error, tomllib.TOMLDecodeError) as exc:
        _record_write_failure(
            root,
            context,
            "write_rejected",
            sorted(set(touched_paths)),
            before_hashes,
            "rejected",
            {"contract_id": contract["contract_id"], "payload_path": payload_relative, "cause": str(exc)},
            protected_scopes,
        )
        raise ContextSystemError(str(exc)) from exc

    applied = 0
    try:
        for operation in operations:
            _commit_operation(root, operation, rendered, protected_scopes)
            applied += 1
    except Exception as exc:  # noqa: BLE001 - every partial mutation must roll back
        rollback_errors: list[str] = []
        for normalized, snapshot in snapshots.items():
            try:
                path = root / normalized
                if snapshot is None:
                    if path.exists():
                        path.unlink()
                else:
                    write_bytes_atomic(path, snapshot)
            except Exception as rollback_exc:  # noqa: BLE001
                rollback_errors.append(f"{normalized}: {rollback_exc}")
        event = _record_write_failure(
            root,
            context,
            "write_failed",
            sorted(set(touched_paths)),
            before_hashes,
            "failed",
            {
                "contract_id": contract["contract_id"],
                "payload_path": payload_relative,
                "cause": str(exc),
                "applied_operation_count": applied,
                "rollback": "failed" if rollback_errors else "success",
                "rollback_errors": rollback_errors,
            },
            protected_scopes,
        )
        raise ContextSystemError(f"write failed and rollback {'failed' if rollback_errors else 'succeeded'}: {event['event_id']}") from exc

    _update_catalog_lifecycle(root, operations, before_hashes, protected_scopes)
    after_hashes = {
        normalized: sha256_file(root / normalized) if (root / normalized).exists() else None
        for normalized in sorted(set(touched_paths))
    }
    retry_of = payload.get("retry_of_event_id")
    event_type = "write_retried" if retry_of else (
        "lifecycle_applied" if any(operation["operation"] in {"move_file", "delete_file"} for operation in operations) else "write_applied"
    )
    event = append_event(
        root,
        event_type,
        context["request"]["task_id"],
        sorted(set(touched_paths)),
        before_hashes,
        after_hashes,
        "success",
        {"contract_id": contract["contract_id"], "payload_path": payload_relative, "retry_of_event_id": retry_of},
        protected_scopes,
    )
    counts = sync_catalog(root) if (root / "catalog/bootstrap.json").exists() else {}
    return {"event_id": event["event_id"], "after_hashes": after_hashes, **counts}


def close_protected_context(root: Path, context_path: str) -> dict[str, Any]:
    """Expire one task-scoped protected authorization without deleting user data."""
    relative = assert_allowed_path(context_path, root)
    context = load_json(root / relative)
    request = context.get("request", {})
    scopes = [
        normalize_authorized_protected_scope(scope, root)
        for scope in request.get("authorized_protected_scopes", [])
    ]
    if not scopes:
        raise ContextSystemError("protected context closure requires at least one exact task scope")
    if any(
        event.get("event_type") == "protected_scope_closed"
        and event.get("task_id") == request.get("task_id")
        and event.get("details", {}).get("request_hash") == context.get("request_hash")
        for event in load_jsonl(root / "records/work/events.jsonl")
    ):
        raise ContextSystemError(f"protected task context is already closed: {request.get('task_id')}")
    event = append_event(
        root,
        "protected_scope_closed",
        request.get("task_id"),
        scopes,
        {scope: None for scope in scopes},
        {scope: None for scope in scopes},
        "success",
        {
            "context_id": context.get("context_id"),
            "request_hash": context.get("request_hash"),
            "authorized_protected_scopes": scopes,
            "data_deleted": False,
        },
        scopes,
    )
    counts = sync_catalog(root) if (root / "catalog/bootstrap.json").exists() else {}
    return {"event_id": event["event_id"], "closed_scopes": scopes, **counts}


def _history_hash(record: dict[str, Any], hash_field: str) -> str:
    value = dict(record)
    value.pop(hash_field, None)
    return sha256_text(canonical_json(value))


def _append_review_record(
    records: list[dict[str, Any]],
    record_id_value: str,
    record_kind: str,
    action: str,
    outcome: str,
    actor: str,
    timestamp: str,
    reason: str,
    before_hash: str | None,
    after_hash: str | None,
    source_ids: list[str],
) -> dict[str, Any]:
    sequence = len(records) + 1
    review = {
        "schema_version": SCHEMA_VERSION,
        "review_id": f"review.{stable_slug(record_id_value)}.{sequence:04d}",
        "record_id": record_id_value,
        "record_kind": record_kind,
        "action": action,
        "outcome": outcome,
        "actor": actor,
        "timestamp": timestamp,
        "reason": reason,
        "source_ids": source_ids,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "previous_review_hash": records[-1]["review_hash"] if records else None,
        "review_hash": "",
    }
    review["review_hash"] = _history_hash(review, "review_hash")
    records.append(review)
    return review


def _append_revision_record(
    records: list[dict[str, Any]],
    record_id_value: str,
    record_kind: str,
    from_revision: int | None,
    to_revision: int,
    actor: str,
    timestamp: str,
    reason: str,
    before_hash: str | None,
    after_hash: str,
) -> dict[str, Any]:
    sequence = len(records) + 1
    revision = {
        "schema_version": SCHEMA_VERSION,
        "revision_id": f"revision.{stable_slug(record_id_value)}.{sequence:04d}",
        "record_id": record_id_value,
        "record_kind": record_kind,
        "from_revision": from_revision,
        "to_revision": to_revision,
        "actor": actor,
        "timestamp": timestamp,
        "reason": reason,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "previous_revision_hash": records[-1]["revision_hash"] if records else None,
        "revision_hash": "",
    }
    revision["revision_hash"] = _history_hash(revision, "revision_hash")
    records.append(revision)
    return revision


def _validate_knowledge_sources(record: dict[str, Any], source_ids: set[str]) -> None:
    missing = [reference.get("source_id") for reference in record.get("source_refs", []) if reference.get("source_id") not in source_ids]
    if missing:
        raise ContextSystemError(f"knowledge record has unregistered sources: {missing}")


def maintain_knowledge(root: Path, operation_path: str) -> dict[str, Any]:
    relative = assert_allowed_path(operation_path, root)
    operation = load_json(root / relative)
    required = ["operation_id", "task_id", "action", "actor", "timestamp", "reason"]
    missing = [field for field in required if field not in operation]
    if missing:
        raise ContextSystemError(f"knowledge operation missing fields: {missing}")
    items_path = root / "knowledge/items.jsonl"
    reviews_path = root / REVIEW_STORE_PATH
    revisions_path = root / REVISION_STORE_PATH
    relations_path = root / RELATION_STORE_PATH
    sources = load_jsonl(root / SOURCE_STORE_PATH)
    source_ids = {record["source_id"] for record in sources}
    items = load_jsonl(items_path)
    reviews = load_jsonl(reviews_path)
    revisions = load_jsonl(revisions_path)
    relations = load_jsonl(relations_path)
    action = operation["action"]
    before_records = {
        "knowledge/items.jsonl": items_path.read_bytes() if items_path.exists() else None,
        REVIEW_STORE_PATH: reviews_path.read_bytes() if reviews_path.exists() else None,
        REVISION_STORE_PATH: revisions_path.read_bytes() if revisions_path.exists() else None,
        RELATION_STORE_PATH: relations_path.read_bytes() if relations_path.exists() else None,
    }
    changed_ids: list[str] = []

    if action == "link_conflict":
        knowledge_ids = sorted(operation.get("knowledge_ids", []))
        if len(knowledge_ids) != 2 or len(set(knowledge_ids)) != 2:
            raise ContextSystemError("link_conflict requires exactly two distinct knowledge IDs")
        by_id = {item["knowledge_id"]: item for item in items}
        if any(knowledge_id not in by_id for knowledge_id in knowledge_ids):
            raise ContextSystemError(f"conflict knowledge record not found: {knowledge_ids}")
        expected_hashes = operation.get("expected_record_hashes", {})
        for knowledge_id in knowledge_ids:
            actual_hash = sha256_text(canonical_json(by_id[knowledge_id]))
            if expected_hashes.get(knowledge_id) != actual_hash:
                raise ContextSystemError(f"knowledge conflict hash mismatch: {knowledge_id}")
        relation_id = f"relation.{stable_slug(knowledge_ids[0])}.contradicted-by.{stable_slug(knowledge_ids[1])}"
        if any(relation.get("relation_id") == relation_id for relation in relations):
            raise ContextSystemError(f"conflict relation already exists: {relation_id}")
        references: dict[tuple[str, str], dict[str, str]] = {}
        for knowledge_id in knowledge_ids:
            for reference in by_id[knowledge_id].get("source_refs", []):
                references[(reference["source_id"], reference["locator"])] = reference
        relation = {
            "schema_version": SCHEMA_VERSION,
            "record_kind": "relation",
            "relation_id": relation_id,
            "relation_type": "contradicted_by",
            "source_record_id": knowledge_ids[0],
            "target_record_id": knowledge_ids[1],
            "status": "active",
            "review_status": "verified",
            "source_refs": [references[key] for key in sorted(references)],
            "retrieval_eligible": True,
        }
        relation_hash = sha256_text(canonical_json(relation))
        relations.append(relation)
        _append_revision_record(
            revisions, relation_id, "relation", None, 1, operation["actor"],
            operation["timestamp"], operation["reason"], None, relation_hash,
        )
        _append_review_record(
            reviews, relation_id, "relation", action, "verified", operation["actor"],
            operation["timestamp"], operation["reason"], None, relation_hash,
            sorted({reference["source_id"] for reference in relation["source_refs"]}),
        )
        changed_ids.append(relation_id)
    elif action == "create_candidate":
        record = dict(operation.get("record") or {})
        knowledge_id = record.get("knowledge_id")
        if not knowledge_id or any(item["knowledge_id"] == knowledge_id for item in items):
            raise ContextSystemError(f"knowledge candidate ID is missing or already exists: {knowledge_id}")
        if record.get("record_kind") != "knowledge" or record.get("status") != "candidate" or record.get("retrieval_eligible"):
            raise ContextSystemError("new knowledge must start as a non-retrieval-eligible candidate")
        if record.get("revision") != 1:
            raise ContextSystemError("new knowledge candidate must start at revision 1")
        _validate_knowledge_sources(record, source_ids)
        missing_fields = validate_required(record, root / "schemas/knowledge.schema.json")
        if missing_fields:
            raise ContextSystemError(f"knowledge candidate missing fields: {missing_fields}")
        items.append(record)
        after_hash = sha256_text(canonical_json(record))
        _append_revision_record(revisions, knowledge_id, "knowledge", None, 1, operation["actor"], operation["timestamp"], operation["reason"], None, after_hash)
        _append_review_record(reviews, knowledge_id, "knowledge", action, "candidate", operation["actor"], operation["timestamp"], operation["reason"], None, after_hash, [ref["source_id"] for ref in record["source_refs"]])
        changed_ids.append(knowledge_id)
    else:
        knowledge_id = operation.get("knowledge_id")
        index = next((index for index, item in enumerate(items) if item["knowledge_id"] == knowledge_id), None)
        if index is None:
            raise ContextSystemError(f"knowledge record not found: {knowledge_id}")
        current = items[index]
        before_hash = sha256_text(canonical_json(current))
        if operation.get("expected_record_hash") != before_hash:
            raise ContextSystemError(f"knowledge before hash mismatch: {knowledge_id}")
        if operation.get("expected_revision") != current.get("revision"):
            raise ContextSystemError(f"knowledge revision mismatch: {knowledge_id}")
        updated = dict(current)
        updates = operation.get("updates", {})
        forbidden = {"knowledge_id", "record_kind", "created_at", "revision"}
        if forbidden & set(updates):
            raise ContextSystemError(f"knowledge updates contain immutable fields: {sorted(forbidden & set(updates))}")
        updated.update(updates)
        updated["updated_at"] = operation["timestamp"]
        updated["revision"] = current["revision"] + 1
        if action == "review":
            outcome = operation.get("outcome")
            allowed_outcomes = {"reviewed", "verified", "needs_review", "rejected"}
            if outcome not in allowed_outcomes:
                raise ContextSystemError(f"unsupported knowledge review outcome: {outcome}")
            updated["status"] = outcome
            updated["retrieval_eligible"] = outcome == "verified"
            if outcome == "verified":
                updated["validated_by"] = operation["actor"]
                updated["validated_at"] = operation["timestamp"]
                updated["last_checked_at"] = operation["timestamp"]
        elif action == "supersede":
            updated["status"] = "superseded"
            updated["retrieval_eligible"] = False
            outcome = "superseded"
        elif action == "revise":
            outcome = updated.get("status", "needs_review")
            if outcome == "verified" and not operation.get("evidence_revalidated"):
                updated["status"] = "needs_review"
                updated["retrieval_eligible"] = False
                outcome = "needs_review"
        else:
            raise ContextSystemError(f"unsupported knowledge action: {action}")
        _validate_knowledge_sources(updated, source_ids)
        missing_fields = validate_required(updated, root / "schemas/knowledge.schema.json")
        if missing_fields:
            raise ContextSystemError(f"knowledge update missing fields: {missing_fields}")
        after_hash = sha256_text(canonical_json(updated))
        items[index] = updated
        _append_revision_record(revisions, knowledge_id, "knowledge", current["revision"], updated["revision"], operation["actor"], operation["timestamp"], operation["reason"], before_hash, after_hash)
        _append_review_record(reviews, knowledge_id, "knowledge", action, outcome, operation["actor"], operation["timestamp"], operation["reason"], before_hash, after_hash, [ref["source_id"] for ref in updated["source_refs"]])
        changed_ids.append(knowledge_id)
        if action == "supersede" and operation.get("replacement_record"):
            replacement = dict(operation["replacement_record"])
            replacement_id = replacement.get("knowledge_id")
            if not replacement_id or any(item["knowledge_id"] == replacement_id for item in items):
                raise ContextSystemError(f"replacement knowledge ID is missing or already exists: {replacement_id}")
            if replacement.get("status") != "candidate" or replacement.get("retrieval_eligible") or replacement.get("revision") != 1:
                raise ContextSystemError("replacement knowledge must be a revision-1 non-eligible candidate")
            _validate_knowledge_sources(replacement, source_ids)
            items.append(replacement)
            replacement_hash = sha256_text(canonical_json(replacement))
            _append_revision_record(revisions, replacement_id, "knowledge", None, 1, operation["actor"], operation["timestamp"], operation["reason"], None, replacement_hash)
            relation_id = f"relation.{stable_slug(replacement_id)}.supersedes.{stable_slug(knowledge_id)}"
            relations.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "record_kind": "relation",
                    "relation_id": relation_id,
                    "relation_type": "supersedes",
                    "source_record_id": replacement_id,
                    "target_record_id": knowledge_id,
                    "status": "candidate",
                    "review_status": "pending",
                    "source_refs": replacement["source_refs"],
                    "retrieval_eligible": False,
                }
            )
            changed_ids.append(replacement_id)

    rendered = {
        "knowledge/items.jsonl": [canonical_json(record) for record in sorted(items, key=lambda item: item["knowledge_id"])],
        REVIEW_STORE_PATH: [canonical_json(record) for record in reviews],
        REVISION_STORE_PATH: [canonical_json(record) for record in revisions],
        RELATION_STORE_PATH: [canonical_json(record) for record in sorted(relations, key=lambda item: item["relation_id"])],
    }
    try:
        for path, lines in rendered.items():
            write_text_atomic(root / path, "\n".join(lines) + ("\n" if lines else ""))
    except Exception as exc:  # noqa: BLE001
        for path, snapshot in before_records.items():
            target = root / path
            if snapshot is None:
                if target.exists():
                    target.unlink()
            else:
                write_bytes_atomic(target, snapshot)
        raise ContextSystemError(f"knowledge lifecycle write failed and was rolled back: {exc}") from exc
    event = append_event(
        root,
        "record_reviewed" if action == "review" else "record_lifecycle",
        operation["task_id"],
        list(rendered),
        {path: sha256_bytes(content) if content is not None else None for path, content in before_records.items()},
        {path: sha256_file(root / path) for path in rendered},
        "success",
        {"operation_id": operation["operation_id"], "action": action, "record_ids": changed_ids},
    )
    counts = sync_catalog(root) if (root / "catalog/bootstrap.json").exists() else {}
    return {"event_id": event["event_id"], "record_ids": changed_ids, **counts}


def check_source_hashes(root: Path, task_id: str = "task.source.hash-check") -> dict[str, Any]:
    store_paths = [SOURCE_STORE_PATH, "knowledge/items.jsonl", REVIEW_STORE_PATH, REVISION_STORE_PATH]
    snapshots = {
        relative: (root / relative).read_bytes() if (root / relative).exists() else None
        for relative in store_paths
    }
    sources = load_jsonl(root / SOURCE_STORE_PATH)
    items = load_jsonl(root / "knowledge/items.jsonl")
    reviews = load_jsonl(root / REVIEW_STORE_PATH)
    revisions = load_jsonl(root / REVISION_STORE_PATH)
    changed_sources: list[str] = []
    changed_knowledge: list[str] = []
    timestamp = now_iso()
    for source in sources:
        if source.get("source_type") != "project_document" or source.get("status") != "active":
            continue
        locator_path = source["locator"].split("#", 1)[0]
        normalized = assert_allowed_path(locator_path, root)
        path = root / normalized
        actual_hash = sha256_file(path) if path.exists() else None
        if actual_hash == source.get("content_sha256"):
            continue
        before_hash = sha256_text(canonical_json(source))
        source["status"] = "needs_review"
        source["retrieval_eligible"] = False
        source["observed_content_sha256"] = actual_hash
        source["last_checked_at"] = timestamp
        after_hash = sha256_text(canonical_json(source))
        prior_source_revisions = [record for record in revisions if record.get("record_id") == source["source_id"]]
        from_revision = prior_source_revisions[-1]["to_revision"] if prior_source_revisions else None
        _append_revision_record(
            revisions,
            source["source_id"],
            "source",
            from_revision,
            (from_revision or 0) + 1,
            "context_system",
            timestamp,
            "Registered source content changed or disappeared.",
            before_hash,
            after_hash,
        )
        _append_review_record(reviews, source["source_id"], "source", "hash_check", "needs_review", "context_system", timestamp, "Registered source content changed or disappeared.", before_hash, after_hash, [source["source_id"]])
        changed_sources.append(source["source_id"])
        for item in items:
            if not any(reference["source_id"] == source["source_id"] for reference in item.get("source_refs", [])):
                continue
            item_before = sha256_text(canonical_json(item))
            old_revision = item["revision"]
            item["status"] = "needs_review"
            item["retrieval_eligible"] = False
            item["updated_at"] = timestamp
            item["revision"] = old_revision + 1
            item_after = sha256_text(canonical_json(item))
            _append_revision_record(revisions, item["knowledge_id"], "knowledge", old_revision, item["revision"], "context_system", timestamp, f"Source hash changed: {source['source_id']}", item_before, item_after)
            _append_review_record(reviews, item["knowledge_id"], "knowledge", "source_hash_change", "needs_review", "context_system", timestamp, f"Source hash changed: {source['source_id']}", item_before, item_after, [source["source_id"]])
            changed_knowledge.append(item["knowledge_id"])
    if changed_sources:
        try:
            write_jsonl_atomic(root / SOURCE_STORE_PATH, sorted(sources, key=lambda item: item["source_id"]))
            write_jsonl_atomic(root / "knowledge/items.jsonl", sorted(items, key=lambda item: item["knowledge_id"]))
            write_jsonl_atomic(root / REVIEW_STORE_PATH, reviews)
            write_jsonl_atomic(root / REVISION_STORE_PATH, revisions)
        except Exception as exc:  # noqa: BLE001 - maintenance must restore every canonical store
            rollback_errors: list[str] = []
            for relative, snapshot in snapshots.items():
                try:
                    target = root / relative
                    if snapshot is None:
                        if target.exists():
                            target.unlink()
                    else:
                        write_bytes_atomic(target, snapshot)
                except Exception as rollback_exc:  # noqa: BLE001
                    rollback_errors.append(f"{relative}: {rollback_exc}")
            raise ContextSystemError(
                f"source maintenance failed; rollback {'failed: ' + '; '.join(rollback_errors) if rollback_errors else 'succeeded'}: {exc}"
            ) from exc
    after_store_hashes = {
        relative: sha256_file(root / relative) if (root / relative).exists() else None
        for relative in store_paths
    }
    event = append_event(
        root,
        "source_checked",
        task_id,
        store_paths,
        {relative: sha256_bytes(snapshot) if snapshot is not None else None for relative, snapshot in snapshots.items()},
        after_store_hashes,
        "success",
        {"changed_source_ids": changed_sources, "changed_knowledge_ids": changed_knowledge},
    )
    counts = sync_catalog(root) if (root / "catalog/bootstrap.json").exists() else {}
    return {"event_id": event["event_id"], "changed_source_ids": changed_sources, "changed_knowledge_ids": changed_knowledge, **counts}


def maintain_source(root: Path, operation_path: str) -> dict[str, Any]:
    relative = assert_allowed_path(operation_path, root)
    operation = load_json(root / relative)
    required = ["operation_id", "task_id", "source_id", "expected_record_hash", "actor", "timestamp", "reason", "outcome"]
    missing = [field for field in required if field not in operation]
    if missing:
        raise ContextSystemError(f"source review operation missing fields: {missing}")
    if operation["outcome"] != "accept_current_hash":
        raise ContextSystemError(f"unsupported source review outcome: {operation['outcome']}")
    store_paths = [SOURCE_STORE_PATH, REVIEW_STORE_PATH, REVISION_STORE_PATH]
    snapshots = {
        path: (root / path).read_bytes() if (root / path).exists() else None
        for path in store_paths
    }
    sources = load_jsonl(root / SOURCE_STORE_PATH)
    reviews = load_jsonl(root / REVIEW_STORE_PATH)
    revisions = load_jsonl(root / REVISION_STORE_PATH)
    index = next((index for index, source in enumerate(sources) if source["source_id"] == operation["source_id"]), None)
    if index is None:
        raise ContextSystemError(f"source record not found: {operation['source_id']}")
    source = sources[index]
    before_hash = sha256_text(canonical_json(source))
    if before_hash != operation["expected_record_hash"]:
        raise ContextSystemError(f"source record before hash mismatch: {operation['source_id']}")
    if source.get("status") != "needs_review":
        raise ContextSystemError(f"source is not awaiting review: {operation['source_id']}")
    if source.get("source_type") != "project_document":
        raise ContextSystemError("accept_current_hash supports project_document sources only")
    locator_path = assert_allowed_path(source["locator"].split("#", 1)[0], root)
    locator = root / locator_path
    if not locator.exists():
        raise ContextSystemError(f"source review cannot accept a missing path: {locator_path}")
    actual_hash = sha256_file(locator)
    if source.get("observed_content_sha256") != actual_hash:
        raise ContextSystemError(f"source changed again after detection: {operation['source_id']}")
    updated = dict(source)
    updated["content_sha256"] = actual_hash
    updated["observed_content_sha256"] = actual_hash
    updated["status"] = "active"
    updated["retrieval_eligible"] = True
    updated["observed_at"] = operation["timestamp"]
    updated["last_checked_at"] = operation["timestamp"]
    after_hash = sha256_text(canonical_json(updated))
    sources[index] = updated
    prior = [record for record in revisions if record.get("record_id") == source["source_id"]]
    from_revision = prior[-1]["to_revision"] if prior else None
    _append_revision_record(
        revisions,
        source["source_id"],
        "source",
        from_revision,
        (from_revision or 0) + 1,
        operation["actor"],
        operation["timestamp"],
        operation["reason"],
        before_hash,
        after_hash,
    )
    _append_review_record(
        reviews,
        source["source_id"],
        "source",
        "source_review",
        "active",
        operation["actor"],
        operation["timestamp"],
        operation["reason"],
        before_hash,
        after_hash,
        [source["source_id"]],
    )
    try:
        write_jsonl_atomic(root / SOURCE_STORE_PATH, sorted(sources, key=lambda item: item["source_id"]))
        write_jsonl_atomic(root / REVIEW_STORE_PATH, reviews)
        write_jsonl_atomic(root / REVISION_STORE_PATH, revisions)
    except Exception as exc:  # noqa: BLE001
        for path, snapshot in snapshots.items():
            target = root / path
            if snapshot is None:
                if target.exists():
                    target.unlink()
            else:
                write_bytes_atomic(target, snapshot)
        raise ContextSystemError(f"source review failed and was rolled back: {exc}") from exc
    event = append_event(
        root,
        "record_reviewed",
        operation["task_id"],
        store_paths,
        {path: sha256_bytes(snapshot) if snapshot is not None else None for path, snapshot in snapshots.items()},
        {path: sha256_file(root / path) for path in store_paths},
        "success",
        {"operation_id": operation["operation_id"], "source_id": source["source_id"], "outcome": operation["outcome"]},
    )
    counts = sync_catalog(root) if (root / "catalog/bootstrap.json").exists() else {}
    return {"event_id": event["event_id"], "source_id": source["source_id"], **counts}


def _normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return " ".join(re.findall(r"[0-9a-z가-힣]+", normalized))


def _search_terms(value: str) -> list[str]:
    stopwords = {"근거", "찾기", "찾아줘", "알려줘", "관련", "대한", "있는", "없는"}
    return [term for term in _normalize_search_text(value).split() if len(term) > 1 and term not in stopwords]


def _retrieval_eligible(record: dict[str, Any]) -> bool:
    kind = record.get("record_kind")
    if kind == "decision":
        return record.get("status") == "accepted" and bool(record.get("retrieval_eligible"))
    if kind == "knowledge":
        return record.get("status") == "verified" and bool(record.get("retrieval_eligible"))
    if kind == "case":
        return record.get("status") in {"confirmed", "resolved", "recurring"} and bool(record.get("retrieval_eligible"))
    if kind == "source":
        return record.get("status") == "active" and bool(record.get("retrieval_eligible"))
    if kind == "rule":
        return record.get("status") == "active"
    if kind == "file":
        return record.get("status") == "active" and record.get("index_scope") == "global"
    return False


def _retrieval_candidates(root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    sources = load_jsonl(root / SOURCE_STORE_PATH)
    sources_by_id = {source["source_id"]: source for source in sources}
    candidates: list[dict[str, Any]] = []
    for record in load_jsonl(root / "catalog/records.jsonl") + sources:
        item_id = record_id(record)
        title = record.get("title") or record.get("legacy_id") or item_id
        metadata_text = " ".join(
            str(value)
            for value in (
                item_id,
                record.get("legacy_id", ""),
                title,
                " ".join(record.get("task_tags", [])),
                record.get("record_kind", ""),
                record.get("status", ""),
            )
        )
        candidates.append(
            {
                "item_id": item_id,
                "item_kind": record.get("record_kind"),
                "title": title,
                "status": record.get("status"),
                "task_tags": record.get("task_tags", []),
                "path": None,
                "eligible": _retrieval_eligible(record),
                "metadata_text": _normalize_search_text(metadata_text),
                "record": record,
            }
        )
    for rule in load_jsonl(root / "catalog/rules.jsonl"):
        record = {**rule, "record_kind": "rule"}
        candidates.append(
            {
                "item_id": rule["rule_id"],
                "item_kind": "rule",
                "title": rule["rule_id"],
                "status": rule["status"],
                "task_tags": rule.get("task_tags", []),
                "path": rule["pack_path"],
                "eligible": _retrieval_eligible(record),
                "metadata_text": _normalize_search_text(" ".join([rule["rule_id"], rule.get("text", ""), " ".join(rule.get("task_tags", []))])),
                "record": record,
            }
        )
    for file_record in load_file_catalog(root):
        record = {**file_record, "record_kind": "file"}
        candidates.append(
            {
                "item_id": file_record["file_id"],
                "item_kind": "file",
                "title": file_record["purpose"],
                "status": file_record["status"],
                "task_tags": file_record.get("task_tags", []),
                "path": file_record["path"],
                "eligible": _retrieval_eligible(record),
                "metadata_text": _normalize_search_text(" ".join([file_record["file_id"], file_record["path"], file_record["kind"], file_record["purpose"], " ".join(file_record.get("task_tags", []))])),
                "record": record,
            }
        )
    return candidates, sources_by_id


def _candidate_source_trace(
    candidate: dict[str, Any], sources_by_id: dict[str, dict[str, Any]], root: Path
) -> list[dict[str, Any]]:
    record = candidate["record"]
    if candidate["item_kind"] in {"rule", "file"}:
        references = []
    elif candidate["item_kind"] == "source":
        references = [{"source_id": candidate["item_id"], "locator": record["locator"]}]
    else:
        references = list(record.get("source_refs", []))
    traces: list[dict[str, Any]] = []
    for reference in references:
        source = sources_by_id.get(reference["source_id"])
        if not source:
            continue
        traces.append(
            {
                "source_id": source["source_id"],
                "locator": reference.get("locator") or source["locator"],
                "source_locator": source["locator"],
                "source_status": source["status"],
                "content_sha256": source.get("content_sha256"),
                "retrieval_eligible": bool(source.get("retrieval_eligible")),
                "instruction_eligible": source.get("status") == "active" and source.get("authority") in {"active_policy", "active_contract"},
            }
        )
    if candidate["item_kind"] == "rule":
        path = candidate["path"]
        traces.append(
            {
                "source_id": f"file-source:{candidate['item_id']}",
                "locator": f"{path}#heading:{candidate['item_id']}",
                "source_locator": path,
                "source_status": "active",
                "content_sha256": sha256_file(root / path),
                "retrieval_eligible": True,
                "instruction_eligible": True,
            }
        )
    elif candidate["item_kind"] == "file":
        record_hash = record.get("content_sha256") or record.get("runtime_hash")
        traces.append(
            {
                "source_id": f"file-source:{candidate['item_id']}",
                "locator": candidate["path"],
                "source_locator": candidate["path"],
                "source_status": record["status"],
                "content_sha256": record_hash,
                "retrieval_eligible": True,
                "instruction_eligible": False,
            }
        )
    return traces


def _text_candidate_score(query_text: str, candidate: dict[str, Any]) -> float:
    query_normalized = _normalize_search_text(query_text)
    metadata = candidate["metadata_text"]
    if query_normalized == candidate["item_id"].lower():
        return 1000.0
    aliases = [candidate["item_id"], str(candidate["record"].get("legacy_id", ""))]
    if any(alias and _normalize_search_text(alias) in query_normalized for alias in aliases):
        return 500.0
    terms = _search_terms(query_text)
    if not terms:
        return 0.0
    matched = [term for term in terms if term in metadata]
    if not matched:
        return 0.0
    title = _normalize_search_text(candidate["title"])
    title_matches = sum(term in title for term in matched)
    return (len(matched) / len(terms)) * 100.0 + title_matches * 20.0


def _metadata_candidate_match(candidate: dict[str, Any], filters: dict[str, Any]) -> bool:
    record = candidate["record"]
    kinds = filters.get("kinds", [])
    if kinds and candidate["item_kind"] not in kinds and record.get("kind") not in kinds:
        return False
    if filters.get("statuses") and candidate["status"] not in filters["statuses"]:
        return False
    if filters.get("task_tags") and not set(filters["task_tags"]) & set(candidate["task_tags"]):
        return False
    if filters.get("path_prefixes"):
        path = candidate.get("path") or ""
        if not any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in filters["path_prefixes"]):
            return False
    return True


def retrieve_evaluation_query(root: Path, query: dict[str, Any]) -> dict[str, Any]:
    candidates, sources_by_id = _retrieval_candidates(root)
    by_id = {candidate["item_id"]: candidate for candidate in candidates}
    exclusions: list[dict[str, Any]] = []
    for scope in query.get("scope_paths", []):
        try:
            assert_allowed_path(scope, root)
        except ContextSystemError as exc:
            return {
                "query_id": query["query_id"],
                "outcome": "rejected",
                "rejection_reason": str(exc),
                "results": [],
                "exclusions": [{"id": scope, "reason": "protected_scope_prefilter"}],
                "conflicts": [],
            }
    mode = query["mode"]
    selected: list[tuple[dict[str, Any], str, float]] = []
    if mode == "exact":
        for item_id in query.get("exact_ids", []):
            candidate = by_id.get(item_id)
            if not candidate:
                exclusions.append({"id": item_id, "reason": "not_found"})
            elif not candidate["eligible"]:
                exclusions.append({"id": item_id, "reason": f"ineligible_status:{candidate['status']}"})
            else:
                selected.append((candidate, "exact_id", 1000.0))
    elif mode == "metadata":
        for candidate in candidates:
            if candidate["eligible"] and _metadata_candidate_match(candidate, query.get("filters", {})):
                selected.append((candidate, "metadata_match", 100.0))
    elif mode == "text":
        ranked = [
            (candidate, _text_candidate_score(query["query"], candidate))
            for candidate in candidates
            if candidate["eligible"]
        ]
        ranked = sorted((item for item in ranked if item[1] > 0), key=lambda item: (-item[1], item[0]["item_id"]))
        for candidate, score in ranked[: query.get("seed_limit", query["k"])]:
            selected.append((candidate, "metadata_text_match", score))
    elif mode == "conflict_scan":
        for candidate in candidates:
            if candidate["eligible"] and candidate["record"].get("conflict_ids"):
                selected.append((candidate, "conflict_scan", 100.0))
    else:
        raise ContextSystemError(f"unsupported evaluation query mode: {mode}")

    if query.get("expand_relations"):
        selected_ids = {candidate["item_id"] for candidate, _, _ in selected}
        for relation in load_jsonl(root / RELATION_STORE_PATH):
            if relation.get("status") != "active" or relation.get("review_status") != "verified" or not relation.get("retrieval_eligible"):
                continue
            source_id = relation["source_record_id"]
            target_id = relation["target_record_id"]
            if source_id not in selected_ids and target_id not in selected_ids:
                continue
            other_id = target_id if source_id in selected_ids else source_id
            candidate = by_id.get(other_id)
            if candidate and candidate["eligible"] and other_id not in selected_ids:
                selected.append((candidate, f"one_hop:{relation['relation_id']}", 90.0))
                selected_ids.add(other_id)
    deduped: list[tuple[dict[str, Any], str, float]] = []
    seen: set[str] = set()
    for candidate, reason, score in sorted(selected, key=lambda item: (-item[2], item[0]["item_id"])):
        if candidate["item_id"] not in seen:
            seen.add(candidate["item_id"])
            deduped.append((candidate, reason, score))
    results = []
    for candidate, reason, score in deduped[: query["k"]]:
        results.append(
            {
                "item_id": candidate["item_id"],
                "item_kind": candidate["item_kind"],
                "title": candidate["title"],
                "status": candidate["status"],
                "selection_reason": reason,
                "score": round(score, 6),
                "source_trace": _candidate_source_trace(candidate, sources_by_id, root),
                "conflicts": list(candidate["record"].get("conflict_ids", [])),
            }
        )
    return {
        "query_id": query["query_id"],
        "outcome": "success",
        "rejection_reason": None,
        "results": results,
        "exclusions": exclusions,
        "conflicts": sorted({conflict for result in results for conflict in result["conflicts"]}),
    }


def evaluate_retrieval(root: Path, evaluation_path: str, output_path: str) -> dict[str, Any]:
    evaluation_relative = assert_allowed_path(evaluation_path, root)
    output_relative = assert_allowed_path(output_path, root)
    evaluation = load_json(root / evaluation_relative)
    missing = validate_required(evaluation, root / "schemas/retrieval_evaluation.schema.json")
    if missing:
        raise ContextSystemError(f"retrieval evaluation missing fields: {missing}")
    thresholds = evaluation["thresholds"]
    query_results: list[dict[str, Any]] = []
    for query in evaluation["queries"]:
        retrieved = retrieve_evaluation_query(root, query)
        result_ids = [result["item_id"] for result in retrieved["results"]]
        expected = set(query["expected_ids"])
        returned = set(result_ids)
        relevant = len(expected & returned)
        recall = relevant / len(expected) if expected else (1.0 if not returned else 0.0)
        precision = relevant / len(returned) if returned else (1.0 if not expected else 0.0)
        traced = [result for result in retrieved["results"] if result["source_trace"]]
        trace_rate = len(traced) / len(retrieved["results"]) if retrieved["results"] else 1.0
        protected_leakage = sum(
            1
            for result in retrieved["results"]
            for trace in result["source_trace"]
            if PurePosixPath(trace["source_locator"]).parts and PurePosixPath(trace["source_locator"]).parts[0] in {"backup", "inputs", "outputs"}
        )
        ineligible_results = [result["item_id"] for result in retrieved["results"] if result["status"] in {"candidate", "needs_review", "superseded", "rejected", "historical_candidate"}]
        result_bytes = len(canonical_json(retrieved["results"]).encode("utf-8"))
        required_exclusions = set(query.get("required_exclusion_ids", []))
        actual_exclusions = {item["id"] for item in retrieved["exclusions"]}
        expected_outcome = query.get("expected_outcome", "success")
        passed = all(
            [
                retrieved["outcome"] == expected_outcome,
                recall >= thresholds["minimum_recall_at_k"],
                precision >= thresholds["minimum_precision_at_k"],
                trace_rate >= thresholds["minimum_source_trace_rate"],
                protected_leakage <= thresholds["maximum_protected_leakage"],
                not ineligible_results,
                result_bytes <= query["budget_bytes"],
                required_exclusions <= actual_exclusions,
            ]
        )
        query_results.append(
            {
                **retrieved,
                "expected_ids": sorted(expected),
                "metrics": {
                    "recall_at_k": recall,
                    "precision_at_k": precision,
                    "source_trace_rate": trace_rate,
                    "protected_leakage": protected_leakage,
                    "ineligible_result_ids": ineligible_results,
                    "result_bytes": result_bytes,
                    "budget_bytes": query["budget_bytes"],
                },
                "passed": passed,
            }
        )
    all_passed = all(result["passed"] for result in query_results)
    logical_result_hash = sha256_text(canonical_json(query_results))
    result = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": evaluation["evaluation_id"],
        "evaluated_at": now_iso(),
        "retriever": "direct-metadata-relation-baseline",
        "retriever_version": "r4.1",
        "source_evaluation_path": evaluation_relative,
        "source_evaluation_sha256": sha256_file(root / evaluation_relative),
        "thresholds": thresholds,
        "queries": query_results,
        "logical_result_hash": logical_result_hash,
        "summary": {
            "queries": len(query_results),
            "passed": sum(result["passed"] for result in query_results),
            "failed": sum(not result["passed"] for result in query_results),
            "minimum_recall_at_k": min(result["metrics"]["recall_at_k"] for result in query_results),
            "minimum_precision_at_k": min(result["metrics"]["precision_at_k"] for result in query_results),
            "minimum_source_trace_rate": min(result["metrics"]["source_trace_rate"] for result in query_results),
            "protected_leakage": sum(result["metrics"]["protected_leakage"] for result in query_results),
            "budget_failures": sum(result["metrics"]["result_bytes"] > result["metrics"]["budget_bytes"] for result in query_results),
        },
        "fts_decision": "not_needed_baseline_passed" if all_passed else "required_baseline_gap",
        "search_projection": None,
        "ok": all_passed,
    }
    output_before_hash = sha256_file(root / output_relative) if (root / output_relative).exists() else None
    write_json_atomic(root / output_relative, result)
    event = append_event(
        root,
        "retrieval_evaluated",
        "task.r4.evaluate",
        [evaluation_relative, output_relative],
        {evaluation_relative: sha256_file(root / evaluation_relative), output_relative: output_before_hash},
        {evaluation_relative: sha256_file(root / evaluation_relative), output_relative: sha256_file(root / output_relative)},
        "success" if all_passed else "failed",
        {"evaluation_id": evaluation["evaluation_id"], "summary": result["summary"], "fts_decision": result["fts_decision"]},
    )
    result["event_id"] = event["event_id"]
    if (root / "catalog/bootstrap.json").exists():
        sync_catalog(root)
    return result


def _acceptance_copy_project(source: Path, destination: Path) -> None:
    """Copy only globally governed, non-protected files into an isolated cold-start root."""
    for relative in iter_project_files(source):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)


def _acceptance_write_fixture(
    root: Path,
    name: str,
    task_id: str,
    actions: list[str],
    targets: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    *,
    request_extra: dict[str, Any] | None = None,
    protected_file_manifest: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    (root / "context/work").mkdir(parents=True, exist_ok=True)
    (root / "context/payloads").mkdir(parents=True, exist_ok=True)
    request_hash = sha256_text(f"{task_id}:{name}")
    payload_relative = f"context/payloads/{name}.json"
    context_relative = f"context/work/{name}.json"
    context = {
        "schema_version": SCHEMA_VERSION,
        "context_id": f"context.{task_id}",
        "request": {"task_id": task_id, "write_payload_path": payload_relative, **(request_extra or {})},
        "request_hash": request_hash,
        "protected_file_manifest": protected_file_manifest or [],
        "write_contract": {
            "schema_version": SCHEMA_VERSION,
            "contract_id": f"contract.{task_id}",
            "request_hash": request_hash,
            "allowed_actions": actions,
            "targets": targets,
            "selected_rule_ids": [],
            "validators": sorted({validator for target in targets for validator in target.get("validators", [])}),
            "required_updates": ["event"],
        },
    }
    write_json_atomic(root / context_relative, context)
    write_json_atomic(root / payload_relative, {"operations": operations})
    return write_fixture(root, context_relative, payload_relative)


def _acceptance_contract_target(
    root: Path,
    path: str,
    status: str,
    *,
    owner: str = "test",
    authority: str = "fixture",
) -> dict[str, Any]:
    full_path = root / path
    return {
        "file_id": f"file.fixture.{stable_slug(path)}",
        "path": path,
        "status": status,
        "before_file_hash": sha256_file(full_path) if status == "active" else None,
        "unit_ids": [],
        "before_unit_hashes": {},
        "owner": owner,
        "authority": authority,
        "write_when": ["acceptance_fixture"],
        "validators": ["validate.content_hash"],
    }


def _acceptance_knowledge_record(
    knowledge_id: str,
    statement: str,
    source_id: str,
    timestamp: str,
    *,
    status: str = "candidate",
    task_tags: list[str] | None = None,
) -> dict[str, Any]:
    verified = status == "verified"
    return {
        "schema_version": SCHEMA_VERSION,
        "record_kind": "knowledge",
        "knowledge_id": knowledge_id,
        "title": knowledge_id,
        "language": "en",
        "classification": "fact",
        "statement": statement,
        "created_at": timestamp,
        "updated_at": timestamp,
        "author": "r5-acceptance",
        "status": status,
        "confidence": "medium",
        "confidence_basis": "R-5 fixed operational fixture",
        "validated_by": "r5-acceptance" if verified else "",
        "validated_at": timestamp if verified else "",
        "source_refs": [{"source_id": source_id, "locator": "R-5 fixture"}],
        "relation_ids": [],
        "validity_scope": "R-5 acceptance only",
        "last_checked_at": timestamp,
        "review_policy": "event_driven",
        "review_due_at": None,
        "review_triggers": ["source_change", "conflict"],
        "revision": 1,
        "retrieval_eligible": verified,
        "task_tags": task_tags or ["r5", "fixture"],
    }


def _scenario_file_lifecycle(expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = "artifact.txt"
        states: list[str] = []
        _acceptance_write_fixture(
            root, "create", "task.r5.lifecycle.create", ["create"],
            [_acceptance_contract_target(root, path, "planned")],
            [{"target_path": path, "operation": "replace_file", "content": "created\n"}],
        )
        states.append("created")
        _acceptance_write_fixture(
            root, "modify", "task.r5.lifecycle.modify", ["write"],
            [_acceptance_contract_target(root, path, "active")],
            [{"target_path": path, "operation": "replace_file", "content": "modified\n"}],
        )
        states.append("modified")
        moved = "moved.txt"
        _acceptance_write_fixture(
            root, "move", "task.r5.lifecycle.move", ["move"],
            [_acceptance_contract_target(root, path, "active"), _acceptance_contract_target(root, moved, "planned")],
            [{"target_path": path, "destination_path": moved, "operation": "move_file"}],
        )
        states.append("moved")
        _acceptance_write_fixture(
            root, "delete", "task.r5.lifecycle.delete", ["delete"],
            [_acceptance_contract_target(root, moved, "active")],
            [{"target_path": moved, "operation": "delete_file"}],
        )
        states.append("deleted")
        events = load_jsonl(root / "records/work/events.jsonl")
        evidence = {
            "states": states,
            "final_file_exists": (root / moved).exists(),
            "success_events": sum(event["result"] == "success" for event in events),
            "event_types": [event["event_type"] for event in events],
        }
        passed = (
            evidence["states"] == expected["states"]
            and evidence["final_file_exists"] is expected["final_file_exists"]
            and evidence["success_events"] >= expected["minimum_success_events"]
        )
        return passed, evidence


def _scenario_source_review(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "knowledge").mkdir()
        (root / "schemas").mkdir()
        shutil.copy2(root_source / "schemas/knowledge.schema.json", root / "schemas/knowledge.schema.json")
        source_path = root / "source.md"
        source_path.write_text("before\n", encoding="utf-8")
        timestamp = "2026-07-21T03:00:00+09:00"
        source = {
            "source_id": "source.r5.fixture", "record_kind": "source", "source_type": "project_document",
            "locator": "source.md", "status": "active", "retrieval_eligible": True,
            "content_sha256": sha256_file(source_path),
        }
        item = _acceptance_knowledge_record(
            "knowledge.r5.source-dependent", "Source dependent fixture.", source["source_id"], timestamp,
            status="verified",
        )
        write_jsonl_atomic(root / SOURCE_STORE_PATH, [source])
        write_jsonl_atomic(root / "knowledge/items.jsonl", [item])
        for relative in (REVIEW_STORE_PATH, REVISION_STORE_PATH, RELATION_STORE_PATH):
            (root / relative).write_text("", encoding="utf-8")
        source_path.write_text("after\n", encoding="utf-8")
        check_source_hashes(root, "task.r5.source.detect")
        detected_source = load_jsonl(root / SOURCE_STORE_PATH)[0]
        detected_item = load_jsonl(root / "knowledge/items.jsonl")[0]
        source_operation = {
            "operation_id": "op.r5.source.accept", "task_id": "task.r5.source.review",
            "source_id": source["source_id"],
            "expected_record_hash": sha256_text(canonical_json(detected_source)),
            "actor": "r5-acceptance", "timestamp": timestamp,
            "reason": "R-5 reviewed the changed source hash.", "outcome": "accept_current_hash",
        }
        write_json_atomic(root / "source_review.json", source_operation)
        maintain_source(root, "source_review.json")
        item_operation = {
            "operation_id": "op.r5.knowledge.reverify", "task_id": "task.r5.source.review",
            "action": "review", "outcome": "verified", "knowledge_id": detected_item["knowledge_id"],
            "expected_record_hash": sha256_text(canonical_json(detected_item)),
            "expected_revision": detected_item["revision"], "actor": "r5-acceptance",
            "timestamp": timestamp, "reason": "R-5 reverified dependent knowledge.",
        }
        write_json_atomic(root / "knowledge_review.json", item_operation)
        maintain_knowledge(root, "knowledge_review.json")
        reviewed_source = load_jsonl(root / SOURCE_STORE_PATH)[0]
        reviewed_item = load_jsonl(root / "knowledge/items.jsonl")[0]
        evidence = {
            "detected_source_status": detected_source["status"],
            "detected_knowledge_status": detected_item["status"],
            "reviewed_source_status": reviewed_source["status"],
            "reviewed_knowledge_status": reviewed_item["status"],
            "review_records": len(load_jsonl(root / REVIEW_STORE_PATH)),
            "revision_records": len(load_jsonl(root / REVISION_STORE_PATH)),
        }
        return all(evidence[key] == value for key, value in expected.items()), evidence


def _scenario_conflict_supersession(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative in ("knowledge", "schemas", "operations"):
            (root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copy2(root_source / "schemas/knowledge.schema.json", root / "schemas/knowledge.schema.json")
        source = {"source_id": "source.r5.fixture", "record_kind": "source"}
        write_jsonl_atomic(root / SOURCE_STORE_PATH, [source])
        for relative in ("knowledge/items.jsonl", REVIEW_STORE_PATH, REVISION_STORE_PATH, RELATION_STORE_PATH):
            (root / relative).write_text("", encoding="utf-8")
        timestamp = "2026-07-21T03:05:00+09:00"
        for suffix, statement in (("alpha", "Value is alpha."), ("beta", "Value is beta.")):
            record = _acceptance_knowledge_record(f"knowledge.r5.{suffix}", statement, source["source_id"], timestamp)
            operation = {
                "operation_id": f"op.r5.create.{suffix}", "task_id": "task.r5.conflict",
                "action": "create_candidate", "actor": "r5-acceptance", "timestamp": timestamp,
                "reason": "R-5 conflicting fixture.", "record": record,
            }
            path = root / f"operations/create_{suffix}.json"
            write_json_atomic(path, operation)
            maintain_knowledge(root, path.relative_to(root).as_posix())
            current = next(item for item in load_jsonl(root / "knowledge/items.jsonl") if item["knowledge_id"] == record["knowledge_id"])
            review = {
                "operation_id": f"op.r5.verify.{suffix}", "task_id": "task.r5.conflict",
                "action": "review", "outcome": "verified", "knowledge_id": record["knowledge_id"],
                "expected_record_hash": sha256_text(canonical_json(current)), "expected_revision": current["revision"],
                "actor": "r5-acceptance", "timestamp": timestamp, "reason": "Verify both conflicting claims independently.",
            }
            review_path = root / f"operations/review_{suffix}.json"
            write_json_atomic(review_path, review)
            maintain_knowledge(root, review_path.relative_to(root).as_posix())
        items = {item["knowledge_id"]: item for item in load_jsonl(root / "knowledge/items.jsonl")}
        conflict = {
            "operation_id": "op.r5.link-conflict", "task_id": "task.r5.conflict", "action": "link_conflict",
            "knowledge_ids": ["knowledge.r5.alpha", "knowledge.r5.beta"],
            "expected_record_hashes": {item_id: sha256_text(canonical_json(items[item_id])) for item_id in ("knowledge.r5.alpha", "knowledge.r5.beta")},
            "actor": "r5-acceptance", "timestamp": timestamp, "reason": "Preserve both contradictory claims.",
        }
        write_json_atomic(root / "operations/conflict.json", conflict)
        maintain_knowledge(root, "operations/conflict.json")
        items = {item["knowledge_id"]: item for item in load_jsonl(root / "knowledge/items.jsonl")}
        replacement = _acceptance_knowledge_record("knowledge.r5.gamma", "Value is gamma.", source["source_id"], timestamp)
        supersede = {
            "operation_id": "op.r5.supersede-alpha", "task_id": "task.r5.conflict", "action": "supersede",
            "knowledge_id": "knowledge.r5.alpha",
            "expected_record_hash": sha256_text(canonical_json(items["knowledge.r5.alpha"])),
            "expected_revision": items["knowledge.r5.alpha"]["revision"], "actor": "r5-acceptance",
            "timestamp": timestamp, "reason": "Preserve the old claim beside its replacement.",
            "replacement_record": replacement,
        }
        write_json_atomic(root / "operations/supersede.json", supersede)
        maintain_knowledge(root, "operations/supersede.json")
        final_items = {item["knowledge_id"]: item for item in load_jsonl(root / "knowledge/items.jsonl")}
        relations = load_jsonl(root / RELATION_STORE_PATH)
        evidence = {
            "knowledge_ids": sorted(final_items),
            "relation_types": sorted({relation["relation_type"] for relation in relations}),
            "superseded_status": final_items["knowledge.r5.alpha"]["status"],
            "replacement_status": final_items["knowledge.r5.gamma"]["status"],
            "conflicting_record_preserved": "knowledge.r5.beta" in final_items,
        }
        passed = (
            evidence["knowledge_ids"] == sorted(expected["knowledge_ids"])
            and evidence["relation_types"] == sorted(expected["relation_types"])
            and evidence["superseded_status"] == expected["superseded_status"]
            and evidence["replacement_status"] == expected["replacement_status"]
            and evidence["conflicting_record_preserved"]
        )
        return passed, evidence


def _scenario_partial_failure(expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "context/work").mkdir(parents=True)
        (root / "context/payloads").mkdir(parents=True)
        for name in ("a.txt", "b.txt"):
            (root / name).write_text(f"{name[0]}-before\n", encoding="utf-8")
        targets = [_acceptance_contract_target(root, name, "active") for name in ("a.txt", "b.txt")]
        operations = [
            {"target_path": name, "operation": "replace_file", "content": f"{name[0]}-after\n"}
            for name in ("a.txt", "b.txt")
        ]
        original_commit = globals()["_commit_operation"]
        calls = {"count": 0}

        def fail_second(*args: Any, **kwargs: Any) -> None:
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("R-5 simulated second-operation failure")
            original_commit(*args, **kwargs)

        globals()["_commit_operation"] = fail_second
        try:
            try:
                _acceptance_write_fixture(
                    root, "partial", "task.r5.partial", ["write"], targets, operations,
                )
            except ContextSystemError:
                pass
        finally:
            globals()["_commit_operation"] = original_commit
        failed_event = load_jsonl(root / "records/work/events.jsonl")[-1]
        rollback_contents = [(root / name).read_text(encoding="utf-8").strip() for name in ("a.txt", "b.txt")]
        payload_path = root / "context/payloads/partial.json"
        payload = load_json(payload_path)
        payload["retry_of_event_id"] = failed_event["event_id"]
        write_json_atomic(payload_path, payload)
        retry = write_fixture(root, "context/work/partial.json", "context/payloads/partial.json")
        retry_event = next(event for event in load_jsonl(root / "records/work/events.jsonl") if event["event_id"] == retry["event_id"])
        final_contents = [(root / name).read_text(encoding="utf-8").strip() for name in ("a.txt", "b.txt")]
        evidence = {
            "rollback": failed_event["details"]["rollback"],
            "rollback_contents": rollback_contents,
            "retry_event_type": retry_event["event_type"],
            "retry_of_event_id": retry_event["details"]["retry_of_event_id"],
            "final_contents": final_contents,
        }
        passed = (
            evidence["rollback"] == expected["rollback"]
            and rollback_contents == ["a-before", "b-before"]
            and evidence["retry_event_type"] == expected["retry_event_type"]
            and evidence["retry_of_event_id"] == failed_event["event_id"]
            and evidence["final_contents"] == expected["final_contents"]
        )
        return passed, evidence


def _acceptance_task_request(
    task_id: str,
    *,
    target_paths: list[str],
    target_kinds: list[str],
    include_scopes: list[str],
    task_tags: list[str],
    target_record_ids: list[str] | None = None,
    actions: list[str] | None = None,
    phase: str = "read",
    output_audience: str = "agent",
    authorized_protected_scopes: list[str] | None = None,
    write_payload_path: str | None = None,
    record_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "requested_by": "r5-acceptance",
        "intent": f"R-5 fixed acceptance request for {task_id}.",
        "actions": actions or ["read"],
        "phase": phase,
        "target_paths": target_paths,
        "target_file_ids": [],
        "target_unit_ids": [],
        "target_record_ids": target_record_ids or [],
        "target_record_kinds": [],
        "target_kinds": target_kinds,
        "output_audience": output_audience,
        "include_scopes": include_scopes,
        "exclude_scopes": ["backup", "inputs", "outputs"],
        "task_tags": task_tags,
        "as_of": "2026-07-21T03:10:00+09:00",
        "context_budget": 12000,
    }
    if authorized_protected_scopes:
        request["authorized_protected_scopes"] = authorized_protected_scopes
    if write_payload_path:
        request["write_payload_path"] = write_payload_path
    if record_filters:
        request["record_filters"] = record_filters
    return request


def _scenario_cold_rebuild(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        root.mkdir()
        _acceptance_copy_project(root_source, root)
        recorded = load_json(root / "evaluation/retrieval/r4_baseline_result.json")
        before = evaluate_retrieval(
            root, "evaluation/retrieval/r4_queries.json", "evaluation/retrieval/r4_baseline_result.json"
        )
        removed: list[str] = []
        for relative in expected["deleted_projections"]:
            path = root / relative
            if path.exists():
                path.unlink()
                removed.append(relative)
        absent_before_rebuild = all(not (root / relative).exists() for relative in expected["deleted_projections"])
        sync_catalog(root)
        after = evaluate_retrieval(
            root, "evaluation/retrieval/r4_queries.json", "evaluation/retrieval/r4_baseline_result.json"
        )
        physical_indexes = sum(
            Path(relative).suffix.lower() in {".db", ".sqlite", ".sqlite3"}
            for relative in iter_project_files(root)
        )
        evidence = {
            "recorded_r4_logical_result_hash": recorded["logical_result_hash"],
            "before_rebuild_logical_result_hash": before["logical_result_hash"],
            "after_rebuild_logical_result_hash": after["logical_result_hash"],
            "fts_decision": after["fts_decision"],
            "physical_search_indexes": physical_indexes,
            "deleted_projections": removed,
            "absent_before_rebuild": absent_before_rebuild,
            "rebuilt_projections_exist": all((root / relative).exists() for relative in expected["deleted_projections"]),
            "query_differences": {
                item_before["query_id"]: [
                    sha256_text(canonical_json(item_before)),
                    sha256_text(canonical_json(item_after)),
                ]
                for item_before, item_after in zip(before["queries"], after["queries"])
                if item_before != item_after
            },
        }
        passed = (
            evidence["recorded_r4_logical_result_hash"] == expected["logical_result_hash"]
            and evidence["before_rebuild_logical_result_hash"] == evidence["after_rebuild_logical_result_hash"]
            and evidence["fts_decision"] == expected["fts_decision"]
            and evidence["physical_search_indexes"] == expected["physical_search_indexes"]
            and evidence["deleted_projections"] == expected["deleted_projections"]
            and evidence["absent_before_rebuild"]
            and evidence["rebuilt_projections_exist"]
        )
        return passed, evidence


def _scenario_new_session(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        contexts: list[dict[str, Any]] = []
        for suffix in ("one", "two"):
            root = base / suffix
            root.mkdir()
            _acceptance_copy_project(root_source, root)
            contexts.append(
                resolve_request(root, expected["request_path"], f"context/work/r5_cold_{suffix}.json")
            )
        evidence = {
            "same_revision_manifest": contexts[0]["revision_manifest"] == contexts[1]["revision_manifest"],
            "same_selection_ids": contexts[0]["selection_ids"] == contexts[1]["selection_ids"],
            "same_selection_fingerprint": contexts[0]["selection_fingerprint"] == contexts[1]["selection_fingerprint"],
            "selection_fingerprint": contexts[0]["selection_fingerprint"],
            "revision_differences": {
                key: [contexts[0]["revision_manifest"].get(key), contexts[1]["revision_manifest"].get(key)]
                for key in sorted(set(contexts[0]["revision_manifest"]) | set(contexts[1]["revision_manifest"]))
                if contexts[0]["revision_manifest"].get(key) != contexts[1]["revision_manifest"].get(key)
            },
        }
        passed = all(evidence[key] is expected[key] for key in (
            "same_revision_manifest", "same_selection_ids", "same_selection_fingerprint"
        ))
        return passed, evidence


def _scenario_protected_namespace(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        root.mkdir()
        _acceptance_copy_project(root_source, root)
        authorized_target = root / expected["authorized_target"]
        unauthorized_target = root / expected["unauthorized_target"]
        authorized_target.parent.mkdir(parents=True)
        unauthorized_target.parent.mkdir(parents=True)
        authorized_target.write_bytes(b"R5-video-before")
        unauthorized_target.write_bytes(b"R5-secret-never-read")
        request_relative = "context/requests/r5_protected.json"
        context_relative = "context/work/r5_protected.json"
        payload_relative = "context/payloads/r5_protected.json"
        request = _acceptance_task_request(
            "task.r5.protected", target_paths=[expected["authorized_target"]], target_kinds=["video"],
            include_scopes=[expected["authorized_scope"]], task_tags=["video", "protected"],
            actions=["read", "write"], authorized_protected_scopes=[expected["authorized_scope"]],
            write_payload_path=payload_relative,
        )
        write_json_atomic(root / request_relative, request)
        context = resolve_request(root, request_relative, context_relative)
        write_json_atomic(
            root / payload_relative,
            {"operations": [{
                "target_path": expected["authorized_target"], "operation": "write_binary",
                "content_base64": base64.b64encode(b"R5-video-after").decode("ascii"),
            }]},
        )
        write_fixture(root, context_relative, payload_relative)
        close_result = close_protected_context(root, context_relative)
        try:
            write_fixture(root, context_relative, payload_relative)
            reuse_after_close = "accepted"
        except ContextSystemError:
            reuse_after_close = "rejected"
        unauthorized_request = _acceptance_task_request(
            "task.r5.protected.escape", target_paths=[expected["unauthorized_target"]], target_kinds=["video"],
            include_scopes=[expected["authorized_scope"]], task_tags=["video", "protected"],
            authorized_protected_scopes=[expected["authorized_scope"]],
        )
        write_json_atomic(root / "context/requests/r5_protected_escape.json", unauthorized_request)
        try:
            resolve_request(root, "context/requests/r5_protected_escape.json", "context/work/r5_protected_escape.json")
            unauthorized_rejected = False
        except ContextSystemError:
            unauthorized_rejected = True
        global_entries = [
            record["path"] for record in load_file_catalog(root)
            if PurePosixPath(record["path"]).parts and PurePosixPath(record["path"]).parts[0] in {"inputs", "outputs"}
        ]
        manifest_paths = [record["path"] for record in context["protected_file_manifest"]]
        evidence = {
            "authorized_manifest_paths": manifest_paths,
            "unauthorized_rejected": unauthorized_rejected,
            "global_catalog_entries": len(global_entries),
            "reuse_after_close": reuse_after_close,
            "scope_close_event": close_result["event_id"],
            "data_deleted": not authorized_target.exists(),
            "authorized_content_hash": sha256_file(authorized_target),
        }
        passed = (
            manifest_paths == [expected["authorized_target"]]
            and unauthorized_rejected
            and evidence["global_catalog_entries"] == expected["global_catalog_entries"]
            and evidence["reuse_after_close"] == expected["reuse_after_close"]
            and not evidence["data_deleted"]
        )
        return passed, evidence


def _scenario_real_task_leakage(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        root.mkdir()
        _acceptance_copy_project(root_source, root)
        protected_path = root / "inputs/r5-video-task/source.mp4"
        protected_path.parent.mkdir(parents=True)
        protected_path.write_bytes(b"R5-video")
        requests = {
            "report": _acceptance_task_request(
                "task.r5.leakage.report",
                target_paths=["docs/reports/2026-07-21_R-4_검색_평가_결과.md"],
                target_kinds=["report"], include_scopes=["docs/reports"], task_tags=["report"],
            ),
            "knowledge": _acceptance_task_request(
                "task.r5.leakage.knowledge", target_paths=["knowledge/items.jsonl"],
                target_kinds=["knowledge"], include_scopes=["knowledge"], task_tags=["knowledge"],
                target_record_ids=["knowledge.context.shared-work-context"],
            ),
            "video": _acceptance_task_request(
                "task.r5.leakage.video", target_paths=["inputs/r5-video-task/source.mp4"],
                target_kinds=["video"], include_scopes=["inputs/r5-video-task"], task_tags=["video"],
                authorized_protected_scopes=["inputs/r5-video-task"],
            ),
        }
        expected_by_label = {task["task_label"]: task for task in expected["tasks"]}
        task_evidence: list[dict[str, Any]] = []
        total_leakage = 0
        exact = True
        for label in ("report", "knowledge", "video"):
            request_path = f"context/requests/r5_leakage_{label}.json"
            context_path = f"context/work/r5_leakage_{label}.json"
            write_json_atomic(root / request_path, requests[label])
            context = resolve_request(root, request_path, context_path)
            actual_rules = sorted(context["selection_ids"]["rules"])
            actual_files = sorted(item["path"] for item in context["read_manifest"])
            expected_rules = sorted(expected_by_label[label]["expected_rule_ids"])
            expected_files = sorted(expected_by_label[label]["expected_file_paths"])
            unexpected_rules = sorted(set(actual_rules) - set(expected_rules))
            unexpected_files = sorted(set(actual_files) - set(expected_files))
            missing_rules = sorted(set(expected_rules) - set(actual_rules))
            missing_files = sorted(set(expected_files) - set(actual_files))
            leakage = len(unexpected_rules) + len(unexpected_files)
            total_leakage += leakage
            exact = exact and not (unexpected_rules or unexpected_files or missing_rules or missing_files)
            task_evidence.append({
                "task_label": label, "selected_rule_ids": actual_rules, "selected_file_paths": actual_files,
                "unexpected_rule_ids": unexpected_rules, "unexpected_file_paths": unexpected_files,
                "missing_rule_ids": missing_rules, "missing_file_paths": missing_files, "leakage": leakage,
            })
        evidence = {"tasks": task_evidence, "rule_file_leakage": total_leakage, "exact_selection": exact}
        passed = exact and total_leakage <= expected["maximum_rule_file_leakage"]
        return passed, evidence


def _scenario_feedback_next_context(root_source: Path, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        root.mkdir()
        _acceptance_copy_project(root_source, root)
        timestamp = "2026-07-21T03:15:00+09:00"
        source_id = "source.repo.project-rules"
        candidate = _acceptance_knowledge_record(
            expected["knowledge_id"], "R-5 feedback must reach the next context.", source_id,
            timestamp, task_tags=["r5-feedback"],
        )
        create_path = "context/payloads/r5_feedback_create.json"
        write_json_atomic(root / create_path, {
            "operation_id": "op.r5.feedback.create", "task_id": "task.r5.feedback",
            "action": "create_candidate", "actor": "r5-acceptance", "timestamp": timestamp,
            "reason": "R-5 event-to-candidate fixture.", "record": candidate,
        })
        maintain_knowledge(root, create_path)
        filters = {"kinds": ["knowledge"], "statuses": ["verified"], "task_tags": ["r5-feedback"], "retrieval_eligible": True}
        pre_request = _acceptance_task_request(
            "task.r5.feedback.pre", target_paths=[], target_kinds=["knowledge"],
            include_scopes=["knowledge"], task_tags=["knowledge"], record_filters=filters,
        )
        write_json_atomic(root / "context/requests/r5_feedback_pre.json", pre_request)
        pre_context = resolve_request(root, "context/requests/r5_feedback_pre.json", "context/work/r5_feedback_pre.json")
        pre_selected = expected["knowledge_id"] in pre_context["selection_ids"]["records"]
        current = next(item for item in load_jsonl(root / "knowledge/items.jsonl") if item["knowledge_id"] == expected["knowledge_id"])
        review_path = "context/payloads/r5_feedback_review.json"
        write_json_atomic(root / review_path, {
            "operation_id": "op.r5.feedback.review", "task_id": "task.r5.feedback",
            "action": "review", "outcome": "verified", "knowledge_id": expected["knowledge_id"],
            "expected_record_hash": sha256_text(canonical_json(current)), "expected_revision": current["revision"],
            "actor": "r5-acceptance", "timestamp": timestamp,
            "reason": "R-5 reviewed the feedback candidate.",
        })
        maintain_knowledge(root, review_path)
        post_request = _acceptance_task_request(
            "task.r5.feedback.post", target_paths=[], target_kinds=["knowledge"],
            include_scopes=["knowledge"], task_tags=["knowledge"], record_filters=filters,
        )
        write_json_atomic(root / "context/requests/r5_feedback_post.json", post_request)
        post_context = resolve_request(root, "context/requests/r5_feedback_post.json", "context/work/r5_feedback_post.json")
        post_selected = expected["knowledge_id"] in post_context["selection_ids"]["records"]
        event_types = [event["event_type"] for event in load_jsonl(root / "records/work/events.jsonl")]
        evidence = {
            "pre_review_selected": pre_selected,
            "post_review_selected": post_selected,
            "required_event_types_present": sorted(set(expected["event_types"]) & set(event_types)),
            "selected_record_ids": post_context["selection_ids"]["records"],
        }
        passed = (
            pre_selected is expected["pre_review_selected"]
            and post_selected is expected["post_review_selected"]
            and set(expected["event_types"]) <= set(event_types)
        )
        return passed, evidence


def evaluate_operational_acceptance(root: Path, evaluation_path: str, output_path: str) -> dict[str, Any]:
    evaluation_relative = assert_allowed_path(evaluation_path, root)
    output_relative = assert_allowed_path(output_path, root)
    evaluation = load_json(root / evaluation_relative)
    missing = validate_required(evaluation, root / "schemas/operational_acceptance.schema.json")
    if missing:
        raise ContextSystemError(f"operational acceptance missing fields: {missing}")
    scenario_ids = [scenario["scenario_id"] for scenario in evaluation["scenarios"]]
    scenario_kinds = [scenario["scenario_kind"] for scenario in evaluation["scenarios"]]
    if len(scenario_ids) != 9 or len(set(scenario_ids)) != 9 or len(set(scenario_kinds)) != 9:
        raise ContextSystemError("R-5 acceptance requires nine unique scenario IDs and kinds")
    handlers = {
        "file_lifecycle": lambda expected: _scenario_file_lifecycle(expected),
        "source_review_transition": lambda expected: _scenario_source_review(root, expected),
        "conflict_supersession_coexistence": lambda expected: _scenario_conflict_supersession(root, expected),
        "partial_failure_resume": lambda expected: _scenario_partial_failure(expected),
        "index_delete_cold_rebuild": lambda expected: _scenario_cold_rebuild(root, expected),
        "new_session_cold_start": lambda expected: _scenario_new_session(root, expected),
        "protected_namespace_isolation": lambda expected: _scenario_protected_namespace(root, expected),
        "real_task_leakage": lambda expected: _scenario_real_task_leakage(root, expected),
        "feedback_next_context": lambda expected: _scenario_feedback_next_context(root, expected),
    }
    scenario_results: list[dict[str, Any]] = []
    for scenario in evaluation["scenarios"]:
        try:
            passed, evidence = handlers[scenario["scenario_kind"]](scenario["expected"])
            error = None
        except Exception as exc:  # noqa: BLE001 - every scenario must report its failure independently
            passed, evidence, error = False, {}, f"{type(exc).__name__}: {exc}"
        scenario_results.append({
            "scenario_id": scenario["scenario_id"],
            "scenario_kind": scenario["scenario_kind"],
            "passed": passed,
            "evidence": evidence,
            "error": error,
        })
    leakage = sum(
        result["evidence"].get("rule_file_leakage", 0)
        for result in scenario_results
    )
    summary = {
        "scenarios": len(scenario_results),
        "passed": sum(result["passed"] for result in scenario_results),
        "failed": sum(not result["passed"] for result in scenario_results),
        "rule_file_leakage": leakage,
    }
    thresholds = evaluation["thresholds"]
    ok = (
        summary["scenarios"] == thresholds["required_scenarios"]
        and summary["failed"] <= thresholds["maximum_failed"]
        and leakage <= thresholds["maximum_rule_file_leakage"]
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": evaluation["evaluation_id"],
        "evaluated_at": now_iso(),
        "source_evaluation_path": evaluation_relative,
        "source_evaluation_sha256": sha256_file(root / evaluation_relative),
        "scenarios": scenario_results,
        "logical_result_hash": sha256_text(canonical_json(scenario_results)),
        "summary": summary,
        "ok": ok,
    }
    before_hash = sha256_file(root / output_relative) if (root / output_relative).exists() else None
    write_json_atomic(root / output_relative, result)
    event = append_event(
        root, "operational_acceptance_evaluated", "task.r5.evaluate",
        [evaluation_relative, output_relative],
        {evaluation_relative: sha256_file(root / evaluation_relative), output_relative: before_hash},
        {evaluation_relative: sha256_file(root / evaluation_relative), output_relative: sha256_file(root / output_relative)},
        "success" if ok else "failed",
        {"evaluation_id": evaluation["evaluation_id"], "summary": summary},
    )
    if (root / "catalog/bootstrap.json").exists():
        sync_catalog(root)
    return {**result, "event_id": event["event_id"]}


def cli() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Deterministic project context, lifecycle, and retrieval system")
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Project root")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("bootstrap")
    subparsers.add_parser("sync")
    subparsers.add_parser("validate")
    plan_parser = subparsers.add_parser("plan-file")
    plan_parser.add_argument("--path", required=True)
    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--request", required=True)
    resolve_parser.add_argument("--output", required=True)
    write_parser = subparsers.add_parser("write-fixture")
    write_parser.add_argument("--context", required=True)
    write_parser.add_argument("--payload", required=True)
    knowledge_parser = subparsers.add_parser("maintain-knowledge")
    knowledge_parser.add_argument("--operation", required=True)
    source_parser = subparsers.add_parser("check-sources")
    source_parser.add_argument("--task-id", default="task.source.hash-check")
    source_review_parser = subparsers.add_parser("maintain-source")
    source_review_parser.add_argument("--operation", required=True)
    close_protected_parser = subparsers.add_parser("close-protected-context")
    close_protected_parser.add_argument("--context", required=True)
    evaluation_parser = subparsers.add_parser("evaluate-retrieval")
    evaluation_parser.add_argument("--evaluation", required=True)
    evaluation_parser.add_argument("--output", required=True)
    acceptance_parser = subparsers.add_parser("evaluate-operations")
    acceptance_parser.add_argument("--evaluation", required=True)
    acceptance_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        with repository_lock(root):
            if args.command == "bootstrap":
                result = bootstrap(root)
            elif args.command == "sync":
                result = sync_catalog(root)
            elif args.command == "validate":
                result = validate_project(root)
            elif args.command == "plan-file":
                result = plan_file(root, args.path)
            elif args.command == "resolve":
                result = resolve_request(root, args.request, args.output)
            elif args.command == "write-fixture":
                result = write_fixture(root, args.context, args.payload)
            elif args.command == "maintain-knowledge":
                result = maintain_knowledge(root, args.operation)
            elif args.command == "check-sources":
                result = check_source_hashes(root, args.task_id)
            elif args.command == "maintain-source":
                result = maintain_source(root, args.operation)
            elif args.command == "close-protected-context":
                result = close_protected_context(root, args.context)
            elif args.command == "evaluate-retrieval":
                result = evaluate_retrieval(root, args.evaluation, args.output)
            elif args.command == "evaluate-operations":
                result = evaluate_operational_acceptance(root, args.evaluation, args.output)
            else:  # pragma: no cover
                raise ContextSystemError(f"unsupported command: {args.command}")
    except ContextSystemError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not isinstance(result, dict) or result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(cli())
