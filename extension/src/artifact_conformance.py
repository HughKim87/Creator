"""Extension 문서 정본 block과 등록 JSON artifact의 의미 일치 검사."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
from typing import Any


ARTIFACT_BLOCK = re.compile(
    r"<!-- project-artifact:v1 path=(?P<path>[^ ]+) verify=json-semantic -->"
    r"\s*```json\s*(?P<payload>.*?)```\s*<!-- /project-artifact -->",
    re.S,
)


class ArtifactConformanceError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactConformanceError(f"중복 JSON key: {key}")
        result[key] = value
    return result


def _decode(raw: str, label: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                ArtifactConformanceError(f"{label}에 비유한 숫자가 있다: {item}")
            ),
        )
    except ArtifactConformanceError:
        raise
    except json.JSONDecodeError as exc:
        raise ArtifactConformanceError(f"{label}이 유효한 JSON이 아니다") from exc


def _relative_file(root: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise ArtifactConformanceError(f"{label}은 root 안 상대경로여야 한다: {value}")
    target = (root / candidate).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ArtifactConformanceError(f"{label}이 root 밖을 가리킨다: {value}") from exc
    if not target.is_file():
        raise ArtifactConformanceError(f"{label} 파일이 없다: {value}")
    return target


class ArtifactConformanceService:
    def __init__(self, root: Path | str, owners: Mapping[str, str]) -> None:
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ArtifactConformanceError("project root가 없다")
        self.owners = dict(owners)
        if len(self.owners) != len(set(self.owners)):
            raise ArtifactConformanceError("artifact target이 중복됐다")

    def check(self) -> dict[str, Any]:
        drift: list[dict[str, str]] = []
        for target_ref, owner_ref in sorted(self.owners.items()):
            try:
                owner = _relative_file(self.root, owner_ref, "owner")
                raw = owner.read_bytes()
                if raw.startswith(b"\xef\xbb\xbf") or b"\x00" in raw:
                    raise ArtifactConformanceError(f"owner가 BOM·NUL 없는 UTF-8이 아니다: {owner_ref}")
                text = raw.decode("utf-8", "strict")
                matches = [
                    match for match in ARTIFACT_BLOCK.finditer(text)
                    if match.group("path") == target_ref
                ]
                if len(matches) != 1:
                    raise ArtifactConformanceError(
                        f"owner에서 artifact block을 정확히 하나 찾아야 한다: {target_ref} ({len(matches)})"
                    )
                expected = _decode(matches[0].group("payload"), f"{owner_ref} 정본 block")
                target = _relative_file(self.root, target_ref, "artifact")
                actual = _decode(target.read_text(encoding="utf-8"), target_ref)
                if actual != expected:
                    drift.append({"target": target_ref, "owner": owner_ref, "reason": "semantic_drift"})
            except (ArtifactConformanceError, UnicodeDecodeError, OSError) as exc:
                drift.append({"target": target_ref, "owner": owner_ref, "reason": str(exc)})
        return {"artifacts": len(self.owners), "drift": drift, "ok": not drift}
