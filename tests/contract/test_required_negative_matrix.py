import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from tests.contract.test_pre_commit_hook import _run_hook
from video_workflow.checks.execution import run_process

ROOT = Path(__file__).resolve().parents[2]


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    return env


def _uv() -> str:
    candidate = os.environ.get("VIDEO_WORKFLOW_UV") or shutil.which("uv")
    assert candidate is not None
    assert Path(candidate).is_file()
    return candidate


def _run(
    argv: list[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 60,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(item) for item in argv],
        cwd=cwd,
        env=env or _base_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        shell=False,
    )


def _write(root: Path, relative: str, content: str = "") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _doctor_repository(
    root: Path,
    *,
    python_version: str = "3.12",
    include_tests: bool = True,
    backup_import: bool = False,
) -> None:
    files = {
        "AGENTS.md": "# fixture\n",
        "PROJECT_RULES.md": "# fixture\n",
        "README.md": "# fixture\n",
        "pyproject.toml": "[project]\nname='fixture'\nversion='0.0.0'\n",
        "uv.lock": "version = 1\nrevision = 3\n",
        ".python-version": f"{python_version}\n",
        "src/video_workflow/__init__.py": "",
        "src/video_workflow/cli.py": "",
        ".githooks/pre-commit": "workflow check --scope fast\nexit 127\n",
        ".github/workflows/ci.yml": "uv sync --locked\nworkflow check --scope full\n",
    }
    if backup_import:
        files["src/video_workflow/bad.py"] = "import backup.tools\n"
    if include_tests:
        files.update(
            {
                "tests/unit/checks/.gitkeep": "",
                "tests/contract/.gitkeep": "",
                "tests/smoke/.gitkeep": "",
            }
        )
    for relative, content in files.items():
        _write(root, relative, content)
    initialized = _run(["git", "init", "-q"], cwd=root)
    assert initialized.returncode == 0, initialized.stderr
    staged = _run(["git", "add", "-A"], cwd=root)
    assert staged.returncode == 0, staged.stderr


def _doctor(root: Path) -> subprocess.CompletedProcess[str]:
    return _run(
        [sys.executable, "-m", "video_workflow", "--root", root, "doctor", "--json"],
        cwd=root,
    )


def _scenario(name: str) -> subprocess.CompletedProcess[str]:
    env = _base_env()
    env["VIDEO_WORKFLOW_UV"] = _uv()
    env["VIDEO_WORKFLOW_TEST_SCENARIO"] = name
    return _run(
        [
            sys.executable,
            "-m",
            "video_workflow",
            "--root",
            ROOT,
            "check",
            "--scope",
            "fast",
            "--json",
        ],
        cwd=ROOT,
        env=env,
    )


def test_01_child_exit_seven_reaches_cli_and_hook():
    direct = _run([sys.executable, "-c", "raise SystemExit(7)"], cwd=ROOT)
    env = _base_env()
    env["VIDEO_WORKFLOW_TEST_CHILD_EXIT"] = "7"
    cli = _run(
        [sys.executable, "-m", "video_workflow", "check", "--scope", "fast", "--json"],
        cwd=ROOT,
        env=env,
    )
    assert direct.returncode == 7
    assert cli.returncode == 7
    assert _run_hook(include_uv=True).returncode == 7


def test_02_missing_checker_module_fails():
    completed = _scenario("missing_checker")
    payload = json.loads(completed.stdout)
    assert completed.returncode != 0
    assert payload["commands"][-1]["name"] == "format"
    assert payload["commands"][-1]["returncode"] != 0


def test_03_wrong_python_version_fails():
    with tempfile.TemporaryDirectory(prefix="stage01-wrong-python-") as directory:
        root = Path(directory)
        _doctor_repository(root, python_version="0.0")
        completed = _doctor(root)
    payload = json.loads(completed.stdout)
    check = next(item for item in payload["checks"] if item["code"] == "python_version")
    assert completed.returncode != 0
    assert check["ok"] is False


def test_04_declared_dependencies_missing_fails():
    runtime = Path(sys._base_executable)
    assert runtime.is_file()
    env = _base_env()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["VIDEO_WORKFLOW_UV"] = _uv()
    completed = _run(
        [runtime, "-m", "video_workflow", "--root", ROOT, "check", "--scope", "fast"],
        cwd=ROOT,
        env=env,
    )
    assert completed.returncode != 0


def test_05_lock_and_project_mismatch_fails():
    with tempfile.TemporaryDirectory(prefix="stage01-lock-mismatch-") as directory:
        root = Path(directory)
        shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
        shutil.copy2(ROOT / "uv.lock", root / "uv.lock")
        shutil.copy2(ROOT / ".python-version", root / ".python-version")
        project = (root / "pyproject.toml").read_text(encoding="utf-8")
        project = project.replace('version = "0.1.0"', 'version = "0.1.1"')
        (root / "pyproject.toml").write_text(project, encoding="utf-8", newline="\n")
        completed = _run(
            [_uv(), "lock", "--check", "--offline", "--no-cache"],
            cwd=root,
        )
    assert completed.returncode != 0


def test_06_outside_git_repository_fails():
    with tempfile.TemporaryDirectory(prefix="stage01-no-git-") as directory:
        completed = _doctor(Path(directory))
    assert completed.returncode != 0


def test_07_unexpected_git_root_fails():
    with tempfile.TemporaryDirectory(prefix="stage01-root-mismatch-") as directory:
        root = Path(directory)
        _doctor_repository(root)
        child = root / "nested"
        child.mkdir()
        completed = _doctor(child)
    payload = json.loads(completed.stdout)
    check = next(item for item in payload["checks"] if item["code"] == "repository_root")
    assert completed.returncode != 0
    assert check["ok"] is False


