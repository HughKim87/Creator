"""Artifact/integration regression checks; these do not grade script quality."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / '.agents/skills/coordinate-video-production/scripts/check_skill_bundle.py'
spec = importlib.util.spec_from_file_location('video_script_bundle_check', CHECK)
BUNDLE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BUNDLE)
SKILL = '.agents/skills/write-video-script'
MEMBERS = (SKILL + '/SKILL.md', SKILL + '/agents/openai.yaml',
           SKILL + '/references/script-review.md')


class VideoScriptBundleTests(unittest.TestCase):
    def fixture(self):
        scratch = ROOT / 'extension/data'
        scratch.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='video-script-bundle-', dir=scratch)
        root = Path(temporary.name).resolve()
        self.assertTrue(root.is_relative_to(scratch.resolve()))
        self.addCleanup(temporary.cleanup)
        data = json.loads((ROOT / BUNDLE.MANIFEST).read_text(encoding='utf-8'))
        for rel in [BUNDLE.MANIFEST, *data['files']]:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, target)
        return root

    def test_registered_artifacts_are_bound_to_reviewed_bundle(self):
        data = json.loads((ROOT / BUNDLE.MANIFEST).read_text(encoding='utf-8'))
        self.assertIn('write-video-script', BUNDLE.SKILLS)
        for rel in MEMBERS:
            self.assertEqual(data['files'][rel], BUNDLE.digest(ROOT / rel))
        self.assertEqual(BUNDLE.inspect(ROOT)['status'], 'valid')

    def test_coordinator_link_resolves_to_registered_skill(self):
        owner = ROOT / '.agents/skills/coordinate-video-production/SKILL.md'
        targets = re.findall(r'\[write-video-script\]\(([^)]+)\)', owner.read_text(encoding='utf-8'))
        self.assertTrue(targets)
        for link in targets:
            self.assertEqual((owner.parent / link).resolve(), (ROOT / MEMBERS[0]).resolve())

    def test_complete_project_bundle_works_without_external_skill_installation(self):
        root = self.fixture()
        self.assertEqual(BUNDLE.inspect(root)['status'], 'valid')
        for rel in MEMBERS:
            owner = root / rel
            if owner.suffix != '.md':
                continue
            for link in re.findall(r'\]\(([^)]+)\)', owner.read_text(encoding='utf-8')):
                self.assertTrue((owner.parent / link).resolve().is_relative_to(root))
                self.assertTrue((owner.parent / link).is_file(), link)

    def test_missing_review_reference_fails_without_repair(self):
        root = self.fixture()
        target = root / MEMBERS[2]
        target.unlink()
        self.assertEqual(BUNDLE.inspect(root)['status'], 'invalid')
        self.assertIn('missing: ' + MEMBERS[2], BUNDLE.inspect(root)['errors'])
        self.assertFalse(target.exists())

    def test_changed_skill_fails_without_silently_rerecording(self):
        root = self.fixture()
        manifest_before = (root / BUNDLE.MANIFEST).read_bytes()
        target = root / MEMBERS[0]
        target.write_text(target.read_text(encoding='utf-8') + '\nChanged fixture.\n', encoding='utf-8')
        self.assertIn('changed: ' + MEMBERS[0], BUNDLE.inspect(root)['errors'])
        self.assertEqual((root / BUNDLE.MANIFEST).read_bytes(), manifest_before)

    def test_windows_line_endings_preserve_reviewed_identity(self):
        root = self.fixture()
        target = root / MEMBERS[2]
        target.write_bytes(target.read_bytes().replace(b'\n', b'\r\n'))
        self.assertEqual(BUNDLE.inspect(root)['status'], 'valid')


if __name__ == '__main__':
    unittest.main()
