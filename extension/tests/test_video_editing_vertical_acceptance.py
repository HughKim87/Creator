from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from video_editing import (
    PREMIERE_CS6_V4_PROFILE,
    PremiereXmlError,
    clean_srt,
    validate_srt,
    validate_timeline,
    write_legacy_timeline,
    write_premiere_xml,
)


SRT = """1
00:00:00,000 --> 00:00:01,000
첫 문장

2
00:00:01,100 --> 00:00:01,050
둘째 문장

3
00:00:02,100 --> 00:00:04,000
제외할 문장
"""
HEADER = "idx,track,name,src_in,src_out,frames,tl_start,tl_end,gap_before\n"
VIDEO = (
    HEADER
    + "1,video,V001,0,100,100,0,100,0\n"
    + "2,video,V002,200,300,100,100,200,0\n"
)
AUDIO = (
    HEADER
    + "1,audio,A001,0,98,98,0,98,0\n"
    + "2,audio,A002,200,300,100,100,200,2\n"
)


class VideoEditingVerticalAcceptanceTests(unittest.TestCase):
    def test_synthetic_legacy_inputs_reach_cs6_without_source_mutation_or_hidden_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-vertical-") as raw:
            root = Path(raw)
            subtitle = root / "source.srt"
            video_csv = root / "video.csv"
            audio_csv = root / "audio.csv"
            cleaned_subtitle = root / "cleaned.srt"
            timeline_path = root / "timeline.json"
            xml_path = root / "timeline.xml"
            subtitle.write_text(SRT, encoding="utf-8", newline="\n")
            video_csv.write_text(VIDEO, encoding="utf-8", newline="\n")
            audio_csv.write_text(AUDIO, encoding="utf-8", newline="\n")
            source_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (subtitle, video_csv, audio_csv)
            }

            clean_srt(
                subtitle,
                cleaned_subtitle,
                media_end_ms=3_000,
                timestamp_overrides={2: {"end_ms": 2_000}},
                excluded_indices=frozenset({3}),
            )
            validate_srt(cleaned_subtitle, media_end_ms=3_000)

            imported = write_legacy_timeline(
                video_csv,
                audio_csv,
                timeline_path,
                timeline_id="synthetic-vertical",
                sequence_name="synthetic_vertical",
                source_id="synthetic-source",
                source_path="media/synthetic-source.mp4",
                source_total_frames=1_000,
                frame_rate_numerator=30,
                frame_rate_denominator=1,
                width=960,
                height=540,
                sample_rate=32_000,
                channels=1,
            )
            self.assertEqual(imported["semantic_gate"], "pending")
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(PremiereXmlError, "semantic_gate"):
                write_premiere_xml(
                    timeline,
                    xml_path,
                    profile=PREMIERE_CS6_V4_PROFILE,
                )
            self.assertFalse(xml_path.exists())

            timeline["semantic_gate"] = {
                "status": "passed",
                "reviewed_by": "test:explicit-semantic-review",
                "notes": "Synthetic acceptance only.",
            }
            validated = validate_timeline(timeline)
            generated = write_premiere_xml(
                validated,
                xml_path,
                profile=PREMIERE_CS6_V4_PROFILE,
            )
            self.assertEqual(generated["validation_status"], "structure-validated")
            self.assertEqual(ET.fromstring(xml_path.read_bytes()).attrib["version"], "4")
            self.assertEqual(
                {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (subtitle, video_csv, audio_csv)
                },
                source_hashes,
            )
            self.assertEqual(
                sorted(path.name for path in root.iterdir()),
                [
                    "audio.csv",
                    "cleaned.srt",
                    "source.srt",
                    "timeline.json",
                    "timeline.xml",
                    "video.csv",
                ],
            )


if __name__ == "__main__":
    unittest.main()
