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
        "skill": "",
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
        "browser": {
            "surface": "chrome",
            "profile_label": "Reusable test profile",
            "profile_directory": "Profile 19",
            "required_origin": "https://notebooklm.google.com",
            "connection_scope": "browser_runtime",
            "status": "connected",
            "verification_method": "profile_targeted_launch",
            "last_verified_at": "2026-07-26T00:00:00+09:00",
        },
        "paths": {
            "work_dir": "extension/work/2026-07-26-test",
            "input_dir": "extension/inputs/2026-07-26-test",
            "output_dir": "extension/outputs/2026-07-26-test",
        },
        "stages": {
            name: {
                **complete_stage(),
                "skill": MODULE.EXPECTED_SKILLS[name],
            }
            for name in MODULE.STAGE_ORDER
        },
        "next_action": "none",
        "updated_at": "2026-07-26T00:00:00+09:00",
    }


class VideoJobValidationTests(unittest.TestCase):
    def test_current_notebook_host_is_recognized_without_accepting_lookalikes(self) -> None:
        for host in ("notebooklm.google.com", "notebook.google.com"):
            self.assertTrue(MODULE.is_notebooklm_url(f"https://{host}/notebook/example"))
        for url in (
            "https://notebook.google.com.evil.test/notebook/example",
            "http://notebook.google.com/notebook/example",
            "https://notebook.google.com:8443/notebook/example",
        ):
            self.assertFalse(MODULE.is_notebooklm_url(url))

    def test_verified_service_migration_preserves_requested_origin(self) -> None:
        job = complete_job()
        job["browser"]["resolved_origin"] = "https://notebook.google.com"
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(job["browser"]["required_origin"], "https://notebooklm.google.com")
        job["browser"]["resolved_origin"] = "https://notebook.google.com.evil.test"
        result = MODULE.validate_video_job(job)
        self.assertIn("browser.resolved_origin is not an approved service origin", result["errors"])

    def test_complete_job_is_valid(self) -> None:
        result = MODULE.validate_video_job(complete_job())
        self.assertEqual(result["status"], "valid", result["errors"])

    def test_arbitrary_profile_directory_is_valid(self) -> None:
        job = complete_job()
        job["browser"]["profile_label"] = "Another account"
        job["browser"]["profile_directory"] = "Profile 27"
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "valid", result["errors"])

    def test_claude_in_chrome_device_is_a_supported_connection(self) -> None:
        job = complete_job()
        job["browser"]["verification_method"] = "claude_in_chrome_device"
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "valid", result["errors"])
        job["browser"]["verification_method"] = "builtin_browser"
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")

    def test_missing_profile_directory_is_invalid(self) -> None:
        job = complete_job()
        job["browser"]["profile_directory"] = ""
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "browser.profile_directory must be non-empty text",
            result["errors"],
        )

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
            "skill": MODULE.EXPECTED_SKILLS["video"],
            "artifacts": [],
            "validation": "",
            "note": "",
        }
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("captions must remain pending" in item for item in result["errors"]))

    def test_v2_rejects_recorded_worktree_that_differs_from_current_check(self) -> None:
        job = complete_job()
        job["schema_version"] = "video-job-v2"
        job["execution_context"] = {
            "worktree": {
                "root": "C:/workspace/ainotebook",
                "branch": "main",
                "expected_branch": "codex/ainotebook",
                "status": "valid",
                "checked_at": "2026-07-26T00:00:00+09:00",
            }
        }
        result = MODULE.validate_video_job(
            job,
            worktree_result={
                "status": "valid",
                "root": "C:/workspace/ainotebook",
                "branch": "codex/ainotebook",
                "expected_branch": "codex/ainotebook",
                "errors": [],
            },
        )
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(
            any("worktree.branch differs" in item for item in result["errors"])
        )

    def test_v3_requires_thumbnail_contract(self) -> None:
        job = complete_job()
        job["schema_version"] = "video-job-v3"
        job["execution_context"] = {
            "worktree": {
                "root": "C:/workspace/ainotebook",
                "branch": "codex/ainotebook",
                "expected_branch": "codex/ainotebook",
                "status": "valid",
                "checked_at": "2026-07-26T00:00:00+09:00",
            }
        }
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("thumbnail_contract must be an object", result["errors"])

    def test_v3_delegated_approval_requires_explicit_user_instruction(self) -> None:
        job = complete_job()
        job["schema_version"] = "video-job-v3"
        job["execution_context"] = {
            "worktree": {
                "root": "C:/workspace/ainotebook",
                "branch": "codex/ainotebook",
                "expected_branch": "codex/ainotebook",
                "status": "valid",
                "checked_at": "2026-07-26T00:00:00+09:00",
            }
        }
        job["thumbnail_contract"] = {
            "generation_mode": "one_shot_imagegen",
            "allow_local_text_composite": False,
            "approval_mode": "delegated_by_user",
            "instruction_source": "default",
        }
        result = MODULE.validate_video_job(job)
        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "delegated thumbnail approval requires explicit_user instruction",
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
