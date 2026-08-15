from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "core" / "src"))

from file_data import (  # noqa: E402
    DesignContractError,
    DesignInvalidatedError,
    DesignRequiredError,
    WorkStateService,
    compare_request_contract,
    compute_design_fingerprint,
    validate_execution_contract,
)
from test_support import TEST_WRITE_CAPABILITY  # noqa: E402


WORK_ID = "123e4567-e89b-42d3-a456-426614174021"


def base_request() -> dict[str, object]:
    return {
        "desired_outcome": "complete the requested work",
        "authorized_actions": ["edit project files"],
        "excluded_scope": ["inputs", "outputs"],
        "input_refs": ["fixture://neutral"],
        "protection_boundaries": ["inputs", "outputs"],
        "required_decisions": [],
        "verification_levels": ["unit", "structure"],
    }


class ExecutionContractTests(unittest.TestCase):
    def test_legacy_request_and_non_persistent_tiers_have_no_design_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execution-tier-") as raw_root:
            root = Path(raw_root)
            self.assertIsNone(validate_execution_contract(root, None))
            self.assertEqual(
                validate_execution_contract(root, {"tier": "quick"}),
                {"tier": "quick", "phase_id": None, "design_ref": None, "design_fingerprint": None},
            )
            self.assertEqual(
                validate_execution_contract(root, {"tier": "standard"})["tier"],
                "standard",
            )
            with self.assertRaises(DesignContractError):
                validate_execution_contract(
                    root,
                    {"tier": "quick", "phase_id": "M2"},
                )

    def test_controlled_work_requires_matching_design_and_rejects_stale_design(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execution-controlled-") as raw_root:
            root = Path(raw_root)
            design = root / "extension" / "work" / "M2.md"
            design.parent.mkdir(parents=True)
            design.write_text("phase: M2\nlifecycle: ready\n", encoding="utf-8")
            design_ref = "extension/work/M2.md"
            fingerprint = compute_design_fingerprint(root, design_ref)
            execution = {
                "tier": "controlled",
                "phase_id": "M2",
                "design_ref": design_ref,
                "design_fingerprint": fingerprint,
            }
            service = WorkStateService(
                root,
                _write_capability=TEST_WRITE_CAPABILITY,
            )
            service.initialize()
            request = base_request()
            request["execution"] = execution
            requested = service.create_work(
                request,
                actor="user",
                next_action="start M2",
                work_id=WORK_ID,
                timestamp=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
            )
            self.assertEqual(requested["payload"]["request"]["execution"], execution)
            design.write_text("phase: M2\nlifecycle: invalidated\n", encoding="utf-8")
            events_before, _ = service.store.list_events("work_events")
            with self.assertRaises(DesignInvalidatedError):
                service.transition(
                    WORK_ID,
                    expected_state_hash=requested["content_hash"],
                    actor="agent",
                    action="start",
                    outcome="success",
                    to_status="in_progress",
                    next_action="repair design",
                    timestamp=datetime(2026, 7, 29, 3, 1, tzinfo=UTC),
                )
            events_after, _ = service.store.list_events("work_events")
            self.assertEqual(events_after, events_before)

    def test_controlled_work_without_design_is_rejected_before_event_append(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execution-required-") as raw_root:
            root = Path(raw_root)
            service = WorkStateService(root, _write_capability=TEST_WRITE_CAPABILITY)
            service.initialize()
            request = base_request()
            request["execution"] = {"tier": "controlled"}
            with self.assertRaises(DesignRequiredError):
                service.create_work(
                    request,
                    actor="user",
                    next_action="start M2",
                    work_id=WORK_ID,
                )
            events, _ = service.store.list_events("work_events")
            self.assertEqual(events, [])

    def test_request_correction_requires_reapproval(self) -> None:
        previous = base_request()
        current = base_request()
        current["desired_outcome"] = "changed outcome"
        result = compare_request_contract(previous, current)
        self.assertTrue(result["invalidated"])
        self.assertTrue(result["reapproval_required"])
        self.assertEqual(result["changed_fields"], ["desired_outcome"])


if __name__ == "__main__":
    unittest.main()
