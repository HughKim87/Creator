import json
import tempfile
from pathlib import Path

from video_workflow.checks.baseline import _load_manifest, _safe_manifest_path


def test_manifest_path_rejects_data_and_traversal():
    assert _safe_manifest_path("nested/inputs/a.bin") is None
    assert _safe_manifest_path("nested/outputs/a.bin") is None
    assert _safe_manifest_path("../escape.py") is None
    assert _safe_manifest_path("tools/check.py") == "tools/check.py"


def test_corrupt_manifest_fails_closed():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "docs" / "rebuild" / "stage-00" / "BACKUP_MANIFEST.json"
        path.parent.mkdir(parents=True)
        path.write_text("{broken", encoding="utf-8")
        entries, check = _load_manifest(root)
    assert entries == []
    assert not check.ok


def test_manifest_with_forbidden_entry_fails_closed():
    payload = {
        "schema_version": 2,
        "files": [
            {
                "path": "nested/outputs/result.json",
                "role": "contract",
                "sha256": "0" * 64,
            }
        ],
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "docs" / "rebuild" / "stage-00" / "BACKUP_MANIFEST.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        entries, check = _load_manifest(root)
    assert entries == []
    assert not check.ok
