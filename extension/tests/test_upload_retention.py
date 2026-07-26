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
    def _package(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path, Path]:
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
        package.write_text(
            json.dumps(
                {
                    "schema_version": "youtube-manual-upload-v2",
                    "artifacts": {
                        "video": "output/video.mp4",
                        "thumbnail": "output/thumbnail.jpg",
                        "captions": "output/captions.ko.srt",
                        "title_thumbnail_package": "youtube-title-thumbnail.json",
                    },
                    "preparation": {
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
                },
                ensure_ascii=False,
            ),
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


if __name__ == "__main__":
    unittest.main()
