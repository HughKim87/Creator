from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "extension" / "src"))

from learning import aggregate_measurements, audit_complexity, validate_measurement  # noqa: E402
from learning.metrics import MeasurementError  # noqa: E402


def row(job_id: str, actual: float, *, rework: int = 0) -> dict[str, object]:
    return {
        "job_id": job_id,
        "baseline_minutes": 60,
        "actual_minutes": actual,
        "user_revision_minutes": 5,
        "first_pass_accepted": rework == 0,
        "rework_count": rework,
        "automation_steps": 4,
        "manual_steps": 6,
        "approval_wait_minutes": 2,
        "retention": "aggregate_only",
    }


class LearningMetricsTests(unittest.TestCase):
    def test_three_fixture_rows_aggregate_without_per_job_output(self) -> None:
        aggregate = aggregate_measurements(
            [row("fixture-1", 40), row("fixture-2", 45), row("fixture-3", 50)]
        )
        self.assertEqual(aggregate["sample_count"], 3)
        self.assertEqual(aggregate["first_pass_acceptance_rate"], 1.0)
        self.assertEqual(aggregate["retention"], "aggregate_only")
        self.assertNotIn("job_ids", aggregate)
        self.assertEqual(audit_complexity(aggregate)["decision"], "retain")

    def test_complexity_candidate_and_insufficient_sample_are_not_rule_changes(self) -> None:
        candidate = aggregate_measurements(
            [row("fixture-1", 70, rework=1), row("fixture-2", 75, rework=1), row("fixture-3", 80, rework=2)]
        )
        self.assertEqual(audit_complexity(candidate)["decision"], "candidate")
        insufficient = aggregate_measurements([row("fixture-1", 40)])
        self.assertEqual(audit_complexity(insufficient)["decision"], "defer")

    def test_measurement_rejects_path_and_raw_content_retention(self) -> None:
        with self.assertRaises(MeasurementError):
            validate_measurement(row("extension/inputs/raw", 40))
        bad = row("fixture-1", 40)
        bad["retention"] = "per_job_report"
        with self.assertRaises(MeasurementError):
            validate_measurement(bad)
        extra = row("fixture-1", 40)
        extra["raw_transcript"] = "must not enter aggregate"
        with self.assertRaises(MeasurementError):
            validate_measurement(extra)


if __name__ == "__main__":
    unittest.main()
