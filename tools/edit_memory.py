#!/usr/bin/env python3
"""Persistent edit-decision memory backed by SQLite and append-only events."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
EVENT_TYPES = {
    "source_atom.registered",
    "story_beat.defined",
    "revision.created",
    "revision.status_changed",
    "timeline.node_added",
    "timeline.edge_added",
    "revision.operation_added",
    "feedback.recorded",
    "evaluation.recorded",
    "baseline.set",
}
REVISION_STATUSES = {"candidate", "working", "preferred", "approved", "rejected", "superseded"}
BASELINE_NAMES = {"working", "preferred", "approved"}


class EditMemoryError(RuntimeError):
    """Raised when an edit-memory event would create invalid state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EditMemoryError(f"{label} must be an object")
    return value


def require_text(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EditMemoryError(f"{key} must be a non-empty string")
    return value.strip()


def optional_text(mapping: dict[str, Any], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise EditMemoryError(f"{key} must be null or a non-empty string")
    return value.strip()


def require_number(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EditMemoryError(f"{key} must be a number")
    return float(value)


DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    revision_id TEXT,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    supersedes_event_id TEXT,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS source_atoms (
    atom_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_in REAL NOT NULL,
    source_out REAL NOT NULL,
    sentence_complete_at REAL,
    speaker TEXT,
    scene_id TEXT,
    story_function TEXT,
    emotion TEXT,
    transcript TEXT,
    safe_cut_points_json TEXT NOT NULL,
    created_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS story_beats (
    beat_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    purpose TEXT NOT NULL,
    viewer_information TEXT,
    character_state_before TEXT,
    character_state_after TEXT,
    status TEXT NOT NULL,
    created_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS revisions (
    revision_id TEXT PRIMARY KEY,
    parent_revision_id TEXT REFERENCES revisions(revision_id),
    source_id TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS timeline_nodes (
    revision_id TEXT NOT NULL REFERENCES revisions(revision_id),
    node_id TEXT NOT NULL,
    sequence_name TEXT NOT NULL,
    position INTEGER NOT NULL,
    atom_id TEXT REFERENCES source_atoms(atom_id),
    source_in REAL NOT NULL,
    source_out REAL NOT NULL,
    label TEXT NOT NULL,
    role TEXT NOT NULL,
    video_track INTEGER NOT NULL,
    audio_mode TEXT,
    timeline_start REAL,
    created_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id),
    PRIMARY KEY (revision_id, node_id),
    UNIQUE (revision_id, sequence_name, position)
);

CREATE TABLE IF NOT EXISTS timeline_edges (
    revision_id TEXT NOT NULL REFERENCES revisions(revision_id),
    edge_id TEXT NOT NULL,
    from_node_id TEXT NOT NULL,
    to_node_id TEXT NOT NULL,
    semantic_relation TEXT,
    audio_transition TEXT,
    continuity_risk REAL,
    evidence TEXT,
    created_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id),
    PRIMARY KEY (revision_id, edge_id),
    FOREIGN KEY (revision_id, from_node_id) REFERENCES timeline_nodes(revision_id, node_id),
    FOREIGN KEY (revision_id, to_node_id) REFERENCES timeline_nodes(revision_id, node_id)
);

CREATE TABLE IF NOT EXISTS revision_operations (
    operation_id TEXT PRIMARY KEY,
    revision_id TEXT NOT NULL REFERENCES revisions(revision_id),
    position INTEGER NOT NULL,
    operation_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT,
    rationale TEXT NOT NULL,
    preserve_json TEXT NOT NULL,
    created_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id),
    UNIQUE (revision_id, position)
);

CREATE TABLE IF NOT EXISTS feedback_events (
    event_id TEXT PRIMARY KEY REFERENCES events(event_id),
    revision_id TEXT REFERENCES revisions(revision_id),
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    dimension TEXT NOT NULL,
    severity TEXT NOT NULL,
    scope TEXT NOT NULL,
    observation TEXT NOT NULL,
    evidence TEXT,
    persists_until TEXT NOT NULL,
    supersedes_event_id TEXT REFERENCES feedback_events(event_id)
);

CREATE TABLE IF NOT EXISTS evaluation_events (
    event_id TEXT PRIMARY KEY REFERENCES events(event_id),
    revision_id TEXT NOT NULL REFERENCES revisions(revision_id),
    evaluator TEXT NOT NULL,
    method TEXT NOT NULL,
    scope TEXT NOT NULL,
    verdict TEXT NOT NULL,
    dimensions_json TEXT NOT NULL,
    evidence TEXT,
    actual_av_observed INTEGER NOT NULL CHECK (actual_av_observed IN (0, 1))
);

CREATE TABLE IF NOT EXISTS baseline_pointers (
    name TEXT PRIMARY KEY,
    revision_id TEXT REFERENCES revisions(revision_id),
    note TEXT,
    updated_at TEXT NOT NULL,
    updated_event_id TEXT NOT NULL UNIQUE REFERENCES events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_events_revision ON events(revision_id, seq);
CREATE INDEX IF NOT EXISTS idx_feedback_target ON feedback_events(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_revision ON evaluation_events(revision_id);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(DDL)
    created_at = connection.execute(
        "SELECT value FROM metadata WHERE key = 'created_at'"
    ).fetchone()
    now = utc_now()
    if created_at is None:
        connection.execute("INSERT INTO metadata(key, value) VALUES('created_at', ?)", (now,))
    connection.execute(
        "INSERT INTO metadata(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(SCHEMA_VERSION),),
    )
    connection.execute(
        "INSERT INTO metadata(key, value) VALUES('updated_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (now,),
    )
    connection.commit()


def _insert_event(connection: sqlite3.Connection, event: dict[str, Any], source_file: str | None) -> bool:
    event_id = require_text(event, "event_id")
    event_type = require_text(event, "event_type")
    if event_type not in EVENT_TYPES:
        raise EditMemoryError(f"unsupported event_type: {event_type}")
    aggregate_type = require_text(event, "aggregate_type")
    aggregate_id = require_text(event, "aggregate_id")
    revision_id = optional_text(event, "revision_id")
    occurred_at = require_text(event, "occurred_at")
    supersedes_event_id = optional_text(event, "supersedes_event_id")
    payload = require_mapping(event.get("payload"), "payload")
    payload_json = canonical_json(payload)

    existing = connection.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
    if existing is not None:
        comparable = {
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "revision_id": revision_id,
            "occurred_at": occurred_at,
            "payload_json": payload_json,
            "supersedes_event_id": supersedes_event_id,
        }
        if all(existing[key] == value for key, value in comparable.items()):
            return False
        raise EditMemoryError(f"event_id already exists with different content: {event_id}")

    connection.execute(
        "INSERT INTO events(event_id, event_type, aggregate_type, aggregate_id, revision_id, "
        "occurred_at, payload_json, supersedes_event_id, source_file) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event_id,
            event_type,
            aggregate_type,
            aggregate_id,
            revision_id,
            occurred_at,
            payload_json,
            supersedes_event_id,
            source_file,
        ),
    )
    _reduce_event(connection, event_id, event_type, aggregate_id, revision_id, occurred_at, payload, supersedes_event_id)
    return True


def _reduce_event(
    connection: sqlite3.Connection,
    event_id: str,
    event_type: str,
    aggregate_id: str,
    revision_id: str | None,
    occurred_at: str,
    payload: dict[str, Any],
    supersedes_event_id: str | None,
) -> None:
    reducers = {
        "source_atom.registered": _source_atom_registered,
        "story_beat.defined": _story_beat_defined,
        "revision.created": _revision_created,
        "revision.status_changed": _revision_status_changed,
        "timeline.node_added": _timeline_node_added,
        "timeline.edge_added": _timeline_edge_added,
        "revision.operation_added": _revision_operation_added,
        "feedback.recorded": _feedback_recorded,
        "evaluation.recorded": _evaluation_recorded,
        "baseline.set": _baseline_set,
    }
    reducers[event_type](
        connection, event_id, aggregate_id, revision_id, occurred_at, payload, supersedes_event_id
    )


def _source_atom_registered(connection, event_id, aggregate_id, _revision_id, _occurred_at, payload, _supersedes):
    source_in = require_number(payload, "source_in")
    source_out = require_number(payload, "source_out")
    if source_out <= source_in:
        raise EditMemoryError("source atom source_out must be greater than source_in")
    safe_points = payload.get("safe_cut_points", [])
    if not isinstance(safe_points, list) or any(
        isinstance(value, bool) or not isinstance(value, (int, float)) for value in safe_points
    ):
        raise EditMemoryError("safe_cut_points must be a number array")
    if any(float(value) < source_in or float(value) > source_out for value in safe_points):
        raise EditMemoryError("safe_cut_points must stay inside the atom range")
    sentence_complete_at = payload.get("sentence_complete_at")
    if sentence_complete_at is not None:
        if isinstance(sentence_complete_at, bool) or not isinstance(sentence_complete_at, (int, float)):
            raise EditMemoryError("sentence_complete_at must be null or a number")
        if not source_in <= float(sentence_complete_at) <= source_out:
            raise EditMemoryError("sentence_complete_at must stay inside the atom range")
    connection.execute(
        "INSERT INTO source_atoms VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            aggregate_id,
            require_text(payload, "source_id"),
            source_in,
            source_out,
            sentence_complete_at,
            optional_text(payload, "speaker"),
            optional_text(payload, "scene_id"),
            optional_text(payload, "story_function"),
            optional_text(payload, "emotion"),
            optional_text(payload, "transcript"),
            canonical_json([float(value) for value in safe_points]),
            event_id,
        ),
    )


def _story_beat_defined(connection, event_id, aggregate_id, _revision_id, _occurred_at, payload, _supersedes):
    position = payload.get("position")
    if isinstance(position, bool) or not isinstance(position, int) or position < 1:
        raise EditMemoryError("story beat position must be a positive integer")
    connection.execute(
        "INSERT INTO story_beats VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            aggregate_id,
            require_text(payload, "source_id"),
            position,
            require_text(payload, "purpose"),
            optional_text(payload, "viewer_information"),
            optional_text(payload, "character_state_before"),
            optional_text(payload, "character_state_after"),
            require_text(payload, "status"),
            event_id,
        ),
    )


def _revision_created(connection, event_id, aggregate_id, revision_id, occurred_at, payload, _supersedes):
    if revision_id is not None and revision_id != aggregate_id:
        raise EditMemoryError("revision.created revision_id must match aggregate_id when provided")
    status = require_text(payload, "status")
    if status not in REVISION_STATUSES:
        raise EditMemoryError(f"unsupported revision status: {status}")
    parent = optional_text(payload, "parent_revision_id")
    connection.execute(
        "INSERT INTO revisions VALUES(?, ?, ?, ?, ?, ?, ?)",
        (
            aggregate_id,
            parent,
            require_text(payload, "source_id"),
            require_text(payload, "hypothesis"),
            status,
            occurred_at,
            event_id,
        ),
    )


def _revision_status_changed(connection, _event_id, aggregate_id, revision_id, _occurred_at, payload, _supersedes):
    target = revision_id or aggregate_id
    status = require_text(payload, "status")
    if status not in REVISION_STATUSES:
        raise EditMemoryError(f"unsupported revision status: {status}")
    cursor = connection.execute("UPDATE revisions SET status = ? WHERE revision_id = ?", (status, target))
    if cursor.rowcount != 1:
        raise EditMemoryError(f"unknown revision: {target}")


def _timeline_node_added(connection, event_id, aggregate_id, revision_id, _occurred_at, payload, _supersedes):
    if revision_id is None:
        raise EditMemoryError("timeline.node_added requires revision_id")
    source_in = require_number(payload, "source_in")
    source_out = require_number(payload, "source_out")
    if source_out <= source_in:
        raise EditMemoryError("timeline node source_out must be greater than source_in")
    position = payload.get("position")
    if isinstance(position, bool) or not isinstance(position, int) or position < 1:
        raise EditMemoryError("timeline node position must be a positive integer")
    video_track = payload.get("video_track", 1)
    if isinstance(video_track, bool) or not isinstance(video_track, int) or video_track < 1:
        raise EditMemoryError("timeline node video_track must be a positive integer")
    timeline_start = payload.get("timeline_start")
    if timeline_start is not None and (
        isinstance(timeline_start, bool) or not isinstance(timeline_start, (int, float))
    ):
        raise EditMemoryError("timeline_start must be null or a number")
    connection.execute(
        "INSERT INTO timeline_nodes VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            revision_id,
            aggregate_id,
            require_text(payload, "sequence_name"),
            position,
            optional_text(payload, "atom_id"),
            source_in,
            source_out,
            require_text(payload, "label"),
            require_text(payload, "role"),
            video_track,
            optional_text(payload, "audio_mode"),
            timeline_start,
            event_id,
        ),
    )


def _timeline_edge_added(connection, event_id, aggregate_id, revision_id, _occurred_at, payload, _supersedes):
    if revision_id is None:
        raise EditMemoryError("timeline.edge_added requires revision_id")
    risk = payload.get("continuity_risk")
    if risk is not None:
        if isinstance(risk, bool) or not isinstance(risk, (int, float)) or not 0 <= float(risk) <= 1:
            raise EditMemoryError("continuity_risk must be null or a number from 0 to 1")
    connection.execute(
        "INSERT INTO timeline_edges VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            revision_id,
            aggregate_id,
            require_text(payload, "from_node_id"),
            require_text(payload, "to_node_id"),
            optional_text(payload, "semantic_relation"),
            optional_text(payload, "audio_transition"),
            None if risk is None else float(risk),
            optional_text(payload, "evidence"),
            event_id,
        ),
    )


