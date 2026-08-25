from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "video-to-srt"
    / "scripts"
    / "review_srt.py"
)
SPEC = importlib.util.spec_from_file_location("review_srt", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CaptionReviewTests(unittest.TestCase):
    def _files(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path]:
        temporary = tempfile.TemporaryDirectory(prefix="caption-review-")
        root = Path(temporary.name)
        srt = root / "captions.srt"
        srt.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\n무한 루프\n",
            encoding="utf-8",
        )
        raw = root / "transcript.json"
        raw.write_text(
            json.dumps(
                {
                    "segments": [
                        {
                            "id": 1,
                            "words": [
                                {
                                    "start": 0.0,
                                    "end": 0.5,
                                    "word": "무할루프",
                                    "probability": 0.6,
                                }
                            ],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        glossary = root / "glossary.json"
        glossary.write_text(
            json.dumps(
                {
                    "replacements": [
                        {"from": "무할루프", "to": "무한 루프"},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return temporary, srt, raw, glossary

    def test_full_read_confirmation_produces_reviewed_status(self) -> None:
        temporary, srt, raw, glossary = self._files()
        self.addCleanup(temporary.cleanup)
        result = MODULE.build_review(
            srt,
            raw,
            glossary,
            low_confidence_threshold=0.85,
            confirm_full_read=True,
        )
        self.assertEqual(result["status"], "reviewed")
        self.assertTrue(result["manual_review"]["full_srt_reviewed"])
        self.assertEqual(result["replacement_source_hits"], [])
        self.assertFalse(result["low_confidence_words"][0]["present_in_final_srt"])

    def test_unresolved_replacement_source_is_invalid(self) -> None:
        temporary, srt, raw, glossary = self._files()
        self.addCleanup(temporary.cleanup)
        srt.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\n무할루프\n",
            encoding="utf-8",
        )
        result = MODULE.build_review(
            srt,
            raw,
            glossary,
            low_confidence_threshold=0.85,
            confirm_full_read=True,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["replacement_source_hits"][0]["from"], "무할루프")


if __name__ == "__main__":
    unittest.main()
