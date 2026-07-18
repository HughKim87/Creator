"""Contract and failure tests for tools/state_io.py using synthetic data only."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import state_io  # noqa: E402


def synthetic_output(
    *,
    version: int = 1,
    path: str = "outputs/sample_project/analysis.json",
    status: str = "current",
    supersedes: str | None = None,
    approval_state: str = "approved",
    approval_scope: str = "next_stage",
    next_use: str = "ineligible",
) -> dict[str, Any]:
    return {
        "role": "analysis",
        "version": version,
        "path": path,
        "source_id": "source_001",
        "status": status,
        "supersedes": supersedes,
        "integrity": {
            "algorithm": "sha256",
            "digest": "0" * 64,
            "size_bytes": 2,
        },
        "validation_level": "structure_validated",
        "approval_state": approval_state,
        "approval_scope": approval_scope,
        "next_use": next_use,
    }


def synthetic_state() -> dict[str, Any]:
    return {
        "schema_version": 3,
        "project_id": "sample_project",
        "current_stage": "analysis",
        "reference_input": {
            "source_id": "source_001",
            "path": "inputs/synthetic_샘플.mp4",
            "fingerprint": {
                "algorithm": "sha256",
                "digest": "0" * 64,
                "size_bytes": 1024,
            },
        },
        "outputs": [synthetic_output()],
        "next_action": "review_analysis",
        "blocker": None,
        "user_decision": None,
        "validation_level": "structure_validated",
    }


def write_recorded_file(
    workspace: Path,
    relative_path: str,
    record: dict[str, Any],
    integrity_key: str,
    content: bytes,
) -> Path:
    target = workspace.joinpath(*relative_path.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    record[integrity_key] = {
        "algorithm": "sha256",
        "digest": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }
    return target


def write_recorded_output(
    workspace: Path, output: dict[str, Any], content: bytes
) -> Path:
    return write_recorded_file(
        workspace, output["path"], output, "integrity", content
    )


def write_reference(
    workspace: Path, payload: dict[str, Any], content: bytes = b"synthetic video"
) -> Path:
    reference = payload["reference_input"]
    return write_recorded_file(
        workspace, reference["path"], reference, "fingerprint", content
    )


class StateIOTests(unittest.TestCase):
    def test_round_trip_preserves_synthetic_unicode_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = state_io.save_state(
                temporary_directory, "sample_project", synthetic_state()
            )
            self.assertEqual(target.name, "state.json")
            self.assertEqual(
                state_io.load_state(temporary_directory, "sample_project"),
                synthetic_state(),
            )
            raw = target.read_bytes()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))

    def test_missing_field_is_rejected_before_directory_creation(self) -> None:
        payload = synthetic_state()
        del payload["next_action"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(state_io.StateValidationError):
                state_io.save_state(temporary_directory, "sample_project", payload)
            self.assertFalse(Path(temporary_directory, "sample_project").exists())

    def test_wrong_type_and_unknown_field_are_rejected(self) -> None:
        wrong_type = synthetic_state()
        wrong_type["schema_version"] = True
        unknown_field = synthetic_state()
        unknown_field["hidden_state"] = "not_allowed"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(wrong_type)
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(unknown_field)

    def test_project_and_document_paths_cannot_escape_boundaries(self) -> None:
        with self.assertRaises(state_io.StateValidationError):
            state_io.state_path("outputs", "../escape")

        absolute_input = synthetic_state()
        absolute_input["reference_input"]["path"] = "C:/outside/video.mp4"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(absolute_input)

        dotted_input = synthetic_state()
        dotted_input["reference_input"]["path"] = "inputs/./video.mp4"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(dotted_input)

        escaped_output = synthetic_state()
        escaped_output["outputs"][0]["path"] = "outputs/other/analysis.json"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(escaped_output)

    def test_project_id_and_source_id_must_match_their_context(self) -> None:
        project_mismatch = synthetic_state()
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(project_mismatch, expected_project_id="other_project")

        source_mismatch = synthetic_state()
        source_mismatch["outputs"][0]["source_id"] = "source_002"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(source_mismatch)

    def test_interrupted_replace_preserves_prior_state_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            original = synthetic_state()
            target = state_io.save_state(
                temporary_directory, "sample_project", original
            )
            original_bytes = target.read_bytes()
            updated = copy.deepcopy(original)
            updated["current_stage"] = "review"
            updated["next_action"] = "request_user_decision"

            with patch("state_io.os.replace", side_effect=OSError("synthetic interruption")):
                with self.assertRaises(state_io.StateIOError):
                    state_io.save_state(
                        temporary_directory, "sample_project", updated
                    )

            self.assertEqual(target.read_bytes(), original_bytes)
            self.assertEqual(
                state_io.load_state(temporary_directory, "sample_project"), original
            )
            self.assertEqual(list(target.parent.glob(".state.*.tmp")), [])

    def test_invalid_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory, "sample_project", "state.json")
            target.parent.mkdir()
            target.write_text("{invalid", encoding="utf-8")
            with self.assertRaises(state_io.StateIOError):
                state_io.load_state(temporary_directory, "sample_project")

    def test_serialized_payload_contains_only_declared_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = state_io.save_state(
                temporary_directory, "sample_project", synthetic_state()
            )
            persisted = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(set(persisted), state_io._STATE_KEYS)

    def test_multiple_current_outputs_for_one_role_are_rejected(self) -> None:
        payload = synthetic_state()
        payload["outputs"].append(
            synthetic_output(
                version=2,
                path="outputs/sample_project/analysis__v002.json",
            )
        )
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(payload)

    def test_next_use_requires_current_validated_and_resolved_approval(self) -> None:
        pending = synthetic_state()
        pending["outputs"][0]["next_use"] = "eligible"
        pending["outputs"][0]["approval_state"] = "pending"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(pending)

        unvalidated = synthetic_state()
        unvalidated["outputs"][0]["next_use"] = "eligible"
        unvalidated["outputs"][0]["validation_level"] = "parsed"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(unvalidated)

    def test_approval_scope_must_match_approval_state(self) -> None:
        unnecessary_scope = synthetic_state()
        output = unnecessary_scope["outputs"][0]
        output["approval_state"] = "not_required"
        output["approval_scope"] = "next_stage"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(unnecessary_scope)

        missing_scope = synthetic_state()
        missing_scope["outputs"][0]["approval_scope"] = "none"
        with self.assertRaises(state_io.StateValidationError):
            state_io.validate_state(missing_scope)

    def test_reference_input_must_exist_and_match_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            payload = synthetic_state()
            with self.assertRaises(state_io.StateIOError):
                state_io.validate_reference_input(workspace, payload)

            target = workspace.joinpath(*payload["reference_input"]["path"].split("/"))
            target.parent.mkdir(parents=True)
            target.write_bytes(b"wrong input")
            with self.assertRaises(state_io.StateIOError):
                state_io.validate_reference_input(workspace, payload)

            write_reference(workspace, payload)
            state_io.validate_reference_input(workspace, payload)

    def test_missing_eligible_output_and_integrity_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            payload = synthetic_state()
            payload["outputs"][0]["next_use"] = "eligible"
            with self.assertRaises(state_io.StateIOError):
                state_io.validate_output_files(workspace, payload)

            target = workspace.joinpath(*payload["outputs"][0]["path"].split("/"))
            target.parent.mkdir(parents=True)
            target.write_bytes(b"wrong content")
            with self.assertRaises(state_io.StateIOError):
                state_io.validate_output_files(workspace, payload)

    def test_validation_scopes_avoid_unrelated_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            payload = synthetic_state()
            prior = payload["outputs"][0]
            prior["path"] = "outputs/sample_project/analysis__v001.json"
            prior["status"] = "superseded"
            current = synthetic_output(
                version=2,
                path="outputs/sample_project/analysis__v002.json",
                supersedes=prior["path"],
                next_use="eligible",
            )
            failed = synthetic_output(
                version=3,
                path="outputs/sample_project/analysis__v003_failed.json",
                status="failed",
                approval_state="revision_requested",
            )
            payload["outputs"].extend([current, failed])
            write_recorded_output(workspace, prior, b"prior")
            write_recorded_output(workspace, current, b"current")

            state_io.validate_output_files(workspace, payload, scope="eligible")
            state_io.validate_output_files(workspace, payload, scope="promotion")
            with self.assertRaises(state_io.StateIOError):
                state_io.validate_output_files(workspace, payload, scope="all")
            with self.assertRaises(state_io.StateValidationError):
                state_io.validate_output_files(workspace, payload, scope="unknown")

    def test_eligible_state_requires_verified_promotion_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            payload = synthetic_state()
            payload["outputs"][0]["next_use"] = "eligible"

            with self.assertRaises(state_io.StateValidationError):
                state_io.save_state(workspace / "outputs", "sample_project", payload)
            with self.assertRaises(state_io.StateIOError):
                state_io.save_promoted_state(
                    workspace, workspace / "outputs", "sample_project", payload
                )

            write_reference(workspace, payload)
            write_recorded_output(workspace, payload["outputs"][0], b"current")
            target = state_io.save_promoted_state(
                workspace, workspace / "outputs", "sample_project", payload
            )
            self.assertEqual(target, workspace / "outputs/sample_project/state.json")
            self.assertEqual(
                state_io.load_state(workspace / "outputs", "sample_project"), payload
            )

            with self.assertRaises(state_io.StateValidationError):
                state_io.save_promoted_state(
                    workspace, workspace / "elsewhere", "sample_project", payload
                )

    def test_superseded_and_failed_files_are_preserved_with_current_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            payload = synthetic_state()
            prior = payload["outputs"][0]
            prior["path"] = "outputs/sample_project/analysis__v001.json"
            prior["status"] = "superseded"
            current = synthetic_output(
                version=2,
                path="outputs/sample_project/analysis__v002.json",
                supersedes=prior["path"],
                next_use="eligible",
            )
            failed = synthetic_output(
                version=3,
                path="outputs/sample_project/analysis__v003_failed.json",
                status="failed",
                approval_state="revision_requested",
            )
            payload["outputs"].extend([current, failed])
            prior_path = write_recorded_output(workspace, prior, b"prior")
            current_path = write_recorded_output(workspace, current, b"current")
            failed_path = write_recorded_output(workspace, failed, b"failed")
            write_reference(workspace, payload)

            state_io.validate_output_files(workspace, payload, scope="all")
            state_io.save_promoted_state(
                workspace, workspace / "outputs", "sample_project", payload
            )
            loaded = state_io.load_state(workspace / "outputs", "sample_project")

            self.assertEqual(len(loaded["outputs"]), 3)
            self.assertEqual(loaded["outputs"][1]["supersedes"], prior["path"])
            self.assertTrue(prior_path.exists())
            self.assertTrue(current_path.exists())
            self.assertTrue(failed_path.exists())


if __name__ == "__main__":
    unittest.main()
