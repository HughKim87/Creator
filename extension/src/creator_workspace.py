"""Job-scoped paths and OS-owned cross-process leases for one Creator checkout.

Standard library only. Inspection never creates directories. Existing runtime
locations are read through an exact catalog, never discovered in other jobs.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,78}[a-z0-9])?\Z")
RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(10)), *(f'lpt{i}' for i in range(10))}


def identifier(value: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value) or value in RESERVED:
        raise ValueError('job/component ID must be 1..80 lowercase ASCII letters, digits or hyphens; no reserved device names')
    return value


def safe_path(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    # Reject Windows separators even when the caller runs in a Linux VM.
    if not relative or '\\' in relative or ':' in relative:
        raise ValueError('unsafe workspace path')
    parts = Path(relative).parts
    if Path(relative).is_absolute() or '..' in parts:
        raise ValueError('workspace path must be relative and contained')
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise ValueError('workspace path crosses a link boundary')
    if not current.resolve().is_relative_to(root):
        raise ValueError('workspace path escapes root')
    return current


def runtime_path(component: str, root: Path = ROOT) -> Path:
    identifier(component)
    catalog = safe_path(root, 'extension/config/workspace-runtime.json')
    data = json.loads(catalog.read_text(encoding='utf-8'))
    if data.get('schema_version') != 'creator-shared-runtime-v1':
        raise ValueError('unsupported runtime catalog')
    entry = data['components'].get(component)
    if not isinstance(entry, dict):
        raise ValueError(f'unknown runtime component: {component}')
    target = safe_path(root, 'extension/.runtime/' + entry['path'])
    # Prefer canonical path; once installed it must never silently fall back.
    if target.exists():
        return target
    for legacy in entry.get('legacy', []):
        candidate = safe_path(root, 'extension/.runtime/' + legacy)
        if candidate.exists():
            return candidate
    return target


def job_paths(job: str, root: Path = ROOT) -> dict[str, Path]:
    base = 'extension/jobs/' + identifier(job)
    return {'root': safe_path(root, base), **{
        kind: safe_path(root, base + '/' + kind)
        for kind in ('inputs', 'work', 'outputs', 'logs')}}


def current_job_paths(root: Path = ROOT) -> dict[str, Path] | None:
    job = os.environ.get('CREATOR_JOB_ID')
    if not job:
        return None
    paths = job_paths(job, root)
    supplied = os.environ.get('CREATOR_JOB_ROOT')
    if supplied and Path(supplied).resolve() != paths['root']:
        raise ValueError('CREATOR_JOB_ROOT differs from the selected job')
    return paths


def git(root: Path, *args: str) -> str:
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(root), *args],
                            capture_output=True, text=True, encoding='utf-8', check=True)
    return result.stdout.strip()


def provenance(root: Path) -> dict:
    catalog = safe_path(root, 'extension/config/workspace-runtime.json')
    return {'commit': git(root, 'rev-parse', 'HEAD'),
            'runtime_catalog_sha256': hashlib.sha256(catalog.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}


def atomic_json(path: Path, data: dict):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class Lease:
    """Stable lock inode; the OS releases ownership after exit/crash.

    Lock files remain in the ignored runtime. Never unlink a shared lock file:
    replacing its inode would let two processes own different locks by name.
    """
    def __init__(self, name: str, root: Path = ROOT):
        self.path = safe_path(root, 'extension/.runtime/locks/' + identifier(name) + '.lock')
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open('a+b')
        if self.path.stat().st_size == 0:
            self.stream.write(b'0')
            self.stream.flush()
        try:
            self.stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stream.close()
            self.stream = None
            raise RuntimeError(f'resource is busy: {self.path.stem}') from None
        return self

    def __exit__(self, *exc):
        if self.stream:
            self.stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            self.stream.close()
            self.stream = None


def init_job(job: str, root: Path = ROOT) -> dict:
    paths = job_paths(job, root)
    info = provenance(root)
    with Lease('job-' + hashlib.sha256(job.encode()).hexdigest(), root):
        paths['root'].mkdir(parents=True, exist_ok=False)
        for key, path in paths.items():
            if key != 'root':
                path.mkdir()
        record = {'schema_version': 'creator-job-v1', 'job_id': job,
                  'created_at': datetime.now(timezone.utc).isoformat(),
                  'provenance': info, 'status': 'initialized', 'runs': []}
        atomic_json(paths['root'] / 'job.json', record)
        (paths['root'] / 'state.md').write_text(
            '# ' + job + '\n\n## 현재 단계\n\ninitialized\n\n## 직전 게이트\n\n작업 경로 생성. 제작 검증 not_run.\n\n'
            '## 승인 상태\n\n작업별 사용자 지시를 따른다.\n\n## 차단\n\n없음.\n\n'
            '## 알려진 위험\n\n원본·산출물 접근 권한과 버전은 실행 전에 확인한다.\n\n'
            '## 첫 다음 행동\n\n1. 이 job의 입력과 제작 범위를 확정한다.\n', encoding='utf-8')
    return inspect_job(job, root)


def inspect_job(job: str, root: Path = ROOT) -> dict:
    paths = job_paths(job, root)
    path = safe_path(root, 'extension/jobs/' + job + '/job.json')
    record = json.loads(path.read_text(encoding='utf-8'))
    if record.get('schema_version') != 'creator-job-v1' or record.get('job_id') != job:
        raise ValueError('job record identity mismatch')
    for key, value in paths.items():
        if not value.is_dir():
            raise ValueError('missing job directory: ' + key)
    return {'status': 'valid', 'job_id': job, 'paths': {k: str(v) for k, v in paths.items()}, 'record': record}


def stop_owned(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=False)
    else:
        import signal
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name != 'nt':
            import signal
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def run_job(job: str, command: list[str], root: Path = ROOT, *, gpu=False, accept_code_change=False) -> int:
    if not command:
        raise ValueError('a child command is required')
    root = Path(root).resolve()
    if git(root, 'branch', '--show-current') != 'main':
        raise ValueError('job execution requires main')
    # Do not claim an arbitrary dirty checkout is the pinned commit.
    dirty = git(root, 'status', '--porcelain', '--ignore-submodules=all', '--untracked-files=normal')
    if dirty:
        raise ValueError('commit common code changes before running a job')
    with ExitStack() as stack:
        stack.enter_context(Lease('job-' + hashlib.sha256(identifier(job).encode()).hexdigest(), root))
        if gpu:
            stack.enter_context(Lease('gpu', root))
        result = inspect_job(job, root)
        record = result['record']
        info = provenance(root)
        if record['provenance'] != info and not accept_code_change:
            raise ValueError('code/runtime catalog changed; review then use --accept-code-change')
        paths = job_paths(job, root)
        temp = safe_path(root, 'extension/jobs/' + job + '/work/tmp')
        temp.mkdir(exist_ok=True)
        env = dict(os.environ, CREATOR_JOB_ID=job, CREATOR_JOB_ROOT=str(paths['root']),
                   CREATOR_WORKSPACE_ROOT=str(root),
                   CREATOR_WORK_DIR=str(paths['work']), CREATOR_OUTPUT_DIR=str(paths['outputs']),
                   CREATOR_LOG_DIR=str(paths['logs']), TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
                   PYTHONDONTWRITEBYTECODE='1')
        ffmpeg_bin = runtime_path('ffmpeg', root) / 'bin'
        if ffmpeg_bin.is_dir():
            env['PATH'] = str(ffmpeg_bin) + os.pathsep + env.get('PATH', '')
        if gpu:
            env['CREATOR_GPU_LEASE_HELD'] = '1'
        # Store no command text; it may contain private user material.
        run = {'started_at': datetime.now(timezone.utc).isoformat(), 'provenance': info, 'status': 'running'}
        record['runs'].append(run)
        record['provenance'] = info
        record['status'] = 'running'
        atomic_json(paths['root'] / 'job.json', record)
        process = None
        code = 1
        try:
            process = subprocess.Popen(command, cwd=root, env=env,
                **({'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}))
            code = process.wait()
        except KeyboardInterrupt:
            code = 130
            if process:
                stop_owned(process)
        finally:
            if process and process.poll() is None:
                stop_owned(process)
            run.update(finished_at=datetime.now(timezone.utc).isoformat(), returncode=code,
                       status='succeeded' if code == 0 else ('cancelled' if code == 130 else 'failed'))
            record['status'] = run['status']
            atomic_json(paths['root'] / 'job.json', record)
        return code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    sub = p.add_subparsers(dest='action', required=True)
    for action in ('init', 'inspect', 'run'):
        s = sub.add_parser(action)
        s.add_argument('--job', required=True)
        if action == 'run':
            s.add_argument('--gpu', action='store_true')
            s.add_argument('--accept-code-change', action='store_true')
            s.add_argument('command', nargs=argparse.REMAINDER)
    s = sub.add_parser('runtime')
    s.add_argument('--component', required=True)
    a = p.parse_args()
    try:
        if a.action == 'runtime':
            print(runtime_path(a.component, a.root))
            return 0
        if a.action == 'run':
            cmd = a.command[1:] if a.command[:1] == ['--'] else a.command
            return run_job(a.job, cmd, a.root, gpu=a.gpu, accept_code_change=a.accept_code_change)
        print(json.dumps(init_job(a.job, a.root) if a.action == 'init' else inspect_job(a.job, a.root), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        p.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
