"""Restore an archived filesystem snapshot into a new, empty directory.

Default is read-only planning. A snapshot includes historical .git pointer files;
it is not a registered Git checkout. See WORKSPACE.md for bundle-based recovery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from windows_reparse_snapshot import read_point, restore_point


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def restore(archive, label, destination, materialize=False):
    archive, destination = Path(archive).resolve(), Path(destination).absolute()
    inventory = json.loads((archive / 'original-inventory.json').read_text(encoding='utf-8'))
    original = Path(inventory['roots'][label]['root'])
    # Never overlay or replace an existing tree, including the archive/source.
    if destination.exists() or any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                                   for p in (destination, *destination.parents)):
        raise ValueError('destination must be absent and must not cross links')
    records = []
    state = json.loads((archive / 'migration-state.json').read_text(encoding='utf-8'))
    original_archive = Path(state.get('archive', str(archive)))
    ledger = archive / 'recovery-ledger.jsonl'
    if sha256(ledger) != state['verification']['ledger_sha256']:
        raise ValueError('recovery ledger integrity mismatch')
    with ledger.open(encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            if item['root'] != label:
                continue
            relative = Path(item['original']).relative_to(original)
            if '..' in relative.parts or relative.is_absolute():
                raise ValueError('unsafe recovery relative path')
            stored = Path(item['current']).relative_to(original_archive)
            if '..' in stored.parts:
                raise ValueError('unsafe archive source path')
            item['current'] = str(archive / stored)
            if item.get('kind') == 'windows-reparse-point':
                item['reparse_blob'] = str(archive / Path(item['reparse_blob']).relative_to(original_archive))
            records.append((item, destination / relative))
    if len(records) != len(inventory['roots'][label]['files']):
        raise ValueError('incomplete snapshot inventory')
    if materialize:
        # Check all sources before creating any destination. Never print contents.
        for item, _ in records:
            current = Path(item['current'])
            if item.get('kind') == 'windows-reparse-point':
                raw = read_point(current)
                if hashlib.sha256(raw).hexdigest() != item['sha256'] or Path(item['reparse_blob']).read_bytes() != raw:
                    raise ValueError('special snapshot source changed')
            elif not current.is_file() or sha256(current) != item['sha256']:
                raise ValueError('snapshot source changed; stop without overwriting anything')
        destination.mkdir(parents=True)
        for directory in inventory['roots'][label]['directories']:
            (destination / directory).mkdir(parents=True, exist_ok=True)
        for item, target in records:
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.get('kind') == 'windows-reparse-point':
                restore_point(target, Path(item['reparse_blob']).read_bytes(), item['mtime_ns'], item['directory'])
                continue
            with Path(item['current']).open('rb') as source, target.open('xb') as output:
                shutil.copyfileobj(source, output, 8 * 1024 * 1024)
            shutil.copystat(item['current'], target)
            if sha256(target) != item['sha256']:
                raise ValueError('restored file verification failed; originals retained')
    return {'root': label, 'files': len(records), 'bytes': sum(x['bytes'] for x, _ in records),
            'mode': 'restored-and-hash-verified' if materialize else 'plan-only',
            'destination': str(destination), 'git_registration': 'not_restored'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--root', required=True, choices=('main', 'wardogs', 'replier', 'ainotebook', 'dokkaebi'))
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--materialize', action='store_true')
    args = parser.parse_args()
    print(json.dumps(restore(args.archive, args.root, args.destination, args.materialize)))


if __name__ == '__main__':
    main()
