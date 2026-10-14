import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from qwen_reference import select_reference, read_srt_file


class ReferenceTests(unittest.TestCase):
    def test_long_srt_selects_aligned_short_window(self):
        srt = "1\n00:00:00,000 --> 00:00:08,000\n첫 문장입니다.\n\n2\n00:00:08,000 --> 00:00:59,500\n두 번째입니다.\n\n3\n00:00:59,500 --> 00:01:05,000\n제외할 문장입니다."
        start, end, text = select_reference(281, srt)
        self.assertEqual((start, end), (0, 59.5))
        self.assertEqual(text, "첫 문장입니다. 두 번째입니다.")
        self.assertNotIn("-->", text)

    def test_no_silent_cut_without_matching_transcript(self):
        with self.assertRaises(ValueError):
            select_reference(281, "전체 녹음의 발화문입니다.")

    def test_wrong_srt_audio_pair_rejected(self):
        with self.assertRaises(ValueError):
            select_reference(10, "1\n00:00:00,000 --> 00:00:18,000\n문장")

    def test_offset_window_keeps_alignment(self):
        self.assertEqual(select_reference(30, "1\n00:00:03,000 --> 00:00:23,000\n문장"),
                         (0, 30, "문장"))

    def test_twenty_to_sixty_seconds_uses_full_recording(self):
        for duration in (20, 35.5, 60):
            self.assertEqual(select_reference(duration, "발화문"), (0, duration, "발화문"))

    def test_under_twenty_seconds_rejected(self):
        with self.assertRaisesRegex(ValueError, "최소 20초"):
            select_reference(19.99, "발화문")

    def test_short_srt_window_cannot_bypass_minimum(self):
        with self.assertRaises(ValueError):
            select_reference(120, "1\n00:00:00,000 --> 00:00:18,000\n짧은 문장\n\n2\n00:00:18,000 --> 00:01:05,000\n긴 문장")

    def test_srt_file_encodings_keep_korean_and_normalize_newlines(self):
        scratch = Path(__file__).resolve().parents[1] / ".runtime/qwen-tts/verification"
        scratch.mkdir(parents=True, exist_ok=True)
        text = "1\r\n00:00:00,000 --> 00:00:02,000\r\n안녕하세요.\r\n"
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            for encoding in ("utf-8-sig", "cp949"):
                path = Path(folder) / "sample.srt"
                path.write_bytes(text.encode(encoding))
                self.assertEqual(read_srt_file(path), text.replace("\r\n", "\n").strip())


if __name__ == "__main__":
    unittest.main()
