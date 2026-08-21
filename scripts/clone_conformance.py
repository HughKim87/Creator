"""Verify the project from clean clones placed in representative paths."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[1]


def _environment() -> dict[str, str]:
    """Give Git for Windows shell helpers a process-local search path."""

    environment = os.environ.copy()
    git = shutil.which("git")
    if os.name == "nt" and git:
        install_root = Path(git).resolve().parents[1]
        helpers = [
            install_root / "usr" / "bin",
            install_root / "mingw64" / "bin",
            install_root / "mingw64" / "libexec" / "git-core",
        ]
        available = [str(path) for path in helpers if path.is_dir()]
        if available:
            environment["PATH"] = os.pathsep.join(
                [*available, environment.get("PATH", "")]
            ).rstrip(os.pathsep)
    return environment


def _run(command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": (completed.stdout or "")[-1200:],
        "stderr": (completed.stderr or "")[-1200:],
    }


def _overlay_worktree(clone: Path) -> None:
    """Apply tracked edits and copy untracked non-protected files into a test clone."""

    diff = subprocess.run(
        [
            "git", "-c", "core.quotepath=false", "-c",
            f"safe.directory={ROOT.as_posix()}", "diff", "--binary", "HEAD",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    if diff.stdout:
        subprocess.run(
            ["git", "apply", "--binary", "-"],
            cwd=clone,
            input=diff.stdout,
            capture_output=True,
            check=True,
        )
    status = subprocess.run(
        [
            "git", "-c", "core.quotepath=false", "-c",
            f"safe.directory={ROOT.as_posix()}", "status", "--short",
            "--untracked-files=all", "-z",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    entries = status.split("\0")
    for entry in entries:
        if not entry or not entry.startswith("?? "):
            continue
        relative = Path(entry[3:])
        if set(relative.parts) & {"inputs", "outputs", ".git", ".runtime"}:
            continue
        source = ROOT / relative
        destination = clone / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    subprocess.run(
        ["git", "add", "-A"],
        cwd=clone,
        capture_output=True,
        check=True,
    )


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory(prefix="project-foundation-clone-") as raw_temp:
        temp_root = Path(raw_temp)
        for label in ("ascii", "한글 경로", "space path"):
            clone = temp_root / f"clone-{label}-{uuid.uuid4().hex}"
            cloned = _run(
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "clone",
                    "--no-hardlinks",
                    "--no-local",
                    str(ROOT),
                    str(clone),
                ],
                ROOT,
            )
            if not cloned["ok"]:
                results.append({"label": label, "clone": cloned})
                continue
            submodule = _run(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "-c",
                    f"submodule.core.url={(ROOT / 'core').as_posix()}",
                    "submodule",
                    "update",
                    "--init",
                    "--recursive",
                ],
                clone,
            )
            if not submodule["ok"]:
                results.append({"label": label, "clone": cloned, "submodule": submodule})
                continue
            _overlay_worktree(clone)
            bootstrap = _run(["python", "-B", "scripts/bootstrap.py", "--json"], clone)
            verify = _run(["python", "-B", "scripts/verify.py", "--no-clone"], clone)
            results.append(
                {
                    "label": label,
                    "clone": cloned,
                    "submodule": submodule,
                    "bootstrap": bootstrap,
                    "verify": verify,
                    "ok": bootstrap["ok"] and verify["ok"],
                }
            )
    result = {"ok": all(item.get("ok", False) for item in results), "clones": results}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
