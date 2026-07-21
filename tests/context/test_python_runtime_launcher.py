from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "tools/runtime/run_python.cmd"
SYSTEM_ROOT = Path(os.environ.get("SystemRoot", r"C:\Windows"))
COMMAND_PROMPT = SYSTEM_ROOT / "System32/cmd.exe"


@unittest.skipUnless(COMMAND_PROMPT.exists(), "Windows command prompt is required for the project launcher test")
class PythonRuntimeLauncherTests(unittest.TestCase):
    def run_launcher(self, project_python: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = ""
        environment["PROJECT_PYTHON"] = project_python
        return subprocess.run(
            [str(LAUNCHER), *arguments],
            cwd=ROOT,
            env=environment,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_explicit_runtime_works_with_empty_path(self) -> None:
        completed = self.run_launcher(
            sys.executable,
            "-c",
            "import sys; print('launcher-ok'); print(sys.executable)",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.splitlines()[0], "launcher-ok")
        self.assertEqual(Path(completed.stdout.splitlines()[1]).resolve(), Path(sys.executable).resolve())

    def test_module_option_is_forwarded_without_powershell_binding(self) -> None:
        completed = self.run_launcher(sys.executable, "-m", "site", "--user-site")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout.strip())

    def test_invalid_explicit_runtime_fails_without_path_fallback(self) -> None:
        missing = ROOT / "temp/does-not-exist/python.exe"
        completed = self.run_launcher(str(missing), "--version")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("PROJECT_PYTHON does not point to a working Python executable", completed.stderr)

    def test_explicit_runtime_without_required_capability_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "fake-python.cmd"
            fake.write_text(
                "@echo off\n"
                "echo %* | \"%SystemRoot%\\System32\\findstr.exe\" /C:\"tomllib\" >nul\n"
                "if not errorlevel 1 exit /b 1\n"
                "exit /b 0\n",
                encoding="ascii",
            )

            completed = self.run_launcher(str(fake), "--version")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("Python 3.11+ and tomllib", completed.stderr)


if __name__ == "__main__":
    unittest.main()
