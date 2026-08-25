from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO
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
    def _package(
        self,
        *,
        schema: str = "youtube-manual-upload-v2",
    ) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path]:
        temporary = tempfile.TemporaryDirectory(
            prefix="youtube-upload-retention-",
            dir=REPO / "extension" / "work",
        )
        root = Path(temporary.name)
        output = root / "output"
        archive = root / "archive"
        output.mkdir()
        for name in (
            "video.mp4",
            "thumbnail.jpg",
            "captions.ko.srt",
            "YOUTUBE-MANUAL-UPLOAD.md",
            "technical.json",
        ):
            (output / name).write_text(name, encoding="utf-8")
        package = root / "youtube-manual-upload.json"
        title_package = root / "youtube-title-thumbnail.json"
        title_package.write_text("{}", encoding="utf-8")
        data = {
                    "schema_version": schema,
                    "artifacts": {
                        "video": "output/video.mp4",
                        "thumbnail": "output/thumbnail.jpg",
                        "captions": "output/captions.ko.srt",
                        "title_thumbnail_package": "youtube-title-thumbnail.json",
                    },
                    "preparation": {
                        "status": "ready",
                        "youtube_actions": "manual_by_user",
                        "output_dir": "output",
                        "guide": "output/YOUTUBE-MANUAL-UPLOAD.md",
                        "archive_dir": "archive",
                        "final_output_files": [
                            "video.mp4",
                            "thumbnail.jpg",
                            "captions.ko.srt",
                            "YOUTUBE-MANUAL-UPLOAD.md",
                        ],
                    },
                }
        if schema == "youtube-manual-upload-v3":
            data["artifact_hashes"] = {
                "video": MODULE._sha256(output / "video.mp4"),
                "thumbnail": MODULE._sha256(output / "thumbnail.jpg"),
                "captions": MODULE._sha256(output / "captions.ko.srt"),
                "title_thumbnail_package": MODULE._sha256(title_package),
            }
        package.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
        return temporary, package, output, archive

    def test_dry_run_keeps_only_four_user_files(self) -> None:
        temporary, package, output, _ = self._package()
        self.addCleanup(temporary.cleanup)
        plan = MODULE.build_plan(package)
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(len(plan["keep"]), 4)
        self.assertEqual(len(plan["archive"]), 1)
        self.assertEqual(
            plan["archive"][0]["source"],
            str((output / "technical.json").resolve()),
        )
        self.assertTrue((output / "technical.json").exists())

    def test_apply_moves_planned_file_without_deleting_it(self) -> None:
        temporary, package, output, archive = self._package()
        self.addCleanup(temporary.cleanup)
        plan = MODULE.apply_plan(MODULE.build_plan(package))
        self.assertEqual(len(plan["moved"]), 1)
        self.assertFalse((output / "technical.json").exists())
        self.assertTrue((archive / "technical.json").exists())
        self.assertTrue((output / "video.mp4").exists())
        self.assertTrue((output / "YOUTUBE-MANUAL-UPLOAD.md").exists())

    def test_rejects_archive_directory_inside_output(self) -> None:
        temporary, package, _, _ = self._package()
        self.addCleanup(temporary.cleanup)
        data = json.loads(package.read_text(encoding="utf-8"))
        data["preparation"]["archive_dir"] = "output/archive"
        package.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.build_plan(package)

    def test_v3_thumbnail_change_invalidates_retention_plan(self) -> None:
        temporary, package, output, _ = self._package(
            schema="youtube-manual-upload-v3"
        )
        self.addCleanup(temporary.cleanup)
        (output / "thumbnail.jpg").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(
            ValueError, "artifact hash differs: thumbnail"
        ):
            MODULE.build_plan(package)

    def test_v3_pending_package_cannot_be_retained_as_final(self) -> None:
        temporary, package, _, _ = self._package(
            schema="youtube-manual-upload-v3"
        )
        self.addCleanup(temporary.cleanup)
        data = json.loads(package.read_text(encoding="utf-8"))
        data["preparation"]["status"] = "pending"
        package.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(
            ValueError, "preparation.status must be ready"
        ):
            MODULE.build_plan(package)


if __name__ == "__main__":
    unittest.main()
