"""Generated read-only state views (stage 03 task 03-4).

``export`` renders ``generated/status.json`` and
``generated/SESSION_HANDOFF.md`` from the database. The views are never an
input: no command reads them to decide state, and manual edits are simply
overwritten by the next export. Files are written to a temporary path and
atomically replaced so a failed write never leaves half a file.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from video_workflow.storage.port import StoredState
from video_workflow.storage.sqlite_store import APPLICATION_VERSION, SqliteStateStore

DO_NOT_EDIT = "DO NOT EDIT — generated from workflow.sqlite"
VIEW_SCHEMA_VERSION = 1


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _status_payload(stored: StoredState, generated_at: str) -> dict[str, object]:
    state = stored.state
    return {
        "do_not_edit": DO_NOT_EDIT,
        "schema_version": VIEW_SCHEMA_VERSION,
        "application_version": APPLICATION_VERSION,
        "generated_at": generated_at,
        "project_id": state.project_id.value,
        "state_version": stored.state_version,
        "last_event_id": stored.last_event_id,
        "phase": state.phase.value,
        "lifecycle": state.lifecycle.value,
        "source_registered": state.source_id is not None,
        "generation_count": len(state.generations),
        "open_generation": next(
            (
                generation.generation_id.value
                for generation in state.generations
                if generation.status.value == "open"
            ),
            None,
        ),
        "artifact_count": len(state.artifacts),
        "approval_count": len(state.approvals),
        "failure_count": len(state.failures),
    }


def _handoff_markdown(payload: dict[str, object]) -> str:
    lines = [
        f"<!-- {DO_NOT_EDIT} -->",
        "",
        "# 프로젝트 상태 핸드오프 (생성 문서)",
        "",
        f"- project_id: `{payload['project_id']}`",
        f"- state_version: {payload['state_version']}",
        f"- last_event_id: `{payload['last_event_id']}`",
        f"- phase: `{payload['phase']}`",
        f"- lifecycle: `{payload['lifecycle']}`",
        f"- generations: {payload['generation_count']} (open: `{payload['open_generation']}`)",
        f"- artifacts: {payload['artifact_count']}, "
        f"approvals: {payload['approval_count']}, "
        f"failures: {payload['failure_count']}",
        f"- generated_at: {payload['generated_at']} "
        f"(application {payload['application_version']}, "
        f"view schema v{payload['schema_version']})",
        "",
        "이 문서는 `workflow.sqlite`에서 생성된 읽기 전용 보기다. 상태 변경은",
        "`workflow state ...` 명령으로만 하며, 이 파일을 편집해도 무시된다.",
        "",
    ]
    return "\n".join(lines)


def export_views(store: SqliteStateStore) -> tuple[Path, Path]:
    """Render both views deterministically; returns their paths."""
    stored = store.load()
    generated_dir = store.project_dir / "generated"
    generated_dir.mkdir(exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    payload = _status_payload(stored, generated_at)
    status_path = generated_dir / "status.json"
    handoff_path = generated_dir / "SESSION_HANDOFF.md"
    _atomic_write(
        status_path,
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    _atomic_write(handoff_path, _handoff_markdown(payload))
    return status_path, handoff_path


def normalized_view_bytes(store: SqliteStateStore) -> bytes:
    """View content with the volatile timestamp fixed, for determinism tests."""
    stored = store.load()
    payload = _status_payload(stored, generated_at="1970-01-01T00:00:00+00:00")
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
