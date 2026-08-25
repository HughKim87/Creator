"""Creator 창작 위임 의미가 소비 정책 한 곳에서만 소유되는지 검사한다."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
CLAUSE_ID = "creator-video-creative-delegation-v1"
POLICY = ROOT / "PROJECT_RULES.md"
FIXTURE = ROOT / "extension" / "tests" / "fixtures" / "creative-delegation-v1.json"
DEPENDENTS = (
    ROOT / ".agents" / "skills" / "coordinate-video-production" / "SKILL.md",
    ROOT
    / ".agents"
    / "skills"
    / "coordinate-video-production"
    / "references"
    / "video-job-format.md",
    ROOT / ".agents" / "skills" / "youtube-title-thumbnail" / "SKILL.md",
    ROOT
    / ".agents"
    / "skills"
    / "youtube-title-thumbnail"
    / "references"
    / "package-format.md",
)


def contract_errors(policy: str, dependents: dict[str, str]) -> list[str]:
    errors: list[str] = []
    block = re.findall(
        rf"<!-- {CLAUSE_ID} -->(.*?)<!-- /{CLAUSE_ID} -->", policy, re.S
    )
    if len(block) != 1 or f"`{CLAUSE_ID}`" not in block[0]:
        errors.append("canonical clause must exist exactly once")
    for name, text in dependents.items():
        if CLAUSE_ID not in text:
            errors.append(f"{name} does not reference canonical clause")
        if re.search(r"\bsupersedes\b", text, re.I):
            errors.append(f"{name} claims superseding authority")
        if "끝까지 진행”은" in text and "근거가 아니다" in text:
            errors.append(f"{name} independently denies a canonical trigger")
    return errors


class CreativeDelegationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = POLICY.read_text(encoding="utf-8")
        self.dependents = {
            path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
            for path in DEPENDENTS
        }
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_policy_is_the_only_semantic_authority(self) -> None:
        self.assertEqual(contract_errors(self.policy, self.dependents), [])

    def test_fixture_uses_one_clause_and_supported_modes(self) -> None:
        self.assertEqual(self.fixture["schema_version"], "creative-delegation-fixture-v1")
        self.assertEqual(self.fixture["authority_clause"], CLAUSE_ID)
        ids = [case["id"] for case in self.fixture["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 5)
        for case in self.fixture["cases"]:
            self.assertTrue(case["utterance"])
            self.assertIn(
                case["expected_execution_mode"],
                {"autonomous_local_pipeline", "review_gated"},
            )
            self.assertIn(
                case["expected_approval_mode"], {"delegated_by_user", "review_gated"}
            )

    def test_missing_clause_reference_is_detected(self) -> None:
        injected = dict(self.dependents)
        first = next(iter(injected))
        injected[first] = injected[first].replace(CLAUSE_ID, "missing-clause")
        self.assertTrue(contract_errors(self.policy, injected))

    def test_superseding_authority_is_detected(self) -> None:
        injected = dict(self.dependents)
        first = next(iter(injected))
        injected[first] += "\nThis section supersedes project policy.\n"
        self.assertTrue(contract_errors(self.policy, injected))


if __name__ == "__main__":
    unittest.main()
