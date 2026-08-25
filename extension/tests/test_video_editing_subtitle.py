from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from video_editing import (
    SubtitleError,
    clean_srt,
    parse_srt,
    validate_cues,
    validate_srt,
)


VALID = """1
00:00:00,000 --> 00:00:01,000
첫 줄

2
00:00:01,100 --> 00:00:02,000
두 번째

3
00:00:02,100 --> 00:00:03,000
세 번째
"""

REPAIRABLE = """1
00:00:00,000 --> 00:00:01,000
첫 줄

2
00:00:01,100 --> 00:00:01,050
두 번째

3
00:00:02,000 --> 00:00:03,000
세 번째

4
00:00:03,100 --> 00:00:05,500
미디어 밖 마지막
"""


class VideoEditingSubtitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]

    def _write(self, root: Path, content: str = VALID) -> Path:
        source = root / "source.srt"
        source.write_text(content, encoding="utf-8", newline="\n")
        return source

    def test_valid_parse_and_validation_report_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-valid-") as raw:
            source = self._write(Path(raw))
            first = validate_srt(source, media_end_ms=3_000)
            second = validate_srt(source, media_end_ms=3_000)
            self.assertEqual(first, second)
            self.assertEqual(first["cues"], 3)
            self.assertEqual(first["end_ms"], 3_000)

    def test_bom_and_crlf_are_accepted_and_rendered_canonically(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-bom-") as raw:
            root = Path(raw)
            source = root / "source.srt"
            destination = root / "cleaned.srt"
            source.write_bytes(b"\xef\xbb\xbf" + VALID.replace("\n", "\r\n").encode("utf-8"))
            result = clean_srt(
                source,
                destination,
                media_end_ms=3_000,
                timestamp_overrides={},
            )
            self.assertEqual(result["source_cues"], 3)
            self.assertNotIn(b"\r\n", destination.read_bytes())
            self.assertFalse(destination.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_invalid_encoding_timestamp_and_duration_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-invalid-") as raw:
            root = Path(raw)
            source = root / "source.srt"
            source.write_bytes(b"1\n00:00:00,000 --> 00:00:01,000\n\xff\n")
            with self.assertRaisesRegex(SubtitleError, "strict UTF-8"):
                parse_srt(source)
            source.write_text(
                "1\n00:99:00,000 --> 00:99:01,000\ntext\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SubtitleError, "invalid timestamp"):
                parse_srt(source)
            source.write_text(
                "1\n00:00:01,000 --> 00:00:01,000\ntext\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SubtitleError, "positive duration"):
                validate_cues(parse_srt(source))

    def test_index_overlap_and_media_bounds_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-order-") as raw:
            root = Path(raw)
            source = self._write(root)
            cues = parse_srt(source)
            with self.assertRaisesRegex(SubtitleError, "sequential"):
                validate_cues([cues[0], cues[2]])
            overlap = VALID.replace("00:00:01,100", "00:00:00,900")
            source.write_text(overlap, encoding="utf-8")
            with self.assertRaisesRegex(SubtitleError, "overlaps"):
                validate_cues(parse_srt(source))
            source.write_text(VALID, encoding="utf-8")
            with self.assertRaisesRegex(SubtitleError, "media duration"):
                validate_cues(parse_srt(source), media_end_ms=2_999)

    def test_explicit_override_and_middle_exclusion_preserve_source_and_text(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-clean-") as raw:
            root = Path(raw)
            source = self._write(root, REPAIRABLE)
            destination = root / "cleaned.srt"
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            original_text = {cue.index: cue.text_lines for cue in parse_srt(source)}
            result = clean_srt(
                source,
                destination,
                media_end_ms=5_000,
                timestamp_overrides={2: {"end_ms": 1_900}},
                excluded_indices=frozenset({3, 4}),
            )
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            self.assertEqual(result["changed_indices"], [2, 3, 4])
            self.assertEqual(result["excluded_indices"], [3, 4])
            cleaned = parse_srt(destination)
            validate_cues(cleaned, media_end_ms=5_000)
            self.assertEqual(
                [cue.text_lines for cue in cleaned],
                [original_text[1], original_text[2]],
            )

    def test_unknown_override_conflict_and_unknown_field_create_no_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-explicit-") as raw:
            root = Path(raw)
            source = self._write(root)
            cases = (
                ({4: {"end_ms": 2_000}}, frozenset(), "unknown cue"),
                ({2: {"end_ms": 2_000}}, frozenset({2}), "cannot have overrides"),
                ({2: {"duration_ms": 900}}, frozenset(), "unknown timestamp"),
            )
            for number, (overrides, excluded, message) in enumerate(cases):
                destination = root / f"out-{number}.srt"
                with self.assertRaisesRegex(SubtitleError, message):
                    clean_srt(
                        source,
                        destination,
                        media_end_ms=3_000,
                        timestamp_overrides=overrides,
                        excluded_indices=excluded,
                    )
                self.assertFalse(destination.exists())

    def test_source_destination_parent_and_existing_output_guards(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-guards-") as raw:
            root = Path(raw)
            source = self._write(root)
            with self.assertRaisesRegex(SubtitleError, "different files"):
                clean_srt(
                    source,
                    source,
                    media_end_ms=3_000,
                    timestamp_overrides={},
                )
            missing = root / "missing" / "out.srt"
            with self.assertRaisesRegex(SubtitleError, "does not exist"):
                clean_srt(
                    source,
                    missing,
                    media_end_ms=3_000,
                    timestamp_overrides={},
                )
            destination = root / "out.srt"
            destination.write_text("user content\n", encoding="utf-8")
            with self.assertRaisesRegex(SubtitleError, "already exists"):
                clean_srt(
                    source,
                    destination,
                    media_end_ms=3_000,
                    timestamp_overrides={},
                )
            self.assertEqual(destination.read_text(encoding="utf-8"), "user content\n")
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                ["out.srt", "source.srt"],
            )

    def test_failed_cleanup_leaves_no_destination_or_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-no-partial-") as raw:
            root = Path(raw)
            source = self._write(root, REPAIRABLE)
            destination = root / "out.srt"
            with self.assertRaisesRegex(SubtitleError, "positive duration"):
                clean_srt(
                    source,
                    destination,
                    media_end_ms=5_000,
                    timestamp_overrides={},
                    excluded_indices=frozenset({4}),
                )
            self.assertEqual([item.name for item in root.iterdir()], ["source.srt"])

    def test_cli_validate_and_clean_emit_json_and_only_requested_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="subtitle-cli-") as raw:
            root = Path(raw)
            source = self._write(root, REPAIRABLE)
            destination = root / "cleaned.srt"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                [
                    str(self.root / "core" / "src"),
                    str(self.root / "extension" / "src"),
                ]
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUTF8"] = "1"
            clean = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "video_editing",
                    "subtitle-clean",
                    "--source",
                    str(source),
                    "--destination",
                    str(destination),
                    "--media-end-ms",
                    "5000",
                    "--end",
                    "2=1900",
                    "--exclude",
                    "4",
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(clean.returncode, 0, clean.stderr)
            self.assertTrue(json.loads(clean.stdout)["ok"])
            validate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "video_editing",
                    "subtitle-validate",
                    "--source",
                    str(destination),
                    "--media-end-ms",
                    "5000",
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertTrue(json.loads(validate.stdout)["ok"])
            self.assertEqual(
                sorted(item.name for item in root.iterdir()),
                ["cleaned.srt", "source.srt"],
            )


if __name__ == "__main__":
    unittest.main()
