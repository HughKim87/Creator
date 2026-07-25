from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "prepare-youtube-upload"
    / "scripts"
    / "prepare_upload_package.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_upload_package", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ManualUploadPackageTests(unittest.TestCase):
    def _package(
        self, *, include_channel_id: bool = False
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory(prefix="manual-upload-package-")
        root = Path(temporary.name)
        (root / "video.mp4").write_bytes(b"video")
        Image.new("RGB", (1280, 720), "white").save(root / "thumbnail.jpg")
        (root / "captions.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\ncaption\n",
            encoding="utf-8",
        )
        title = "AI 하네스란? 입문자를 위한 안전한 에이전트 적용 방법 총정리"
        (root / "title-thumbnail.json").write_text(
            json.dumps(
                {
                    "title": {"selected": title},
                    "thumbnail": {"upload": "thumbnail.jpg"},
                    "validation": {"user_approved": True},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        channel = {"name": "Test channel"}
        if include_channel_id:
            channel["id"] = "UC_NOT_PROVIDED"
        package = root / "youtube-manual-upload.json"
        package.write_text(
            json.dumps(
                {
                    "schema_version": "youtube-manual-upload-v1",
                    "channel": channel,
                    "artifacts": {
                        "video": "video.mp4",
                        "thumbnail": "thumbnail.jpg",
                        "captions": "captions.srt",
                        "title_thumbnail_package": "title-thumbnail.json",
                    },
                    "metadata": {
                        "title": title,
                        "description": "description",
                        "language": "ko",
                        "caption_language": "ko",
                        "category": "교육",
                        "playlist": "",
                        "made_for_kids": False,
                        "visibility_recommendation": "private",
                    },
                    "preparation": {
                        "status": "ready",
                        "youtube_actions": "manual_by_user",
                        "keep_files": [],
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return temporary, package

    def _run(self, package: Path) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), str(package), "--check"]):
            with redirect_stdout(output):
                code = MODULE.main()
        return code, json.loads(output.getvalue())

    def test_channel_name_without_id_is_ready(self) -> None:
        temporary, package = self._package()
        self.addCleanup(temporary.cleanup)
        code, result = self._run(package)
        self.assertEqual(code, 0, result["errors"])
        self.assertEqual(result["status"], "ready")

    def test_channel_id_is_rejected_from_manual_package(self) -> None:
        temporary, package = self._package(include_channel_id=True)
        self.addCleanup(temporary.cleanup)
        code, result = self._run(package)
        self.assertEqual(code, 1)
        self.assertIn(
            "manual packages must not contain channel IDs",
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
