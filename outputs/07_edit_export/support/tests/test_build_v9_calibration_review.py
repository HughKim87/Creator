import importlib.util
import sys
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "outputs" / "07_edit_export" / "support" / "build_v9_calibration_review.py"
SPEC = importlib.util.spec_from_file_location("build_v9_calibration_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class V9CalibrationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.load_rows(ROOT / "outputs" / "07_edit_export" / "v9_calibration_cutlist_r2.csv")
        cls.timeline = MODULE.add_timeline(cls.rows, Fraction(60, 1))
        cls.document = MODULE.build_document(cls.rows, "../../inputs/source video.mp4", Fraction(60, 1))

    def test_absolute_frame_durations_make_linked_cuts_contiguous(self):
        by_sequence = {}
        for item in self.timeline:
            if item["audio_mode"] == "linked":
                by_sequence.setdefault(item["sequence"], []).append(item)
        for items in by_sequence.values():
            items.sort(key=lambda item: item["timeline_start"])
            for previous, current in zip(items, items[1:]):
                self.assertAlmostEqual(previous["timeline_end"], current["timeline_start"], places=6)

    def test_review_player_is_not_fixed_and_supports_v2(self):
        self.assertIn(".player-card{position:static", self.document)
        self.assertNotIn(".player-card{position:sticky", self.document)
        self.assertNotIn(".player-card{position:fixed", self.document)
        self.assertIn('id="baseVideo"', self.document)
        self.assertIn('id="overlayVideo"', self.document)
        self.assertIn("syncOverlay", self.document)
        self.assertEqual(self.document.count('class="sequence-card"'), 3)

    def test_review_states_calibration_gate(self):
        self.assertIn("전체본이 아닙니다", self.document)
        self.assertIn("v9 전체 편집으로 확장하지 않습니다", self.document)
        self.assertIn("사용자 리듬 승인", self.document)


if __name__ == "__main__":
    unittest.main()
