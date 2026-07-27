from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from video_editing import (
    CLIP_FIELDS,
    SEMANTIC_GATE_FIELDS,
    SEQUENCE_FIELDS,
    SOURCE_FIELDS,
    TIMELINE_FIELDS,
    TimelineValidationError,
    inspect_timeline,
    validate_timeline,
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


if __name__ == "__main__":
    unittest.main()
