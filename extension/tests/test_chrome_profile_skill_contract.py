import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"
CONNECT = SKILLS / "connect-chrome-profile" / "SKILL.md"
CONNECT_AGENT = SKILLS / "connect-chrome-profile" / "agents" / "openai.yaml"
COORDINATE = SKILLS / "coordinate-video-production" / "SKILL.md"
RESEARCH = SKILLS / "notebooklm-research-topic" / "SKILL.md"
RESEARCH_AGENT = SKILLS / "notebooklm-research-topic" / "agents" / "openai.yaml"
VIDEO = SKILLS / "notebooklm-generate-video" / "SKILL.md"
VIDEO_AGENT = SKILLS / "notebooklm-generate-video" / "agents" / "openai.yaml"
JOB_FORMAT = (
    SKILLS
    / "coordinate-video-production"
    / "references"
    / "video-job-format.md"
)
GITIGNORE = ROOT / ".gitignore"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ChromeProfileSkillContractTests(unittest.TestCase):
    def test_connector_requires_caller_owned_profile_and_origin(self) -> None:
        text = read(CONNECT)
        self.assertIn("`profile_directory`: 필수", text)
        self.assertIn("`target_origin`: 필수", text)
        self.assertIn("이 스킬에는 프로필과 origin 기본값이 없다", text)
        self.assertNotIn("Profile 4", text)
        self.assertNotIn("Profile 4", read(CONNECT_AGENT))

    def test_connector_uses_exact_profile_launch_delta(self) -> None:
        text = read(CONNECT)
        required = [
            "chrome:control-chrome",
            "CODEX_CHROME_PREFERENCES_PATH",
            "open-chrome-window.js --dry-run --json",
            "select-profile-delta.mjs",
            'agent.browsers.get(descriptor.id)',
            'discoveryMode: "post_launch_initial"',
            'discoveryMode: "baseline_delta"',
            "profile_launch_delta_not_found",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_coordinate_owns_per_job_profile_value(self) -> None:
        text = read(COORDINATE)
        self.assertIn("프로필 설정은 두 계층만 사용한다", text)
        self.assertIn("browser.profile_directory", text)
        self.assertIn("resolve_browser_profile.py", text)
        self.assertIn("프로필 directory나 alias가 있으면 그 입력을 사용", text)
        self.assertIn("worktree-local 기본값을 자동 사용", text)
        self.assertIn("SESSION_HANDOFF.md", text)
        self.assertIn("프로필 설정에 사용하거나 수정하지 않는다", text)
        self.assertNotIn("Profile 4", text)

    def test_worktree_runtime_defaults_are_git_ignored(self) -> None:
        text = read(GITIGNORE)
        self.assertIn("/extension/.runtime/", text)

    def test_dependent_skills_forward_job_values_without_fallback(self) -> None:
        for path in (RESEARCH, VIDEO):
            text = read(path)
            with self.subTest(path=path):
                self.assertIn("$connect-chrome-profile", text)
                self.assertIn("browser.profile_directory", text)
                self.assertIn("browser.required_origin", text)
                self.assertIn("기본값을 만들지 말고", text)
                self.assertNotIn("Profile 4", text)
        for path in (RESEARCH_AGENT, VIDEO_AGENT):
            with self.subTest(path=path):
                self.assertNotIn("Profile 4", read(path))

    def test_job_example_records_parameterized_profile_contract(self) -> None:
        text = read(JOB_FORMAT)
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        browser = payload["browser"]
        self.assertEqual(browser["surface"], "chrome")
        self.assertEqual(browser["profile_label"], "<optional-profile-label>")
        self.assertEqual(
            browser["profile_directory"],
            "<required-profile-directory>",
        )
        self.assertEqual(browser["connection_scope"], "browser_runtime")
        self.assertEqual(browser["status"], "needs_connection")
        self.assertEqual(browser["verification_method"], "")

    def test_connector_does_not_persist_sensitive_connection_identity(self) -> None:
        match = re.search(
            r"```json\s*(\{.*?\})\s*```",
            read(JOB_FORMAT),
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        browser_block = json.loads(match.group(1))["browser"]
        self.assertNotIn("browser_id", browser_block)
        self.assertNotIn("extension_instance_id", browser_block)
        self.assertNotIn("profile_path", browser_block)


if __name__ == "__main__":
    unittest.main()
