#!/usr/bin/env python3
"""Validate a YouTube title and thumbnail runtime package."""

from __future__ import annotations

import argparse
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


SCHEMA_VERSION = "youtube-title-thumbnail-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate title, source, and thumbnail package fields."
    )
    parser.add_argument("package", type=Path)
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


def resolve_path(base: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty path")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    if not candidate.is_file():
        raise ValueError(f"{field} not found: {candidate}")
    return candidate.resolve()


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    return value


def validate(package_path: Path) -> dict[str, Any]:
    data = read_json(package_path)
    errors: list[str] = []
    warnings: list[str] = []
    base = package_path.resolve().parent

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    try:
        source = require_object(data.get("source"), "source")
        video = resolve_path(base, source.get("video"), "source.video")
        captions = resolve_path(
            base, source.get("captions"), "source.captions"
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
        video = captions = None

    try:
        title = require_object(data.get("title"), "title")
        selected = title.get("selected")
        if not isinstance(selected, str) or not selected.strip():
            raise ValueError("title.selected must be a non-empty string")
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
            candidate_text = item.get("text")
            if not isinstance(candidate_text, str) or not candidate_text.strip():
                errors.append(
                    f"title.candidates[{index}].text must be non-empty"
                )
                continue
            candidate_texts.append(candidate_text)
            if not 40 <= len(candidate_text) <= 65:
                errors.append(
                    f"title.candidates[{index}].text length must be 40-65, "
                    f"got {len(candidate_text)}"
                )
            if not isinstance(item.get("angle"), str) or not item["angle"]:
                errors.append(
                    f"title.candidates[{index}].angle must be non-empty"
                )
        if selected not in candidate_texts:
            errors.append("title.selected must appear in title.candidates")
        if title.get("status") not in {"draft", "approved"}:
            errors.append("title.status must be draft or approved")
    except ValueError as exc:
        errors.append(str(exc))
        selected = ""
        title_length = None

    try:
        thumbnail = require_object(data.get("thumbnail"), "thumbnail")
        upload = resolve_path(
            base, thumbnail.get("upload"), "thumbnail.upload"
        )
        master = resolve_path(
            base, thumbnail.get("master"), "thumbnail.master"
        )
        background = resolve_path(
            base, thumbnail.get("background"), "thumbnail.background"
        )
        preview = resolve_path(
            base, thumbnail.get("mobile_preview"), "thumbnail.mobile_preview"
        )
        text_blocks = require_list(thumbnail.get("text"), "thumbnail.text")
        if not 2 <= len(text_blocks) <= 3:
            errors.append("thumbnail.text must contain 2 or 3 blocks")
        for index, block in enumerate(text_blocks, start=1):
            if not isinstance(block, str) or not block.strip():
                errors.append(
                    f"thumbnail.text[{index}] must be a non-empty string"
                )
        if not isinstance(
            thumbnail.get("generation_prompt"), str
        ) or not thumbnail["generation_prompt"].strip():
            errors.append("thumbnail.generation_prompt must be non-empty")
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
        upload = master = background = preview = None
        width = height = upload_bytes = None
        image_format = upload_sha256 = None

    validation = data.get("validation")
    if not isinstance(validation, dict):
        errors.append("validation must be an object")
        validation = {}
    if validation.get("facts_traceable") is not True:
        errors.append("validation.facts_traceable must be true")
    if validation.get("mobile_preview_reviewed") is not True:
        errors.append("validation.mobile_preview_reviewed must be true")
    if validation.get("user_approved") is not True:
        warnings.append("Title and thumbnail are not yet user-approved")

    return {
        "status": "valid" if not errors else "invalid",
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
        "master": str(master) if master else None,
        "background": str(background) if background else None,
        "mobile_preview": str(preview) if preview else None,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    args = parse_args()
    try:
        result = validate(args.package)
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
