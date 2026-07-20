"""SQLite store unit tests: lifecycle, schema safety, append-only, migration."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest

from video_workflow.domain import ProjectId
from video_workflow.storage import (
    CorruptionError,
    DatabaseExistsError,
    DatabaseMissingError,
    FutureSchemaError,
    MigrationError,
    SqliteStateStore,
    WorkspaceError,
)
from video_workflow.storage import sqlite_store as store_module


def _workspace(tmp_path: Path) -> Path:
    # Korean + space in the path is a required scenario.
    workspace = tmp_path / "작업 공간"
    workspace.mkdir()
    return workspace


def _project_id(seed: int = 1) -> ProjectId:
    return ProjectId.from_uuid(uuid.UUID(int=seed, version=4))


def test_init_creates_layout_and_refuses_overwrite(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    store = SqliteStateStore.initialize(workspace, _project_id())
    assert store.db_path.is_file()
    for subdir in ("source_refs", "artifacts", "approvals", "generated"):
        assert (store.project_dir / subdir).is_dir()
    stored = store.load()
    assert stored.state_version == 0
    assert stored.state.phase.value == "intake"
    with pytest.raises(DatabaseExistsError):
        SqliteStateStore.initialize(workspace, _project_id())


def test_read_commands_never_create_databases(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    with pytest.raises(DatabaseMissingError):
        SqliteStateStore.open(workspace, _project_id())
    # Nothing was created as a side effect.
    assert not (workspace / "projects").exists() or not any(
        (workspace / "projects").rglob("workflow.sqlite")
    )


def test_network_share_workspace_is_refused(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceError):
        SqliteStateStore.initialize(Path("//server/share/ws"), _project_id())
    with pytest.raises(WorkspaceError):
        SqliteStateStore.open(Path("\\\\server\\share\\ws"), _project_id())


def test_future_schema_fails_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    store = SqliteStateStore.initialize(workspace, _project_id())
    connection = sqlite3.connect(store.db_path)
    connection.execute("UPDATE schema_meta SET schema_version = 99")
    connection.commit()
    connection.close()
    with pytest.raises(FutureSchemaError):
        SqliteStateStore.open(workspace, _project_id())
    with pytest.raises(FutureSchemaError):
        store.load()


def test_tables_without_schema_meta_is_corruption(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    store = SqliteStateStore.initialize(workspace, _project_id())
    connection = sqlite3.connect(store.db_path)
    connection.execute("DROP TABLE schema_meta")
    connection.commit()
    connection.close()
    with pytest.raises(CorruptionError):
        store.load()


def test_workflow_events_are_append_only(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    store = SqliteStateStore.initialize(workspace, _project_id())
    connection = sqlite3.connect(store.db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        "INSERT INTO workflow_events (event_id, command_id, request_digest, "
        "project_id, event_type, prev_lifecycle, next_lifecycle, prev_phase, "
        "next_phase, state_version, actor_kind, actor_id, payload_json, "
        "occurred_at) VALUES ('evt-x', 'cmd-x', ?, ?, 'source_registered', "
        "'active', 'active', 'intake', 'intake', 1, 'agent', 'test', '{}', "
        "'2026-07-17T05:00:00+00:00')",
        ("0" * 64, _project_id().value),
    )
    connection.commit()
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute("UPDATE workflow_events SET actor_id = 'evil'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute("DELETE FROM workflow_events")
    connection.close()


def test_constraints_reject_bad_rows(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    store = SqliteStateStore.initialize(workspace, _project_id())
    connection = sqlite3.connect(store.db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    with pytest.raises(sqlite3.IntegrityError):
        # Unknown project (FK violation).
        connection.execute(
            "INSERT INTO sources (source_id, project_id, fingerprint_algorithm, "
            "fingerprint_digest, size_bytes, locator, registered_at) VALUES "
            "('src-x', 'prj-missing', 'sha256', ?, 1, 'l', 'now')",
            ("0" * 64,),
        )
    with pytest.raises(sqlite3.IntegrityError):
        # CHECK violation (bad lifecycle enum).
        connection.execute("UPDATE projects SET lifecycle_status = 'nonsense'")
    connection.close()


def test_migration_noop_and_failure_restores_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = _workspace(tmp_path)
    store = SqliteStateStore.initialize(workspace, _project_id())
    assert store.migrate() == (1, 1)  # already current: no-op

    original = store_module._known_migrations()

    def with_bad_migration() -> list[tuple[int, str, str]]:
        return [*original, (2, "0002_bad.sql", "CREATE TABLE broken (x INVALID_TYPE;")]

    monkeypatch.setattr(store_module, "_known_migrations", with_bad_migration)
    with pytest.raises(MigrationError, match="restored"):
        store.migrate()
    monkeypatch.setattr(store_module, "_known_migrations", lambda: original)
    # The previous database is intact and usable.
    stored = store.load()
    assert stored.state_version == 0
