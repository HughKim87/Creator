from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


def _handoff_route(handoff: str, label: str) -> Path:
    match = re.search(rf"(?m)^- {re.escape(label)}: `([^`]+)`$", handoff)
    if match is None:
        raise ValueError(f"missing handoff route: {label}")
    return ROOT / match.group(1)


class StagedDesignRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = (ROOT / "SESSION_HANDOFF.md").read_text(encoding="utf-8")
        cls.overall_path = _handoff_route(cls.handoff, "활성 전체 설계")
        cls.active_phase_path = _handoff_route(cls.handoff, "활성 단계 설계")
        cls.evidence_path = _handoff_route(cls.handoff, "선택 근거")
        cls.overall = cls.overall_path.read_text(encoding="utf-8")
        phase_routes = re.findall(
            r"\[(M[0-6]) 설계\]\((project-foundation/[^)]+\.md)\)",
            cls.overall,
        )
        cls.phase_paths = {
            phase_id: cls.overall_path.parent / relative_path
            for phase_id, relative_path in phase_routes
        }
        cls.phases = {
            phase_id: path.read_text(encoding="utf-8")
            for phase_id, path in cls.phase_paths.items()
        }
        cls.evidence = cls.evidence_path.read_text(encoding="utf-8")

    def test_handoff_routes_one_existing_overall_and_active_phase_design(self):
        self.assertTrue(self.overall_path.is_file())
        self.assertTrue(self.active_phase_path.is_file())
        self.assertNotEqual(self.overall_path, self.active_phase_path)
        self.assertEqual(
            1,
            len(re.findall(r"(?m)^- 활성 전체 설계: `[^`]+`$", self.handoff)),
        )
        self.assertEqual(
            1,
            len(re.findall(r"(?m)^- 활성 단계 설계: `[^`]+`$", self.handoff)),
        )
        active_phase = self.active_phase_path.read_text(encoding="utf-8")
        active_id = re.search(r"(?m)^- 단계 ID: `(M[0-6])`$", active_phase)
        self.assertIsNotNone(active_id)
        self.assertIn(f"기반 {active_id.group(1)}", self.handoff)
        self.assertRegex(
            active_phase,
            r"(?m)^- lifecycle: `(draft|ready|in_progress|blocked)`$",
        )

    def test_overall_routes_every_bounded_phase_design(self):
        self.assertEqual({f"M{number}" for number in range(7)}, set(self.phase_paths))
        self.assertLessEqual(len(self.overall.splitlines()), 120)
        self.assertLessEqual(len(self.overall), 8_000)
        for phase_id, phase in self.phases.items():
            with self.subTest(phase=phase_id):
                self.assertTrue(self.phase_paths[phase_id].is_file())
                self.assertLessEqual(len(phase.splitlines()), 160)
                self.assertLessEqual(len(phase), 12_000)

    def test_overall_design_is_a_short_stage_map(self):
        self.assertIn("- 문서 역할: `overall-design`", self.overall)
        self.assertIn("## 최종 목표", self.overall)
        self.assertIn("## 불변식과 금지 범위", self.overall)
        self.assertIn("## 단계 지도", self.overall)
        self.assertIn("## 단계 전환 계약", self.overall)
        self.assertNotIn("활성화 시 작성", self.overall)

    def test_every_phase_owns_exact_gates_and_valid_lifecycle(self):
        active_resolved = self.active_phase_path.resolve()
        for phase_id, phase in self.phases.items():
            with self.subTest(phase=phase_id):
                self.assertIn("- 문서 역할: `phase-design`", phase)
                self.assertIn(f"- 단계 ID: `{phase_id}`", phase)
                for heading in (
                    "## Entry gate",
                    "## Execution slices와 slice gate",
                    "## Exit gate",
                    "## 중단·복구 조건",
                    "## Transition gate",
                ):
                    self.assertIn(heading, phase)
                self.assertRegex(phase, r"(?m)^## 첫 (?:다음|활성화) 행동$")
                if self.phase_paths[phase_id].resolve() != active_resolved:
                    self.assertRegex(
                        phase,
                        r"(?m)^- lifecycle: `(planned|passed|invalidated|superseded)`$",
                    )

    def test_long_report_is_optional_reference_evidence(self):
        self.assertTrue(self.evidence_path.is_file())
        self.assertIn("- 상태: 선택적 `reference-evidence`.", self.evidence)
        self.assertIn("startup 필수 읽기로 사용하지 않는다", self.evidence)
        self.assertNotEqual(self.evidence_path, self.overall_path)
        self.assertNotEqual(self.evidence_path, self.active_phase_path)


if __name__ == "__main__":
    unittest.main()
