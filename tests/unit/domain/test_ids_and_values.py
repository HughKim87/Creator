"""Strict validation of ids, fingerprints, actors, and time rules."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest

from tests.support.domain_factories import FIXED_NOW, human_actor
from video_workflow.domain import (
    Actor,
    ActorKind,
    ActorProvenance,
    DomainValidationError,
    EventId,
    GenerationId,
    ProjectId,
    SourceFingerprint,
    SourceId,
    TypedId,
)
from video_workflow.domain.values import require_strict_int, require_utc

VALID_UUID = uuid.UUID(int=0xABCDEF0123456789ABCDEF, version=4)


def test_id_round_trip_and_prefix() -> None:
    project = ProjectId.from_uuid(VALID_UUID)
    assert project.value.startswith("prj-")
    assert ProjectId.parse(project.value) == project


def test_id_rejects_wrong_prefix() -> None:
    source = SourceId.from_uuid(VALID_UUID)
    with pytest.raises(DomainValidationError):
        ProjectId.parse(source.value)


@pytest.mark.parametrize(
    "bad",
    [
        123,
        None,
        b"prj-bytes",
        "prj-not-a-uuid",
        "prj-",
        "PRJ-" + str(VALID_UUID),
        "prj-" + str(VALID_UUID).upper(),
    ],
)
def test_id_rejects_invalid_input(bad: object) -> None:
    with pytest.raises(DomainValidationError):
        ProjectId.parse(bad)


def test_id_rejects_non_v4_uuid() -> None:
    v1 = uuid.uuid1()
    with pytest.raises(DomainValidationError):
        EventId.from_uuid(v1)


def test_abstract_id_cannot_instantiate() -> None:
    with pytest.raises(DomainValidationError):
        TypedId("prj-" + str(VALID_UUID))


def test_fingerprint_valid() -> None:
    fingerprint = SourceFingerprint("sha256", "0" * 64, 0)
    assert fingerprint.digest == "0" * 64


@pytest.mark.parametrize(
    ("algorithm", "digest", "size"),
    [
        ("md5", "0" * 64, 1),
        ("sha256", "0" * 63, 1),
        ("sha256", "Z" * 64, 1),
        ("sha256", "0" * 64, -1),
        ("sha256", "0" * 64, "100"),  # implicit numeric string conversion refused
        ("sha256", "0" * 64, True),  # bool is not an int here
        ("sha256", 0, 1),
    ],
)
def test_fingerprint_rejects_invalid(algorithm: str, digest: object, size: object) -> None:
    with pytest.raises(DomainValidationError):
        SourceFingerprint(algorithm, digest, size)  # type: ignore[arg-type]


def test_require_strict_int_rejects_bool_and_str() -> None:
    with pytest.raises(DomainValidationError):
        require_strict_int(True, "field")
    with pytest.raises(DomainValidationError):
        require_strict_int("3", "field")
    assert require_strict_int(3, "field") == 3


def test_require_utc_rejects_naive_and_offset() -> None:
    with pytest.raises(DomainValidationError):
        require_utc(datetime(2026, 7, 17, 5, 0, 0), "field")
    with pytest.raises(DomainValidationError):
        require_utc(
            datetime(2026, 7, 17, 5, 0, 0, tzinfo=timezone(timedelta(hours=9))),
            "field",
        )
    assert require_utc(datetime(2026, 7, 17, 5, 0, 0, tzinfo=UTC), "field")


def test_human_actor_requires_provenance() -> None:
    with pytest.raises(DomainValidationError):
        Actor(kind=ActorKind.HUMAN, actor_id="user", provenance=None)
    assert human_actor().provenance is not None


def test_provenance_requires_fields() -> None:
    with pytest.raises(DomainValidationError):
        ActorProvenance(channel=" ", session_id="s", decided_at=FIXED_NOW)
    with pytest.raises(DomainValidationError):
        ActorProvenance(channel="chat", session_id="", decided_at=FIXED_NOW)


def test_generation_id_distinct_from_event_id() -> None:
    generation = GenerationId.from_uuid(VALID_UUID)
    event = EventId.from_uuid(VALID_UUID)
    assert generation.value != event.value
