from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / ".agents"
    / "skills"
    / "coordinate-video-production"
    / "scripts"
    / "resolve_browser_profile.py"
)
SPEC = importlib.util.spec_from_file_location("resolve_browser_profile", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BrowserProfileResolutionTests(unittest.TestCase):
    def test_explicit_values_work_without_defaults_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            defaults = MODULE.load_workflow_defaults(Path(directory) / "missing.json")
            result = MODULE.resolve_browser_profile(defaults, profile_directory="Profile 7", required_origin="https://notebooklm.google.com")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["browser"]["profile_directory"], "Profile 7")

    def test_missing_values_are_reported_without_discarding_explicit_input(self) -> None:
        result = MODULE.resolve_browser_profile({}, profile_directory="Profile 7")
        self.assertEqual(result["status"], "needs_input")
        self.assertEqual(result["missing_fields"], ["required_origin"])

    def test_complete_alias_does_not_require_default_browser(self) -> None:
        result = MODULE.resolve_browser_profile({"profile_aliases": {"work": {"profile_directory": "Profile 7", "required_origin": "https://notebooklm.google.com"}}}, profile_alias="work")
        self.assertEqual(result["status"], "resolved")

    def test_unknown_alias_is_not_treated_as_missing_config(self) -> None:
        with self.assertRaises(MODULE.ResolutionError):
            MODULE.resolve_browser_profile({}, profile_alias="unknown")

    @classmethod
    def setUpClass(cls) -> None:
        cls.defaults = {
            "schema_version": "video-workflow-defaults-v1",
            "browser": {
                "profile_label": "Profile 4",
                "profile_directory": "Profile 4",
                "required_origin": "https://notebooklm.google.com",
            },
            "profile_aliases": {
                "메인프로필": {
                    "profile_label": "Main profile",
                    "profile_directory": "Default",
                }
            },
        }

    def test_loads_worktree_local_json_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "defaults.json"
            path.write_text(
                json.dumps(self.defaults, ensure_ascii=False),
                encoding="utf-8",
            )
            loaded = MODULE.load_workflow_defaults(path)
        self.assertEqual(loaded, self.defaults)

    def test_missing_input_uses_runtime_default(self) -> None:
        result = MODULE.resolve_browser_profile(self.defaults)
        self.assertEqual(result["source"], "runtime_default")
        self.assertEqual(
            result["browser"]["profile_directory"],
            "Profile 4",
        )

    def test_explicit_alias_uses_handoff_mapping(self) -> None:
        result = MODULE.resolve_browser_profile(
            self.defaults,
            profile_alias="메인프로필",
        )
        self.assertEqual(result["source"], "explicit_profile_alias")
        self.assertEqual(
            result["browser"]["profile_directory"],
            "Default",
        )

    def test_explicit_directory_wins_over_runtime_default(self) -> None:
        result = MODULE.resolve_browser_profile(
            self.defaults,
            profile_directory="Profile 31",
            profile_label="Temporary profile",
        )
        self.assertEqual(result["source"], "explicit_profile_directory")
        self.assertEqual(
            result["browser"]["profile_directory"],
            "Profile 31",
        )
        self.assertEqual(
            result["browser"]["profile_label"],
            "Temporary profile",
        )

    def test_conflicting_explicit_inputs_are_rejected(self) -> None:
        with self.assertRaises(MODULE.ResolutionError):
            MODULE.resolve_browser_profile(
                self.defaults,
                profile_directory="Profile 31",
                profile_alias="메인프로필",
            )


if __name__ == "__main__":
    unittest.main()
