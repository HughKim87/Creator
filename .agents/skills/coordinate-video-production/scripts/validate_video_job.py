#!/usr/bin/env python3
"""Validate the minimal structure and stage ordering of VIDEO_JOB.json."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any


STAGE_ORDER = (
    "research",
    "video",
    "captions",
    "title_thumbnail",
    "upload_package",
)
JOB_STATUSES = {"active", "needs_user", "blocked", "complete"}
STAGE_STATUSES = {"pending", "in_progress", "needs_user", "blocked", "complete"}
ACTIVE_STAGE_STATUSES = {"in_progress", "needs_user", "blocked"}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_video_job(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return {"status": "invalid", "errors": ["job must be an object"]}

    if data.get("schema_version") != "video-job-v1":
        errors.append("schema_version must be video-job-v1")
    if not nonempty_text(data.get("job_id")):
        errors.append("job_id must be non-empty text")
    if not nonempty_text(data.get("topic")):
        errors.append("topic must be non-empty text")

    job_status = data.get("status")
    if job_status not in JOB_STATUSES:
        errors.append(f"job status must be one of {sorted(JOB_STATUSES)}")

    stages = data.get("stages")
    if not isinstance(stages, dict):
        errors.append("stages must be an object")
        stages = {}
    expected = set(STAGE_ORDER)
    actual = set(stages)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"missing stages: {missing}")
    if unexpected:
        errors.append(f"unexpected stages: {unexpected}")

    active_stages: list[tuple[str, str]] = []
    previous_complete = True
    statuses: dict[str, str | None] = {}
    for name in STAGE_ORDER:
        stage = stages.get(name)
        if not isinstance(stage, dict):
            if name in stages:
                errors.append(f"stages.{name} must be an object")
            previous_complete = False
            statuses[name] = None
            continue
        status = stage.get("status")
        statuses[name] = status if isinstance(status, str) else None
        if status not in STAGE_STATUSES:
            errors.append(
                f"stages.{name}.status must be one of {sorted(STAGE_STATUSES)}"
            )
        if status in ACTIVE_STAGE_STATUSES:
            active_stages.append((name, status))
        if not previous_complete and status != "pending":
            errors.append(
                f"stages.{name} must remain pending until every prior stage is complete"
            )
        if status == "complete":
            artifacts = stage.get("artifacts")
            if (
                not isinstance(artifacts, list)
                or not artifacts
                or any(not nonempty_text(item) for item in artifacts)
            ):
                errors.append(
                    f"stages.{name}.artifacts must contain verified artifact references"
                )
            if not nonempty_text(stage.get("validation")):
                errors.append(
                    f"stages.{name}.validation is required when status is complete"
                )
        previous_complete = previous_complete and status == "complete"

    if len(active_stages) > 1:
        errors.append(f"at most one active stage is allowed: {active_stages}")

    all_complete = all(statuses.get(name) == "complete" for name in STAGE_ORDER)
    if job_status == "complete" and not all_complete:
        errors.append("job status complete requires all five stages to be complete")
    if all_complete and job_status != "complete":
        errors.append("all five complete stages require job status complete")
    if job_status == "needs_user" and not any(
        status == "needs_user" for status in statuses.values()
    ):
        errors.append("job status needs_user requires one needs_user stage")
    if job_status == "blocked" and not any(
        status == "blocked" for status in statuses.values()
    ):
        errors.append("job status blocked requires one blocked stage")

    next_action = data.get("next_action")
    if job_status == "complete":
        if next_action != "none":
            errors.append("complete jobs must set next_action to none")
    elif not nonempty_text(next_action):
        errors.append("next_action must be non-empty text")
    updated_at = data.get("updated_at")
    if not nonempty_text(updated_at):
        errors.append("updated_at must be non-empty ISO 8601 text")
    else:
        try:
            parsed = datetime.fromisoformat(updated_at)
            if parsed.tzinfo is None:
                errors.append("updated_at must include a timezone")
        except ValueError:
            errors.append("updated_at must be valid ISO 8601 text")

    return {
        "status": "valid" if not errors else "invalid",
        "job_id": data.get("job_id"),
        "stage_statuses": statuses,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    job_path = args.job.resolve()
    if not job_path.is_file():
        raise SystemExit(f"Job not found: {job_path}")
    try:
        data = json.loads(job_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read job: {exc}") from exc
    result = validate_video_job(data)
    result["job"] = str(job_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
