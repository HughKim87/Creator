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
    / "prepare-youtube-upload"
    / "scripts"
    / "retain_upload_package.py"
)
SPEC = importlib.util.spec_from_file_location("retain_upload_package", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class UploadRetentionTests(unittest.TestCase):
    def _package(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory(prefix="youtube-upload-retention-")
        root = Path(temporary.name)
        for name in (
            "video.mp4",
            "thumbnail.jpg",
            "captions.ko.srt",
            "youtube-title-thumbnail.json",
            "description.ko.md",
            "YOUTUBE-MANUAL-UPLOAD.md",
            "thumbnail-v2.jpg",
        ):
            (root / name).write_text(name, encoding="utf-8")
        package = root / "youtube-manual-upload.json"
        package.write_text(
            json.dumps(
                {
                    "schema_version": "youtube-manual-upload-v1",
                    "artifacts": {
                        "video": "video.mp4",
                        "thumbnail": "thumbnail.jpg",
                        "captions": "captions.ko.srt",
                        "title_thumbnail_package": "youtube-title-thumbnail.json",
                    },
                    "preparation": {
                        "keep_files": ["description.ko.md"],
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return temporary, package

    def test_dry_run_keeps_upload_assets_metadata_and_guide(self) -> None:
        temporary, package = self._package()
        self.addCleanup(temporary.cleanup)
        plan = MODULE.build_plan(package)
        self.assertEqual(plan["status"], "ready")
        self.assertIn(str(package), plan["keep"])
        self.assertIn(str(package.with_name("description.ko.md")), plan["keep"])
        self.assertIn(str(package.with_name("thumbnail-v2.jpg")), plan["delete"])
        self.assertTrue((package.parent / "thumbnail-v2.jpg").exists())

    def test_apply_deletes_only_planned_sibling_files(self) -> None:
        temporary, package = self._package()
        self.addCleanup(temporary.cleanup)
        plan = MODULE.apply_plan(MODULE.build_plan(package))
        self.assertEqual(len(plan["deleted"]), 1)
        self.assertFalse((package.parent / "thumbnail-v2.jpg").exists())
        self.assertTrue((package.parent / "video.mp4").exists())
        self.assertTrue((package.parent / "YOUTUBE-MANUAL-UPLOAD.md").exists())

    def test_rejects_keep_file_outside_package_directory(self) -> None:
        temporary, package = self._package()
        self.addCleanup(temporary.cleanup)
        data = json.loads(package.read_text(encoding="utf-8"))
        data["preparation"]["keep_files"] = ["../not-allowed.txt"]
        package.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.build_plan(package)


if __name__ == "__main__":
    unittest.main()
