from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "coordinate-video-production"
    / "scripts"
    / "validate_video_job.py"
)
SPEC = importlib.util.spec_from_file_location("validate_video_job", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def complete_stage() -> dict[str, object]:
    return {
        "status": "complete",
        "skill": "test",
        "artifacts": ["artifact"],
        "validation": "verified",
        "note": "",
    }


def complete_job() -> dict[str, object]:
    return {
        "schema_version": "video-job-v1",
        "job_id": "2026-07-26-test",
        "topic": "test topic",
        "status": "complete",
        "stages": {
            name: complete_stage()
            for name in MODULE.STAGE_ORDER
        },
        "next_action": "none",
        "updated_at": "2026-07-26T00:00:00+09:00",
    }


class VideoJobValidationTests(unittest.TestCase):
    def test_complete_job_is_valid(self) -> None:
        result = MODULE.validate_video_job(complete_job())
        self.assertEqual(result["status"], "valid", result["errors"])

    def test_complete_job_cannot_leave_manual_upload_as_next_action(self) -> None:
        job = complete_job()
        job["next_action"] = "Ask the user to confirm the YouTube upload"
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "complete jobs must set next_action to none",
            result["errors"],
        )

    def test_unknown_stage_is_invalid(self) -> None:
        job = complete_job()
        job["stages"]["upload_package_unused"] = complete_stage()
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("unexpected stages" in item for item in result["errors"]))

    def test_complete_stage_requires_artifacts_and_validation(self) -> None:
        job = complete_job()
        job["stages"]["captions"]["artifacts"] = []
        job["stages"]["captions"]["validation"] = ""
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("captions.artifacts" in item for item in result["errors"]))
        self.assertTrue(any("captions.validation" in item for item in result["errors"]))

    def test_later_stage_cannot_start_before_prior_completion(self) -> None:
        job = complete_job()
        job["status"] = "active"
        job["stages"]["video"] = {
            "status": "pending",
            "skill": "test",
            "artifacts": [],
            "validation": "",
            "note": "",
        }
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("captions must remain pending" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
