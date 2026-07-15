import json
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt", "project tool wrappers are Windows-specific")
class ToolWrapperTests(unittest.TestCase):
    def run_cmd(self, command):
        return subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )

    def test_python_wrapper_resolves_a_working_python3(self):
        result = self.run_cmd(
            'call tools\\run_python.bat -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)"'
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_git_wrapper_handles_repository_safe_directory(self):
        result = self.run_cmd("call tools\\git_project.bat rev-parse --show-toplevel")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            Path(result.stdout.strip()).resolve(),
            ROOT.resolve(),
        )

    def test_preflight_returns_only_existing_scan_roots(self):
        script = ROOT / "tools" / "project_preflight.ps1"
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-Json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
            errors="replace",
            check=False,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["missing_required"], [])
        self.assertTrue(payload["scan_roots"])
        for relative in payload["scan_roots"]:
            self.assertTrue((ROOT / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
