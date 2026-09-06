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


REPO = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO
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


TITLE = "AI 하네스란? 입문자를 위한 안전한 에이전트 적용 방법 총정리"


class ManualUploadPackageTests(unittest.TestCase):
    def test_finalizer_rechecks_retention_and_rejects_stale_hashes_before_writes(self) -> None:
        spec = importlib.util.spec_from_file_location("editorial_fixture", Path(__file__).with_name("test_title_thumbnail_package.py"))
        fixture_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture_module)
        fixture = fixture_module.TitleThumbnailPackageTests()
        self.addCleanup(fixture.doCleanups)
        _, title_path = fixture._editorial_package()
        temporary, template = self._package(schema="youtube-manual-upload-v3")
        self.addCleanup(temporary.cleanup)
        data = json.loads(template.read_text(encoding="utf-8"))
        title_data = json.loads(title_path.read_text(encoding="utf-8"))
        data["metadata"]["title"] = title_data["title"]["selected"]
        data["artifacts"]["title_thumbnail_package"] = title_path.name
        data["artifact_hashes"] = {key: MODULE.sha256(title_path.parent / value) for key, value in data["artifacts"].items()}
        package = title_path.with_name("youtube-manual-upload.json")
        package.write_text(json.dumps(data), encoding="utf-8")
        finalizer_spec = importlib.util.spec_from_file_location("finalizer", SCRIPT.with_name("finalize_upload_package.py"))
        finalizer = importlib.util.module_from_spec(finalizer_spec)
        finalizer_spec.loader.exec_module(finalizer)
        guide = title_path.parent / "output/YOUTUBE-MANUAL-UPLOAD.md"
        self.assertEqual(finalizer.finalize(package)["status"], "ready")
        self.assertFalse(guide.exists())
        extra = title_path.parent / "output/technical.txt"
        extra.write_text("technical", encoding="utf-8")
        result = finalizer.finalize(package, apply=True)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["checks"]["retention_after"]["archive"], [])
        self.assertFalse(extra.exists())
        self.assertEqual(len(list(guide.parent.iterdir())), 4)
        self.assertIn(data["metadata"]["title"], guide.read_text(encoding="utf-8"))
        original_guide = guide.read_bytes()
        data["artifact_hashes"]["thumbnail"] = "0" * 64
        package.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            finalizer.finalize(package, apply=True)
        self.assertEqual(guide.read_bytes(), original_guide)

    def _package(
        self,
        *,
        schema: str = "youtube-manual-upload-v1",
        include_channel_id: bool = False,
        visual_approved: bool = True,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory(
            prefix="manual-upload-package-",
            dir=REPO / "extension" / "work",
        )
        root = Path(temporary.name)
        output = root if schema.endswith("-v1") else root / "output"
        output.mkdir(exist_ok=True)
        (output / "video.mp4").write_bytes(b"video")
        Image.new("RGB", (1280, 720), "white").save(
            output / "thumbnail.jpg"
        )
        (output / "captions.srt").write_text(
            "1\n00:00:00,000 --> 00:00:01,000\ncaption\n",
            encoding="utf-8",
        )

        title_package = root / "title-thumbnail.json"
        if schema in {
            "youtube-manual-upload-v2",
            "youtube-manual-upload-v3",
        }:
            title_schema = (
                "youtube-title-thumbnail-v3"
                if schema.endswith("-v3")
                else "youtube-title-thumbnail-v2"
            )
            title_data = {
                "schema_version": title_schema,
                "title": {
                    "selected": TITLE,
                    "status": "approved",
                    "approval_method": "explicit_user",
                },
                "thumbnail": {"upload": "output/thumbnail.jpg"},
                "approval": {
                    "copy": {
                        "status": "approved",
                        "method": "explicit_user",
                    },
                    "image_generation": {
                        "status": "approved",
                        "method": "explicit_user",
                    },
                    "visual": {
                        "status": "approved" if visual_approved else "pending",
                        "method": "explicit_user",
                    },
                },
            }
            if schema.endswith("-v3"):
                title_data["approval_policy"] = {
                    "mode": "review_gated",
                    "instruction_source": "explicit_user",
                }
        else:
            title_data = {
                "schema_version": "youtube-title-thumbnail-v1",
                "title": {"selected": TITLE, "status": "approved"},
                "thumbnail": {"upload": "thumbnail.jpg"},
                "validation": {"user_approved": True},
            }
        title_package.write_text(
            json.dumps(title_data, ensure_ascii=False),
            encoding="utf-8",
        )

        channel = {"name": "Test channel"}
        if include_channel_id:
            channel["id"] = "UC_NOT_PROVIDED"
        package = root / "youtube-manual-upload.json"
        preparation: dict[str, object] = {
            "status": "ready",
            "youtube_actions": "manual_by_user",
        }
        artifact_prefix = "" if schema.endswith("-v1") else "output/"
        if schema in {
            "youtube-manual-upload-v2",
            "youtube-manual-upload-v3",
        }:
            preparation.update(
                {
                    "output_dir": "output",
                    "guide": "output/YOUTUBE-MANUAL-UPLOAD.md",
                    "archive_dir": "archive",
                    "final_output_files": [
                        "video.mp4",
                        "thumbnail.jpg",
                        "captions.srt",
                        "YOUTUBE-MANUAL-UPLOAD.md",
                    ],
                }
            )
        else:
            preparation["keep_files"] = []
        data = {
                    "schema_version": schema,
                    "channel": channel,
                    "artifacts": {
                        "video": f"{artifact_prefix}video.mp4",
                        "thumbnail": f"{artifact_prefix}thumbnail.jpg",
                        "captions": f"{artifact_prefix}captions.srt",
                        "title_thumbnail_package": "title-thumbnail.json",
                    },
                    "metadata": {
                        "title": TITLE,
                        "description": "description",
                        "language": "ko",
                        "caption_language": "ko",
                        "category": "교육",
                        "playlist": "",
                        "made_for_kids": False,
                        "visibility_recommendation": "private",
                    },
                    "preparation": preparation,
                }
        if schema == "youtube-manual-upload-v3":
            data["artifact_hashes"] = {
                "video": MODULE.sha256(output / "video.mp4"),
                "thumbnail": MODULE.sha256(output / "thumbnail.jpg"),
                "captions": MODULE.sha256(output / "captions.srt"),
                "title_thumbnail_package": MODULE.sha256(title_package),
            }
        package.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
        return temporary, package

    def _run(self, package: Path) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), str(package), "--check"]):
            with redirect_stdout(output):
                code = MODULE.main()
        return code, json.loads(output.getvalue())

    def test_v1_channel_name_without_id_is_ready(self) -> None:
        temporary, package = self._package()
        self.addCleanup(temporary.cleanup)
        code, result = self._run(package)
        self.assertEqual(code, 0, result["errors"])
        self.assertEqual(result["status"], "ready")

    def test_v2_four_file_contract_is_ready(self) -> None:
        temporary, package = self._package(schema="youtube-manual-upload-v2")
        self.addCleanup(temporary.cleanup)
        code, result = self._run(package)
        self.assertEqual(code, 0, result["errors"])
        self.assertEqual(
            set(result["finalization"]["final_output_files"]),
            {
                "video.mp4",
                "thumbnail.jpg",
                "captions.srt",
                "YOUTUBE-MANUAL-UPLOAD.md",
            },
        )

    def test_v2_rejects_unapproved_final_visual(self) -> None:
        temporary, package = self._package(
            schema="youtube-manual-upload-v2",
            visual_approved=False,
        )
        self.addCleanup(temporary.cleanup)
        code, result = self._run(package)
        self.assertEqual(code, 1)
        self.assertIn(
            "title-thumbnail approval.visual is not approved",
            result["errors"],
        )

    def test_v3_hash_contract_is_ready(self) -> None:
        temporary, package = self._package(schema="youtube-manual-upload-v3")
        self.addCleanup(temporary.cleanup)
        code, result = self._run(package)
        self.assertEqual(code, 0, result["errors"])
        self.assertEqual(result["status"], "ready")

    def test_v3_thumbnail_change_invalidates_package(self) -> None:
        temporary, package = self._package(schema="youtube-manual-upload-v3")
        self.addCleanup(temporary.cleanup)
        root = package.parent
        Image.new("RGB", (1280, 720), "black").save(
            root / "output" / "thumbnail.jpg"
        )
        code, result = self._run(package)
        self.assertEqual(code, 1)
        self.assertIn("artifact hash differs: thumbnail", result["errors"])

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
