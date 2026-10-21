"""Approved local migration: preserve every source byte, never discard data.

The journal maps every original file to its archive/current location. Inspection
does not read private file contents. Copies are verified by SHA-256; same-volume
renames are verified by file identity. No generic cleanup mode; retire only verified duplicate sources and four archived Git registrations.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import re
import html
from windows_reparse_snapshot import read_point, reparse, restore_point
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext

EVENT_LOCK = threading.Lock()
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path('D:/AI Agent/Creator-Archive/2026-10-21')
ROOTS = {
    'main': ROOT,
    'wardogs': Path('C:/Users/Hugh/.codex/worktrees/wardogs/Creator'),
    'replier': Path('D:/AI Agent/GitHub/Creator-24HReplier'),
    'ainotebook': Path('D:/AI Agent/GitHub/Creator-ainotebook'),
    'dokkaebi': Path('D:/AI Agent/GitHub/Creator-dokkaebi'),
}
LOCAL = ROOT / 'extension/data/consolidation'
MAIN_DATA = ('extension/.runtime', 'extension/work', 'extension/outputs',
             'extension/inputs', 'inputs', 'outputs', '.codex-tmp', 'Claude outputs')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.pending')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def git(root, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(root), *args], text=True, encoding='utf-8', stderr=subprocess.STDOUT).strip()


def is_link(path):
    return reparse(path) or path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def contained(path, roots):
    path = Path(os.path.abspath(path))
    if not any(path == r or path.is_relative_to(r) for r in roots):
        raise ValueError('operation target outside approved roots')
    # The operation can move a link itself but may not traverse one.
    for ancestor in path.parents:
        if any(ancestor == r.parent for r in roots):
            break
        if is_link(ancestor):
            raise ValueError('operation crosses an unapproved link')
    return path


def scan(base, prefix=''):
    files, dirs, links, boundaries = [], [], [], []
    stack = [(base, prefix)]
    while stack:
        folder, rel = stack.pop()
        if is_link(folder):
            links.append(link_metadata(folder, rel))
            continue
        dirs.append(rel)
        if folder != base and (folder / '.git').exists():
            boundaries.append(rel)
        with os.scandir(folder) as entries:
            for entry in entries:
                path = Path(entry.path)
                name = str(Path(rel) / entry.name).replace('\\', '/')
                if is_link(path):
                    links.append(link_metadata(path, name))
                elif entry.is_dir(follow_symlinks=False):
                    stack.append((path, name))
                elif entry.is_file(follow_symlinks=False):
                    # Windows DirEntry.stat may return zero file IDs; Path.stat
                    # queries the actual volume/file identity.
                    st = path.stat(follow_symlinks=False)
                    files.append({'path': name, 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
                                  'device': st.st_dev, 'inode': st.st_ino})
                else:
                    raise ValueError('unsupported filesystem entry')
    return {'files': files, 'directories': dirs, 'links': links, 'nested_git': boundaries}


def link_metadata(path, relative):
    try:
        target = os.readlink(path)
    except (OSError, ValueError):
        target = None
    return {'path': relative, 'target': target,
            'reparse_tag': getattr(path.lstat(), 'st_reparse_tag', None)}


def inventory():
    if (LOCAL / 'migration-inventory.json').exists():
        raise ValueError('initial migration inventory already exists; do not overwrite')
    result = {'checked_at': stamp(), 'roots': {}}
    for label, root in ROOTS.items():
        if label == 'main':
            data = {'files': [], 'directories': [], 'links': [], 'nested_git': []}
            for relative in MAIN_DATA:
                path = root / relative
                if path.exists():
                    part = scan(path, relative)
                    for key in data:
                        data[key].extend(part[key])
        else:
            data = scan(root)
        data.update(root=str(root), head=git(root, 'rev-parse', 'HEAD'),
                    status=git(root, 'status', '--porcelain', '--untracked-files=normal'))
        result['roots'][label] = data
        print(json.dumps({'root': label, 'files': len(data['files']),
                          'GiB': round(sum(x['bytes'] for x in data['files']) / 2**30, 2),
                          'links': len(data['links']), 'nested_git': data['nested_git'],
                          'status': 'clean' if not data['status'] else 'dirty'}, ensure_ascii=False), flush=True)
    save(LOCAL / 'migration-inventory.json', result)
    return result


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def event(data):
    path = LOCAL / 'migration-journal.jsonl'
    with EVENT_LOCK:
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'at': stamp(), **data}, ensure_ascii=False) + '\n')
            stream.flush()
            if not data.get('op', '').startswith('copy-') and data.get('op') != 'archive-internal-hardlink':
                os.fsync(stream.fileno())



def copy_verified(source, target):
    source = contained(source, [*ROOTS.values(), ARCHIVE])
    target = contained(target, [ROOT, ARCHIVE])
    assert_main_core_untouched(target)
    if is_link(source) or not source.is_file():
        raise ValueError('copy source is not a regular file')
    before = source.stat()
    if target.exists():
        if target.stat().st_size == before.st_size:
            source_sha, target_sha = digest(source), digest(target)
            if source_sha == target_sha:
                return target_sha
        raise ValueError('refuse to replace an existing different destination')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.migration-pending')
    if temporary.exists():
        raise ValueError('incomplete copy needs review')
    event({'op': 'copy-intent', 'source': str(source), 'target': str(target), 'bytes': before.st_size})
    h = hashlib.sha256()
    with source.open('rb') as incoming, temporary.open('xb') as outgoing:
        for block in iter(lambda: incoming.read(8 * 1024 * 1024), b''):
            outgoing.write(block)
            h.update(block)
        outgoing.flush()
        # Originals stay preserved through the full verification gate; avoid a
        # separate volume flush for each tiny dependency file. Every copy is
        # read back and hashed before its receipt is recorded.
    shutil.copystat(source, temporary)
    first, second = h.hexdigest(), digest(temporary)
    after = source.stat()
    if first != second or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('source changed or copy verification failed; originals retained')
    temporary.rename(target)
    event({'op': 'copy-verified', 'source': str(source), 'target': str(target), 'bytes': before.st_size, 'sha256': first})
    return first


def load_state():
    return json.loads((LOCAL / 'migration-state.json').read_text(encoding='utf-8'))


def persist(state):
    save(LOCAL / 'migration-state.json', state)
    save(ARCHIVE / 'migration-state.json', state)


def assert_main_core_untouched(path):
    path = Path(os.path.abspath(path))
    if path == ROOT / 'core' or path.is_relative_to(ROOT / 'core'):
        raise ValueError('main Core is immutable')


def move_preserved(source, target):
    source = contained(source, [*ROOTS.values(), ARCHIVE])
    target = contained(target, [ROOT, ARCHIVE])
    assert_main_core_untouched(source)
    assert_main_core_untouched(target)
    if target.exists() or is_link(source):
        raise ValueError('move requires an absent target and a non-link source')
    if source.stat().st_dev != target.parent.stat().st_dev:
        raise ValueError('cross-volume moves require verified copy first')
    st = source.stat()
    event({'op': 'rename-intent', 'source': str(source), 'target': str(target)})
    source.rename(target)
    after = target.stat()
    if (st.st_dev, st.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError('rename file identity changed')
    event({'op': 'rename-preserved', 'source': str(source), 'target': str(target), 'inode': after.st_ino})


def copy_tree_verified(source, target, resume=False):
    if target.exists() and not resume:
        raise ValueError('archive tree destination already exists')
    record = scan(source)
    if record['links']:
        raise ValueError('links require an explicit boundary plan')
    target.mkdir(parents=True, exist_ok=resume)
    receipts = {}
    if resume:
        for line in (LOCAL / 'migration-journal.jsonl').open(encoding='utf-8'):
            entry = json.loads(line)
            if entry.get('op') == 'copy-verified':
                receipts[entry['target']] = entry['sha256']
    for directory in record['directories']:
        (target / directory).mkdir(parents=True, exist_ok=True)
    def copy_item(file):
        original, destination = source / file['path'], target / file['path']
        if resume and destination.exists() and str(destination) in receipts:
            st = destination.stat()
            if (st.st_size, st.st_mtime_ns) != (file['bytes'], file['mtime_ns']):
                raise ValueError('previous copy metadata changed')
            return file['path'], receipts[str(destination)]
        partial = destination.with_name(destination.name + '.migration-pending')
        if partial.exists():
            # Own interrupted derivative, retained for inspection; original is intact.
            retained = ARCHIVE / 'interrupted-copies' / destination.relative_to(ARCHIVE)
            retained.parent.mkdir(parents=True, exist_ok=True)
            if retained.exists():
                raise ValueError('previous partial already retained')
            partial.rename(retained)
        return file['path'], copy_verified(original, destination)
    hashes = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for index, (name, sha) in enumerate(pool.map(copy_item, record['files']), 1):
            hashes[name] = sha
            if index % 500 == 0:
                print(json.dumps({'copy_tree': source.name, 'files': index, 'total': len(record['files'])}), flush=True)
    return record, hashes



def archive_worktrees(resume=False):
    if (LOCAL / 'migration-state.json').exists() and not resume:
        raise ValueError('migration state already exists; inspect/resume explicitly')
    inventory_data = json.loads((LOCAL / 'migration-inventory.json').read_text(encoding='utf-8'))
    if not resume and ARCHIVE.exists() and any(ARCHIVE.iterdir()):
        raise ValueError('archive root is not empty; refuse to mix runs')
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    state = {'schema_version': 'creator-migration-v1', 'started_at': stamp(),
             'phase': 'archive-worktrees', 'archive': str(ARCHIVE),
             'roots': {}, 'relocations': [], 'final_jobs': {}, 'verification': {}}
    if resume:
        state = load_state()
        if state['phase'] != 'archive-worktrees' or state['roots']:
            raise ValueError('only interrupted first source copy can resume here')
    persist(state)
    # Separate Git registration/submodule metadata is preserved before any roots move.
    for label, root in ROOTS.items():
        if label == 'main':
            continue
        expected = inventory_data['roots'][label]
        if git(root, 'rev-parse', 'HEAD') != expected['head'] or git(root, 'status', '--porcelain', '--untracked-files=normal'):
            raise ValueError('source worktree changed; stop before moving')
        directory = Path(git(root, 'rev-parse', '--absolute-git-dir'))
        target = ARCHIVE / 'git-metadata' / label
        if not resume:
            copy_tree_verified(directory, target)
        event({'op': 'git-metadata-preserved', 'source': str(directory), 'target': str(target)})
    if not resume:
        copy_tree_verified(LOCAL / 'recovery', ARCHIVE / 'recovery')
    save(ARCHIVE / 'original-inventory.json', inventory_data)
    for label, root in ROOTS.items():
        if label == 'main':
            continue
        target = ARCHIVE / 'worktrees' / label
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = inventory_data['roots'][label]
        current = scan(root)
        old = {x['path']: (x['bytes'], x['mtime_ns'], x['inode']) for x in expected['files']}
        now = {x['path']: (x['bytes'], x['mtime_ns'], x['inode']) for x in current['files']}
        if old != now or current['links']:
            raise ValueError('worktree inventory drift; stop')
        copied = root.stat().st_dev != target.parent.stat().st_dev
        if copied:
            _, hashes = copy_tree_verified(root, target, resume=resume)
        else:
            move_preserved(root, target)
            hashes = {}
        state['roots'][label] = {'original': str(root), 'archive': str(target),
                                 'copied_source_still_present': copied, 'head': expected['head'],
                                 'file_count': len(expected['files']), 'hashes': hashes}
        persist(state)
        print(json.dumps({'archived_root': label, 'mode': 'verified-copy-source-retained' if copied else 'identity-preserving-rename', 'files': len(expected['files'])}), flush=True)
    state['phase'] = 'archive-worktrees-complete'
    persist(state)


_mapping_state = None
_mapping_length = -1
_mapping_rows = {}


def locate(original, state):
    """Resolve the most specific original path, then each later relocation."""
    global _mapping_state, _mapping_length, _mapping_rows
    if _mapping_state is not state or _mapping_length != len(state['relocations']):
        rows = {Path(r['original']): Path(r['archive']) for r in state['roots'].values()}
        rows.update({Path(r['source']): Path(r['target']) for r in state['relocations']})
        _mapping_state, _mapping_length, _mapping_rows = state, len(state['relocations']), rows
    current = Path(original)
    visited = set()
    while current not in visited:
        visited.add(current)
        for ancestor in (current, *current.parents):
            if ancestor in _mapping_rows:
                current = _mapping_rows[ancestor] / current.relative_to(ancestor)
                break
        else:
            return current
    raise ValueError('migration mapping cycle')



def relocate(source, target, state):
    source, target = Path(source), Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    move_preserved(source, target)
    state['relocations'].append({'source': str(source), 'target': str(target), 'at': stamp()})
    # The append-only rename journal is durable before this checkpoint.
    if len(state['relocations']) % 100 == 0:
        persist(state)


def migrate_tools():
    state = load_state()
    for label, record in state['roots'].items():
        if record.get('hashes'):
            receipt = LOCAL / ('copy-hashes-' + label + '.json')
            save(receipt, record['hashes'])
            save(ARCHIVE / receipt.name, record['hashes'])
            record['hash_file'] = str(receipt)
            record['hashes'] = {}
    persist(state)
    if state['phase'] != 'archive-worktrees-complete':
        raise ValueError('archive gate is not complete')
    sys_path = str(ROOT / 'extension/src')
    import sys
    sys.path.insert(0, sys_path)
    from creator_workspace import runtime_path, init_job
    moves = (
        ('wardogs', 'extension/.runtime/qwen-asr', 'qwen-asr'),
        ('ainotebook', 'extension/.runtime/python-deps', 'python-deps'),
        ('ainotebook', 'extension/.runtime/models/whisper', 'whisper-models'),
        ('replier', 'extension/.runtime/replier-llm', 'replier-llm'),
    )
    for label, relative, component in moves:
        source = locate(ROOTS[label] / relative, state)
        target = runtime_path(component, ROOT)
        if not source.is_dir() or target.exists():
            raise ValueError('tool source missing or main destination exists')
        download = source / ('range-download-parts' if component == 'qwen-asr'
                             else 'ollama-windows-amd64-v0.40.4.zip')
        if component in {'qwen-asr', 'replier-llm'} and download.exists():
            relocate(download, ARCHIVE / 'tool-downloads' / component / download.name, state)
        relocate(source, target, state)
        print(json.dumps({'shared_tool_moved': component}), flush=True)
    init_job('24hreplier', ROOT)
    source = locate(ROOTS['replier'] / 'extension/data/replier', state)
    if source.exists():
        relocate(source, ROOT / 'extension/jobs/24hreplier/work/replier', state)
    settings = locate(ROOTS['ainotebook'] / 'extension/.runtime/video-workflow-defaults.json', state)
    destination = ROOT / 'extension/.runtime/video-workflow-defaults.json'
    if settings.exists() and not destination.exists():
        relocate(settings, destination, state)
    state['phase'] = 'shared-tools-moved'
    persist(state)


def url_path(url):
    parts = urlsplit(url)
    if parts.scheme != 'file' or parts.netloc.lower() not in {'', 'localhost'}:
        raise ValueError('unexpected XML pathurl')
    path = unquote(parts.path)
    if re.match(r'^/[A-Za-z]:', path):
        path = path[1:]
    return Path(path)


def path_url(path):
    text = Path(path).as_posix()
    return 'file://localhost' + quote('/' + text.lstrip('/'), safe='/:')


def asset_target(job_root, source):
    source = Path(source)
    suffix = hashlib.sha256(str(source).casefold().encode('utf-8')).hexdigest()[:10]
    name = source.stem + '-' + suffix + source.suffix
    original = 'inputs' in {part.lower() for part in source.parts}
    return job_root / ('inputs' if original else 'outputs/assets') / name


def preserve_asset(original, target, state):
    current = locate(original, state)
    if target.exists():
        return
    if not current.is_file():
        raise FileNotFoundError(str(original))
    # Move an archived/original file once; later job copies are independently scoped.
    if current.is_relative_to(ARCHIVE) or any(
            current.is_relative_to(ROOT / data) for data in MAIN_DATA):
        relocate(current, target, state)
    else:
        copy_verified(current, target)


def migrate_final_jobs():
    state = load_state()
    if state['phase'] != 'shared-tools-moved':
        raise ValueError('shared tool gate is not complete')
    import sys
    sys.path.insert(0, str(ROOT / 'extension/src'))
    from creator_workspace import init_job, job_paths
    plan = json.loads((LOCAL / 'cleanup-plan.json').read_text(encoding='utf-8'))
    excluded = 'C:/Users/Hugh/Desktop/2026-10-05 01-56-11.mp4'.casefold()
    for selection in plan['final_candidates']:
        job = selection['job']
        init_job(job, ROOT)
        paths = job_paths(job, ROOT)
        info = {'source_root': selection['root'], 'files': [], 'xml': [], 'status': 'preserved-import'}
        for file in selection['files']:
            original = Path(selection['root']) / file['path']
            current = locate(original, state)
            if not current.is_file():
                raise FileNotFoundError('selected final file missing')
            is_xml = current.suffix.lower() == '.xml'
            baseline = job == 'dokkaebi-voice-review' and is_xml
            metadata = job == 'backroom-shorts' and current.suffix.lower() not in {'.mp4', '.srt'}
            target = paths['work'] / ('baselines' if baseline else 'metadata') / current.name if (baseline or metadata) else paths['outputs'] / current.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if is_xml:
                raw = current.read_bytes()
                text = raw.decode('utf-8')
                bindings, exceptions = {}, []
                def replace(match):
                    url = html.unescape(match.group(1))
                    source = url_path(url)
                    if source.as_posix().casefold() == excluded:
                        exceptions.append({'source': str(source), 'status': 'excluded-missing-by-user'})
                        return match.group(0)
                    destination = asset_target(paths['root'], source)
                    preserve_asset(source, destination, state)
                    bindings[url] = str(destination)
                    return '<pathurl>' + html.escape(path_url(destination)) + '</pathurl>'
                rendered = re.sub(r'<pathurl>(.*?)</pathurl>', replace, text, flags=re.S)
                # Parse both documents to ensure only pathurl text changed, not XML structure.
                import xml.etree.ElementTree as ET
                before_tree, after_tree = ET.fromstring(raw), ET.fromstring(rendered)
                before_nodes, after_nodes = list(before_tree.iter()), list(after_tree.iter())
                if len(before_nodes) != len(after_nodes):
                    raise ValueError('XML node structure changed')
                for before, after in zip(before_nodes, after_nodes):
                    if before.tag != after.tag or before.attrib != after.attrib or (before.tag != 'pathurl' and before.text != after.text):
                        raise ValueError('XML changed beyond media references')
                if target.exists():
                    raise ValueError('derived XML destination exists')
                target.write_bytes(rendered.encode('utf-8'))
                record = {'original': str(original), 'archived_original': str(current), 'target': str(target),
                          'original_sha256': hashlib.sha256(raw).hexdigest(), 'target_sha256': digest(target),
                          'bindings': bindings, 'excluded': exceptions}
                info['xml'].append(record)
                event({'op': 'xml-references-rebound', 'source': str(original), 'target': str(target),
                       'bindings': len(bindings), 'excluded': len(exceptions)})
            else:
                preserve_asset(original, target, state)
            info['files'].append(str(target))
        save(paths['work'] / 'migration.json', info)
        state['final_jobs'][job] = info
        persist(state)
        print(json.dumps({'job_preserved': job, 'final_files': len(info['files']),
                          'references': sum(len(x['bindings']) for x in info['xml']),
                          'excluded': sum(len(x['excluded']) for x in info['xml'])}), flush=True)
    state['phase'] = 'final-jobs-moved'
    persist(state)


def archive_main_data():
    state = load_state()
    if state['phase'] != 'final-jobs-moved':
        raise ValueError('final jobs gate is not complete')
    targets = ['extension/outputs', '.codex-tmp', 'Claude outputs']
    # Keep code-owned generic work files; archive task-specific work folders only.
    work = ROOT / 'extension/work'
    if work.exists():
        targets.extend(str(p.relative_to(ROOT)).replace('\\', '/') for p in work.iterdir()
                       if p.name not in {'.gitkeep', 'qwen-local-setup.json'})
    runtime = ROOT / 'extension/.runtime'
    keep = {'ffmpeg', 'whisper.cpp', 'qwen-tts', 'gpt-sovits', 'tools', 'models', 'environments',
            'cache', 'locks', 'replier-desktop', 'video-workflow-defaults.json'}
    targets.extend(str(p.relative_to(ROOT)).replace('\\', '/') for p in runtime.iterdir() if p.name not in keep)
    personal = {
        'qwen-tts': ('voice-prompts', 'verification', 'jobs', 'audio-temp', 'ui.pid', 'ui.stdout.log', 'ui.stderr.log'),
        'gpt-sovits': ('voices', 'verification', 'probe-ready.json', 'tts-infer.yaml', 'matplotlib'),
    }
    for component, names in personal.items():
        for name in names:
            targets.append('extension/.runtime/' + component + '/' + name)
    for relative in targets:
        source = ROOT / relative
        if source.exists():
            destination = ARCHIVE / 'main' / relative
            relocate(source, destination, state)
            print(json.dumps({'main_surface_archived': relative}), flush=True)
    for job, info in state['final_jobs'].items():
        for xml in info['xml']:
            xml['archived_original'] = str(locate(Path(xml['original']), state))
        save(ROOT / 'extension/jobs' / job / 'work/migration.json', info)
    state['phase'] = 'data-migration-complete'
    persist(state)



def preserve_special_entries():
    state = load_state()
    if state['phase'] != 'data-migration-complete':
        raise ValueError('data migration must be complete')
    inventory_data = json.loads((LOCAL / 'migration-inventory.json').read_text(encoding='utf-8'))
    state.setdefault('special_entries', {})
    for label, baseline in inventory_data['roots'].items():
        for item in baseline['files']:
            original = Path(baseline['root']) / item['path']
            current = locate(original, state)
            before = current.lstat()
            if not getattr(before, 'st_file_attributes', 0) & 0x400:
                continue
            if before.st_size != item['bytes'] or before.st_mtime_ns != item['mtime_ns']:
                raise ValueError('special entry metadata changed')
            raw = read_point(current)
            sha = hashlib.sha256(raw).hexdigest()
            blob = ARCHIVE / 'reparse-blobs' / label / (sha + '.bin')
            blob.parent.mkdir(parents=True, exist_ok=True)
            if blob.exists():
                if blob.read_bytes() != raw:
                    raise ValueError('existing special metadata differs')
            else:
                with blob.open('xb') as stream:
                    stream.write(raw)
            if not current.is_relative_to(ARCHIVE):
                target = ARCHIVE / 'special-entries' / label / item['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() or reparse(target):
                    raise ValueError('special archive destination exists')
                event({'op': 'rename-intent', 'source': str(current), 'target': str(target), 'kind': 'reparse-point'})
                current.rename(target)
                after = target.lstat()
                if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or read_point(target) != raw:
                    raise ValueError('special point identity/payload changed')
                event({'op': 'rename-preserved', 'source': str(current), 'target': str(target), 'inode': after.st_ino, 'kind': 'reparse-point'})
                state['relocations'].append({'source': str(current), 'target': str(target), 'at': stamp()})
                current = target
            state['special_entries'][str(original)] = {'kind': 'windows-reparse-point',
                'current': str(current), 'reparse_blob': str(blob), 'sha256': sha,
                'directory': bool(before.st_file_attributes & 0x10), 'tag': before.st_reparse_tag}
            persist(state)
    print(json.dumps({'opaque_special_entries_preserved': len(state['special_entries'])}), flush=True)


def verify_recovery():
    state = load_state()
    if state['phase'] not in {'data-migration-complete', 'recovery-verified'}:
        raise ValueError('data migration gate is not complete')
    inventory_data = json.loads((LOCAL / 'migration-inventory.json').read_text(encoding='utf-8'))
    ledger = LOCAL / 'recovery-ledger.jsonl'
    pending = ledger.with_suffix('.pending')
    count, size, cache, private_count = 0, 0, {}, 0
    independent_copies, identity_locks = {}, {}
    dictionary_lock = threading.Lock()
    large_io = threading.Lock()
    renamed_sources = []
    for line in (LOCAL / 'migration-journal.jsonl').open(encoding='utf-8'):
        entry = json.loads(line)
        if entry.get('op') == 'rename-preserved':
            renamed_sources.append(Path(entry['source']))
    private_probes = LOCAL / 'private-restore-probe'
    if private_probes.exists():
        raise ValueError('restore probe already exists; inspect before retry')
    private_probes.mkdir()
    tasks = []
    for label, baseline in inventory_data['roots'].items():
        copied = state['roots'].get(label, {})
        expected_hashes = copied.get('hashes', {})
        if copied.get('hash_file'):
            expected_hashes = json.loads(Path(copied['hash_file']).read_text(encoding='utf-8'))
        tasks.extend((label, baseline['root'], item, copied, expected_hashes) for item in baseline['files'])
    # Small files run concurrently; large streams run serially to avoid disk seeking.
    tasks.sort(key=lambda task: task[2]['bytes'] >= 32 * 1024 * 1024)
    # Initialize the read-only path resolver before workers start.
    locate(ROOT / 'extension', state)
    def verify_file(task):
        label, root, item, copied, expected_hashes = task
        original = Path(root) / item['path']
        current = locate(original, state)
        special = state.get('special_entries', {}).get(str(original))
        if special:
            st = current.lstat()
            raw = read_point(current)
            if (st.st_size, st.st_mtime_ns) != (item['bytes'], item['mtime_ns']) or hashlib.sha256(raw).hexdigest() != special['sha256'] or Path(special['reparse_blob']).read_bytes() != raw:
                raise ValueError('special point backup mismatch')
            return {'root': label, 'original': str(original), 'live': str(current),
                    'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns, 'device': st.st_dev,
                    'inode': st.st_ino, 'proof': 'opaque-reparse-payload-and-preserved-identity', **special}
        if not current.is_file() or is_link(current):
            raise ValueError('original has no recoverable regular file: ' + str(original))
        st = current.stat()
        if st.st_size != item['bytes'] or st.st_mtime_ns != item['mtime_ns']:
            raise ValueError('original metadata changed: ' + str(original))
        identity = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
        with dictionary_lock:
            lock = identity_locks.setdefault(identity, threading.Lock())
        with lock, (large_io if st.st_size >= 32 * 1024 * 1024 else nullcontext()):
            sha = cache.get(identity)
            if sha is None:
                sha = digest(current)
                after = current.stat()
                if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity:
                    raise ValueError('file changed during verification')
                cache[identity] = sha
            if copied.get('copied_source_still_present'):
                if expected_hashes.get(item['path']) != sha:
                    raise ValueError('copy differs from original verified digest')
                proof = 'sha256-verified-copy'
            else:
                proof = original_proof(item, original, current, st, renamed_sources)
            live = current
            # Only archive-internal hardlinks: future edits in main cannot alter backup.
            if not current.is_relative_to(ARCHIVE):
                backup = ARCHIVE / 'snapshots' / label / item['path']
                backup.parent.mkdir(parents=True, exist_ok=True)
                previous = independent_copies.get(identity)
                if previous is not None:
                    if backup.exists():
                        first, second = previous.stat(), backup.stat()
                        if (first.st_dev, first.st_ino) != (second.st_dev, second.st_ino):
                            if copy_verified(current, backup) != sha:
                                raise ValueError('existing independent archive alias differs')
                    else:
                        os.link(previous, backup)
                        event({'op': 'archive-internal-hardlink', 'source': str(previous), 'target': str(backup)})
                elif copy_verified(current, backup) != sha:
                    raise ValueError('independent archive snapshot differs')
                independent_copies[identity] = backup
                current = backup
                st = current.stat()
            return {'root': label, 'original': str(original), 'current': str(current), 'live': str(live),
                    'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns, 'device': st.st_dev,
                    'inode': st.st_ino, 'sha256': sha, 'proof': proof}
    with pending.open('x', encoding='utf-8') as stream, ThreadPoolExecutor(max_workers=8) as pool:
        for record in pool.map(verify_file, tasks):
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
            relative = Path(record['original']).relative_to(ROOTS[record['root']]).as_posix()
            private = ((record['root'] == 'replier' and relative.startswith('extension/data/replier/'))
                       or '/voice-prompts/' in relative or '/gpt-sovits/voices/' in relative
                       or relative.endswith('/video-workflow-defaults.json')
                       or Path(relative).name in {'Preferences', 'Local State'})
            if private:
                restored = private_probes / record['root'] / relative
                restored.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(record['current'], restored)
                if digest(restored) != record['sha256']:
                    raise ValueError('private settings restore failed')
                private_count += 1
            count += 1
            size += record['bytes']
            if count % 5000 == 0:
                print(json.dumps({'verified_files': count, 'GiB': round(size / 2**30, 2)}), flush=True)
        stream.flush()
        os.fsync(stream.fileno())
    pending.rename(ledger)
    # This is an owned synthetic restore only; original/private records stay preserved.
    if private_probes.parent != LOCAL or private_probes.name != 'private-restore-probe':
        raise ValueError('unexpected probe boundary')
    shutil.rmtree(private_probes)
    xml_references, excluded = 0, 0
    for job, info in state['final_jobs'].items():
        for xml in info['xml']:
            if digest(Path(xml['archived_original'])) != xml['original_sha256'] or digest(Path(xml['target'])) != xml['target_sha256']:
                raise ValueError('original or derived XML changed')
            for destination in xml['bindings'].values():
                if not Path(destination).is_relative_to(ROOT / 'extension/jobs' / job) or not Path(destination).is_file():
                    raise ValueError('final XML asset missing')
                xml_references += 1
            excluded += len(xml['excluded'])
    copy_verified(ledger, ARCHIVE / ledger.name)
    receipt = {'at': stamp(), 'files': count, 'logical_bytes': size,
               'unique_regular_file_identities': len(cache),
               'unique_file_identities': len(cache) + len({(Path(x['current']).lstat().st_dev, Path(x['current']).lstat().st_ino) for x in state.get('special_entries', {}).values()}), 'ledger_sha256': digest(ledger),
               'private_restore_files': private_count, 'xml_references': xml_references,
               'user_excluded_missing_references': excluded,
               'special_reparse_points': len(state.get('special_entries', {})),
               'private_decryption_or_service_login': 'not_run'}
    state['verification'] = receipt
    state['phase'] = 'recovery-verified'
    persist(state)
    print(json.dumps(receipt), flush=True)


def retire_worktrees():
    state = load_state()
    if state['phase'] != 'recovery-verified':
        raise ValueError('full recovery verification is required before retirement')
    ledger = LOCAL / 'recovery-ledger.jsonl'
    if digest(ledger) != state['verification']['ledger_sha256']:
        raise ValueError('recovery ledger changed')
    streams = json.loads((LOCAL / 'wardogs-stream-inventory.json').read_text(encoding='utf-8'))
    if Path(streams['root']) != ROOTS['wardogs'] or streams['count'] != 0:
        raise ValueError('cross-volume source has unverified additional data streams')
    baseline = json.loads((LOCAL / 'migration-inventory.json').read_text(encoding='utf-8'))
    # Only the second source of an already verified cross-volume move is retired.
    for label, record in state['roots'].items():
        source = Path(record['original'])
        if not record['copied_source_still_present']:
            if source.exists():
                raise ValueError('retired source unexpectedly exists')
            continue
        if label != 'wardogs' or source != ROOTS['wardogs'] or source == ROOT or is_link(source):
            raise ValueError('unexpected cross-volume source boundary')
        now = scan(source)
        expected = baseline['roots'][label]
        fields = lambda items: {x['path']: (x['bytes'], x['mtime_ns']) for x in items}
        if now['links'] or fields(now['files']) != fields(expected['files']):
            raise ValueError('cross-volume source drift; originals retained')
        checked = 0
        with ledger.open(encoding='utf-8') as stream:
            for line in stream:
                item = json.loads(line)
                if item['root'] != label:
                    continue
                destination = Path(item['current'])
                st = destination.stat()
                if (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns) != (
                    item['device'], item['inode'], item['bytes'], item['mtime_ns']):
                    raise ValueError('verified destination changed; source retained')
                checked += 1
        if checked != len(expected['files']):
            raise ValueError('incomplete source preservation receipt')
        event({'op': 'verified-cross-volume-move-source-retirement', 'source': str(source),
               'files_preserved': checked, 'ledger_sha256': state['verification']['ledger_sha256']})
        shutil.rmtree(source)
        record['copied_source_still_present'] = False
        persist(state)
    # Prune only these four stale registrations; all registration/Core bytes were archived.
    active = subprocess.check_output(
        ['git', '-C', str(ROOT), 'worktree', 'list', '--porcelain', '-z'],
        encoding='utf-8').replace('\x00', '\n').count('worktree ')
    if active != 5:
        raise ValueError('unexpected worktree registration count; inspect before pruning')
    dry = git(ROOT, 'worktree', 'prune', '--dry-run', '--verbose', '--expire', 'now')
    lines = [line for line in dry.splitlines() if line.strip()]
    if len(lines) != 4 or any('gitdir file points to non-existent location' not in line for line in lines):
        raise ValueError('prune dry run differs from the four approved stale worktrees: ' + dry)
    git(ROOT, 'worktree', 'prune', '--verbose', '--expire', 'now')
    final = git(ROOT, 'worktree', 'list', '--porcelain')
    if final.count('worktree ') != 1 or 'branch refs/heads/main' not in final:
        raise ValueError('unexpected remaining worktree')
    state['phase'] = 'worktrees-retired'
    state['retired_at'] = stamp()
    persist(state)
    print(json.dumps({'retired_worktrees': 4, 'remaining_branch': 'main'}), flush=True)


def original_proof(item, original, current, st, renamed_sources):
    if item['device'] and item['inode']:
        if (st.st_dev, st.st_ino) != (item['device'], item['inode']):
            raise ValueError('original file identity changed: ' + str(original))
        return 'original-identity-size-mtime-and-current-sha256'
    # The immutable initial inventory used Windows DirEntry IDs, which may be
    # zero. Do not invent a pre-migration inode: use the recorded atomic rename
    # proof or unchanged source path, plus size/mtime and current content hash.
    if current == original:
        return 'unchanged-source-path-size-mtime-and-current-sha256'
    if any(original == source or original.is_relative_to(source) for source in renamed_sources):
        return 'verified-same-volume-rename-size-mtime-and-current-sha256'
    raise ValueError('missing identity/rename proof for original: ' + str(original))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'archive-worktrees', 'resume-archive', 'tools', 'finals', 'archive-main', 'special', 'verify', 'retire'))
    args = parser.parse_args()
    if args.action == 'inventory':
        inventory()
    elif args.action == 'archive-worktrees':
        archive_worktrees()
    elif args.action == 'resume-archive':
        archive_worktrees(resume=True)
    elif args.action == 'tools':
        migrate_tools()
    elif args.action == 'finals':
        migrate_final_jobs()
    elif args.action == 'archive-main':
        archive_main_data()
    elif args.action == 'verify':
        verify_recovery()
    elif args.action == 'special':
        preserve_special_entries()
    elif args.action == 'retire':
        retire_worktrees()


if __name__ == '__main__':
    main()