def _revision_operation_added(connection, event_id, aggregate_id, revision_id, _occurred_at, payload, _supersedes):
    if revision_id is None:
        raise EditMemoryError("revision.operation_added requires revision_id")
    position = payload.get("position")
    if isinstance(position, bool) or not isinstance(position, int) or position < 1:
        raise EditMemoryError("revision operation position must be a positive integer")
    preserve = payload.get("preserve", [])
    if not isinstance(preserve, list) or any(not isinstance(value, str) for value in preserve):
        raise EditMemoryError("preserve must be a string array")
    connection.execute(
        "INSERT INTO revision_operations VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            aggregate_id,
            revision_id,
            position,
            require_text(payload, "operation_type"),
            require_text(payload, "target_type"),
            require_text(payload, "target_id"),
            canonical_json(payload.get("before")) if "before" in payload else None,
            canonical_json(payload.get("after")) if "after" in payload else None,
            require_text(payload, "rationale"),
            canonical_json(preserve),
            event_id,
        ),
    )


def _feedback_recorded(connection, event_id, _aggregate_id, revision_id, _occurred_at, payload, supersedes_event_id):
    connection.execute(
        "INSERT INTO feedback_events VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event_id,
            revision_id,
            require_text(payload, "target_type"),
            require_text(payload, "target_id"),
            require_text(payload, "verdict"),
            require_text(payload, "dimension"),
            require_text(payload, "severity"),
            require_text(payload, "scope"),
            require_text(payload, "observation"),
            optional_text(payload, "evidence"),
            require_text(payload, "persists_until"),
            supersedes_event_id,
        ),
    )


