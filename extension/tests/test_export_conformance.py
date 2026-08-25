from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "extension" / "src"))

from domain_conformance import compare_domains, domain_conformance, empty_domain_conformance  # noqa: E402
from game_pilot import run_game_pilot  # noqa: E402


class ExportConformanceTests(unittest.TestCase):
    def test_empty_domain_and_game_pilot_use_same_core_revision(self) -> None:
        empty = empty_domain_conformance()
        youtube = domain_conformance("youtube")
        game = run_game_pilot()
        comparison = compare_domains(youtube, game)
        self.assertEqual(empty["status"], "pass")
        self.assertEqual(game["status"], "pass")
        self.assertEqual(game["owner"], "extension.game_pilot")
        self.assertEqual(comparison["status"], "pass")
        self.assertEqual(comparison["core_revisions"], ["contract-2:shared_data-1"])
        self.assertEqual(game["artifacts"], [])

    def test_domain_reports_do_not_change_manifest(self) -> None:
        youtube = domain_conformance("youtube")
        game = run_game_pilot()
        self.assertEqual(youtube["manifest_version"], game["manifest_version"])
        self.assertEqual(youtube["leakage"], [])
        self.assertEqual(game["leakage"], [])


if __name__ == "__main__":
    unittest.main()
