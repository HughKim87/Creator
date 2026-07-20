import tempfile
from pathlib import Path

from video_workflow.doctor import _runtime_boundary_check, run_doctor

ROOT = Path(__file__).resolve().parents[2]


def test_repository_subdirectory_is_not_accepted_as_root():
    report = run_doctor(ROOT / "src")
    check = next(item for item in report.checks if item.code == "repository_root")
    assert not check.ok


def test_outside_git_repository_fails_closed():
    with tempfile.TemporaryDirectory() as directory:
        report = run_doctor(Path(directory))
    check = next(item for item in report.checks if item.code == "repository_root")
    assert not check.ok


def test_backup_import_in_production_source_is_rejected():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "src" / "video_workflow" / "bad.py"
        source.parent.mkdir(parents=True)
        source.write_text("import backup.tools\n", encoding="utf-8")
        check = _runtime_boundary_check(root)
    assert not check.ok
    assert check.evidence["forbidden_import_count"] == 1
