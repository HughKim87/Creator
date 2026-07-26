#!/usr/bin/env python3
"""Validate video job structure, worktree context, approvals, and artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_worktree import inspect_worktree


SCHEMA_VERSIONS = {"video-job-v1", "video-job-v2"}
STAGE_ORDER = (
    "research",
    "video",
    "captions",
    "title_thumbnail",
    "upload_package",
)
EXPECTED_SKILLS = {
    "research": "notebooklm-research-topic",
    "video": "notebooklm-generate-video",
    "captions": "video-to-srt",
    "title_thumbnail": "youtube-title-thumbnail",
    "upload_package": "prepare-youtube-upload",
}
JOB_STATUSES = {"active", "needs_user", "blocked", "complete"}
STAGE_STATUSES = {"pending", "in_progress", "needs_user", "blocked", "complete"}
ACTIVE_STAGE_STATUSES = {"in_progress", "needs_user", "blocked"}
EXECUTION_MODES = {"autonomous_local_pipeline", "review_gated"}
CONNECTION_METHODS = {
    "same_runtime",
    "explicit_tab_mention",
    "profile_targeted_launch",
}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse_timestamp(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not nonempty_text(value):
        errors.append(f"{field} must be non-empty ISO 8601 text")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must be valid ISO 8601 text")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed


def is_notebooklm_url(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.netloc == "notebooklm.google.com"
    )


def resolve_artifact(root: Path, value: str, errors: list[str]) -> Path | None:
    if is_notebooklm_url(value):
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"artifact escapes project root: {value}")
        return None
    if not candidate.is_file() or candidate.stat().st_size == 0:
        errors.append(f"artifact not found or empty: {candidate}")
        return None
    return candidate


def validate_title_package(path: Path, errors: list[str]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read title-thumbnail package: {exc}")
        return
    schema = data.get("schema_version")
    if data.get("title", {}).get("status") != "approved":
        errors.append("title-thumbnail title is not approved")
    if schema == "youtube-title-thumbnail-v2":
        approval = data.get("approval")
        if not isinstance(approval, dict):
            errors.append("title-thumbnail approval object is missing")
            return
        for name in ("copy", "image_generation", "visual"):
            item = approval.get(name)
            if not isinstance(item, dict) or item.get("status") != "approved":
                errors.append(f"title-thumbnail approval.{name} is not approved")
    elif schema == "youtube-title-thumbnail-v1":
        if data.get("validation", {}).get("user_approved") is not True:
            errors.append("title-thumbnail package is not user-approved")
    else:
        errors.append("unsupported title-thumbnail package schema")


def validate_manual_package(
    path: Path,
    project_root: Path,
    errors: list[str],
) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read manual upload package: {exc}")
        return
    preparation = data.get("preparation")
    if not isinstance(preparation, dict):
        errors.append("manual upload preparation object is missing")
        return
    if preparation.get("status") != "ready":
        errors.append("manual upload package is not ready")
    if preparation.get("youtube_actions") != "manual_by_user":
        errors.append("manual upload package must remain manual_by_user")
    if data.get("schema_version") != "youtube-manual-upload-v2":
        return

    base = path.parent
    output_value = preparation.get("output_dir")
    final_values = preparation.get("final_output_files")
    if not nonempty_text(output_value):
        errors.append("manual upload output_dir is missing")
        return
    output_dir = (base / output_value).resolve()
    try:
        output_dir.relative_to(project_root)
    except ValueError:
        errors.append("manual upload output_dir escapes project root")
        return
    if not output_dir.is_dir():
        errors.append(f"manual upload output_dir not found: {output_dir}")
        return
    if (
        not isinstance(final_values, list)
        or len(final_values) != 4
        or any(
            not isinstance(item, str) or Path(item).name != item
            for item in final_values
        )
    ):
        errors.append("manual upload final_output_files must contain 4 filenames")
        return
    actual_files = {
        item.name
        for item in output_dir.iterdir()
        if item.is_file() and not item.is_symlink()
    }
    actual_directories = [
        item.name
        for item in output_dir.iterdir()
        if item.is_dir() or item.is_symlink()
    ]
    if actual_files != set(final_values):
        errors.append(
            "final output files do not match manual package contract: "
            f"expected {sorted(final_values)}, got {sorted(actual_files)}"
        )
    if actual_directories:
        errors.append(
            f"final output contains directories or symlinks: {actual_directories}"
        )


def validate_video_job(
    data: Any,
    *,
    root: Path | None = None,
    check_artifacts: bool = False,
    worktree_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return {"status": "invalid", "errors": ["job must be an object"]}

    schema_version = data.get("schema_version")
    if schema_version not in SCHEMA_VERSIONS:
        errors.append(
            f"schema_version must be one of {sorted(SCHEMA_VERSIONS)}"
        )
    if not nonempty_text(data.get("job_id")):
        errors.append("job_id must be non-empty text")
    if not nonempty_text(data.get("topic")):
        errors.append("topic must be non-empty text")

    job_status = data.get("status")
    if job_status not in JOB_STATUSES:
        errors.append(f"job status must be one of {sorted(JOB_STATUSES)}")

    execution_mode_present = "execution_mode" in data
    execution_mode = data.get("execution_mode", "review_gated")
    if execution_mode_present and execution_mode not in EXECUTION_MODES:
        errors.append(
            f"execution_mode must be one of {sorted(EXECUTION_MODES)}"
        )

    stages = data.get("stages")
    if not isinstance(stages, dict):
        errors.append("stages must be an object")
        stages = {}
    expected = set(STAGE_ORDER)
    actual = set(stages)
    if expected - actual:
        errors.append(f"missing stages: {sorted(expected - actual)}")
    if actual - expected:
        errors.append(f"unexpected stages: {sorted(actual - expected)}")

    active_stages: list[tuple[str, str]] = []
    previous_complete = True
    statuses: dict[str, str | None] = {}
    local_artifacts: dict[str, list[Path]] = {}
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
        if stage.get("skill") != EXPECTED_SKILLS[name]:
            errors.append(
                f"stages.{name}.skill must be {EXPECTED_SKILLS[name]}"
            )
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
                artifacts = []
            if not nonempty_text(stage.get("validation")):
                errors.append(
                    f"stages.{name}.validation is required when status is complete"
                )
            if name == "video" and execution_mode_present:
                playback = stage.get("playback_check")
                if not isinstance(playback, dict):
                    errors.append(
                        "stages.video.playback_check must be an object when video is complete"
                    )
                else:
                    elapsed = playback.get("elapsed_seconds")
                    if (
                        isinstance(elapsed, bool)
                        or not isinstance(elapsed, (int, float))
                        or not 0 < float(elapsed) <= 30
                    ):
                        errors.append(
                            "stages.video.playback_check.elapsed_seconds must be greater than 0 and at most 30"
                        )
                    if playback.get("progressed") is not True:
                        errors.append(
                            "stages.video.playback_check.progressed must be true"
                        )
                    if playback.get("paused") is not True:
                        errors.append(
                            "stages.video.playback_check.paused must be true"
                        )
            if check_artifacts:
                if root is None:
                    errors.append("--check-artifacts requires --root")
                else:
                    resolved: list[Path] = []
                    for item in artifacts:
                        local = resolve_artifact(root, item, errors)
                        if local is not None:
                            resolved.append(local)
                    local_artifacts[name] = resolved
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

    browser = data.get("browser")
    if not isinstance(browser, dict):
        errors.append("browser must be an object")
        browser = {}
    if browser.get("surface") != "chrome":
        errors.append("browser.surface must be chrome")
    for field in ("profile_label", "profile_directory", "required_origin"):
        if not nonempty_text(browser.get(field)):
            errors.append(f"browser.{field} must be non-empty text")
    notebook_started = statuses.get("research") != "pending" or statuses.get(
        "video"
    ) not in {None, "pending"}
    if notebook_started:
        if browser.get("status") != "connected":
            errors.append("NotebookLM stages require browser.status connected")
        if browser.get("verification_method") not in CONNECTION_METHODS:
            errors.append(
                "browser.verification_method must record a supported connection method"
            )
        parse_timestamp(
            browser.get("last_verified_at"),
            "browser.last_verified_at",
            errors,
        )

    paths = data.get("paths")
    if not isinstance(paths, dict):
        errors.append("paths must be an object")
    else:
        for field in ("work_dir", "input_dir", "output_dir"):
            value = paths.get(field)
            if not nonempty_text(value) or Path(value).is_absolute():
                errors.append(f"paths.{field} must be a repository-relative path")

    if schema_version == "video-job-v2":
        execution = data.get("execution_context")
        worktree = (
            execution.get("worktree")
            if isinstance(execution, dict)
            else None
        )
        if not isinstance(worktree, dict):
            errors.append("execution_context.worktree must be an object")
        else:
            if worktree.get("status") != "valid":
                errors.append("execution_context.worktree.status must be valid")
            parse_timestamp(
                worktree.get("checked_at"),
                "execution_context.worktree.checked_at",
                errors,
            )
            for field in ("root", "branch", "expected_branch"):
                if not nonempty_text(worktree.get(field)):
                    errors.append(
                        f"execution_context.worktree.{field} must be non-empty text"
                    )
            if worktree_result:
                if worktree_result.get("status") != "valid":
                    errors.extend(worktree_result.get("errors", []))
                for field in ("root", "branch", "expected_branch"):
                    if worktree.get(field) != worktree_result.get(field):
                        errors.append(
                            f"execution_context.worktree.{field} differs from "
                            "the current worktree check"
                        )

    if check_artifacts and root is not None:
        if statuses.get("research") == "complete":
            research_values = stages["research"].get("artifacts", [])
            if not any(is_notebooklm_url(item) for item in research_values):
                errors.append("research complete requires a NotebookLM URL")
        if statuses.get("video") == "complete" and not any(
            path.suffix.lower() == ".mp4"
            for path in local_artifacts.get("video", [])
        ):
            errors.append("video complete requires a local MP4 artifact")
        if statuses.get("captions") == "complete":
            caption_paths = local_artifacts.get("captions", [])
            if not any(path.suffix.lower() == ".srt" for path in caption_paths):
                errors.append("captions complete requires an SRT artifact")
            if not any(path.suffix.lower() == ".json" for path in caption_paths):
                errors.append("captions complete requires a JSON review artifact")
        if statuses.get("title_thumbnail") == "complete":
            package_paths = [
                path
                for path in local_artifacts.get("title_thumbnail", [])
                if path.name == "youtube-title-thumbnail.json"
            ]
            if not package_paths:
                errors.append(
                    "title_thumbnail complete requires youtube-title-thumbnail.json"
                )
            else:
                validate_title_package(package_paths[0], errors)
            if not any(
                path.suffix.lower() in {".jpg", ".jpeg", ".png"}
                for path in local_artifacts.get("title_thumbnail", [])
            ):
                errors.append("title_thumbnail complete requires an image artifact")
        if statuses.get("upload_package") == "complete":
            upload_paths = local_artifacts.get("upload_package", [])
            package_paths = [
                path
                for path in upload_paths
                if path.name == "youtube-manual-upload.json"
            ]
            if not package_paths:
                errors.append(
                    "upload_package complete requires youtube-manual-upload.json"
                )
            else:
                validate_manual_package(package_paths[0], root, errors)
            if not any(
                path.name == "YOUTUBE-MANUAL-UPLOAD.md"
                for path in upload_paths
            ):
                errors.append(
                    "upload_package complete requires YOUTUBE-MANUAL-UPLOAD.md"
                )

    next_action = data.get("next_action")
    if job_status == "complete":
        if next_action != "none":
            errors.append("complete jobs must set next_action to none")
    elif not nonempty_text(next_action):
        errors.append("next_action must be non-empty text")
    parse_timestamp(data.get("updated_at"), "updated_at", errors)

    return {
        "status": "valid" if not errors else "invalid",
        "schema_version": schema_version,
        "job_id": data.get("job_id"),
        "execution_mode": execution_mode,
        "stage_statuses": statuses,
        "worktree": worktree_result,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--expected-branch")
    parser.add_argument(
        "--check-artifacts",
        action="store_true",
        help="Verify completed-stage local artifacts and final output contract.",
    )
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
    root = args.root.resolve() if args.root else None
    worktree_result = (
        inspect_worktree(root, args.expected_branch) if root else None
    )
    result = validate_video_job(
        data,
        root=root,
        check_artifacts=args.check_artifacts,
        worktree_result=worktree_result,
    )
    result["job"] = str(job_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
