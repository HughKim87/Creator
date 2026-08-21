"""Extension-side consumers of the domain-neutral Core export."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core_clients import public_core_manifest


MANIFEST_FIELDS = frozenset(
    {
        "manifest_version",
        "core_revision",
        "contract_version",
        "capability",
        "capability_version",
        "commands",
        "operations",
        "request_schema",
        "result_schema",
    }
)


def validate_public_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, Mapping) or set(manifest) != MANIFEST_FIELDS:
        raise ValueError(f"public Core manifest field가 정확하지 않다: {sorted(MANIFEST_FIELDS)}")
    if manifest["manifest_version"] != 1:
        raise ValueError("지원하지 않는 manifest_version")
    if manifest["capability"] != "shared_data" or manifest["capability_version"] != 1:
        raise ValueError("shared_data v1 공개 기능이 필요하다")
    if not isinstance(manifest["contract_version"], int) or isinstance(manifest["contract_version"], bool):
        raise ValueError("contract_version은 정수여야 한다")
    if not isinstance(manifest["core_revision"], str) or not manifest["core_revision"]:
        raise ValueError("core_revision이 필요하다")
    for field in ("commands", "operations"):
        value = manifest[field]
        if not isinstance(value, list) or not value or any(not isinstance(item, str) for item in value):
            raise ValueError(f"{field}는 비어 있지 않은 문자열 목록이어야 한다")
    for field in ("request_schema", "result_schema"):
        if not isinstance(manifest[field], str) or not manifest[field]:
            raise ValueError(f"{field}가 필요하다")
    return dict(manifest)


def _core_check(manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    checked = validate_public_manifest(manifest or public_core_manifest())
    rendered = repr(checked).casefold()
    leakage = [term for term in ("youtube", "game", "video") if term in rendered]
    return {
        "status": "pass" if not leakage else "fail",
        "core_revision": checked["core_revision"],
        "manifest_version": checked["manifest_version"],
        "contract_version": checked["contract_version"],
        "capability_version": checked["capability_version"],
        "leakage": leakage,
    }


def empty_domain_conformance(manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Prove that Core starts without a domain owner or domain artifacts."""

    result = _core_check(manifest)
    return {
        "domain": None,
        "owner": None,
        "artifacts": [],
        "acceptance": "startup contract passes without a domain owner",
        **result,
    }


def domain_conformance(
    domain: str,
    *,
    owner: str = "extension",
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Register one extension-owned domain against the same Core revision."""

    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain must be non-empty")
    result = _core_check(manifest)
    return {
        "domain": domain,
        "owner": owner,
        "artifacts": [],
        "acceptance": "domain owner is extension-local; Core manifest is unchanged",
        **result,
    }


def compare_domains(*reports: Mapping[str, Any]) -> dict[str, Any]:
    """Compare multiple domain reports without copying domain rules into Core."""

    if len(reports) < 2:
        raise ValueError("at least two domain reports are required")
    revisions = {report.get("core_revision") for report in reports}
    versions = {report.get("manifest_version") for report in reports}
    return {
        "status": "pass"
        if len(revisions) == 1 and len(versions) == 1 and all(report.get("status") == "pass" for report in reports)
        else "fail",
        "core_revisions": sorted(str(value) for value in revisions),
        "manifest_versions": sorted(str(value) for value in versions),
        "domains": [report.get("domain") for report in reports],
    }
