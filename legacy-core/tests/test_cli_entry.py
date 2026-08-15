"""Test-only CLI entry point with explicit legacy-write capability injection."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))

from file_data.cli import main  # noqa: E402
from file_data.store import _ISOLATED_TEST_WRITE_CAPABILITY  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(_write_capability=_ISOLATED_TEST_WRITE_CAPABILITY))
