"""Storage port (frozen before implementation, stage 03 task 03-1).

The domain layer never imports this module; the service layer depends on
this interface and the SQLite implementation fulfils it. SQLite details must
not leak into domain types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from video_workflow.domain import Command, ProjectState, TransitionAccepted


@dataclass(frozen=True, slots=True)
class StoredState:
    """A loaded snapshot: domain state plus optimistic-concurrency metadata."""

    state: ProjectState
    state_version: int
    last_event_id: str | None


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    """Result of a successfully committed transition."""

    state_version: int
    event_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApprovalProvenanceExtras:
    """Trust-boundary metadata for human approvals (storage-only, non-domain)."""

    provenance_type: str
    request_id: str | None
    evidence_id: str | None


@dataclass(frozen=True, slots=True)
class CommitExtras:
    """Storage-only metadata that accompanies specific commands.

    These values are not part of the pure domain contract (paths, locators,
    reasons, provenance evidence) but must be persisted with the transition.
    """

    reason: str | None = None
    source_locator: str | None = None
    artifact_relative_path: str | None = None
    artifact_size_bytes: int | None = None
    artifact_tool_version: str | None = None
    failure_message: str | None = None
    failure_tool: str | None = None
    approval: ApprovalProvenanceExtras | None = None


@dataclass(frozen=True, slots=True)
class VerifyIssue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class VerifyReport:
    ok: bool
    issues: tuple[VerifyIssue, ...]
    checked: tuple[str, ...]


class StateStore(Protocol):
    """Single source of persistent truth for one project."""

    def load(self) -> StoredState:
        """Load current state. Raises DatabaseMissingError if absent."""
        ...

    def commit_transition(
        self,
        expected_version: int,
        command: Command,
        accepted: TransitionAccepted,
        extras: CommitExtras | None = None,
    ) -> CommitReceipt:
        """Atomically append events and update the snapshot.

        Raises ConcurrencyConflictError when expected_version no longer
        matches; the database is left unchanged on any failure.
        """
        ...

    def verify(self) -> VerifyReport:
        """Run integrity checks without modifying anything."""
        ...
