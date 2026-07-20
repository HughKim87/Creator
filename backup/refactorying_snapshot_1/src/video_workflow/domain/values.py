"""Value objects: source fingerprint, actor provenance, UTC time rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from video_workflow.domain.enums import ActorKind
from video_workflow.domain.errors import DomainValidationError

SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def require_sha256_hex(value: object, field: str) -> str:
    """Validate a lowercase 64-char SHA-256 hex digest. No coercion."""
    if not isinstance(value, str):
        raise DomainValidationError(f"{field} requires str, got {type(value).__name__}")
    if SHA256_HEX_PATTERN.match(value) is None:
        raise DomainValidationError(f"{field} must be 64 lowercase hex chars")
    return value


def require_utc(value: object, field: str) -> datetime:
    """Require a timezone-aware UTC datetime. Naive datetimes are rejected."""
    if not isinstance(value, datetime):
        raise DomainValidationError(f"{field} requires datetime, got {type(value).__name__}")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise DomainValidationError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def require_non_empty_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise DomainValidationError(f"{field} requires str, got {type(value).__name__}")
    if not value.strip():
        raise DomainValidationError(f"{field} must be non-empty")
    return value


def require_strict_int(value: object, field: str) -> int:
    """Reject bools and numeric strings; only real ints pass."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise DomainValidationError(f"{field} requires int, got {type(value).__name__}")
    return value


@dataclass(frozen=True, slots=True)
class SourceFingerprint:
    """Content identity of one input source.

    Invariant: one fingerprint maps to exactly one ``source_id`` and a
    ``source_id`` never accepts a second fingerprint (enforced in
    transitions).
    """

    algorithm: str
    digest: str
    size_bytes: int

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise DomainValidationError("SourceFingerprint.algorithm must be 'sha256'")
        require_sha256_hex(self.digest, "SourceFingerprint.digest")
        if require_strict_int(self.size_bytes, "SourceFingerprint.size_bytes") < 0:
            raise DomainValidationError("SourceFingerprint.size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class ActorProvenance:
    """Provenance evidence for a human decision.

    The domain cannot cryptographically prove identity; it enforces that
    human approvals always carry a verified input channel, session, and
    decision time so an automation actor cannot impersonate a human by
    flipping a single string (structural requirement + transition rules).
    """

    channel: str
    session_id: str
    decided_at: datetime

    def __post_init__(self) -> None:
        require_non_empty_str(self.channel, "ActorProvenance.channel")
        require_non_empty_str(self.session_id, "ActorProvenance.session_id")
        require_utc(self.decided_at, "ActorProvenance.decided_at")


@dataclass(frozen=True, slots=True)
class Actor:
    """The acting party for a command or event."""

    kind: ActorKind
    actor_id: str
    provenance: ActorProvenance | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ActorKind):
            raise DomainValidationError("Actor.kind must be an ActorKind")
        require_non_empty_str(self.actor_id, "Actor.actor_id")
        if self.kind is ActorKind.HUMAN and self.provenance is None:
            raise DomainValidationError("human actors require provenance")
        if self.provenance is not None and not isinstance(self.provenance, ActorProvenance):
            raise DomainValidationError("Actor.provenance must be ActorProvenance")
