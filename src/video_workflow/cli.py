from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from video_workflow.checks.execution import ProcessResult, run_process
from video_workflow.doctor import DoctorReport, run_doctor


@dataclass(frozen=True)
class NamedResult:
    name: str
    process: ProcessResult
    status: str = "completed"


FAST_CHECKS = (
    "lock",
    "format",
    "lint",
    "type",
    "tests",
    "backup_baseline",
    "git_diff",
    "git_cached_diff",
)

FULL_CHECKS = (
    "lock",
    "format",
    "lint",
    "type",
    "tests",
    "backup_baseline",
    "documents",
    "git_diff",
    "git_cached_diff",
)


def _print_doctor(report: DoctorReport, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    print(f"WORKFLOW DOCTOR: {'PASS' if report.ok else 'FAIL'}")
    for check in report.checks:
        print(f"- {check.code}: {'PASS' if check.ok else 'FAIL'} - {check.message}")


def _check_environment() -> dict[str, str]:
    return {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}


def _uv_executable() -> str | None:
    explicit = os.environ.get("VIDEO_WORKFLOW_UV")
    if explicit:
        path = Path(explicit)
        return str(path) if path.is_file() else None
    return shutil.which("uv")


def _missing_uv_result() -> ProcessResult:
    return ProcessResult(("uv",), 127, "", "uv executable not found")


def _command_plan(
    root: Path, scope: str
) -> list[tuple[str, list[str], dict[str, str] | None, float]]:
    uv = _uv_executable()
    test_paths = ["tests/unit", "tests/contract"] if scope == "fast" else ["tests"]
    plan: list[tuple[str, list[str], dict[str, str] | None, float]] = []
    if uv is not None:
        plan.append(("lock", [uv, "lock", "--check", "--offline", "--no-cache"], None, 60))
    plan.extend(
        [
            (
                "format",
                [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
                _check_environment(),
                120,
            ),
            (
                "lint",
                [sys.executable, "-m", "ruff", "check", "src", "tests"],
                _check_environment(),
                120,
            ),
            (
                "type",
                [sys.executable, "-m", "mypy", "src"],
                _check_environment(),
                120,
            ),
            (
                "tests",
                [sys.executable, "-m", "pytest", "-q", "--strict-config", *test_paths],
                _check_environment(),
                300,
            ),
            (
                "backup_baseline",
                [sys.executable, "-m", "video_workflow.checks.baseline", str(root), "--json"],
                _check_environment(),
                120,
            ),
        ]
    )
    if scope == "full":
        plan.append(
            (
                "documents",
                [sys.executable, "-m", "video_workflow.checks.documents", str(root), "--json"],
                _check_environment(),
                60,
            )
        )
    plan.extend(
        [
            (
                "git_diff",
                ["git", "-c", f"safe.directory={root.as_posix()}", "diff", "--check"],
                None,
                30,
            ),
            (
                "git_cached_diff",
                [
                    "git",
                    "-c",
                    f"safe.directory={root.as_posix()}",
                    "diff",
                    "--cached",
                    "--check",
                ],
                None,
                30,
            ),
        ]
    )
    return plan


def _test_fault_plan(
    plan: list[tuple[str, list[str], dict[str, str] | None, float]],
) -> list[tuple[str, list[str], dict[str, str] | None, float]]:
    scenario = os.environ.get("VIDEO_WORKFLOW_TEST_SCENARIO")
    if scenario == "missing_checker":
        return [
            (
                name,
                [sys.executable, "-m", "video_workflow.checks.__missing_checker__"]
                if name == "format"
                else argv,
                env,
                timeout,
            )
            for name, argv, env, timeout in plan
        ]
    if scenario == "missing_result":
        return [item for item in plan if item[0] != "lint"]
    return plan


def _matrix_failure(status: str, message: str) -> NamedResult:
    process = ProcessResult(("workflow", "check-matrix"), 1, "", message)
    return NamedResult("check_matrix", process, status=status)


def _validate_plan(
    scope: str,
    plan: list[tuple[str, list[str], dict[str, str] | None, float]],
) -> NamedResult | None:
    required = FAST_CHECKS if scope == "fast" else FULL_CHECKS
    actual = tuple(item[0] for item in plan)
    if actual != required:
        return _matrix_failure("missing", f"required={required!r}, actual={actual!r}")
    return None


def _contract_probe(root: Path) -> NamedResult | None:
    raw = os.environ.get("VIDEO_WORKFLOW_TEST_CHILD_EXIT")
    if raw is None:
        return None
    try:
        requested = int(raw)
    except ValueError:
        requested = 2
    if not 1 <= requested <= 255:
        requested = 2
    result = run_process(
        [sys.executable, "-c", f"raise SystemExit({requested})"],
        cwd=root,
        env=_check_environment(),
        timeout=30,
    )
    return NamedResult("contract_child_exit_probe", result)


def _run_check(root: Path, scope: str) -> tuple[int, list[NamedResult], DoctorReport]:
    doctor = run_doctor(root)
    if not doctor.ok:
        return 1, [], doctor

    probe = _contract_probe(root)
    if probe is not None:
        return probe.process.returncode, [probe], doctor

    scenario = os.environ.get("VIDEO_WORKFLOW_TEST_SCENARIO")
    if scenario == "raise_exception":
        raise RuntimeError("intentional contract exception")
    if scenario in {"skipped", "not_run"}:
        failure = _matrix_failure(scenario, f"required check reported {scenario}")
        return failure.process.returncode, [failure], doctor

    results: list[NamedResult] = []
    uv_missing = _uv_executable() is None
    if uv_missing:
        missing = NamedResult("lock", _missing_uv_result())
        return missing.process.returncode, [missing], doctor

    plan = _test_fault_plan(_command_plan(root, scope))
    invalid = _validate_plan(scope, plan)
    if invalid is not None:
        return invalid.process.returncode, [invalid], doctor

    for name, argv, env, timeout in plan:
        result = NamedResult(name, run_process(argv, cwd=root, env=env, timeout=timeout))
        results.append(result)
        if result.process.returncode != 0:
            return result.process.returncode, results, doctor
    return 0, results, doctor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workflow")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="validate the repository and environment")
    doctor.add_argument("--json", action="store_true")

    check = commands.add_parser("check", help="run the fail-closed project checks")
    check.add_argument("--scope", choices=("fast", "full"), default="fast")
    check.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "doctor":
        report = run_doctor(root)
        _print_doctor(report, args.json)
        return 0 if report.ok else 1

    code, commands, doctor = _run_check(root, args.scope)
    if args.json:
        payload = {
            "ok": code == 0,
            "scope": args.scope,
            "returncode": code,
            "doctor": doctor.to_dict(),
            "commands": [
                {
                    "name": item.name,
                    "status": item.status,
                    "argv": list(item.process.argv),
                    "returncode": item.process.returncode,
                    "stdout": item.process.stdout,
                    "stderr": item.process.stderr,
                }
                for item in commands
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_doctor(doctor, False)
        for item in commands:
            result = item.process
            print(f"- {item.name}: {' '.join(result.argv)}")
            print(f"  returncode: {result.returncode}")
            if result.stdout.strip():
                print(result.stdout.rstrip())
            if result.stderr.strip():
                print(result.stderr.rstrip(), file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