def _evaluation_recorded(connection, event_id, _aggregate_id, revision_id, _occurred_at, payload, _supersedes):
    if revision_id is None:
        raise EditMemoryError("evaluation.recorded requires revision_id")
    dimensions = payload.get("dimensions", {})
    if not isinstance(dimensions, dict):
        raise EditMemoryError("evaluation dimensions must be an object")
    actual_av = payload.get("actual_av_observed")
    if not isinstance(actual_av, bool):
        raise EditMemoryError("actual_av_observed must be a boolean")
    connection.execute(
        "INSERT INTO evaluation_events VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event_id,
            revision_id,
            require_text(payload, "evaluator"),
            require_text(payload, "method"),
            require_text(payload, "scope"),
            require_text(payload, "verdict"),
            canonical_json(dimensions),
            optional_text(payload, "evidence"),
            int(actual_av),
        ),
    )


def _baseline_set(connection, event_id, aggregate_id, _revision_id, occurred_at, payload, _supersedes):
    name = require_text(payload, "name")
    if name not in BASELINE_NAMES or aggregate_id != name:
        raise EditMemoryError("baseline name must be working, preferred, or approved and match aggregate_id")
    target = optional_text(payload, "revision_id")
    if target is not None:
        row = connection.execute("SELECT status FROM revisions WHERE revision_id = ?", (target,)).fetchone()
        if row is None:
            raise EditMemoryError(f"unknown baseline revision: {target}")
        if row["status"] in {"rejected", "superseded"}:
            raise EditMemoryError(f"baseline cannot point to {row['status']} revision: {target}")
        if name == "approved" and row["status"] != "approved":
            raise EditMemoryError("approved baseline must point to an approved revision")
    connection.execute(
        "INSERT INTO baseline_pointers VALUES(?, ?, ?, ?, ?) "
        "ON CONFLICT(name) DO UPDATE SET revision_id = excluded.revision_id, note = excluded.note, "
        "updated_at = excluded.updated_at, updated_event_id = excluded.updated_event_id",
        (name, target, optional_text(payload, "note"), occurred_at, event_id),
    )


