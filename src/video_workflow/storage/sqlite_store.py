"""SQLite implementation of the state store (stage 03).

Operating contract:
- one ``workflow.sqlite`` per project is the only persistent source of truth;
- ``foreign_keys`` on for every connection, explicit transactions,
  ``BEGIN IMMEDIATE`` for writes, ``busy_timeout`` without hiding lock
  failures;
- optimistic concurrency via ``projects.state_version``;
- network-share workspaces are refused by default;
- reads never create a database; corruption and future schemas fail, never
  auto-reinitialize;
- a consistent backup is taken (SQLite backup API) before migrating an
  existing database.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import cast

from video_workflow.domain import (
    Actor,
    ActorKind,
    ActorProvenance,
    ApprovalDecision,
    ApprovalRecord,
    ApprovalTarget,
    ApprovalType,
    ArtifactId,
    ArtifactRecord,
    ArtifactRole,
    Command,
    CommandId,
    EventId,
    FailureRecord,
    GenerationId,
    GenerationState,
    GenerationStatus,
    LifecycleStatus,
    Phase,
    ProcessedCommand,
    ProjectId,
    ProjectState,
    RecordApproval,
    RecordArtifact,
    RecordFailure,
    RegisterSource,
    SourceFingerprint,
    SourceId,
    TransitionAccepted,
    serialize,
)
from video_workflow.storage.errors import (
    ConcurrencyConflictError,
    CorruptionError,
    DatabaseExistsError,
    DatabaseMissingError,
    FutureSchemaError,
    MigrationError,
    WorkspaceError,
)
from video_workflow.storage.port import (
    CommitExtras,
    CommitReceipt,
    StoredState,
    VerifyIssue,
    VerifyReport,
)

APPLICATION_VERSION = "0.1.0"
DB_FILENAME = "workflow.sqlite"
PROJECT_SUBDIRS = ("source_refs", "artifacts", "approvals", "generated")
_MIGRATIONS_PACKAGE = "video_workflow.storage.migrations"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _is_network_share(path: Path) -> bool:
    text = str(path)
    return text.startswith("\\\\") or text.startswith("//")


def _known_migrations() -> list[tuple[int, str, str]]:
    """Return (version, name, sql) sorted ascending."""
    package = resources.files(_MIGRATIONS_PACKAGE)
    found: list[tuple[int, str, str]] = []
    for entry in package.iterdir():
        name = entry.name
        if not name.endswith(".sql"):
            continue
        prefix = name.split("_", 1)[0]
        if not prefix.isdigit():
            raise MigrationError(f"migration name must start with digits: {name}")
        found.append((int(prefix), name, entry.read_text(encoding="utf-8")))
    found.sort()
    if not found:
        raise MigrationError("no migrations found")
    return found


def project_directory(workspace: Path, project_id: ProjectId) -> Path:
    return workspace / "projects" / project_id.value


@dataclass(frozen=True, slots=True)
class SqliteStateStore:
    """State store bound to one project directory."""

    project_dir: Path
    project_id: ProjectId

    @property
    def db_path(self) -> Path:
        return self.project_dir / DB_FILENAME

    # -- connection helpers -------------------------------------------------

    def _connect(self, *, must_exist: bool = True) -> sqlite3.Connection:
        if must_exist and not self.db_path.is_file():
            raise DatabaseMissingError(
                f"project database not found: {self.db_path.name}; "
                "read commands never create a database (run 'state init')"
            )
        connection = sqlite3.connect(self.db_path, isolation_level=None, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _schema_version(self, connection: sqlite3.Connection) -> int:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if not tables:
            return 0
        if "schema_meta" not in tables:
            raise CorruptionError("database has tables but no schema_meta; refusing to guess")
        row = connection.execute(
            "SELECT MAX(schema_version) AS version FROM schema_meta"
        ).fetchone()
        version = row["version"]
        if not isinstance(version, int):
            raise CorruptionError("schema_meta holds no valid schema_version")
        return version

    def _check_schema(self, connection: sqlite3.Connection) -> None:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise CorruptionError("PRAGMA integrity_check failed; no auto-repair")
        known = _known_migrations()[-1][0]
        current = self._schema_version(connection)
        if current > known:
            raise FutureSchemaError(f"database schema v{current} is newer than supported v{known}")
        if current < known:
            raise MigrationError(f"database schema v{current} needs migration to v{known}")

    # -- lifecycle ----------------------------------------------------------

    @classmethod
    def initialize(cls, workspace: Path, project_id: ProjectId) -> SqliteStateStore:
        """Create the project directory tree and database. Only `init` does this."""
        if _is_network_share(workspace):
            raise WorkspaceError("network-share workspaces are refused by default (WAL safety)")
        if not workspace.is_dir():
            raise WorkspaceError(f"workspace directory does not exist: {workspace}")
        directory = project_directory(workspace, project_id)
        store = cls(project_dir=directory, project_id=project_id)
        if store.db_path.exists():
            raise DatabaseExistsError("project database already exists; init never overwrites")
        directory.mkdir(parents=True, exist_ok=True)
        for subdir in PROJECT_SUBDIRS:
            (directory / subdir).mkdir(exist_ok=True)
        temp_path = directory / (DB_FILENAME + ".tmp")
        if temp_path.exists():
            temp_path.unlink()
        connection = sqlite3.connect(temp_path, isolation_level=None)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            for version, name, sql in _known_migrations():
                try:
                    connection.executescript(sql)
                except sqlite3.Error as exc:
                    raise MigrationError(f"migration {name} failed: {exc}") from exc
                connection.execute(
                    "INSERT INTO schema_meta (schema_version, applied_at, "
                    "application_version) VALUES (?, ?, ?)",
                    (version, _utc_now_iso(), APPLICATION_VERSION),
                )
            now = _utc_now_iso()
            connection.execute(
                "INSERT INTO projects (project_id, source_id, lifecycle_status, "
                "current_phase, state_version, created_at, updated_at, last_event_id) "
                "VALUES (?, NULL, 'active', 'intake', 0, ?, ?, NULL)",
                (project_id.value, now, now),
            )
            connection.commit()
        finally:
            connection.close()
        os.replace(temp_path, store.db_path)
        return store

    @classmethod
    def open(cls, workspace: Path, project_id: ProjectId) -> SqliteStateStore:
        if _is_network_share(workspace):
            raise WorkspaceError("network-share workspaces are refused by default (WAL safety)")
        store = cls(
            project_dir=project_directory(workspace, project_id),
            project_id=project_id,
        )
        connection = store._connect()
        try:
            store._check_schema(connection)
        finally:
            connection.close()
        return store

    def migrate(self) -> tuple[int, int]:
        """Apply pending migrations with a pre-migration backup.

        Returns (from_version, to_version). On failure the previous database
        is restored from the backup and MigrationError is raised.
        """
        connection = self._connect()
        try:
            current = self._schema_version(connection)
        finally:
            connection.close()
        migrations = _known_migrations()
        target = migrations[-1][0]
        if current > target:
            raise FutureSchemaError(f"database schema v{current} is newer than supported v{target}")
        if current == target:
            return current, target
        backup_path = self.db_path.with_name(f"{DB_FILENAME}.bak-v{current}")
        source = sqlite3.connect(self.db_path)
        try:
            destination = sqlite3.connect(backup_path)
            try:
                source.backup(destination)
            finally:
                destination.close()
        finally:
            source.close()
        connection = self._connect()
        try:
            for version, name, sql in migrations:
                if version <= current:
                    continue
                try:
                    connection.executescript(sql)
                    connection.execute(
                        "INSERT INTO schema_meta (schema_version, applied_at, "
                        "application_version) VALUES (?, ?, ?)",
                        (version, _utc_now_iso(), APPLICATION_VERSION),
                    )
                    connection.commit()
                except sqlite3.Error as exc:
                    connection.close()
                    os.replace(backup_path, self.db_path)
                    raise MigrationError(
                        f"migration {name} failed and the previous database was restored: {exc}"
                    ) from exc
        finally:
            try:
                connection.close()
            except sqlite3.Error:  # pragma: no cover - close is best effort
                pass
        return current, target

    # -- load ---------------------------------------------------------------

    def load(self) -> StoredState:
        connection = self._connect()
        try:
            self._check_schema(connection)
            return self._load_with(connection)
        finally:
            connection.close()

    def _load_with(self, connection: sqlite3.Connection) -> StoredState:
        project = connection.execute(
            "SELECT * FROM projects WHERE project_id = ?", (self.project_id.value,)
        ).fetchone()
        if project is None:
            raise CorruptionError("projects row missing for this project id")
        source_id: SourceId | None = None
        fingerprint: SourceFingerprint | None = None
        source_row = connection.execute(
            "SELECT * FROM sources WHERE project_id = ? ORDER BY rowid LIMIT 1",
            (self.project_id.value,),
        ).fetchone()
        if source_row is not None:
            source_id = SourceId.parse(source_row["source_id"])
            fingerprint = SourceFingerprint(
                algorithm=source_row["fingerprint_algorithm"],
                digest=source_row["fingerprint_digest"],
                size_bytes=source_row["size_bytes"],
            )
        generations = tuple(
            GenerationState(
                generation_id=GenerationId.parse(row["generation_id"]),
                status=GenerationStatus.parse(row["status"]),
                baseline_hash=row["baseline_hash"],
            )
            for row in connection.execute(
                "SELECT * FROM generations WHERE project_id = ? ORDER BY rowid",
                (self.project_id.value,),
            )
        )
        artifacts = tuple(
            ArtifactRecord(
                artifact_id=ArtifactId.parse(row["artifact_id"]),
                project_id=self.project_id,
                generation_id=GenerationId.parse(row["generation_id"]),
                source_id=SourceId.parse(row["source_id"]),
                role=ArtifactRole.parse(row["role"]),
                content_hash=row["content_sha256"],
                parent_ids=tuple(
                    ArtifactId.parse(item) for item in json.loads(row["parent_ids_json"])
                ),
                recorded_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in connection.execute(
                "SELECT * FROM artifacts WHERE project_id = ? ORDER BY rowid",
                (self.project_id.value,),
            )
        )
        approvals = tuple(
            ApprovalRecord(
                approval_id=EventId.parse(row["approval_id"]),
                approval_type=ApprovalType.parse(row["scope"]),
                decision=ApprovalDecision.parse(row["decision"]),
                actor=self._actor_from_row(row),
                target=ApprovalTarget(
                    generation_id=(
                        GenerationId.parse(row["generation_id"])
                        if row["generation_id"] is not None
                        else None
                    ),
                    content_hash=row["target_sha256"],
                ),
                decided_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in connection.execute(
                "SELECT * FROM approvals WHERE project_id = ? ORDER BY rowid",
                (self.project_id.value,),
            )
        )
        failures = tuple(
            FailureRecord(
                failure_id=EventId.parse(row["failure_id"]),
                objective=row["failure_code"],
                failure_fingerprint=row["fingerprint"],
                evidence_refs=tuple(json.loads(row["evidence_refs_json"])),
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
            )
            for row in connection.execute(
                "SELECT * FROM failures WHERE project_id = ? ORDER BY rowid",
                (self.project_id.value,),
            )
        )
        processed = tuple(
            ProcessedCommand(
                command_id=CommandId.parse(row["command_id"]),
                request_digest=row["request_digest"],
            )
            for row in connection.execute(
                "SELECT command_id, request_digest FROM workflow_events "
                "WHERE project_id = ? ORDER BY state_version",
                (self.project_id.value,),
            )
        )
        state = ProjectState(
            project_id=self.project_id,
            phase=Phase.parse(project["current_phase"]),
            lifecycle=LifecycleStatus.parse(project["lifecycle_status"]),
            source_id=source_id,
            source_fingerprint=fingerprint,
            generations=generations,
            artifacts=artifacts,
            approvals=approvals,
            failures=failures,
            processed_commands=processed,
        )
        return StoredState(
            state=state,
            state_version=project["state_version"],
            last_event_id=project["last_event_id"],
        )

    @staticmethod
    def _actor_from_row(row: sqlite3.Row) -> Actor:
        kind = ActorKind.parse(row["actor_kind"])
        provenance: ActorProvenance | None = None
        if kind is ActorKind.HUMAN:
            provenance = ActorProvenance(
                channel=row["provenance_type"] or "unknown",
                session_id=row["provenance_session"] or "unknown",
                decided_at=datetime.fromisoformat(row["created_at"]),
            )
        return Actor(kind=kind, actor_id=row["actor_id"], provenance=provenance)

    # -- commit -------------------------------------------------------------

    def commit_transition(
        self,
        expected_version: int,
        command: Command,
        accepted: TransitionAccepted,
        extras: CommitExtras | None = None,
    ) -> CommitReceipt:
        extras = extras or CommitExtras()
        connection = self._connect()
        try:
            self._check_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            try:
                current = self._load_with(connection)
                if current.state_version != expected_version:
                    raise ConcurrencyConflictError(
                        f"expected state_version {expected_version}, "
                        f"found {current.state_version}; reload and retry explicitly"
                    )
                new_version = expected_version + len(accepted.events)
                event_ids = self._insert_events(
                    connection, current, accepted, command, expected_version, extras
                )
                self._apply_records(connection, current.state, accepted, command, extras)
                connection.execute(
                    "UPDATE projects SET source_id = ?, lifecycle_status = ?, "
                    "current_phase = ?, state_version = ?, updated_at = ?, "
                    "last_event_id = ? WHERE project_id = ?",
                    (
                        accepted.state.source_id.value if accepted.state.source_id else None,
                        accepted.state.lifecycle.value,
                        accepted.state.phase.value,
                        new_version,
                        _utc_now_iso(),
                        event_ids[-1] if event_ids else current.last_event_id,
                        self.project_id.value,
                    ),
                )
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            return CommitReceipt(state_version=new_version, event_ids=event_ids)
        finally:
            connection.close()

    def _insert_events(
        self,
        connection: sqlite3.Connection,
        current: StoredState,
        accepted: TransitionAccepted,
        command: Command,
        expected_version: int,
        extras: CommitExtras,
    ) -> tuple[str, ...]:
        from video_workflow.domain import command_digest

        event_ids: list[str] = []
        version = expected_version
        for event in accepted.events:
            version += 1
            payload = json.dumps(
                serialize(event),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            connection.execute(
                "INSERT INTO workflow_events (event_id, command_id, request_digest, "
                "project_id, event_type, prev_lifecycle, next_lifecycle, prev_phase, "
                "next_phase, state_version, actor_kind, actor_id, reason, "
                "payload_json, occurred_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id.value,
                    command.command_id.value,
                    command_digest(command),
                    self.project_id.value,
                    event.kind.value,
                    current.state.lifecycle.value,
                    accepted.state.lifecycle.value,
                    current.state.phase.value,
                    accepted.state.phase.value,
                    version,
                    event.actor.kind.value,
                    event.actor.actor_id,
                    extras.reason,
                    payload,
                    event.occurred_at.isoformat(),
                ),
            )
            event_ids.append(event.event_id.value)
        return tuple(event_ids)

    def _apply_records(
        self,
        connection: sqlite3.Connection,
        old_state: ProjectState,
        accepted: TransitionAccepted,
        command: Command,
        extras: CommitExtras,
    ) -> None:
        new_state = accepted.state
        if isinstance(command, RegisterSource) and old_state.source_id is None:
            connection.execute(
                "INSERT INTO sources (source_id, project_id, fingerprint_algorithm, "
                "fingerprint_digest, size_bytes, locator, registered_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    command.source_id.value,
                    self.project_id.value,
                    command.fingerprint.algorithm,
                    command.fingerprint.digest,
                    command.fingerprint.size_bytes,
                    extras.source_locator or "unspecified",
                    command.occurred_at.isoformat(),
                ),
            )
        old_generations = {
            generation.generation_id: generation for generation in old_state.generations
        }
        for generation in new_state.generations:
            existing = old_generations.get(generation.generation_id)
            if existing is None:
                connection.execute(
                    "INSERT INTO generations (generation_id, project_id, status, "
                    "baseline_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        generation.generation_id.value,
                        self.project_id.value,
                        generation.status.value,
                        generation.baseline_hash,
                        command.occurred_at.isoformat(),
                    ),
                )
            elif existing != generation:
                connection.execute(
                    "UPDATE generations SET status = ?, baseline_hash = ?, "
                    "closed_at = ? WHERE generation_id = ?",
                    (
                        generation.status.value,
                        generation.baseline_hash,
                        command.occurred_at.isoformat(),
                        generation.generation_id.value,
                    ),
                )
        if isinstance(command, RecordArtifact) and len(new_state.artifacts) > len(
            old_state.artifacts
        ):
            record = new_state.artifacts[-1]
            connection.execute(
                "INSERT INTO artifacts (artifact_id, project_id, source_id, "
                "generation_id, role, relative_path, content_sha256, size_bytes, "
                "tool_version, parent_ids_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.artifact_id.value,
                    self.project_id.value,
                    record.source_id.value,
                    record.generation_id.value,
                    record.role.value,
                    extras.artifact_relative_path,
                    record.content_hash,
                    extras.artifact_size_bytes,
                    extras.artifact_tool_version,
                    json.dumps([parent.value for parent in record.parent_ids]),
                    record.recorded_at.isoformat(),
                ),
            )
        if isinstance(command, RecordApproval) and len(new_state.approvals) > len(
            old_state.approvals
        ):
            record_a = new_state.approvals[-1]
            approval_extras = extras.approval
            connection.execute(
                "INSERT INTO approvals (approval_id, project_id, generation_id, "
                "scope, decision, actor_kind, actor_id, provenance_type, "
                "provenance_session, request_id, evidence_id, target_sha256, "
                "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record_a.approval_id.value,
                    self.project_id.value,
                    record_a.target.generation_id.value if record_a.target.generation_id else None,
                    record_a.approval_type.value,
                    record_a.decision.value,
                    record_a.actor.kind.value,
                    record_a.actor.actor_id,
                    approval_extras.provenance_type if approval_extras else None,
                    record_a.actor.provenance.session_id if record_a.actor.provenance else None,
                    approval_extras.request_id if approval_extras else None,
                    approval_extras.evidence_id if approval_extras else None,
                    record_a.target.content_hash,
                    record_a.decided_at.isoformat(),
                ),
            )
        if isinstance(command, RecordFailure) and len(new_state.failures) > len(old_state.failures):
            record_f = new_state.failures[-1]
            connection.execute(
                "INSERT INTO failures (failure_id, project_id, phase, failure_code, "
                "fingerprint, message, tool, evidence_refs_json, occurred_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record_f.failure_id.value,
                    self.project_id.value,
                    old_state.phase.value,
                    record_f.objective,
                    record_f.failure_fingerprint,
                    extras.failure_message or record_f.objective,
                    extras.failure_tool,
                    json.dumps(list(record_f.evidence_refs)),
                    record_f.occurred_at.isoformat(),
                ),
            )

    # -- approval requests (trust boundary bookkeeping) ---------------------

    def create_approval_request(
        self,
        request_id: str,
        scope: str,
        challenge: str,
        generation_id: str | None,
        artifact_id: str | None,
        target_sha256: str | None,
    ) -> None:
        connection = self._connect()
        try:
            self._check_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO approval_requests (request_id, project_id, "
                    "generation_id, scope, artifact_id, target_sha256, challenge, "
                    "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        request_id,
                        self.project_id.value,
                        generation_id,
                        scope,
                        artifact_id,
                        target_sha256,
                        challenge,
                        _utc_now_iso(),
                    ),
                )
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
        finally:
            connection.close()

    def load_approval_request(self, request_id: str) -> sqlite3.Row | None:
        connection = self._connect()
        try:
            self._check_schema(connection)
            row = connection.execute(
                "SELECT * FROM approval_requests WHERE request_id = ? AND project_id = ?",
                (request_id, self.project_id.value),
            ).fetchone()
            return cast(sqlite3.Row | None, row)
        finally:
            connection.close()

    def consume_approval_request(self, request_id: str) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                updated = connection.execute(
                    "UPDATE approval_requests SET status = 'consumed' "
                    "WHERE request_id = ? AND status = 'pending'",
                    (request_id,),
                ).rowcount
                if updated != 1:
                    raise CorruptionError("approval request missing or already consumed")
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
        finally:
            connection.close()

    # -- verify -------------------------------------------------------------

    def verify(self) -> VerifyReport:
        issues: list[VerifyIssue] = []
        checked: list[str] = []
        connection = self._connect()
        try:
            try:
                self._check_schema(connection)
                checked.append("schema")
            except (CorruptionError, FutureSchemaError, MigrationError) as exc:
                return VerifyReport(
                    ok=False,
                    issues=(VerifyIssue("schema", str(exc)),),
                    checked=("schema",),
                )
            project = connection.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (self.project_id.value,),
            ).fetchone()
            if project is None:
                return VerifyReport(
                    ok=False,
                    issues=(VerifyIssue("projects", "project row missing"),),
                    checked=tuple(checked),
                )
            events = connection.execute(
                "SELECT * FROM workflow_events WHERE project_id = ? ORDER BY state_version",
                (self.project_id.value,),
            ).fetchall()
            checked.append("event_chain")
            expected_version = 0
            previous = None
            seen_commands: dict[str, str] = {}
            for event in events:
                expected_version += 1
                if event["state_version"] != expected_version:
                    issues.append(
                        VerifyIssue(
                            "event_chain",
                            f"event {event['event_id']} has state_version "
                            f"{event['state_version']}, expected {expected_version}",
                        )
                    )
                if previous is not None and (
                    event["prev_lifecycle"] != previous["next_lifecycle"]
                    or event["prev_phase"] != previous["next_phase"]
                ):
                    issues.append(
                        VerifyIssue(
                            "event_chain",
                            f"event {event['event_id']} does not chain from {previous['event_id']}",
                        )
                    )
                digest = seen_commands.get(event["command_id"])
                if digest is not None and digest != event["request_digest"]:
                    issues.append(
                        VerifyIssue(
                            "command_ids",
                            f"command {event['command_id']} reused with a different request digest",
                        )
                    )
                seen_commands[event["command_id"]] = event["request_digest"]
                previous = event
            checked.append("snapshot")
            if events:
                last = events[-1]
                if (
                    project["lifecycle_status"] != last["next_lifecycle"]
                    or project["current_phase"] != last["next_phase"]
                    or project["last_event_id"] != last["event_id"]
                    or project["state_version"] != last["state_version"]
                ):
                    issues.append(
                        VerifyIssue(
                            "snapshot",
                            "projects snapshot does not match the last event; no automatic repair",
                        )
                    )
            elif project["state_version"] != 0:
                issues.append(VerifyIssue("snapshot", "state_version > 0 without events"))
            checked.append("approvals")
            for row in connection.execute(
                "SELECT * FROM approvals WHERE project_id = ?",
                (self.project_id.value,),
            ):
                if row["generation_id"] is not None:
                    generation = connection.execute(
                        "SELECT status, baseline_hash FROM generations WHERE generation_id = ?",
                        (row["generation_id"],),
                    ).fetchone()
                    if generation is None:
                        issues.append(
                            VerifyIssue(
                                "approvals",
                                f"approval {row['approval_id']} targets a missing generation",
                            )
                        )
                    elif (
                        row["target_sha256"] is not None
                        and generation["baseline_hash"] is not None
                        and row["target_sha256"] != generation["baseline_hash"]
                    ):
                        issues.append(
                            VerifyIssue(
                                "approvals",
                                f"approval {row['approval_id']} hash no longer "
                                "matches its generation baseline",
                            )
                        )
            checked.append("artifact_files")
            for row in connection.execute(
                "SELECT * FROM artifacts WHERE project_id = ? AND relative_path IS NOT NULL",
                (self.project_id.value,),
            ):
                path = self.project_dir / row["relative_path"]
                if not path.is_file():
                    issues.append(
                        VerifyIssue(
                            "artifact_files",
                            f"artifact {row['artifact_id']} file missing: {row['relative_path']}",
                        )
                    )
                    continue
                digest_value = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest_value != row["content_sha256"]:
                    issues.append(
                        VerifyIssue(
                            "artifact_files",
                            f"artifact {row['artifact_id']} content hash mismatch",
                        )
                    )
            checked.append("source_fingerprint")
            for row in connection.execute(
                "SELECT * FROM sources WHERE project_id = ?",
                (self.project_id.value,),
            ):
                locator = row["locator"]
                if locator in (None, "", "unspecified"):
                    continue
                path = self.project_dir / locator
                if path.is_file():
                    digest_value = hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest_value != row["fingerprint_digest"]:
                        issues.append(
                            VerifyIssue(
                                "source_fingerprint",
                                f"source {row['source_id']} fingerprint drift",
                            )
                        )
            checked.append("generated_views")
            status_path = self.project_dir / "generated" / "status.json"
            if status_path.is_file():
                try:
                    generated = json.loads(status_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    issues.append(VerifyIssue("generated_views", "status.json unreadable"))
                else:
                    if generated.get("state_version") != project["state_version"]:
                        issues.append(
                            VerifyIssue(
                                "generated_views",
                                "generated status.json is stale "
                                "(state_version mismatch); regenerate via export",
                            )
                        )
        finally:
            connection.close()
        return VerifyReport(ok=not issues, issues=tuple(issues), checked=tuple(checked))
