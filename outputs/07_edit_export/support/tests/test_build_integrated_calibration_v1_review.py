import importlib.util
import sys
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "outputs" / "07_edit_export" / "support" / "build_integrated_calibration_v1_review.py"
SPEC = importlib.util.spec_from_file_location("build_integrated_calibration_v1_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class IntegratedCalibrationV1ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.load_rows(ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r2_cutlist.csv")
        cls.decisions = MODULE.load_decisions(
            ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r2_microbeat_decisions.csv"
        )
        cls.timeline = MODULE.add_timeline(cls.rows, Fraction(60, 1))
        cls.document = MODULE.build_document(cls.rows, cls.decisions, "../../inputs/source video.mp4", Fraction(60, 1))

    def test_linked_cuts_are_contiguous_by_source_frame_duration(self):
        by_sequence = {}
        for item in self.timeline:
            if item["audio_mode"] == "linked":
                by_sequence.setdefault(item["sequence"], []).append(item)
        for items in by_sequence.values():
            items.sort(key=lambda item: item["timeline_start"])
            for previous, current in zip(items, items[1:]):
                self.assertAlmostEqual(previous["timeline_end"], current["timeline_start"], places=6)

    def test_player_is_static_and_supports_audio_v2_and_blind_mode(self):
        self.assertIn(".player-card{position:static", self.document)
        self.assertNotIn(".player-card{position:sticky", self.document)
        self.assertNotIn(".player-card{position:fixed", self.document)
        self.assertIn('id="baseVideo"', self.document)
        self.assertIn('id="overlayVideo"', self.document)
        self.assertIn("base.muted=false", self.document)
        self.assertIn('id="blindMode"', self.document)
        self.assertIn("blind-active", self.document)
        self.assertIn("startVisualTail", self.document)
        self.assertIn("tailing=true", self.document)

    def test_page_has_three_sequences_and_one_recommendation(self):
        self.assertEqual(self.document.count('class="sequence-card"'), 3)
        self.assertEqual(self.document.count("한 가지 권고"), 1)
        self.assertIn("AI 비트별 조치", self.document)
        self.assertIn("전체 편집·approved_baseline·current_deliverable로 확장하지 않습니다", self.document)

    def test_central_message_is_not_duplicated(self):
        message = "영화로 보던 백룸은, 직접 헤매고 규칙을 배우며 익숙해질수록 무서움은 줄어도 끝내 긴장이 남는 체험이었다."
        self.assertEqual(self.document.count(message), 1)

    def test_ending_overlay_covers_the_last_black_audio_rows(self):
        ending = [item for item in self.timeline if item["sequence"] == "CAL_C_적응과공포잔존"]
        overlay = next(item for item in ending if item["cut_id"] == "C_V2_ENDING_ROOM")
        signoff = next(item for item in ending if item["cut_id"] == "C_SIGNOFF")
        confession = next(item for item in ending if item["cut_id"] == "C_CONFESSION")
        self.assertAlmostEqual(overlay["timeline_start"], signoff["timeline_start"], places=6)
        self.assertAlmostEqual(overlay["timeline_end"], confession["timeline_end"], places=6)


