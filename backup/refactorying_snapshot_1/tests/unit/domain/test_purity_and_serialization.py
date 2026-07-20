"""Domain purity (no I/O imports) and fail-closed serialization policy."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import video_workflow.domain as domain_package
from tests.support.domain_factories import Driver
from video_workflow.domain import (
    SCHEMA_VERSION,
    SerializationError,
    canonical_json_bytes,
    deserialize,
    serialize,
)

FORBIDDEN_IMPORTS = {
    "os",
    "sys",
    "pathlib",
    "sqlite3",
    "subprocess",
    "shutil",
    "tempfile",
    "socket",
    "random",
    "secrets",
    "time",
    "io",
    "urllib",
    "http",
}


def _domain_modules() -> list[Path]:
    package_dir = Path(domain_package.__file__).parent
    return sorted(package_dir.glob("*.py"))


def test_domain_modules_exist() -> None:
    names = {path.name for path in _domain_modules()}
    assert "transitions.py" in names and "serialization.py" in names


def test_domain_imports_no_io_facilities() -> None:
    offences: list[str] = []
    for path in _domain_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = [node.module]
            for name in names:
                root = name.split(".")[0]
                if root in FORBIDDEN_IMPORTS:
                    offences.append(f"{path.name}: {name}")
                if root == "video_workflow" and not name.startswith("video_workflow.domain"):
                    offences.append(f"{path.name}: {name} (outside domain)")
    assert offences == []


def _sample_state_envelope() -> dict[str, object]:
    driver = Driver()
    driver.to_delivery()
    envelope = serialize(driver.state)
    assert isinstance(envelope, dict)
    return envelope


def test_round_trip_is_byte_identical() -> None:
    driver = Driver()
    driver.to_delivery()
    original = canonical_json_bytes(driver.state)
    restored = deserialize(json.loads(original))
    assert canonical_json_bytes(restored) == original  # type: ignore[arg-type]


def test_serialization_is_deterministic_across_runs() -> None:
    first = Driver()
    first.to_delivery()
    second = Driver()
    second.to_delivery()
    assert canonical_json_bytes(first.state) == canonical_json_bytes(second.state)


def test_unknown_future_schema_version_fails_closed() -> None:
    envelope = _sample_state_envelope()
    envelope["schema_version"] = SCHEMA_VERSION + 1
    with pytest.raises(SerializationError):
        deserialize(envelope)


def test_missing_schema_version_fails_closed() -> None:
    envelope = _sample_state_envelope()
    del envelope["schema_version"]
    with pytest.raises(SerializationError):
        deserialize(envelope)


def test_unknown_field_is_rejected_not_dropped() -> None:
    envelope = _sample_state_envelope()
    data = envelope["data"]
    assert isinstance(data, dict)
    data["surprise_field"] = "x"
    with pytest.raises(SerializationError):
        deserialize(envelope)


def test_unknown_kind_is_rejected() -> None:
    envelope = _sample_state_envelope()
    envelope["kind"] = "MysteryRecord"
    with pytest.raises(SerializationError):
        deserialize(envelope)


def test_naive_datetime_is_rejected() -> None:
    envelope = _sample_state_envelope()
    data = envelope["data"]
    assert isinstance(data, dict)
    approvals = data["approvals"]
    assert isinstance(approvals, list) and approvals
    approval = approvals[0]
    assert isinstance(approval, dict)
    approval_data = approval["data"]
    assert isinstance(approval_data, dict)
    approval_data["decided_at"] = "2026-07-17T05:00:00"  # no offset
    with pytest.raises(SerializationError):
        deserialize(envelope)


def test_payload_never_contains_source_content() -> None:
    """Events carry hashes and ids only; there is no field for raw content."""
    driver = Driver()
    driver.to_delivery()
    envelope = serialize(driver.state)
    text = json.dumps(envelope, ensure_ascii=False)
    data = envelope["data"]
    assert isinstance(data, dict)
    artifact_envelopes = data["artifacts"]
    assert isinstance(artifact_envelopes, list)
    for artifact in artifact_envelopes:
        assert isinstance(artifact, dict)
        artifact_data = artifact["data"]
        assert isinstance(artifact_data, dict)
        assert set(artifact_data) <= {
            "artifact_id",
            "project_id",
            "generation_id",
            "source_id",
            "role",
            "content_hash",
            "parent_ids",
            "recorded_at",
        }
    assert len(text) < 100_000
