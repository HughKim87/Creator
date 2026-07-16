import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RootLayoutSmokeTests(unittest.TestCase):
    def test_stage_one_root_layout_exists(self):
        required = [
            "README.md",
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            "src/video_workflow/__init__.py",
            "src/video_workflow/cli.py",
            "src/video_workflow/doctor.py",
            "src/video_workflow/checks/execution.py",
            "src/video_workflow/checks/repository.py",
            "tests/unit/checks/test_repository.py",
            "tests/contract/test_process_exit_codes.py",
            ".githooks/pre-commit",
            ".github/workflows/ci.yml",
            "docs/rebuild/AGENT_EXECUTION_PLAN.md",
            "docs/rebuild/stage-01/AGENT_STAGE_01_TRUSTED_FOUNDATION.md",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_doctor_contract_requires_lock_file(self):
        from video_workflow.doctor import REQUIRED_PATHS

        self.assertIn("uv.lock", REQUIRED_PATHS)

    def test_design_documents_are_not_at_repository_root(self):
        misplaced = [
            "AGENT_EXECUTION_PLAN.md",
            "AGENT_STAGE_01_TRUSTED_FOUNDATION.md",
            "PROJECT_STRUCTURE_RESEARCH.md",
        ]
        self.assertEqual([path for path in misplaced if (ROOT / path).exists()], [])


if __name__ == "__main__":
    unittest.main()
