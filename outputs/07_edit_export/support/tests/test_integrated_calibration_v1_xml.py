import csv
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


class IntegratedCalibrationV1XmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r2.xml").getroot()
        with (ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r2_cutlist.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.sequences = {
            item.findtext("name"): item
            for item in cls.root.findall(".//bin[name='02_시퀀스']/children/sequence")
        }

    def test_has_exactly_three_sequences_and_expected_tracks(self):
        self.assertEqual(list(self.sequences), [
            "CAL_A_훅과첫진입",
            "CAL_B_빛변화와코미디",
            "CAL_C_적응과공포잔존",
        ])
        self.assertEqual([len(item.findall("media/video/track")) for item in self.sequences.values()], [1, 1, 2])
        self.assertTrue(all(len(item.findall("media/audio/track")) == 2 for item in self.sequences.values()))

    def test_every_video_and_audio_clip_has_matching_source_and_timeline_frames(self):
        clips = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        clips += self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem")
        self.assertTrue(clips)
        for clip in clips:
            self.assertEqual(
                int(clip.findtext("end")) - int(clip.findtext("start")),
                int(clip.findtext("out")) - int(clip.findtext("in")),
                clip.findtext("name"),
            )

    def test_opening_has_no_v2_and_ending_has_one_silent_v2(self):
        sequence_a = self.sequences["CAL_A_훅과첫진입"]
        self.assertEqual(len(sequence_a.findall("media/video/track")), 1)

        sequence_c = self.sequences["CAL_C_적응과공포잔존"]
        v2_names = [item.findtext("name") for item in sequence_c.findall("media/video/track[2]/clipitem")]
        audio_names = [item.findtext("name") for item in sequence_c.findall("media/audio/track/clipitem")]
        self.assertEqual(len(v2_names), 1)
        self.assertTrue(any("종료공간연속화면" in name for name in v2_names))
        self.assertFalse(any(name in audio_names for name in v2_names))

    def test_global_clip_counts_match_cutlist(self):
        linked = sum(row["audio_mode"] == "linked" for row in self.rows)
        silent = sum(row["audio_mode"] == "none" for row in self.rows)
        videos = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        audio = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem")
        self.assertEqual(len(videos), linked + silent)
        self.assertEqual(len(audio), linked * 2)


class IntegratedCalibrationV1R3XmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r3.xml").getroot()
        with (ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r3_cutlist.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.sequences = {
            item.findtext("name"): item
            for item in cls.root.findall(".//bin[name='02_시퀀스']/children/sequence")
        }

    def test_r3_has_hook_and_ending_v2_tracks_with_original_audio(self):
        self.assertEqual(list(self.sequences), [
            "CAL_A_훅과첫진입",
            "CAL_B_빛변화와코미디",
            "CAL_C_적응과공포잔존",
        ])
        self.assertEqual([len(item.findall("media/video/track")) for item in self.sequences.values()], [2, 1, 2])
        self.assertTrue(all(len(item.findall("media/audio/track")) == 2 for item in self.sequences.values()))

        hook_v2 = [
            item.findtext("name")
            for item in self.sequences["CAL_A_훅과첫진입"].findall("media/video/track[2]/clipitem")
        ]
        ending_v2 = [
            item.findtext("name")
            for item in self.sequences["CAL_C_적응과공포잔존"].findall("media/video/track[2]/clipitem")
        ]
        self.assertEqual(len(hook_v2), 1)
        self.assertTrue(any("NPC허세중엔티티근접화면" in name for name in hook_v2))
        self.assertEqual(len(ending_v2), 1)
        self.assertTrue(any("종료공간연속화면과여운" in name for name in ending_v2))

    def test_r3_every_clip_has_equal_source_and_timeline_frames(self):
        clips = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        clips += self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem")
        self.assertTrue(clips)
        for clip in clips:
            self.assertEqual(
                int(clip.findtext("end")) - int(clip.findtext("start")),
                int(clip.findtext("out")) - int(clip.findtext("in")),
                clip.findtext("name"),
            )

    def test_r3_clip_counts_and_silent_overlays_match_cutlist(self):
        linked = sum(row["audio_mode"] == "linked" for row in self.rows)
        silent = sum(row["audio_mode"] == "none" for row in self.rows)
        videos = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        audio = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem")
        self.assertEqual((linked, silent), (21, 2))
        self.assertEqual(len(videos), linked + silent)
        self.assertEqual(len(audio), linked * 2)

    def test_r3_ending_v2_extends_twenty_four_frames_past_linked_audio(self):
        sequence = self.sequences["CAL_C_적응과공포잔존"]
        v2 = sequence.find("media/video/track[2]/clipitem")
        linked_ends = [
            int(item.findtext("end"))
            for item in sequence.findall("media/audio/track/clipitem")
        ]
        self.assertIsNotNone(v2)
        self.assertEqual(int(v2.findtext("end")) - max(linked_ends), 24)


class IntegratedCalibrationV1R4XmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r4.xml").getroot()
        with (ROOT / "outputs" / "07_edit_export" / "integrated_calibration_v1_r4_cutlist.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.sequences = {
            item.findtext("name"): item
            for item in cls.root.findall(".//bin[name='02_시퀀스']/children/sequence")
        }

    def test_r4_has_no_hook_v2_and_three_purposeful_c_overlays(self):
        self.assertEqual(list(self.sequences), [
            "CAL_A_훅과첫진입",
            "CAL_B_빛변화와코미디",
            "CAL_C_적응과공포잔존",
        ])
        self.assertEqual([len(item.findall("media/video/track")) for item in self.sequences.values()], [1, 1, 2])
        self.assertTrue(all(len(item.findall("media/audio/track")) == 2 for item in self.sequences.values()))
        c_v2 = [
            item.findtext("name")
            for item in self.sequences["CAL_C_적응과공포잔존"].findall("media/video/track[2]/clipitem")
        ]
        self.assertEqual(len(c_v2), 3)
        self.assertTrue(any("이전통로회고화면" in name for name in c_v2))
        self.assertTrue(any("종료선언이전방화면" in name for name in c_v2))
        self.assertTrue(any("자백이전방화면과여운" in name for name in c_v2))

    def test_r4_every_clip_has_equal_source_and_timeline_frames(self):
        clips = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        clips += self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem")
        self.assertTrue(clips)
        for clip in clips:
            self.assertEqual(
                int(clip.findtext("end")) - int(clip.findtext("start")),
                int(clip.findtext("out")) - int(clip.findtext("in")),
                clip.findtext("name"),
            )

    def test_r4_clip_counts_match_cutlist_and_confession_tail_is_twenty_four_frames(self):
        linked = sum(row["audio_mode"] == "linked" for row in self.rows)
        silent = sum(row["audio_mode"] == "none" for row in self.rows)
        videos = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        audio = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem")
        self.assertEqual((linked, silent), (20, 3))
        self.assertEqual(len(videos), linked + silent)
        self.assertEqual(len(audio), linked * 2)

        sequence = self.sequences["CAL_C_적응과공포잔존"]
        confession_v2 = next(
            item for item in sequence.findall("media/video/track[2]/clipitem")
            if "자백이전방화면과여운" in item.findtext("name")
        )
        linked_ends = [int(item.findtext("end")) for item in sequence.findall("media/audio/track/clipitem")]
        self.assertEqual(int(confession_v2.findtext("end")) - max(linked_ends), 24)


if __name__ == "__main__":
    unittest.main()
