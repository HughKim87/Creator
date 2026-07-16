import importlib.util
import sys
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "outputs" / "07_edit_export" / "support" / "build_integrated_calibration_v1.py"
SPEC = importlib.util.spec_from_file_location("build_integrated_calibration_v1", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class IntegratedCalibrationV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.build_rows()
        cls.by_sequence = defaultdict(list)
        for item in cls.rows:
            cls.by_sequence[item["sequence"]].append(item)

    def test_has_only_three_representative_positions(self):
        self.assertEqual(set(self.by_sequence), {MODULE.SEQ_A, MODULE.SEQ_B, MODULE.SEQ_C})

    def test_hook_is_10_to_16_second_event_with_context_peak_result(self):
        hook = [item for item in self.by_sequence[MODULE.SEQ_A] if item["cut_id"].startswith("A_HOOK_")]
        self.assertEqual([item["role"] for item in hook], [
            "훅_문맥_위협확인",
            "훅_피크_허세",
            "훅_결과_즉시붕괴",
        ])
        duration = sum(float(item["end"]) - float(item["start"]) for item in hook)
        self.assertGreaterEqual(duration, 10.0)
        self.assertLessEqual(duration, 16.0)

    def test_opening_resets_to_e01_then_e02_without_future_v2(self):
        story = [item for item in self.by_sequence[MODULE.SEQ_A] if not item["cut_id"].startswith("A_HOOK_")]
        self.assertEqual([item["cut_id"] for item in story], [
            "A_MOTIVE_MOVIE",
            "A_MOTIVE_GAME",
            "A_ENTRY_REVEAL",
            "A_ENTRY_EXPERIENCE",
        ])
        self.assertEqual([float(item["start"]) for item in story], sorted(float(item["start"]) for item in story))
        self.assertFalse(any(item["video_track"] == "2" for item in self.by_sequence[MODULE.SEQ_A]))

    def test_middle_uses_e10_and_does_not_repeat_e08(self):
        rows = self.by_sequence[MODULE.SEQ_B]
        self.assertEqual([item["cut_id"] for item in rows], [
            "B_DARK_PROBLEM",
            "B_POWER_ACTION",
            "B_COMEDY_SETUP",
            "B_COMEDY_PAYOFF",
        ])
        self.assertTrue(all(3422.0 <= float(item["start"]) <= 3523.0 for item in rows))
        self.assertIn("코미디", " ".join(item["role"] for item in rows))

    def test_ending_links_e11_to_e14_in_order(self):
        linked = [item for item in self.by_sequence[MODULE.SEQ_C] if item["audio_mode"] == "linked"]
        self.assertEqual([float(item["start"]) for item in linked], sorted(float(item["start"]) for item in linked))
        roles = " ".join(item["role"] for item in linked)
        self.assertIn("E11_메시지회수", roles)
        self.assertIn("E14_최종자백", roles)

    def test_final_black_frame_is_covered_by_prior_unused_ending_room(self):
        overlays = [item for item in self.by_sequence[MODULE.SEQ_C] if item["audio_mode"] == "none"]
        self.assertEqual(len(overlays), 1)
        overlay = overlays[0]
        self.assertEqual(overlay["cut_id"], "C_V2_ENDING_ROOM")
        self.assertEqual(overlay["video_track"], "2")
        self.assertLess(float(overlay["end"]), 4920.340)
        self.assertAlmostEqual(float(overlay["end"]) - float(overlay["start"]), 4.977, places=3)

    def test_audit_input_is_single_sequence_and_has_valid_sections(self):
        audit_rows = MODULE.build_audit_rows(self.rows)
        self.assertEqual({item["sequence"] for item in audit_rows}, {"INTEGRATED_CALIBRATION_V1"})
        self.assertTrue(all(item["cut_id"].startswith(("HOOK_", "B01_", "B02_", "B03_")) for item in audit_rows))
        self.assertEqual(len(audit_rows), 19)

    def test_decisions_cover_every_required_7b_field(self):
        decisions = MODULE.build_decisions(self.rows)
        self.assertEqual(len(decisions), 6)
        for item in decisions:
            self.assertEqual(set(item), set(MODULE.DECISION_FIELDS))
            for field in (
                "story_function",
                "action",
                "selected_ranges",
                "longest_reason",
                "screen_boundary",
                "audio_boundary",
                "rule_ids",
                "reason",
                "evidence",
            ):
                self.assertTrue(item[field], f"{item['decision_id']} missing {field}")


class IntegratedCalibrationV1R3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.build_rows("r3")
        cls.by_sequence = defaultdict(list)
        for item in cls.rows:
            cls.by_sequence[item["sequence"]].append(item)

    def test_hook_splits_fear_and_escape_and_covers_boast_with_same_event_v2(self):
        linked = [
            item for item in self.by_sequence[MODULE.SEQ_A]
            if item["audio_mode"] == "linked" and item["cut_id"].startswith("A_HOOK_")
        ]
        self.assertEqual([item["cut_id"] for item in linked], [
            "A_HOOK_CONTEXT",
            "A_HOOK_BOAST",
            "A_HOOK_FEAR",
            "A_HOOK_ESCAPE",
        ])
        duration = sum(float(item["end"]) - float(item["start"]) for item in linked)
        self.assertAlmostEqual(duration, 12.392, places=3)

        overlay = next(item for item in self.rows if item["cut_id"] == "A_V2_HOOK_BOAST_ENTITY")
        boast = next(item for item in linked if item["cut_id"] == "A_HOOK_BOAST")
        self.assertEqual(MODULE.source_duration_frames(overlay), MODULE.source_duration_frames(boast))
        self.assertAlmostEqual(
            float(overlay["timeline_start"]),
            MODULE.linked_timeline_start(self.rows, MODULE.SEQ_A, "A_HOOK_BOAST"),
            places=6,
        )
        self.assertGreaterEqual(float(overlay["start"]), 2336.323)
        self.assertLessEqual(float(overlay["end"]), 2350.940)

    def test_opening_story_still_resets_to_e01_e02_after_hook_only_v2(self):
        story = [
            item for item in self.by_sequence[MODULE.SEQ_A]
            if item["audio_mode"] == "linked" and not item["cut_id"].startswith("A_HOOK_")
        ]
        self.assertEqual([item["cut_id"] for item in story], [
            "A_MOTIVE_MOVIE",
            "A_MOTIVE_GAME",
            "A_ENTRY_REVEAL",
            "A_ENTRY_EXPERIENCE",
        ])
        overlays = [item for item in self.by_sequence[MODULE.SEQ_A] if item["video_track"] == "2"]
        self.assertEqual([item["cut_id"] for item in overlays], ["A_V2_HOOK_BOAST_ENTITY"])

    def test_middle_restores_switch_action_and_holds_bright_result(self):
        linked = [item for item in self.by_sequence[MODULE.SEQ_B] if item["audio_mode"] == "linked"]
        self.assertEqual([item["cut_id"] for item in linked], [
            "B_DARK_PROBLEM",
            "B_POWER_DISCOVERY",
            "B_COMEDY_SETUP",
            "B_POWER_SWITCH",
            "B_COMEDY_PAYOFF",
        ])
        switch = next(item for item in linked if item["cut_id"] == "B_POWER_SWITCH")
        payoff = next(item for item in linked if item["cut_id"] == "B_COMEDY_PAYOFF")
        self.assertEqual((switch["start"], switch["end"]), ("3513.940", "3516.340"))
        self.assertEqual(payoff["end"], "3523.740")

    def test_ending_uses_full_cue_boundaries_and_has_four_tenths_visual_tail(self):
        tense = next(item for item in self.rows if item["cut_id"] == "C_TENSE_BODY")
        signoff = next(item for item in self.rows if item["cut_id"] == "C_SIGNOFF")
        confession = next(item for item in self.rows if item["cut_id"] == "C_CONFESSION")
        overlay = next(item for item in self.rows if item["cut_id"] == "C_V2_ENDING_ROOM")
        self.assertEqual((tense["start"], tense["end"]), ("4864.365", "4865.940"))
        self.assertEqual((signoff["start"], signoff["end"]), ("4914.090", "4915.940"))
        overlay_start = float(overlay["timeline_start"])
        overlay_end = overlay_start + MODULE.source_duration_frames(overlay) / MODULE.SOURCE_FPS
        linked_end = MODULE.linked_timeline_end(self.rows, MODULE.SEQ_C)
        self.assertAlmostEqual(overlay_start, MODULE.linked_timeline_start(self.rows, MODULE.SEQ_C, "C_SIGNOFF"), places=6)
        self.assertAlmostEqual(overlay_end - linked_end, 0.4, places=6)
        self.assertEqual(confession["end"], "4924.050")

    def test_r3_audit_and_decisions_cover_all_changed_microbeats(self):
        audit_rows = MODULE.build_audit_rows(self.rows)
        self.assertEqual(len(audit_rows), 21)
        self.assertEqual(len({item["cut_id"] for item in audit_rows}), 21)
        decisions = MODULE.build_decisions_r3(self.rows)
        self.assertEqual(len(decisions), 6)
        self.assertIn("user feedback 2026-07-15", decisions[0]["evidence"])
        self.assertIn("3513.940~3516.340", decisions[3]["selected_ranges"])
        for item in decisions:
            self.assertEqual(set(item), set(MODULE.DECISION_FIELDS))
            self.assertTrue(all(item[field] for field in MODULE.DECISION_FIELDS))


class IntegratedCalibrationV1R4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.build_rows("r4")
        cls.by_sequence = defaultdict(list)
        for item in cls.rows:
            cls.by_sequence[item["sequence"]].append(item)

    def test_hook_progresses_once_without_replayed_v2(self):
        linked = [
            item for item in self.by_sequence[MODULE.SEQ_A]
            if item["audio_mode"] == "linked" and item["cut_id"].startswith("A_HOOK_")
        ]
        self.assertEqual([item["cut_id"] for item in linked], [
            "A_HOOK_REVEAL",
            "A_HOOK_TAUNT",
            "A_HOOK_BOAST",
            "A_HOOK_FEAR",
            "A_HOOK_ESCAPE",
        ])
        self.assertAlmostEqual(
            sum(float(item["end"]) - float(item["start"]) for item in linked),
            11.914,
            places=3,
        )
        self.assertEqual((linked[0]["start"], linked[0]["end"]), ("2333.865", "2336.223"))
        self.assertEqual((linked[1]["start"], linked[1]["end"]), ("2336.323", "2338.837"))
        self.assertFalse(any(item["video_track"] == "2" for item in self.by_sequence[MODULE.SEQ_A]))

    def test_middle_removes_repeated_direction_but_preserves_action_and_result(self):
        linked = [item for item in self.by_sequence[MODULE.SEQ_B] if item["audio_mode"] == "linked"]
        self.assertEqual([item["cut_id"] for item in linked], [
            "B_DARK_PROBLEM",
            "B_POWER_DISCOVERY",
            "B_COMEDY_SETUP",
            "B_POWER_SWITCH",
            "B_COMEDY_PAYOFF",
        ])
        discovery = next(item for item in linked if item["cut_id"] == "B_POWER_DISCOVERY")
        self.assertEqual((discovery["start"], discovery["end"]), ("3506.540", "3507.940"))
        self.assertAlmostEqual(MODULE.linked_duration(self.rows, MODULE.SEQ_B), 13.710, places=3)

    def test_ending_removes_redundant_and_context_dependent_cues(self):
        linked = [item for item in self.by_sequence[MODULE.SEQ_C] if item["audio_mode"] == "linked"]
        ids = [item["cut_id"] for item in linked]
        self.assertEqual(ids, [
            "C_REPEAT",
            "C_FIRST_SITUATION",
            "C_FEAR_REMAINS",
            "C_NOT_SCARED",
            "C_SIGNOFF",
            "C_CONFESSION",
        ])
        self.assertNotIn("C_ADAPT", ids)
        self.assertNotIn("C_TENSE_BODY", ids)

    def test_c_overlays_visualize_repetition_and_split_the_ending(self):
        overlays = [item for item in self.by_sequence[MODULE.SEQ_C] if item["audio_mode"] == "none"]
        self.assertEqual([item["cut_id"] for item in overlays], [
            "C_V2_REPEAT_FLASHBACK",
            "C_V2_SIGNOFF_ROOM",
            "C_V2_CONFESSION_ROOM",
        ])
        flashback, signoff_room, confession_room = overlays
        self.assertEqual(flashback["timeline_start"], "0.000000")
        self.assertAlmostEqual(
            float(signoff_room["timeline_start"]),
            MODULE.linked_timeline_start(self.rows, MODULE.SEQ_C, "C_SIGNOFF"),
            places=6,
        )
        self.assertAlmostEqual(
            float(confession_room["timeline_start"]),
            MODULE.linked_timeline_start(self.rows, MODULE.SEQ_C, "C_CONFESSION"),
            places=6,
        )
        confession_room_end = (
            float(confession_room["timeline_start"])
            + MODULE.source_duration_frames(confession_room) / MODULE.SOURCE_FPS
        )
        self.assertAlmostEqual(confession_room_end - MODULE.linked_timeline_end(self.rows, MODULE.SEQ_C), 0.4, places=6)

    def test_r4_audit_and_decisions_cover_every_linked_cut(self):
        audit_rows = MODULE.build_audit_rows(self.rows)
        self.assertEqual(len(audit_rows), 20)
        self.assertEqual(len({item["cut_id"] for item in audit_rows}), 20)
        decisions = MODULE.build_decisions_r4(self.rows)
        self.assertEqual(len(decisions), 6)
        self.assertIn("ffmpeg silencedetect", decisions[0]["evidence"])
        self.assertIn("3506.540~3507.940", decisions[3]["selected_ranges"])
        self.assertIn("4270.832~4275.780", decisions[4]["removed_ranges"])
        self.assertIn("4864.365~4865.940", decisions[5]["removed_ranges"])
        for item in decisions:
            self.assertEqual(set(item), set(MODULE.DECISION_FIELDS))
            self.assertTrue(all(item[field] for field in MODULE.DECISION_FIELDS))


if __name__ == "__main__":
    unittest.main()
