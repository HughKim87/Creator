"""Launch an existing local tool inside an explicit job and shared GPU lease."""
import argparse
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extension/src'))
from creator_workspace import init_job, job_paths, run_job, runtime_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', choices=('tts', 'replier'))
    parser.add_argument('--job', required=True)
    parser.add_argument('--accept-code-change', action='store_true')
    args = parser.parse_args()
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
    return run_job(args.job, command, ROOT, gpu=True, accept_code_change=args.accept_code_change)


if __name__ == '__main__':
    raise SystemExit(main())
