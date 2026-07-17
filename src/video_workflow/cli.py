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


def _add_workspace_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", type=str, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workflow")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="validate the repository and environment")
    doctor.add_argument("--json", action="store_true")

    check = commands.add_parser("check", help="run the fail-closed project checks")
    check.add_argument("--scope", choices=("fast", "full"), default="fast")
    check.add_argument("--json", action="store_true")

    state = commands.add_parser("state", help="project state commands (SQLite truth)")
    state_commands = state.add_subparsers(dest="state_command", required=True)

    state_init = state_commands.add_parser("init", help="create workspace project + DB")
    state_init.add_argument("--workspace", type=Path, required=True)
    state_init.add_argument("--project", type=str, default=None)

    for name in ("status", "verify", "export"):
        sub = state_commands.add_parser(name)
        _add_workspace_arguments(sub)
        sub.add_argument("--json", action="store_true")

    register = state_commands.add_parser("register-source")
    _add_workspace_arguments(register)
    register.add_argument("--file", type=Path, default=None)
    register.add_argument("--sha256", type=str, default=None)
    register.add_argument("--size", type=int, default=None)
    register.add_argument("--locator", type=str, required=True)
    register.add_argument("--reason", type=str, default=None)

    advance = state_commands.add_parser("advance")
    _add_workspace_arguments(advance)
    advance.add_argument("--to", type=str, required=True)
    advance.add_argument("--reason", type=str, required=True)

    wait = state_commands.add_parser("wait")
    _add_workspace_arguments(wait)
    wait.add_argument("--reason", type=str, required=True)

    resume = state_commands.add_parser("resume")
    _add_workspace_arguments(resume)
    resume.add_argument("--reason", type=str, required=True)

    block = state_commands.add_parser("block")
    _add_workspace_arguments(block)
    block.add_argument("--external-code", type=str, required=True)
    block.add_argument("--reason", type=str, required=True)

    unblock = state_commands.add_parser("unblock")
    _add_workspace_arguments(unblock)
    unblock.add_argument("--reason", type=str, required=True)

    fail = state_commands.add_parser("fail")
    _add_workspace_arguments(fail)
    fail.add_argument("--code", type=str, required=True)
    fail.add_argument("--reason", type=str, required=True)
    fail.add_argument("--evidence", type=str, action="append", required=True)
    fail.add_argument("--tool", type=str, default=None)

    retry = state_commands.add_parser("retry")
    _add_workspace_arguments(retry)
    retry.add_argument("--reason", type=str, required=True)

    complete = state_commands.add_parser("complete")
    _add_workspace_arguments(complete)
    complete.add_argument("--reason", type=str, required=True)

    approval = commands.add_parser("approval", help="human approval trust boundary")
    approval_commands = approval.add_subparsers(dest="approval_command", required=True)

    request = approval_commands.add_parser("request")
    _add_workspace_arguments(request)
    request.add_argument(
        "--scope",
        choices=("generation", "technical_validation", "human_av", "waiver"),
        required=True,
    )
    request.add_argument("--generation-id", type=str, default=None)
    request.add_argument("--artifact-id", type=str, default=None)
    request.add_argument("--artifact-sha256", type=str, default=None)

    record = approval_commands.add_parser("record")
    _add_workspace_arguments(record)
    record.add_argument("--request-id", type=str, required=True)
    record.add_argument("--challenge", type=str, required=True)
    record.add_argument("--decision", choices=("approved", "rejected"), required=True)
    record.add_argument("--evidence-id", type=str, required=True)

    verify_approval = approval_commands.add_parser("verify")
    _add_workspace_arguments(verify_approval)
    verify_approval.add_argument("--approval-id", type=str, required=True)
    return parser


