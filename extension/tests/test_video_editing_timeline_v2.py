from __future__ import annotations
from editorial_test_support import synthetic_state

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]

from video_editing import (  # noqa: E402
    TimelineV2Error,
    delivery_fingerprint,
    editorial_fingerprint,
    inspect_timeline_v2,
    migrate_legacy_v1,
    payload_fingerprint,
    task_payload_fingerprint,
    validate_timeline_v2,
    write_validated_premiere_xml,
)
from video_editing import __all__ as public_api  # noqa: E402
import video_editing.delivery as delivery_module  # noqa: E402
from video_editing.premiere_xml import PremiereXmlError  # noqa: E402
from video_editing.timeline_v2 import (  # noqa: E402
    APPROVAL_FIELDS,
    CALIBRATION_FIELDS,
    DECISION_FIELDS,
    DELIVERY_FIELDS,
    EDITORIAL_EVIDENCE_FIELDS,
    EVENT_FIELDS,
    FEEDBACK_FIELDS,
    MICROBEAT_FIELDS,
    REVISION_FIELDS,
    SOURCE_MANIFEST_FIELDS,
    TIMELINE_V2_FIELDS,
    TIME_REFERENCE_FIELDS,
    VALIDATION_FIELDS,
    VALIDATION_PASS_FIELDS,
    source_manifest_fingerprint,
)


SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "$defs",
        "$id",
        "$ref",
        "$schema",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "description",
        "else",
        "enum",
        "if",
        "items",
        "maxItems",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "not",
        "oneOf",
        "pattern",
        "properties",
        "required",
        "then",
        "title",
        "type",
        "uniqueItems",
    }
)


def _schema_keywords(schema: object) -> set[str]:
    seen: set[str] = set()

    def visit(node: object, path: str) -> None:
        if not isinstance(node, dict):
            return
        unknown = set(node) - SUPPORTED_SCHEMA_KEYWORDS
        if unknown:
            raise AssertionError(
                f"unsupported JSON Schema keyword(s) at {path}: {sorted(unknown)}"
            )
        seen.update(node)
        for container_name in ("$defs", "properties"):
            children = node.get(container_name)
            if isinstance(children, dict):
                for name, child in children.items():
                    visit(child, f"{path}.{container_name}.{name}")
        for child_name in ("additionalProperties", "else", "if", "items", "not", "then"):
            child = node.get(child_name)
            if isinstance(child, dict):
                visit(child, f"{path}.{child_name}")
        for child_name in ("allOf", "anyOf", "oneOf"):
            children = node.get(child_name)
            if isinstance(children, list):
                for index, child in enumerate(children):
                    visit(child, f"{path}.{child_name}[{index}]")

    visit(schema, "$")
    return seen


