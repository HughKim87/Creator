#!/usr/bin/env python3
"""Validate a YouTube title and thumbnail runtime package."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it only after user approval."
    ) from exc


SCHEMA_VERSIONS = {
    "youtube-title-thumbnail-v1",
    "youtube-title-thumbnail-v2",
    "youtube-title-thumbnail-v3",
}
GENERATION_MODES = {"one_shot_imagegen", "local_text_composite"}
APPROVAL_METHODS = {"explicit_user", "delegated_by_user"}
APPROVAL_POLICY_MODES = {"review_gated", "delegated_by_user"}
INSTRUCTION_SOURCES = {"explicit_user", "default"}
LOCAL_COMPOSITE_REASONS = {
    "explicit_user_request",
    "repeated_text_errors",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate title, copy approvals, and thumbnail package fields."
    )
    parser.add_argument("package", type=Path)
    parser.add_argument(
        "--require-approved",
        action="store_true",
        help="Fail unless title, copy, image generation, and final visual are approved.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise ValueError("Package contains a NUL byte")
    text = raw.decode("utf-8", errors="strict")
    if "\ufffd" in text:
        raise ValueError("Package contains U+FFFD")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Package root must be an object")
    return value


def find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (
            (candidate / "PROJECT_RULES.md").is_file()
            and (candidate / "extension").is_dir()
        ):
            return candidate.resolve()
    raise ValueError("Cannot locate project root from package path")


def resolve_path(
    base: Path,
    project_root: Path,
    value: Any,
    field: str,
) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty path")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"{field} escapes the project root") from exc
    if not candidate.is_file() or candidate.stat().st_size == 0:
        raise ValueError(f"{field} not found or empty: {candidate}")
    return candidate


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    return value


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def parse_timestamp(value: Any, field: str) -> datetime:
    text = require_text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be valid ISO 8601 text") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def validate_v3_contract(
    data: dict[str, Any],
    errors: list[str],
) -> tuple[str | None, bool, str | None]:
    required_mode: str | None = None
    allow_local = False
    approval_mode: str | None = None
    try:
        generation = require_object(
            data.get("generation_contract"), "generation_contract"
        )
        required_mode = generation.get("required_mode")
        if required_mode not in GENERATION_MODES:
            errors.append(
                "generation_contract.required_mode must be "
                "one_shot_imagegen or local_text_composite"
            )
        allow_value = generation.get("allow_local_text_composite")
        if not isinstance(allow_value, bool):
            errors.append(
                "generation_contract.allow_local_text_composite "
                "must be true or false"
            )
        else:
            allow_local = allow_value
        generation_source = generation.get("instruction_source")
        if generation_source not in INSTRUCTION_SOURCES:
            errors.append(
                "generation_contract.instruction_source must be "
                "explicit_user or default"
            )
        if required_mode == "local_text_composite" and not allow_local:
            errors.append(
                "local_text_composite required mode must allow local composite"
            )
        if allow_local and generation_source != "explicit_user":
            errors.append(
                "local text composite permission requires explicit_user instruction"
            )

        policy = require_object(data.get("approval_policy"), "approval_policy")
        approval_mode = policy.get("mode")
        if approval_mode not in APPROVAL_POLICY_MODES:
            errors.append(
                "approval_policy.mode must be review_gated "
                "or delegated_by_user"
            )
        policy_source = policy.get("instruction_source")
        if policy_source not in INSTRUCTION_SOURCES:
            errors.append(
                "approval_policy.instruction_source must be "
                "explicit_user or default"
            )
        if (
            approval_mode == "delegated_by_user"
            and policy_source != "explicit_user"
        ):
            errors.append(
                "delegated approval policy requires explicit_user instruction"
            )
    except ValueError as exc:
        errors.append(str(exc))
    return required_mode, allow_local, approval_mode


def validate_title(
    data: dict[str, Any],
    errors: list[str],
    *,
    require_approved: bool,
    approval_mode: str | None = None,
) -> tuple[str, int | None, bool]:
    selected = ""
    title_length: int | None = None
    title_approved = False
    try:
        title = require_object(data.get("title"), "title")
        selected = require_text(title.get("selected"), "title.selected")
        if "\n" in selected or "\r" in selected:
            errors.append("title.selected must be one line")
        title_length = len(selected)
        if not 40 <= title_length <= 65:
            errors.append(
                f"title.selected length must be 40-65, got {title_length}"
            )
        candidates = require_list(title.get("candidates"), "title.candidates")
        candidate_texts: list[str] = []
        if len(candidates) < 5:
            errors.append("title.candidates must contain at least 5 items")
        for index, item in enumerate(candidates, start=1):
            if not isinstance(item, dict):
                errors.append(f"title.candidates[{index}] must be an object")
                continue
            try:
                candidate_text = require_text(
                    item.get("text"), f"title.candidates[{index}].text"
                )
                require_text(
                    item.get("angle"), f"title.candidates[{index}].angle"
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue
            candidate_texts.append(candidate_text)
            if not 40 <= len(candidate_text) <= 65:
                errors.append(
                    f"title.candidates[{index}].text length must be 40-65, "
                    f"got {len(candidate_text)}"
                )
        if selected not in candidate_texts:
            errors.append("title.selected must appear in title.candidates")
        status = title.get("status")
        if status not in {"draft", "approved"}:
            errors.append("title.status must be draft or approved")
        title_approved = status == "approved"
        if title_approved and approval_mode is not None:
            method = title.get("approval_method")
            if method not in APPROVAL_METHODS:
                errors.append(
                    "title.approval_method must be explicit_user "
                    "or delegated_by_user"
                )
            elif approval_mode == "review_gated" and method != "explicit_user":
                errors.append(
                    "review_gated title approval must use explicit_user"
                )
        if require_approved and not title_approved:
            errors.append("title.status must be approved")
    except ValueError as exc:
        errors.append(str(exc))
    return selected, title_length, title_approved


def validate_approval(
    data: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    generated_at: datetime | None,
    *,
    require_approved: bool,
    approval_mode: str | None = None,
) -> bool:
    try:
        approval = require_object(data.get("approval"), "approval")
    except ValueError as exc:
        errors.append(str(exc))
        return False

    parsed: dict[str, datetime] = {}
    all_approved = True
    for name in ("copy", "image_generation", "visual"):
        try:
            item = require_object(approval.get(name), f"approval.{name}")
            status = item.get("status")
            if status not in {"pending", "approved"}:
                errors.append(
                    f"approval.{name}.status must be pending or approved"
                )
                all_approved = False
                continue
            if status != "approved":
                all_approved = False
                message = f"approval.{name} is not approved"
                if require_approved:
                    errors.append(message)
                else:
                    warnings.append(message)
                continue
            method = item.get("method")
            if method not in APPROVAL_METHODS:
                errors.append(
                    f"approval.{name}.method must be one of "
                    f"{sorted(APPROVAL_METHODS)}"
                )
                all_approved = False
            elif (
                approval_mode == "review_gated"
                and method != "explicit_user"
            ):
                errors.append(
                    f"approval.{name}.method must be explicit_user "
                    "for review_gated policy"
                )
                all_approved = False
            parsed[name] = parse_timestamp(
                item.get("approved_at"), f"approval.{name}.approved_at"
            )
        except ValueError as exc:
            errors.append(str(exc))
            all_approved = False

    if generated_at and {"copy", "image_generation"} <= parsed.keys():
        if parsed["copy"] > generated_at:
            errors.append("copy approval must not be later than thumbnail.generated_at")
        if parsed["image_generation"] > generated_at:
            errors.append(
                "image generation approval must not be later than "
                "thumbnail.generated_at"
            )
    if generated_at and "visual" in parsed and parsed["visual"] < generated_at:
        errors.append("visual approval must not be earlier than thumbnail.generated_at")
    if {"copy", "image_generation"} <= parsed.keys():
        if parsed["copy"] > parsed["image_generation"]:
            errors.append(
                "copy approval must not be later than image generation approval"
            )
    return all_approved


def validate(package_path: Path, *, require_approved: bool = False) -> dict[str, Any]:
    data = read_json(package_path)
    errors: list[str] = []
    warnings: list[str] = []
    base = package_path.resolve().parent
    project_root = find_project_root(base)
    schema_version = data.get("schema_version")

    if schema_version not in SCHEMA_VERSIONS:
        errors.append(
            f"schema_version must be one of {sorted(SCHEMA_VERSIONS)}"
        )

    required_mode: str | None = None
    allow_local_composite = False
    approval_mode: str | None = None
    if schema_version == "youtube-title-thumbnail-v3":
        (
            required_mode,
            allow_local_composite,
            approval_mode,
        ) = validate_v3_contract(data, errors)

    video = captions = None
    try:
        source = require_object(data.get("source"), "source")
        video = resolve_path(
            base, project_root, source.get("video"), "source.video"
        )
        captions = resolve_path(
            base, project_root, source.get("captions"), "source.captions"
        )
        channel_evidence = require_object(
            source.get("channel_evidence"), "source.channel_evidence"
        )
        if channel_evidence.get("status") not in {
            "verified",
            "unavailable",
            "not_provided",
        }:
            errors.append(
                "source.channel_evidence.status must be verified, "
                "unavailable, or not_provided"
            )
    except ValueError as exc:
        errors.append(str(exc))

    selected, title_length, title_approved = validate_title(
        data,
        errors,
        require_approved=require_approved,
        approval_mode=approval_mode,
    )

    upload = master = source_image = preview = None
    generation_mode = "legacy"
    generated_at: datetime | None = None
    authorization_at: datetime | None = None
    width = height = upload_bytes = None
    image_format = upload_sha256 = None
    try:
        thumbnail = require_object(data.get("thumbnail"), "thumbnail")
        upload = resolve_path(
            base, project_root, thumbnail.get("upload"), "thumbnail.upload"
        )
        master = resolve_path(
            base, project_root, thumbnail.get("master"), "thumbnail.master"
        )
        preview = resolve_path(
            base,
            project_root,
            thumbnail.get("mobile_preview"),
            "thumbnail.mobile_preview",
        )
        text_blocks = require_list(thumbnail.get("text"), "thumbnail.text")
        if not 2 <= len(text_blocks) <= 3:
            errors.append("thumbnail.text must contain 2 or 3 blocks")
        for index, block in enumerate(text_blocks, start=1):
            try:
                require_text(block, f"thumbnail.text[{index}]")
            except ValueError as exc:
                errors.append(str(exc))
        require_text(
            thumbnail.get("generation_prompt"), "thumbnail.generation_prompt"
        )

        if schema_version in {
            "youtube-title-thumbnail-v2",
            "youtube-title-thumbnail-v3",
        }:
            generation_mode = thumbnail.get("generation_mode")
            if generation_mode not in GENERATION_MODES:
                errors.append(
                    "thumbnail.generation_mode must be one_shot_imagegen "
                    "or local_text_composite"
                )
            source_field = (
                "generated_source"
                if generation_mode == "one_shot_imagegen"
                else "background"
            )
            source_image = resolve_path(
                base,
                project_root,
                thumbnail.get(source_field),
                f"thumbnail.{source_field}",
            )
            if generation_mode == "local_text_composite":
                require_text(thumbnail.get("font"), "thumbnail.font")
                if schema_version == "youtube-title-thumbnail-v3":
                    if not allow_local_composite:
                        errors.append(
                            "generation contract forbids local_text_composite"
                        )
                    authorization = require_object(
                        thumbnail.get("local_composite_authorization"),
                        "thumbnail.local_composite_authorization",
                    )
                    reason = authorization.get("reason")
                    if reason not in LOCAL_COMPOSITE_REASONS:
                        errors.append(
                            "thumbnail.local_composite_authorization.reason "
                            "must be explicit_user_request or repeated_text_errors"
                        )
                    if authorization.get("approved_by") != "explicit_user":
                        errors.append(
                            "local composite authorization must be explicit_user"
                        )
                    authorization_at = parse_timestamp(
                        authorization.get("approved_at"),
                        "thumbnail.local_composite_authorization.approved_at",
                    )
                    if reason == "repeated_text_errors":
                        attempts = authorization.get("one_shot_attempts")
                        if (
                            isinstance(attempts, bool)
                            or not isinstance(attempts, int)
                            or attempts < 2
                        ):
                            errors.append(
                                "repeated_text_errors requires "
                                "one_shot_attempts of at least 2"
                            )
                    image_approval = (
                        data.get("approval", {}).get("image_generation", {})
                        if isinstance(data.get("approval"), dict)
                        else {}
                    )
                    if (
                        not isinstance(image_approval, dict)
                        or image_approval.get("status") != "approved"
                        or image_approval.get("method") != "explicit_user"
                    ):
                        errors.append(
                            "local_text_composite requires explicit_user "
                            "image generation approval"
                        )
            strategy = require_object(
                thumbnail.get("copy_strategy"), "thumbnail.copy_strategy"
            )
            for key in ("hook", "payoff", "scope"):
                require_text(
                    strategy.get(key), f"thumbnail.copy_strategy.{key}"
                )
            generated_at = parse_timestamp(
                thumbnail.get("generated_at"), "thumbnail.generated_at"
            )
            if (
                generation_mode == "local_text_composite"
                and schema_version == "youtube-title-thumbnail-v3"
                and authorization_at is not None
                and authorization_at > generated_at
            ):
                errors.append(
                    "local composite authorization must not be later than "
                    "thumbnail.generated_at"
                )
            if (
                schema_version == "youtube-title-thumbnail-v3"
                and required_mode == "one_shot_imagegen"
                and generation_mode != "one_shot_imagegen"
                and not allow_local_composite
            ):
                errors.append(
                    "thumbnail.generation_mode differs from required one-shot mode"
                )
            if (
                schema_version == "youtube-title-thumbnail-v3"
                and required_mode == "local_text_composite"
                and generation_mode != "local_text_composite"
            ):
                errors.append(
                    "thumbnail.generation_mode differs from required local mode"
                )
        else:
            source_image = resolve_path(
                base,
                project_root,
                thumbnail.get("background"),
                "thumbnail.background",
            )

        with Image.open(upload) as image:
            width, height = image.size
            image_format = image.format
            if width < 1280 or height < 720:
                errors.append(
                    f"thumbnail must be at least 1280x720, got {width}x{height}"
                )
            if abs(width / height - 16 / 9) > 0.001:
                errors.append(
                    f"thumbnail must be 16:9, got {width}x{height}"
                )
            if image_format not in {"JPEG", "PNG"}:
                errors.append(
                    f"thumbnail format must be JPEG or PNG, got {image_format}"
                )
        upload_bytes = upload.stat().st_size
        upload_sha256 = hashlib.sha256(upload.read_bytes()).hexdigest()
    except ValueError as exc:
        errors.append(str(exc))

    validation = data.get("validation")
    if not isinstance(validation, dict):
        errors.append("validation must be an object")
        validation = {}
    required_flags = ["facts_traceable", "mobile_preview_reviewed"]
    if schema_version in {
        "youtube-title-thumbnail-v2",
        "youtube-title-thumbnail-v3",
    }:
        required_flags.extend(
            [
                "text_exact",
                "clickability_reviewed",
                "title_thumbnail_not_duplicate",
            ]
        )
    for field in required_flags:
        if validation.get(field) is not True:
            errors.append(f"validation.{field} must be true")

    if schema_version in {
        "youtube-title-thumbnail-v2",
        "youtube-title-thumbnail-v3",
    }:
        approval_ready = validate_approval(
            data,
            errors,
            warnings,
            generated_at,
            require_approved=require_approved,
            approval_mode=approval_mode,
        )
    else:
        approval_ready = validation.get("user_approved") is True
        if not approval_ready:
            message = "Title and thumbnail are not yet user-approved"
            if require_approved:
                errors.append(message)
            else:
                warnings.append(message)
        if require_approved and not title_approved:
            errors.append("title.status must be approved")

    return {
        "status": "valid" if not errors else "invalid",
        "schema_version": schema_version,
        "package": str(package_path.resolve()),
        "selected_title": selected,
        "title_length": title_length,
        "video": str(video) if video else None,
        "captions": str(captions) if captions else None,
        "thumbnail": str(upload) if upload else None,
        "thumbnail_size": [width, height] if width and height else None,
        "thumbnail_format": image_format,
        "thumbnail_bytes": upload_bytes,
        "thumbnail_sha256": upload_sha256,
        "generation_mode": generation_mode,
        "master": str(master) if master else None,
        "source_image": str(source_image) if source_image else None,
        "mobile_preview": str(preview) if preview else None,
        "approval_ready": approval_ready and title_approved,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    try:
        result = validate(
            args.package, require_approved=args.require_approved
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "status": "invalid",
            "package": str(args.package.resolve()),
            "errors": [str(exc)],
            "warnings": [],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
