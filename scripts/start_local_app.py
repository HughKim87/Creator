"""Launch an existing local tool inside an explicit job and shared GPU lease."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import webbrowser

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extension/src'))
from creator_workspace import Lease, git, init_job, job_paths, run_job, runtime_path, stop_owned
from tts_build import is_current


def open_running_tts():
    try:
        with urllib.request.urlopen('http://127.0.0.1:7865/config', timeout=2) as response:
            config = json.load(response)
        if any(isinstance(value := component.get('props', {}).get('value'), str)
               and value.startswith('# 내 목소리로 대본 읽기')
               for component in config.get('components', [])):
            if not is_current(config):
                raise RuntimeError('TTS 서버가 이전 코드로 실행 중입니다. 브라우저를 닫아도 서버는 종료되지 않습니다. '
                                   'TTS를 실행한 콘솔에서 Ctrl+C로 서버를 종료한 뒤 다시 실행하세요.')
            webbrowser.open('http://127.0.0.1:7865')
            return True
    except (OSError, ValueError):
        pass
    return False


def run_desktop_tts(job, command):
    """Interactive UI session; production jobs keep their commit checks."""
    if git(ROOT, 'branch', '--show-current') != 'main':
        raise ValueError('desktop TTS execution requires main')
    paths = job_paths(job, ROOT)
    with Lease('job-' + hashlib.sha256(job.encode()).hexdigest(), ROOT), Lease('gpu', ROOT):
        temp = paths['work'] / 'tmp'
        temp.mkdir(exist_ok=True)
        env = dict(os.environ, CREATOR_JOB_ID=job, CREATOR_JOB_ROOT=str(paths['root']),
                   CREATOR_WORKSPACE_ROOT=str(ROOT), CREATOR_WORK_DIR=str(paths['work']),
                   CREATOR_OUTPUT_DIR=str(paths['outputs']), CREATOR_LOG_DIR=str(paths['logs']),
                   CREATOR_GPU_LEASE_HELD='1', PYTHONDONTWRITEBYTECODE='1',
                   TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
        ffmpeg = runtime_path('ffmpeg', ROOT) / 'bin'
        if ffmpeg.is_dir():
            env['PATH'] = str(ffmpeg) + os.pathsep + env.get('PATH', '')
        process = subprocess.Popen(command, cwd=ROOT, env=env)
        try:
            return process.wait()
        finally:
            stop_owned(process)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', choices=('tts', 'replier'))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--job')
    selection.add_argument('--desktop', action='store_true', help='Open the personal TTS workspace')
    parser.add_argument('--accept-code-change', action='store_true')
    args = parser.parse_args()
    if args.desktop and args.app != 'tts':
        parser.error('--desktop is only supported for tts')
    if args.desktop and open_running_tts():
        return 0
    if args.desktop:
        args.job = 'voice-tts-desktop'
    paths = job_paths(args.job, ROOT)
    if not paths['root'].exists():
        init_job(args.job, ROOT)
    if args.app == 'tts':
        python = runtime_path('qwen-tts', ROOT) / 'venv/Scripts/python.exe'
        if not python.is_file():
            parser.exit(1, 'Qwen environment is absent; installation requires separate authorization.\n')
        command = [str(python), '-B', str(ROOT / 'extension/src/qwen_tts_local.py'), '--open-browser']
    else:
        exe = runtime_path('replier-desktop', ROOT) / '24HReplier.exe'
        if not exe.is_file():
            subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                            '-File', str(ROOT / 'scripts/Build-24HReplier.ps1')], cwd=ROOT, check=True)
        command = [str(exe)]
    if args.desktop:
        return run_desktop_tts(args.job, command)
    return run_job(args.job, command, ROOT, gpu=True, accept_code_change=args.accept_code_change)


if __name__ == '__main__':
    raise SystemExit(main())
