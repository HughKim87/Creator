"""Read-only runtime preflight for a tracked project checkout."""

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
        return {
            "status": "unavailable",
            "reason": "node executable is not available",
            "supported_range": ">=20 <22",
        }
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
        return {
            "status": "unavailable",
            "reason": completed.stderr.strip() or "node preflight returned invalid JSON",
            "supported_range": ">=20 <22",
        }
    if completed.returncode != 0:
        result.setdefault("reason", "node runtime is outside the supported range")
    return result


def preflight() -> dict[str, Any]:
    python_supported = sys.version_info >= (3, 11)
    pillow_available = importlib.util.find_spec("PIL") is not None
    return {
        "ok": python_supported,
        "project_root": ROOT.as_posix(),
        "runtime": {
            "python": {
                "version": ".".join(str(part) for part in sys.version_info[:3]),
                "status": "ready" if python_supported else "unavailable",
                "supported_range": ">=3.11",
            },
            "node": _node_status(),
        },
        "dependencies": {
            "core": {
                "status": "ready",
                "source": "python-standard-library",
            },
            "thumbnail": {
                "status": "ready" if pillow_available else "unavailable",
                "package": "Pillow",
                "install_hint": "python -m pip install -e .[thumbnail]"
                if not pillow_available
                else None,
            },
        },
        "external_capabilities": {
            "browser-user-session": {
                "status": "needs_user",
                "reason": "a signed-in user session is intentionally not part of clone bootstrap",
            }
        },
        "actions": {
            "install_performed": False,
            "network_used": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the machine-readable result")
    parser.parse_args()
    result = preflight()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
