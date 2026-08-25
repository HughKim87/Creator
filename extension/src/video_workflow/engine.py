"""Small, deterministic VIDEO_JOB orchestration engine.

The engine owns next-step selection and phase boundaries.  It does not own
browser sessions, NotebookLM actions, protected media, or user approvals.
Those capabilities are represented by adapters and explicit boundary results.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from typing import Any, Protocol


STAGE_ORDER = (
    "research",
    "video",
    "captions",
    "title_thumbnail",
    "upload_package",
)
STAGE_SKILLS = {
    "research": "notebooklm-research-topic",
    "video": "notebooklm-generate-video",
    "captions": "video-to-srt",
    "title_thumbnail": "youtube-title-thumbnail",
    "upload_package": "prepare-youtube-upload",
}
ACTIVE_STATUSES = frozenset({"in_progress", "needs_user", "blocked"})


class WorkflowError(ValueError):
    """Raised when an engine operation violates a workflow boundary."""


class WorkflowAdapter(Protocol):
    """Adapter boundary shared by deterministic and external execution."""

    def preflight(self, stage: str, job: Mapping[str, Any]) -> dict[str, Any]: ...

    def execute(self, stage: str, job: Mapping[str, Any]) -> dict[str, Any]: ...


@dataclass
class SyntheticArtifactStore:
    """In-memory artifact store used only by deterministic acceptance tests."""

    items: dict[str, bytes]

    def __init__(self) -> None:
        self.items = {}

    def put(self, reference: str, content: bytes | str) -> str:
        if not isinstance(reference, str) or not reference.strip():
            raise WorkflowError("artifact reference must be non-empty")
        data = content.encode("utf-8") if isinstance(content, str) else content
        if not isinstance(data, bytes) or not data:
            raise WorkflowError("artifact content must be non-empty bytes")
        self.items[reference] = data
        return _sha256(data)

    def hash(self, reference: str) -> str | None:
        data = self.items.get(reference)
        return None if data is None else _sha256(data)


def _sha256(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


class LocalSyntheticAdapter:
    """Deterministic local adapter; it never touches protected project data."""

    def __init__(self, store: SyntheticArtifactStore) -> None:
        self.store = store

    def preflight(self, stage: str, job: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "status": "ready",
            "adapter": "local_synthetic",
            "stage": stage,
            "reason": "synthetic fixture has no external capability",
        }

    def execute(self, stage: str, job: Mapping[str, Any]) -> dict[str, Any]:
        reference = f"fixture://video-workflow/{stage}"
        content = f"synthetic:{stage}:{job.get('job_id', 'unknown')}".encode("utf-8")
        fingerprint = self.store.put(reference, content)
        result = {
            "status": "complete",
            "adapter": "local_synthetic",
            "stage": stage,
            "artifacts": [{"ref": reference, "sha256": fingerprint}],
            "validation": f"synthetic {stage} artifact verified",
        }
        if stage == "video":
            result["playback_check"] = {
                "elapsed_seconds": 1,
                "progressed": True,
                "paused": True,
            }
        return result


class ExternalAgentAdapter:
    """Explicit unavailable boundary for browser/NotebookLM execution."""

    def __init__(self, reason: str = "external agent adapter requires a user session") -> None:
        self.reason = reason

    def preflight(self, stage: str, job: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "adapter": "external_agent",
            "stage": stage,
            "reason": self.reason,
        }

    def execute(self, stage: str, job: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "adapter": "external_agent",
            "stage": stage,
            "reason": self.reason,
        }


class WorkflowEngine:
    """Select, execute, verify, and resume one VIDEO_JOB stage at a time."""

    def __init__(
        self,
        job: Mapping[str, Any],
        *,
        adapters: Mapping[str, WorkflowAdapter] | None = None,
        artifact_store: SyntheticArtifactStore | None = None,
        validator: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        if not isinstance(job, Mapping):
            raise WorkflowError("VIDEO_JOB must be an object")
        self.job = deepcopy(dict(job))
        self.artifact_store = artifact_store or SyntheticArtifactStore()
        self.adapters = dict(adapters or {})
        self.default_adapter: WorkflowAdapter = ExternalAgentAdapter()
        self.validator = validator

    def _validate_job(self) -> dict[str, Any] | None:
        if self.validator is None:
            return None
        result = dict(self.validator(self.job))
        if result.get("status") != "valid":
            return {
                "status": "blocked",
                "reason": "VIDEO_JOB validation failed",
                "errors": list(result.get("errors", [])),
            }
        return None

    def _stage(self, name: str) -> dict[str, Any]:
        stages = self.job.get("stages")
        if not isinstance(stages, dict) or not isinstance(stages.get(name), dict):
            raise WorkflowError(f"VIDEO_JOB stage is missing: {name}")
        return stages[name]

    def next_step(self) -> dict[str, Any]:
        """Return one ready stage or an explicit boundary status."""

        invalid = self._validate_job()
        if invalid is not None:
            return {"stage": None, **invalid}
        previous_complete = True
        for name in STAGE_ORDER:
            stage = self._stage(name)
            status = stage.get("status")
            if status in ACTIVE_STATUSES:
                return {
                    "status": status,
                    "stage": name,
                    "skill": STAGE_SKILLS[name],
                    "mode": "resume" if status == "in_progress" else "boundary",
                    "reason": stage.get("note", "active stage requires attention"),
                }
            if status != "complete" and status != "pending":
                return {
                    "status": "blocked",
                    "stage": name,
                    "skill": STAGE_SKILLS[name],
                    "reason": f"unsupported stage status: {status}",
                }
            if status == "pending":
                if not previous_complete:
                    return {
                        "status": "blocked",
                        "stage": name,
                        "skill": STAGE_SKILLS[name],
                        "reason": "prior stage is not complete",
                    }
                return {
                    "status": "ready",
                    "stage": name,
                    "skill": STAGE_SKILLS[name],
                    "mode": "start",
                }
            previous_complete = previous_complete and status == "complete"
        return {"status": "complete", "stage": None, "reason": "all stages complete"}

    def _adapter_for(self, stage: str) -> WorkflowAdapter:
        return self.adapters.get(stage, self.default_adapter)

    def _resume_check(self, stage: str) -> dict[str, Any] | None:
        data = self._stage(stage)
        if data.get("status") != "in_progress":
            return None
        artifacts = data.get("artifacts", [])
        hashes = data.get("artifact_hashes", {})
        if not artifacts:
            return None
        if not isinstance(hashes, Mapping):
            return {
                "status": "blocked",
                "stage": stage,
                "reason": "resume requires artifact_hashes for recorded artifacts",
            }
        verified_hashes: dict[str, str] = {}
        for reference in artifacts:
            if not isinstance(reference, str):
                return {
                    "status": "blocked",
                    "stage": stage,
                    "reason": "resume artifact references must be strings",
                }
            actual = self.artifact_store.hash(reference)
            if actual is None or hashes.get(reference) != actual:
                return {
                    "status": "blocked",
                    "stage": stage,
                    "reason": f"artifact fingerprint changed or is unavailable: {reference}",
                }
            verified_hashes[reference] = actual
        return {
            "status": "ready",
            "stage": stage,
            "skill": STAGE_SKILLS[stage],
            "mode": "resume_verified",
            "artifacts": [
                {"ref": reference, "sha256": fingerprint}
                for reference, fingerprint in verified_hashes.items()
            ],
            "validation": "recorded artifact fingerprints re-verified; stage execution not repeated",
        }

    def preflight(self) -> dict[str, Any]:
        step = self.next_step()
        if step["status"] != "ready" and step["status"] != "in_progress":
            return step
        stage = step["stage"]
        resume = self._resume_check(stage)
        if resume is not None:
            return resume
        stage_data = self._stage(stage)
        if stage == "title_thumbnail":
            contract = self.job.get("thumbnail_contract", {})
            if isinstance(contract, Mapping) and contract.get("approval_mode") == "review_gated":
                approval = stage_data.get("approval")
                if not isinstance(approval, Mapping) or approval.get("status") != "approved":
                    return {
                        "status": "needs_user",
                        "stage": stage,
                        "skill": STAGE_SKILLS[stage],
                        "reason": "title and thumbnail approval is user-owned",
                    }
        adapter_result = self._adapter_for(stage).preflight(stage, self.job)
        return {"stage": stage, "skill": STAGE_SKILLS[stage], **adapter_result}

    def execute(self) -> dict[str, Any]:
        ready = self.preflight()
        if ready.get("status") != "ready" and ready.get("status") != "in_progress":
            return ready
        stage = ready["stage"]
        if ready.get("mode") == "resume_verified":
            return {
                "status": "complete",
                "stage": stage,
                "skill": STAGE_SKILLS[stage],
                "artifacts": ready["artifacts"],
                "validation": ready["validation"],
            }
        result = self._adapter_for(stage).execute(stage, self.job)
        return {"stage": stage, "skill": STAGE_SKILLS[stage], **result}

    def verify(self, execution: Mapping[str, Any]) -> dict[str, Any]:
        """Verify result hashes and boundary status without claiming user approval."""

        result = dict(execution)
        if result.get("status") != "complete":
            return result
        stage = result.get("stage")
        artifacts = result.get("artifacts")
        if not isinstance(stage, str) or stage not in STAGE_ORDER:
            return {**result, "status": "blocked", "reason": "execution stage is invalid"}
        if not isinstance(artifacts, list) or not artifacts:
            return {**result, "status": "blocked", "reason": "completed execution has no artifacts"}
        hashes: dict[str, str] = {}
        for artifact in artifacts:
            if not isinstance(artifact, Mapping) or not isinstance(artifact.get("ref"), str):
                return {**result, "status": "blocked", "reason": "artifact record is invalid"}
            reference = artifact["ref"]
            actual = self.artifact_store.hash(reference)
            if actual is None or artifact.get("sha256") != actual:
                return {
                    **result,
                    "status": "blocked",
                    "reason": f"artifact fingerprint verification failed: {reference}",
                }
            hashes[reference] = actual
        return {**result, "status": "verified", "artifact_hashes": hashes}

    def transition(self, verified: Mapping[str, Any]) -> dict[str, Any]:
        """Apply only a verified stage result to the in-memory VIDEO_JOB snapshot."""

        result = dict(verified)
        stage_name = result.get("stage")
        status = result.get("status")
        if not isinstance(stage_name, str) or stage_name not in STAGE_ORDER:
            raise WorkflowError("verified result has no valid stage")
        stage = self._stage(stage_name)
        if status == "verified":
            artifacts = result["artifacts"]
            stage.update(
                {
                    "status": "complete",
                    "artifacts": [item["ref"] for item in artifacts],
                    "artifact_hashes": dict(result["artifact_hashes"]),
                    "validation": result.get("validation", "verified"),
                    "note": result.get("note", ""),
                }
            )
            if "playback_check" in result:
                stage["playback_check"] = deepcopy(result["playback_check"])
        elif status in {"needs_user", "blocked", "unavailable"}:
            stage["status"] = "needs_user" if status == "needs_user" else "blocked"
            stage["note"] = result.get("reason", status)
        else:
            raise WorkflowError(f"cannot transition unverified result: {status}")
        statuses = [self._stage(name).get("status") for name in STAGE_ORDER]
        if all(item == "complete" for item in statuses):
            self.job["status"] = "complete"
            self.job["next_action"] = "none"
        elif status == "needs_user":
            self.job["status"] = "needs_user"
            self.job["next_action"] = result.get("reason", "user action required")
        elif status in {"blocked", "unavailable"}:
            self.job["status"] = "blocked"
            self.job["next_action"] = result.get("reason", "workflow recovery required")
        else:
            self.job["status"] = "active"
            self.job["next_action"] = f"continue {stage_name} workflow"
        return deepcopy(self.job)

    def record_approval(self, stage: str, approval: Mapping[str, Any]) -> dict[str, Any]:
        """Record a user-owned approval and reopen only that stage."""

        if stage not in STAGE_ORDER:
            raise WorkflowError(f"unknown stage: {stage}")
        if not isinstance(approval, Mapping) or approval.get("status") != "approved":
            raise WorkflowError("approval must explicitly have status approved")
        stage_data = self._stage(stage)
        stage_data["approval"] = dict(approval)
        if stage_data.get("status") == "needs_user":
            stage_data["status"] = "pending"
        self.job["status"] = "active"
        self.job["next_action"] = f"resume {stage}"
        return deepcopy(self.job)

    def run_next(self) -> dict[str, Any]:
        """Execute one stage boundary and return its verified transition result."""

        execution = self.execute()
        if execution.get("status") == "complete":
            execution = self.verify(execution)
        if execution.get("status") in {"verified", "needs_user", "blocked", "unavailable"}:
            snapshot = self.transition(execution)
            return {"result": execution, "job": snapshot}
        return {"result": execution, "job": deepcopy(self.job)}

    def run_until_boundary(self, *, max_steps: int = len(STAGE_ORDER)) -> dict[str, Any]:
        """Continue only while local gates are ready; stop at user/external boundaries."""

        history: list[dict[str, Any]] = []
        for _ in range(max_steps):
            step = self.next_step()
            if step["status"] in {"complete", "needs_user", "blocked"}:
                return {"status": step["status"], "history": history, "job": deepcopy(self.job), "step": step}
            result = self.run_next()
            history.append(result)
            if result["result"].get("status") in {"needs_user", "blocked", "unavailable"}:
                return {
                    "status": result["result"]["status"],
                    "history": history,
                    "job": result["job"],
                    "step": result["result"],
                }
        return {
            "status": "blocked",
            "history": history,
            "job": deepcopy(self.job),
            "step": {"status": "blocked", "reason": "max_steps exceeded"},
        }