def _powershell_schema_accepts(value: object, schema_path: Path) -> bool:
    executable = shutil.which("pwsh")
    if executable is None:
        raise AssertionError("PowerShell 7 with Test-Json is required for schema tests")
    environment = os.environ.copy()
    environment["VIDEO_EDIT_V2_SCHEMA_PATH"] = str(schema_path.resolve())
    script = (
        "$inputJson=[Console]::In.ReadToEnd();"
        "$ErrorActionPreference='Stop';"
        "try {"
        "$accepted=Test-Json -Json $inputJson "
        "-SchemaFile $env:VIDEO_EDIT_V2_SCHEMA_PATH -ErrorAction SilentlyContinue;"
        "if($accepted){[Console]::Out.Write('true')}"
        "else{[Console]::Out.Write('false')}"
        "} catch { [Console]::Error.Write($_.Exception.Message); exit 3 }"
    )
    result = subprocess.run(
        [
            executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        input=json.dumps(value, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=environment,
        check=False,
    )
    rendered = result.stdout.strip().lower()
    if result.returncode != 0 or rendered not in {"true", "false"}:
        raise AssertionError(
            "external Test-Json evaluation failed closed: "
            f"exit={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
    return rendered == "true"


class VideoEditingTimelineV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_path = (
            ROOT / "extension" / "examples" / "video-edit-timeline-v2.json"
        )
        cls.schema_path = (
            ROOT / "extension" / "schemas" / "video-edit-timeline-v2.schema.json"
        )

    def _timeline(self) -> dict:
        return json.loads(self.example_path.read_text(encoding="utf-8"))

    def _refresh_review(self, value: dict) -> None:
        value["validation"]["reviewed_editorial_fingerprint"] = editorial_fingerprint(
            value
        )

    def _codes(
        self,
        value: dict,
        *,
        purpose: str | None = "premiere_xml",
        calibration_reference: dict | None = None,
        baseline_reference: dict | None = None,
        reference_payloads: tuple[dict, ...] = (),
    ) -> set[str]:
        with self.assertRaises(TimelineV2Error) as raised:
            validate_timeline_v2(
                value,
                purpose=purpose,
                calibration_reference=calibration_reference,
                baseline_reference=baseline_reference,
                reference_payloads=reference_payloads,
            )
        return {issue["code"] for issue in raised.exception.issues}

    def _approve_revision(self, value: dict) -> dict:
        value["revision"]["status"] = "approved"
        self._refresh_review(value)
        value["approval"]["decisions"] = [
            {
                "id": "decision-1",
                "artifact_id": value["timeline_id"],
                "approved_scope": "entire_revision",
                "source_manifest_hash": source_manifest_fingerprint(
                    value["source_manifest"]
                ),
                "decision": "approved",
                "invalidated_by": [],
                "approved_by": "user",
                "checked_at": "2026-08-28T00:00:00+09:00",
                "reviewed_editorial_fingerprint": editorial_fingerprint(value),
            }
        ]
        return value

    def _approved_calibration(
        self, timeline_id: str = "synthetic-video-edit-v2"
    ) -> dict:
        value = self._timeline()
        value["timeline_id"] = timeline_id
        value["revision"]["state_owner_id"] = timeline_id
        value["delivery"]["artifact_id"] = timeline_id
        self._approve_revision(value)
        value["approval"]["calibration"] = {
            "required": True,
            "status": "approved",
            "artifact_id": timeline_id,
            "approved_payload_fingerprint": payload_fingerprint(value),
            "approved_by": "user",
            "approval_evidence": "explicit synthetic calibration approval",
            "checked_at": "2026-08-28T00:00:00+09:00",
        }
        validate_timeline_v2(value, purpose="premiere_xml")
        return value

    def _full_edit_from_calibration(self, calibration: dict) -> dict:
        value = deepcopy(calibration)
        value["timeline_id"] = "synthetic-full-edit-v2"
        value["workflow_profile"] = "new_full_edit"
        value["revision"].update(
            {
                "status": "working_candidate",
                "supersedes": calibration["timeline_id"],
                "state_owner_id": value["timeline_id"],
            }
        )
        value["approval"]["calibration"].update(
            {
                "artifact_id": calibration["timeline_id"],
                "approved_payload_fingerprint": task_payload_fingerprint(
                    calibration
                ),
            }
        )
        value["approval"]["decisions"] = []
        value["delivery"].update(
            {
                "artifact_id": value["timeline_id"],
                "output_path": "synthetic-full-edit.xml",
            }
        )
        self._refresh_review(value)
        return value

    def _approved_delta_from_baseline(self, baseline: dict) -> dict:
        value = deepcopy(baseline)
        value["timeline_id"] = "synthetic-approved-delta-v2"
        value["workflow_profile"] = "approved_delta"
        value["revision"].update(
            {
                "status": "working_candidate",
                "supersedes": baseline["timeline_id"],
                "state_owner_id": value["timeline_id"],
            }
        )
        value["editorial_evidence"]["feedback"][
            "baseline_payload_fingerprint"
        ] = task_payload_fingerprint(baseline)
        value["approval"]["decisions"] = []
        value["delivery"].update(
            {
                "artifact_id": value["timeline_id"],
                "output_path": "synthetic-approved-delta.xml",
            }
        )
        self._refresh_review(value)
        return value

    def _ready_for_temp(self, root: Path) -> tuple[dict, Path, Path]:
        source = root / "synthetic-original.mp4"
        source.write_bytes(b"synthetic-media")
        output = root / "synthetic-output.xml"
        value = self._timeline()
        value["source_manifest"]["path"] = str(source)
        value["source_manifest"]["content_sha256"] = (
            "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        )
        value["source_manifest"]["byte_size"] = source.stat().st_size
        value["delivery"]["output_path"] = str(output)
        self._refresh_review(value)
        return value, source, output

    def test_valid_payload_separates_editorial_task_and_delivery_fingerprints(self) -> None:
        value = self._timeline()
        self.assertEqual(validate_timeline_v2(value, purpose="premiere_xml"), value)
        report = inspect_timeline_v2(value, purpose="premiere_xml")
        self.assertTrue(report["ok"])
        self.assertEqual(report["payload_fingerprint"], payload_fingerprint(value))
        self.assertEqual(
            report["task_payload_fingerprint"],
            task_payload_fingerprint(value),
        )
        self.assertEqual(
            report["editorial_fingerprint"], editorial_fingerprint(value)
        )
        self.assertEqual(report["delivery_fingerprint"], delivery_fingerprint(value))

        editorial_change = deepcopy(value)
        editorial_change["sequence"]["video_clips"][0]["edit_reason"] += " changed"
        self.assertNotEqual(
            editorial_fingerprint(value), editorial_fingerprint(editorial_change)
        )
        self.assertNotEqual(
            payload_fingerprint(value), payload_fingerprint(editorial_change)
        )
        self.assertNotEqual(
            delivery_fingerprint(value), delivery_fingerprint(editorial_change)
        )
        self.assertIn("stale_semantic_review", self._codes(editorial_change))

        task_only = deepcopy(value)
        task_only["revision"]["supersedes"] = "synthetic-older-task"
        self.assertEqual(
            editorial_fingerprint(value), editorial_fingerprint(task_only)
        )
        self.assertNotEqual(payload_fingerprint(value), payload_fingerprint(task_only))
        self.assertNotEqual(
            delivery_fingerprint(value), delivery_fingerprint(task_only)
        )
        validate_timeline_v2(task_only, purpose="premiere_xml")

        delivery_only = deepcopy(value)
        delivery_only["delivery"]["output_path"] = "another-output.xml"
        self.assertEqual(
            editorial_fingerprint(value), editorial_fingerprint(delivery_only)
        )
        self.assertEqual(payload_fingerprint(value), payload_fingerprint(delivery_only))
        self.assertEqual(
            task_payload_fingerprint(value),
            task_payload_fingerprint(delivery_only),
        )
        self.assertNotEqual(
            delivery_fingerprint(value), delivery_fingerprint(delivery_only)
        )
        validate_timeline_v2(delivery_only, purpose="premiere_xml")

        validation_only = deepcopy(value)
        validation_only["validation"]["passes"]["causal_space"]["evidence"] += " detail"
        self.assertEqual(
            editorial_fingerprint(value), editorial_fingerprint(validation_only)
        )
        self.assertEqual(payload_fingerprint(value), payload_fingerprint(validation_only))
        self.assertNotEqual(
            task_payload_fingerprint(value),
            task_payload_fingerprint(validation_only),
        )
        self.assertNotEqual(
            delivery_fingerprint(value), delivery_fingerprint(validation_only)
        )

    def test_raw_time_mismatch_parse_error_and_coordinate_bounds_are_rejected(self) -> None:
        value = self._timeline()
        value["editorial_evidence"]["time_references"][0].update(
            {"raw": "banana", "unit": "frames"}
        )
        self._refresh_review(value)
        self.assertIn("time_reference_parse_error", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["time_references"][0]["start_frame"] = 613
        self._refresh_review(value)
        self.assertIn("time_reference_frame_mismatch", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["time_references"][0].update(
            {
                "raw": "1201",
                "coordinate_system": "source",
                "unit": "frames",
                "start_frame": 1201,
                "end_frame": 1201,
            }
        )
        self._refresh_review(value)
        self.assertIn("time_reference_coordinate_bounds", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["events"][0]["source_out"] = 999999999
        self._refresh_review(value)
        self.assertIn("event_source_bounds", self._codes(value))

    def test_cause_free_action_and_unknown_clip_reference_are_rejected(self) -> None:
        value = self._timeline()
        first = value["editorial_evidence"]["events"][0]
        first["role"] = "action"
        first["depends_on"] = []
        self._refresh_review(value)
        self.assertIn("missing_cause_anchor", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["events"][0]["video_clip_ids"] = ["missing"]
        self._refresh_review(value)
        self.assertIn("unknown_clip_reference", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["events"][0]["timeline_order"] = 1
        value["editorial_evidence"]["events"][1]["timeline_order"] = 2
        self._refresh_review(value)
        self.assertIn("event_order", self._codes(value))

    def test_event_and_microbeat_require_exact_clip_coverage_and_binding(self) -> None:
        value = self._timeline()
        value["sequence"]["video_clips"][0]["edit_role"] = "unclassified"
        self._refresh_review(value)
        self.assertIn("unclassified_clip", self._codes(value))

        value = self._timeline()
        second_event = value["editorial_evidence"]["events"][1]
        second_event["video_clip_ids"].append("V001")
        second_event["source_in"] = 0
        self._refresh_review(value)
        self.assertIn("event_clip_coverage", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["microbeats"][0]["video_clip_ids"] = []
        self._refresh_review(value)
        self.assertIn("microbeat_clip_coverage", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["microbeats"][1][
            "event_id"
        ] = "event-discovery"
        self._refresh_review(value)
        self.assertIn("microbeat_event_mismatch", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["microbeats"][0]["media_scope"] = "video"
        self._refresh_review(value)
        self.assertIn("microbeat_media_scope_mismatch", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["microbeats"][0]["boundary_review"] = "pending"
        self._refresh_review(value)
        self.assertIn("microbeat_review_incomplete", self._codes(value))

        value = self._timeline()
        value["editorial_evidence"]["microbeats"][0].update(
            {"source_in": 500, "source_out": 600}
        )
        self._refresh_review(value)
        self.assertIn("microbeat_envelope_mismatch", self._codes(value))

    def test_one_semantic_reviewer_and_current_payload_are_required(self) -> None:
        value = self._timeline()
        value["validation"]["passes"]["av_boundary"]["reviewer"] = "agent:other"
        self.assertIn("reviewer_mismatch", self._codes(value))

        value = self._timeline()
        value["validation"]["passes"]["tempo_repetition"]["status"] = "not_run"
        self.assertIn("semantic_gate_incomplete", self._codes(value))

    def test_three_semantic_perspectives_can_share_one_full_playback(self) -> None:
        value = self._timeline()
        shared_method = "uninterrupted normal-speed full-sequence playback run=review-1"
        shared_checked_at = "2026-08-28T00:00:00+09:00"
        evidence = {
            "causal_space": "ordered cause, action, result, and spatial transition review",
            "tempo_repetition": "pace, repetition, and functional silence review",
            "av_boundary": "full playback plus targeted A/B boundary ledger review",
        }
        for name, perspective_evidence in evidence.items():
            record = value["validation"]["passes"][name]
            record["method"] = shared_method
            record["checked_at"] = shared_checked_at
            record["evidence"] = perspective_evidence

        self.assertTrue(_powershell_schema_accepts(value, self.schema_path))
        validate_timeline_v2(value, purpose="premiere_xml")

    def test_approved_revision_needs_exact_active_user_decision(self) -> None:
        value = self._timeline()
        value["revision"]["status"] = "approved"
        self._refresh_review(value)
        self.assertIn("approval_payload_mismatch", self._codes(value))

        self._approve_revision(value)
        validate_timeline_v2(value, purpose="premiere_xml")

        value["approval"]["decisions"][0][
            "reviewed_editorial_fingerprint"
        ] = "sha256:" + "0" * 64
        self.assertIn("approval_payload_mismatch", self._codes(value))

    def test_latest_exact_user_decision_controls_rejection_conflict_and_supersession(
        self,
    ) -> None:
        approved = self._approve_revision(self._timeline())

        rejected = deepcopy(approved)
        rejected_decision = deepcopy(rejected["approval"]["decisions"][0])
        rejected_decision.update(
            {
                "id": "decision-newer-rejection",
                "decision": "rejected",
                "checked_at": "2026-08-28T00:01:00+09:00",
            }
        )
        rejected["approval"]["decisions"].append(rejected_decision)
        rejected_codes = self._codes(rejected)
        self.assertIn("user_rejected_revision", rejected_codes)
        self.assertIn("rejected_revision_state_mismatch", rejected_codes)
        rejected["revision"]["status"] = "use_prohibited"
        validate_timeline_v2(rejected)

        tied = deepcopy(approved)
        tied_decision = deepcopy(tied["approval"]["decisions"][0])
        tied_decision.update(
            {
                "id": "decision-tied-rejection",
                "decision": "rejected",
            }
        )
        tied["approval"]["decisions"].append(tied_decision)
        self.assertIn("approval_decision_conflict", self._codes(tied))

        superseded = deepcopy(approved)
        superseded_decision = deepcopy(superseded["approval"]["decisions"][0])
        superseded_decision.update(
            {
                "id": "decision-newer-supersession",
                "decision": "superseded",
                "checked_at": "2026-08-28T00:01:00+09:00",
            }
        )
        superseded["approval"]["decisions"].append(superseded_decision)
        superseded_codes = self._codes(superseded)
        self.assertIn("superseded_revision", superseded_codes)
        self.assertIn("superseded_revision_state_mismatch", superseded_codes)
        superseded["revision"]["status"] = "historical"
        validate_timeline_v2(superseded)

    def test_whole_revision_scope_and_user_owned_rejection_are_schema_runtime_invariants(
        self,
    ) -> None:
        partial = self._approve_revision(self._timeline())
        partial["approval"]["decisions"][0][
            "approved_scope"
        ] = "partial synthetic scope"
        self.assertFalse(_powershell_schema_accepts(partial, self.schema_path))
        self.assertIn("invalid_v2_fields", self._codes(partial))

        agent_rejection = self._approve_revision(self._timeline())
        agent_rejection["revision"]["status"] = "use_prohibited"
        agent_rejection["approval"]["decisions"][0].update(
            {
                "decision": "rejected",
                "approved_by": "agent:synthetic-fixture",
            }
        )
        self.assertFalse(
            _powershell_schema_accepts(agent_rejection, self.schema_path)
        )
        self.assertIn(
            "invalid_user_rejection",
            self._codes(agent_rejection, purpose=None),
        )

    def test_full_edit_requires_the_actual_approved_calibration_payload(self) -> None:
        calibration = self._approved_calibration()
        value = self._full_edit_from_calibration(calibration)

        self.assertIn("calibration_reference_required", self._codes(value))
        validate_timeline_v2(
            value,
            purpose="premiere_xml",
            calibration_reference=calibration,
        )

        wrong_reference = self._approved_calibration(
            "synthetic-other-calibration-v2"
        )
        self.assertIn(
            "unreferenced_reference_payload",
            self._codes(value, calibration_reference=wrong_reference),
        )
        wrong_identity_binding = deepcopy(value)
        wrong_identity_binding["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = task_payload_fingerprint(wrong_reference)
        self.assertIn(
            "calibration_reference_mismatch",
            self._codes(
                wrong_identity_binding,
                calibration_reference=wrong_reference,
            ),
        )

    def test_not_required_calibration_still_requires_exact_approved_reference(
        self,
    ) -> None:
        calibration = self._approved_calibration()
        value = self._full_edit_from_calibration(calibration)
        value["approval"]["calibration"].update(
            {"required": False, "status": "not_required"}
        )

        self.assertIn("calibration_reference_required", self._codes(value))
        validate_timeline_v2(
            value,
            purpose="premiere_xml",
            calibration_reference=calibration,
        )

        wrong_reference = self._approved_calibration(
            "synthetic-wrong-grammar-reference-v2"
        )
        self.assertIn(
            "unreferenced_reference_payload",
            self._codes(value, calibration_reference=wrong_reference),
        )
        wrong_identity_binding = deepcopy(value)
        wrong_identity_binding["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = task_payload_fingerprint(wrong_reference)
        self.assertIn(
            "calibration_reference_mismatch",
            self._codes(
                wrong_identity_binding,
                calibration_reference=wrong_reference,
            ),
        )

    def test_reference_chronology_and_task_state_are_fail_closed(self) -> None:
        calibration = self._approved_calibration()

        mismatched_time = deepcopy(calibration)
        mismatched_time["approval"]["calibration"][
            "checked_at"
        ] = "2026-08-28T00:01:00+09:00"
        self.assertIn(
            "calibration_decision_time_mismatch",
            self._codes(mismatched_time),
        )

        late_calibration = deepcopy(calibration)
        late_calibration["approval"]["calibration"][
            "checked_at"
        ] = "2026-08-28T00:02:00+09:00"
        late_calibration["approval"]["decisions"][0][
            "checked_at"
        ] = "2026-08-28T00:02:00+09:00"
        validate_timeline_v2(late_calibration, purpose="premiere_xml")
        early_full_edit = self._full_edit_from_calibration(late_calibration)
        self.assertIn(
            "calibration_precedes_revision",
            self._codes(
                early_full_edit,
                calibration_reference=late_calibration,
            ),
        )

        approval_mutation = deepcopy(calibration)
        approval_mutation["approval"]["calibration"][
            "approval_evidence"
        ] += " mutated"
        self.assertEqual(
            payload_fingerprint(approval_mutation),
            payload_fingerprint(calibration),
        )
        self.assertNotEqual(
            task_payload_fingerprint(approval_mutation),
            task_payload_fingerprint(calibration),
        )
        full_edit = self._full_edit_from_calibration(calibration)
        self.assertIn(
            "unreferenced_reference_payload",
            self._codes(
                full_edit,
                calibration_reference=approval_mutation,
            ),
        )
        approval_payload_binding = deepcopy(full_edit)
        approval_payload_binding["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = payload_fingerprint(approval_mutation)
        self.assertIn(
            "calibration_reference_mismatch",
            self._codes(
                approval_payload_binding,
                calibration_reference=approval_mutation,
            ),
        )

        validation_mutation = deepcopy(calibration)
        validation_mutation["validation"]["passes"]["causal_space"][
            "evidence"
        ] += " mutated"
        self.assertEqual(
            payload_fingerprint(validation_mutation),
            payload_fingerprint(calibration),
        )
        self.assertNotEqual(
            task_payload_fingerprint(validation_mutation),
            task_payload_fingerprint(calibration),
        )
        self.assertIn(
            "unreferenced_reference_payload",
            self._codes(
                full_edit,
                calibration_reference=validation_mutation,
            ),
        )
        validation_payload_binding = deepcopy(full_edit)
        validation_payload_binding["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = payload_fingerprint(validation_mutation)
        self.assertIn(
            "calibration_reference_mismatch",
            self._codes(
                validation_payload_binding,
                calibration_reference=validation_mutation,
            ),
        )

        late_baseline = self._full_edit_from_calibration(calibration)
        self._approve_revision(late_baseline)
        late_baseline["approval"]["decisions"][0][
            "checked_at"
        ] = "2026-08-28T00:02:00+09:00"
        early_delta = self._approved_delta_from_baseline(late_baseline)
        self.assertIn(
            "baseline_precedes_revision",
            self._codes(
                early_delta,
                purpose=None,
                calibration_reference=calibration,
                baseline_reference=late_baseline,
            ),
        )

    def test_current_revision_is_an_allowed_exact_delta_baseline(self) -> None:
        calibration = self._approved_calibration()
        current_baseline = self._full_edit_from_calibration(calibration)
        self._approve_revision(current_baseline)
        current_baseline["revision"]["status"] = "current"
        validate_timeline_v2(
            current_baseline,
            purpose="premiere_xml",
            calibration_reference=calibration,
        )

        value = self._approved_delta_from_baseline(current_baseline)
        validate_timeline_v2(
            value,
            purpose="premiere_xml",
            reference_payloads=(current_baseline, calibration),
        )

    def test_approved_delta_requires_the_actual_approved_baseline_payload(self) -> None:
        baseline = self._approved_calibration()
        value = self._approved_delta_from_baseline(baseline)

        validate_timeline_v2(value, baseline_reference=baseline)
        self.assertIn("baseline_reference_required", self._codes(value))

        wrong_reference = self._approved_calibration("synthetic-other-baseline-v2")
        self.assertIn(
            "unreferenced_reference_payload",
            self._codes(
                value,
                purpose=None,
                baseline_reference=wrong_reference,
            ),
        )
        wrong_identity_binding = deepcopy(value)
        wrong_identity_binding["editorial_evidence"]["feedback"][
            "baseline_payload_fingerprint"
        ] = task_payload_fingerprint(wrong_reference)
        self.assertIn(
            "revision_supersedes_mismatch",
            self._codes(
                wrong_identity_binding,
                purpose=None,
                baseline_reference=wrong_reference,
            ),
        )

    def test_approved_delta_must_carry_forward_unresolved_baseline_defect(
        self,
    ) -> None:
        baseline = self._approved_calibration()
        baseline["editorial_evidence"]["feedback"]["defects"] = [
            {
                "id": "defect-user-deferred",
                "scope": "synthetic discovery boundary",
                "clip_ids": ["V001"],
                "status": "approved_defer",
                "evidence": "synthetic user decision retained for regression",
                "approved_by": "user",
            }
        ]
        self._approve_revision(baseline)
        baseline["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = payload_fingerprint(baseline)
        validate_timeline_v2(baseline, purpose="premiere_xml")

        value = self._approved_delta_from_baseline(baseline)
        value["editorial_evidence"]["feedback"]["defects"] = []
        self._refresh_review(value)
        self.assertIn(
            "feedback_defect_missing",
            self._codes(
                value,
                purpose=None,
                baseline_reference=baseline,
            ),
        )

    def test_approved_delta_enforces_actual_diff_defect_and_preservation_scopes(
        self,
    ) -> None:
        baseline = self._approved_calibration()
        feedback = baseline["editorial_evidence"]["feedback"]
        feedback["positive_locks"] = [
            {
                "id": "lock-reaction",
                "scope": "approved reaction beat",
                "clip_ids": ["V002", "A002"],
                "evidence": "user approved reaction continuity",
                "preserved": True,
            }
        ]
        feedback["untouched"] = [
            {
                "id": "untouched-reaction-audio",
                "scope": "approved reaction audio",
                "clip_ids": ["A002"],
                "evidence": "outside the requested defect",
                "preserved": True,
            }
        ]
        feedback["defects"] = [
            {
                "id": "defect-opening-wording",
                "scope": "opening information beat",
                "clip_ids": ["V001"],
                "status": "approved_defer",
                "evidence": "user deferred this exact clip for a delta",
                "approved_by": "user",
            }
        ]
        self._approve_revision(baseline)
        baseline["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = payload_fingerprint(baseline)
        validate_timeline_v2(baseline, purpose="premiere_xml")

        changed = self._approved_delta_from_baseline(baseline)
        changed["sequence"]["video_clips"][0][
            "edit_reason"
        ] = "승인된 결함 범위 안에서 원인 정보를 더 명확히 보존한다."
        changed["editorial_evidence"]["feedback"]["defects"][0].update(
            {"status": "resolved", "approved_by": None}
        )
        self._refresh_review(changed)
        validate_timeline_v2(
            changed,
            purpose=None,
            baseline_reference=baseline,
        )

        protected_mutation = deepcopy(changed)
        protected_mutation["sequence"]["video_clips"][1][
            "edit_reason"
        ] += " unauthorized"
        self._refresh_review(protected_mutation)
        protected_codes = self._codes(
            protected_mutation,
            purpose=None,
            baseline_reference=baseline,
        )
        self.assertIn("positive_lock_diff", protected_codes)
        self.assertIn("feedback_unscoped_delta", protected_codes)

        missing_lock = deepcopy(changed)
        missing_lock["editorial_evidence"]["feedback"]["positive_locks"] = []
        self._refresh_review(missing_lock)
        self.assertIn(
            "feedback_lock_missing",
            self._codes(
                missing_lock,
                purpose=None,
                baseline_reference=baseline,
            ),
        )

        no_delta = self._approved_delta_from_baseline(baseline)
        no_delta["editorial_evidence"]["feedback"]["defects"][0].update(
            {"status": "resolved", "approved_by": None}
        )
        self._refresh_review(no_delta)
        self.assertIn(
            "resolved_defect_without_delta",
            self._codes(
                no_delta,
                purpose=None,
                baseline_reference=baseline,
            ),
        )

    def test_format_regeneration_preserves_editorial_content_and_changes_delivery_only(
        self,
    ) -> None:
        baseline = self._approved_calibration()
        value = deepcopy(baseline)
        value["timeline_id"] = "synthetic-format-regeneration-v2"
        value["workflow_profile"] = "format_regeneration"
        value["revision"].update(
            {
                "status": "working_candidate",
                "supersedes": baseline["timeline_id"],
                "state_owner_id": value["timeline_id"],
            }
        )
        value["editorial_evidence"]["feedback"][
            "baseline_payload_fingerprint"
        ] = task_payload_fingerprint(baseline)
        value["approval"]["decisions"] = []
        value["delivery"].update(
            {
                "artifact_id": value["timeline_id"],
                "output_path": "synthetic-format-regeneration.xml",
            }
        )
        self._refresh_review(value)
        self.assertEqual(
            editorial_fingerprint(value),
            editorial_fingerprint(baseline),
        )
        validate_timeline_v2(
            value,
            purpose="premiere_xml",
            baseline_reference=baseline,
        )

        editorial_mutation = deepcopy(value)
        editorial_mutation["sequence"]["video_clips"][0][
            "edit_reason"
        ] += " changed"
        self._refresh_review(editorial_mutation)
        self.assertIn(
            "format_regeneration_editorial_change",
            self._codes(
                editorial_mutation,
                purpose=None,
                baseline_reference=baseline,
            ),
        )

    def test_audio_event_ownership_cannot_interleave_a_b_a(self) -> None:
        value = self._timeline()
        third_audio = deepcopy(value["sequence"]["audio_clips"][1])
        third_audio.update(
            {
                "id": "A003",
                "source_in": 420,
                "source_out": 480,
                "frames": 60,
                "timeline_start": 240,
                "timeline_end": 300,
                "gap_before": 0,
            }
        )
        value["sequence"]["audio_clips"].append(third_audio)
        value["editorial_evidence"]["events"][0]["audio_clip_ids"].append(
            "A003"
        )
        value["editorial_evidence"]["events"][0]["source_out"] = 480
        value["editorial_evidence"]["microbeats"][0]["audio_clip_ids"].append(
            "A003"
        )
        value["editorial_evidence"]["microbeats"][0]["source_out"] = 480
        self._refresh_review(value)

        codes = self._codes(value)
        self.assertIn("event_timeline_discontinuity", codes)
        self.assertIn("event_clip_order", codes)

    def test_fractional_frame_rate_rejects_ambiguous_colon_timecode(self) -> None:
        value = self._timeline()
        value["source_manifest"]["frame_rate"] = {
            "numerator": 60000,
            "denominator": 1001,
        }
        self._refresh_review(value)
        self.assertIn("time_reference_parse_error", self._codes(value))

    def test_transitive_reference_bundle_rejects_dangling_cycle_and_ambiguity(
        self,
    ) -> None:
        calibration = self._approved_calibration(
            "synthetic-chain-calibration-v2"
        )
        baseline = self._full_edit_from_calibration(calibration)
        self._approve_revision(baseline)
        validate_timeline_v2(
            baseline,
            purpose="premiere_xml",
            reference_payloads=(calibration,),
        )
        value = self._approved_delta_from_baseline(baseline)

        validate_timeline_v2(
            value,
            purpose="premiere_xml",
            reference_payloads=(baseline, calibration),
        )

        self.assertIn(
            "calibration_reference_required",
            self._codes(value, reference_payloads=(baseline,)),
        )
        cycle = deepcopy(value)
        cycle["approval"]["calibration"][
            "approved_payload_fingerprint"
        ] = payload_fingerprint(cycle)
        self.assertEqual(
            cycle["approval"]["calibration"][
                "approved_payload_fingerprint"
            ],
            payload_fingerprint(cycle),
        )
        self.assertIn("reference_cycle", self._codes(cycle))

        ambiguous_calibration = deepcopy(calibration)
        ambiguous_calibration["approval"]["calibration"][
            "approval_evidence"
        ] += " conflicting state"
        self.assertEqual(
            payload_fingerprint(ambiguous_calibration),
            payload_fingerprint(calibration),
        )
        self.assertIn(
            "ambiguous_reference_payload",
            self._codes(
                value,
                reference_payloads=(
                    baseline,
                    calibration,
                    ambiguous_calibration,
                ),
            ),
        )

    def test_reference_bundle_requires_valid_consumed_closure(self) -> None:
        value = self._timeline()
        self.assertIn(
            "invalid_reference_payload",
            self._codes(
                value,
                reference_payloads=({"timeline_version": 2},),
            ),
        )

        calibration = self._approved_calibration(
            "synthetic-used-calibration-v2"
        )
        full_edit = self._full_edit_from_calibration(calibration)
        unused = self._approved_calibration(
            "synthetic-unused-calibration-v2"
        )
        self.assertIn(
            "unreferenced_reference_payload",
            self._codes(
                full_edit,
                reference_payloads=(calibration, unused),
            ),
        )

    def test_reference_bundle_has_a_bounded_resource_limit(self) -> None:
        value = self._timeline()
        references = tuple(deepcopy(value) for _ in range(65))
        self.assertIn(
            "reference_bundle_too_large",
            self._codes(value, purpose=None, reference_payloads=references),
        )

    def test_timestamp_schema_is_structural_and_runtime_checks_calendar_dates(
        self,
    ) -> None:
        invalid_calendar = self._timeline()
        invalid_calendar["revision"][
            "checked_at"
        ] = "2026-02-30T00:00:00+09:00"
        self.assertTrue(
            _powershell_schema_accepts(invalid_calendar, self.schema_path)
        )
        self.assertIn("invalid_timestamp", self._codes(invalid_calendar))

    def test_guarded_writer_verifies_source_and_exact_delivery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-v2-") as raw:
            root = Path(raw)
            value, source, output = self._ready_for_temp(root)
            result = write_validated_premiere_xml(
                value,
                output,
                profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
            )
            self.assertTrue(output.is_file())
            self.assertEqual(result["payload_fingerprint"], payload_fingerprint(value))
            self.assertEqual(
                result["editorial_fingerprint"], editorial_fingerprint(value)
            )
            self.assertEqual(
                result["delivery_fingerprint"], delivery_fingerprint(value)
            )
            self.assertEqual(ET.parse(output).getroot().attrib["version"], "4")
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                [source.name, output.name],
            )
            with self.assertRaisesRegex(PremiereXmlError, "already exists"):
                write_validated_premiere_xml(
                    value,
                    output,
                    profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                )

    def test_guarded_writer_rejects_profile_path_collision_and_source_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-v2-blocked-") as raw:
            root = Path(raw)
            value, source, output = self._ready_for_temp(root)
            with self.assertRaisesRegex(PremiereXmlError, "profile"):
                write_validated_premiere_xml(
                    value, output, profile="sequence-v5", editorial_state=synthetic_state(value)
                )
            self.assertFalse(output.exists())

            timeline_path = root / "timeline-input.xml"
            value["delivery"]["output_path"] = str(timeline_path)
            with self.assertRaisesRegex(PremiereXmlError, "collides"):
                write_validated_premiere_xml(
                    value,
                    timeline_path,
                    profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                    input_paths=(timeline_path,),
                )
            self.assertFalse(timeline_path.exists())

            value["delivery"]["output_path"] = str(output)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(PremiereXmlError, "SHA-256"):
                write_validated_premiere_xml(
                    value,
                    output,
                    profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                )
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".*.tmp")), [])

    def test_guarded_writer_rejects_relative_and_noncanonical_source_paths(self) -> None:
        cases = (
            (
                "relative",
                lambda root, source: source.name,
                "absolute canonical path",
            ),
            (
                "parent-segment",
                lambda root, source: str(
                    root / "unused-directory" / ".." / source.name
                ),
                "canonical path",
            ),
        )
        for name, render_path, expected_message in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"video-edit-v2-source-path-{name}-"
            ) as raw:
                root = Path(raw)
                value, source, output = self._ready_for_temp(root)
                value["source_manifest"]["path"] = render_path(root, source)
                self._refresh_review(value)
                with self.assertRaisesRegex(PremiereXmlError, expected_message):
                    write_validated_premiere_xml(
                        value,
                        output,
                        profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                    )
                self.assertFalse(output.exists())
                self.assertEqual(list(root.glob(".*.tmp")), [])

    def test_guarded_writer_requires_absolute_canonical_declared_and_requested_outputs(
        self,
    ) -> None:
        def parent_segment(root: Path, output: Path) -> Path:
            return root / "unused-directory" / ".." / output.name

        cases = (
            (
                "relative-both",
                lambda root, output: output.name,
                lambda root, output: Path(output.name),
            ),
            (
                "relative-declaration",
                lambda root, output: output.name,
                lambda root, output: output,
            ),
            (
                "relative-argument",
                lambda root, output: str(output),
                lambda root, output: Path(output.name),
            ),
            (
                "noncanonical-declaration",
                lambda root, output: str(parent_segment(root, output)),
                lambda root, output: output,
            ),
            (
                "noncanonical-argument",
                lambda root, output: str(output),
                lambda root, output: parent_segment(root, output),
            ),
        )
        for name, render_declared, render_requested in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"video-edit-v2-output-path-{name}-"
            ) as raw:
                root = Path(raw)
                value, source, output = self._ready_for_temp(root)
                value["delivery"]["output_path"] = render_declared(root, output)
                requested = render_requested(root, output)
                previous_cwd = Path.cwd()
                os.chdir(root)
                try:
                    with self.assertRaises(PremiereXmlError):
                        write_validated_premiere_xml(
                            value,
                            requested,
                            profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                        )
                finally:
                    os.chdir(previous_cwd)
                self.assertFalse(output.exists())
                self.assertEqual(list(root.glob(".*.tmp")), [])
                self.assertEqual(
                    sorted(item.name for item in root.iterdir()),
                    [source.name],
                )

    def test_relative_delivery_cannot_resolve_to_different_outputs_by_cwd(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="video-edit-v2-output-cwd-"
        ) as raw:
            root = Path(raw)
            first_cwd = root / "first"
            second_cwd = root / "second"
            first_cwd.mkdir()
            second_cwd.mkdir()
            value, source, absolute_output = self._ready_for_temp(root)
            value["delivery"]["output_path"] = "same-relative-output.xml"
            previous_cwd = Path.cwd()
            try:
                for cwd in (first_cwd, second_cwd):
                    with self.subTest(cwd=cwd.name):
                        os.chdir(cwd)
                        with self.assertRaises(PremiereXmlError):
                            write_validated_premiere_xml(
                                value,
                                Path("same-relative-output.xml"),
                                profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                            )
                        self.assertFalse(
                            (cwd / "same-relative-output.xml").exists()
                        )
                        self.assertEqual(list(cwd.glob(".*.tmp")), [])
            finally:
                os.chdir(previous_cwd)
            self.assertFalse(absolute_output.exists())
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                sorted([source.name, first_cwd.name, second_cwd.name]),
            )

    def test_pre_publish_source_mutation_leaves_no_output_or_temp_file(self) -> None:
        class RefreshingSourceHandle:
            def __init__(self, path: Path) -> None:
                self.path = path
                self.buffer = b""
                self.position = 0

            def seek(self, offset: int, whence: int = 0) -> int:
                if whence != 0 or offset != 0:
                    raise AssertionError("fixture only supports seek(0)")
                self.buffer = self.path.read_bytes()
                self.position = 0
                return 0

            def read(self, size: int = -1) -> bytes:
                end = len(self.buffer) if size < 0 else self.position + size
                chunk = self.buffer[self.position:end]
                self.position += len(chunk)
                return chunk

        @contextmanager
        def refreshing_source(path: Path):
            yield RefreshingSourceHandle(path)

        with tempfile.TemporaryDirectory(
            prefix="video-edit-v2-source-race-"
        ) as raw:
            root = Path(raw)
            value, source, output = self._ready_for_temp(root)
            original_write = delivery_module._write_no_clobber

            def mutate_before_publish(
                target: Path,
                rendered: bytes,
                *,
                pre_publish=None,
            ) -> None:
                source.write_bytes(b"changed-during-publish")
                original_write(
                    target,
                    rendered,
                    pre_publish=pre_publish,
                )

            with patch.object(
                delivery_module,
                "_locked_source",
                refreshing_source,
            ), patch.object(
                delivery_module,
                "_write_no_clobber",
                mutate_before_publish,
            ):
                with self.assertRaisesRegex(
                    PremiereXmlError,
                    "source media changed during XML generation",
                ):
                    write_validated_premiere_xml(
                        value,
                        output,
                        profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                    )
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".*.tmp")), [])
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                [source.name],
            )

    def test_writer_defect_matrix_never_leaves_output_or_temporary_files(self) -> None:
        def raw_time_mismatch(value: dict) -> None:
            value["editorial_evidence"]["time_references"][0]["start_frame"] += 1
            self._refresh_review(value)

        def duplicate_event_coverage(value: dict) -> None:
            event = value["editorial_evidence"]["events"][1]
            event["video_clip_ids"].append("V001")
            event["source_in"] = 0
            self._refresh_review(value)

        def wrong_microbeat_event(value: dict) -> None:
            value["editorial_evidence"]["microbeats"][1][
                "event_id"
            ] = "event-discovery"
            self._refresh_review(value)

        def stale_editorial_review(value: dict) -> None:
            value["sequence"]["video_clips"][0]["edit_reason"] += " stale"

        def missing_calibration_reference(value: dict) -> None:
            value["workflow_profile"] = "new_full_edit"
            value["approval"]["calibration"].update(
                {
                    "status": "approved",
                    "artifact_id": "approved-calibration",
                    "approved_payload_fingerprint": "sha256:" + "1" * 64,
                    "approved_by": "user",
                    "approval_evidence": "synthetic approval",
                    "checked_at": "2026-08-28T00:00:00+09:00",
                }
            )
            self._refresh_review(value)

        def missing_baseline_reference(value: dict) -> None:
            value["workflow_profile"] = "approved_delta"
            value["revision"]["supersedes"] = "approved-baseline"
            value["editorial_evidence"]["feedback"][
                "baseline_payload_fingerprint"
            ] = "sha256:" + "2" * 64
            self._refresh_review(value)

        cases = (
            ("raw-time-mismatch", raw_time_mismatch, "time_reference_frame_mismatch"),
            (
                "event-duplicate-coverage",
                duplicate_event_coverage,
                "event_clip_coverage",
            ),
            (
                "microbeat-wrong-event",
                wrong_microbeat_event,
                "microbeat_event_mismatch",
            ),
            ("stale-review", stale_editorial_review, "stale_semantic_review"),
            (
                "missing-calibration-reference",
                missing_calibration_reference,
                "calibration_reference_required",
            ),
            (
                "missing-baseline-reference",
                missing_baseline_reference,
                "baseline_reference_required",
            ),
        )
        for name, mutate, expected_code in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"video-edit-v2-no-output-{name}-"
            ) as raw:
                root = Path(raw)
                value, source, output = self._ready_for_temp(root)
                mutate(value)
                with self.assertRaises(TimelineV2Error) as raised:
                    write_validated_premiere_xml(
                        value,
                        output,
                        profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                    )
                self.assertIn(
                    expected_code,
                    {issue["code"] for issue in raised.exception.issues},
                )
                self.assertFalse(output.exists())
                self.assertEqual(list(root.glob(".*.tmp")), [])
                self.assertEqual(sorted(item.name for item in root.iterdir()), [source.name])

    def test_atomic_no_clobber_allows_exactly_one_concurrent_writer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-v2-race-") as raw:
            root = Path(raw)
            value, _source, output = self._ready_for_temp(root)

            def run() -> str:
                try:
                    write_validated_premiere_xml(
                        deepcopy(value),
                        output,
                        profile="premiere-cs6-v4",
                        editorial_state=synthetic_state(value),
                    )
                except PremiereXmlError:
                    return "blocked"
                return "written"

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = sorted(pool.map(lambda _: run(), range(2)))
            self.assertEqual(results, ["blocked", "written"])
            self.assertEqual(ET.parse(output).getroot().attrib["version"], "4")
            self.assertEqual(list(root.glob(".*.tmp")), [])

    @unittest.skipUnless(os.name == "nt", "mandatory source lock is Windows-specific")
    def test_real_windows_source_snapshot_blocks_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-v2-source-lock-") as raw:
            source = Path(raw) / "source.mp4"
            source.write_bytes(b"immutable-during-snapshot")
            with delivery_module._locked_source(source):
                with self.assertRaises(OSError):
                    source.write_bytes(b"mutation-must-fail")
            source.write_bytes(b"mutation-after-release")
            self.assertEqual(source.read_bytes(), b"mutation-after-release")

    @unittest.skipUnless(os.name == "nt", "process race contract is Windows-specific")
    def test_cli_process_race_allows_exactly_one_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-v2-process-race-") as raw:
            root = Path(raw)
            value, _source, output = self._ready_for_temp(root)
            state_path = root / "editorial-state.json"
            state_path.write_text(json.dumps(synthetic_state(value)), encoding="utf-8")
            timeline_path = root / "timeline-v2.json"
            timeline_path.write_text(
                json.dumps(value, ensure_ascii=False), encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [str(ROOT / "core" / "src"), str(ROOT / "extension" / "src")]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            command = [
                sys.executable,
                "-m",
                "video_editing",
                "premiere-xml",
                "--editorial-state-json", str(state_path),
                "--timeline-json",
                str(timeline_path),
                "--output",
                str(output),
                "--profile",
                "premiere-cs6-v4",
            ]
            processes = [
                subprocess.Popen(
                    command,
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=environment,
                )
                for _ in range(2)
            ]
            results = [process.communicate(timeout=30) for process in processes]
            return_codes = sorted(process.returncode for process in processes)
            self.assertEqual(return_codes, [0, 2], results)
            self.assertEqual(ET.parse(output).getroot().attrib["version"], "4")
            self.assertEqual(list(root.glob(".*.tmp")), [])

    def test_cli_uses_v2_as_the_only_contract_and_creates_one_xml(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-v2-cli-") as raw:
            root = Path(raw)
            value, source, output = self._ready_for_temp(root)
            state_path = root / "editorial-state.json"
            state_path.write_text(json.dumps(synthetic_state(value)), encoding="utf-8")
            timeline_path = root / "timeline-v2.json"
            timeline_path.write_text(
                json.dumps(value, ensure_ascii=False), encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [str(ROOT / "core" / "src"), str(ROOT / "extension" / "src")]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "video_editing",
                    "premiere-xml",
                    "--editorial-state-json", str(state_path),
                    "--timeline-json",
                    str(timeline_path),
                    "--output",
                    str(output),
                    "--profile",
                    "premiere-cs6-v4",
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                sorted([source.name, output.name, timeline_path.name, state_path.name]),
            )

    def test_cli_malformed_delivery_without_profile_is_structured_no_output_error(
        self,
    ) -> None:
        for name, malformed_delivery in (
            ("list", []),
            ("string", "not-a-delivery-object"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"video-edit-v2-cli-malformed-{name}-"
            ) as raw:
                root = Path(raw)
                value, source, output = self._ready_for_temp(root)
                value["delivery"] = malformed_delivery
                state_path = root / "editorial-state.json"
                state_path.write_text(json.dumps(synthetic_state(value)), encoding="utf-8")
                timeline_path = root / "timeline-v2.json"
                timeline_path.write_text(
                    json.dumps(value, ensure_ascii=False),
                    encoding="utf-8",
                )
                environment = os.environ.copy()
                environment["PYTHONPATH"] = os.pathsep.join(
                    [
                        str(ROOT / "core" / "src"),
                        str(ROOT / "extension" / "src"),
                    ]
                )
                environment["PYTHONDONTWRITEBYTECODE"] = "1"
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "video_editing",
                        "premiere-xml",
                        "--editorial-state-json", str(state_path),
                        "--timeline-json",
                        str(timeline_path),
                        "--output",
                        str(output),
                    ],
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    env=environment,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)
                report = json.loads(result.stderr)
                self.assertFalse(report["ok"])
                self.assertEqual(report["error"]["kind"], "invalid_v2_fields")
                self.assertTrue(report["error"]["message"])
                self.assertFalse(output.exists())
                self.assertEqual(list(root.glob(".*.tmp")), [])
                self.assertEqual(
                    sorted(item.name for item in root.iterdir()),
                    sorted([source.name, timeline_path.name, state_path.name]),
                )

    def test_cli_non_utf8_timeline_is_structured_no_output_error(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="video-edit-v2-cli-non-utf8-"
        ) as raw:
            root = Path(raw)
            value, source, output = self._ready_for_temp(root)
            state_path = root / "editorial-state.json"
            state_path.write_text(json.dumps(synthetic_state(value)), encoding="utf-8")
            timeline_path = root / "timeline-v2.json"
            timeline_path.write_bytes(b"\xff\xfe{not-utf8}")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [str(ROOT / "core" / "src"), str(ROOT / "extension" / "src")]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "video_editing",
                    "premiere-xml",
                    "--editorial-state-json", str(state_path),
                    "--timeline-json",
                    str(timeline_path),
                    "--output",
                    str(output),
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stderr)
            self.assertFalse(report["ok"])
            self.assertEqual(report["error"]["kind"], "xml_error")
            self.assertIn("valid UTF-8", report["error"]["message"])
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".*.tmp")), [])
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                sorted([source.name, timeline_path.name, state_path.name]),
            )

    def test_low_level_xml_writers_are_not_public_package_api(self) -> None:
        self.assertNotIn("build_premiere_xml", public_api)
        self.assertNotIn("write_premiere_xml", public_api)
        self.assertIn("write_validated_premiere_xml", public_api)
        self.assertIn("editorial_fingerprint", public_api)
        self.assertIn("payload_fingerprint", public_api)
        self.assertIn("task_payload_fingerprint", public_api)
        self.assertIn("delivery_fingerprint", public_api)

    def test_legacy_migration_is_not_run_and_cannot_inherit_approval(self) -> None:
        legacy_timeline = json.loads(
            (
                ROOT / "extension" / "examples" / "video-edit-timeline-v1.json"
            ).read_text(encoding="utf-8")
        )
        legacy_contract = json.loads(
            (
                ROOT / "extension" / "examples" / "video-edit-contract-v1.json"
            ).read_text(encoding="utf-8")
        )
        migrated = migrate_legacy_v1(
            legacy_timeline,
            legacy_contract,
            timeline_id="synthetic-migrated-v2",
            source_content_sha256="sha256:" + "1" * 64,
            source_byte_size=123,
            delivery_output_path="synthetic-migrated.xml",
            checked_at="2026-08-28T00:00:00+09:00",
        )
        self.assertEqual(migrated["revision"]["status"], "working_candidate")
        self.assertEqual(
            [clip["id"] for clip in migrated["sequence"]["video_clips"]],
            ["V001", "V002.m1", "V002.m2"],
        )
        self.assertEqual(
            [clip["id"] for clip in migrated["sequence"]["audio_clips"]],
            ["A001", "A002.m1", "A002.m2"],
        )
        for track in ("video_clips", "audio_clips"):
            first_split, second_split = migrated["sequence"][track][1:]
            self.assertEqual(
                (first_split["source_in"], first_split["source_out"]),
                (300, 360),
            )
            self.assertEqual(
                (first_split["timeline_start"], first_split["timeline_end"]),
                (120, 180),
            )
            self.assertEqual(
                (second_split["source_in"], second_split["source_out"]),
                (360, 420),
            )
            self.assertEqual(
                (second_split["timeline_start"], second_split["timeline_end"]),
                (180, 240),
            )
            self.assertEqual(second_split["gap_before"], 0)
        events_by_id = {
            event["id"]: event
            for event in migrated["editorial_evidence"]["events"]
        }
        self.assertEqual(
            events_by_id["event-reaction"]["video_clip_ids"],
            ["V002.m1"],
        )
        self.assertEqual(
            events_by_id["event-reaction"]["audio_clip_ids"],
            ["A002.m1"],
        )
        self.assertEqual(
            events_by_id["event-result"]["video_clip_ids"],
            ["V002.m2"],
        )
        self.assertEqual(
            events_by_id["event-result"]["audio_clip_ids"],
            ["A002.m2"],
        )
        for media_scope in ("video", "audio"):
            sequence_key = f"{media_scope}_clips"
            event_key = f"{media_scope}_clip_ids"
            retained_ids = [
                clip["id"] for clip in migrated["sequence"][sequence_key]
            ]
            owned_ids = [
                clip_id
                for event in migrated["editorial_evidence"]["events"]
                for clip_id in event[event_key]
            ]
            self.assertCountEqual(owned_ids, retained_ids)
            self.assertEqual(len(owned_ids), len(set(owned_ids)))
        calibration = migrated["approval"]["calibration"]
        self.assertEqual(calibration["status"], "pending")
        self.assertIsNone(calibration["artifact_id"])
        self.assertIsNone(calibration["approved_payload_fingerprint"])
        self.assertIsNone(calibration["approved_by"])
        self.assertIsNone(calibration["approval_evidence"])
        self.assertIsNone(calibration["checked_at"])
        self.assertEqual(migrated["approval"]["decisions"], [])
        self.assertEqual(migrated["validation"]["semantic_status"], "not_run")
        self.assertIsNone(migrated["validation"]["reviewed_editorial_fingerprint"])
        self.assertIsNone(migrated["validation"]["reviewer"])
        self.assertTrue(
            all(
                review == {
                    "status": "not_run",
                    "method": None,
                    "reviewer": None,
                    "checked_at": None,
                    "evidence": None,
                }
                for review in migrated["validation"]["passes"].values()
            )
        )
        self.assertTrue(
            all(
                beat["boundary_review"] == "pending"
                and beat["event_id"]
                and beat["media_scope"] in {"video", "audio"}
                for beat in migrated["editorial_evidence"]["microbeats"]
            )
        )

    def test_legacy_migration_splits_multiple_boundaries_without_id_collision(
        self,
    ) -> None:
        legacy_timeline = json.loads(
            (
                ROOT / "extension" / "examples" / "video-edit-timeline-v1.json"
            ).read_text(encoding="utf-8")
        )
        legacy_contract = json.loads(
            (
                ROOT / "extension" / "examples" / "video-edit-contract-v1.json"
            ).read_text(encoding="utf-8")
        )
        legacy_timeline["sequence"]["video_clips"][0]["id"] = "V002.m1"
        legacy_contract["events"][1]["source_out"] = 330
        legacy_contract["events"].insert(
            2,
            {
                "id": "event-action",
                "role": "reaction",
                "source_in": 330,
                "source_out": 360,
                "depends_on": ["event-reaction"],
                "microbeat_status": "reviewed",
                "continuity_reason": None,
            },
        )
        legacy_contract["events"][3]["depends_on"] = ["event-action"]

        migrated = migrate_legacy_v1(
            legacy_timeline,
            legacy_contract,
            timeline_id="synthetic-multi-boundary-v2",
            source_content_sha256="sha256:" + "1" * 64,
            source_byte_size=123,
            delivery_output_path="synthetic-multi-boundary.xml",
            checked_at="2026-08-28T00:00:00+09:00",
        )
        video_ids = [
            clip["id"] for clip in migrated["sequence"]["video_clips"]
        ]
        self.assertEqual(
            video_ids,
            ["V002.m1", "V002.m1.2", "V002.m2", "V002.m3"],
        )
        split_video = migrated["sequence"]["video_clips"][1:]
        self.assertEqual(
            [
                (clip["source_in"], clip["source_out"])
                for clip in split_video
            ],
            [(300, 330), (330, 360), (360, 420)],
        )
        self.assertEqual(
            [
                (clip["timeline_start"], clip["timeline_end"])
                for clip in split_video
            ],
            [(120, 150), (150, 180), (180, 240)],
        )
        self.assertEqual(
            len(video_ids),
            len(set(video_ids)),
        )
        self.assertEqual(migrated["validation"]["semantic_status"], "not_run")
        validate_timeline_v2(migrated)
        codes = self._codes(migrated)
        self.assertIn("microbeat_review_incomplete", codes)
        self.assertIn("semantic_gate_incomplete", codes)

    def test_runtime_and_v2_schema_share_the_complete_structural_surface(self) -> None:
        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(TIMELINE_V2_FIELDS))
        properties = schema["properties"]
        self.assertEqual(set(properties["source_manifest"]["required"]), set(SOURCE_MANIFEST_FIELDS))
        evidence = properties["editorial_evidence"]
        self.assertEqual(set(evidence["required"]), set(EDITORIAL_EVIDENCE_FIELDS))
        self.assertEqual(set(evidence["properties"]["time_references"]["items"]["required"]), set(TIME_REFERENCE_FIELDS))
        self.assertEqual(set(evidence["properties"]["events"]["items"]["required"]), set(EVENT_FIELDS))
        self.assertEqual(set(evidence["properties"]["microbeats"]["items"]["required"]), set(MICROBEAT_FIELDS))
        self.assertIn("event_id", MICROBEAT_FIELDS)
        self.assertIn("media_scope", MICROBEAT_FIELDS)
        self.assertEqual(set(evidence["properties"]["feedback"]["required"]), set(FEEDBACK_FIELDS))
        self.assertEqual(set(properties["revision"]["required"]), set(REVISION_FIELDS))
        self.assertEqual(set(properties["approval"]["required"]), set(APPROVAL_FIELDS))
        self.assertEqual(set(properties["approval"]["properties"]["calibration"]["required"]), set(CALIBRATION_FIELDS))
        self.assertIn("checked_at", CALIBRATION_FIELDS)
        self.assertEqual(set(properties["approval"]["properties"]["decisions"]["items"]["required"]), set(DECISION_FIELDS))
        self.assertIn("reviewed_editorial_fingerprint", DECISION_FIELDS)
        self.assertEqual(set(properties["validation"]["required"]), set(VALIDATION_FIELDS))
        self.assertIn("reviewed_editorial_fingerprint", VALIDATION_FIELDS)
        self.assertEqual(set(schema["$defs"]["review_pass"]["required"]), set(VALIDATION_PASS_FIELDS))
        self.assertEqual(set(properties["delivery"]["required"]), set(DELIVERY_FIELDS))
        self.assertEqual(properties["delivery"]["properties"]["profile"]["const"], "premiere-cs6-v4")
        self.assertIs(properties["delivery"]["properties"]["overwrite"]["const"], False)
        self.assertTrue(schema["allOf"], "schema must encode conditional states, not field sets only")

        seen_keywords = _schema_keywords(schema)
        self.assertTrue(
            {"allOf", "anyOf", "if", "oneOf", "pattern", "then"}
            <= seen_keywords
        )

    def test_schema_and_runtime_share_representable_accept_reject_corpus(self) -> None:
        valid = self._timeline()
        cases: list[tuple[str, dict, bool]] = [("valid", valid, True)]

        extra = deepcopy(valid)
        extra["unexpected"] = True
        cases.append(("extra-field", extra, False))
        overwrite = deepcopy(valid)
        overwrite["delivery"]["overwrite"] = True
        cases.append(("overwrite", overwrite, False))
        wrong_profile = deepcopy(valid)
        wrong_profile["delivery"]["profile"] = "sequence-v5"
        cases.append(("profile", wrong_profile, False))

        missing_event_id = deepcopy(valid)
        del missing_event_id["editorial_evidence"]["microbeats"][0]["event_id"]
        cases.append(("missing-event-id", missing_event_id, False))
        wrong_media_scope = deepcopy(valid)
        wrong_media_scope["editorial_evidence"]["microbeats"][0][
            "media_scope"
        ] = "captions"
        cases.append(("invalid-media-scope", wrong_media_scope, False))

        incomplete_review = deepcopy(valid)
        incomplete_review["validation"]["passes"]["causal_space"]["status"] = "not_run"
        cases.append(("semantic-pass-incomplete", incomplete_review, False))
        missing_evidence = deepcopy(valid)
        missing_evidence["validation"]["passes"]["causal_space"]["method"] = None
        cases.append(("passed-review-evidence", missing_evidence, False))
        unknown_semantic_status = deepcopy(valid)
        unknown_semantic_status["validation"]["semantic_status"] = "pending"
        cases.append(("unknown-semantic-status", unknown_semantic_status, False))

        invalid_calibration_state = deepcopy(valid)
        invalid_calibration_state["approval"]["calibration"].update(
            {
                "required": False,
                "status": "approved",
                "artifact_id": invalid_calibration_state["timeline_id"],
                "approved_payload_fingerprint": "sha256:" + "1" * 64,
                "approved_by": "user",
                "approval_evidence": "stale approval",
                "checked_at": "2026-08-28T00:00:00+09:00",
            }
        )
        cases.append(("invalid-calibration-state", invalid_calibration_state, False))
        pending_calibration_evidence = deepcopy(valid)
        pending_calibration_evidence["approval"]["calibration"][
            "checked_at"
        ] = "2026-08-28T00:00:00+09:00"
        cases.append(
            ("pending-calibration-evidence", pending_calibration_evidence, False)
        )

        delta_without_baseline = deepcopy(valid)
        delta_without_baseline["workflow_profile"] = "approved_delta"
        cases.append(("delta-baseline", delta_without_baseline, False))
        unclassified = deepcopy(valid)
        unclassified["sequence"]["video_clips"][0]["edit_role"] = "unclassified"
        cases.append(("unclassified", unclassified, False))
        bad_time = deepcopy(valid)
        bad_time["editorial_evidence"]["time_references"][0].update(
            {"raw": "banana", "unit": "frames"}
        )
        cases.append(("time-unit", bad_time, False))
        removed_but_retained = deepcopy(valid)
        removed_but_retained["editorial_evidence"]["microbeats"][0]["decision"] = "remove"
        cases.append(("removed-retained", removed_but_retained, False))

        whitespace_event = deepcopy(valid)
        whitespace_event["editorial_evidence"]["microbeats"][0]["event_id"] = "   "
        cases.append(("whitespace-event-id", whitespace_event, False))
        whitespace_revision_time = deepcopy(valid)
        whitespace_revision_time["revision"]["checked_at"] = "   "
        cases.append(("whitespace-revision-time", whitespace_revision_time, False))
        malformed_revision_time = deepcopy(valid)
        malformed_revision_time["revision"]["checked_at"] = "banana"
        cases.append(("malformed-revision-time", malformed_revision_time, False))

        for name, value, expected in cases:
            with self.subTest(name=name, surface="schema"):
                self.assertEqual(
                    _powershell_schema_accepts(value, self.schema_path), expected
                )
            with self.subTest(name=name, surface="runtime"):
                try:
                    validate_timeline_v2(value)
                except TimelineV2Error:
                    accepted = False
                else:
                    accepted = True
                self.assertEqual(accepted, expected)


if __name__ == "__main__":
    unittest.main()
