from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "extension" / "src"))

from video_editing.edit_contract import (  # noqa: E402
    ARTIFACT_FIELDS,
    CALIBRATION_FIELDS,
    CONTRACT_FIELDS,
    DEFECT_FIELDS,
    DELIVERABLE_FIELDS,
    EVENT_FIELDS,
    FEEDBACK_FIELDS,
    PRESERVATION_FIELDS,
    STATE_FIELDS,
    TIME_REFERENCE_FIELDS,
    VALIDATION_FIELDS,
    EditContractError,
    fingerprint_source_manifest,
    inspect_edit_contract,
    validate_edit_contract,
)


class VideoEditingRuleGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract_path = ROOT / "extension" / "examples" / "video-edit-contract-v1.json"
        self.timeline_path = ROOT / "extension" / "examples" / "video-edit-timeline-v1.json"
        self.timeline = json.loads(self.timeline_path.read_text(encoding="utf-8"))
        self.source_manifest_hash = fingerprint_source_manifest(self.timeline["source"])

    def _contract(self) -> dict:
        return json.loads(self.contract_path.read_text(encoding="utf-8"))

    def _codes(self, contract: dict, *, timeline_id: str = "synthetic-video-edit") -> set[str]:
        with self.assertRaises(EditContractError) as raised:
            validate_edit_contract(
                contract,
                purpose="premiere_xml",
                timeline_id=timeline_id,
                expected_source_manifest_hash=self.source_manifest_hash,
            )
        return {issue["code"] for issue in raised.exception.issues}

    def test_valid_contract_passes_every_rule_gate_deterministically(self) -> None:
        contract = self._contract()
        self.assertEqual(
            validate_edit_contract(
                contract,
                purpose="premiere_xml",
                timeline_id="synthetic-video-edit",
                expected_source_manifest_hash=self.source_manifest_hash,
            ),
            contract,
        )
        first = inspect_edit_contract(
            contract,
            purpose="premiere_xml",
            timeline_id="synthetic-video-edit",
            expected_source_manifest_hash=self.source_manifest_hash,
        )
        second = inspect_edit_contract(
            deepcopy(contract),
            purpose="premiere_xml",
            timeline_id="synthetic-video-edit",
            expected_source_manifest_hash=self.source_manifest_hash,
        )
        self.assertEqual(first, second)
        self.assertTrue(first["ok"])
        self.assertEqual(len(first["checks"]), 8)
        changed = deepcopy(contract)
        changed["feedback"]["defects"][0]["evidence"] += " changed"
        self.assertNotEqual(
            first["fingerprint"],
            inspect_edit_contract(
                changed,
                purpose="premiere_xml",
                timeline_id="synthetic-video-edit",
                expected_source_manifest_hash=self.source_manifest_hash,
            )["fingerprint"],
        )

    def test_time_coordinate_must_be_confirmed_before_editing(self) -> None:
        contract = self._contract()
        contract["time_references"][0]["confirmed_by"] = "agent_assumption"
        self.assertIn("ambiguous_time_reference", self._codes(contract))

    def test_full_expansion_requires_user_approved_calibration(self) -> None:
        contract = self._contract()
        contract["calibration"]["status"] = "pending"
        contract["calibration"]["approved_by"] = None
        contract["calibration"]["approval_evidence"] = None
        self.assertIn("calibration_not_approved", self._codes(contract))

    def test_pending_calibration_can_generate_only_a_calibration_phase_xml(self) -> None:
        contract = self._contract()
        contract["phase"] = "calibration"
        contract["calibration"]["status"] = "pending"
        contract["calibration"]["approved_by"] = None
        contract["calibration"]["approval_evidence"] = None
        validate_edit_contract(
            contract,
            purpose="premiere_xml",
            timeline_id="synthetic-video-edit",
            expected_source_manifest_hash=self.source_manifest_hash,
        )

    def test_rejected_calibration_cannot_be_exported_again(self) -> None:
        contract = self._contract()
        contract["phase"] = "calibration"
        contract["calibration"]["status"] = "rejected"
        contract["calibration"]["approved_by"] = None
        contract["calibration"]["approval_evidence"] = None
        self.assertIn("calibration_rejected", self._codes(contract))

    def test_approved_calibration_requires_user_owned_evidence(self) -> None:
        contract = self._contract()
        contract["calibration"]["approved_by"] = "agent"
        contract["calibration"]["approval_evidence"] = None
        self.assertIn("calibration_approval_missing", self._codes(contract))

    def test_reaction_without_earlier_cause_is_blocked(self) -> None:
        contract = self._contract()
        contract["events"][1]["depends_on"] = []
        self.assertIn("missing_cause_anchor", self._codes(contract))

    def test_dependency_cannot_point_forward_or_to_missing_event(self) -> None:
        contract = self._contract()
        contract["events"][1]["depends_on"] = ["event-result"]
        self.assertIn("invalid_event_dependency", self._codes(contract))

    def test_reaction_dependency_must_be_a_causal_anchor_not_atmosphere(self) -> None:
        contract = self._contract()
        contract["events"][0]["role"] = "atmosphere"
        self.assertIn("missing_cause_anchor", self._codes(contract))

    def test_rough_block_cannot_pass_as_microbeat_edit(self) -> None:
        contract = self._contract()
        contract["events"][0]["microbeat_status"] = "pending"
        self.assertIn("microbeat_review_incomplete", self._codes(contract))

    def test_uncuttable_event_requires_source_based_reason(self) -> None:
        contract = self._contract()
        contract["events"][2]["continuity_reason"] = None
        self.assertIn("missing_continuity_reason", self._codes(contract))

    def test_positive_feedback_and_untouched_scope_are_regression_locks(self) -> None:
        contract = self._contract()
        contract["feedback"]["positive_locks"][0]["preserved"] = False
        contract["feedback"]["untouched"] = [{"id": "approved-opening", "preserved": False}]
        codes = self._codes(contract)
        self.assertIn("positive_lock_regression", codes)
        self.assertIn("untouched_scope_regression", codes)

    def test_unresolved_defect_requires_explicit_user_defer(self) -> None:
        contract = self._contract()
        defect = contract["feedback"]["defects"][0]
        defect["status"] = "approved_defer"
        defect["approved_by"] = None
        self.assertIn("unresolved_defect", self._codes(contract))
        defect["approved_by"] = "user"
        validate_edit_contract(
            contract,
            purpose="premiere_xml",
            timeline_id="synthetic-video-edit",
            expected_source_manifest_hash=self.source_manifest_hash,
        )

    def test_contract_source_manifest_must_match_export_timeline(self) -> None:
        contract = self._contract()
        with self.assertRaises(EditContractError) as raised:
            validate_edit_contract(
                contract,
                purpose="premiere_xml",
                timeline_id="synthetic-video-edit",
                expected_source_manifest_hash="sha256:" + "f" * 64,
            )
        self.assertIn(
            "source_manifest_mismatch",
            {issue["code"] for issue in raised.exception.issues},
        )

    def test_state_conflict_rejected_revision_and_wrong_timeline_are_blocked(self) -> None:
        contract = self._contract()
        contract["state"]["owner_conflict"] = True
        contract["state"]["source_revision_status"] = "use_prohibited"
        codes = self._codes(contract, timeline_id="different-timeline")
        self.assertIn("state_owner_conflict", codes)
        self.assertIn("invalid_source_revision", codes)
        self.assertIn("current_artifact_mismatch", codes)

    def test_semantic_gate_needs_all_normal_speed_review_perspectives(self) -> None:
        contract = self._contract()
        contract["validation"]["causal_space"] = "not_run"
        contract["validation"]["editorial_score"] = 95
        codes = self._codes(contract)
        self.assertIn("semantic_gate_without_normal_speed_review", codes)
        self.assertIn("editorial_score_without_semantic_gate", codes)

    def test_passed_semantic_gate_requires_reviewer_identity(self) -> None:
        contract = self._contract()
        contract["validation"]["reviewed_by"] = None
        self.assertIn("semantic_gate_without_reviewer", self._codes(contract))

    def test_premiere_xml_purpose_requires_exact_single_continuous_xml(self) -> None:
        contract = self._contract()
        contract["deliverable"]["artifacts"][0]["count"] = 2
        contract["deliverable"]["sequence_mode"] = "multiple_explicit"
        self.assertIn("deliverable_contract_mismatch", self._codes(contract))

    def test_runtime_and_schema_field_sets_match(self) -> None:
        schema = json.loads(
            (ROOT / "extension" / "schemas" / "video-edit-contract-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(schema["required"]), set(CONTRACT_FIELDS))
        properties = schema["properties"]
        self.assertEqual(set(properties["time_references"]["items"]["required"]), set(TIME_REFERENCE_FIELDS))
        self.assertEqual(set(properties["deliverable"]["required"]), set(DELIVERABLE_FIELDS))
        self.assertEqual(
            set(
                properties["deliverable"]["properties"]["artifacts"]["items"][
                    "required"
                ]
            ),
            set(ARTIFACT_FIELDS),
        )
        self.assertEqual(set(properties["calibration"]["required"]), set(CALIBRATION_FIELDS))
        self.assertEqual(set(properties["events"]["items"]["required"]), set(EVENT_FIELDS))
        self.assertEqual(set(properties["feedback"]["required"]), set(FEEDBACK_FIELDS))
        self.assertEqual(set(schema["$defs"]["preservation_list"]["items"]["required"]), set(PRESERVATION_FIELDS))
        self.assertEqual(set(properties["feedback"]["properties"]["defects"]["items"]["required"]), set(DEFECT_FIELDS))
        self.assertEqual(set(properties["state"]["required"]), set(STATE_FIELDS))
        self.assertEqual(set(properties["validation"]["required"]), set(VALIDATION_FIELDS))

    def test_cli_blocks_xml_before_writing_when_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-rule-gate-") as raw:
            temp_root = Path(raw)
            contract = self._contract()
            contract["events"][1]["depends_on"] = []
            contract_path = temp_root / "contract.json"
            output_path = temp_root / "blocked.xml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
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
                    "rule-gate",
                    "--timeline-json",
                    str(self.timeline_path),
                    "--edit-contract-json",
                    str(contract_path),
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output_path.exists())
            self.assertIn("migrate-v1", result.stderr)
            self.assertEqual(sorted(item.name for item in temp_root.iterdir()), ["contract.json"])

    def test_cli_requires_v2_migration_before_xml_generation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-missing-contract-") as raw:
            output_path = Path(raw) / "blocked.xml"
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
                    "--timeline-json",
                    str(self.timeline_path),
                    "--output",
                    str(output_path),
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output_path.exists())
            self.assertIn("migrate-v1", result.stderr)


if __name__ == "__main__":
    unittest.main()
