import importlib.util
import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "outputs" / "07_edit_export" / "support" / "build_v9_calibration.py"
SPEC = importlib.util.spec_from_file_location("build_v9_calibration", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def parse_srt(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    cues = []
    for match in pattern.finditer(text):
        values = [int(value) for value in match.groups()]
        start = values[0] * 3600 + values[1] * 60 + values[2] + values[3] / 1000
        end = values[4] * 3600 + values[5] * 60 + values[6] + values[7] / 1000
        cues.append((start, end))
    return cues


class V9CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = MODULE.build_rows()
        cls.by_sequence = defaultdict(list)
        for item in cls.rows:
            cls.by_sequence[item["sequence"]].append(item)

    def test_three_calibration_sequences_only(self):
        self.assertEqual(
            set(self.by_sequence),
            {
                "CAL_A_훅과빠른진입",
                "CAL_B_추격과코미디",
                "CAL_C_주제회수와아이러니",
            },
        )

    def test_hook_is_one_complete_event_and_entry_is_early(self):
        rows = self.by_sequence["CAL_A_훅과빠른진입"]
        hook = next(item for item in rows if item["cut_id"] == "A_HOOK")
        self.assertAlmostEqual(float(hook["end"]) - float(hook["start"]), 12.9, places=3)
        cursor_frames = 0
        starts = {}
        for item in rows:
            if item["audio_mode"] != "linked":
                continue
            starts[item["cut_id"]] = cursor_frames / 60
            cursor_frames += round(float(item["end"]) * 60) - round(float(item["start"]) * 60)
        self.assertLessEqual(starts["A_ENTRY"], 32.0)
        overlays = [item for item in rows if item["video_track"] == "2"]
        self.assertEqual(overlays, [])

    def test_only_explicit_hook_breaks_chronology(self):
        a_rows = self.by_sequence["CAL_A_훅과빠른진입"]
        a_story = [item for item in a_rows if item["cut_id"] != "A_HOOK"]
        self.assertEqual([item["cut_id"] for item in a_story], ["A_MOTIVE", "A_CONDITION", "A_ENTRY"])
        self.assertEqual([float(item["start"]) for item in a_story], sorted(float(item["start"]) for item in a_story))

        b_rows = self.by_sequence["CAL_B_추격과코미디"]
        self.assertEqual([float(item["start"]) for item in b_rows], sorted(float(item["start"]) for item in b_rows))

        c_rows = self.by_sequence["CAL_C_주제회수와아이러니"]
        recap_start = next(float(item["start"]) for item in c_rows if item["cut_id"] == "C_CURIOSITY")
        c_overlays = [item for item in c_rows if item["audio_mode"] == "none"]
        self.assertEqual(len(c_overlays), 4)
        self.assertTrue(all(float(item["end"]) <= recap_start for item in c_overlays))

    def test_linked_timeline_is_delegated_to_media_aware_xml_builder(self):
        linked = [item for item in self.rows if item["audio_mode"] == "linked"]
        self.assertTrue(linked)
        self.assertTrue(all(item["timeline_start"] == "" for item in linked))

    def test_chase_is_microbeats_and_preserves_comedy(self):
        rows = self.by_sequence["CAL_B_추격과코미디"]
        linked = [item for item in rows if item["audio_mode"] == "linked"]
        duration = sum(float(item["end"]) - float(item["start"]) for item in linked)
        self.assertAlmostEqual(duration, 73.975, places=3)
        self.assertLessEqual(max(float(item["end"]) - float(item["start"]) for item in linked), 8.901)
        roles = " ".join(item["role"] for item in linked)
        self.assertIn("코미디", roles)
        self.assertIn("회복", roles)

    def test_theme_is_one_line_and_parking_lot_is_covered(self):
        rows = self.by_sequence["CAL_C_주제회수와아이러니"]
        spoken = [item for item in rows if item["cut_id"] in {"C_CURIOSITY", "C_PLAY"}]
        duration = sum(float(item["end"]) - float(item["start"]) for item in spoken)
        self.assertAlmostEqual(duration, 16.683, places=3)
        overlays = [item for item in rows if item["video_track"] == "2"]
        self.assertEqual(len(overlays), 4)
        self.assertEqual(float(overlays[0]["timeline_start"]), 0.0)
        self.assertAlmostEqual(
            float(overlays[-1]["timeline_start"]) + float(overlays[-1]["end"]) - float(overlays[-1]["start"]),
            16.683,
            places=3,
        )
        linked_ranges = [(float(item["start"]), float(item["end"])) for item in rows if item["audio_mode"] == "linked"]
        self.assertFalse(any(start < 3549.940 and end > 3527.090 for start, end in linked_ranges))
        self.assertFalse(any(start < 4735.940 and end > 4694.190 for start, end in linked_ranges))

    def test_decisions_record_keep_compress_remove_and_cutaway(self):
        decisions = [dict(zip(MODULE.DECISION_FIELDS, values)) for values in MODULE.DECISIONS]
        self.assertEqual({item["action"] for item in decisions}, {"keep", "compress", "remove", "cutaway"})
        targets = " ".join(item["target"] for item in decisions)
        self.assertIn("v8 훅", targets)
        self.assertIn("v8 B12", targets)
        self.assertIn("v8 B14", targets)
        self.assertIn("v8 B17", targets)
        self.assertIn("초반 미래 플레이 삽입", targets)

    def test_linked_audio_boundaries_do_not_split_srt_cues(self):
        cues = parse_srt(ROOT / "inputs" / "2026-06-30 00-23-03.srt")
        crossings = []
        tolerance = 0.050
        for item in self.rows:
            if item["audio_mode"] != "linked":
                continue
            for boundary_name in ("start", "end"):
                boundary = float(item[boundary_name])
                for cue_start, cue_end in cues:
                    if cue_start + tolerance < boundary < cue_end - tolerance:
                        crossings.append((item["cut_id"], boundary_name, boundary, cue_start, cue_end))
        self.assertEqual(crossings, [])


if __name__ == "__main__":
    unittest.main()
