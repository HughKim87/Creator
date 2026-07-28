"""Domain-neutral export and migration manifest for Extension consumers."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


CORE_EXPORT_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "core_revision": "file-data-v1",
    "schema_version": 1,
    "compatibility": {
        "python": ">=3.11",
        "record_schema": 1,
        "read_legacy_records": True,
    },
    "migration": {
        "strategy": "append-only-compatible",
        "breaking_changes": "new_manifest_version_required",
        "protected_data": "never exported",
    },
    "exports": [
        "file_data.RecordStore",
        "file_data.WorkStateService",
        "file_data.MaintenanceService",
        "file_data.validate_record",
    ],
}


class ExportContractError(ValueError):
    """Raised when an export manifest is not domain-neutral."""


def validate_export_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise ExportContractError("export manifest must be an object")
    required = {"manifest_version", "core_revision", "schema_version", "compatibility", "migration", "exports"}
    if set(manifest) != required:
        raise ExportContractError(f"export manifest must contain exactly: {sorted(required)}")
    for field in ("manifest_version", "schema_version"):
        if manifest[field] != 1:
            raise ExportContractError(f"unsupported {field}")
    if not isinstance(manifest["core_revision"], str) or not manifest["core_revision"].strip():
        raise ExportContractError("core_revision must be non-empty")
    if not isinstance(manifest["compatibility"], Mapping) or not isinstance(manifest["migration"], Mapping):
        raise ExportContractError("compatibility and migration must be objects")
    exports = manifest["exports"]
    if not isinstance(exports, list) or not exports or any(not isinstance(item, str) for item in exports):
        raise ExportContractError("exports must be a non-empty list of strings")
    return deepcopy(dict(manifest))


def get_export_manifest() -> dict[str, Any]:
    return validate_export_manifest(CORE_EXPORT_MANIFEST)
