"""Validate, render, archive and recheck one already-approved manual package."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


SCRIPTS = Path(__file__).resolve().parent


def run(script: Path, *args: object) -> dict:
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), *map(str, args)], capture_output=True)
    if result.returncode:
        raise ValueError(result.stdout.decode("utf-8", errors="replace") + result.stderr.decode("utf-8", errors="replace"))
    data = json.loads(result.stdout.decode("utf-8"))
    if data.get("errors") or data.get("warnings"):
        raise ValueError(f"validation did not pass: {data}")
    return data


def finalize(package: Path, *, apply: bool = False) -> dict:
    package = package.resolve()
    # Read-only validation checks paths, approvals and hashes before any write.
    checks = {"package": run(SCRIPTS / "prepare_upload_package.py", package, "--check")}
    title = Path(checks["package"]["artifacts"]["title_thumbnail_package"])
    checks["title"] = run(SCRIPTS.parent.parent / "youtube-title-thumbnail/scripts/validate_package.py", title, "--require-approved", "--require-editorial")
    if not apply:
        return {"status": "ready", "checks": checks, "external_actions": "none"}
    checks["guide"] = run(SCRIPTS / "prepare_upload_package.py", package)
    checks["retention_plan"] = run(SCRIPTS / "retain_upload_package.py", package)
    if checks["retention_plan"]["unexpected_directories"]:
        raise ValueError("unexpected output directories; archive not applied")
    checks["retention_apply"] = run(SCRIPTS / "retain_upload_package.py", package, "--apply")
    checks["retention_after"] = run(SCRIPTS / "retain_upload_package.py", package)
    if checks["retention_after"]["archive"] or checks["retention_after"]["unexpected_directories"]:
        raise ValueError("final output retention recheck failed")
    checks["package_after"] = run(SCRIPTS / "prepare_upload_package.py", package, "--check")
    return {"status": "complete", "checks": checks, "external_actions": "none"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = finalize(args.package, apply=args.apply)
        code = 0
    except (OSError, ValueError, KeyError) as exc:
        result = {"status": "invalid", "errors": [str(exc)], "external_actions": "none"}
        code = 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