def _state_main(args: argparse.Namespace) -> int:
    """Handle `workflow state ...` and `workflow approval ...` commands."""
    import uuid as _uuid

    from video_workflow.domain import (
        DomainValidationError,
        ProjectId,
        SourceFingerprint,
    )
    from video_workflow.services.state_service import (
        StateService,
        fingerprint_file,
    )
    from video_workflow.services.state_views import export_views
    from video_workflow.storage import SqliteStateStore, StorageError

    def _fail(message: str) -> int:
        print(f"ERROR: {message}", file=sys.stderr)
        return 1

    try:
        if args.command == "state" and args.state_command == "init":
            project_id = (
                ProjectId.parse(args.project)
                if args.project
                else ProjectId.from_uuid(_uuid.uuid4())
            )
            workspace = args.workspace.resolve()
            store = SqliteStateStore.initialize(workspace, project_id)
            print(
                json.dumps(
                    {"project_id": project_id.value, "database": store.db_path.name},
                    ensure_ascii=False,
                )
            )
            return 0

        project_id = ProjectId.parse(args.project)
        store = SqliteStateStore.open(args.workspace.resolve(), project_id)
        service = StateService(store)

        if args.command == "approval":
            return _approval_main(args, store, service)

        state_command: str = args.state_command
        if state_command == "status":
            stored = store.load()
            payload: dict[str, object] = {
                "project_id": stored.state.project_id.value,
                "phase": stored.state.phase.value,
                "lifecycle": stored.state.lifecycle.value,
                "state_version": stored.state_version,
                "last_event_id": stored.last_event_id,
                "generations": len(stored.state.generations),
                "artifacts": len(stored.state.artifacts),
                "approvals": len(stored.state.approvals),
                "failures": len(stored.state.failures),
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if state_command == "verify":
            report = store.verify()
            payload = {
                "ok": report.ok,
                "checked": list(report.checked),
                "issues": [
                    {"code": issue.code, "message": issue.message} for issue in report.issues
                ],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0 if report.ok else 1
        if state_command == "export":
            status_path, handoff_path = export_views(store)
            print(
                json.dumps(
                    {"status": status_path.name, "handoff": handoff_path.name},
                    ensure_ascii=False,
                )
            )
            return 0
        if state_command == "register-source":
            if args.file is not None:
                fingerprint = fingerprint_file(args.file)
            elif args.sha256 is not None and args.size is not None:
                fingerprint = SourceFingerprint(
                    algorithm="sha256", digest=args.sha256, size_bytes=args.size
                )
            else:
                return _fail("register-source needs --file or --sha256 with --size")
            outcome = service.register_source(fingerprint, args.locator, reason=args.reason)
        elif state_command == "advance":
            outcome = service.advance(args.to, reason=args.reason)
        elif state_command == "wait":
            outcome = service.wait(args.reason)
        elif state_command in ("resume", "retry", "unblock"):
            outcome = service.resume(args.reason)
        elif state_command == "block":
            outcome = service.block(args.external_code, args.reason)
        elif state_command == "fail":
            outcome = service.fail(args.code, args.reason, tuple(args.evidence), tool=args.tool)
        elif state_command == "complete":
            outcome = service.complete(args.reason)
        else:  # pragma: no cover - argparse prevents this
            return _fail(f"unknown state command {state_command!r}")

        if outcome.rejection is not None:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "code": outcome.rejection.code,
                        "message": outcome.rejection.message,
                    },
                    ensure_ascii=False,
                )
            )
            return 1
        assert outcome.receipt is not None
        print(
            json.dumps(
                {
                    "ok": True,
                    "state_version": outcome.receipt.state_version,
                    "event_ids": list(outcome.receipt.event_ids),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (StorageError, DomainValidationError) as exc:
        return _fail(str(exc))


def _approval_main(
    args: argparse.Namespace,
    store: object,
    service: object,
) -> int:
    import uuid as _uuid

    from video_workflow.domain import (
        ApprovalDecision,
        ApprovalTarget,
        ApprovalType,
        GenerationId,
    )
    from video_workflow.services.state_service import StateService, new_challenge
    from video_workflow.storage import ApprovalTrustError, SqliteStateStore

    assert isinstance(store, SqliteStateStore)
    assert isinstance(service, StateService)

    if args.approval_command == "request":
        request_id = f"req-{_uuid.uuid4()}"
        challenge = new_challenge()
        store.create_approval_request(
            request_id=request_id,
            scope=args.scope,
            challenge=challenge,
            generation_id=args.generation_id,
            artifact_id=args.artifact_id,
            target_sha256=args.artifact_sha256,
        )
        print(
            json.dumps(
                {
                    "request_id": request_id,
                    "challenge": challenge,
                    "scope": args.scope,
                    "note": (
                        "The user must run 'workflow approval record' "
                        "interactively with this challenge."
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 0
    if args.approval_command == "record":
        row = store.load_approval_request(args.request_id)
        if row is None:
            print("ERROR: unknown approval request", file=sys.stderr)
            return 1
        if row["status"] != "pending":
            print("ERROR: approval request already consumed", file=sys.stderr)
            return 1
        target = ApprovalTarget(
            generation_id=(
                GenerationId.parse(row["generation_id"])
                if row["generation_id"] is not None
                else None
            ),
            content_hash=row["target_sha256"],
        )
        try:
            outcome = service.record_human_approval(
                ApprovalType.parse(row["scope"]),
                target,
                ApprovalDecision.parse(args.decision),
                request_id=args.request_id,
                challenge_response=args.challenge,
                evidence_id=args.evidence_id,
                expected_challenge=row["challenge"],
                request_target_sha256=row["target_sha256"],
                interactive=sys.stdin.isatty(),
            )
        except ApprovalTrustError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        if outcome.rejection is not None:
            print(f"ERROR: {outcome.rejection.code}: {outcome.rejection.message}", file=sys.stderr)
            return 1
        store.consume_approval_request(args.request_id)
        assert outcome.receipt is not None
        print(
            json.dumps(
                {"ok": True, "state_version": outcome.receipt.state_version}, ensure_ascii=False
            )
        )
        return 0
    if args.approval_command == "verify":
        request_row = store.load_approval_request(args.approval_id)
        stored = store.load()
        for record in stored.state.approvals:
            if record.approval_id.value == args.approval_id:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "approval_type": record.approval_type.value,
                            "decision": record.decision.value,
                            "actor_kind": record.actor.kind.value,
                            "target_generation": (
                                record.target.generation_id.value
                                if record.target.generation_id
                                else None
                            ),
                            "target_hash": record.target.content_hash,
                        },
                        ensure_ascii=False,
                    )
                )
                return 0
        _ = request_row
        print("ERROR: approval not found", file=sys.stderr)
        return 1
    print("ERROR: unknown approval command", file=sys.stderr)  # pragma: no cover
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command in ("state", "approval"):
        return _state_main(args)
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
