import importlib.util
import json
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "edit_memory.py"
SPEC = importlib.util.spec_from_file_location("edit_memory", MODULE_PATH)
EDIT_MEMORY = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = EDIT_MEMORY
SPEC.loader.exec_module(EDIT_MEMORY)


class EditMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db_path = Path(self.temporary.name) / "memory.sqlite3"
        self.connection = EDIT_MEMORY.connect(self.db_path)
        self.addCleanup(self.connection.close)
        EDIT_MEMORY.initialize(self.connection)

    def event(self, event_id, event_type, aggregate_type, aggregate_id, payload, revision_id=None, **extra):
        value = {
            "event_id": event_id,
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "occurred_at": "2026-07-15T10:00:00+00:00",
            "payload": payload,
        }
        if revision_id is not None:
            value["revision_id"] = revision_id
        value.update(extra)
        return value

    def base_events(self):
        return [
            self.event(
                "e-revision",
                "revision.created",
                "revision",
                "r1",
                {"source_id": "source", "parent_revision_id": None, "hypothesis": "test", "status": "candidate"},
                revision_id="r1",
            ),
            self.event(
                "e-node-a",
                "timeline.node_added",
                "timeline_node",
                "a",
                {"sequence_name": "hook", "position": 1, "source_in": 1.0, "source_out": 2.0, "label": "A", "role": "setup"},
                revision_id="r1",
            ),
            self.event(
                "e-node-b",
                "timeline.node_added",
                "timeline_node",
                "b",
                {"sequence_name": "hook", "position": 2, "source_in": 3.0, "source_out": 4.0, "label": "B", "role": "reaction"},
                revision_id="r1",
            ),
            self.event(
                "e-edge",
                "timeline.edge_added",
                "timeline_edge",
                "a_to_b",
                {"from_node_id": "a", "to_node_id": "b", "continuity_risk": 0.4, "audio_transition": "L-cut"},
                revision_id="r1",
            ),
            self.event(
                "e-baseline",
                "baseline.set",
                "baseline",
                "working",
                {"name": "working", "revision_id": "r1", "note": "agent-selected working state"},
            ),
        ]

    def test_applies_events_and_builds_working_snapshot(self):
        result = EDIT_MEMORY.apply_batch(self.connection, {"schema_version": 1, "events": self.base_events()})
        self.assertEqual(result, {"applied": 5, "skipped": 0})
        state = EDIT_MEMORY.snapshot(self.connection)
        self.assertEqual(state["event_count"], 5)
        self.assertEqual(state["baselines"]["working"]["revision_id"], "r1")
        self.assertEqual(state["revisions"][0]["node_count"], 2)
        self.assertEqual(state["revisions"][0]["edge_count"], 1)

    def test_reapplying_identical_events_is_idempotent(self):
        batch = {"schema_version": 1, "events": self.base_events()}
        EDIT_MEMORY.apply_batch(self.connection, batch)
        result = EDIT_MEMORY.apply_batch(self.connection, batch)
        self.assertEqual(result, {"applied": 0, "skipped": 5})

    def test_duplicate_event_id_with_changed_payload_is_rejected(self):
        batch = {"schema_version": 1, "events": self.base_events()}
        EDIT_MEMORY.apply_batch(self.connection, batch)
        changed = self.base_events()[0]
        changed["payload"]["hypothesis"] = "different"
        with self.assertRaises(EDIT_MEMORY.EditMemoryError):
            EDIT_MEMORY.apply_batch(self.connection, {"schema_version": 1, "events": [changed]})

    def test_failed_edge_rolls_back_whole_batch(self):
        events = self.base_events()[:1]
        events.append(
            self.event(
                "e-bad-edge",
                "timeline.edge_added",
                "timeline_edge",
                "missing_to_missing",
                {"from_node_id": "missing", "to_node_id": "also_missing"},
                revision_id="r1",
            )
        )
        with self.assertRaises(EDIT_MEMORY.EditMemoryError):
            EDIT_MEMORY.apply_batch(self.connection, {"schema_version": 1, "events": events})
        self.assertEqual(EDIT_MEMORY.snapshot(self.connection)["event_count"], 0)

    def test_superseded_feedback_leaves_only_latest_memory_active(self):
        EDIT_MEMORY.apply_batch(
            self.connection, {"schema_version": 1, "events": self.base_events()[:1]}
        )
        first = self.event(
            "feedback-1",
            "feedback.recorded",
            "feedback",
            "hook-cut",
            {"target_type": "timeline_node", "target_id": "a", "verdict": "reject", "dimension": "speech_continuity", "severity": "high", "scope": "hook", "observation": "speech was cut", "persists_until": "superseded_by_confirmed_fix"},
            revision_id="r1",
        )
        second = self.event(
            "feedback-2",
            "feedback.recorded",
            "feedback",
            "hook-cut-fixed",
            {"target_type": "timeline_node", "target_id": "a", "verdict": "resolved", "dimension": "speech_continuity", "severity": "high", "scope": "hook", "observation": "complete utterance retained", "persists_until": "superseded_by_new_evidence"},
            revision_id="r1",
            supersedes_event_id="feedback-1",
        )
        EDIT_MEMORY.apply_batch(self.connection, {"schema_version": 1, "events": [first, second]})
        active = EDIT_MEMORY.active_feedback(self.connection)
        self.assertEqual([item["event_id"] for item in active], ["feedback-2"])

    def test_rejected_revision_cannot_be_working_baseline(self):
        rejected = self.base_events()[0]
        rejected["payload"]["status"] = "rejected"
        baseline = self.base_events()[-1]
        with self.assertRaises(EDIT_MEMORY.EditMemoryError):
            EDIT_MEMORY.apply_batch(
                self.connection, {"schema_version": 1, "events": [rejected, baseline]}
            )

    def test_validation_reports_missing_observation_without_blocking_memory(self):
        EDIT_MEMORY.apply_batch(
            self.connection, {"schema_version": 1, "events": self.base_events()}
        )
        result = EDIT_MEMORY.validate(self.connection)
        self.assertTrue(result["ok"])
        self.assertIn("approved baseline is not selected", result["warnings"])
        self.assertIn("revision has no actual A/V observation: r1", result["warnings"])
        self.assertIn("revision has no agent actual A/V observation: r1", result["warnings"])

    def test_json_output_handles_unicode_on_text_stream(self):
        stream = StringIO()
        EDIT_MEMORY.print_json({"range": "2336.323–2341.940", "message": "발화 보존"}, stream)
        parsed = json.loads(stream.getvalue())
        self.assertEqual(parsed["message"], "발화 보존")


if __name__ == "__main__":
    unittest.main()
