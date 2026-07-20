"""Strongly typed identifiers with strict generation and parsing rules.

Rules (stage 02 contract):
- Canonical form is ``<prefix>-<uuid4>`` with a lowercase canonical UUID4.
- Parsing rejects non-strings, wrong prefixes, uppercase, and non-v4 UUIDs.
- The domain never generates UUIDs itself; the application layer supplies
  them (``from_uuid``) so pure functions stay deterministic.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import ClassVar, Self

from video_workflow.domain.errors import DomainValidationError

_UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@dataclass(frozen=True, slots=True)
class TypedId:
    """Base class for prefixed identifiers. Do not instantiate directly."""

    value: str
    prefix: ClassVar[str] = ""

    def __post_init__(self) -> None:
        if type(self) is TypedId or not self.prefix:
            raise DomainValidationError("TypedId is abstract; use a concrete id type")
        if not isinstance(self.value, str):
            raise DomainValidationError(
                f"{type(self).__name__} requires str, got {type(self.value).__name__}"
            )
        marker = f"{self.prefix}-"
        if not self.value.startswith(marker):
            raise DomainValidationError(
                f"{type(self).__name__} must start with {marker!r}: {self.value!r}"
            )
        if _UUID4_PATTERN.match(self.value[len(marker) :]) is None:
            raise DomainValidationError(
                f"{type(self).__name__} must embed a canonical lowercase UUID4: {self.value!r}"
            )

    @classmethod
    def from_uuid(cls, value: uuid.UUID) -> Self:
        """Build an id from an externally supplied UUID (must be version 4)."""
        if not isinstance(value, uuid.UUID):
            raise DomainValidationError(
                f"{cls.__name__}.from_uuid requires uuid.UUID, got {type(value).__name__}"
            )
        if value.version != 4:
            raise DomainValidationError(f"{cls.__name__} requires a version-4 UUID")
        return cls(f"{cls.prefix}-{value}")

    @classmethod
    def parse(cls, value: object) -> Self:
        """Strictly parse external input. No implicit type conversion."""
        if not isinstance(value, str):
            raise DomainValidationError(
                f"{cls.__name__}.parse requires str, got {type(value).__name__}"
            )
        return cls(value)


@dataclass(frozen=True, slots=True)
class ProjectId(TypedId):
    prefix: ClassVar[str] = "prj"


@dataclass(frozen=True, slots=True)
class SourceId(TypedId):
    prefix: ClassVar[str] = "src"


@dataclass(frozen=True, slots=True)
class GenerationId(TypedId):
    prefix: ClassVar[str] = "gen"


@dataclass(frozen=True, slots=True)
class ArtifactId(TypedId):
    prefix: ClassVar[str] = "art"


@dataclass(frozen=True, slots=True)
class EventId(TypedId):
    prefix: ClassVar[str] = "evt"


@dataclass(frozen=True, slots=True)
class CommandId(TypedId):
    prefix: ClassVar[str] = "cmd"
