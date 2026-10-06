from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from video_editing import (
    PREMIERE_CS6_V4_PROFILE,
    SEQUENCE_V5_PROFILE,
    SUPPORTED_XML_PROFILES,
    PremiereXmlError,
    TimelineValidationError,
)
from video_editing.premiere_xml import _build_premiere_xml, _write_premiere_xml


class VideoEditingPremiereCs6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.example_path = (
            cls.root / "extension" / "examples" / "video-edit-timeline-v1.json"
        )

    def _timeline(self) -> dict:
        return json.loads(self.example_path.read_text(encoding="utf-8"))

    def _cs6_root(self, timeline: dict | None = None) -> ET.Element:
        return ET.fromstring(
            _build_premiere_xml(
                timeline or self._timeline(),
                profile=PREMIERE_CS6_V4_PROFILE,
            )
        )

    def test_profile_ids_are_explicit_and_sequence_v5_byte_regression_is_preserved(
        self,
    ) -> None:
        timeline = self._timeline()
        default = _build_premiere_xml(timeline)
        explicit = _build_premiere_xml(timeline, profile=SEQUENCE_V5_PROFILE)
        self.assertEqual(default, explicit)
        self.assertEqual(len(default), 11_629)
        self.assertEqual(
            hashlib.sha256(default).hexdigest(),
            "9553f10ace7728334187edaafe159d2a4a02b8afdcb21ad95ad65d0a226de100",
        )
        self.assertEqual(
            SUPPORTED_XML_PROFILES,
            {SEQUENCE_V5_PROFILE, PREMIERE_CS6_V4_PROFILE},
        )

    def test_cs6_has_declaration_doctype_and_exact_project_structure(self) -> None:
        rendered = _build_premiere_xml(
            self._timeline(),
            profile=PREMIERE_CS6_V4_PROFILE,
        )
        self.assertTrue(
            rendered.startswith(
                b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n'
            )
        )
        root = ET.fromstring(rendered)
        self.assertEqual(root.tag, "xmeml")
        self.assertEqual(root.attrib, {"version": "4"})
        self.assertEqual(len(root.findall("./project")), 1)
        self.assertEqual(len(root.findall("./project/children/bin")), 1)
        self.assertEqual(
            len(root.findall("./project/children/bin/children/clip")),
            1,
        )
        self.assertEqual(
            len(root.findall("./project/children/bin/children/sequence")),
            1,
        )

    def test_one_master_file_definition_and_all_references_share_its_id(self) -> None:
        root = self._cs6_root()
        files = root.findall(".//file")
        definitions = [file for file in files if file.find("pathurl") is not None]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(
            definitions[0].findtext("pathurl"),
            "file://localhost/media/original-main.mp4",
        )
        self.assertEqual({file.attrib["id"] for file in files}, {"file-1"})
        self.assertEqual(len(root.findall(".//file/pathurl")), 1)

    def test_cs6_preserves_video_audio_ranges_gap_channels_and_output_mapping(
        self,
    ) -> None:
        root = self._cs6_root()
        sequence_path = "./project/children/bin/children/sequence"
        video_items = root.findall(f"{sequence_path}/media/video/track/clipitem")
        audio_tracks = root.findall(f"{sequence_path}/media/audio/track")
        self.assertEqual(len(video_items), 2)
        self.assertEqual(len(audio_tracks), 2)
        self.assertEqual(
            [
                (
                    item.findtext("start"),
                    item.findtext("end"),
                    item.findtext("in"),
                    item.findtext("out"),
                )
                for item in video_items
            ],
            [("0", "120", "0", "120"), ("120", "240", "300", "420")],
        )
        self.assertEqual(
            [
                (item.findtext("start"), item.findtext("end"))
                for item in audio_tracks[0].findall("clipitem")
            ],
            [("0", "118"), ("120", "240")],
        )
        self.assertEqual(
            [track.findtext("outputchannelindex") for track in audio_tracks],
            ["1", "2"],
        )
        self.assertEqual(
            [
                item.findtext("sourcetrack/trackindex")
                for item in audio_tracks[1].findall("clipitem")
            ],
            ["2", "2"],
        )

    def test_every_link_target_exists_and_uuid_and_bytes_are_deterministic(self) -> None:
        timeline = self._timeline()
        first = _build_premiere_xml(timeline, profile=PREMIERE_CS6_V4_PROFILE)
        second = _build_premiere_xml(
            deepcopy(timeline),
            profile=PREMIERE_CS6_V4_PROFILE,
        )
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        root = ET.fromstring(first)
        clip_ids = {item.attrib["id"] for item in root.findall(".//clipitem")}
        link_targets = {item.text for item in root.findall(".//link/linkclipref")}
        self.assertTrue(link_targets)
        self.assertTrue(link_targets.issubset(clip_ids))
        uuids = [item.text for item in root.findall(".//uuid")]
        self.assertEqual(len(uuids), 2)
        self.assertEqual(len(set(uuids)), 2)

    def test_cs6_uses_source_metadata_instead_of_old_fixed_media_values(self) -> None:
        timeline = self._timeline()
        timeline["source"]["frame_rate"] = {"numerator": 25, "denominator": 1}
        timeline["source"]["video"] = {"width": 640, "height": 360}
        timeline["source"]["audio"] = {"sample_rate": 32_000, "channels": 1}
        root = self._cs6_root(timeline)
        self.assertEqual(
            {item.text for item in root.findall(".//rate/timebase")},
            {"25"},
        )
        self.assertEqual(
            {item.text for item in root.findall(".//samplecharacteristics/width")},
            {"640"},
        )
        self.assertEqual(
            {item.text for item in root.findall(".//samplecharacteristics/height")},
            {"360"},
        )
        self.assertEqual(
            {item.text for item in root.findall(".//samplecharacteristics/samplerate")},
            {"32000"},
        )
        sequence_audio_tracks = root.findall(
            "./project/children/bin/children/sequence/media/audio/track"
        )
        self.assertEqual(len(sequence_audio_tracks), 1)
        self.assertEqual(sequence_audio_tracks[0].attrib["premiereTrackType"], "Mono")

    def test_cs6_matches_the_app_validated_v18_import_contract(self) -> None:
        root = self._cs6_root()
        sequence = root.find("./project/children/bin/children/sequence")
        self.assertIsNotNone(sequence)
        assert sequence is not None
        file_definition = root.find(".//file/pathurl/..")
        self.assertIsNotNone(file_definition)
        assert file_definition is not None

        self.assertEqual(file_definition.findtext("media/audio/channelcount"), "2")
        self.assertIsNone(
            file_definition.find("media/audio/samplecharacteristics/channelcount")
        )
        self.assertIsNotNone(file_definition.find("timecode/reel/name"))
        self.assertIsNone(sequence.find("in"))
        self.assertIsNone(sequence.find("out"))
        self.assertIsNone(sequence.find("media/audio/format/samplecharacteristics/rate"))
        self.assertEqual(root.findall(".//clipitem/rate"), [])
        self.assertEqual(root.findall(".//clipitem/logginginfo"), [])
        self.assertEqual(root.findall(".//clipitem/labels"), [])

        video_track = sequence.find("media/video/track")
        self.assertIsNotNone(video_track)
        assert video_track is not None
        self.assertEqual(
            [child.tag for child in list(video_track)[:2]],
            ["enabled", "locked"],
        )
        audio_track = sequence.find("media/audio/track")
        self.assertIsNotNone(audio_track)
        assert audio_track is not None
        self.assertEqual(
            [child.tag for child in list(audio_track)[:2]],
            ["enabled", "locked"],
        )

        video_item = video_track.find("clipitem")
        self.assertIsNotNone(video_item)
        assert video_item is not None
        self.assertIsNone(video_item.find("sourcetrack"))
        for link in root.findall(".//clipitem/link"):
            media_type = link.findtext("mediatype")
            if media_type == "audio":
                self.assertEqual(link.findtext("groupindex"), "1")
            else:
                self.assertIsNone(link.find("groupindex"))

    def test_invalid_profile_timeline_and_pending_gate_create_no_output(self) -> None:
        with self.assertRaisesRegex(PremiereXmlError, "unsupported"):
            _build_premiere_xml(self._timeline(), profile="unknown")
        with tempfile.TemporaryDirectory(prefix="cs6-invalid-") as raw:
            root = Path(raw)
            cases = []
            invalid = self._timeline()
            invalid["sequence"]["video_clips"][0]["frames"] = 119
            cases.append((invalid, TimelineValidationError))
            pending = self._timeline()
            pending["semantic_gate"] = {
                "status": "pending",
                "reviewed_by": None,
                "notes": "",
            }
            cases.append((pending, PremiereXmlError))
            for number, (timeline, error) in enumerate(cases):
                output = root / f"invalid-{number}.xml"
                with self.assertRaises(error):
                    _write_premiere_xml(
                        timeline,
                        output,
                        profile=PREMIERE_CS6_V4_PROFILE,
                    )
                self.assertFalse(output.exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_writer_and_cli_create_only_requested_structure_validated_xml(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cs6-write-") as raw:
            root = Path(raw)
            output = root / "timeline.xml"
            result = _write_premiere_xml(
                self._timeline(),
                output,
                profile=PREMIERE_CS6_V4_PROFILE,
            )
            self.assertEqual(result["profile"], PREMIERE_CS6_V4_PROFILE)
            self.assertEqual(result["validation_status"], "structure-validated")
            self.assertEqual(result["bytes"], output.stat().st_size)
            with self.assertRaisesRegex(PremiereXmlError, "already exists"):
                _write_premiere_xml(
                    self._timeline(),
                    output,
                    profile=PREMIERE_CS6_V4_PROFILE,
                )
            self.assertEqual([item.name for item in root.iterdir()], ["timeline.xml"])

            timeline_path = root / "timeline.json"
            contract_path = root / "edit-contract.json"
            cli_output = root / "cli.xml"
            timeline_path.write_text(
                json.dumps(self._timeline(), ensure_ascii=False),
                encoding="utf-8",
            )
            contract_path.write_text(
                (
                    self.root
                    / "extension"
                    / "examples"
                    / "video-edit-contract-v1.json"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [
                    str(self.root / "core" / "src"),
                    str(self.root / "extension" / "src"),
                ]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUTF8"] = "1"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "video_editing",
                    "premiere-xml",
                    "--timeline-json",
                    str(timeline_path),
                    "--output",
                    str(cli_output),
                    "--profile",
                    PREMIERE_CS6_V4_PROFILE,
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stdout)
            payload = json.loads(completed.stderr)
            self.assertIn("migrate-v1", payload["error"]["message"])
            self.assertFalse(cli_output.exists())
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                ["edit-contract.json", "timeline.json", "timeline.xml"],
            )


if __name__ == "__main__":
    unittest.main()
