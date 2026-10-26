"""Exercise job isolation and OS process locks, rather than matching implementation text."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from creator_workspace import (ROOT, Lease, current_job_paths, identifier, init_job,
                               inspect_job, job_paths, run_job, runtime_path, safe_path)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / 'extension/data'
        scratch.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='workspace-test-', dir=scratch)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        config = self.root / 'extension/config'
        config.mkdir(parents=True)
        shutil.copyfile(ROOT / 'extension/config/workspace-runtime.json', config / 'workspace-runtime.json')
        (self.root / '.gitignore').write_text('extension/jobs/\nextension/.runtime/\n', encoding='utf-8')
        self.git('init', '-b', 'main')
        self.git('add', '--', '.gitignore', 'extension/config/workspace-runtime.json')
        self.commit('fixture')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True, stderr=subprocess.STDOUT).strip()

    def commit(self, message):
        self.git('-c', 'user.name=Workspace Fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgSign=false', 'commit', '-m', message)

    def test_two_parallel_jobs_write_separate_outputs_and_keep_git_clean(self):
        for job in ('video-a', 'video-b'):
            init_job(job, self.root)
        command = [sys.executable, '-B', '-c',
                   'import os,time;from pathlib import Path;time.sleep(.1);'
                   'Path(os.environ["CREATOR_OUTPUT_DIR"],"result.txt").write_text(os.environ["CREATOR_JOB_ID"]);'
                   'Path(os.environ["TMP"],"temp.txt").write_text(os.environ["CREATOR_JOB_ID"])']
        with ThreadPoolExecutor(2) as pool:
            codes = list(pool.map(lambda job: run_job(job, command, self.root), ('video-a', 'video-b')))
        self.assertEqual(codes, [0, 0])
        for job in ('video-a', 'video-b'):
            paths = job_paths(job, self.root)
            self.assertEqual((paths['outputs'] / 'result.txt').read_text(), job)
            self.assertEqual((paths['work'] / 'tmp/temp.txt').read_text(), job)
            self.assertEqual(inspect_job(job, self.root)['record']['status'], 'succeeded')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_job_duplicate_initialization_preserves_record(self):
        init_job('video-a', self.root)
        old = (job_paths('video-a', self.root)['root'] / 'job.json').read_bytes()
        with self.assertRaises(FileExistsError):
            init_job('video-a', self.root)
        self.assertEqual((job_paths('video-a', self.root)['root'] / 'job.json').read_bytes(), old)

    def test_failed_command_preserves_outputs_and_can_resume(self):
        init_job('video-a', self.root)
        code = run_job('video-a', [sys.executable, '-c', 'raise SystemExit(7)'], self.root)
        self.assertEqual(code, 7)
        self.assertEqual(inspect_job('video-a', self.root)['record']['status'], 'failed')
        self.assertEqual(run_job('video-a', [sys.executable, '-c', 'pass'], self.root), 0)
        self.assertEqual(len(inspect_job('video-a', self.root)['record']['runs']), 2)

    def test_code_change_requires_explicit_acceptance_and_preserves_old_run_version(self):
        init_job('video-a', self.root)
        command = [sys.executable, '-c', 'pass']
        self.assertEqual(run_job('video-a', command, self.root), 0)
        old = inspect_job('video-a', self.root)['record']['provenance']
        (self.root / 'code.txt').write_text('new version')
        self.git('add', 'code.txt')
        self.commit('new code')
        with self.assertRaisesRegex(ValueError, 'changed'):
            run_job('video-a', command, self.root)
        self.assertEqual(run_job('video-a', command, self.root, accept_code_change=True), 0)
        runs = inspect_job('video-a', self.root)['record']['runs']
        self.assertEqual(runs[0]['provenance'], old)
        self.assertNotEqual(runs[0]['provenance'], runs[1]['provenance'])

    def test_uncommitted_edits_run_without_committing_or_changing_user_files(self):
        init_job('video-a', self.root)
        tracked = self.root / 'tracked.py'
        tracked.write_text('original')
        self.git('add', 'tracked.py')
        self.commit('fixture code')
        # Accept the new base once; subsequent local edits need no extra flag.
        run_job('video-a', [sys.executable, '-c', 'pass'], self.root, accept_code_change=True)
        tracked.write_text('local edit')
        (self.root / 'uncommitted.py').write_text('staged edit')
        self.git('add', 'uncommitted.py')
        (self.root / 'new.py').write_text('untracked edit')
        before = self.git('status', '--porcelain')
        head = self.git('rev-parse', 'HEAD')
        command = [sys.executable, '-c',
                   'import os;from pathlib import Path;'
                   'Path(os.environ["CREATOR_WORK_DIR"],"ran.txt").write_text("ran")']
        self.assertEqual(run_job('video-a', command, self.root), 0)
        self.assertEqual((job_paths('video-a', self.root)['work'] / 'ran.txt').read_text(), 'ran')
        self.assertEqual(self.git('status', '--porcelain'), before)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(tracked.read_text(), 'local edit')
        runs = inspect_job('video-a', self.root)['record']['runs']
        self.assertFalse(runs[0]['working_tree']['dirty'])
        self.assertTrue(runs[1]['working_tree']['dirty'])
        self.assertEqual(runs[0]['provenance'], runs[1]['provenance'])
        self.assertNotEqual(runs[0]['working_tree']['status_sha256'],
                            runs[1]['working_tree']['status_sha256'])

    def test_dirty_runtime_catalog_still_requires_explicit_acceptance(self):
        init_job('video-a', self.root)
        catalog = self.root / 'extension/config/workspace-runtime.json'
        catalog.write_text(catalog.read_text(encoding='utf-8') + '\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'code/runtime catalog changed'):
            run_job('video-a', [sys.executable, '-c', 'pass'], self.root)
        self.assertEqual(run_job('video-a', [sys.executable, '-c', 'pass'], self.root,
                                 accept_code_change=True), 0)
        self.assertTrue(inspect_job('video-a', self.root)['record']['runs'][0]['working_tree']['dirty'])

    def test_non_main_branch_does_not_run(self):
        init_job('video-a', self.root)
        self.git('checkout', '-b', 'other')
        with self.assertRaisesRegex(ValueError, 'main'):
            run_job('video-a', [sys.executable, '-c', 'pass'], self.root)

    def test_inspect_does_not_create_job_or_locks(self):
        with self.assertRaises(FileNotFoundError):
            inspect_job('missing', self.root)
        self.assertFalse((self.root / 'extension/jobs').exists())
        self.assertFalse((self.root / 'extension/.runtime').exists())

    def test_identifiers_reject_path_traversal_and_windows_aliases(self):
        for job in ('../a', 'A', 'a/b', 'a\\b', 'con', 'a.', 'a ', 'aux', 'COM1', ''):
            with self.subTest(job=job), self.assertRaises(ValueError):
                identifier(job)
        init_job('a' * 80, self.root)

    def test_legacy_runtime_is_reused_without_copying_or_downloading(self):
        legacy = self.root / 'extension/.runtime/qwen-tts'
        legacy.mkdir(parents=True)
        self.assertEqual(runtime_path('qwen-tts', self.root), legacy)
        canonical = self.root / 'extension/.runtime/environments/qwen-tts/0.1.1'
        self.assertFalse(canonical.exists())
        canonical.mkdir(parents=True)
        self.assertEqual(runtime_path('qwen-tts', self.root), canonical)

    def test_runtime_catalog_cannot_escape_root(self):
        config = self.root / 'extension/config/workspace-runtime.json'
        config.write_text(json.dumps({'schema_version': 'creator-shared-runtime-v1',
                                     'components': {'test': {'path': '../../../outside'}}}))
        with self.assertRaises(ValueError):
            runtime_path('test', self.root)

    def test_selected_job_cannot_use_another_job_root(self):
        with patch.dict(os.environ, {'CREATOR_JOB_ID': 'video-a', 'CREATOR_JOB_ROOT': str(self.root / 'other')}):
            with self.assertRaises(ValueError):
                current_job_paths(self.root)

    def test_junctions_are_not_followed(self):
        outside = self.root / 'outside'
        outside.mkdir()
        link = self.root / 'escape'
        if os.name == 'nt':
            # Exact fixture link, no user directories. rmdir removes only the junction.
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
            if result.returncode:
                self.skipTest('junction creation unavailable')
            self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)
        else:
            link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            safe_path(self.root, 'escape/file')

    def test_lock_excludes_a_separate_process_and_recovers_after_crash(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'extension/src'), PYTHONDONTWRITEBYTECODE='1')
        command = [sys.executable, '-B', '-c',
                   'import sys;from pathlib import Path;from creator_workspace import Lease;'
                   'lock=Lease("gpu",Path(sys.argv[1]));lock.__enter__();print("locked",flush=True);sys.stdin.read()', str(self.root)]
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        self.assertEqual(child.stdout.readline().strip(), 'locked')
        with self.assertRaises(RuntimeError):
            with Lease('gpu', self.root):
                pass
        child.kill()
        child.wait(timeout=10)
        child.communicate()
        with Lease('gpu', self.root):
            pass

    def test_same_job_runner_cannot_start_twice(self):
        init_job('video-a', self.root)
        import hashlib
        with Lease('job-' + hashlib.sha256(b'video-a').hexdigest(), self.root):
            with self.assertRaises(RuntimeError):
                run_job('video-a', [sys.executable, '-c', 'pass'], self.root)

    def test_cancel_stops_owned_process_and_releases_lock(self):
        init_job('video-a', self.root)
        # Real child, controlled interruption in the parent's wait boundary.
        real_wait = subprocess.Popen.wait
        interrupted = []
        def wait(process, *args, **kwargs):
            if not interrupted and process.args[:2] == [sys.executable, '-c']:
                interrupted.append(True)
                raise KeyboardInterrupt
            return real_wait(process, *args, **kwargs)
        with patch.object(subprocess.Popen, 'wait', wait):
            self.assertEqual(run_job('video-a', [sys.executable, '-c', 'import time;time.sleep(30)'], self.root), 130)
        self.assertEqual(inspect_job('video-a', self.root)['record']['status'], 'cancelled')
        self.assertEqual(run_job('video-a', [sys.executable, '-c', 'pass'], self.root), 0)


if __name__ == '__main__':
    unittest.main()