def test_08_corrupt_json_and_toml_fail():
    with tempfile.TemporaryDirectory(prefix="stage01-corrupt-config-") as directory:
        root = Path(directory)
        _write(root, "docs/rebuild/stage-00/BACKUP_MANIFEST.json", "{broken")
        json_result = _run(
            [sys.executable, "-m", "video_workflow.checks.baseline", root, "--json"],
            cwd=root,
        )
        _write(root, "pyproject.toml", "[broken")
        toml_result = _run(
            [_uv(), "lock", "--check", "--offline", "--no-cache"],
            cwd=root,
        )
    assert json_result.returncode != 0
    assert toml_result.returncode != 0


def test_09_unhandled_check_exception_is_nonzero():
    completed = _scenario("raise_exception")
    assert completed.returncode != 0
    assert "intentional contract exception" in completed.stderr


def test_10_backup_runtime_import_fails():
    with tempfile.TemporaryDirectory(prefix="stage01-backup-import-") as directory:
        root = Path(directory)
        _doctor_repository(root, backup_import=True)
        completed = _doctor(root)
    payload = json.loads(completed.stdout)
    check = next(item for item in payload["checks"] if item["code"] == "runtime_backup_boundary")
    assert completed.returncode != 0
    assert check["ok"] is False


def test_11_synthetic_forbidden_tracked_segment_fails_before_file_access():
    env = _base_env()
    env["VIDEO_WORKFLOW_TEST_TRACKED_PATH"] = "nested/inputs/synthetic-probe"
    completed = _run(
        [sys.executable, "-m", "video_workflow", "doctor", "--json"],
        cwd=ROOT,
        env=env,
    )
    payload = json.loads(completed.stdout)
    check = next(item for item in payload["checks"] if item["code"] == "tracked_data_boundary")
    assert completed.returncode != 0
    assert check["evidence"]["forbidden_count"] == 1
    assert "synthetic-probe" not in completed.stdout


def test_12_git_inventory_never_recursively_enumerates_filesystem():
    code = """
from pathlib import Path
from unittest.mock import patch
from video_workflow.checks.repository import git_tracked_paths
import sys
with patch.object(Path, 'rglob', side_effect=AssertionError('rglob called')):
    with patch('os.walk', side_effect=AssertionError('os.walk called')):
        _, result = git_tracked_paths(Path(sys.argv[1]))
raise SystemExit(result.returncode)
"""
    completed = _run([sys.executable, "-c", code, ROOT], cwd=ROOT)
    assert completed.returncode == 0


def test_13_korean_space_git_root_passes():
    with tempfile.TemporaryDirectory(prefix="Stage 01 한글 경로 ") as directory:
        root = Path(directory)
        _doctor_repository(root)
        completed = _doctor(root)
    assert completed.returncode == 0, completed.stderr


def test_14_hook_without_uv_is_exactly_127():
    assert _run_hook(include_uv=False).returncode == 127


def test_15_missing_tests_and_zero_collection_fail():
    with tempfile.TemporaryDirectory(prefix="stage01-missing-tests-") as directory:
        root = Path(directory)
        _doctor_repository(root, include_tests=False)
        missing = _run(
            [sys.executable, "-m", "video_workflow", "--root", root, "check", "--json"],
            cwd=root,
        )
    with tempfile.TemporaryDirectory(prefix="stage01-zero-tests-") as directory:
        zero = _run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=Path(directory),
            env={**_base_env(), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        )
    assert missing.returncode != 0
    assert zero.returncode == 5


@pytest.mark.parametrize(
    "scenario,status",
    [("missing_result", "missing"), ("skipped", "skipped"), ("not_run", "not_run")],
)
def test_16_missing_skipped_and_not_run_results_fail(scenario: str, status: str):
    completed = _scenario(scenario)
    payload = json.loads(completed.stdout)
    assert completed.returncode != 0
    assert payload["commands"][0]["status"] == status


def test_17_invalid_executable_permission_and_timeout_are_nonzero():
    missing = run_process(["definitely-missing-stage01-executable"])
    with tempfile.TemporaryDirectory(prefix="stage01-permission-") as directory:
        permission = run_process([directory])
    timeout = run_process(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout=0.01,
    )
    assert missing.returncode == 127
    assert permission.returncode == 126
    assert timeout.returncode == 124


def test_18_path_python_cannot_replace_locked_sys_executable():
    with tempfile.TemporaryDirectory(prefix="stage01-fake-python-") as directory:
        fake = Path(directory)
        _write(fake, "python.cmd", "@exit /b 99\n")
        env = _base_env()
        env["PATH"] = os.pathsep.join((str(fake), env.get("PATH", "")))
        env["VIDEO_WORKFLOW_UV"] = _uv()
        code = """
import json, sys
from pathlib import Path
from video_workflow.cli import _command_plan
plan = _command_plan(Path(sys.argv[1]), 'full')
required = {'format', 'lint', 'type', 'tests', 'backup_baseline', 'documents'}
python_commands = [
    argv[0]
    for name, argv, _, _ in plan
    if name in required
]
print(json.dumps({'expected': sys.executable, 'actual': python_commands}))
ok = python_commands and all(item == sys.executable for item in python_commands)
raise SystemExit(0 if ok else 1)
"""
        completed = _run([sys.executable, "-c", code, ROOT], cwd=ROOT, env=env)
    assert completed.returncode == 0


def test_required_negative_matrix_has_all_eighteen_cases():
    cases = {
        int(name.split("_")[1])
        for name, function in globals().items()
        if name.startswith("test_")
        and len(name.split("_")) > 2
        and name.split("_")[1].isdigit()
        and inspect.isfunction(function)
    }
    assert cases == set(range(1, 19))
