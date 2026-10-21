"""Read-only metadata inventory for the explicitly selected Creator worktrees.

Writes one local report; never removes, copies or opens media contents.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'inputs', '.git', 'core', '__pycache__'}


def git(root, *args):
    p = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
                        '-C', str(root), *args], capture_output=True, text=True,
                       encoding='utf-8', check=True)
    return p.stdout.strip()


def inventory(root):
    files, boundaries = [], []
    # Exact data surfaces approved for cleanup planning. Input originals excluded.
    for rel in ('extension/.runtime', 'extension/work', 'extension/outputs', 'outputs', 'extension/jobs'):
        base = root / rel
        if not base.exists():
            continue
        stack = [base]
        while stack:
            directory = stack.pop()
            if directory.is_symlink() or directory.is_junction():
                boundaries.append(directory.relative_to(root).as_posix())
                continue
            for item in os.scandir(directory):
                path = Path(item.path)
                if item.name in SKIP:
                    continue
                # Do not inventory private settings, tokens or browser profiles.
                name = item.name.lower()
                if any(x in name for x in ('token', 'credential', 'secret', 'cookie', 'profile', '.env')):
                    continue
                if item.is_symlink() or path.is_junction():
                    boundaries.append(path.relative_to(root).as_posix())
                elif item.is_dir(follow_symlinks=False):
                    stack.append(path)
                elif item.is_file(follow_symlinks=False):
                    st = item.stat(follow_symlinks=False)
                    files.append({'path': path.relative_to(root).as_posix(), 'bytes': st.st_size,
                                  'mtime_ns': st.st_mtime_ns})
    return {'root': str(root), 'head': git(root, 'rev-parse', 'HEAD'),
            'tracked_status': git(root, 'status', '--porcelain', '--ignore-submodules=all', '--untracked-files=no'),
            'files': files, 'boundaries': boundaries,
            'limitations': 'metadata only; inputs/private settings excluded; not a content backup'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    roots = [Path(line[9:]) for line in git(ROOT, 'worktree', 'list', '--porcelain').splitlines()
             if line.startswith('worktree ')]
    # Complete reads before replacing any report.
    report = {'checked_at': datetime.now(timezone.utc).isoformat(),
              'refs': git(ROOT, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads', 'refs/tags/before'),
              'worktrees': [inventory(r) for r in roots]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for tree in report['worktrees']:
        groups = {}
        for f in tree['files']:
            parts = Path(f['path']).parts
            key = '/'.join(parts[:3])
            group = groups.setdefault(key, {'files': 0, 'bytes': 0})
            group['files'] += 1
            group['bytes'] += f['bytes']
        print(json.dumps({'root': tree['root'], 'tracked_status': tree['tracked_status'],
                          'groups': groups, 'boundaries': tree['boundaries']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