def apply_batch(connection: sqlite3.Connection, batch: dict[str, Any], source_file: str | None = None) -> dict[str, int]:
    if batch.get("schema_version") != SCHEMA_VERSION:
        raise EditMemoryError(f"batch schema_version must be {SCHEMA_VERSION}")
    events = batch.get("events")
    if not isinstance(events, list):
        raise EditMemoryError("events must be an array")
    applied = 0
    skipped = 0
    try:
        connection.execute("BEGIN IMMEDIATE")
        for index, raw_event in enumerate(events):
            event = require_mapping(raw_event, f"events[{index}]")
            if _insert_event(connection, event, source_file):
                applied += 1
            else:
                skipped += 1
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES('updated_at', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (utc_now(),),
        )
        connection.commit()
    except (sqlite3.Error, EditMemoryError) as exc:
        connection.rollback()
        if isinstance(exc, EditMemoryError):
            raise
        raise EditMemoryError(str(exc)) from exc
    return {"applied": applied, "skipped": skipped}


def active_feedback(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT f.* FROM feedback_events f "
        "WHERE NOT EXISTS (SELECT 1 FROM feedback_events newer WHERE newer.supersedes_event_id = f.event_id) "
        "ORDER BY CASE f.severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 ELSE 2 END, f.event_id"
    ).fetchall()
    return [dict(row) for row in rows]


