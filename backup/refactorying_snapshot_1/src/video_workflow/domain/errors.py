"""Domain contract errors.

The domain layer is pure: no filesystem, no database, no subprocess, no clock.
Every constraint violation raises one of these types instead of silently
coercing or truncating values (fail-closed).
"""

from __future__ import annotations


class DomainValidationError(ValueError):
    """A domain value or record violates its contract."""


class SerializationError(ValueError):
    """A serialized payload cannot be accepted under the fixed schema policy."""
