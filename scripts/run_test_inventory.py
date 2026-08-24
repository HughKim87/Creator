"""Run one maintained test inventory and emit complete machine-readable results."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
INVENTORIES = {
    "core": (
        ROOT / "core" / "tests",
        {
            "test_integrity.py",
            "test_rule_routing.py",
            "test_state_contract.py",
        },
    ),
    "shared-data": (
        ROOT / "core" / "experimental" / "shared_data" / "tests",
        {
            "test_shared_cli.py",
            "test_shared_context.py",
            "test_shared_data.py",
            "test_shared_knowledge.py",
            "test_shared_lifecycle.py",
            "test_shared_work.py",
        },
    ),
    "extension": (
        ROOT / "extension" / "tests",
        {
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
            "test_video_editing_legacy_csv.py",
            "test_video_editing_premiere_cs6.py",
            "test_video_editing_subtitle.py",
            "test_video_editing_vertical_acceptance.py",
            "test_video_editing_workflow.py",
            "test_video_job_validation.py",
            "test_verification_pipeline.py",
            "test_video_to_srt_runtime.py",
            "test_video_workflow_engine.py",
            "test_video_worktree_routing.py",
            "test_youtube_domain.py",
        },
    ),
}
OPTIONAL_MODULES = {
    "test_manual_upload_package.py": ("PIL", "Pillow dependency is unavailable"),
    "test_title_thumbnail_package.py": ("PIL", "Pillow dependency is unavailable"),
}


def inventory_drift(scope: str, discovered: set[str]) -> tuple[list[str], list[str]]:
    expected = INVENTORIES[scope][1]
    return sorted(expected - discovered), sorted(discovered - expected)


def run_inventory(scope: str) -> dict[str, object]:
    test_root, expected = INVENTORIES[scope]
    discovered = {path.name for path in test_root.glob("test_*.py")} if test_root.is_dir() else set()
    missing, unexpected = inventory_drift(scope, discovered)
    skipped_modules: list[dict[str, str]] = []
    selected: list[str] = []
    for name in sorted(expected & discovered):
        dependency = OPTIONAL_MODULES.get(name)
        if dependency and importlib.util.find_spec(dependency[0]) is None:
            skipped_modules.append({"module": name, "reason": dependency[1]})
        else:
            selected.append(name)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    sys.path.insert(0, str(test_root))
    try:
        for name in selected:
            suite.addTests(loader.loadTestsFromName(Path(name).stem))
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    finally:
        sys.path.pop(0)

    failures = [{"test": str(test), "detail": detail[-2000:]} for test, detail in result.failures]
    errors = [{"test": str(test), "detail": detail[-2000:]} for test, detail in result.errors]
    skipped_tests = [{"test": str(test), "reason": reason} for test, reason in result.skipped]
    ok = not missing and not unexpected and result.wasSuccessful()
    return {
        "ok": ok,
        "scope": scope,
        "expected_modules": sorted(expected),
        "discovered_modules": sorted(discovered),
        "missing_modules": missing,
        "unexpected_modules": unexpected,
        "selected_modules": selected,
        "skipped_modules": skipped_modules,
        "tests_run": result.testsRun,
        "skipped_tests": skipped_tests,
        "failures": failures,
        "errors": errors,
        "display": stream.getvalue()[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=sorted(INVENTORIES), required=True)
    args = parser.parse_args()
    payload = run_inventory(args.scope)
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
