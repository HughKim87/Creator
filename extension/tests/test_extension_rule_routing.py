from collections import Counter
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "extension"
RULES_DIR = EXTENSION / "rules"
INTENT_FIXTURE = (
    EXTENSION / "tests" / "fixtures" / "rule-routing-intents-v1.json"
)


class ExtensionRuleRoutingTests(unittest.TestCase):
    def test_intent_fixture_covers_every_extension_rule(self):
        payload = json.loads(INTENT_FIXTURE.read_text(encoding="utf-8"))
        cases = payload["cases"]
        covered = {
            owner
            for case in cases
            for owner in case["expected_owners"]
            if owner.startswith("extension/rules/")
        }
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in RULES_DIR.glob("*.md")
        }
        self.assertEqual(expected, covered)

    def test_read_only_domain_work_is_an_extension_trigger(self):
        readme = (EXTENSION / "README.md").read_text(encoding="utf-8")
        self.assertIn("분석, 실행, 재개, 검증, 생성 또는 변경할 때", readme)
        cases = {
            case["id"]: case
            for case in json.loads(INTENT_FIXTURE.read_text(encoding="utf-8"))["cases"]
        }
        read_only = cases["read-only-video-analysis"]
        self.assertIn(
            "extension/rules/video-editing-intake-and-instructions.md",
            read_only["expected_owners"],
        )
        self.assertEqual(1, len(read_only["expected_owners"]))

    def test_intent_fixture_is_owned_by_the_consumer_router(self):
        payload = json.loads(INTENT_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual("consumer-rule-routing-intents-v1", payload["fixture_version"])
        self.assertEqual("PROJECT_RULES.md", payload["router"])
        for case in payload["cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue(
                    all(
                        owner.startswith("extension/rules/")
                        for owner in case["expected_owners"]
                    )
                )

    def test_project_policy_routes_every_rule_exactly_once(self):
        policy = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        match = re.search(
            r"<!--\s*core-rule-routes:v1\s*-->(.*?)"
            r"<!--\s*/core-rule-routes:v1\s*-->",
            policy,
            re.S,
        )
        self.assertIsNotNone(match)
        routed = re.findall(
            r"\[[^\]]+\]\((extension/rules/[^)]+\.md)\)",
            match.group(1),
        )
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in RULES_DIR.glob("*.md")
        }

        self.assertEqual(expected, set(routed))
        self.assertEqual(
            {path: 1 for path in expected},
            dict(Counter(routed)),
        )
        for relative_path in routed:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

        readme = (EXTENSION / "README.md").read_text(encoding="utf-8")
        self.assertNotRegex(readme, r"\]\(rules/[^)]+\.md\)")

    def test_every_rule_declares_routing_metadata(self):
        for path in RULES_DIR.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertRegex(text, r"(?m)^- 목적:")
                self.assertRegex(text, r"(?m)^- 읽는 시점:")
                self.assertRegex(text, r"(?m)^- 책임:")
                self.assertRegex(text, r"(?m)^- 상태:")
                self.assertRegex(text, r"(?m)^- 관련 권위:")

    def test_generic_file_lifecycle_rules_are_not_extension_owners(self):
        readme = (EXTENSION / "README.md").read_text(encoding="utf-8")
        policy = (ROOT / "PROJECT_RULES.md").read_text(encoding="utf-8")
        for name in ("file-extraction.md", "file-cleanup.md"):
            with self.subTest(path=name):
                self.assertFalse((RULES_DIR / name).exists())
                self.assertNotIn(f"(rules/{name})", readme)
                self.assertNotIn(f"(extension/rules/{name})", policy)

    def test_rule_and_replay_ids_have_single_owners(self):
        rule_documents = {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(RULES_DIR.glob("*.md"))
        }
        rules_text = "\n".join(rule_documents.values())
        rule_ids = re.findall(r"(?m)^### (R\d{2}) —", rules_text)
        replay_ids = re.findall(r"(?m)^\| (TC\d{2}) \|", rules_text)

        expected_rules = {f"R{number:02d}" for number in range(1, 17)}
        expected_replays = {f"TC{number:02d}" for number in range(1, 17)}
        self.assertEqual(expected_rules, set(rule_ids))
        self.assertEqual(expected_replays, set(replay_ids))
        self.assertEqual(
            {item: 1 for item in expected_rules},
            dict(Counter(rule_ids)),
        )
        self.assertEqual(
            {item: 1 for item in expected_replays},
            dict(Counter(replay_ids)),
        )

        for name, text in rule_documents.items():
            sections = re.split(r"(?m)(?=^### R\d{2} —)", text)
            for section in sections[1:]:
                rule_id = re.match(r"### (R\d{2}) —", section).group(1)
                with self.subTest(path=name, rule=rule_id):
                    self.assertIn("- 조건:", section)
                    self.assertIn("- 행동:", section)
                    self.assertIn("- 예외:", section)
                    self.assertIn("- 검증:", section)

    def test_original_replay_expectations_are_preserved(self):
        rules_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(RULES_DIR.glob("*.md"))
        )
        rows = {
            match.group(1): match.group(2)
            for match in re.finditer(
                r"(?m)^\| (TC\d{2}) \| [^|]+ \| ([^|]+) \|$",
                rules_text,
            )
        }
        expected_phrases = {
            "TC01": "지루함을 계약으로 받고",
            "TC02": "최신 지시를 적용하고 재확인하지 않는다",
            "TC03": "보호 데이터를 열지 않는다",
            "TC04": "XML 외 산출물을 만들지 않는다",
            "TC05": "microbeat로 2차 편집한다",
            "TC06": "최소 공간·행동 연결을 유지한다",
            "TC07": "cue 전체 보존을 강제하지 않는다",
            "TC08": "audio-only gap으로 파편을 제거한다",
            "TC09": "새 상황의 첫 반응은 유지한다",
            "TC10": "대사를 임의 추가하지 않는다",
            "TC11": "수정 clip과 인접 경계의 이전 승인만 무효화",
            "TC12": "기술 통과·의미 실패",
        }
        for replay_id, phrase in expected_phrases.items():
            with self.subTest(replay=replay_id):
                self.assertIn(phrase, rows[replay_id])

    def test_contract_does_not_duplicate_rule_bodies(self):
        contract = (
            EXTENSION
            / "docs"
            / "domain"
            / "youtube"
            / "VIDEO_EDITING_WORKFLOW_CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertNotRegex(contract, r"(?m)^### R\d{2} —")
        self.assertIn("R01~R16", contract)
        self.assertIn("TC01~TC16", contract)

    def test_video_artifacts_use_task_rule_and_single_scratch_lifecycle(self):
        lineage = (
            RULES_DIR / "video-editing-artifact-lineage.md"
        ).read_text(encoding="utf-8")
        self.assertIn("하나의 scratch root", lineage)
        self.assertIn("발견 즉시 task-rule에 기록", lineage)
        self.assertIn("closeout에서 일괄 제거", lineage)
        self.assertIn("소비자·만료 조건", lineage)

    def test_candidate_reference_is_routed_but_not_active_rule(self):
        readme = (EXTENSION / "README.md").read_text(encoding="utf-8")
        relative = "docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md"
        self.assertEqual(readme.count(f"]({relative})"), 1)
        candidate = EXTENSION / relative
        self.assertTrue(candidate.is_file())
        text = candidate.read_text(encoding="utf-8")
        self.assertIn("현재 운영 규칙이나 기본 합격값이 아니다", text)
        self.assertIn("두 번째 독립 영상", text)


if __name__ == "__main__":
    unittest.main()
