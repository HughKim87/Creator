"""Deterministic R-2A/R-2B task-scoped context and corpus system.

This module uses only the Python standard library. Markdown and JSON/JSONL are
the canonical project artifacts; catalogs and work contexts are deterministic
views with explicit integrity policies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote


SCHEMA_VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_TOP_LEVEL = {"backup", "inputs", "outputs", ".git", ".agents", ".codex"}
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
CATALOG_PROJECTIONS = {
    "catalog/files.jsonl",
    "catalog/records.jsonl",
    "catalog/rules.jsonl",
    "catalog/units.jsonl",
}
CORPUS_JSONL_PATHS = ["knowledge/decisions.jsonl", "knowledge/items.jsonl"]
SOURCE_STORE_PATH = "knowledge/sources.jsonl"
RELATION_STORE_PATH = "knowledge/relations.jsonl"
CASE_ROOT = "knowledge/cases"
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


class ContextSystemError(RuntimeError):
    """Raised when scope, contract, or integrity validation fails."""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


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


def write_text_atomic(path: Path, content: str) -> None:
    if "\x00" in content:
        raise ContextSystemError(f"refusing NUL content: {path}")
    content.encode("utf-8", errors="strict")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


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


def classify_file(path: str, root: Path = PROJECT_ROOT, status: str = "active") -> dict[str, Any]:
    normalized = assert_allowed_path(path, root)
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
        "tools/context/context_system.py": ("code", "Implement deterministic R-2A/R-2B parsing, cataloging, corpus resolving, validation, and Markdown writing.", "project_agents", "active_implementation", ["context_system_execution"], ["approved_implementation_change"]),
        "tests/context/test_context_system.py": ("test", "Verify R-2A/R-2B context-system contracts.", "project_agents", "active_test", ["r2a_validation", "r2b_validation"], ["test_maintenance"]),
    }
    if normalized in special:
        kind, purpose, owner, authority, read_when, write_when = special[normalized]
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
        unit_strategy = "whole_file"
        validators = ["validate.utf8", "validate.nul", "validate.python_compile"]
    else:
        unit_strategy = "whole_file"
        validators = ["validate.content_hash"]

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

    return {
        "schema_version": SCHEMA_VERSION,
        "file_id": file_id_for_path(normalized),
        "path": normalized,
        "kind": kind,
        "purpose": purpose,
        "owner": owner,
        "authority": authority,
        "status": status,
        "language": language,
        "sensitivity": "public_project",
        "index_scope": "none" if authority in {"derived", "retained_evidence"} else "global",
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
        "observed_at": now_iso(),
        "moved_from": [],
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
    id_fields = ("decision_id", "knowledge_id", "case_id", "source_id", "relation_id", "file_id", "rule_id", "unit_id", "event_id", "task_id", "context_id", "id")
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


def make_unit(
    file_record: dict[str, Any],
    unit_id: str,
    locator_type: str,
    locator: str,
    purpose: str,
    content: str,
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
        "status": "active",
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
    strategy = file_record["unit_strategy"]
    text = read_utf8(path)
    if strategy == "markdown_heading":
        return markdown_units(text, file_record)
    if strategy == "json_pointer":
        return json_pointer_units(json.loads(text), file_record)
    if strategy == "jsonl_record_id":
        return jsonl_units(load_jsonl(path), file_record)
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
    planned = {
        record["path"]: record
        for record in existing
        if record.get("status") == "planned" and not (root / record["path"]).exists()
    }
    paths = iter_project_files(root)
    if "catalog/files.jsonl" not in paths:
        paths.append("catalog/files.jsonl")
    records = [classify_file(path, root, "active") for path in sorted(set(paths))]
    for path in sorted(planned):
        records.append(classify_file(path, root, "planned"))
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
        "target_paths": [assert_allowed_path(item, root) for item in target_paths],
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
    records.append(classify_file(normalized, root, "planned"))
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
        {"status": "planned"},
    )
    sync_catalog(root)
    return {"file_id": file_id_for_path(normalized), "path": normalized, "event_id": event["event_id"]}


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
    required = load_json(root / "schemas/task_request.schema.json")["required"]
    missing = [field for field in required if field not in request]
    if missing:
        raise ContextSystemError(f"task request missing fields: {missing}")
    for target in request["target_paths"]:
        assert_allowed_path(target, root)
    for scope in request["include_scopes"]:
        assert_allowed_path(scope, root)
    for scope in request["exclude_scopes"]:
        normalized = normalize_path(scope, root)
        if normalized.split("/", 1)[0] not in PROTECTED_TOP_LEVEL:
            assert_allowed_path(normalized, root)


def resolve_request(root: Path, request_path: str, output_path: str) -> dict[str, Any]:
    request_relative = assert_allowed_path(request_path, root)
    output_relative = assert_allowed_path(output_path, root)
    sync_catalog(root)
    request = load_json(root / request_relative)
    validate_task_request(request, root)
    request_hash = sha256_text(canonical_json(request))
    rules = load_jsonl(root / "catalog/rules.jsonl")
    files = load_file_catalog(root)
    units = load_jsonl(root / "catalog/units.jsonl")
    corpus_records = load_jsonl(root / "catalog/records.jsonl")
    source_records = load_jsonl(root / SOURCE_STORE_PATH)
    relation_records = load_jsonl(root / RELATION_STORE_PATH)
    files_by_path = {record["path"]: record for record in files}
    files_by_id = {record["file_id"]: record for record in files}
    units_by_id = {record["unit_id"]: record for record in units}
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
        normalized = assert_allowed_path(target_path, root)
        record = files_by_path.get(normalized)
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
            for unit in units
            if unit["file_id"] == file_record["file_id"] and unit["locator"].split(" > ")[-1] == f"heading:{rule_id}"
        ]
        if not candidates:
            candidates = [unit for unit in units if unit["file_id"] == file_record["file_id"] and rule_id in unit["locator"]]
        for unit in candidates:
            selected_unit_ids[unit["unit_id"]] = f"selected_rule:{rule_id}"

    requested_record_ids = request.get("target_record_ids", [])
    selected_record_ids: dict[str, str] = {}
    for requested_id in requested_record_ids:
        record = records_by_id.get(requested_id)
        if not record:
            raise ContextSystemError(f"target record ID is not registered: {requested_id}")
        selected_record_ids[requested_id] = "exact_target_record"
    selected_relations: list[dict[str, Any]] = []
    for relation in relation_records:
        if relation.get("status") != "active" or relation.get("review_status") != "verified" or not relation.get("retrieval_eligible"):
            continue
        source_id = relation["source_record_id"]
        target_id = relation["target_record_id"]
        if source_id in requested_record_ids or target_id in requested_record_ids:
            selected_relations.append(relation)
            other_id = target_id if source_id in requested_record_ids else source_id
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

    write_contract: dict[str, Any] | None = None
    if set(request["actions"]) & {"create", "write"}:
        targets = []
        for record in target_records:
            if not record["path"].endswith(".md"):
                raise ContextSystemError(f"R-2A writer only supports Markdown: {record['path']}")
            if record["status"] == "planned" and "create" not in request["actions"]:
                raise ContextSystemError(f"planned target requires create action: {record['path']}")
            target_units = [unit for unit in units if unit["file_id"] == record["file_id"]]
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
            "allowed_actions": sorted(set(request["actions"]) & {"create", "write"}),
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
        "authority": {
            "user_scope": {"include": request["include_scopes"], "exclude": request["exclude_scopes"]},
            "kernel_rule_ids": KERNEL_RULE_IDS,
            "selected_conditional_rule_ids": selected_rules,
            "predicate_evidence": predicate_evidence,
        },
        "read_manifest": read_manifest,
        "record_manifest": record_manifest,
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
        {"selected_rules": selected_rules, "selected_files": sorted(selected_file_ids), "selected_units": sorted(selected_unit_ids), "selected_records": sorted(selected_record_ids), "selected_relations": [record["relation_id"] for record in selected_relations]},
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
                destination.relative_to(root.resolve())
            except ValueError:
                errors.append(f"link escapes project: {relative} -> {target}")
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
                errors.append(f"source path missing: {source['source_id']} -> {normalized}")
            elif source.get("content_sha256") != sha256_file(path):
                errors.append(f"source content hash mismatch: {source['source_id']}")
        if source.get("status") == "historical_candidate":
            if source.get("retrieval_eligible") or source.get("authority") in {"active_policy", "active_contract"}:
                errors.append(f"historical candidate became active instruction: {source['source_id']}")
    for relation in relations:
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
    if len(parsed_rules) != 21 or len({rule["rule_id"] for rule in parsed_rules}) != 21:
        errors.append("conditional rules are not 21 unique records")
    if set(mapped_ids) != set(kernel_ids) | {rule["rule_id"] for rule in parsed_rules}:
        errors.append("bootstrap rule mapping does not match live kernel and packs")
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

    link_errors, link_count = validate_markdown_links(root, actual_paths)
    errors.extend(link_errors)
    errors.extend(validate_event_chain(root))
    corpus_errors, corpus_counts = validate_corpus(root)
    errors.extend(corpus_errors)
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
            "events": len(load_jsonl(root / "records/work/events.jsonl")),
            **corpus_counts,
            "local_links": link_count,
            "orphan_files": len(orphan_paths),
        },
    }


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
    raise ContextSystemError(f"unsupported Markdown operation: {mode}")


def write_fixture(root: Path, context_path: str, payload_path: str) -> dict[str, Any]:
    context_relative = assert_allowed_path(context_path, root)
    payload_relative = assert_allowed_path(payload_path, root)
    context = load_json(root / context_relative)
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
    operation_paths = [assert_allowed_path(operation["target_path"], root) for operation in operations]
    if len(set(operation_paths)) != len(operation_paths):
        raise ContextSystemError("write rejected: duplicate payload target")
    if set(operation_paths) != set(contract_targets):
        raise ContextSystemError("write rejected: payload targets do not match contract targets")

    rendered: dict[str, str] = {}
    before_hashes: dict[str, str | None] = {}
    for operation, normalized in zip(operations, operation_paths):
        target = contract_targets[normalized]
        path = root / normalized
        if path.suffix.lower() != ".md":
            raise ContextSystemError(f"write rejected: non-Markdown target {normalized}")
        exists = path.exists()
        actual_before = sha256_file(path) if exists else None
        if actual_before != target["before_file_hash"]:
            raise ContextSystemError(f"write rejected: before hash mismatch for {normalized}")
        if target["status"] == "planned" and exists:
            raise ContextSystemError(f"write rejected: planned target already exists {normalized}")
        if target["status"] == "active" and not exists:
            raise ContextSystemError(f"write rejected: active target is missing {normalized}")
        current = read_utf8(path) if exists else None
        content = apply_payload_operation(root, operation, current)
        if "\x00" in content:
            raise ContextSystemError(f"write rejected: NUL content for {normalized}")
        if content.count("```") % 2:
            raise ContextSystemError(f"write rejected: unbalanced Markdown fence for {normalized}")
        rendered[normalized] = content
        before_hashes[normalized] = actual_before

    after_hashes: dict[str, str | None] = {}
    for normalized in operation_paths:
        write_text_atomic(root / normalized, rendered[normalized])
        after_hashes[normalized] = sha256_file(root / normalized)
    event = append_event(
        root,
        "write_applied",
        context["request"]["task_id"],
        operation_paths,
        before_hashes,
        after_hashes,
        "success",
        {"contract_id": contract["contract_id"], "payload_path": payload_relative},
    )
    counts = sync_catalog(root)
    return {"event_id": event["event_id"], "after_hashes": after_hashes, **counts}


def cli() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="R-2A deterministic context system")
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
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
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
        else:  # pragma: no cover
            raise ContextSystemError(f"unsupported command: {args.command}")
    except ContextSystemError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not isinstance(result, dict) or result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(cli())
