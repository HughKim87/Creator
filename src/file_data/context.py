from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import UUID

from .lifecycle import LIFECYCLE_STATES, TARGET_TYPES, LifecycleError, LifecycleService
from .record import UnsafePathError, resolve_project_path
from .store import InputContractError


DEFAULT_CHAR_LIMIT = 12_000
EXCLUSION_DETAIL_LIMIT = 20
FILTER_FIELDS = frozenset({"record_type", "state", "scope", "evidence_role"})


class ContextError(InputContractError):
    pass


class ContextLimitError(ContextError):
    pass


def _non_empty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextError(f"{field} must be a non-empty string")
    return value.strip()


def _uuid(value: Any, field: str) -> str:
    rendered = _non_empty(value, field)
    try:
        parsed = UUID(rendered)
    except (ValueError, AttributeError) as exc:
        raise ContextError(f"{field} must be a UUID") from exc
    if parsed.version != 4 or str(parsed) != rendered:
        raise ContextError(f"{field} must be a lowercase UUIDv4")
    return rendered


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _content_size(item: Mapping[str, Any]) -> tuple[int, int]:
    if item["kind"] == "document":
        rendered = item["content"]
    else:
        rendered = _canonical(item["payload"])
    return len(rendered), len(rendered.encode("utf-8"))


