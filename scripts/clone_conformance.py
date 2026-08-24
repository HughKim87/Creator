"""Verify the project from clean clones placed in representative paths."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_PATHSPECS = (
    ":(exclude)inputs/**",
    ":(exclude)outputs/**",
    ":(exclude)extension/inputs/**",
    ":(exclude)extension/outputs/**",
)


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
            "--", ".", *PROTECTED_PATHSPECS,
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
            "--untracked-files=all", "-z", "--", ".", *PROTECTED_PATHSPECS,
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


def _result(results: list[dict], preflight: dict | None = None) -> dict:
    preflight_ok = preflight is None or preflight.get("ok", False)
    ok = bool(preflight_ok and results and all(item.get("ok", False) for item in results))
    result = {
        "ok": ok,
        "scope": "local",
        "status": "pass" if ok else "fail",
        "clones": results,
    }
    if preflight is not None:
        result["preflight"] = preflight
    return result


def _probe_temp_runtime(temp_root: Path) -> dict:
    """Fail fast when Node cannot execute a script below the clone temp root."""

    probe = temp_root / "node-temp-path-preflight.mjs"
    probe.write_text("console.log('node-temp-path-ready');\n", encoding="utf-8")
    try:
        process = _run(["node", str(probe)], temp_root)
    finally:
        probe.unlink(missing_ok=True)
    return {
        "ok": process["ok"],
        "status": "pass" if process["ok"] else "fail",
        "failure_class": None if process["ok"] else "environment",
        "reason": (
            "temporary clone root is executable by Node"
            if process["ok"]
            else "Node cannot execute below the temporary clone root"
        ),
        "process": process,
    }


def _run_clone_checks(clone: Path) -> dict:
    """Run dependent clone checks without continuing after bootstrap failure."""

    _overlay_worktree(clone)
    bootstrap = _run([sys.executable, "-B", "scripts/bootstrap.py", "--json"], clone)
    if not bootstrap["ok"]:
        return {
            "bootstrap": bootstrap,
            "verify": {
                "ok": None,
                "status": "not_run",
                "reason": "bootstrap failed",
            },
            "ok": False,
        }
    verify = _run([sys.executable, "-B", "scripts/verify.py", "--no-clone"], clone)
    return {"bootstrap": bootstrap, "verify": verify, "ok": verify["ok"]}


def _clone_results(temp_root: Path) -> list[dict]:
    results = []
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
        checks = _run_clone_checks(clone)
        results.append(
            {
                "label": label,
                "scope": "local",
                "clone": cloned,
                "submodule": submodule,
                **checks,
            }
        )
    return results


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="project-foundation-clone-") as raw_temp:
        temp_root = Path(raw_temp)
        preflight = _probe_temp_runtime(temp_root)
        results = _clone_results(temp_root) if preflight["ok"] else []
    result = _result(results, preflight)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
