import importlib.util
import re
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "guard" / "agent_guard.py"
SPEC = importlib.util.spec_from_file_location("agent_guard", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class AgentGuardTests(unittest.TestCase):
    def denied_bash(self, command):
        return any(re.search(pattern, command) for pattern, _ in MODULE.BASH_DENY)

    def denied_path(self, path):
        return any(re.search(pattern, path) for pattern, _ in MODULE.PATH_DENY)

    def test_rejects_root_and_nested_temp_outputs(self):
        self.assertTrue(self.denied_bash("python watch.py --out-dir temp/video-watch"))
        self.assertTrue(self.denied_bash("python watch.py --output outputs/temp/frames"))
        self.assertTrue(self.denied_bash("python watch.py --out-dir workspace/outputs/frames"))
        self.assertTrue(self.denied_bash("python task.py --out-dir runs/source/support"))

    def test_allows_durable_output(self):
        self.assertFalse(self.denied_bash("python watch.py --out-dir outputs/06_analysis/source_assets"))

    def test_rejects_temp_and_backup_writes(self):
        self.assertTrue(self.denied_path("temp/frames/a.jpg"))
        self.assertTrue(self.denied_path("outputs/backups/file.md"))
        self.assertTrue(self.denied_path("SESSION_HANDOFF.md.bak_1"))
        self.assertTrue(self.denied_path("workspace/outputs/frames/a.jpg"))
        self.assertTrue(self.denied_path("runs/source/support/task.py"))


if __name__ == "__main__":
    unittest.main()
