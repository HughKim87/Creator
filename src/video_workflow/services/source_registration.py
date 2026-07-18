"""Source registration service (stage 04 task 04-2).

Coordinates fingerprinting, media probing, and the domain registration as
one logical operation: if the file changes while being registered, the
command fails and no partial record remains (the domain commit is a single
transaction; nothing is written before it).

Identity and hash rules live in the domain (`SourceFingerprint`, one
fingerprint per source id); file reading and FFprobe live in adapters.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from video_workflow.adapters.media_probe import MediaInfo, MediaProbe, MediaProbeError
from video_workflow.domain import SourceFingerprint
from video_workflow.services.state_service import (
    ApplyOutcome,
    StateService,
    fingerprint_file,
)

# Paths whose segments indicate temporary, backup, or output material must
# never be registered as input sources (legacy contract preserved).
FORBIDDEN_SOURCE_SEGMENTS = frozenset(
    {"outputs", "output", "temp", "tmp", "backup", "generated", "artifacts", ".staging"}
)


class SourceRegistrationError(RuntimeError):
    """Registration refused; nothing was recorded."""


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    outcome: ApplyOutcome
    fingerprint: SourceFingerprint
    media: MediaInfo


def _segments_for_check(path: Path) -> tuple[str, ...]:
    """Path segments relevant to the temp/backup/output rule.

    The OS temp root itself is stripped first: the rule targets project
    temp/output/backup directories, not the sandbox location that tests and
    isolated runs legitimately live in.
    """
    resolved = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        return resolved.relative_to(temp_root).parts
    except ValueError:
        return resolved.parts


def validate_source_path(path: Path) -> None:
    if not path.is_file():
        raise SourceRegistrationError(f"source does not exist: {path.name}")
    if path.stat().st_size == 0:
        raise SourceRegistrationError(f"source is empty (0 bytes): {path.name}")
    lowered = {segment.lower() for segment in _segments_for_check(path)}
    forbidden = lowered & FORBIDDEN_SOURCE_SEGMENTS
    if forbidden:
        raise SourceRegistrationError(
            f"temporary/backup/output paths are not registrable sources: "
            f"{sorted(forbidden)} in {path.name}"
        )


def register_source_file(
    service: StateService,
    probe: MediaProbe,
    path: Path,
    locator: str,
    reason: str | None = None,
) -> RegistrationResult:
    """Fingerprint, probe, re-fingerprint, then register in one commit."""
    validate_source_path(path)
    first = fingerprint_file(path)
    try:
        media = probe.probe(path)
    except MediaProbeError as exc:
        raise SourceRegistrationError(f"media probe failed: {exc}") from exc
    second = fingerprint_file(path)
    if first != second:
        raise SourceRegistrationError(
            "source changed while being registered; no partial record was kept"
        )
    outcome = service.register_source(first, locator=locator, reason=reason)
    return RegistrationResult(outcome=outcome, fingerprint=first, media=media)
