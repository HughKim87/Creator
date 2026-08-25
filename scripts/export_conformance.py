"""Check empty-domain and dual-domain conformance against one Core manifest."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "extension" / "src"))

from domain_conformance import compare_domains, domain_conformance, empty_domain_conformance  # noqa: E402
from game_pilot import run_game_pilot  # noqa: E402


def main() -> int:
    empty = empty_domain_conformance()
    youtube = domain_conformance("youtube")
    game = run_game_pilot()
    comparison = compare_domains(youtube, game)
    result = {
        "ok": all(item["status"] == "pass" for item in (empty, youtube, game, comparison)),
        "empty_domain": empty,
        "youtube_extension": youtube,
        "game_extension": game,
        "comparison": comparison,
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
