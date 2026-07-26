from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image


REPO = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO
    / ".agents"
    / "skills"
    / "youtube-title-thumbnail"
    / "scripts"
    / "validate_package.py"
)
SPEC = importlib.util.spec_from_file_location("validate_title_thumbnail", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


TITLE = "AI Agent 입문 도구 추천: Obsidian·Graphiti·RAG를 구분하는 법"


class TitleThumbnailPackageTests(unittest.TestCase):
    def _package(
        self,
        *,
        visual_status: str = "approved",
        visual_time: str = "2026-07-26T08:05:00+09:00",
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory(
            prefix="title-thumbnail-package-",
            dir=REPO / "extension" / "work",
        )
        root = Path(temporary.name)
        output = root / "output"
        output.mkdir()
        (output / "video.mp4").write_bytes(b"video")
        (output / "captions.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\ncaption\n",
            encoding="utf-8",
        )
        for path, size in (
            (root / "source.png", (1672, 941)),
            (root / "master.png", (1280, 720)),
            (root / "preview.jpg", (320, 180)),
            (output / "thumbnail.jpg", (1280, 720)),
        ):
            Image.new("RGB", size, "navy").save(path)
        package = root / "youtube-title-thumbnail.json"
        package.write_text(
            json.dumps(
                {
                    "schema_version": "youtube-title-thumbnail-v2",
                    "source": {
                        "video": "output/video.mp4",
                        "captions": "output/captions.srt",
                        "channel_evidence": {
                            "status": "not_provided",
                            "note": "test",
                        },
                    },
                    "title": {
                        "selected": TITLE,
                        "status": "approved",
                        "candidates": [
                            {"text": TITLE, "angle": f"angle-{index}"}
                            for index in range(5)
                        ],
                        "rationale": "test",
                    },
                    "thumbnail": {
                        "generation_mode": "one_shot_imagegen",
                        "generated_source": "source.png",
                        "master": "master.png",
                        "upload": "output/thumbnail.jpg",
                        "mobile_preview": "preview.jpg",
                        "text": [
                            "에이전트는 왜 자꾸 까먹을까?",
                            "기억 설계부터 다릅니다",
                        ],
                        "badge": "Obsidian · Graphiti · RAG",
                        "copy_strategy": {
                            "hook": "반복되는 기억 손실",
                            "payoff": "기억 설계가 해답",
                            "scope": "Obsidian · Graphiti · RAG",
                        },
                        "generation_prompt": "finished thumbnail",
                        "generated_at": "2026-07-26T08:00:00+09:00",
                    },
                    "approval": {
                        "copy": {
                            "status": "approved",
                            "method": "explicit_user",
                            "approved_at": "2026-07-26T07:50:00+09:00",
                        },
                        "image_generation": {
                            "status": "approved",
                            "method": "explicit_user",
                            "approved_at": "2026-07-26T07:55:00+09:00",
                        },
                        "visual": {
                            "status": visual_status,
                            "method": "explicit_user",
                            "approved_at": visual_time,
                        },
                    },
                    "validation": {
                        "facts_traceable": True,
                        "text_exact": True,
                        "mobile_preview_reviewed": True,
                        "clickability_reviewed": True,
                        "title_thumbnail_not_duplicate": True,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return temporary, package

    def test_v2_approved_package_is_valid(self) -> None:
        temporary, package = self._package()
        self.addCleanup(temporary.cleanup)
        result = MODULE.validate(package, require_approved=True)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertTrue(result["approval_ready"])
        self.assertEqual(result["generation_mode"], "one_shot_imagegen")

    def test_v2_pending_visual_is_invalid_when_approval_is_required(self) -> None:
        temporary, package = self._package(visual_status="pending")
        self.addCleanup(temporary.cleanup)
        result = MODULE.validate(package, require_approved=True)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("approval.visual is not approved", result["errors"])

    def test_v2_visual_approval_cannot_predate_generation(self) -> None:
        temporary, package = self._package(
            visual_time="2026-07-26T07:59:00+09:00"
        )
        self.addCleanup(temporary.cleanup)
        result = MODULE.validate(package, require_approved=True)
        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "visual approval must not be earlier than thumbnail.generated_at",
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
