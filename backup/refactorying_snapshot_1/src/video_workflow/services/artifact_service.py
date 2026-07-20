"""Artifact promotion with a crash-consistent protocol and reconciliation
(stage 04 task 04-5).

SQLite commits and filesystem moves are not one atomic transaction, so this
service never claims "atomic promotion". Instead:

1. the artifact file is produced into a generation-scoped staging directory
   on the same volume as its final path, fully flushed, then verified
   (existence, size, SHA-256);
2. a DB transaction records the artifact (lifecycle ``staging``) through the
   domain command;
3. the file is moved to its final path with ``os.replace`` (same volume);
4. a separate DB transaction re-verifies path and hash and marks the
   artifact ``ready``;
5. any failure leaves the record ``staging``/``failed``/``quarantined`` for
   ``workflow artifact reconcile`` — never a false success.

``reconcile`` detects mismatches without deleting anything and only
auto-fixes the provably safe ``staging -> ready`` case (final file present,
hash and lineage confirmed).
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from video_workflow.domain import ArtifactId, ArtifactRole, GenerationId
from video_workflow.services.state_service import ApplyOutcome, StateService
from video_workflow.storage.sqlite_store import SqliteStateStore

ARTIFACTS_DIR = "artifacts"
STAGING_DIR = ".staging"


class ArtifactPromotionError(RuntimeError):
    """Promotion failed at a stated boundary; nothing was reported as success."""


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class PromotionReceipt:
    artifact_id: str
    relative_path: str
    content_sha256: str
    size_bytes: int
    lifecycle: str


@dataclass(frozen=True, slots=True)
class ReconcileFinding:
    code: str
    artifact_id: str | None
    path: str | None
    detail: str
    resolution: str


@dataclass(frozen=True, slots=True)
class ReconcileReport:
    findings: tuple[ReconcileFinding, ...]
    auto_fixed: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not self.findings


class ArtifactService:
    """Filesystem+DB artifact promotion for one project."""

    def __init__(self, store: SqliteStateStore, service: StateService) -> None:
        self._store = store
        self._service = service

    def _final_dir(self, generation_id: GenerationId) -> Path:
        return self._store.project_dir / ARTIFACTS_DIR / generation_id.value

    def _staging_dir(self, generation_id: GenerationId) -> Path:
        return self._store.project_dir / ARTIFACTS_DIR / STAGING_DIR / generation_id.value

    def promote(
        self,
        generation_id: GenerationId,
        role: ArtifactRole,
        final_name: str,
        produce: Callable[[Path], None],
        *,
        tool_version: str | None = None,
        parent_ids: tuple[ArtifactId, ...] = (),
    ) -> PromotionReceipt:
        if "/" in final_name or "\\" in final_name or final_name.startswith("."):
            raise ArtifactPromotionError(f"invalid artifact name: {final_name!r}")
        staging_dir = self._staging_dir(generation_id)
        final_dir = self._final_dir(generation_id)
        staging_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)
        staging_path = staging_dir / final_name
        final_path = final_dir / final_name
        if final_path.exists():
            raise ArtifactPromotionError(
                f"final artifact path already exists: {final_name} (no overwrite)"
            )
        if staging_path.exists():
            raise ArtifactPromotionError(
                f"stale staging file exists: {final_name}; run artifact reconcile"
            )

        # 1) Produce and flush the file in staging (same volume as final).
        produce(staging_path)
        if not staging_path.is_file():
            raise ArtifactPromotionError("producer did not create the staging file")
        with staging_path.open("rb+") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        size = staging_path.stat().st_size
        if size == 0:
            raise ArtifactPromotionError("staging file is empty (0 bytes)")
        digest = _sha256_of(staging_path)

        # 2) Record the artifact (lifecycle 'staging') through the domain.
        relative = f"{ARTIFACTS_DIR}/{generation_id.value}/{final_name}"
        outcome: ApplyOutcome = self._service.record_artifact(
            generation_id,
            role,
            digest,
            parent_ids=parent_ids,
            relative_path=relative,
            size_bytes=size,
            tool_version=tool_version,
        )
        if outcome.rejection is not None:
            raise ArtifactPromotionError(
                f"artifact registration refused: {outcome.rejection.code}: "
                f"{outcome.rejection.message}"
            )
        stored = self._store.load()
        artifact_id = stored.state.artifacts[-1].artifact_id.value

        # 3) Atomic same-volume replace into the final path.
        try:
            os.replace(staging_path, final_path)
        except OSError as exc:
            self._store.set_artifact_lifecycle(artifact_id, "failed", expected_current="staging")
            raise ArtifactPromotionError(
                f"file replace failed; artifact left failed for reconcile: {exc}"
            ) from exc

        # 4) Separate transaction: re-verify then mark ready.
        if not final_path.is_file() or _sha256_of(final_path) != digest:
            self._store.set_artifact_lifecycle(
                artifact_id, "quarantined", expected_current="staging"
            )
            raise ArtifactPromotionError("post-replace verification failed; artifact quarantined")
        self._store.set_artifact_lifecycle(
            artifact_id, "ready", expected_current="staging", relative_path=relative
        )
        return PromotionReceipt(
            artifact_id=artifact_id,
            relative_path=relative,
            content_sha256=digest,
            size_bytes=size,
            lifecycle="ready",
        )

    # -- reconciliation ------------------------------------------------------

    def reconcile(self) -> ReconcileReport:
        findings: list[ReconcileFinding] = []
        auto_fixed: list[str] = []
        rows = self._store.list_artifact_rows()
        recorded_paths: set[str] = set()
        for row in rows:
            relative = row["relative_path"]
            lifecycle = row["artifact_lifecycle"]
            artifact_id = row["artifact_id"]
            if relative is None:
                continue
            recorded_paths.add(relative)
            path = self._store.project_dir / relative
            staging_path = (
                self._store.project_dir
                / ARTIFACTS_DIR
                / STAGING_DIR
                / row["generation_id"]
                / Path(relative).name
            )
            file_exists = path.is_file()
            if lifecycle == "staging":
                if file_exists and _sha256_of(path) == row["content_sha256"]:
                    # Provably safe auto-fix: final file matches recorded hash.
                    self._store.set_artifact_lifecycle(
                        artifact_id, "ready", expected_current="staging"
                    )
                    auto_fixed.append(artifact_id)
                elif staging_path.is_file():
                    findings.append(
                        ReconcileFinding(
                            code="stale_staging",
                            artifact_id=artifact_id,
                            path=str(staging_path.name),
                            detail="staging record and staging file remain",
                            resolution="verify producer outcome; re-run promotion "
                            "or mark failed (user decision)",
                        )
                    )
                else:
                    findings.append(
                        ReconcileFinding(
                            code="staging_without_file",
                            artifact_id=artifact_id,
                            path=relative,
                            detail="DB staging record without staging or final file",
                            resolution="mark failed after user confirmation",
                        )
                    )
            elif lifecycle == "ready":
                if not file_exists:
                    findings.append(
                        ReconcileFinding(
                            code="ready_without_file",
                            artifact_id=artifact_id,
                            path=relative,
                            detail="ready artifact file is missing",
                            resolution="restore from backup or quarantine "
                            "(user decision; nothing deleted)",
                        )
                    )
                elif _sha256_of(path) != row["content_sha256"]:
                    self._store.set_artifact_lifecycle(
                        artifact_id, "quarantined", expected_current="ready"
                    )
                    findings.append(
                        ReconcileFinding(
                            code="hash_mismatch",
                            artifact_id=artifact_id,
                            path=relative,
                            detail="file content no longer matches recorded hash; "
                            "artifact quarantined (file untouched)",
                            resolution="investigate modification; user decides "
                            "restore or supersede",
                        )
                    )
        artifacts_root = self._store.project_dir / ARTIFACTS_DIR
        if artifacts_root.is_dir():
            for path in sorted(artifacts_root.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(self._store.project_dir).as_posix()
                if f"/{STAGING_DIR}/" in f"/{relative}":
                    continue
                if relative not in recorded_paths:
                    findings.append(
                        ReconcileFinding(
                            code="orphan_file",
                            artifact_id=None,
                            path=relative,
                            detail="file exists without a DB record",
                            resolution="quarantine candidate; deletion requires user approval",
                        )
                    )
        return ReconcileReport(findings=tuple(findings), auto_fixed=tuple(auto_fixed))
