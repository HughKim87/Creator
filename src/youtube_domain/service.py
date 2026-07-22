from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from file_data import ContextService


PACK_VERSION = 1
TASK_NAME = "preproduction_evidence_pack"
MAX_CHAR_LIMIT = 12_000
REQUEST_FIELDS = frozenset(
    {"video", "documents", "records", "search", "char_limit", "baseline_characters"}
)
VIDEO_FIELDS = frozenset({"id", "working_title", "audience", "goal"})
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class YouTubeDomainError(ValueError):
    pass


class YouTubeEvidenceError(YouTubeDomainError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _text(value: Any, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise YouTubeDomainError(f"{field} must be a non-empty string")
    rendered = value.strip()
    if len(rendered) > maximum:
        raise YouTubeDomainError(f"{field} must be at most {maximum} characters")
    return rendered


def _video(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != VIDEO_FIELDS:
        raise YouTubeDomainError(f"video must contain exactly: {sorted(VIDEO_FIELDS)}")
    video_id = _text(value["id"], "video.id", maximum=80)
    if not SLUG_PATTERN.fullmatch(video_id):
        raise YouTubeDomainError("video.id must be a lowercase ASCII slug")
    return {
        "id": video_id,
        "working_title": _text(value["working_title"], "video.working_title", maximum=200),
        "audience": _text(value["audience"], "video.audience", maximum=500),
        "goal": _text(value["goal"], "video.goal", maximum=1000),
    }


def _selections(value: Any, field: str, identity: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise YouTubeDomainError(f"{field} must be a list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != {identity, "reason"}:
            raise YouTubeDomainError(f"each {field} item must contain {identity} and reason")
        identifier = _text(item[identity], f"{field}.{identity}", maximum=200)
        if identifier in seen:
            raise YouTubeDomainError(f"duplicate {field} selection: {identifier}")
        seen.add(identifier)
        normalized.append(
            {identity: identifier, "reason": _text(item["reason"], f"{field}.reason", maximum=500)}
        )
    return sorted(normalized, key=lambda item: (item[identity], item["reason"]))


def validate_request(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != REQUEST_FIELDS:
        raise YouTubeDomainError(f"request must contain exactly: {sorted(REQUEST_FIELDS)}")
    video = _video(value["video"])
    documents = _selections(value["documents"], "documents", "ref")
    records = _selections(value["records"], "records", "id")
    search = value["search"]
    if search is not None:
        search = _text(search, "search", maximum=500)
    if not documents and not records and search is None:
        raise YouTubeDomainError("at least one direct evidence selection or search is required")
    char_limit = value["char_limit"]
    if (
        not isinstance(char_limit, int)
        or isinstance(char_limit, bool)
        or not 1 <= char_limit <= MAX_CHAR_LIMIT
    ):
        raise YouTubeDomainError(f"char_limit must be between 1 and {MAX_CHAR_LIMIT}")
    baseline = value["baseline_characters"]
    if not isinstance(baseline, int) or isinstance(baseline, bool) or baseline < 1:
        raise YouTubeDomainError("baseline_characters must be a positive integer")
    return {
        "video": video,
        "documents": documents,
        "records": records,
        "search": search,
        "char_limit": char_limit,
        "baseline_characters": baseline,
    }


class YouTubeEvidenceService:
    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root).resolve()
        self.context = ContextService(self.root)

    def build_pack(self, request: Mapping[str, Any]) -> dict[str, Any]:
        normalized = validate_request(request)
        video = normalized["video"]
        context_request: dict[str, Any] = {
            "purpose": f"YouTube pre-production evidence for {video['id']}: {video['goal']}",
            "documents": normalized["documents"],
            "records": normalized["records"],
            "char_limit": normalized["char_limit"],
            "baseline_characters": normalized["baseline_characters"],
        }
        if normalized["search"] is not None:
            context_request["search"] = normalized["search"]
        context_package = self.context.build_package(context_request)
        selected_ids = {
            item["id"]
            for item in context_package["selected"]
            if item["kind"] == "record"
        }
        requested_ids = {item["id"] for item in normalized["records"]}
        missing = sorted(requested_ids - selected_ids)
        if missing:
            raise YouTubeEvidenceError(
                "requested evidence records are not current selections: " + ", ".join(missing)
            )
        if not context_package["selected"]:
            raise YouTubeEvidenceError("evidence pack cannot be empty")
        pack: dict[str, Any] = {
            "pack_version": PACK_VERSION,
            "domain": "youtube",
            "task": TASK_NAME,
            "video": video,
            "approval_gate": {
                "status": "review_required",
                "owner": "user",
                "decision": "working_title_and_creative_direction",
                "reason": "evidence selection does not approve a creative direction",
            },
            "context_package": context_package,
        }
        pack["fingerprint"] = "sha256:" + hashlib.sha256(
            _canonical(pack).encode("utf-8")
        ).hexdigest()
        return pack
