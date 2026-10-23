"""Repeatable flat-schema validation for the create-shorts bundle; no PyYAML required."""
import ast
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SKILL = BASE.parent / '.agents/skills/create-shorts'


def validate_bundle(root):
    ROOT = Path(root).resolve()
    files = ['SKILL.md', 'agents/openai.yaml', 'references/editing.md',
             'references/manifest.md', 'scripts/shorts_review.py', 'assets/review.html']
    contents = {p: (ROOT / p).read_text(encoding='utf-8-sig') for p in files}
    for path, text in contents.items():
        assert '\x00' not in text and '\ufffd' not in text, path
        assert '[TODO:' not in text, path
    skill = contents['SKILL.md']
    match = re.match(r'^---\n(.*?)\n---\n', skill, re.S)
    assert match
    front = {}
    for line in match.group(1).splitlines():
        key, value = line.split(': ', 1)
        assert key not in front and key in ['name', 'description']
        assert not re.search(r':\s|^[-\[\]{}&*!|>\'\"%@`]|\s#', value)
        front[key] = value
    assert front['name'] == ROOT.name and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', front['name'])
    assert len(front['name']) <= 64 and 0 < len(front['description']) <= 1024
    assert not any(c in front['description'] for c in '<>')
    interface, policy, section = {}, {}, None
    for line in contents['agents/openai.yaml'].splitlines():
        if not line.strip():
            continue
        if line in ['interface:', 'policy:']:
            section = line[:-1]
            continue
        assert line.startswith('  ') and section
        key, raw = line[2:].split(': ', 1)
        if section == 'interface':
            interface[key] = json.loads(raw)
        else:
            assert key == 'allow_implicit_invocation' and raw == 'true'
            policy[key] = True
    assert 25 <= len(interface['short_description']) <= 64
    assert '$create-shorts' in interface['default_prompt'] and policy['allow_implicit_invocation']
    for label, relative in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', skill):
        assert (ROOT / relative).resolve().is_relative_to(ROOT.resolve()) and (ROOT / relative).is_file(), relative
    ast.parse(contents['scripts/shorts_review.py'])
    assert contents['assets/review.html'].count('__REVIEW_DATA__') == 1
    return files


class ShortsBundleTests(unittest.TestCase):
    def test_repository_bundle_is_complete_and_valid(self):
        self.assertEqual(len(validate_bundle(SKILL)), 6)

    def fixture(self):
        scratch = BASE / 'data'
        scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='shorts-bundle-test-', dir=scratch)
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'create-shorts'
        shutil.copytree(SKILL, root)
        return root

    def test_missing_reference_is_rejected(self):
        root = self.fixture()
        (root / 'references/editing.md').unlink()
        with self.assertRaises(FileNotFoundError):
            validate_bundle(root)

    def test_duplicate_frontmatter_key_is_rejected(self):
        root = self.fixture()
        skill = root / 'SKILL.md'
        skill.write_text(skill.read_text(encoding='utf-8').replace('name: create-shorts',
                         'name: create-shorts\nname: create-shorts', 1), encoding='utf-8')
        with self.assertRaises(AssertionError):
            validate_bundle(root)

    def test_reference_cannot_escape_skill_root(self):
        root = self.fixture()
        skill = root / 'SKILL.md'
        skill.write_text(skill.read_text(encoding='utf-8') + '\n[outside](../outside.md)\n', encoding='utf-8')
        with self.assertRaises(AssertionError):
            validate_bundle(root)


if __name__ == '__main__':
    unittest.main()
