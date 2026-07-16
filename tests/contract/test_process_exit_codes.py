import sys
import tempfile
import unittest
from pathlib import Path

from video_workflow.checks.execution import run_process


class ProcessExitCodeContractTests(unittest.TestCase):
    def test_preserves_child_exit_code_seven(self):
        result = run_process([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(result.returncode, 7)

    def test_missing_executable_is_127(self):
        result = run_process(["definitely-missing-video-workflow-command"])
        self.assertEqual(result.returncode, 127)

    def test_timeout_is_124(self):
        result = run_process([sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.01)
        self.assertEqual(result.returncode, 124)

    def test_korean_space_working_directory(self):
        with tempfile.TemporaryDirectory(prefix="한글 경로 ") as directory:
            result = run_process(
                [sys.executable, "-c", "from pathlib import Path; assert Path.cwd().is_dir()"],
                cwd=Path(directory),
            )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
