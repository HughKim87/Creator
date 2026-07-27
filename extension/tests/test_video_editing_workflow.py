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
    CLIP_FIELDS,
    SEMANTIC_GATE_FIELDS,
    SEQUENCE_FIELDS,
    SOURCE_FIELDS,
    TIMELINE_FIELDS,
    PremiereXmlError,
    TimelineValidationError,
    build_premiere_xml,
    inspect_timeline,
    validate_timeline,
    write_premiere_xml,
)


class VideoEditingTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.example_path = (
            cls.root / "extension" / "examples" / "video-edit-timeline-v1.json"
        )

    def _timeline(self) -> dict:
        return json.loads(self.example_path.read_text(encoding="utf-8"))

    def _assert_code(self, timeline: dict, code: str) -> None:
        with self.assertRaises(TimelineValidationError) as raised:
            validate_timeline(timeline)
        self.assertEqual(raised.exception.code, code)
        report = inspect_timeline(timeline)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], code)

    def test_valid_timeline_is_normalized_and_deterministic(self) -> None:
        timeline = self._timeline()
        normalized = validate_timeline(timeline)
        self.assertEqual(normalized, timeline)
        first = inspect_timeline(timeline)
        second = inspect_timeline(deepcopy(timeline))
        self.assertEqual(first, second)
        self.assertTrue(first["ok"])
        self.assertEqual(first["total_frames"], 240)
        self.assertEqual(first["audio_gap_frames"], 2)
        self.assertEqual(len(first["checks"]), 9)

    def test_duplicate_clip_id_is_rejected(self) -> None:
        timeline = self._timeline()
        timeline["sequence"]["audio_clips"][0]["id"] = "V001"
        self._assert_code(timeline, "duplicate_clip_id")

    def test_invalid_frame_range_is_rejected(self) -> None:
        timeline = self._timeline()
        timeline["sequence"]["video_clips"][0]["source_out"] = 0
        self._assert_code(timeline, "invalid_fields")
        timeline = self._timeline()
        timeline["sequence"]["video_clips"][0]["source_in"] = 120
        self._assert_code(timeline, "invalid_frame_range")

    def test_length_equation_mismatch_is_rejected(self) -> None:
        timeline = self._timeline()
        timeline["sequence"]["video_clips"][0]["frames"] = 119
        self._assert_code(timeline, "length_mismatch")

    def test_video_gap_and_continuity_are_rejected(self) -> None:
        timeline = self._timeline()
        timeline["sequence"]["video_clips"][1]["gap_before"] = 1
        self._assert_code(timeline, "video_gap")
        timeline = self._timeline()
        timeline["sequence"]["video_clips"][1]["timeline_start"] = 121
        timeline["sequence"]["video_clips"][1]["timeline_end"] = 241
        self._assert_code(timeline, "video_continuity")

    def test_audio_gap_formula_is_enforced(self) -> None:
        timeline = self._timeline()
        timeline["sequence"]["audio_clips"][1]["gap_before"] = 1
        self._assert_code(timeline, "audio_continuity")

    def test_av_total_mismatch_is_rejected(self) -> None:
        timeline = self._timeline()
        audio = timeline["sequence"]["audio_clips"][1]
        audio["source_out"] -= 1
        audio["frames"] -= 1
        audio["timeline_end"] -= 1
        self._assert_code(timeline, "av_total_mismatch")

    def test_source_bounds_and_lineage_are_enforced(self) -> None:
        timeline = self._timeline()
        timeline["source"]["total_frames"] = 400
        self._assert_code(timeline, "source_bounds")
        timeline = self._timeline()
        timeline["sequence"]["audio_clips"][0]["source_id"] = "edited-copy"
        self._assert_code(timeline, "source_lineage")

    def test_source_order_reversal_requires_explicit_exception(self) -> None:
        timeline = self._timeline()
        second = timeline["sequence"]["video_clips"][1]
        second.update({"source_in": 60, "source_out": 180, "source_order_exception": False})
        self._assert_code(timeline, "undeclared_source_order")
        second["source_order_exception"] = True
        normalized = validate_timeline(timeline)
        self.assertTrue(
            normalized["sequence"]["video_clips"][1]["source_order_exception"]
        )

    def test_passed_semantic_gate_requires_reviewer(self) -> None:
        timeline = self._timeline()
        timeline["semantic_gate"]["reviewed_by"] = None
        self._assert_code(timeline, "invalid_fields")

    def test_runtime_and_schema_fields_match(self) -> None:
        schema = json.loads(
            (
                self.root
                / "extension"
                / "schemas"
                / "video-edit-timeline-v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["required"]), set(TIMELINE_FIELDS))
        self.assertEqual(
            set(schema["properties"]["source"]["required"]),
            set(SOURCE_FIELDS),
        )
        self.assertEqual(
            set(schema["properties"]["sequence"]["required"]),
            set(SEQUENCE_FIELDS),
        )
        self.assertEqual(
            set(schema["properties"]["semantic_gate"]["required"]),
            set(SEMANTIC_GATE_FIELDS),
        )
        self.assertEqual(
            set(schema["$defs"]["clip"]["required"]),
            set(CLIP_FIELDS),
        )

    def test_premiere_xml_is_deterministic_and_uses_one_original_source(self) -> None:
        timeline = self._timeline()
        first = build_premiere_xml(timeline)
        second = build_premiere_xml(deepcopy(timeline))
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        root = ET.fromstring(first)
        self.assertEqual(root.tag, "xmeml")
        self.assertEqual(root.attrib["version"], "5")
        self.assertEqual(root.findtext("./sequence/duration"), "240")
        file_ids = {element.attrib["id"] for element in root.findall(".//file")}
        self.assertEqual(file_ids, {"file-1"})
        path_urls = [
            element.text for element in root.findall(".//file/pathurl")
        ]
        self.assertEqual(path_urls, ["file://localhost/media/original-main.mp4"])

    def test_premiere_xml_preserves_clip_ranges_audio_gap_and_stereo_tracks(self) -> None:
        root = ET.fromstring(build_premiere_xml(self._timeline()))
        video_items = root.findall("./sequence/media/video/track/clipitem")
        audio_tracks = root.findall("./sequence/media/audio/track")
        audio_items = root.findall("./sequence/media/audio/track/clipitem")
        self.assertEqual(len(video_items), 2)
        self.assertEqual(len(audio_tracks), 2)
        self.assertEqual(len(audio_items), 4)
        self.assertEqual(
            [
                (
                    item.findtext("name"),
                    item.findtext("start"),
                    item.findtext("end"),
                    item.findtext("in"),
                    item.findtext("out"),
                )
                for item in video_items
            ],
            [
                ("V001", "0", "120", "0", "120"),
                ("V002", "120", "240", "300", "420"),
            ],
        )
        first_channel = audio_tracks[0].findall("clipitem")
        self.assertEqual(
            [(item.findtext("start"), item.findtext("end")) for item in first_channel],
            [("0", "118"), ("120", "240")],
        )
        linked = video_items[1].findall("link")
        self.assertEqual(len(linked), 3)

    def test_xml_generation_requires_semantic_gate_and_supported_rate(self) -> None:
        timeline = self._timeline()
        timeline["semantic_gate"].update(
            {"status": "pending", "reviewed_by": None, "notes": ""}
        )
        with self.assertRaisesRegex(PremiereXmlError, "semantic_gate"):
            build_premiere_xml(timeline)
        timeline = self._timeline()
        timeline["source"]["frame_rate"] = {"numerator": 25, "denominator": 2}
        with self.assertRaisesRegex(PremiereXmlError, "unsupported frame rate"):
            build_premiere_xml(timeline)

    def test_writer_is_atomic_and_refuses_overwrite_by_default(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-xml-") as raw:
            root = Path(raw)
            output = root / "timeline.xml"
            result = write_premiere_xml(self._timeline(), output)
            self.assertTrue(output.is_file())
            self.assertEqual(result["bytes"], output.stat().st_size)
            self.assertEqual(
                result["sha256"],
                hashlib.sha256(output.read_bytes()).hexdigest(),
            )
            self.assertEqual([item.name for item in root.iterdir()], ["timeline.xml"])
            with self.assertRaisesRegex(PremiereXmlError, "already exists"):
                write_premiere_xml(self._timeline(), output)

    def test_invalid_timeline_creates_no_xml_or_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-invalid-") as raw:
            root = Path(raw)
            output = root / "timeline.xml"
            timeline = self._timeline()
            timeline["sequence"]["video_clips"][0]["frames"] = 119
            with self.assertRaises(TimelineValidationError):
                write_premiere_xml(timeline, output)
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_validates_and_generates_only_requested_xml(self) -> None:
        with tempfile.TemporaryDirectory(prefix="video-edit-cli-") as raw:
            root = Path(raw)
            timeline_path = root / "timeline.json"
            output_path = root / "timeline.xml"
            timeline_path.write_text(
                json.dumps(self._timeline(), ensure_ascii=False),
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
            validate_command = [
                sys.executable,
                "-m",
                "video_editing",
                "validate",
                "--timeline-json",
                str(timeline_path),
            ]
            validated = subprocess.run(
                validate_command,
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["ok"])
            generate_command = [
                sys.executable,
                "-m",
                "video_editing",
                "premiere-xml",
                "--timeline-json",
                str(timeline_path),
                "--output",
                str(output_path),
            ]
            generated = subprocess.run(
                generate_command,
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertTrue(json.loads(generated.stdout)["ok"])
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                ["timeline.json", "timeline.xml"],
            )

    def test_contract_rules_replay_cases_and_owner_routing_are_complete(self) -> None:
        contract_path = (
            self.root
            / "extension"
            / "docs"
            / "domain"
            / "youtube"
            / "VIDEO_EDITING_WORKFLOW_CONTRACT.md"
        )
        contract = contract_path.read_text(encoding="utf-8")
        for number in range(1, 13):
            rule_id = f"R{number:02d}"
            start = contract.index(f"### {rule_id}")
            next_heading = (
                contract.index(f"### R{number + 1:02d}", start)
                if number < 12
                else contract.index("## 7.", start)
            )
            block = contract[start:next_heading]
            self.assertEqual(contract.count(f"### {rule_id} "), 1)
            for field in ("조건", "행동", "예외", "검증"):
                self.assertIn(f"- {field}:", block)
        replay_ids = [
            line.split("|")[1].strip()
            for line in contract.splitlines()
            if line.startswith("| TC")
        ]
        self.assertEqual(replay_ids, [f"TC{number:02d}" for number in range(1, 13)])
        self.assertNotIn("local_changes_backup", contract)
        self.assertNotIn("extension/reports", contract)
        readme = (
            self.root / "extension" / "README.md"
        ).read_text(encoding="utf-8")
        owner = "docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md"
        self.assertEqual(readme.count(owner), 1)


if __name__ == "__main__":
    unittest.main()
