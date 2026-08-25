"""Extension-owned artifact registrations passed to the foundation verifier."""

from __future__ import annotations


EXTENSION_ARTIFACT_OWNERS: dict[str, str] = {
    ".obsidian/app.json": "README.md",
    "extension/schemas/youtube-evidence-request-v1.schema.json": (
        "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md"
    ),
    "extension/schemas/youtube-evidence-pack-v1.schema.json": (
        "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md"
    ),
    "extension/examples/youtube/foundation-evidence.request.json": (
        "extension/docs/domain/youtube/YOUTUBE_EVIDENCE_PACK_CONTRACT.md"
    ),
}


def artifact_owners() -> dict[str, str]:
    """Return a copy so the verifier cannot mutate the extension registry."""

    return dict(EXTENSION_ARTIFACT_OWNERS)
