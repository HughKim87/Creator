import unittest
from pathlib import Path
from unittest.mock import patch

from video_workflow.checks.repository import (
    forbidden_tracked_paths,
    git_tracked_paths,
    has_forbidden_segment,
)


class RepositoryBoundaryTests(unittest.TestCase):
    def test_rejects_forbidden_segment_at_any_depth(self):
        self.assertTrue(has_forbidden_segment("inputs/example.bin"))
        self.assertTrue(has_forbidden_segment("nested/outputs/result.json"))
        self.assertTrue(has_forbidden_segment(r"nested\inputs\example.bin"))

    def test_allows_framework_and_stage_document_paths(self):
        self.assertFalse(has_forbidden_segment("src/video_workflow/cli.py"))
        self.assertFalse(has_forbidden_segment("docs/rebuild/stage-00/STAGE_REPORT.md"))

    def test_reports_only_forbidden_tracked_paths(self):
        paths = [
            "src/video_workflow/cli.py",
            "docs/rebuild/stage-00/STAGE_REPORT.md",
            "nested/outputs/result.json",
        ]
        self.assertEqual(forbidden_tracked_paths(paths), ["nested/outputs/result.json"])

    def test_git_inventory_does_not_use_recursive_filesystem_discovery(self):
        root = Path(__file__).resolve().parents[3]
        with patch.object(Path, "rglob", side_effect=AssertionError("rglob must not be used")):
            paths, result = git_tracked_paths(root)
        self.assertEqual(result.returncode, 0)
        self.assertIsInstance(paths, list)


if __name__ == "__main__":
    unittest.main()
