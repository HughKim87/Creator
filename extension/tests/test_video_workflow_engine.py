from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "extension" / "src"))

from video_workflow import (  # noqa: E402
    ExternalAgentAdapter,
    LocalSyntheticAdapter,
    SyntheticArtifactStore,
    WorkflowEngine,
)


VALIDATOR_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "coordinate-video-production"
    / "scripts"
    / "validate_video_job.py"
)
VALIDATOR_SPEC = importlib.util.spec_from_file_location("m4_video_job_validator", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR_MODULE = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR_MODULE)


STAGES = (
    "research",
    "video",
    "captions",
    "title_thumbnail",
    "upload_package",
)
SKILLS = {
    "research": "notebooklm-research-topic",
    "video": "notebooklm-generate-video",
    "captions": "video-to-srt",
    "title_thumbnail": "youtube-title-thumbnail",
    "upload_package": "prepare-youtube-upload",
}


def job_fixture() -> dict[str, object]:
    return {
        "schema_version": "video-job-v3",
        "job_id": "synthetic-m4",
        "topic": "synthetic workflow",
        "status": "active",
        "browser": {
            "surface": "chrome",
            "profile_label": "synthetic",
            "profile_directory": "Profile Synthetic",
            "required_origin": "https://notebooklm.google.com",
            "status": "connected",
            "verification_method": "profile_targeted_launch",
            "last_verified_at": "2026-07-29T00:00:00+09:00",
        },
        "paths": {
            "work_dir": "extension/work/synthetic-m4",
            "input_dir": "extension/inputs/synthetic-m4",
            "output_dir": "extension/outputs/synthetic-m4",
        },
        "execution_context": {
            "worktree": {
                "root": "C:/workspace/synthetic",
                "branch": "codex/synthetic",
                "expected_branch": "codex/synthetic",
                "status": "valid",
                "checked_at": "2026-07-29T00:00:00+09:00",
            }
        },
        "thumbnail_contract": {
            "approval_mode": "review_gated",
            "generation_mode": "one_shot_imagegen",
            "allow_local_text_composite": False,
            "instruction_source": "explicit_user",
        },
        "stages": {
            name: {
                "status": "pending",
                "skill": SKILLS[name],
                "artifacts": [],
                "validation": "",
                "note": "",
            }
            for name in STAGES
        },
        "next_action": "start research",
        "updated_at": "2026-07-29T00:00:00+09:00",
    }


class CountingAdapter(LocalSyntheticAdapter):
    def __init__(self, store: SyntheticArtifactStore) -> None:
        super().__init__(store)
        self.execute_count = 0

    def execute(self, stage: str, job: dict[str, object]) -> dict[str, object]:
        self.execute_count += 1
        return super().execute(stage, job)


class VideoWorkflowEngineTests(unittest.TestCase):
    def local_engine(self) -> tuple[WorkflowEngine, SyntheticArtifactStore]:
        store = SyntheticArtifactStore()
        adapter = LocalSyntheticAdapter(store)
        return (
            WorkflowEngine(
                job_fixture(),
                adapters={name: adapter for name in STAGES},
                artifact_store=store,
                validator=VALIDATOR_MODULE.validate_video_job,
            ),
            store,
        )

    def test_synthetic_pipeline_stops_for_user_approval_then_completes(self) -> None:
        engine, _ = self.local_engine()
        waiting = engine.run_until_boundary()
        self.assertEqual(waiting["status"], "needs_user")
        self.assertEqual(waiting["step"]["stage"], "title_thumbnail")
        self.assertEqual(waiting["job"]["stages"]["captions"]["status"], "complete")
        self.assertEqual(waiting["job"]["stages"]["title_thumbnail"]["status"], "needs_user")

        engine.record_approval(
            "title_thumbnail",
            {"status": "approved", "method": "explicit_user"},
        )
        finished = engine.run_until_boundary()
        self.assertEqual(finished["status"], "complete")
        self.assertEqual(finished["job"]["status"], "complete")
        self.assertEqual(finished["job"]["next_action"], "none")
        self.assertTrue(all(finished["job"]["stages"][name]["status"] == "complete" for name in STAGES))

    def test_external_unavailable_is_a_boundary_not_success(self) -> None:
        engine = WorkflowEngine(
            job_fixture(),
            adapters={"research": ExternalAgentAdapter()},
        )
        result = engine.run_next()
        self.assertEqual(result["result"]["status"], "unavailable")
        self.assertEqual(result["job"]["status"], "blocked")
        self.assertEqual(result["job"]["stages"]["research"]["status"], "blocked")

    def test_resume_rechecks_hash_without_reexecuting_verified_stage(self) -> None:
        store = SyntheticArtifactStore()
        adapter = CountingAdapter(store)
        reference = "fixture://video-workflow/video"
        fingerprint = store.put(reference, "already generated")
        job = job_fixture()
        job["stages"]["research"]["status"] = "complete"
        job["stages"]["research"]["artifacts"] = ["fixture://research"]
        job["stages"]["video"] = {
            "status": "in_progress",
            "skill": SKILLS["video"],
            "artifacts": [reference],
            "artifact_hashes": {reference: fingerprint},
            "validation": "",
            "note": "interrupted after generation",
        }
        store.put("fixture://research", "research")
        engine = WorkflowEngine(
            job,
            adapters={"video": adapter},
            artifact_store=store,
        )
        preflight = engine.preflight()
        self.assertEqual(preflight["mode"], "resume_verified")
        result = engine.run_next()
        self.assertEqual(result["result"]["status"], "verified")
        self.assertEqual(adapter.execute_count, 0)
        self.assertEqual(result["job"]["stages"]["video"]["status"], "complete")

    def test_resume_hash_drift_blocks_before_adapter(self) -> None:
        store = SyntheticArtifactStore()
        reference = "fixture://video-workflow/captions"
        store.put(reference, "new content")
        job = job_fixture()
        job["stages"]["research"]["status"] = "complete"
        job["stages"]["video"]["status"] = "complete"
        job["stages"]["captions"] = {
            "status": "in_progress",
            "skill": SKILLS["captions"],
            "artifacts": [reference],
            "artifact_hashes": {reference: "sha256:" + "0" * 64},
            "validation": "",
            "note": "interrupted",
        }
        engine = WorkflowEngine(job, artifact_store=store)
        result = engine.preflight()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("fingerprint", result["reason"])

    def test_invalid_job_validator_blocks_selection(self) -> None:
        engine = WorkflowEngine(
            job_fixture(),
            validator=lambda job: {"status": "invalid", "errors": ["fixture invalid"]},
        )
        result = engine.next_step()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["errors"], ["fixture invalid"])


if __name__ == "__main__":
    unittest.main()
