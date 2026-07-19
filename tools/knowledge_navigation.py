"""Bounded L3.1 document-routing benchmark and fail-closed Graphify audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Sequence
from urllib.parse import unquote


ACTIVE_MARKDOWN_ALLOWLIST = (
    "AGENTS.md",
    "PROJECT_RULES.md",
    "SESSION_HANDOFF.md",
    "docs/agent/DOCUMENT_REGISTRY.md",
    "docs/agent/REBUILD_PRINCIPLES.md",
    "docs/agent/REBUILD_PLAN.md",
    "docs/agent/RECONSTRUCTION_MAP.md",
    "docs/agent/WORKFLOW_FOUNDATION.md",
    "docs/agent/EDITING_QUALITY_RULES.md",
    "docs/agent/TOOL_REQUIREMENTS.md",
    "docs/agent/SKILL_REQUIREMENTS.md",
    "docs/agent/FILE_DATA_CONTRACT.md",
)

PROTECTED_PREFIXES = tuple(
    f"{directory}/" for directory in ("inputs", "outputs", "backup", ".git", ".agents", ".codex")
)

PROFILE_SOURCES = {
    "resume_current_work": (
        "AGENTS.md",
        "PROJECT_RULES.md",
        "SESSION_HANDOFF.md",
    ),
    "change_document_route": (
        "AGENTS.md",
        "PROJECT_RULES.md",
        "SESSION_HANDOFF.md",
        "docs/agent/DOCUMENT_REGISTRY.md",
        "docs/agent/RECONSTRUCTION_MAP.md",
    ),
    "handle_video_task_state": (
        "AGENTS.md",
        "PROJECT_RULES.md",
        "SESSION_HANDOFF.md",
        "docs/agent/FILE_DATA_CONTRACT.md",
    ),
}

PROFILE_MARKERS = {
    "resume_current_work": ("`PROJECT_RULES.md`", "`SESSION_HANDOFF.md`"),
    "change_document_route": ("`docs/agent/DOCUMENT_REGISTRY.md`", "affected active documents"),
    "handle_video_task_state": ("`docs/agent/FILE_DATA_CONTRACT.md`", "exact designated `state.json`"),
}

MANDATORY_STARTUP_SOURCES = set(PROFILE_SOURCES["resume_current_work"])

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PATH_KEYS = {"file", "file_path", "path", "source", "source_file"}
VALID_CONFIDENCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}

PROFILE_QUESTIONS = {
    "resume_current_work": "Which documents govern resuming the current project work?",
    "change_document_route": "Which documents govern changing the document route?",
    "handle_video_task_state": "Which documents govern handling video task state?",
}

TYPED_PROFILE_QUERIES = {
    "resume_current_work": {
        "route_id": "resume_current_work",
        "selector_value": None,
        "selected_paths": (),
    },
    "change_document_route": {
        "route_id": "change_document_route",
        "selector_value": "affected document authority",
        "selected_paths": ("docs/agent/RECONSTRUCTION_MAP.md",),
    },
    "handle_video_task_state": {
        "route_id": "handle_video_task_state",
        "selector_value": "exact designated task state",
        "selected_paths": ("outputs/synthetic_baseline/state.json",),
    },
}

QUERY_SOURCE = re.compile(r"\[src=(.*?) loc=")
INLINE_CODE = re.compile(r"`([^`]+)`")
ROUTE_GRAPH_SCHEMA_VERSION = 1
ROUTE_GRAPH_SOURCE_PATHS = (
    "AGENTS.md",
    "docs/agent/DOCUMENT_REGISTRY.md",
)
ROUTE_READ_RELATIONS = {"always_read", "read_when_current_work", "requires"}
ROUTE_EDGE_RELATIONS = ROUTE_READ_RELATIONS | {"writes_to"}


def _profile_row(agents_text: str, profile: str) -> str:
    prefix = f"| `{profile}` |"
    lines = agents_text.splitlines()
    try:
        start = lines.index("## Validated representative profiles")
    except ValueError as error:
        raise ValueError("missing validated representative profiles") from error
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.startswith(prefix):
            return line
    raise ValueError(f"missing routing profile: {profile}")


def _validate_direct_route(agents_text: str, profile: str) -> tuple[str, ...]:
    row = _profile_row(agents_text, profile)
    missing = [marker for marker in PROFILE_MARKERS[profile] if marker not in row]
    if missing:
        raise ValueError(f"routing profile {profile} lacks markers: {missing}")
    return PROFILE_SOURCES[profile]


def _estimated_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def _unresolved_links(root: Path, relative_path: str, text: str) -> list[str]:
    unresolved: list[str] = []
    source = root / relative_path
    for raw_target in MARKDOWN_LINK.findall(text):
        target = unquote(raw_target.strip().split("#", 1)[0])
        if not target or "://" in target or target.startswith(("mailto:", "data:")):
            continue
        if not (source.parent / target).resolve().exists():
            unresolved.append(raw_target)
    return unresolved


def _synthetic_state() -> dict[str, Any]:
    return {
        "schema_version": 3,
        "project_id": "synthetic_baseline",
        "current_stage": "analysis",
        "reference_input": {
            "source_id": "synthetic_source_001",
            "path": "inputs/synthetic_sample.mp4",
            "fingerprint": {
                "algorithm": "sha256",
                "digest": "0" * 64,
                "size_bytes": 0,
            },
        },
        "outputs": [],
        "next_action": "review_analysis",
        "blocker": None,
        "user_decision": None,
        "validation_level": "structure_validated",
    }


def build_direct_baseline(root: Path, output_path: Path, iterations: int = 100) -> dict[str, Any]:
    root = root.resolve()
    output_path = output_path.resolve()
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")

    missing_allowlist = [path for path in ACTIVE_MARKDOWN_ALLOWLIST if not (root / path).is_file()]
    if missing_allowlist:
        raise ValueError(f"allowlisted sources missing: {missing_allowlist}")

    fixture_path = output_path.parent / "synthetic_workspace" / "outputs" / "synthetic_baseline" / "state.json"
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_text = json.dumps(_synthetic_state(), ensure_ascii=False, indent=2) + "\n"
    fixture_path.write_text(fixture_text, encoding="utf-8", newline="\n")

    profiles: dict[str, Any] = {}
    for profile in PROFILE_SOURCES:
        timings: list[float] = []
        selected: tuple[str, ...] = ()
        for _ in range(iterations):
            started = time.perf_counter()
            selected = _validate_direct_route(agents_text, profile)
            timings.append((time.perf_counter() - started) * 1000)

        source_rows: list[dict[str, Any]] = []
        unresolved: list[dict[str, str]] = []
        for relative_path in selected:
            text = (root / relative_path).read_text(encoding="utf-8")
            source_rows.append(
                {
                    "path": relative_path,
                    "characters": len(text),
                    "estimated_tokens": _estimated_tokens(text),
                }
            )
            unresolved.extend(
                {"source": relative_path, "target": target}
                for target in _unresolved_links(root, relative_path, text)
            )

        if profile == "handle_video_task_state":
            source_rows.append(
                {
                    "path": str(fixture_path),
                    "scope": "synthetic_exact_state_not_graphified",
                    "characters": len(fixture_text),
                    "estimated_tokens": _estimated_tokens(fixture_text),
                }
            )

        expected = set(PROFILE_SOURCES[profile])
        actual = set(selected)
        profiles[profile] = {
            "selected_sources": source_rows,
            "total_estimated_tokens": sum(row["estimated_tokens"] for row in source_rows),
            "median_route_selection_ms": round(statistics.median(timings), 6),
            "wrong_authority_selections": sorted(actual.symmetric_difference(expected)),
            "unresolved_local_links": unresolved,
        }

    result = {
        "schema_version": 1,
        "measurement": "direct_markdown_routing_baseline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "token_estimator": "ceil(characters / 4)",
        "iterations_per_profile": iterations,
        "allowlisted_framework_sources": list(ACTIVE_MARKDOWN_ALLOWLIST),
        "protected_path_reads": 0,
        "profiles": profiles,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def _iter_path_values(value: Any, key: str | None = None) -> Iterable[str]:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            yield from _iter_path_values(child_value, str(child_key))
    elif isinstance(value, list):
        for child in value:
            yield from _iter_path_values(child, key)
    elif isinstance(value, str) and key in PATH_KEYS:
        yield value


def _normalize_graph_path(value: str, root: Path) -> str | None:
    path_value = unquote(value.strip()).split("#", 1)[0]
    candidate = Path(path_value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError:
        return None
    normalized = relative.as_posix()
    return normalized if normalized.endswith(".md") else None


def audit_graph(graph_path: Path, root: Path) -> dict[str, Any]:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    discovered: set[str] = set()
    external_paths: set[str] = set()
    for value in _iter_path_values(graph):
        normalized = _normalize_graph_path(value, root)
        if normalized is None:
            if value.lower().endswith(".md"):
                external_paths.add(value)
            continue
        discovered.add(normalized)

    protected = sorted(
        path for path in discovered if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    unexpected = sorted(path for path in discovered if path not in ACTIVE_MARKDOWN_ALLOWLIST)
    nodes = graph.get("nodes", [])
    links = graph.get("links", graph.get("edges", []))
    node_ids = {str(node.get("id")) for node in nodes if node.get("id") is not None}
    missing_node_source = sorted(
        str(node.get("id", f"node[{index}]"))
        for index, node in enumerate(nodes)
        if not isinstance(node.get("source_file"), str)
        or _normalize_graph_path(node["source_file"], root) not in ACTIVE_MARKDOWN_ALLOWLIST
    )
    invalid_edge_confidence = sorted(
        index
        for index, link in enumerate(links)
        if str(link.get("confidence", "")).upper() not in VALID_CONFIDENCE
    )
    invalid_edge_relation = sorted(
        index for index, link in enumerate(links) if not str(link.get("relation", "")).strip()
    )
    invalid_edge_source = sorted(
        index
        for index, link in enumerate(links)
        if not isinstance(link.get("source_file"), str)
        or _normalize_graph_path(link["source_file"], root) not in ACTIVE_MARKDOWN_ALLOWLIST
    )
    orphan_edges = sorted(
        index
        for index, link in enumerate(links)
        if str(link.get("source")) not in node_ids or str(link.get("target")) not in node_ids
    )
    return {
        "graph_path": str(graph_path.resolve()),
        "discovered_markdown_sources": sorted(discovered),
        "protected_path_nodes": protected,
        "unexpected_markdown_sources": unexpected,
        "external_markdown_paths": sorted(external_paths),
        "missing_or_invalid_node_sources": missing_node_source,
        "invalid_edge_confidence": invalid_edge_confidence,
        "invalid_edge_relation": invalid_edge_relation,
        "invalid_edge_source": invalid_edge_source,
        "orphan_edges": orphan_edges,
        "passed": not any((
            protected,
            unexpected,
            external_paths,
            missing_node_source,
            invalid_edge_confidence,
            invalid_edge_relation,
            invalid_edge_source,
            orphan_edges,
        )),
    }


def sanitize_graph(input_path: Path, output_path: Path, root: Path) -> dict[str, Any]:
    """Copy only traceable allowlisted nodes and fully labelled edges."""
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if input_path == output_path:
        raise ValueError("sanitized graph must use a new output path")

    graph = json.loads(input_path.read_text(encoding="utf-8"))
    original_nodes = graph.get("nodes", [])
    original_links = graph.get("links", graph.get("edges", []))
    kept_nodes: list[dict[str, Any]] = []
    kept_ids: set[str] = set()
    dropped_node_ids: list[str] = []
    for index, raw_node in enumerate(original_nodes):
        node = dict(raw_node)
        node_id = str(node.get("id", f"node[{index}]"))
        source_file = node.get("source_file")
        normalized = (
            _normalize_graph_path(source_file, root)
            if isinstance(source_file, str)
            else None
        )
        if normalized not in ACTIVE_MARKDOWN_ALLOWLIST:
            dropped_node_ids.append(node_id)
            continue
        node["source_file"] = normalized
        if "#" in source_file and not node.get("source_location"):
            node["source_location"] = "#" + source_file.split("#", 1)[1]
        kept_nodes.append(node)
        kept_ids.add(node_id)

    kept_links: list[dict[str, Any]] = []
    dropped_edge_indexes: list[int] = []
    for index, raw_link in enumerate(original_links):
        link = dict(raw_link)
        confidence = str(link.get("confidence", "")).upper()
        relation = str(link.get("relation", "")).strip()
        source_file = link.get("source_file")
        normalized = (
            _normalize_graph_path(source_file, root)
            if isinstance(source_file, str)
            else None
        )
        if (
            str(link.get("source")) not in kept_ids
            or str(link.get("target")) not in kept_ids
            or confidence not in VALID_CONFIDENCE
            or not relation
            or normalized not in ACTIVE_MARKDOWN_ALLOWLIST
        ):
            dropped_edge_indexes.append(index)
            continue
        link["confidence"] = confidence
        link["relation"] = relation
        link["source_file"] = normalized
        kept_links.append(link)

    graph["nodes"] = kept_nodes
    if "links" in graph:
        graph["links"] = kept_links
    else:
        graph["edges"] = kept_links
    if "hyperedges" in graph:
        graph["hyperedges"] = []
    graph["navigation_sanitization"] = {
        "source_graph": str(input_path),
        "policy": "allowlisted_sources_and_fully_labelled_edges_only",
        "dropped_node_ids": sorted(dropped_node_ids),
        "dropped_edge_indexes": dropped_edge_indexes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary_path.replace(output_path)
    audit = audit_graph(output_path, root)
    return {
        "input_graph": str(input_path),
        "output_graph": str(output_path),
        "original_nodes": len(original_nodes),
        "kept_nodes": len(kept_nodes),
        "dropped_nodes": len(dropped_node_ids),
        "original_edges": len(original_links),
        "kept_edges": len(kept_links),
        "dropped_edges": len(dropped_edge_indexes),
        "audit": audit,
        "passed": audit["passed"] and bool(kept_nodes) and bool(kept_links),
    }


def query_graph(
    graph_path: Path,
    root: Path,
    manifest_path: Path,
    question: str,
    token_budget: int = 1000,
) -> dict[str, Any]:
    """Run Graphify's in-process query path and return UTF-8-safe structured evidence."""
    manifest_audit = audit_manifest(manifest_path, root)
    if not manifest_audit["passed"]:
        raise ValueError("query refused because graph manifest is stale or out of scope")
    audit = audit_graph(graph_path, root)
    if not audit["passed"]:
        raise ValueError("query refused because graph audit failed")

    from graphify.serve import _query_graph_text
    from networkx.readwrite import json_graph

    raw = json.loads(graph_path.read_text(encoding="utf-8"))
    if "links" not in raw and "edges" in raw:
        raw = dict(raw, links=raw["edges"])
    try:
        graph = json_graph.node_link_graph(raw, edges="links")
    except TypeError:
        graph = json_graph.node_link_graph(raw)
    started = time.perf_counter()
    query_text = _query_graph_text(
        graph,
        question,
        mode="bfs",
        depth=2,
        token_budget=token_budget,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    selected_sources = sorted({
        normalized
        for value in QUERY_SOURCE.findall(query_text)
        if (normalized := _normalize_graph_path(value, root)) in ACTIVE_MARKDOWN_ALLOWLIST
    })
    unexpected_sources = sorted({
        value
        for value in QUERY_SOURCE.findall(query_text)
        if _normalize_graph_path(value, root) not in ACTIVE_MARKDOWN_ALLOWLIST
    })
    source_tokens = sum(
        _estimated_tokens((root / relative_path).read_text(encoding="utf-8"))
        for relative_path in selected_sources
    )
    return {
        "question": question,
        "elapsed_ms": round(elapsed_ms, 6),
        "query_output_estimated_tokens": _estimated_tokens(query_text),
        "selected_source_estimated_tokens": source_tokens,
        "selected_sources": selected_sources,
        "unexpected_sources": unexpected_sources,
        "query_text": query_text,
        "passed": bool(selected_sources) and not unexpected_sources,
    }


def compare_profile_queries(
    graph_path: Path,
    root: Path,
    manifest_path: Path,
    baseline_path: Path,
    output_path: Path,
    token_budget: int = 1000,
) -> dict[str, Any]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    profiles: dict[str, Any] = {}
    for profile, question in PROFILE_QUESTIONS.items():
        query = query_graph(graph_path, root, manifest_path, question, token_budget)
        expected = set(PROFILE_SOURCES[profile])
        graph_selected = set(query["selected_sources"])
        effective_sources = graph_selected | MANDATORY_STARTUP_SOURCES
        direct_tokens = baseline["profiles"][profile]["total_estimated_tokens"]
        effective_source_tokens = sum(
            _estimated_tokens((root / relative_path).read_text(encoding="utf-8"))
            for relative_path in effective_sources
        )
        fixed_task_tokens = sum(
            row["estimated_tokens"]
            for row in baseline["profiles"][profile]["selected_sources"]
            if row["path"] not in expected
        )
        graph_total = (
            query["query_output_estimated_tokens"]
            + effective_source_tokens
            + fixed_task_tokens
        )
        profiles[profile] = {
            **query,
            "query_execution_passed": query["passed"],
            "graph_selected_sources": sorted(graph_selected),
            "effective_sources_with_mandatory_startup": sorted(effective_sources),
            "effective_source_estimated_tokens": effective_source_tokens,
            "expected_sources": sorted(expected),
            "missing_expected_sources": sorted(expected - effective_sources),
            "wrong_authority_selections": sorted(effective_sources - expected),
            "fixed_task_estimated_tokens": fixed_task_tokens,
            "graph_total_estimated_tokens": graph_total,
            "direct_total_estimated_tokens": direct_tokens,
            "estimated_token_delta": graph_total - direct_tokens,
            "passed": (
                query["passed"]
                and effective_sources == expected
                and graph_total < direct_tokens
            ),
        }
    result = {
        "schema_version": 1,
        "measurement": "graphify_vs_direct_routing",
        "graph_path": str(graph_path.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "baseline_path": str(baseline_path.resolve()),
        "profiles": profiles,
        "passed": all(profile["passed"] for profile in profiles.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def detect_manifest(root: Path) -> dict[str, Any]:
    """Run Graphify's detector and require the exact approved Markdown set."""
    from graphify.detect import detect

    root = root.resolve()
    with TemporaryDirectory(prefix="graphify-detect-") as cache_directory:
        detection = detect(root, cache_root=Path(cache_directory))
    detected: set[str] = set()
    for values in detection["files"].values():
        for value in values:
            candidate = Path(value)
            if candidate.is_absolute():
                candidate = candidate.resolve().relative_to(root)
            detected.add(candidate.as_posix())

    expected = set(ACTIVE_MARKDOWN_ALLOWLIST)
    protected = sorted(
        path for path in detected if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    return {
        "detected_sources": sorted(detected),
        "expected_sources": sorted(expected),
        "missing_sources": sorted(expected - detected),
        "unexpected_sources": sorted(detected - expected),
        "protected_sources": protected,
        "walk_errors": detection["walk_errors"],
        "graphifyignore_patterns": detection["graphifyignore_patterns"],
        "passed": detected == expected and not protected and not detection["walk_errors"],
    }


def audit_manifest(manifest_path: Path, root: Path) -> dict[str, Any]:
    """Require Graphify's manifest to match the exact current allowlisted bytes."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = set(ACTIVE_MARKDOWN_ALLOWLIST)
    actual = set(manifest)
    stale_sources: list[str] = []
    invalid_entries: list[str] = []
    for relative_path in sorted(expected & actual):
        entry = manifest.get(relative_path)
        recorded_hash = entry.get("semantic_hash") if isinstance(entry, dict) else None
        if not isinstance(recorded_hash, str):
            invalid_entries.append(relative_path)
            continue
        current_hash = hashlib.md5((root / relative_path).read_bytes()).hexdigest()
        if current_hash != recorded_hash.lower():
            stale_sources.append(relative_path)
    return {
        "manifest_path": str(manifest_path.resolve()),
        "missing_sources": sorted(expected - actual),
        "unexpected_sources": sorted(actual - expected),
        "invalid_entries": invalid_entries,
        "stale_sources": stale_sources,
        "passed": not any((
            expected - actual,
            actual - expected,
            invalid_entries,
            stale_sources,
        )),
    }


def _markdown_table(text: str, heading: str) -> list[dict[str, str]]:
    """Return a simple pipe table immediately below an exact Markdown heading."""
    lines = text.splitlines()
    try:
        heading_index = lines.index(heading)
    except ValueError as error:
        raise ValueError(f"missing table heading: {heading}") from error

    table_lines: list[str] = []
    for line in lines[heading_index + 1:]:
        if not table_lines and not line.strip():
            continue
        if not line.startswith("|"):
            if table_lines:
                break
            continue
        table_lines.append(line)
    if len(table_lines) < 2:
        raise ValueError(f"missing table under heading: {heading}")

    def cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    headers = cells(table_lines[0])
    separator = cells(table_lines[1])
    if len(headers) != len(separator) or not all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in separator
    ):
        raise ValueError(f"invalid table header under heading: {heading}")
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        values = cells(line)
        if len(values) != len(headers):
            raise ValueError(f"invalid table row under heading {heading}: {line}")
        rows.append(dict(zip(headers, values)))
    return rows


def _strip_code(value: str) -> str:
    return value[1:-1] if len(value) >= 2 and value.startswith("`") and value.endswith("`") else value


def _fixed_document_paths(value: str) -> list[str]:
    paths: list[str] = []
    for code_value in INLINE_CODE.findall(value):
        path = code_value.split("#", 1)[0]
        if Path(path).suffix.lower() in {".md", ".json"}:
            paths.append(Path(path).as_posix())
    return paths


def _registry_records(root: Path) -> list[dict[str, str]]:
    registry_text = (root / "docs/agent/DOCUMENT_REGISTRY.md").read_text(encoding="utf-8")
    records: list[dict[str, str]] = []
    for row in _markdown_table(registry_text, "## Registered documents"):
        records.append({
            **row,
            "ID": _strip_code(row["ID"]),
            "Path": _strip_code(row["Path"]),
        })
    return records


def _authority_hashes(root: Path) -> dict[str, str]:
    return {
        relative_path: hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
        for relative_path in ROUTE_GRAPH_SOURCE_PATHS
    }


def build_typed_route_graph(root: Path, output_path: Path) -> dict[str, Any]:
    """Generate a Graphify-compatible one-hop graph from the two routing authorities."""
    root = root.resolve()
    output_path = output_path.resolve()
    try:
        output_path.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("typed route graph output must stay outside the repository")

    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    route_rows = _markdown_table(agents_text, "## Task routing")
    write_rows = _markdown_table(agents_text, "## Write-back routing")
    registry_records = _registry_records(root)

    document_nodes: list[dict[str, Any]] = []
    document_id_by_path: dict[str, str] = {}
    for record in registry_records:
        document_path = record["Path"]
        node_id = f"document:{record['ID']}"
        if document_path in document_id_by_path:
            raise ValueError(f"duplicate registered document path: {document_path}")
        document_id_by_path[document_path] = node_id
        document_nodes.append({
            "id": node_id,
            "kind": "document",
            "label": record["ID"],
            "document_id": record["ID"],
            "document_path": document_path,
            "document_kind": record["Kind"],
            "lifecycle": record["Lifecycle"],
            "authority": record["Authority"],
            "read_trigger": record["Read trigger"],
            "source_file": "docs/agent/DOCUMENT_REGISTRY.md",
            "source_location": "#registered-documents",
        })

    nodes: list[dict[str, Any]] = list(document_nodes)
    links: list[dict[str, Any]] = []

    def add_link(source: str, target_path: str, relation: str) -> None:
        target = document_id_by_path.get(target_path)
        if target is None:
            raise ValueError(f"routed path is not registered: {target_path}")
        link_key = (source, target, relation)
        if any((link["source"], link["target"], link["relation"]) == link_key for link in links):
            return
        links.append({
            "source": source,
            "target": target,
            "relation": relation,
            "confidence": "EXTRACTED",
            "source_file": "AGENTS.md",
        })

    route_ids: set[str] = set()
    for row in route_rows:
        route_id = _strip_code(row["Route ID"])
        if route_id in route_ids:
            raise ValueError(f"duplicate route ID: {route_id}")
        route_ids.add(route_id)
        selector = row["Selector before read"]
        node_id = f"route:{route_id}"
        nodes.append({
            "id": node_id,
            "kind": "route",
            "label": row["Task intent"],
            "route_id": route_id,
            "selector": selector,
            "selector_required": selector.lower() != "none",
            "default_exclusions": row["Do not read by default"],
            "source_file": "AGENTS.md",
            "source_location": "#task-routing",
        })
        add_link(node_id, "AGENTS.md", "always_read")
        add_link(node_id, "PROJECT_RULES.md", "always_read")
        handoff_relation = "requires" if route_id == "resume_current_work" else "read_when_current_work"
        add_link(node_id, "SESSION_HANDOFF.md", handoff_relation)
        for document_path in _fixed_document_paths(row["Required read delta"]):
            add_link(node_id, document_path, "requires")

    write_ids: set[str] = set()
    for row in write_rows:
        write_id = _strip_code(row["Write ID"])
        if write_id in write_ids:
            raise ValueError(f"duplicate write ID: {write_id}")
        write_ids.add(write_id)
        node_id = f"write:{write_id}"
        fixed_targets = _fixed_document_paths(row["Write to"])
        nodes.append({
            "id": node_id,
            "kind": "write_route",
            "label": row["Information changed"],
            "write_id": write_id,
            "selector_required": not fixed_targets,
            "write_instruction": row["Write to"],
            "source_file": "AGENTS.md",
            "source_location": "#write-back-routing",
        })
        for document_path in fixed_targets:
            add_link(node_id, document_path, "writes_to")

    graph = {
        "directed": True,
        "multigraph": False,
        "graph": {
            "navigation_contract": {
                "schema_version": ROUTE_GRAPH_SCHEMA_VERSION,
                "generated_from": list(ROUTE_GRAPH_SOURCE_PATHS),
                "source_sha256": _authority_hashes(root),
                "max_hops": 1,
                "read_relations": sorted(ROUTE_READ_RELATIONS),
                "fallback": "AGENTS.md#task-routing",
            }
        },
        "nodes": nodes,
        "links": links,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary_path.replace(output_path)
    audit = audit_typed_route_graph(output_path, root)
    return {
        "output_graph": str(output_path),
        "routes": len(route_ids),
        "write_routes": len(write_ids),
        "documents": len(document_nodes),
        "edges": len(links),
        "audit": audit,
        "passed": audit["passed"],
    }


def audit_typed_route_graph(graph_path: Path, root: Path) -> dict[str, Any]:
    """Validate provenance, staleness, one-hop shape, and exact authority coverage."""
    root = root.resolve()
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    node_ids = [str(node.get("id")) for node in nodes]
    node_by_id = {str(node.get("id")): node for node in nodes}
    duplicate_node_ids = sorted({node_id for node_id in node_ids if node_ids.count(node_id) > 1})
    orphan_edges: list[int] = []
    invalid_edges: list[int] = []
    for index, link in enumerate(links):
        source = node_by_id.get(str(link.get("source")))
        target = node_by_id.get(str(link.get("target")))
        if source is None or target is None:
            orphan_edges.append(index)
            continue
        relation = str(link.get("relation", ""))
        source_kind = source.get("kind")
        valid_shape = (
            target.get("kind") == "document"
            and (
                (source_kind == "route" and relation in ROUTE_READ_RELATIONS)
                or (source_kind == "write_route" and relation == "writes_to")
            )
        )
        if (
            relation not in ROUTE_EDGE_RELATIONS
            or not valid_shape
            or link.get("confidence") != "EXTRACTED"
            or link.get("source_file") != "AGENTS.md"
        ):
            invalid_edges.append(index)

    registry_records = _registry_records(root)
    registered_paths = {record["Path"] for record in registry_records}
    document_paths = {
        str(node.get("document_path"))
        for node in nodes
        if node.get("kind") == "document"
    }
    protected_document_paths = sorted(
        path for path in document_paths
        if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    missing_document_paths = sorted(registered_paths - document_paths)
    unexpected_document_paths = sorted(document_paths - registered_paths)

    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    expected_routes = {
        _strip_code(row["Route ID"])
        for row in _markdown_table(agents_text, "## Task routing")
    }
    expected_writes = {
        _strip_code(row["Write ID"])
        for row in _markdown_table(agents_text, "## Write-back routing")
    }
    graph_routes = {
        str(node.get("route_id")) for node in nodes if node.get("kind") == "route"
    }
    graph_writes = {
        str(node.get("write_id")) for node in nodes if node.get("kind") == "write_route"
    }
    missing_startup_edges: list[str] = []
    for route_id in sorted(graph_routes):
        source_id = f"route:{route_id}"
        targets = {
            node_by_id[str(link["target"])].get("document_path")
            for link in links
            if str(link.get("source")) == source_id
            and str(link.get("target")) in node_by_id
        }
        if not {"AGENTS.md", "PROJECT_RULES.md"}.issubset(targets):
            missing_startup_edges.append(route_id)

    contract = graph.get("graph", {}).get("navigation_contract", {})
    recorded_hashes = contract.get("source_sha256", {})
    current_hashes = _authority_hashes(root)
    stale_sources = sorted(
        path for path in ROUTE_GRAPH_SOURCE_PATHS
        if recorded_hashes.get(path) != current_hashes[path]
    )
    invalid_contract = not (
        contract.get("schema_version") == ROUTE_GRAPH_SCHEMA_VERSION
        and contract.get("max_hops") == 1
        and set(contract.get("read_relations", [])) == ROUTE_READ_RELATIONS
        and contract.get("fallback") == "AGENTS.md#task-routing"
    )
    base_audit = audit_graph(graph_path, root)
    result = {
        "graph_path": str(graph_path.resolve()),
        "routes": len(graph_routes),
        "write_routes": len(graph_writes),
        "documents": len(document_paths),
        "edges": len(links),
        "duplicate_node_ids": duplicate_node_ids,
        "missing_routes": sorted(expected_routes - graph_routes),
        "unexpected_routes": sorted(graph_routes - expected_routes),
        "missing_write_routes": sorted(expected_writes - graph_writes),
        "unexpected_write_routes": sorted(graph_writes - expected_writes),
        "missing_document_paths": missing_document_paths,
        "unexpected_document_paths": unexpected_document_paths,
        "protected_document_paths": protected_document_paths,
        "missing_startup_edges": missing_startup_edges,
        "invalid_edges": invalid_edges,
        "orphan_edges": orphan_edges,
        "stale_sources": stale_sources,
        "invalid_contract": invalid_contract,
        "base_graph_audit": base_audit,
    }
    result["passed"] = not any((
        duplicate_node_ids,
        result["missing_routes"],
        result["unexpected_routes"],
        result["missing_write_routes"],
        result["unexpected_write_routes"],
        missing_document_paths,
        unexpected_document_paths,
        protected_document_paths,
        missing_startup_edges,
        invalid_edges,
        orphan_edges,
        stale_sources,
        invalid_contract,
        not base_audit["passed"],
    ))
    return result


def _normalized_selected_path(value: str, root: Path) -> str:
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"selected path is outside the workspace: {value}") from error
    return relative.as_posix()


def query_typed_route(
    graph_path: Path,
    root: Path,
    route_id: str,
    *,
    include_handoff: bool = True,
    selector_value: str | None = None,
    selected_paths: Sequence[str] = (),
) -> dict[str, Any]:
    """Select exact documents from one route without semantic or document-node traversal."""
    root = root.resolve()
    audit = audit_typed_route_graph(graph_path, root)
    if not audit["passed"]:
        raise ValueError("typed route query refused because graph is stale or invalid")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    node_by_id = {str(node["id"]): node for node in graph["nodes"]}
    route_node = node_by_id.get(f"route:{route_id}")
    if route_node is None or route_node.get("kind") != "route":
        raise ValueError(f"unknown route ID: {route_id}")

    selected_documents: list[str] = []
    traversed_edges = 0
    for link in graph["links"]:
        if str(link.get("source")) != route_node["id"]:
            continue
        relation = str(link.get("relation"))
        if relation == "read_when_current_work" and not include_handoff:
            continue
        if relation not in ROUTE_READ_RELATIONS:
            continue
        target = node_by_id[str(link["target"])]
        selected_documents.append(str(target["document_path"]))
        traversed_edges += 1

    exact_selected_items: list[str] = []
    registered_paths = {
        str(node["document_path"])
        for node in graph["nodes"]
        if node.get("kind") == "document"
    }
    if selected_paths and not route_node.get("selector_required"):
        raise ValueError(f"route {route_id} does not accept additional selected paths")
    for raw_path in selected_paths:
        relative_path = _normalized_selected_path(raw_path, root)
        protected_prefix = next(
            (prefix for prefix in PROTECTED_PREFIXES if relative_path.startswith(prefix)),
            None,
        )
        if protected_prefix:
            if route_id not in {"handle_video_task_state", "work_on_user_data"} or protected_prefix not in {"inputs/", "outputs/"}:
                raise ValueError(f"route {route_id} cannot select protected path: {relative_path}")
            exact_selected_items.append(relative_path)
            continue
        if relative_path not in registered_paths:
            raise ValueError(f"selected document is not registered: {relative_path}")
        selected_documents.append(relative_path)

    selected_documents = list(dict.fromkeys(selected_documents))
    selector_required = bool(route_node.get("selector_required"))
    selector_satisfied = not selector_required or bool(selector_value and selector_value.strip())
    return {
        "route_id": route_id,
        "route_source": "AGENTS.md#task-routing",
        "selected_documents": selected_documents,
        "exact_selected_items_not_indexed": exact_selected_items,
        "selector": route_node.get("selector"),
        "selector_value": selector_value,
        "selector_satisfied": selector_satisfied,
        "default_exclusions": route_node.get("default_exclusions"),
        "traversal_hops": 1,
        "traversed_edges": traversed_edges,
        "document_node_expansion": 0,
        "graph_document_contents_loaded": 0,
        "direct_fallback": "AGENTS.md#task-routing",
        "passed": selector_satisfied,
    }


def compact_typed_route_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return the minimum successful payload consumed after mandatory startup reads."""
    if not result.get("passed"):
        raise ValueError("cannot compact an incomplete typed route result")
    return {
        "route_id": result["route_id"],
        "read_delta": [
            path for path in result["selected_documents"]
            if path not in MANDATORY_STARTUP_SOURCES
        ],
    }


def compare_typed_routes(
    graph_path: Path,
    root: Path,
    current_baseline_path: Path,
    historical_baseline_path: Path,
    historical_semantic_comparison_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Compare typed routing with both the current and original three-profile token baselines."""
    root = root.resolve()
    current_baseline = json.loads(current_baseline_path.read_text(encoding="utf-8"))
    historical_baseline = json.loads(historical_baseline_path.read_text(encoding="utf-8"))
    historical_semantic = json.loads(
        historical_semantic_comparison_path.read_text(encoding="utf-8")
    )
    profiles: dict[str, Any] = {}
    for profile, query_args in TYPED_PROFILE_QUERIES.items():
        started = time.perf_counter()
        route = query_typed_route(
            graph_path,
            root,
            query_args["route_id"],
            selector_value=query_args["selector_value"],
            selected_paths=query_args["selected_paths"],
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        payload = compact_typed_route_result(route)
        payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        query_tokens = _estimated_tokens(payload_text)

        expected = set(PROFILE_SOURCES[profile])
        selected = set(route["selected_documents"])
        selected_source_tokens = sum(
            _estimated_tokens((root / path).read_text(encoding="utf-8"))
            for path in selected
        )
        fixed_task_tokens = sum(
            row["estimated_tokens"]
            for row in current_baseline["profiles"][profile]["selected_sources"]
            if row["path"] not in expected
        )
        current_direct_tokens = current_baseline["profiles"][profile]["total_estimated_tokens"]
        current_typed_tokens = selected_source_tokens + fixed_task_tokens + query_tokens
        historical_direct_tokens = historical_baseline["profiles"][profile]["total_estimated_tokens"]
        historical_semantic_tokens = historical_semantic["profiles"][profile]["graph_total_estimated_tokens"]
        historical_typed_tokens = historical_direct_tokens + query_tokens
        wrong_authorities = sorted(selected - expected)
        missing_authorities = sorted(expected - selected)
        profiles[profile] = {
            "route_id": query_args["route_id"],
            "compact_query_payload": payload,
            "compact_query_estimated_tokens": query_tokens,
            "query_elapsed_ms": round(elapsed_ms, 6),
            "selected_documents": sorted(selected),
            "selected_source_estimated_tokens": selected_source_tokens,
            "fixed_task_estimated_tokens": fixed_task_tokens,
            "wrong_authority_selections": wrong_authorities,
            "missing_expected_sources": missing_authorities,
            "historical_direct_estimated_tokens": historical_direct_tokens,
            "historical_semantic_graph_estimated_tokens": historical_semantic_tokens,
            "historical_corpus_typed_estimated_tokens": historical_typed_tokens,
            "historical_typed_delta_vs_direct": historical_typed_tokens - historical_direct_tokens,
            "historical_typed_reduction_vs_semantic": historical_semantic_tokens - historical_typed_tokens,
            "current_direct_estimated_tokens": current_direct_tokens,
            "current_typed_estimated_tokens": current_typed_tokens,
            "current_typed_delta_vs_direct": current_typed_tokens - current_direct_tokens,
            "exact_selection_passed": not wrong_authorities and not missing_authorities,
            "token_benefit_vs_direct_passed": current_typed_tokens < current_direct_tokens,
        }

    exact_selection_passed = all(row["exact_selection_passed"] for row in profiles.values())
    token_benefit_passed = all(
        row["token_benefit_vs_direct_passed"] for row in profiles.values()
    )
    result = {
        "schema_version": 1,
        "measurement": "typed_route_vs_direct_and_semantic_graphify",
        "token_estimator": "ceil(characters / 4)",
        "graph_path": str(graph_path.resolve()),
        "current_baseline_path": str(current_baseline_path.resolve()),
        "historical_baseline_path": str(historical_baseline_path.resolve()),
        "historical_semantic_comparison_path": str(
            historical_semantic_comparison_path.resolve()
        ),
        "profiles": profiles,
        "exact_selection_passed": exact_selection_passed,
        "token_benefit_vs_direct_passed": token_benefit_passed,
        "default_route_decision": (
            "typed_graphify_default" if exact_selection_passed and token_benefit_passed
            else "direct_default_typed_graph_optional"
        ),
        "passed": exact_selection_passed and token_benefit_passed,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def query_typed_write(graph_path: Path, root: Path, write_id: str) -> dict[str, Any]:
    """Resolve one write-back authority without reading its document body."""
    audit = audit_typed_route_graph(graph_path, root)
    if not audit["passed"]:
        raise ValueError("typed write query refused because graph is stale or invalid")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    node_by_id = {str(node["id"]): node for node in graph["nodes"]}
    write_node = node_by_id.get(f"write:{write_id}")
    if write_node is None or write_node.get("kind") != "write_route":
        raise ValueError(f"unknown write ID: {write_id}")
    targets = [
        str(node_by_id[str(link["target"])]["document_path"])
        for link in graph["links"]
        if str(link.get("source")) == write_node["id"]
        and link.get("relation") == "writes_to"
    ]
    return {
        "write_id": write_id,
        "write_source": "AGENTS.md#write-back-routing",
        "write_targets": targets,
        "write_instruction": write_node.get("write_instruction"),
        "selector_required": bool(write_node.get("selector_required")),
        "traversal_hops": 1,
        "passed": bool(targets) or bool(write_node.get("selector_required")),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser("baseline")
    baseline.add_argument("--root", type=Path, default=Path.cwd())
    baseline.add_argument("--output", type=Path, required=True)
    baseline.add_argument("--iterations", type=int, default=100)

    audit = subparsers.add_parser("audit-graph")
    audit.add_argument("--root", type=Path, default=Path.cwd())
    audit.add_argument("--graph", type=Path, required=True)

    sanitize = subparsers.add_parser("sanitize-graph")
    sanitize.add_argument("--root", type=Path, default=Path.cwd())
    sanitize.add_argument("--input", type=Path, required=True)
    sanitize.add_argument("--output", type=Path, required=True)

    query_profiles = subparsers.add_parser("query-profiles")
    query_profiles.add_argument("--root", type=Path, default=Path.cwd())
    query_profiles.add_argument("--graph", type=Path, required=True)
    query_profiles.add_argument("--manifest", type=Path, required=True)
    query_profiles.add_argument("--baseline", type=Path, required=True)
    query_profiles.add_argument("--output", type=Path, required=True)
    query_profiles.add_argument("--budget", type=int, default=1000)

    manifest_audit = subparsers.add_parser("audit-manifest")
    manifest_audit.add_argument("--root", type=Path, default=Path.cwd())
    manifest_audit.add_argument("--manifest", type=Path, required=True)

    detect_parser = subparsers.add_parser("detect-manifest")
    detect_parser.add_argument("--root", type=Path, default=Path.cwd())

    route_build = subparsers.add_parser("build-route-graph")
    route_build.add_argument("--root", type=Path, default=Path.cwd())
    route_build.add_argument("--output", type=Path, required=True)

    route_audit = subparsers.add_parser("audit-route-graph")
    route_audit.add_argument("--root", type=Path, default=Path.cwd())
    route_audit.add_argument("--graph", type=Path, required=True)

    route_query = subparsers.add_parser("route-task")
    route_query.add_argument("--root", type=Path, default=Path.cwd())
    route_query.add_argument("--graph", type=Path, required=True)
    route_query.add_argument("--route-id", required=True)
    route_query.add_argument("--selector")
    route_query.add_argument("--include", action="append", default=[])
    route_query.add_argument("--no-handoff", action="store_true")
    route_query.add_argument("--verbose", action="store_true")

    write_query = subparsers.add_parser("route-write")
    write_query.add_argument("--root", type=Path, default=Path.cwd())
    write_query.add_argument("--graph", type=Path, required=True)
    write_query.add_argument("--write-id", required=True)

    typed_compare = subparsers.add_parser("compare-typed-routes")
    typed_compare.add_argument("--root", type=Path, default=Path.cwd())
    typed_compare.add_argument("--graph", type=Path, required=True)
    typed_compare.add_argument("--current-baseline", type=Path, required=True)
    typed_compare.add_argument("--historical-baseline", type=Path, required=True)
    typed_compare.add_argument("--historical-semantic-comparison", type=Path, required=True)
    typed_compare.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "baseline":
        result = build_direct_baseline(args.root, args.output, args.iterations)
    elif args.command == "audit-graph":
        result = audit_graph(args.graph, args.root)
    elif args.command == "sanitize-graph":
        result = sanitize_graph(args.input, args.output, args.root)
    elif args.command == "query-profiles":
        try:
            result = compare_profile_queries(
                args.graph,
                args.root,
                args.manifest,
                args.baseline,
                args.output,
                args.budget,
            )
        except ValueError as error:
            result = {
                "measurement": "graphify_vs_direct_routing",
                "error": str(error),
                "direct_fallback_required": True,
                "passed": False,
            }
    elif args.command == "audit-manifest":
        result = audit_manifest(args.manifest, args.root)
    elif args.command == "detect-manifest":
        result = detect_manifest(args.root)
    elif args.command == "build-route-graph":
        result = build_typed_route_graph(args.root, args.output)
    elif args.command == "audit-route-graph":
        result = audit_typed_route_graph(args.graph, args.root)
    elif args.command == "route-task":
        try:
            full_result = query_typed_route(
                args.graph,
                args.root,
                args.route_id,
                include_handoff=not args.no_handoff,
                selector_value=args.selector,
                selected_paths=args.include,
            )
            result = full_result if args.verbose else compact_typed_route_result(full_result)
        except ValueError as error:
            result = {
                "route_id": args.route_id,
                "error": str(error),
                "direct_fallback_required": True,
                "passed": False,
            }
    elif args.command == "route-write":
        try:
            result = query_typed_write(args.graph, args.root, args.write_id)
        except ValueError as error:
            result = {
                "write_id": args.write_id,
                "error": str(error),
                "direct_fallback_required": True,
                "passed": False,
            }
    else:
        result = compare_typed_routes(
            args.graph,
            args.root,
            args.current_baseline,
            args.historical_baseline,
            args.historical_semantic_comparison,
            args.output,
        )
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
