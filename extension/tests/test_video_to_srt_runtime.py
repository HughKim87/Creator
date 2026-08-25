from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "video-to-srt"
    / "scripts"
    / "transcribe_to_srt.py"
)
VALIDATE_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "video-to-srt"
    / "scripts"
    / "validate_srt.py"
)
SPEC = importlib.util.spec_from_file_location("transcribe_to_srt", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VALIDATE_SPEC = importlib.util.spec_from_file_location("validate_srt", VALIDATE_SCRIPT)
assert VALIDATE_SPEC and VALIDATE_SPEC.loader
VALIDATE_MODULE = importlib.util.module_from_spec(VALIDATE_SPEC)
VALIDATE_SPEC.loader.exec_module(VALIDATE_MODULE)
SKILL_ROOT = SCRIPT.parents[1]


class VideoToSrtRuntimeTests(unittest.TestCase):
    def test_default_runtime_paths_are_project_scoped_and_not_job_scoped(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.assertEqual(
            MODULE.DEFAULT_RUNTIME_DEPENDENCIES,
            project_root / "extension" / ".runtime" / "python-deps",
        )
        self.assertEqual(
            MODULE.DEFAULT_MODEL_DIR,
            project_root / "extension" / ".runtime" / "models" / "whisper",
        )
        self.assertNotIn("extension\\work", str(MODULE.DEFAULT_MODEL_DIR))
        self.assertNotIn("extension\\work", str(MODULE.DEFAULT_RUNTIME_DEPENDENCIES))

    def test_validator_reuses_the_same_project_runtime(self) -> None:
        self.assertEqual(
            VALIDATE_MODULE.DEFAULT_RUNTIME_DEPENDENCIES,
            MODULE.DEFAULT_RUNTIME_DEPENDENCIES,
        )

    def test_skill_references_do_not_retain_task_glossaries(self) -> None:
        references = SKILL_ROOT / "references"
        self.assertEqual([], sorted(path.name for path in references.glob("*.json")))
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        glossary_format = (references / "glossary-format.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("영상별 용어 사전은 `.agents/skills/video-to-srt/references/`에 두지 않는다", skill)
        self.assertIn("task glossary는 후속 소비자가 없으면 제거", glossary_format)

if __name__ == "__main__":
    unittest.main()