def _revision_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT r.*, "
        "(SELECT COUNT(*) FROM timeline_nodes n WHERE n.revision_id = r.revision_id) AS node_count, "
        "(SELECT COUNT(*) FROM timeline_edges e WHERE e.revision_id = r.revision_id) AS edge_count, "
        "(SELECT COUNT(*) FROM evaluation_events v WHERE v.revision_id = r.revision_id) AS evaluation_count, "
        "(SELECT COUNT(*) FROM evaluation_events v WHERE v.revision_id = r.revision_id "
        " AND v.actual_av_observed = 1) AS actual_av_evaluation_count "
        ", (SELECT COUNT(*) FROM evaluation_events v WHERE v.revision_id = r.revision_id "
        " AND v.actual_av_observed = 1 AND v.evaluator = 'agent') AS agent_actual_av_evaluation_count "
        ", (SELECT COUNT(*) FROM evaluation_events v WHERE v.revision_id = r.revision_id "
        " AND v.actual_av_observed = 1 AND v.evaluator = 'user') AS user_actual_av_evaluation_count "
        "FROM revisions r ORDER BY r.created_at, r.revision_id"
    ).fetchall()
    return [dict(row) for row in rows]


def snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    metadata = {row["key"]: row["value"] for row in connection.execute("SELECT * FROM metadata")}
    baselines = {
        row["name"]: {
            "revision_id": row["revision_id"],
            "note": row["note"],
            "updated_at": row["updated_at"],
        }
        for row in connection.execute("SELECT * FROM baseline_pointers ORDER BY name")
    }
    for name in sorted(BASELINE_NAMES):
        baselines.setdefault(name, {"revision_id": None, "note": "not set", "updated_at": None})
    evaluations = []
    for row in connection.execute("SELECT * FROM evaluation_events ORDER BY event_id"):
        item = dict(row)
        item["dimensions"] = json.loads(item.pop("dimensions_json"))
        item["actual_av_observed"] = bool(item["actual_av_observed"])
        evaluations.append(item)
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": metadata,
        "event_count": connection.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        "revisions": _revision_rows(connection),
        "baselines": baselines,
        "active_feedback": active_feedback(connection),
        "evaluations": evaluations,
    }


