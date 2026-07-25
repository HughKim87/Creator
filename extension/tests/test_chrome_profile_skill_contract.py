import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"
CONNECT = SKILLS / "connect-chrome-profile" / "SKILL.md"
COORDINATE = SKILLS / "coordinate-video-production" / "SKILL.md"
RESEARCH = SKILLS / "notebooklm-research-topic" / "SKILL.md"
VIDEO = SKILLS / "notebooklm-generate-video" / "SKILL.md"
JOB_FORMAT = (
    SKILLS
    / "coordinate-video-production"
    / "references"
    / "video-job-format.md"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ChromeProfileSkillContractTests(unittest.TestCase):
    def test_connector_uses_official_profile_recovery(self) -> None:
        text = read(CONNECT)
        required = [
            "chrome:control-chrome",
            'agent.documentation.get("chrome-troubleshooting")',
            "check-extension-installed.js --json",
            "CODEX_CHROME_PREFERENCES_PATH",
            "open-chrome-window.js --dry-run --json",
            "open-chrome-window.js",
            "2초",
            "한 번 통신에 성공한 뒤에는 해당 런타임에서 확장 감지를 반복하지 않는다",
            "공식 복구 절차가 끝나기 전에는 사용자에게 수동 프로필 전환을 요구",
            "explicit_tab_mention",
            "profile_targeted_launch",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertLess(
            text.index("첫 가벼운 연결 호출이 실패하면"),
            text.index("check-extension-installed.js --json"),
        )

    def test_dependent_skills_require_connector_before_browser_work(self) -> None:
        forbidden_manual_prompt = (
            "Chrome Profile 4를 열고 ChatGPT 확장 사이드 패널이 로드된 상태로 알려주세요"
        )
        for path in (COORDINATE, RESEARCH, VIDEO):
            text = read(path)
            with self.subTest(path=path):
                self.assertIn("$connect-chrome-profile", text)
                self.assertNotIn(forbidden_manual_prompt, text)

    def test_job_example_records_safe_profile_contract(self) -> None:
        text = read(JOB_FORMAT)
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        browser = payload["browser"]
        self.assertEqual(browser["surface"], "chrome")
        self.assertEqual(browser["profile_label"], "Profile 4")
        self.assertEqual(browser["profile_directory"], "Profile 4")
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
