from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


def _handoff_route(handoff: str, label: str) -> Path | None:
    match = re.search(rf"(?m)^- {re.escape(label)}: `([^`]+)`\.?$", handoff)
    if match is not None:
        return ROOT / match.group(1)
    if re.search(rf"(?m)^- {re.escape(label)}: 없음\.?$", handoff):
        return None
    raise ValueError(f"missing handoff route: {label}")


def _metadata_value(document: str, label: str) -> str:
    match = re.search(rf"(?m)^- {re.escape(label)}:\s*(.+)$", document)
    if match is None:
        raise ValueError(f"missing metadata: {label}")
    value = match.group(1).strip()
    if value.startswith("`") and "`" in value[1:]:
        return value[1 : value.index("`", 1)]
    return value


class StagedDesignRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
        cls.overall_path = _handoff_route(cls.handoff, "활성 전체 설계")
        cls.active_phase_path = _handoff_route(cls.handoff, "활성 단계 설계")
        if cls.overall_path is None and cls.active_phase_path is not None:
            raise ValueError("an active phase requires an active overall design")
        cls.idle = cls.overall_path is None
        cls.overall = (
            "" if cls.overall_path is None else cls.overall_path.read_text(encoding="utf-8")
        )
        cls.active_phase = (
            ""
            if cls.active_phase_path is None
            else cls.active_phase_path.read_text(encoding="utf-8")
        )

    def test_handoff_routes_existing_active_documents(self):
        if self.idle:
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^- 활성 전체 설계: 없음\.?$", self.handoff)),
            )
            self.assertIsNone(self.active_phase_path)
            return
        self.assertTrue(self.overall_path.is_file())
        self.assertEqual(
            1,
            len(re.findall(r"(?m)^- 활성 전체 설계: `[^`]+`\.?$", self.handoff)),
        )
        if self.active_phase_path is None:
            self.assertEqual(
                1,
                len(re.findall(r"(?m)^- 활성 단계 설계: 없음\.?$", self.handoff)),
            )
            return
        self.assertTrue(self.active_phase_path.is_file())
        self.assertNotEqual(self.overall_path, self.active_phase_path)
        self.assertEqual(
            1,
            len(re.findall(r"(?m)^- 활성 단계 설계: `[^`]+`\.?$", self.handoff)),
        )

    def test_required_designs_are_bounded_and_have_distinct_roles(self):
        if self.idle:
            self.assertFalse((ROOT / "extension" / "work" / "repository-consolidation").exists())
            return
        self.assertLessEqual(len(self.overall.splitlines()), 300)
        self.assertLessEqual(len(self.overall), 20_000)
        self.assertEqual("overall-design", _metadata_value(self.overall, "문서 분류"))
        if self.active_phase_path is None:
            return
        self.assertLessEqual(len(self.active_phase.splitlines()), 160)
        self.assertLessEqual(len(self.active_phase), 12_000)
        self.assertEqual("phase-design", _metadata_value(self.active_phase, "문서 분류"))

    def test_overall_routes_only_the_active_detailed_phase(self):
        if self.idle:
            self.assertNotRegex(self.handoff, r"(?m)^- 활성 (전체|단계) 설계: `")
            return
        active_links = re.findall(
            r"(?m)^- 활성 단계:\s*\[[^]]+\]\(([^)]+)\)$",
            self.overall,
        )
        if self.active_phase_path is None:
            self.assertEqual([], active_links)
            return
        relative_phase = self.active_phase_path.relative_to(self.overall_path.parent).as_posix()
        self.assertEqual([relative_phase], active_links)

    def test_active_phase_owns_exact_execution_gates(self):
        if self.idle or self.active_phase_path is None:
            return
        phase_id = _metadata_value(self.active_phase, "phase ID")
        self.assertRegex(phase_id, r"^[A-Za-z0-9_-]+$")
        self.assertIn(phase_id, self.active_phase_path.name)
        self.assertRegex(
            self.active_phase,
            r"(?m)^- lifecycle: `(draft|ready|in_progress|blocked|passed|invalidated|superseded)`$",
        )
        headings = {
            heading.casefold()
            for heading in re.findall(r"(?m)^#{2,3}\s+(.+)$", self.active_phase)
        }
        self.assertIn("entry gate", headings)
        self.assertTrue(any("exit" in heading and "gate" in heading for heading in headings))
        self.assertTrue(any("slice" in heading and "gate" in heading for heading in headings))
        self.assertTrue(any("복구" in heading or "중단" in heading for heading in headings))
        self.assertRegex(self.active_phase, r"(?m)^- 첫 다음 행동:\s*.+$")

    def test_optional_evidence_is_not_routed_as_required_state(self):
        self.assertNotRegex(self.handoff, r"(?m)^- (M0 evidence|선택 근거):")
        if self.idle or self.active_phase_path is None:
            return
        self.assertIn("optional evidence owner", self.active_phase)
        self.assertIn("startup-required 아님", self.active_phase)

    def test_handoff_declares_truthful_resume_contract(self):
        mode = _metadata_value(self.handoff, "handoff mode")
        self.assertIn(mode, {"same-workspace", "portable"})
        if mode == "same-workspace":
            self.assertIn("uncommitted", self.handoff)
        headings = set(re.findall(r"(?m)^##\s+(.+)$", self.handoff))
        self.assertIn("첫 다음 행동", headings)
        self.assertTrue(any("시작 prompt" in heading for heading in headings))
        self.assertRegex(self.handoff, r"(?m)^1\.\s+.+$")

    def test_local_completion_has_stable_resume_state(self):
        if not re.search(r"(?m)^- 상태: 로컬 구현 완료\.", self.handoff):
            return
        self.assertRegex(
            self.handoff,
            r"(?m)^- uncommitted dependency: 없음\.$",
        )
        next_actions = re.search(
            r"(?ms)^## 첫 다음 행동\s*(.+?)(?=^## |\Z)",
            self.handoff,
        )
        self.assertIsNotNone(next_actions)
        assert next_actions is not None
        self.assertNotRegex(next_actions.group(1), r"(?i)commit|커밋")
        self.assertRegex(next_actions.group(1), r"승인|대기")


if __name__ == "__main__":
    unittest.main()
