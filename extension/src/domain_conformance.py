"""Extension-side consumers of the domain-neutral Core export."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from file_data import get_export_manifest, validate_export_manifest


def _core_check(manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    checked = validate_export_manifest(manifest or get_export_manifest())
    rendered = repr(checked).casefold()
    leakage = [term for term in ("youtube", "game", "video") if term in rendered]
    return {
        "status": "pass" if not leakage else "fail",
        "core_revision": checked["core_revision"],
        "manifest_version": checked["manifest_version"],
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
