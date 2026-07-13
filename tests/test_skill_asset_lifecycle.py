import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCHECK_PATH = ROOT / "tools" / "doccheck" / "check_docs.py"
DOCHECK_SPEC = importlib.util.spec_from_file_location("check_docs", DOCHECK_PATH)
DOCHECK = importlib.util.module_from_spec(DOCHECK_SPEC)
assert DOCHECK_SPEC and DOCHECK_SPEC.loader
sys.modules[DOCHECK_SPEC.name] = DOCHECK
DOCHECK_SPEC.loader.exec_module(DOCHECK)
STAGE_SKILLS = [
    "subtitle-cleanup",
    "dialogue-based-planning",
    "gameplay-video-analysis",
    "video-watch",
    "premiere-editing-export",
    "final-video-review",
]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8-sig")


class SkillAssetLifecycleTests(unittest.TestCase):
    def test_source_identity_survives_stage_four_through_eight(self):
        for name in STAGE_SKILLS:
            with self.subTest(skill=name):
                self.assertIn("source_id", read(f"skills/{name}/SKILL.md"))

    def test_analysis_edit_and_review_use_manifest_and_current_pointer(self):
        for name in ("gameplay-video-analysis", "premiere-editing-export", "final-video-review"):
            content = read(f"skills/{name}/SKILL.md")
            with self.subTest(skill=name):
                self.assertIn("source_asset_manifest", content)
                self.assertIn("CURRENT.json", content)

    def test_skills_do_not_recreate_workspace_or_temp_output_trees(self):
        for name in STAGE_SKILLS:
            content = read(f"skills/{name}/SKILL.md")
            with self.subTest(skill=name):
                self.assertNotIn("workspace/outputs", content)
                self.assertNotIn("workspace\\outputs", content)
                self.assertNotIn("--out-dir temp", content)

    def test_transcript_example_has_required_durable_output(self):
        lines = read("skills/video-watch/SKILL.md").splitlines()
        examples = [line for line in lines if "python" in line and "--detail transcript" in line]
        self.assertTrue(examples)
        self.assertTrue(all("--out-dir outputs/" in line for line in examples))


class PythonFileLifecycleTests(unittest.TestCase):
    def write(self, root, relative, content):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def findings_for(self, root, relative):
        findings = []
        DOCHECK.check_python_lifecycle(root, findings, [Path(relative)])
        return findings

    def test_allows_a_documented_new_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "tools/README.md", "`tools/needed_tool.py`\n")
            self.write(root, "tools/needed_tool.py", "print('needed')\n")
            self.assertEqual(self.findings_for(root, "tools/needed_tool.py"), [])

    def test_rejects_an_undocumented_new_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "tools/README.md", "# Tools\n")
            self.write(root, "tools/one_off.py", "print('one off')\n")
            findings = self.findings_for(root, "tools/one_off.py")
            self.assertTrue(any(item.level == "ERROR" and "등록되지 않았다" in item.message for item in findings))

    def test_task_scoped_script_requires_location_and_cleanup_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "outputs/07_edit_export/support/inspect_once.py"
            self.write(root, relative, "# Lifecycle: task-scoped\n# Cleanup: after review\n")
            findings = self.findings_for(root, relative)
            self.assertFalse(any(item.level == "ERROR" for item in findings))
            self.assertTrue(any(item.level == "WARN" for item in findings))


if __name__ == "__main__":
    unittest.main()
