import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".githooks" / "pre-commit"


def _shell() -> str:
    direct = shutil.which("sh")
    if direct:
        return direct
    result = subprocess.run(
        ["git", "--exec-path"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    candidate = Path(result.stdout.strip()).parents[2] / "bin" / "sh.exe"
    assert candidate.is_file()
    return str(candidate)


def _write_command(directory: Path, name: str, body: str) -> None:
    command = directory / name
    command.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8", newline="\n")
    command.chmod(0o755)


def _run_hook(
    include_uv: bool,
    *,
    uv_name: str = "uv",
    uv_body: str = "exit 7",
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        commands = Path(directory)
        _write_command(commands, "git", f'printf "%s\\n" "{ROOT.as_posix()}"')
        if include_uv:
            _write_command(commands, uv_name, uv_body)
        if os.name == "nt" and uv_name.lower().endswith(".exe"):
            _write_command(
                commands,
                "cygpath",
                'test "$1" = "-w" || exit 8\n'
                'case "$2" in *.exe) printf "%s\\n" "C:/fake/uv.exe" ;; '
                "*) exit 8 ;; esac",
            )
        env = os.environ.copy()
        env.pop("VIDEO_WORKFLOW_UV", None)
        env["PATH"] = str(commands)
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "safe.directory"
        env["GIT_CONFIG_VALUE_0"] = ROOT.as_posix()
        return subprocess.run(
            [_shell(), str(HOOK)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )


def test_hook_preserves_uv_child_exit_seven():
    assert _run_hook(include_uv=True).returncode == 7


def test_hook_missing_uv_is_127():
    assert _run_hook(include_uv=False).returncode == 127


@pytest.mark.skipif(os.name != "nt", reason="Git Bash extension normalization is Windows-only")
def test_hook_normalizes_extensionless_git_bash_uv_path_for_windows_python():
    body = 'case "$VIDEO_WORKFLOW_UV" in *:*.exe) exit 0 ;; *) exit 9 ;; esac'
    completed = _run_hook(include_uv=True, uv_name="uv.exe", uv_body=body)
    assert completed.returncode == 0, completed.stderr
