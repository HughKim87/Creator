"""Run the deterministic local verification gate for this checkout."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_PATHSPECS = (
    ":(exclude)inputs/**",
    ":(exclude)outputs/**",
    ":(exclude)extension/inputs/**",
    ":(exclude)extension/outputs/**",
)

sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "extension" / "src"))

from artifact_conformance import ArtifactConformanceService  # noqa: E402
from core_check.declarations import declared_compatibility  # noqa: E402
from extension_registry import artifact_owners  # noqa: E402


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(path)
        for path in (
            ROOT / "core",
            ROOT / "core" / "src",
            ROOT / "extension" / "src",
            ROOT / "core" / "tests",
        )
    )
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(command: list[str], *, cwd: Path = ROOT) -> dict[str, Any]:
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
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": stdout[-2000:],
        "stderr": stderr[-2000:],
        "_stdout_full": stdout,
        "_stderr_full": stderr,
    }


def _parse_json(process: dict[str, Any], label: str) -> dict[str, Any]:
    try:
        payload = json.loads(process["_stdout_full"])
    except (json.JSONDecodeError, TypeError):
        return {
            "ok": False,
            "status": "invalid_json",
            "label": label,
            "display": process["stdout"],
        }
    if not isinstance(payload, dict):
        return {"ok": False, "status": "invalid_json_type", "label": label}
    return payload


def _version(executable: str) -> tuple[int, int, int] | None:
    process = _run(
        [
            executable,
            "-c",
            "import json,sys; print(json.dumps(list(sys.version_info[:3])))",
        ]
    )
    if not process["ok"]:
        return None
    try:
        value = json.loads(process["_stdout_full"])
    except json.JSONDecodeError:
        return None
    if not isinstance(value, list) or len(value) != 3 or not all(isinstance(v, int) for v in value):
        return None
    return tuple(value)  # type: ignore[return-value]


def _runtime_contract() -> tuple[dict[str, Any], str | None]:
    core_minimum = tuple(
        int(part) for part in declared_compatibility(ROOT / "core")["python_min"].split(".")
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirement = project["project"]["requires-python"]
    match = re.search(r">=\s*(\d+)\.(\d+)", requirement)
    maintainer_minimum = tuple(int(part) for part in match.groups()) if match else ()

    core_executable: str | None = None
    for name in (f"python{core_minimum[0]}.{core_minimum[1]}", f"python{core_minimum[0]}{core_minimum[1]}"):
        candidate = shutil.which(name)
        if candidate and (_version(candidate) or ())[:2] == core_minimum:
            core_executable = str(Path(candidate).resolve())
            break
    maintainer_version = sys.version_info[:3]
    payload = {
        "ok": bool(
            core_executable
            and maintainer_minimum
            and maintainer_version[:2] >= maintainer_minimum
        ),
        "core": {
            "minimum": ".".join(map(str, core_minimum)),
            "executable": core_executable,
            "version": _version(core_executable) if core_executable else None,
            "status": "ready" if core_executable else "unavailable",
        },
        "maintainer": {
            "minimum": ".".join(map(str, maintainer_minimum)),
            "executable": str(Path(sys.executable).resolve()),
            "version": maintainer_version,
            "status": "ready"
            if maintainer_minimum and maintainer_version[:2] >= maintainer_minimum
            else "unavailable",
        },
    }
    return payload, core_executable


def _inventory(scope: str, executable: str) -> dict[str, Any]:
    process = _run(
        [executable, "-B", "scripts/run_test_inventory.py", "--scope", scope]
    )
    payload = _parse_json(process, f"{scope}-test-inventory")
    payload["process"] = process
    payload["ok"] = bool(process["ok"] and payload.get("ok"))
    return payload


def _test_gate(core_python: str | None) -> dict[str, Any]:
    if core_python is None:
        unavailable = {
            "ok": False,
            "status": "not_run",
            "reason": "declared Core minimum Python is unavailable",
        }
        core = dict(unavailable)
        shared = dict(unavailable)
    else:
        core = _inventory("core", core_python)
        shared = _inventory("shared-data", core_python)
    extension = _inventory("extension", sys.executable)
    return {
        "ok": bool(core["ok"] and shared["ok"] and extension["ok"]),
        "core": core,
        "shared_data": shared,
        "extension": extension,
    }


def _maintenance_gate() -> dict[str, Any]:
    owners = artifact_owners()
    result = ArtifactConformanceService(ROOT, owners).check()
    return {
        "ok": result["ok"],
        "status": "pass" if result["ok"] else "attention_required",
        "errors": result["drift"],
        "metrics": {},
        "artifacts": len(owners),
    }


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
        "entries": sorted(
            entry for entry in completed.stdout.decode("utf-8", errors="replace").split("\0") if entry
        ),
        "error": completed.stderr.decode("utf-8", errors="replace")[-1000:],
    }


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _public(item) for key, item in value.items() if not key.startswith("_")}
    if isinstance(value, list):
        return [_public(item) for item in value]
    return value


def _remote_conformance_state() -> dict[str, Any]:
    return {
        "ok": None,
        "scope": "remote",
        "status": "not_run",
        "reason": "requires approved published refs and remote credentials",
    }


def _failure_taxonomy(result: dict[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for stage, failure_class in (
        ("runtime-contract", "setup"),
        ("bootstrap", "setup"),
        ("node", "setup"),
        ("core-contract", "contract"),
        ("tests", "test"),
        ("maintenance", "contract"),
        ("local-conformance", "conformance"),
        ("working-tree", "side_effect"),
    ):
        value = result[stage.replace("-", "_")]
        if isinstance(value, dict) and value.get("ok") is False:
            failures.append({"stage": stage, "class": failure_class, "status": "failed"})
    for name, capability in result["bootstrap"].get("external_capabilities", {}).items():
        if capability.get("status") != "ready":
            failures.append(
                {
                    "stage": name,
                    "class": "external",
                    "status": str(capability.get("status", "unavailable")),
                }
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-clone", action="store_true", help="skip local clone conformance")
    arguments = parser.parse_args()
    before = _git_snapshot()
    runtime_contract, core_python = _runtime_contract()

    bootstrap_process = _run([sys.executable, "-B", "scripts/bootstrap.py", "--json"])
    bootstrap = _parse_json(bootstrap_process, "bootstrap")
    bootstrap["ok"] = bool(bootstrap_process["ok"] and bootstrap.get("ok"))

    node = _run(["node", "scripts/node_verify.mjs"])
    if core_python:
        contract = _run(
            [
                core_python,
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
    else:
        contract = {
            "ok": False,
            "status": "not_run",
            "reason": "declared Core minimum Python is unavailable",
        }
    tests = _test_gate(core_python)
    maintenance = _maintenance_gate()

    if arguments.no_clone:
        local_conformance: dict[str, Any] = {
            "ok": True,
            "scope": "local",
            "status": "not_run",
            "reason": "--no-clone selected for inner verification",
        }
    else:
        clone_process = _run([sys.executable, "-B", "scripts/clone_conformance.py"])
        local_conformance = _parse_json(clone_process, "local-clone-conformance")
        local_conformance["process"] = clone_process
        local_conformance["ok"] = bool(clone_process["ok"] and local_conformance.get("ok"))

    after = _git_snapshot()
    working_tree = {
        "ok": bool(before["ok"] and after["ok"] and before["entries"] == after["entries"]),
        "before": before,
        "after": after,
    }
    remote_conformance = _remote_conformance_state()
    result = {
        "ok": False,
        "runtime_contract": runtime_contract,
        "bootstrap": bootstrap,
        "bootstrap_process": bootstrap_process,
        "node": node,
        "core_contract": contract,
        "tests": tests,
        "maintenance": maintenance,
        "local_conformance": local_conformance,
        "remote_conformance": remote_conformance,
        "working_tree": working_tree,
    }
    result["ok"] = bool(
        runtime_contract["ok"]
        and bootstrap["ok"]
        and node["ok"]
        and contract["ok"]
        and tests["ok"]
        and maintenance["ok"]
        and local_conformance["ok"]
        and working_tree["ok"]
    )
    result["failure_taxonomy"] = _failure_taxonomy(result)
    print(json.dumps(_public(result), ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
