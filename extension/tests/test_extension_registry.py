from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "extension" / "src"))

from extension_registry import artifact_owners  # noqa: E402
from artifact_conformance import ArtifactConformanceService  # noqa: E402


class ExtensionRegistryTests(unittest.TestCase):
    def test_extension_registry_is_one_way_and_preserves_all_artifacts(self) -> None:
        extension_owners = artifact_owners()
        self.assertEqual(
            set(extension_owners),
            {
                ".obsidian/app.json",
                "extension/schemas/youtube-evidence-request-v1.schema.json",
                "extension/schemas/youtube-evidence-pack-v1.schema.json",
                "extension/examples/youtube/foundation-evidence.request.json",
            },
        )
        result = ArtifactConformanceService(ROOT, extension_owners).check()
        self.assertEqual(result, {"artifacts": 4, "drift": [], "ok": True})

    def test_extension_registry_returns_a_copy(self) -> None:
        owners = artifact_owners()
        owners.clear()
        self.assertEqual(len(artifact_owners()), 4)


if __name__ == "__main__":
    unittest.main()
