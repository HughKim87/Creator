from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "SESSION_HANDOFF.md"
STATE_DIR = ROOT / "state"
REQUIRED_SECTIONS = (
    "현재 단계",
    "직전 게이트",
    "승인 상태",
    "차단",
    "알려진 위험",
    "첫 다음 행동",
)


def _routes(text: str) -> dict[str, str]:
    return dict(re.findall(r"(?m)^\| `([^`]+)` \| `(state/[^`]+\.md)` \|$", text))


class WorktreeStateFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = ROUTER.read_text(encoding="utf-8")
        self.routes = _routes(self.router)

    def test_router_lists_unique_branch_state_files(self) -> None:
        self.assertIn("main", self.routes)
        self.assertEqual(len(self.routes), len(set(self.routes.values())))

    def test_every_existing_state_file_is_routed(self) -> None:
        routed = set(self.routes.values())
        for path in sorted(STATE_DIR.glob("*.md")):
            with self.subTest(path=path.name):
                self.assertIn(path.relative_to(ROOT).as_posix(), routed)

    def test_existing_state_files_have_core_sections(self) -> None:
        for path in sorted(STATE_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for section in REQUIRED_SECTIONS:
                    self.assertRegex(text, rf"(?m)^## {re.escape(section)}\s*$")


if __name__ == "__main__":
    unittest.main()
