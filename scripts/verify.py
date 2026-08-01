"""Run the single deterministic Q0-Q3 verification gate for this checkout."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE_TESTS = ROOT / "core" / "tests"
EXTENSION_TESTS = ROOT / "extension" / "tests"
OPTIONAL_EXTENSION_TESTS = {
    "test_manual_upload_package.py",
    "test_title_thumbnail_package.py",
}

sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "extension" / "src"))

from extension_registry import artifact_owners  # noqa: E402
from file_data.document_data import CORE_ARTIFACT_OWNERS  # noqa: E402
from file_data.maintenance import MaintenanceService  # noqa: E402


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    python_path = os.pathsep.join(
        str(path) for path in (ROOT / "core" / "src", ROOT / "extension" / "src", CORE_TESTS)
    )
    environment["PYTHONPATH"] = python_path
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
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    }


def _test_gate() -> dict[str, Any]:
    core = _run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "core/tests", "-q"])
    optional_ready = shutil.which("python") is not None
    try:
        import PIL  # noqa: F401
    except ModuleNotFoundError:
        optional_ready = False
    extension_paths = sorted(EXTENSION_TESTS.glob("test_*.py"))
    if not optional_ready:
        extension_paths = [
            path for path in extension_paths if path.name not in OPTIONAL_EXTENSION_TESTS
        ]
    extension = _run(
        [sys.executable, "-B", "-m", "unittest", "-q", *[str(path) for path in extension_paths]]
    )
    return {
        "core": core,
        "extension": extension,
        "optional_thumbnail_tests": "ready" if optional_ready else "unavailable",
    }


def _maintenance_gate() -> dict[str, Any]:
    owners = {**CORE_ARTIFACT_OWNERS, **artifact_owners()}
    result = MaintenanceService(
        ROOT,
        artifact_owners=owners,
    ).verify(allow_core_changes=True)
    return {
        "ok": result["ok"],
        "status": result["status"],
        "errors": result["errors"],
        "metrics": result.get("metrics", {}),
        "artifacts": len(owners),
    }


def _failure_taxonomy(
    *,
    bootstrap: dict[str, Any],
    bootstrap_payload: dict[str, Any],
    node: dict[str, Any],
    tests: dict[str, Any],
    maintenance: dict[str, Any],
    clone: dict[str, Any] | str,
) -> list[dict[str, str]]:
    """Map gate failures to the next recovery owner without changing exit semantics."""

    failures: list[dict[str, str]] = []
    if not bootstrap["ok"] or not bootstrap_payload.get("ok"):
        failures.append({"stage": "bootstrap", "class": "setup", "status": "failed"})
    if not node["ok"]:
        failures.append({"stage": "node", "class": "setup", "status": "failed"})
    if not tests["core"]["ok"]:
        failures.append({"stage": "core-tests", "class": "test", "status": "failed"})
    if not tests["extension"]["ok"]:
        failures.append({"stage": "extension-tests", "class": "test", "status": "failed"})
    if not maintenance["ok"]:
        failures.append({"stage": "maintenance", "class": "contract", "status": "failed"})
    if isinstance(clone, dict) and not clone["ok"]:
        failures.append({"stage": "clone-conformance", "class": "conformance", "status": "failed"})
    for name, capability in bootstrap_payload.get("external_capabilities", {}).items():
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
    parser.add_argument("--no-clone", action="store_true", help="skip the outer clone conformance run")
    arguments = parser.parse_args()
    bootstrap = _run([sys.executable, "-B", "scripts/bootstrap.py", "--json"])
    try:
        bootstrap_payload = json.loads(bootstrap["stdout"])
    except json.JSONDecodeError:
        bootstrap_payload = {"ok": False, "status": "invalid_json"}
    node = _run(["node", "scripts/node_verify.mjs"])
    tests = _test_gate()
    maintenance = _maintenance_gate()
    clone: dict[str, Any] | str = "skipped"
    if not arguments.no_clone:
        clone = _run([sys.executable, "-B", "scripts/clone_conformance.py"])
    result = {
        "ok": bool(
            bootstrap["ok"]
            and bootstrap_payload.get("ok")
            and node["ok"]
            and tests["core"]["ok"]
            and tests["extension"]["ok"]
            and maintenance["ok"]
            and (arguments.no_clone or clone["ok"])
        ),
        "bootstrap": bootstrap_payload,
        "node": node,
        "tests": tests,
        "maintenance": maintenance,
        "clone_conformance": clone,
    }
    result["failure_taxonomy"] = _failure_taxonomy(
        bootstrap=bootstrap,
        bootstrap_payload=bootstrap_payload,
        node=node,
        tests=tests,
        maintenance=maintenance,
        clone=clone,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