class IntegratedCalibrationV1R3ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.load_rows(ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r3_cutlist.csv")
        cls.decisions = MODULE.load_decisions(
            ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r3_microbeat_decisions.csv"
        )
        cls.timeline = MODULE.add_timeline(cls.rows, Fraction(60, 1))
        cls.document = MODULE.build_document(cls.rows, cls.decisions, "../../inputs/source video.mp4", Fraction(60, 1))

    def test_r3_hook_overlay_exactly_covers_boast(self):
        opening = [item for item in self.timeline if item["sequence"] == "CAL_A_훅과첫진입"]
        boast = next(item for item in opening if item["cut_id"] == "A_HOOK_BOAST")
        overlay = next(item for item in opening if item["cut_id"] == "A_V2_HOOK_BOAST_ENTITY")
        self.assertAlmostEqual(overlay["timeline_start"], boast["timeline_start"], places=6)
        self.assertAlmostEqual(overlay["timeline_end"], boast["timeline_end"], places=6)

    def test_r3_middle_contains_real_switch_action_before_payoff(self):
        middle = [
            item for item in self.timeline
            if item["sequence"] == "CAL_B_빛변화와코미디" and item["audio_mode"] == "linked"
        ]
        ids = [item["cut_id"] for item in middle]
        self.assertLess(ids.index("B_POWER_SWITCH"), ids.index("B_COMEDY_PAYOFF"))
        payoff = next(item for item in middle if item["cut_id"] == "B_COMEDY_PAYOFF")
        self.assertAlmostEqual(payoff["end"], 3523.740, places=3)

    def test_r3_ending_overlay_has_four_tenths_visual_tail(self):
        ending = [item for item in self.timeline if item["sequence"] == "CAL_C_적응과공포잔존"]
        overlay = next(item for item in ending if item["cut_id"] == "C_V2_ENDING_ROOM")
        signoff = next(item for item in ending if item["cut_id"] == "C_SIGNOFF")
        confession = next(item for item in ending if item["cut_id"] == "C_CONFESSION")
        self.assertAlmostEqual(overlay["timeline_start"], signoff["timeline_start"], places=6)
        self.assertAlmostEqual(overlay["timeline_end"] - confession["timeline_end"], 0.4, places=6)

    def test_r3_page_preserves_contract_and_visual_tail_playback(self):
        self.assertEqual(self.document.count('class="sequence-card"'), 3)
        self.assertEqual(self.document.count("한 가지 권고"), 1)
        self.assertIn("startVisualTail", self.document)
        self.assertIn("무음 엔딩 여운 재생 중", self.document)
        message = "영화로 보던 백룸은, 직접 헤매고 규칙을 배우며 익숙해질수록 무서움은 줄어도 끝내 긴장이 남는 체험이었다."
        self.assertEqual(self.document.count(message), 1)


class IntegratedCalibrationV1R4ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.load_rows(ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r4_cutlist.csv")
        cls.decisions = MODULE.load_decisions(
            ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r4_microbeat_decisions.csv"
        )
        cls.timeline = MODULE.add_timeline(cls.rows, Fraction(60, 1))
        cls.document = MODULE.build_document(cls.rows, cls.decisions, "../../inputs/source video.mp4", Fraction(60, 1))

    def test_r4_page_preserves_player_and_single_recommendation_contract(self):
        self.assertEqual(self.document.count('class="sequence-card"'), 3)
        self.assertEqual(self.document.count("한 가지 권고"), 1)
        self.assertIn(".player-card{position:static", self.document)
        self.assertIn("startVisualTail", self.document)
        self.assertIn('id="blindMode"', self.document)

    def test_r4_hook_has_no_overlay_replay(self):
        opening = [item for item in self.timeline if item["sequence"] == "CAL_A_훅과첫진입"]
        self.assertFalse(any(item["audio_mode"] == "none" for item in opening))
        hook = [item for item in opening if str(item["cut_id"]).startswith("A_HOOK_")]
        self.assertEqual([item["cut_id"] for item in hook[:2]], ["A_HOOK_REVEAL", "A_HOOK_TAUNT"])

    def test_r4_confession_overlay_has_four_tenths_visual_tail(self):
        ending = [item for item in self.timeline if item["sequence"] == "CAL_C_적응과공포잔존"]
        confession = next(item for item in ending if item["cut_id"] == "C_CONFESSION")
        overlay = next(item for item in ending if item["cut_id"] == "C_V2_CONFESSION_ROOM")
        self.assertAlmostEqual(overlay["timeline_start"], confession["timeline_start"], places=6)
        self.assertAlmostEqual(overlay["timeline_end"] - confession["timeline_end"], 0.4, places=6)


if __name__ == "__main__":
    unittest.main()