class ContextService:
    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root).resolve()
        self.lifecycle = LifecycleService(self.root)

    def _record_sources(self, record: Mapping[str, Any]) -> list[dict[str, str]]:
        payload = record["payload"]
        if record["record_type"] == "source":
            source_ids = [record["id"]]
        elif record["record_type"] in {"knowledge", "decision"}:
            source_ids = list(payload["source_ids"])
        else:
            source_ids = [payload["source_id"]]
        sources: list[dict[str, str]] = []
        for source_id in source_ids:
            source = self.lifecycle.store.get_record(source_id)
            if source["record_type"] != "source":
                raise ContextError(f"record source reference is not a source: {source_id}")
            try:
                source_state = self.lifecycle.get_state(source_id)["payload"]["state"]
            except LifecycleError:
                source_state = "unregistered"
            sources.append(
                {
                    "id": source_id,
                    "evidence_role": source["payload"]["evidence_role"],
                    "lifecycle_state": source_state,
                }
            )
        return sources

    def _record_item(self, target_id: str, reason: str) -> dict[str, Any]:
        bundle = self.lifecycle.get_record(_uuid(target_id, "record_id"))
        record = bundle["record"]
        state = bundle["lifecycle"]["payload"]["state"]
        return {
            "kind": "record",
            "id": record["id"],
            "record_type": record["record_type"],
            "lifecycle_state": state,
            "reason": _non_empty(reason, "reason"),
            "sources": self._record_sources(record),
            "payload": record["payload"],
        }

    def _document_item(self, document_ref: str, reason: str) -> dict[str, Any]:
        ref = _non_empty(document_ref, "document_ref").replace("\\", "/")
        try:
            target = resolve_project_path(self.root, ref)
        except UnsafePathError as exc:
            raise ContextError(str(exc)) from exc
        if not target.is_file():
            raise ContextError(f"document does not exist: {ref}")
        raw = target.read_bytes()
        try:
            content = raw.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise ContextError(f"document is not strict UTF-8: {ref}") from exc
        if "\x00" in content:
            raise ContextError(f"document contains NUL: {ref}")
        return {
            "kind": "document",
            "ref": target.relative_to(self.root).as_posix(),
            "status": "active",
            "reason": _non_empty(reason, "reason"),
            "sources": [{"ref": target.relative_to(self.root).as_posix()}],
            "content": content,
        }

    def measure_documents(self, document_refs: Sequence[str]) -> dict[str, int]:
        refs = sorted({_non_empty(ref, "document_ref").replace("\\", "/") for ref in document_refs})
        characters = 0
        utf8_bytes = 0
        for ref in refs:
            item = self._document_item(ref, "baseline measurement")
            item_characters, item_bytes = _content_size(item)
            characters += item_characters
            utf8_bytes += item_bytes
        return {"documents": len(refs), "characters": characters, "utf8_bytes": utf8_bytes}

    def _normalized_filters(self, filters: Mapping[str, Any] | None) -> dict[str, str]:
        if filters is None:
            return {}
        if not isinstance(filters, Mapping) or not set(filters) <= FILTER_FIELDS:
            raise ContextError(f"filters only allow: {sorted(FILTER_FIELDS)}")
        normalized: dict[str, str] = {}
        for key, value in filters.items():
            rendered = _non_empty(value, key)
            if key == "record_type" and rendered not in TARGET_TYPES:
                raise ContextError(f"record_type must be one of: {sorted(TARGET_TYPES)}")
            if key == "state" and rendered not in LIFECYCLE_STATES:
                raise ContextError(f"state must be one of: {sorted(LIFECYCLE_STATES)}")
            if key == "evidence_role" and rendered not in {"primary", "supporting", "contextual"}:
                raise ContextError("evidence_role is invalid")
            normalized[key] = rendered
        return normalized

    def filter_records(self, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        normalized = self._normalized_filters(filters)
        state_filter = normalized.get("state", "current")
        records: list[dict[str, Any]] = []
        for lifecycle_state in self.lifecycle.list_states(state=state_filter):
            record = self.lifecycle.store.get_record(lifecycle_state["payload"]["target_id"])
            if normalized.get("record_type") not in {None, record["record_type"]}:
                continue
            if "scope" in normalized:
                if record["record_type"] != "knowledge" or record["payload"]["scope"] != normalized["scope"]:
                    continue
            sources = self._record_sources(record)
            if "evidence_role" in normalized and normalized["evidence_role"] not in {
                source["evidence_role"] for source in sources
            }:
                continue
            records.append(
                {
                    "id": record["id"],
                    "record_type": record["record_type"],
                    "lifecycle_state": lifecycle_state["payload"]["state"],
                    "sources": sources,
                }
            )
        return sorted(records, key=lambda item: item["id"])

    def _search_fields(self, record: Mapping[str, Any]) -> dict[str, str]:
        payload = record["payload"]
        if record["record_type"] == "source":
            return {"locator": payload["locator"]}
        if record["record_type"] == "knowledge":
            return {
                "statement": payload["statement"],
                "scope": payload["scope"],
                "classification": payload["classification"],
            }
        if record["record_type"] == "decision":
            return {
                "problem": payload["problem"],
                "rationale": payload["rationale"],
                "selected_option": payload["selected_option"],
            }
        return {
            "title": payload["title"],
            "symptom": payload["symptom"],
            "confirmed_cause": payload["confirmed_cause"],
            "prevention": "\n".join(payload["prevention"]),
        }

    def search(self, text: str, filters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        needle = _non_empty(text, "text").casefold()
        candidates = self.filter_records({**self._normalized_filters(filters), "state": "current"})
        matches: list[dict[str, Any]] = []
        for candidate in candidates:
            record = self.lifecycle.store.get_record(candidate["id"])
            matched_fields = sorted(
                field for field, value in self._search_fields(record).items() if needle in value.casefold()
            )
            if matched_fields:
                matches.append({**candidate, "matched_fields": matched_fields})
        return matches

    def build_package(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(request, Mapping):
            raise ContextError("context request must be an object")
        allowed = {
            "purpose", "documents", "records", "search", "filters", "char_limit",
            "baseline_characters", "exclusion_detail_limit",
        }
        if not set(request) <= allowed:
            raise ContextError(f"context request only allows: {sorted(allowed)}")
        purpose = _non_empty(request.get("purpose"), "purpose")
        char_limit = request.get("char_limit", DEFAULT_CHAR_LIMIT)
        if not isinstance(char_limit, int) or isinstance(char_limit, bool) or char_limit < 1:
            raise ContextError("char_limit must be a positive integer")
        detail_limit = request.get("exclusion_detail_limit", EXCLUSION_DETAIL_LIMIT)
        if not isinstance(detail_limit, int) or isinstance(detail_limit, bool) or not 0 <= detail_limit <= 20:
            raise ContextError("exclusion_detail_limit must be between 0 and 20")
        baseline = request.get("baseline_characters")
        if baseline is not None and (
            not isinstance(baseline, int) or isinstance(baseline, bool) or baseline < 1
        ):
            raise ContextError("baseline_characters must be a positive integer")
        documents = request.get("documents", [])
        records = request.get("records", [])
        if not isinstance(documents, list) or not isinstance(records, list):
            raise ContextError("documents and records must be lists")
        selected: list[dict[str, Any]] = []
        direct_keys: set[tuple[str, str]] = set()
        excluded_details: list[dict[str, str]] = []
        excluded_counts: dict[str, int] = {}

        def exclude(ref: str, reason: str) -> None:
            excluded_counts[reason] = excluded_counts.get(reason, 0) + 1
            if len(excluded_details) < detail_limit:
                excluded_details.append({"ref": ref, "reason": reason})

        for item in sorted(
            documents,
            key=lambda value: (value.get("ref", ""), value.get("reason", ""))
            if isinstance(value, Mapping) else ("", ""),
        ):
            if not isinstance(item, Mapping) or set(item) != {"ref", "reason"}:
                raise ContextError("each document selection must contain ref and reason")
            document_item = self._document_item(item["ref"], item["reason"])
            key = ("document", document_item["ref"])
            if key not in direct_keys:
                selected.append(document_item)
                direct_keys.add(key)
        for item in sorted(
            records,
            key=lambda value: (value.get("id", ""), value.get("reason", ""))
            if isinstance(value, Mapping) else ("", ""),
        ):
            if not isinstance(item, Mapping) or set(item) != {"id", "reason"}:
                raise ContextError("each record selection must contain id and reason")
            record_item = self._record_item(item["id"], item["reason"])
            key = ("record", record_item["id"])
            if key in direct_keys:
                continue
            if record_item["lifecycle_state"] != "current":
                exclude(record_item["id"], f"noncurrent:{record_item['lifecycle_state']}")
            else:
                selected.append(record_item)
                direct_keys.add(key)
        direct_characters = sum(_content_size(item)[0] for item in selected)
        if direct_characters > char_limit:
            raise ContextLimitError(
                f"required direct context exceeds char_limit: {direct_characters} > {char_limit}"
            )
        search_text = request.get("search")
        filters = self._normalized_filters(request.get("filters"))
        if filters.get("state") not in {None, "current"}:
            raise ContextError("context package filters only allow current state")
        if search_text is not None:
            candidates = self.search(search_text, filters)
        elif filters:
            candidates = self.filter_records({**filters, "state": "current"})
        else:
            candidates = []
        for candidate in candidates:
                key = ("record", candidate["id"])
                if key in direct_keys:
                    continue
                reason = (
                    "string_match:" + ",".join(candidate["matched_fields"])
                    if "matched_fields" in candidate
                    else "structured_filter"
                )
                item = self._record_item(candidate["id"], reason)
                projected = direct_characters + _content_size(item)[0]
                if projected > char_limit:
                    exclude(candidate["id"], "size_limit")
                    continue
                selected.append(item)
                direct_keys.add(key)
                direct_characters = projected
        selected = sorted(selected, key=lambda item: (item["kind"], item.get("id", item.get("ref"))))
        content_characters = sum(_content_size(item)[0] for item in selected)
        content_bytes = sum(_content_size(item)[1] for item in selected)
        reduction = None if baseline is None else round((1 - content_characters / baseline) * 100, 2)
        package: dict[str, Any] = {
            "package_version": 1,
            "purpose": purpose,
            "settings": {
                "char_limit": char_limit,
                "search": search_text,
                "filters": filters,
                "exclusion_detail_limit": detail_limit,
            },
            "selected": selected,
            "excluded": {
                "details": sorted(excluded_details, key=lambda item: (item["reason"], item["ref"])),
                "counts_by_reason": dict(sorted(excluded_counts.items())),
            },
            "metrics": {
                "selected_items": len(selected),
                "content_characters": content_characters,
                "content_utf8_bytes": content_bytes,
                "baseline_characters": baseline,
                "reduction_percent": reduction,
            },
        }
        package["fingerprint"] = "sha256:" + hashlib.sha256(
            _canonical(package).encode("utf-8")
        ).hexdigest()
        return package
