import importlib.util
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "premiere-editing-export"
    / "scripts"
    / "make_premiere_xml.py"
)
SPEC = importlib.util.spec_from_file_location("make_premiere_xml", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PremiereXmlTests(unittest.TestCase):
    def source(self, index=1, name="source.mp4", fps=Fraction(60, 1), channels=2):
        media = MODULE.MediaInfo(5000.0, 1920, 1080, fps, 48000, channels)
        return MODULE.SourceInfo(index, Path(name), media, MODULE.seconds_to_frames(media.duration, fps))

    def cut(self, index, start, end, *, sequence="", cut_id="", source="source.mp4", order=0):
        return MODULE.Cut(
            index,
            start,
            end,
            f"label_{index}",
            source=source,
            sequence=sequence,
            cut_id=cut_id or f"cut_{index}",
            order=order or index,
        )

    def build(self, cuts, sources=None):
        sources = sources or {"source.mp4": self.source()}
        return MODULE.build_xml(
            "TEST",
            "LEGACY_SEQUENCE",
            cuts,
            sources,
            candidates=False,
        )

    def test_source_and_timeline_frame_lengths_match(self):
        root = self.build([self.cut(1, 2119.78, 2120.29)])
        clip = root.find(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
        timeline = int(clip.findtext("end")) - int(clip.findtext("start"))
        source = int(clip.findtext("out")) - int(clip.findtext("in"))
        self.assertEqual(source, timeline)
        self.assertEqual(int(clip.findtext("duration")), 300000)

    def test_multi_sequence_groups_start_at_zero_and_follow_order(self):
        cuts = [
            self.cut(1, 2.0, 3.0, sequence="SEQ_A", cut_id="A2", order=2),
            self.cut(2, 0.0, 1.0, sequence="SEQ_A", cut_id="A1", order=1),
            self.cut(3, 4.0, 5.0, sequence="SEQ_B", cut_id="B1", order=1),
        ]
        root = self.build(cuts)
        sequences = root.findall(".//bin[name='02_시퀀스']/children/sequence")
        self.assertEqual([s.findtext("name") for s in sequences], ["SEQ_A", "SEQ_B"])
        self.assertEqual([c.findtext("name") for c in sequences[0].findall("media/video/track/clipitem")], ["02_label_2", "01_label_1"])
        self.assertTrue(all(s.findtext("media/video/track/clipitem/start") == "0" for s in sequences))

    def test_build_context_is_fresh_for_each_xml(self):
        cuts = [self.cut(1, 0.0, 1.0)]
        first = self.build(cuts)
        second = self.build(cuts)
        self.assertEqual(len(first.findall(".//file/name")), 1)
        self.assertEqual(len(second.findall(".//file/name")), 1)

    def test_rejects_duplicate_ids_zero_frame_and_mixed_media(self):
        with self.assertRaisesRegex(ValueError, "중복 cut_id"):
            self.build([self.cut(1, 0.0, 1.0, cut_id="dup"), self.cut(2, 2.0, 3.0, cut_id="dup")])
        with self.assertRaisesRegex(ValueError, "0프레임 컷"):
            self.build([self.cut(1, 1.001, 1.002)])
        with self.assertRaisesRegex(ValueError, "소스 범위 밖 컷"):
            self.build([self.cut(1, 4999.0, 5001.0)])

        sources = {
            "source.mp4": self.source(),
            "source2.mp4": self.source(index=2, name="source2.mp4", fps=Fraction(30, 1)),
        }
        with self.assertRaisesRegex(ValueError, "혼합 FPS"):
            self.build(
                [self.cut(1, 0.0, 1.0), self.cut(2, 0.0, 1.0, source="source2.mp4")],
                sources,
            )
        sources["source2.mp4"] = self.source(index=2, name="source2.mp4", channels=1)
        with self.assertRaisesRegex(ValueError, "혼합 오디오 채널"):
            self.build(
                [self.cut(1, 0.0, 1.0), self.cut(2, 0.0, 1.0, source="source2.mp4")],
                sources,
            )

    def test_legacy_and_extended_csv_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            legacy = tmp / "legacy.csv"
            legacy.write_text("0,1,one\n1,2,two\n", encoding="utf-8")
            legacy_cuts = MODULE.read_cuts(legacy)
            self.assertEqual([cut.label for cut in legacy_cuts], ["one", "two"])
            self.assertEqual([cut.cut_id for cut in legacy_cuts], ["cut_001", "cut_002"])

            extended = tmp / "extended.csv"
            extended.write_text(
                "sequence,order,cut_id,start,end,label\nSEQ,2,C2,2,3,two\nSEQ,1,C1,0,1,one\n",
                encoding="utf-8",
            )
            extended_cuts = MODULE.read_cuts(extended)
            grouped = MODULE.group_cuts(extended_cuts, "fallback")
            self.assertEqual([cut.cut_id for cut in grouped["SEQ"]], ["C1", "C2"])


if __name__ == "__main__":
    unittest.main()
