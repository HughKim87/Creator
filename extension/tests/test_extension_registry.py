from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "src"))
sys.path.insert(0, str(ROOT / "extension" / "src"))

from extension_registry import artifact_owners  # noqa: E402
from file_data.document_data import ArtifactService, CORE_ARTIFACT_OWNERS  # noqa: E402


class ExtensionRegistryTests(unittest.TestCase):
    def test_extension_registry_is_one_way_and_preserves_all_artifacts(self) -> None:
        extension_owners = artifact_owners()
        self.assertEqual(
            set(extension_owners),
            {
                "extension/schemas/youtube-evidence-request-v1.schema.json",
                "extension/schemas/youtube-evidence-pack-v1.schema.json",
                "extension/examples/youtube/foundation-evidence.request.json",
            },
        )
        combined = {**CORE_ARTIFACT_OWNERS, **extension_owners}
        result = ArtifactService(ROOT, artifact_owners=combined).check()
        self.assertEqual(result, {"artifacts": 20, "drift": []})

    def test_extension_registry_returns_a_copy(self) -> None:
        owners = artifact_owners()
        owners.clear()
        self.assertEqual(len(artifact_owners()), 3)


if __name__ == "__main__":
    unittest.main()
