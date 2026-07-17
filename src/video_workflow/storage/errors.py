"""Storage-layer errors (fail-closed).

Every abnormal condition is a typed error; nothing degrades to a warning or
silently creates/repairs state.
"""

from __future__ import annotations


class StorageError(RuntimeError):
    """Base class for storage failures."""


class WorkspaceError(StorageError):
    """Workspace path is unusable (missing, network share, not a directory)."""


class DatabaseMissingError(StorageError):
    """Read command was issued but the project database does not exist."""


class DatabaseExistsError(StorageError):
    """`init` refused to overwrite an existing project database."""


class MigrationError(StorageError):
    """Migration could not be applied safely; the previous DB stays usable."""


class FutureSchemaError(StorageError):
    """Database schema is newer than this application understands."""


class CorruptionError(StorageError):
    """Integrity check failed; no automatic repair is attempted."""


class ConcurrencyConflictError(StorageError):
    """Another writer committed first (state_version mismatch)."""


class ApprovalTrustError(StorageError):
    """Human-approval trust boundary violated (challenge, evidence, actor)."""