def validate(connection: sqlite3.Connection) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        errors.append(f"sqlite integrity: {integrity}")
    for row in connection.execute("PRAGMA foreign_key_check"):
        errors.append(f"foreign key failure: {tuple(row)}")

    revisions = {row["revision_id"]: row["parent_revision_id"] for row in connection.execute(
        "SELECT revision_id, parent_revision_id FROM revisions"
    )}
    for start in revisions:
        seen: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in seen:
                errors.append(f"revision cycle detected from {start}")
                break
            seen.add(current)
            current = revisions.get(current)

    for row in connection.execute(
        "SELECT b.name, b.revision_id, r.status FROM baseline_pointers b "
        "LEFT JOIN revisions r ON r.revision_id = b.revision_id WHERE b.revision_id IS NOT NULL"
    ):
        if row["status"] in {"rejected", "superseded"}:
            errors.append(f"{row['name']} baseline points to {row['status']} revision {row['revision_id']}")
        if row["name"] == "approved" and row["status"] != "approved":
            errors.append(f"approved baseline points to non-approved revision {row['revision_id']}")

    working = connection.execute(
        "SELECT revision_id FROM baseline_pointers WHERE name = 'working'"
    ).fetchone()
    if working is None or working["revision_id"] is None:
        warnings.append("working baseline is not selected")
    approved = connection.execute(
        "SELECT revision_id FROM baseline_pointers WHERE name = 'approved'"
    ).fetchone()
    if approved is None or approved["revision_id"] is None:
        warnings.append("approved baseline is not selected")
    for row in connection.execute(
        "SELECT revision_id FROM revisions WHERE NOT EXISTS ("
        "SELECT 1 FROM evaluation_events e WHERE e.revision_id = revisions.revision_id "
        "AND e.actual_av_observed = 1)"
    ):
        warnings.append(f"revision has no actual A/V observation: {row['revision_id']}")
    for row in connection.execute(
        "SELECT revision_id FROM revisions WHERE NOT EXISTS ("
        "SELECT 1 FROM evaluation_events e WHERE e.revision_id = revisions.revision_id "
        "AND e.actual_av_observed = 1 AND e.evaluator = 'agent')"
    ):
        warnings.append(f"revision has no agent actual A/V observation: {row['revision_id']}")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "snapshot": snapshot(connection)}


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return require_mapping(json.loads(path.read_text(encoding="utf-8")), str(path))
    except (OSError, json.JSONDecodeError) as exc:
        raise EditMemoryError(f"cannot read {path}: {exc}") from exc


def print_json(value: Any, stream=None) -> None:
    stream = stream or sys.stdout
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    encoding = getattr(stream, "encoding", None) or "utf-8"
    encoded = payload.encode(encoding, errors="backslashreplace")
    if hasattr(stream, "buffer"):
        stream.buffer.write(encoded)
        stream.buffer.flush()
    else:  # pragma: no cover - StringIO and unusual embedded runners
        stream.write(encoded.decode(encoding))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Store and query cumulative edit decisions.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "validate"):
        command = subparsers.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
    apply_command = subparsers.add_parser("apply")
    apply_command.add_argument("--db", type=Path, required=True)
    apply_command.add_argument("--input", type=Path, required=True)
    export_command = subparsers.add_parser("export")
    export_command.add_argument("--db", type=Path, required=True)
    export_command.add_argument("--output", type=Path, required=True)
    return parser


def run(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with connect(args.db) as connection:
            initialize(connection)
            if args.command == "init":
                result: Any = {"ok": True, "initialized": str(args.db), "schema_version": SCHEMA_VERSION}
            elif args.command == "apply":
                result = {"ok": True, **apply_batch(connection, read_json(args.input), str(args.input))}
            elif args.command == "status":
                result = snapshot(connection)
            elif args.command == "validate":
                result = validate(connection)
            elif args.command == "export":
                result = snapshot(connection)
                write_json_atomic(args.output, result)
                result = {"ok": True, "output": str(args.output), "event_count": result["event_count"]}
            else:  # pragma: no cover
                raise EditMemoryError(f"unknown command: {args.command}")
        print_json(result)
        return 0 if result.get("ok", True) else 1
    except EditMemoryError as exc:
        print_json({"ok": False, "error": str(exc)}, stream=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
