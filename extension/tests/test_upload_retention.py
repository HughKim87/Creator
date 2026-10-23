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

    def test_other_media_and_zip_are_not_archived(self) -> None:
        temporary, package, output, archive = self._package(schema='youtube-manual-upload-v3')
        self.addCleanup(temporary.cleanup)
        for name in ['001_short.mp4', 'shorts.zip', 'other-captions.srt', 'short-thumb.png']:
            (output / name).write_bytes(b'other final result')
        before = {p.name: p.read_bytes() for p in output.iterdir()}
        plan = MODULE.build_plan(package)
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual(len(plan['unowned_outputs']), 4)
        self.assertEqual([Path(r['source']).name for r in plan['archive']], ['technical.json'])
        with self.assertRaises(ValueError):
            MODULE.apply_plan(plan)
        self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
        self.assertFalse(archive.exists())

    def test_sibling_shorts_folder_survives_upload_finalization(self) -> None:
        temporary, package, output, _ = self._package(schema='youtube-manual-upload-v3')
        self.addCleanup(temporary.cleanup)
        shorts = output.with_name('shorts'); shorts.mkdir()
        short = shorts / '001.mp4'; short.write_bytes(b'short result')
        bundle = shorts / 'shorts.zip'; bundle.write_bytes(b'short bundle')
        MODULE.apply_plan(MODULE.build_plan(package))
        plan = MODULE.build_plan(package)
        self.assertEqual(plan['status'], 'ready')
        self.assertEqual(plan['archive'], [])
        self.assertEqual(len(list(output.iterdir())), 4)
        self.assertEqual(short.read_bytes(), b'short result')
        self.assertEqual(bundle.read_bytes(), b'short bundle')

    def test_explicit_package_intermediate_can_be_archived(self) -> None:
        temporary, package, output, archive = self._package()
        self.addCleanup(temporary.cleanup)
        (output / 'previous-thumbnail.png').write_bytes(b'known package intermediate')
        data = json.loads(package.read_text(encoding='utf-8'))
        data['preparation']['archive_files'] = ['previous-thumbnail.png']
        package.write_text(json.dumps(data), encoding='utf-8')
        MODULE.apply_plan(MODULE.build_plan(package))
        self.assertEqual((archive / 'previous-thumbnail.png').read_bytes(), b'known package intermediate')

    def test_invalid_archive_ownership_list_is_rejected(self) -> None:
        temporary, package, _, _ = self._package()
        self.addCleanup(temporary.cleanup)
        data = json.loads(package.read_text(encoding='utf-8'))
        for names in [['../other.mp4'], ['video.mp4'], ['old.png', 'old.png'], 'old.png']:
            with self.subTest(names=names), self.assertRaises(ValueError):
                data['preparation']['archive_files'] = names
                package.write_text(json.dumps(data), encoding='utf-8')
                MODULE.build_plan(package)

    def test_new_result_after_planning_blocks_before_any_move(self) -> None:
        temporary, package, output, archive = self._package()
        self.addCleanup(temporary.cleanup)
        plan = MODULE.build_plan(package)
        (output / 'new-short.mp4').write_bytes(b'concurrent result')
        with self.assertRaises(ValueError):
            MODULE.apply_plan(plan)
        self.assertTrue((output / 'technical.json').exists())
        self.assertFalse(archive.exists())

    def test_modified_intermediate_after_planning_blocks_before_any_move(self) -> None:
        temporary, package, output, archive = self._package()
        self.addCleanup(temporary.cleanup)
        plan = MODULE.build_plan(package)
        (output / 'technical.json').write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            MODULE.apply_plan(plan)
        self.assertTrue((output / 'technical.json').exists())
        self.assertFalse(archive.exists())

    def test_preflight_allows_missing_guide_but_is_never_an_apply_plan(self) -> None:
        temporary, package, output, archive = self._package(schema='youtube-manual-upload-v3')
        self.addCleanup(temporary.cleanup)
        (output / 'YOUTUBE-MANUAL-UPLOAD.md').unlink()
        plan = MODULE.build_plan(package, preflight=True)
        self.assertEqual(plan['status'], 'ready')
        self.assertTrue(plan['preflight_only'])
        with self.assertRaises(ValueError):
            MODULE.apply_plan(plan)
        self.assertFalse(archive.exists())
        with self.assertRaises(ValueError):
            MODULE.build_plan(package)

    def test_nested_shorts_are_blocked_without_traversal_or_moves(self) -> None:
        temporary, package, output, archive = self._package()
        self.addCleanup(temporary.cleanup)
        shorts=output/'shorts'; shorts.mkdir()
        (shorts/'001.mp4').write_bytes(b'short')
        plan=MODULE.build_plan(package)
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual(plan['unexpected_directories'], [str(shorts.resolve())])
        with self.assertRaises(ValueError):
            MODULE.apply_plan(plan)
        self.assertEqual((shorts/'001.mp4').read_bytes(), b'short')
        self.assertFalse(archive.exists())


if __name__ == "__main__":
    unittest.main()
