"""Run the deterministic local verification gate for the Creator video Host."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_PATHSPECS = (
    ":(exclude)inputs/**",
    ":(exclude)outputs/**",
    ":(exclude)extension/inputs/**",
    ":(exclude)extension/outputs/**",
)

sys.path.insert(0, str(ROOT / "extension" / "src"))

from artifact_conformance import ArtifactConformanceService  # noqa: E402
from extension_registry import artifact_owners  # noqa: E402


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(path) for path in (ROOT / "core" / "src", ROOT / "core", ROOT / "extension" / "src")
    )
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": stdout[-2000:],
        "stderr": stderr[-2000:],
        "_stdout_full": stdout,
    }


def _parse_json(process: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(process["_stdout_full"])
    except (json.JSONDecodeError, TypeError):
        return {"ok": False, "status": "invalid_json", "display": process["stdout"]}
    return payload if isinstance(payload, dict) else {"ok": False, "status": "invalid_json_type"}


def _git_snapshot() -> dict[str, Any]:
    command = [
        "git",
        "-c",
        "core.quotepath=false",
        "-c",
        f"safe.directory={ROOT.as_posix()}",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "-z",
        "--",
        ".",
        *PROTECTED_PATHSPECS,
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    return {
        "ok": completed.returncode == 0,
        "entries": sorted(item for item in completed.stdout.decode("utf-8", errors="replace").split("\0") if item),
    }


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _public(item) for key, item in value.items() if not key.startswith("_")}
    if isinstance(value, list):
        return [_public(item) for item in value]
    return value


def main() -> int:
    before = _git_snapshot()
    bootstrap_process = _run([sys.executable, "-B", "scripts/bootstrap.py", "--json"])
    bootstrap = _parse_json(bootstrap_process)
    bootstrap["ok"] = bool(bootstrap_process["ok"] and bootstrap.get("ok"))
    node = _run(["node", "scripts/node_verify.mjs"])
    consumer = _run(
        [
            sys.executable,
            "-B",
            "-m",
            "core_check",
            "--core-root",
            "core",
            "--consumer-root",
            ".",
            "gate",
        ]
    )
    tests_process = _run([sys.executable, "-B", "scripts/run_test_inventory.py"])
    tests = _parse_json(tests_process)
    tests["ok"] = bool(tests_process["ok"] and tests.get("ok"))
    owners = artifact_owners()
    artifact_result = ArtifactConformanceService(ROOT, owners).check()
    artifacts = {
        "ok": artifact_result["ok"],
        "drift": artifact_result["drift"],
        "artifacts": len(owners),
    }
    after = _git_snapshot()
    working_tree = {
        "ok": bool(before["ok"] and after["ok"] and before["entries"] == after["entries"]),
        "before": before,
        "after": after,
    }
    result = {
        "ok": bool(bootstrap["ok"] and node["ok"] and consumer["ok"] and tests["ok"] and artifacts["ok"] and working_tree["ok"]),
        "bootstrap": bootstrap,
        "node": node,
        "consumer": consumer,
        "tests": tests,
        "artifacts": artifacts,
        "working_tree": working_tree,
    }
    print(json.dumps(_public(result), ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
