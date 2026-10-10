from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / ".agents/skills/connect-chrome-profile/scripts/launch-profile.py"
SPEC = importlib.util.spec_from_file_location("launch_profile", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def runtime(cache, version, package="openai-bundled/chrome"):
    scripts = cache / package / version / "scripts"
    scripts.mkdir(parents=True)
    for name in ("open-chrome-window.js", "chromium-browser-diagnostics.mjs", "extension-ids.json"):
        (scripts / name).write_text("fixture")
    return scripts / "open-chrome-window.js"

class ChromeProfileLauncherTests(unittest.TestCase):
    def test_resolves_numeric_installed_version_without_skill_file_or_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            runtime(cache, "26.9.1")
            expected = runtime(cache, "26.1002.1")
            runtime(cache, "99.1.1", "openai-bundled/plugin-backup-X/chrome")
            self.assertEqual(MODULE.resolve_launcher(cache), expected)

    def test_missing_runtime_is_not_replaced_by_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            runtime(cache, "99.1.1", "openai-bundled/plugin-backup-X/chrome")
            with self.assertRaises(FileNotFoundError):
                MODULE.resolve_launcher(cache)

    def test_profile_env_overrides_inherited_selection_without_reading_profile(self):
        with patch.dict(MODULE.os.environ, {"CODEX_CHROMIUM_PREFERENCES_PATH": "wrong"}):
            env = MODULE.profile_environment("Profile 19", Path("not-existing-user-data"))
        self.assertEqual(env["CODEX_CHROME_PREFERENCES_PATH"], env["CODEX_CHROMIUM_PREFERENCES_PATH"])
        self.assertEqual(Path(env["CODEX_CHROME_PREFERENCES_PATH"]).parts[-2:], ("Profile 19", "Preferences"))
        for profile in ("", "..", "../Other", "C:/Other"):
            with self.assertRaises(ValueError):
                MODULE.validate_profile(profile)

    def test_dry_run_rejects_wrong_profile(self):
        output = subprocess.CompletedProcess([], 0, json.dumps({
            "profileDirectory": "Profile 2", "browserFamily": "chrome", "dryRun": True
        }), "")
        with patch.object(MODULE.subprocess, "run", return_value=output):
            with self.assertRaises(ValueError):
                MODULE.inspect_plan("node", Path("launcher"), "Profile 19", {})

    def test_launch_does_not_wait_or_inherit_output_pipes(self):
        with patch.object(MODULE.subprocess, "Popen") as launch, patch.object(MODULE.subprocess, "run") as run:
            MODULE.launch("node", Path("launcher"), {"profile": "fixture"})
        run.assert_not_called()
        args, kwargs = launch.call_args
        self.assertEqual(args[0], ["node", "launcher", "--json"])
        self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)

if __name__ == "__main__":
    unittest.main()
