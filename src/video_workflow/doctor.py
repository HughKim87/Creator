from __future__ import annotations

import ast
import importlib.util
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from video_workflow.checks.repository import (
    forbidden_tracked_paths,
    git_root,
    git_tracked_paths,
)

REQUIRED_PATHS = (
    "AGENTS.md",
    "PROJECT_RULES.md",
    "README.md",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "src/video_workflow/__init__.py",
    "src/video_workflow/cli.py",
    "tests/unit/checks",
    "tests/contract",
    "tests/smoke",
    ".githooks/pre-commit",
    ".github/workflows/ci.yml",
)


@dataclass(frozen=True)
class CheckResult:
    code: str
    ok: bool
    message: str
    evidence: dict[str, object]


@dataclass(frozen=True)
class DoctorReport:
    root: str
    checks: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "root": self.root,
            "checks": [asdict(check) for check in self.checks],
        }


def _repository_root_check(root: Path) -> CheckResult:
    actual, command = git_root(root)
    if command.returncode != 0 or actual is None:
        return CheckResult(
            "repository_root",
            False,
            "Git root could not be resolved",
            {"returncode": command.returncode},
        )
    matches = actual == root
    return CheckResult(
        "repository_root",
        matches,
        "single expected Git root" if matches else "resolved Git root differs from requested root",
        {"matches_expected": matches},
    )


def _required_paths_check(root: Path) -> CheckResult:
    missing = [path for path in REQUIRED_PATHS if not (root / path).exists()]
    return CheckResult(
        "required_paths",
        not missing,
        f"present: {len(REQUIRED_PATHS) - len(missing)}/{len(REQUIRED_PATHS)}",
        {"missing_count": len(missing)},
    )


def _python_version_check(root: Path) -> CheckResult:
    version_file = root / ".python-version"
    if not version_file.is_file():
        return CheckResult("python_version", False, ".python-version is missing", {})
    expected = version_file.read_text(encoding="utf-8-sig").strip()
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"
    return CheckResult(
        "python_version",
        expected == actual,
        f"expected {expected}, running {actual}",
        {"expected": expected, "actual": actual},
    )


def _package_import_check() -> CheckResult:
    spec = importlib.util.find_spec("video_workflow")
    available = spec is not None and spec.origin is not None
    return CheckResult(
        "package_import",
        available,
        "video_workflow import is available" if available else "video_workflow is not importable",
        {"available": available},
    )


def _runtime_boundary_check(root: Path) -> CheckResult:
    backup = (root / "backup").resolve()
    backup_on_path = False
    for entry in sys.path:
        try:
            candidate = Path(entry or ".").resolve()
        except OSError:
            continue
        if candidate == backup or backup in candidate.parents:
            backup_on_path = True
            break

    forbidden_imports = 0
    source_root = root / "src" / "video_workflow"
    for source in source_root.rglob("*.py"):
        try:
            tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=source.name)
        except (OSError, UnicodeError, SyntaxError):
            forbidden_imports += 1
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                forbidden_imports += sum(
                    alias.name == "backup" or alias.name.startswith("backup.")
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                forbidden_imports += int(module == "backup" or module.startswith("backup."))

    ok = not backup_on_path and forbidden_imports == 0
    return CheckResult(
        "runtime_backup_boundary",
        ok,
        "backup is outside runtime imports" if ok else "backup runtime dependency detected",
        {"backup_on_sys_path": backup_on_path, "forbidden_import_count": forbidden_imports},
    )


def _tracked_boundary_check(root: Path) -> CheckResult:
    paths, command = git_tracked_paths(root)
    if command.returncode != 0:
        detail = command.stderr.strip() or "git ls-files failed"
        return CheckResult(
            "tracked_data_boundary",
            False,
            detail,
            {"returncode": command.returncode},
        )
    forbidden = forbidden_tracked_paths(paths)
    return CheckResult(
        "tracked_data_boundary",
        not forbidden,
        f"tracked paths checked: {len(paths)}",
        {"forbidden_count": len(forbidden), "tracked_count": len(paths)},
    )


def _wiring_check(root: Path) -> CheckResult:
    try:
        hook = (root / ".githooks" / "pre-commit").read_text(encoding="utf-8-sig")
        ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return CheckResult("check_wiring", False, type(exc).__name__, {})
    hook_ok = "workflow check --scope fast" in hook and "exit 127" in hook
    ci_ok = "workflow check --scope full" in ci and "uv sync --locked" in ci
    return CheckResult(
        "check_wiring",
        hook_ok and ci_ok,
        "hook and CI use the public check command",
        {"hook": hook_ok, "ci": ci_ok},
    )


def _root_path_check(root: Path) -> CheckResult:
    value = str(root)
    has_space = " " in value
    has_non_ascii = any(ord(character) > 127 for character in value)
    return CheckResult(
        "root_path",
        root.is_dir(),
        "root path resolved",
        {"contains_space": has_space, "contains_non_ascii": has_non_ascii},
    )


def run_doctor(root: Path) -> DoctorReport:
    resolved = root.resolve()
    checks = (
        _repository_root_check(resolved),
        _required_paths_check(resolved),
        _python_version_check(resolved),
        _package_import_check(),
        _runtime_boundary_check(resolved),
        _tracked_boundary_check(resolved),
        _wiring_check(resolved),
        _root_path_check(resolved),
    )
    return DoctorReport(root=resolved.as_posix(), checks=checks)
