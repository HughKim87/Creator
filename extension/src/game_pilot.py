"""Minimal game-development domain pilot owned entirely by Extension."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from domain_conformance import domain_conformance


GAME_DOMAIN_OWNER = "extension.game_pilot"


def run_game_pilot(manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    result = domain_conformance("game", owner=GAME_DOMAIN_OWNER, manifest=manifest)
    result.update(
        {
            "pilot": "minimal",
            "artifacts": [],
            "acceptance": "empty game domain registers owner and passes Core conformance",
        }
    )
    return result
