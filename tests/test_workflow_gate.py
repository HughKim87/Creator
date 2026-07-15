import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "workflow_gate.py"
SPEC = importlib.util.spec_from_file_location("workflow_gate", MODULE_PATH)
WORKFLOW_GATE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = WORKFLOW_GATE
SPEC.loader.exec_module(WORKFLOW_GATE)


class WorkflowGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "docs").mkdir()
        (self.root / "outputs" / "07_edit_export").mkdir(parents=True)
        self.contract = {
            "schema_version": 1,
            "state_path": "outputs/WORKFLOW_STATE.json",
            "rule_registry_path": "outputs/WORKFLOW_RULE_REGISTRY.json",
            "edit_change_ledger_path": "outputs/07_edit_export/EDIT_CHANGE_LEDGER.json",
            "phase_order": [
                "data_analysis",
                "planning",
                "edit_calibration",
                "edit_full",
                "validation",
                "final",
            ],
            "transition_policy": {"require_immediate_predecessor_approval": True},
            "calibration_policy": {
                "required_positions": ["opening", "middle", "ending"],
                "agent_checks_before_user": [
                    "actual_av_playback",
                    "speech_boundaries",
                    "message_visible_without_review_metadata",
                ],
                "recommended_packages_shown_to_user": 1,
                "user_checkpoint_count_before_full_expansion": 1,
                "full_edit_before_user_checkpoint": False,
                "mp4_requires_current_request_authorization": True,
            },
            "revision_routing": {
                "message_or_viewer_promise": ["planning", "edit_calibration"],
                "rhythm_or_comedy": ["edit_calibration"],
                "local_cut_or_boundary": ["affected_ranges_only"],
                "source_fingerprint_or_target_audience_changed": ["data_analysis"],
            },
            "transitions": {
                "planning": {
                    "requires": ["phases.data_analysis.checks.ready"],
                    "rules_required_before": "planning",
                },
                "edit_calibration": {
                    "requires": [
                        "phases.data_analysis.approved_for_next_phase",
                        "phases.planning.approved_for_next_phase",
                        "phases.planning.checks.agent_red_team_reviewed",
                        "calibration_generation_allowed",
                    ],
                    "rules_required_before": "edit_calibration",
                },
                "edit_full": {
                    "requires": [
                        "phases.edit_calibration.approved_for_next_phase",
                        "phases.edit_calibration.checks.actual_av_playback_reviewed",
                        "phases.edit_calibration.checks.agent_self_reviewed",
                        "phases.edit_calibration.checks.user_direction_approved",
                        "generation_lock_released",
                    ],
                    "rules_required_before": "edit_full",
                },
            },
            "artifact_roles": [
                "calibration_candidate",
                "historical_failure_evidence",
                "approved_baseline",
                "current_deliverable",
            ],
            "required_rule_fields": [
                "id",
                "status",
                "scope",
                "owner_phase",
                "rule",
                "source",
                "enforcement",
                "required_before",
                "verification_status",
                "evidence",
            ],
            "verification_statuses": ["pending", "passed", "failed", "superseded"],
        }
        phases = {
            name: {"status": "blocked", "approved_for_next_phase": False, "checks": {}}
            for name in self.contract["phase_order"]
        }
        phases["data_analysis"]["checks"]["ready"] = False
        phases["planning"]["checks"]["agent_red_team_reviewed"] = False
        phases["planning"]["checks"]["user_direction_approved"] = False
        phases["edit_calibration"]["checks"].update(
            {
                "actual_av_playback_reviewed": False,
                "agent_self_reviewed": False,
                "user_direction_approved": False,
            }
        )
        self.state = {
            "schema_version": 1,
            "source_id": "sample",
            "mode": "workflow_recovery",
            "calibration_generation_allowed": False,
            "generation_lock_released": False,
            "approved_edit_baseline": None,
            "phases": phases,
        }
        self.registry = {
            "schema_version": 1,
            "source_id": "sample",
            "rules": [self.rule()],
        }
        self.ledger = {
            "schema_version": 1,
            "source_id": "sample",
            "approved_baseline": None,
            "generation_allowed": False,
        }
        self.current = {"artifact_role": "historical_failure_evidence"}
        self.write_all()

    @staticmethod
    def rule():
        return {
            "id": "WF-TEST",
            "status": "active",
            "scope": "global",
            "owner_phase": "data_analysis",
            "rule": "test rule",
            "source": "test",
            "enforcement": {"type": "automatic"},
            "required_before": "planning",
            "verification_status": "pending",
            "evidence": [],
        }

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def write_all(self):
        self.write_json("docs/WORKFLOW_CONTRACT.json", self.contract)
        self.write_json("outputs/WORKFLOW_STATE.json", self.state)
        self.write_json("outputs/WORKFLOW_RULE_REGISTRY.json", self.registry)
        self.write_json("outputs/07_edit_export/EDIT_CHANGE_LEDGER.json", self.ledger)
        self.write_json("outputs/07_edit_export/CURRENT.json", self.current)

    def test_closed_gate_is_coherent_but_transition_is_blocked(self):
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertTrue(result.coherent)
        self.assertTrue(result.blockers["planning"])

    def test_transition_opens_only_after_state_and_rule_evidence_pass(self):
        evidence = self.root / "outputs" / "evidence.txt"
        evidence.write_text("verified", encoding="utf-8")
        self.state["phases"]["data_analysis"]["checks"]["ready"] = True
        self.state["phases"]["data_analysis"]["approved_for_next_phase"] = True
        self.registry["rules"][0]["verification_status"] = "passed"
        self.registry["rules"][0]["evidence"] = ["outputs/evidence.txt"]
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertTrue(result.coherent)
        self.assertEqual(result.blockers["planning"], [])

    def test_current_deliverable_is_rejected_while_final_gate_is_closed(self):
        self.current["artifact_role"] = "current_deliverable"
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertFalse(result.coherent)
        self.assertTrue(any("current_deliverable" in error for error in result.errors))

    def test_rule_schema_failure_is_not_silently_ignored(self):
        del self.registry["rules"][0]["enforcement"]
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertFalse(result.coherent)
        self.assertTrue(any("missing fields" in error for error in result.errors))

    def test_generation_lock_requires_matching_ledger_and_baseline(self):
        self.state["generation_lock_released"] = True
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertFalse(result.coherent)
        self.assertTrue(any("generation lock" in error for error in result.errors))

    def pass_rule(self):
        evidence = self.root / "outputs" / "evidence.txt"
        evidence.write_text("verified", encoding="utf-8")
        self.registry["rules"][0]["verification_status"] = "passed"
        self.registry["rules"][0]["evidence"] = ["outputs/evidence.txt"]

    def test_ai_reviewed_provisional_plan_opens_only_calibration(self):
        self.pass_rule()
        self.state["phases"]["data_analysis"]["checks"]["ready"] = True
        self.state["phases"]["data_analysis"]["approved_for_next_phase"] = True
        self.state["phases"]["planning"]["approved_for_next_phase"] = True
        self.state["phases"]["planning"]["checks"]["agent_red_team_reviewed"] = True
        self.state["calibration_generation_allowed"] = True
        self.current["artifact_role"] = "calibration_candidate"
        self.write_all()

        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertTrue(result.coherent)
        self.assertEqual(result.blockers["edit_calibration"], [])
        self.assertTrue(result.blockers["edit_full"])

    def test_edit_full_requires_self_review_user_approval_and_full_lock(self):
        self.pass_rule()
        self.state["phases"]["data_analysis"]["checks"]["ready"] = True
        self.state["phases"]["data_analysis"]["approved_for_next_phase"] = True
        self.state["phases"]["planning"]["approved_for_next_phase"] = True
        self.state["phases"]["planning"]["checks"]["agent_red_team_reviewed"] = True
        self.state["phases"]["edit_calibration"]["approved_for_next_phase"] = True
        self.state["phases"]["edit_calibration"]["checks"].update(
            {
                "actual_av_playback_reviewed": True,
                "agent_self_reviewed": True,
                "user_direction_approved": True,
            }
        )
        self.state["calibration_generation_allowed"] = True
        self.write_all()
        blocked = WORKFLOW_GATE.audit_project(self.root)
        self.assertTrue(blocked.blockers["edit_full"])

        self.state["mode"] = "active"
        self.state["generation_lock_released"] = True
        self.state["approved_edit_baseline"] = "cal-v1"
        self.ledger["generation_allowed"] = True
        self.ledger["approved_baseline"] = "cal-v1"
        self.current["artifact_role"] = "approved_baseline"
        self.write_all()
        allowed = WORKFLOW_GATE.audit_project(self.root)
        self.assertTrue(allowed.coherent)
        self.assertEqual(allowed.blockers["edit_full"], [])

    def test_calibration_permission_must_be_boolean(self):
        self.state["calibration_generation_allowed"] = "yes"
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertFalse(result.coherent)
        self.assertTrue(any("calibration_generation_allowed" in error for error in result.errors))

    def test_transition_requires_immediate_predecessor_approval(self):
        self.pass_rule()
        self.state["phases"]["data_analysis"]["checks"]["ready"] = True
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertTrue(result.coherent)
        self.assertTrue(any("previous phase not approved" in item for item in result.blockers["planning"]))

    def test_invalid_calibration_policy_is_a_contract_error(self):
        self.contract["calibration_policy"]["recommended_packages_shown_to_user"] = 2
        self.write_all()
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertFalse(result.coherent)
        self.assertTrue(any("one recommended package" in error for error in result.errors))

    def test_edit_memory_prevents_rejected_revision_from_remaining_candidate(self):
        self.contract["edit_memory_view_path"] = "outputs/07_edit_export/edit_memory/CURRENT.json"
        self.state["phases"]["edit_calibration"]["status"] = "candidate_ready"
        self.state["phases"]["edit_calibration"]["candidate"] = {
            "memory_revision_id": "cal-r4",
            "artifact_role": "calibration_candidate",
        }
        memory = {
            "schema_version": 1,
            "revisions": [
                {
                    "revision_id": "cal-r4",
                    "source_id": "sample",
                    "status": "rejected",
                    "agent_actual_av_evaluation_count": 0,
                }
            ],
            "baselines": {
                "working": {"revision_id": None},
                "approved": {"revision_id": None},
            },
            "active_feedback": [{"event_id": "reject-r4"}],
        }
        self.write_all()
        self.write_json("outputs/07_edit_export/edit_memory/CURRENT.json", memory)
        result = WORKFLOW_GATE.audit_project(self.root)
        self.assertFalse(result.coherent)
        self.assertTrue(any("not rejected in workflow state" in error for error in result.errors))
        self.assertTrue(any("historical_failure_evidence" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
