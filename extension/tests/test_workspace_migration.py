"""Small owned fixtures exercise preservation/refusal, never real user data."""
import importlib.util
import json
import os
import struct
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('workspace_migration', ROOT / 'scripts/migrate_workspace_data.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
restore_spec = importlib.util.spec_from_file_location('workspace_restore', ROOT / 'scripts/restore_workspace_snapshot.py')
restore_module = importlib.util.module_from_spec(restore_spec)
restore_spec.loader.exec_module(restore_module)


class PreservationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='migration-fixture-', dir=ROOT / 'extension/data')
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        events = patch.object(module, 'event')
        events.start()
        self.addCleanup(events.stop)

    def test_copy_verifies_content_and_preserves_source(self):
        source = self.root / 'source.bin'
        source.write_bytes(b'owned fixture\0' * 30)
        target = self.root / 'copy.bin'
        result = module.copy_verified(source, target)
        self.assertEqual(source.read_bytes(), target.read_bytes())
        self.assertEqual(result, module.digest(source))

    def test_different_destination_is_never_overwritten(self):
        source, target = self.root / 's', self.root / 't'
        source.write_bytes(b'original')
        target.write_bytes(b'existing')
        with self.assertRaises(ValueError):
            module.copy_verified(source, target)
        self.assertEqual(target.read_bytes(), b'existing')
        self.assertEqual(source.read_bytes(), b'original')

    def test_rename_preserves_file_identity(self):
        source, target = self.root / 's', self.root / 't'
        source.write_bytes(b'owned fixture')
        identity = source.stat().st_ino
        module.move_preserved(source, target)
        self.assertEqual(target.stat().st_ino, identity)
        self.assertFalse(source.exists())

    def test_main_core_and_outside_destination_are_refused(self):
        source = self.root / 's'
        source.write_bytes(b'owned fixture')
        with self.assertRaises(ValueError):
            module.assert_main_core_untouched(ROOT / 'core/anything')
        with self.assertRaises(ValueError):
            module.copy_verified(source, Path('C:/unapproved-destination/file'))

    def test_specific_file_move_wins_over_later_parent_archive(self):
        source = self.root / 'old/assets/a.wav'
        target = self.root / 'job/inputs/a.wav'
        state = {'roots': {}, 'relocations': [
            {'source': str(source), 'target': str(target)},
            {'source': str(self.root / 'old'), 'target': str(self.root / 'archive')},
        ]}
        self.assertEqual(module.locate(source, state), target)
        self.assertEqual(module.locate(self.root / 'old/other.wav', state), self.root / 'archive/other.wav')

    def test_mapping_follows_original_checkout_and_tool_relocation(self):
        old, archive, tool = (self.root / name for name in ('original', 'archive', 'tool'))
        state = {'roots': {'test': {'original': str(old), 'archive': str(archive)}},
                 'relocations': [{'source': str(archive / 'runtime'), 'target': str(tool)}]}
        self.assertEqual(module.locate(old / 'runtime/model.bin', state), tool / 'model.bin')

    def restore_fixture(self):
        archive = self.root / 'archive'
        archive.mkdir()
        original = self.root / 'historical'
        source = archive / 'opaque.bin'
        source.write_bytes(b'owned opaque setting fixture')
        inventory = {'roots': {'main': {'root': str(original),
                                       'files': [{'path': 'settings.bin'}], 'directories': ['']}}}
        (archive / 'original-inventory.json').write_text(json.dumps(inventory), encoding='utf-8')
        ledger = archive / 'recovery-ledger.jsonl'
        ledger.write_text(json.dumps({'root': 'main', 'original': str(original / 'settings.bin'),
                                      'current': str(source), 'bytes': source.stat().st_size,
                                      'sha256': restore_module.sha256(source)}) + '\n', encoding='utf-8')
        state = {'archive': str(archive), 'verification': {'ledger_sha256': restore_module.sha256(ledger)}}
        (archive / 'migration-state.json').write_text(json.dumps(state), encoding='utf-8')
        return archive, source

    def test_snapshot_restore_is_explicit_and_never_overlays_existing_files(self):
        archive, source = self.restore_fixture()
        destination = self.root / 'restored'
        result = restore_module.restore(archive, 'main', destination)
        self.assertEqual(result['mode'], 'plan-only')
        self.assertFalse(destination.exists())
        restore_module.restore(archive, 'main', destination, materialize=True)
        self.assertEqual((destination / 'settings.bin').read_bytes(), source.read_bytes())
        with self.assertRaises(ValueError):
            restore_module.restore(archive, 'main', destination, materialize=True)

    def test_corrupted_snapshot_is_rejected_before_destination_creation(self):
        archive, source = self.restore_fixture()
        source.write_bytes(b'changed fixture')
        destination = self.root / 'refused'
        with self.assertRaises(ValueError):
            restore_module.restore(archive, 'main', destination, materialize=True)
        self.assertFalse(destination.exists())

    def test_zero_windows_inventory_ids_require_a_real_migration_proof(self):
        current = self.root / 'archived.bin'
        current.write_bytes(b'owned fixture')
        original = self.root / 'old/file.bin'
        metadata = {'device': 0, 'inode': 0}
        with self.assertRaises(ValueError):
            module.original_proof(metadata, original, current, current.stat(), [])
        proof = module.original_proof(metadata, original, current, current.stat(), [self.root / 'old'])
        self.assertIn('verified-same-volume-rename', proof)

    def test_known_wrong_file_identity_is_never_downgraded_to_metadata(self):
        current = self.root / 'current.bin'
        current.write_bytes(b'owned fixture')
        metadata = {'device': current.stat().st_dev, 'inode': current.stat().st_ino + 1}
        with self.assertRaises(ValueError):
            module.original_proof(metadata, current, current, current.stat(), [self.root])

    def test_archive_can_be_relocated_before_snapshot_restore(self):
        archive, source = self.restore_fixture()
        moved = self.root / 'relocated-archive'
        archive.rename(moved)
        destination = self.root / 'restored'
        restore_module.restore(moved, 'main', destination, materialize=True)
        self.assertEqual((destination / 'settings.bin').read_bytes(), (moved / source.name).read_bytes())

    @unittest.skipUnless(os.name == 'nt', 'Windows reparse point fixture')
    def test_opaque_linux_link_restores_without_following_its_target(self):
        from windows_reparse_snapshot import read_point, restore_point
        archive, source = self.restore_fixture()
        source.unlink()
        data = struct.pack('<I', 2) + b'/owned-fixture/unavailable-model'
        payload = struct.pack('<IHH', 0xa000001d, len(data), 0) + data
        mtime = 1700000000000000000
        restore_point(source, payload, mtime)
        scanned = module.scan(archive)
        self.assertEqual(len(scanned['links']), 1)
        self.assertEqual(scanned['links'][0]['reparse_tag'], 0xa000001d)
        blob = archive / 'raw-reparse.bin'
        blob.write_bytes(payload)
        ledger = archive / 'recovery-ledger.jsonl'
        record = {'root': 'main', 'original': str(self.root / 'historical/settings.bin'),
                  'current': str(source), 'bytes': 0, 'sha256': module.hashlib.sha256(payload).hexdigest(),
                  'kind': 'windows-reparse-point', 'reparse_blob': str(blob), 'mtime_ns': mtime,
                  'directory': False}
        ledger.write_text(json.dumps(record) + '\n', encoding='utf-8')
        (archive / 'migration-state.json').write_text(json.dumps({'archive': str(archive),
            'verification': {'ledger_sha256': restore_module.sha256(ledger)}}), encoding='utf-8')
        target = self.root / 'restored'
        restore_module.restore(archive, 'main', target, materialize=True)
        self.assertEqual(read_point(target / 'settings.bin'), payload)
        self.assertEqual((target / 'settings.bin').lstat().st_mtime_ns, mtime)
        (target / 'settings.bin').unlink()
        source.unlink()


if __name__ == '__main__':
    unittest.main()
