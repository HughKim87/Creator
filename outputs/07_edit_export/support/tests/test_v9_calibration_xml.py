import csv
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


class V9CalibrationXmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(ROOT / "outputs" / "07_edit_export" / "backrooms_v9_calibration_r2.xml").getroot()
        with (ROOT / "outputs" / "07_edit_export" / "v9_calibration_cutlist_r2.csv").open(encoding="utf-8-sig", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_has_exactly_three_sequences_and_expected_tracks(self):
        sequences = self.root.findall(".//bin[name='02_시퀀스']/children/sequence")
        self.assertEqual([item.findtext("name") for item in sequences], [
            "CAL_A_훅과빠른진입",
            "CAL_B_추격과코미디",
            "CAL_C_주제회수와아이러니",
        ])
        self.assertEqual([len(item.findall("media/video/track")) for item in sequences], [1, 1, 2])
        self.assertTrue(all(len(item.findall("media/audio/track")) == 2 for item in sequences))

    def test_video_and_audio_frame_lengths_match_source_ranges(self):
        for clip in self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem"):
            self.assertEqual(int(clip.findtext("end")) - int(clip.findtext("start")), int(clip.findtext("out")) - int(clip.findtext("in")))
        for clip in self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track/clipitem"):
            self.assertEqual(int(clip.findtext("end")) - int(clip.findtext("start")), int(clip.findtext("out")) - int(clip.findtext("in")))

    def test_cutaways_have_no_audio_and_entry_starts_before_32_seconds(self):
        sequences = {item.findtext("name"): item for item in self.root.findall(".//bin[name='02_시퀀스']/children/sequence")}
        sequence_a = sequences["CAL_A_훅과빠른진입"]
        self.assertEqual(len(sequence_a.findall("media/video/track")), 1)
        entry = next(item for item in sequence_a.findall("media/video/track[1]/clipitem") if "영화첫장면같은백룸진입" in item.findtext("name"))
        self.assertLessEqual(int(entry.findtext("start")), 32 * 60)

        sequence_c = sequences["CAL_C_주제회수와아이러니"]
        video_names = [item.findtext("name") for item in sequence_c.findall("media/video/track[2]/clipitem")]
        audio_names = [item.findtext("name") for item in sequence_c.findall("media/audio/track/clipitem")]
        self.assertEqual(len(video_names), 4)
        self.assertFalse(any(name in audio_names for name in video_names))

    def test_global_clip_counts_match_cutlist_contract(self):
        linked = sum(row["audio_mode"] == "linked" for row in self.rows)
        silent = sum(row["audio_mode"] == "none" for row in self.rows)
        videos = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        audio_tracks = self.root.findall(".//bin[name='02_시퀀스']/children/sequence/media/audio/track")
        self.assertEqual(len(videos), linked + silent)
        self.assertTrue(all(len(track.findall("clipitem")) > 0 for track in audio_tracks))
        self.assertEqual(sum(len(track.findall("clipitem")) for track in audio_tracks), linked * 2)


if __name__ == "__main__":
    unittest.main()
