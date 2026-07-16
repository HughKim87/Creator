from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_DOCUMENTS = (
    "docs/rebuild/AGENT_EXECUTION_PLAN.md",
    "docs/rebuild/research/PROJECT_STRUCTURE_RESEARCH.md",
    "docs/rebuild/stage-00/AGENT_STAGE_00_BASELINE_FREEZE.md",
    "docs/rebuild/stage-00/STAGE_REPORT.md",
    "docs/rebuild/stage-01/AGENT_STAGE_01_TRUSTED_FOUNDATION.md",
)

FORBIDDEN_ROOT_DESIGN_DOCUMENTS = (
    "AGENT_EXECUTION_PLAN.md",
    "PROJECT_STRUCTURE_RESEARCH.md",
    "AGENT_STAGE_00_BASELINE_FREEZE.md",
    "AGENT_STAGE_01_TRUSTED_FOUNDATION.md",
)


def validate_documents(root: Path) -> tuple[bool, str]:
    missing = [path for path in REQUIRED_DOCUMENTS if not (root / path).is_file()]
    misplaced = [path for path in FORBIDDEN_ROOT_DESIGN_DOCUMENTS if (root / path).exists()]
    if missing or misplaced:
        return False, f"missing={len(missing)} misplaced={len(misplaced)}"
    return True, f"required={len(REQUIRED_DOCUMENTS)} misplaced=0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    ok, message = validate_documents(args.root.resolve())
    if args.json:
        print(json.dumps({"ok": ok, "message": message}, ensure_ascii=False))
    else:
        print(f"documents: {'PASS' if ok else 'FAIL'} - {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
