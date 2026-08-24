"""Run the maintained Creator Host test inventory."""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / "extension" / "tests"
EXPECTED = {
    "test_browser_profile_resolution.py",
    "test_caption_review.py",
    "test_chrome_profile_skill_contract.py",
    "test_claude_entrypoint.py",
    "test_creative_delegation_contract.py",
    "test_export_conformance.py",
    "test_extension_registry.py",
    "test_extension_rule_routing.py",
    "test_learning_metrics.py",
    "test_local_runtime.py",
    "test_manual_upload_package.py",
    "test_staged_design_routing.py",
    "test_title_thumbnail_package.py",
    "test_upload_retention.py",
    "test_verification_pipeline.py",
    "test_video_editing_legacy_csv.py",
    "test_video_editing_premiere_cs6.py",
    "test_video_editing_subtitle.py",
    "test_video_editing_vertical_acceptance.py",
    "test_video_editing_workflow.py",
    "test_video_job_validation.py",
    "test_video_to_srt_runtime.py",
    "test_video_workflow_engine.py",
    "test_video_worktree_routing.py",
    "test_youtube_domain.py",
}
OPTIONAL_MODULES = {
    "test_manual_upload_package.py": ("PIL", "Pillow dependency is unavailable"),
    "test_title_thumbnail_package.py": ("PIL", "Pillow dependency is unavailable"),
}


def inventory_drift(discovered: set[str]) -> tuple[list[str], list[str]]:
    return sorted(EXPECTED - discovered), sorted(discovered - EXPECTED)


def run_inventory() -> dict[str, object]:
    discovered = {path.name for path in TEST_ROOT.glob("test_*.py")}
    missing, unexpected = inventory_drift(discovered)
    selected: list[str] = []
    skipped_modules: list[dict[str, str]] = []
    for name in sorted(EXPECTED & discovered):
        dependency = OPTIONAL_MODULES.get(name)
        if dependency and importlib.util.find_spec(dependency[0]) is None:
            skipped_modules.append({"module": name, "reason": dependency[1]})
        else:
            selected.append(name)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    sys.path.insert(0, str(TEST_ROOT))
    try:
        for name in selected:
            suite.addTests(loader.loadTestsFromName(Path(name).stem))
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    finally:
        sys.path.pop(0)

    return {
        "ok": not missing and not unexpected and result.wasSuccessful(),
        "expected_modules": sorted(EXPECTED),
        "discovered_modules": sorted(discovered),
        "missing_modules": missing,
        "unexpected_modules": unexpected,
        "selected_modules": selected,
        "skipped_modules": skipped_modules,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "display": stream.getvalue()[-2000:],
    }


def main() -> int:
    payload = run_inventory()
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
