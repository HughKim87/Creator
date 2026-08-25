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

from video_editing import (
    LegacyCsvError,
    PremiereXmlError,
    TimelineValidationError,
    build_premiere_xml,
    import_legacy_csv,
    inspect_timeline,
    validate_timeline,
    write_legacy_timeline,
)


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


class VideoEditingLegacyCsvTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]

    def _files(
        self,
        root: Path,
        *,
        video: str = VIDEO,
        audio: str = AUDIO,
    ) -> tuple[Path, Path]:
        video_path = root / "video.csv"
        audio_path = root / "audio.csv"
        video_path.write_text(video, encoding="utf-8", newline="\n")
        audio_path.write_text(audio, encoding="utf-8", newline="\n")
        return video_path, audio_path

    def _metadata(self) -> dict:
        return {
            "timeline_id": "synthetic-legacy-import",
            "sequence_name": "synthetic_legacy_sequence",
            "source_id": "synthetic-source",
            "source_path": "media/synthetic-source.mp4",
            "source_total_frames": 1_000,
            "frame_rate_numerator": 30_000,
            "frame_rate_denominator": 1_001,
            "width": 1_280,
            "height": 720,
            "sample_rate": 44_100,
            "channels": 2,
        }

    def test_valid_import_preserves_frames_gaps_and_requires_semantic_review(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-valid-") as raw:
            video, audio = self._files(Path(raw))
            timeline = import_legacy_csv(video, audio, **self._metadata())
            self.assertEqual(validate_timeline(timeline), timeline)
            self.assertEqual(
                [
                    (
                        clip["source_in"],
                        clip["source_out"],
                        clip["frames"],
                        clip["timeline_start"],
                        clip["timeline_end"],
                        clip["gap_before"],
                    )
                    for clip in timeline["sequence"]["audio_clips"]
                ],
                [(0, 98, 98, 0, 98, 0), (200, 300, 100, 100, 200, 2)],
            )
            all_clips = (
                timeline["sequence"]["video_clips"]
                + timeline["sequence"]["audio_clips"]
            )
            self.assertEqual({clip["edit_role"] for clip in all_clips}, {"unclassified"})
            self.assertTrue(
                all("semantic review" in clip["edit_reason"] for clip in all_clips)
            )
            self.assertEqual(timeline["semantic_gate"]["status"], "pending")
            self.assertIsNone(timeline["semantic_gate"]["reviewed_by"])

    def test_source_order_reversal_requires_exact_declared_exception(self) -> None:
        reversed_video = (
            HEADER
            + "1,video,V001,100,200,100,0,100,0\n"
            + "2,video,V002,0,100,100,100,200,0\n"
        )
        with tempfile.TemporaryDirectory(prefix="legacy-order-") as raw:
            video, audio = self._files(Path(raw), video=reversed_video)
            with self.assertRaises(LegacyCsvError) as raised:
                import_legacy_csv(video, audio, **self._metadata())
            self.assertIn(
                "undeclared_source_order",
                {issue["code"] for issue in raised.exception.issues},
            )
            timeline = import_legacy_csv(
                video,
                audio,
                source_order_exceptions=frozenset({"V002"}),
                **self._metadata(),
            )
            self.assertTrue(
                timeline["sequence"]["video_clips"][1]["source_order_exception"]
            )
            with self.assertRaises(LegacyCsvError) as unknown:
                import_legacy_csv(
                    video,
                    audio,
                    source_order_exceptions=frozenset({"missing-clip"}),
                    **self._metadata(),
                )
            self.assertEqual(
                unknown.exception.issues[0]["code"],
                "unknown_source_order_exception",
            )

    def test_csv_structure_errors_are_aggregated_in_stable_order(self) -> None:
        invalid_video = (
            HEADER
            + "1,video,V001,zero,100,100,0,100,0\n"
            + "1,audio,V002,200,300,100,100,200,0\n"
        )
        invalid_audio = (
            HEADER
            + "1,video,A001,0,98,ninety-eight,0,98,0\n"
        )
        with tempfile.TemporaryDirectory(prefix="legacy-csv-errors-") as raw:
            video, audio = self._files(
                Path(raw),
                video=invalid_video,
                audio=invalid_audio,
            )
            with self.assertRaises(LegacyCsvError) as first:
                import_legacy_csv(video, audio, **self._metadata())
            with self.assertRaises(LegacyCsvError) as second:
                import_legacy_csv(video, audio, **self._metadata())
            self.assertEqual(first.exception.issues, second.exception.issues)
            self.assertEqual(
                [issue["code"] for issue in first.exception.issues],
                [
                    "csv_integer",
                    "duplicate_csv_index",
                    "csv_track",
                    "csv_integer",
                    "csv_track",
                ],
            )
            for issue in first.exception.issues:
                self.assertEqual(
                    set(issue),
                    {"code", "message", "track", "clip_id", "index"},
                )

    def test_missing_columns_and_empty_rows_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-columns-") as raw:
            root = Path(raw)
            video, audio = self._files(root, video="idx,track,name\n")
            with self.assertRaises(LegacyCsvError) as columns:
                import_legacy_csv(video, audio, **self._metadata())
            self.assertEqual(columns.exception.issues[0]["code"], "csv_columns")
            video, audio = self._files(root, video=HEADER)
            with self.assertRaises(LegacyCsvError) as rows:
                import_legacy_csv(video, audio, **self._metadata())
            self.assertEqual(rows.exception.issues[0]["code"], "csv_rows")

    def test_timeline_reports_multiple_errors_with_deterministic_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-multi-") as raw:
            video, audio = self._files(Path(raw))
            timeline = import_legacy_csv(video, audio, **self._metadata())
            invalid = deepcopy(timeline)
            invalid["source"]["total_frames"] = 250
            invalid["sequence"]["video_clips"][0]["frames"] = 99
            invalid["sequence"]["video_clips"][1]["gap_before"] = 3
            invalid["sequence"]["audio_clips"][1]["timeline_end"] = 199
            first = inspect_timeline(invalid)
            second = inspect_timeline(deepcopy(invalid))
            self.assertEqual(first, second)
            self.assertFalse(first["ok"])
            codes = [issue["code"] for issue in first["errors"]]
            for code in (
                "length_mismatch",
                "source_bounds",
                "video_gap",
                "av_total_mismatch",
            ):
                self.assertIn(code, codes)
            for issue in first["errors"]:
                self.assertEqual(
                    tuple(issue),
                    ("code", "message", "track", "clip_id", "index"),
                )
            with self.assertRaises(TimelineValidationError) as raised:
                validate_timeline(invalid)
            self.assertEqual(raised.exception.issues, first["errors"])
            self.assertEqual(raised.exception.code, first["errors"][0]["code"])

    def test_video_gap_av_mismatch_and_source_bounds_are_import_blockers(self) -> None:
        invalid_video = VIDEO.replace("100,200,0\n", "103,203,3\n")
        invalid_audio = AUDIO.replace("100,200,2\n", "100,199,2\n")
        metadata = self._metadata()
        metadata["source_total_frames"] = 250
        with tempfile.TemporaryDirectory(prefix="legacy-gates-") as raw:
            video, audio = self._files(
                Path(raw),
                video=invalid_video,
                audio=invalid_audio,
            )
            with self.assertRaises(LegacyCsvError) as raised:
                import_legacy_csv(video, audio, **metadata)
            codes = {issue["code"] for issue in raised.exception.issues}
            self.assertTrue(
                {
                    "video_gap",
                    "length_mismatch",
                    "source_bounds",
                    "av_total_mismatch",
                }.issubset(codes)
            )

    def test_pending_import_cannot_generate_premiere_xml(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-pending-") as raw:
            video, audio = self._files(Path(raw))
            timeline = import_legacy_csv(video, audio, **self._metadata())
            with self.assertRaisesRegex(PremiereXmlError, "semantic_gate"):
                build_premiere_xml(timeline)

    def test_schema_explicitly_supports_only_unreviewed_import_role_addition(self) -> None:
        schema = json.loads(
            (
                self.root
                / "extension"
                / "schemas"
                / "video-edit-timeline-v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        roles = schema["$defs"]["clip"]["properties"]["edit_role"]["enum"]
        self.assertEqual(roles.count("unclassified"), 1)

    def test_writer_is_byte_deterministic_and_refuses_overwrite_or_missing_parent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-write-") as raw:
            root = Path(raw)
            video, audio = self._files(root)
            first_path = root / "first.json"
            second_path = root / "second.json"
            first = write_legacy_timeline(
                video,
                audio,
                first_path,
                **self._metadata(),
            )
            second = write_legacy_timeline(
                video,
                audio,
                second_path,
                **self._metadata(),
            )
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())
            self.assertEqual(
                first["sha256"],
                hashlib.sha256(first_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(first["sha256"], second["sha256"])
            with self.assertRaisesRegex(LegacyCsvError, "already exists"):
                write_legacy_timeline(
                    video,
                    audio,
                    first_path,
                    **self._metadata(),
                )
            missing = root / "missing" / "timeline.json"
            with self.assertRaisesRegex(LegacyCsvError, "does not exist"):
                write_legacy_timeline(video, audio, missing, **self._metadata())
            self.assertFalse(missing.exists())
            self.assertFalse((root / "missing").exists())

    def test_failed_import_creates_no_json_or_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-no-output-") as raw:
            root = Path(raw)
            video, audio = self._files(root, video=VIDEO.replace("100,100", "99,100"))
            output = root / "timeline.json"
            with self.assertRaises(LegacyCsvError):
                write_legacy_timeline(
                    video,
                    audio,
                    output,
                    **self._metadata(),
                )
            self.assertFalse(output.exists())
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                ["audio.csv", "video.csv"],
            )

    def test_cli_writes_only_explicit_pending_json_and_reports_failures(self) -> None:
        with tempfile.TemporaryDirectory(prefix="legacy-cli-") as raw:
            root = Path(raw)
            video, audio = self._files(root)
            output = root / "timeline.json"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [
                    str(self.root / "core" / "src"),
                    str(self.root / "extension" / "src"),
                ]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUTF8"] = "1"
            metadata = self._metadata()
            command = [
                sys.executable,
                "-m",
                "video_editing",
                "import-csv",
                "--video-csv",
                str(video),
                "--audio-csv",
                str(audio),
                "--output",
                str(output),
                "--timeline-id",
                metadata["timeline_id"],
                "--sequence-name",
                metadata["sequence_name"],
                "--source-id",
                metadata["source_id"],
                "--source-path",
                metadata["source_path"],
                "--source-total-frames",
                str(metadata["source_total_frames"]),
                "--frame-rate-numerator",
                str(metadata["frame_rate_numerator"]),
                "--frame-rate-denominator",
                str(metadata["frame_rate_denominator"]),
                "--width",
                str(metadata["width"]),
                "--height",
                str(metadata["height"]),
                "--sample-rate",
                str(metadata["sample_rate"]),
                "--channels",
                str(metadata["channels"]),
            ]
            success = subprocess.run(
                command,
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(success.returncode, 0, success.stderr)
            payload = json.loads(success.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["result"]["semantic_gate"], "pending")
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                ["audio.csv", "timeline.json", "video.csv"],
            )
            failure = subprocess.run(
                command,
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(failure.returncode, 2)
            error = json.loads(failure.stderr)
            self.assertEqual(error["error"]["kind"], "legacy_csv_error")
            self.assertEqual(error["error"]["issues"][0]["code"], "output_exists")


if __name__ == "__main__":
    unittest.main()
