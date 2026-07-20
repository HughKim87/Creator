from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def run_process(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 300,
) -> ProcessResult:
    """Run one argv command without a shell and preserve its exit status."""
    command = tuple(argv)
    if not command or any(not isinstance(part, str) or not part for part in command):
        raise ValueError("argv must contain one or more non-empty strings")

    child_env = os.environ.copy()
    if env is not None:
        child_env.update(env)

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=child_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except FileNotFoundError as exc:
        return ProcessResult(command, 127, "", str(exc))
    except PermissionError as exc:
        return ProcessResult(command, 126, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        detail = stderr or f"command timed out after {timeout} seconds"
        return ProcessResult(command, 124, stdout, detail)

    return ProcessResult(command, completed.returncode, completed.stdout, completed.stderr)
