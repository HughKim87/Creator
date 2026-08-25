"""Read-only Runtime preflight for the Creator video Host checkout."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _node_status() -> dict[str, Any]:
    node = shutil.which("node")
    if node is None:
        return {"status": "unavailable", "supported_range": ">=20 <22"}
    completed = subprocess.run(
        [node, str(ROOT / "scripts" / "node_verify.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"status": "unavailable", "reason": "Node preflight returned invalid JSON"}
    return result


def preflight() -> dict[str, Any]:
    python_ready = sys.version_info >= (3, 11)
    pillow_ready = importlib.util.find_spec("PIL") is not None
    core_ready = (ROOT / "core").is_dir()
    return {
        "ok": bool(python_ready and core_ready),
        "runtime": {
            "python": {
                "version": ".".join(str(part) for part in sys.version_info[:3]),
                "minimum": "3.11",
                "status": "ready" if python_ready else "unavailable",
            },
            "node": _node_status(),
        },
        "core": {"status": "ready" if core_ready else "unavailable"},
        "optional_capabilities": {
            "thumbnail": {
                "status": "ready" if pillow_ready else "unavailable",
                "package": "Pillow",
            },
            "browser-user-session": {
                "status": "needs_user",
                "reason": "signed-in browser state is not part of repository bootstrap",
            },
        },
        "actions": {"install_performed": False, "network_used": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.parse_args()
    result = preflight()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
