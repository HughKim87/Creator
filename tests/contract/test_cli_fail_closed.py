import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    return env


def test_workflow_check_preserves_child_exit_seven():
    env = _base_env()
    env["VIDEO_WORKFLOW_TEST_CHILD_EXIT"] = "7"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "video_workflow",
            "--root",
            str(ROOT),
            "check",
            "--scope",
            "fast",
            "--json",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 7
    assert payload["returncode"] == 7
    assert payload["commands"][0]["returncode"] == 7


def test_missing_declared_tools_fail_outside_locked_environment():
    runtime = Path(sys._base_executable)
    assert runtime.is_file()
    env = _base_env()
    env["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [runtime, "-m", "video_workflow", "--root", str(ROOT), "check", "--scope", "fast"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert completed.returncode != 0


def test_pytest_zero_collection_is_nonzero():
    with tempfile.TemporaryDirectory() as directory:
        env = _base_env()
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=directory,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
    assert completed.returncode == 5


def test_doctor_json_has_evidence_for_every_check():
    completed = subprocess.run(
        [sys.executable, "-m", "video_workflow", "--root", str(ROOT), "doctor", "--json"],
        cwd=ROOT,
        env=_base_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["ok"] is True
    assert all(isinstance(item["evidence"], dict) for item in payload["checks"])
