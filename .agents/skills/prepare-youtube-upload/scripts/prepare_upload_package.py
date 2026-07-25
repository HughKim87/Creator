#!/usr/bin/env python3
"""Validate a manual YouTube upload package and render its copy-ready guide."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required to validate the thumbnail.") from exc


ALLOWED_VISIBILITY = {"private", "unlisted", "public", "scheduled"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--guide", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate without writing the Markdown guide.",
    )
    return parser.parse_args()


def require_mapping(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def require_text(
    value: Any, name: str, errors: list[str], *, maximum: int | None = None
) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{name} must be non-empty text")
        return ""
    if maximum is not None and len(value) > maximum:
        errors.append(f"{name} exceeds {maximum} characters")
    return value


def resolve_artifact(
    base: Path, value: Any, name: str, errors: list[str]
) -> Path | None:
    text = require_text(value, name, errors)
    if not text:
        return None
    candidate = (base / text).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        errors.append(f"{name} escapes the package directory")
        return None
    if not candidate.is_file():
        errors.append(f"{name} not found: {candidate}")
        return None
    if candidate.stat().st_size == 0:
        errors.append(f"{name} is empty: {candidate}")
        return None
    return candidate


def validate_srt(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8-sig")
    if " --> " not in text:
        errors.append("captions do not contain an SRT timing line")
    if not text.strip().startswith("1"):
        errors.append("captions must start with cue 1")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bool_ko(value: bool) -> str:
    return "예" if value else "아니요"


def render_guide(
    package_path: Path,
    data: dict[str, Any],
    resolved: dict[str, Path],
    keep_files: list[Path],
    hashes: dict[str, str],
    warning: str | None,
) -> str:
    channel = data["channel"]
    metadata = data["metadata"]
    script_path = Path(__file__).resolve()
    lines = [
        "# YouTube 수동 업로드 패키지",
        "",
        f"- 원본 데이터: `{package_path}`",
        f"- 재생성: `python \"{script_path}\" \"{package_path}\"`",
        "- 상태: 수동 업로드 준비 완료",
        "- 경계: 이 문서는 YouTube를 조작하지 않으며 업로드는 사용자가 직접 수행한다.",
        "",
    ]
    if warning:
        lines.extend(
            [
                "## 중복 업로드 경고",
                "",
                f"> {warning}",
                "",
            ]
        )
    lines.extend(
        [
            "## 선택할 파일",
            "",
            f"- 영상: `{resolved['video']}`",
            f"- 썸네일: `{resolved['thumbnail']}`",
            f"- 한국어 SRT: `{resolved['captions']}`",
            "",
            "## 복사할 제목",
            "",
            "```text",
            metadata["title"],
            "```",
            "",
            "## 복사할 설명",
            "",
            "```text",
            metadata["description"],
            "```",
            "",
            "## 설정",
            "",
            f"- 채널: {channel['name']} (`{channel['id']}`)",
            f"- 재생목록: {metadata.get('playlist') or '지정 없음'}",
            f"- 카테고리: {metadata['category']}",
            f"- 동영상 언어: {metadata['language']}",
            f"- 자막 언어: {metadata['caption_language']}",
            f"- 아동용: {bool_ko(metadata['made_for_kids'])}",
            f"- 공개 상태 권장값: {metadata['visibility_recommendation']}",
            "",
            "## 함께 보존할 업로드 정보",
            "",
        ]
    )
    for path in keep_files:
        lines.append(f"- `{path.name}`: `{path}`")
    lines.extend(
        [
            "",
            "## 수동 업로드 순서",
            "",
            "1. YouTube Studio에서 올바른 채널인지 확인한다.",
            "2. 영상 파일을 한 번만 선택하고 제목과 설명을 붙여넣는다.",
            "3. 준비된 썸네일을 선택하고 재생목록·카테고리·아동용 여부를 설정한다.",
            "4. 한국어·타이밍 포함 방식으로 SRT 파일을 추가한다.",
            "5. 저작권 검사를 확인하고 원하는 공개 상태를 직접 선택한다.",
            "6. 저장 후 콘텐츠 목록에서 제목·썸네일·자막·공개 상태를 확인한다.",
            "",
            "## 파일 검증값",
            "",
        ]
    )
    for key, label in (
        ("video", "영상"),
        ("thumbnail", "썸네일"),
        ("captions", "SRT"),
    ):
        path = resolved[key]
        lines.append(
            f"- {label}: {path.stat().st_size:,} bytes · SHA-256 `{hashes[key]}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    package_path = args.package.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not package_path.is_file():
        raise SystemExit(f"Package not found: {package_path}")
    try:
        data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read package: {exc}") from exc

    if data.get("schema_version") != "youtube-manual-upload-v1":
        errors.append("schema_version must be youtube-manual-upload-v1")

    channel = require_mapping(data.get("channel"), "channel", errors)
    artifacts = require_mapping(data.get("artifacts"), "artifacts", errors)
    metadata = require_mapping(data.get("metadata"), "metadata", errors)
    preparation = require_mapping(data.get("preparation"), "preparation", errors)

    require_text(channel.get("name"), "channel.name", errors)
    channel_id = require_text(channel.get("id"), "channel.id", errors)
    if channel_id and not channel_id.startswith("UC"):
        errors.append("channel.id must start with UC")

    base = package_path.parent.resolve()
    resolved: dict[str, Path] = {}
    for key in ("video", "thumbnail", "captions", "title_thumbnail_package"):
        path = resolve_artifact(
            base, artifacts.get(key), f"artifacts.{key}", errors
        )
        if path:
            resolved[key] = path

    video = resolved.get("video")
    thumbnail = resolved.get("thumbnail")
    captions = resolved.get("captions")
    title_package = resolved.get("title_thumbnail_package")

    if video and video.suffix.lower() != ".mp4":
        errors.append("artifacts.video must be an MP4 file")
    if captions:
        if captions.suffix.lower() != ".srt":
            errors.append("artifacts.captions must be an SRT file")
        else:
            validate_srt(captions, errors)
    if thumbnail:
        if thumbnail.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            errors.append("thumbnail must be JPEG or PNG")
        if thumbnail.stat().st_size > 2 * 1024 * 1024:
            errors.append("thumbnail exceeds YouTube's 2 MB limit")
        try:
            with Image.open(thumbnail) as image:
                image.verify()
            with Image.open(thumbnail) as image:
                if image.size != (1280, 720):
                    errors.append(
                        f"thumbnail must be 1280x720, got {image.size[0]}x{image.size[1]}"
                    )
        except OSError as exc:
            errors.append(f"thumbnail is unreadable: {exc}")

    title = require_text(metadata.get("title"), "metadata.title", errors, maximum=100)
    description = metadata.get("description")
    if not isinstance(description, str):
        errors.append("metadata.description must be text")
    elif len(description) > 5000:
        errors.append("metadata.description exceeds 5000 characters")
    require_text(metadata.get("language"), "metadata.language", errors)
    require_text(
        metadata.get("caption_language"), "metadata.caption_language", errors
    )
    require_text(metadata.get("category"), "metadata.category", errors)
    if not isinstance(metadata.get("made_for_kids"), bool):
        errors.append("metadata.made_for_kids must be true or false")
    visibility = metadata.get("visibility_recommendation")
    if visibility not in ALLOWED_VISIBILITY:
        errors.append(
            f"metadata.visibility_recommendation must be one of {sorted(ALLOWED_VISIBILITY)}"
        )

    if preparation.get("status") != "ready":
        errors.append("preparation.status must be ready")
    if preparation.get("youtube_actions") != "manual_by_user":
        errors.append("preparation.youtube_actions must be manual_by_user")

    keep_files: list[Path] = []
    raw_keep_files = preparation.get("keep_files", [])
    if not isinstance(raw_keep_files, list):
        errors.append("preparation.keep_files must be a list")
    else:
        for index, value in enumerate(raw_keep_files):
            path = resolve_artifact(
                base,
                value,
                f"preparation.keep_files[{index}]",
                errors,
            )
            if path:
                keep_files.append(path)

    if "approval" in data:
        errors.append("manual packages must not contain external-action approvals")
    if "chrome_profile" in channel:
        errors.append("manual packages must not contain a Chrome profile")

    if title_package:
        try:
            approved = json.loads(title_package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"title-thumbnail package is unreadable: {exc}")
        else:
            selected = approved.get("title", {}).get("selected")
            approved_thumbnail = approved.get("thumbnail", {}).get("upload")
            user_approved = approved.get("validation", {}).get("user_approved")
            if title and selected != title:
                errors.append("manual title differs from the approved package")
            if thumbnail and approved_thumbnail != thumbnail.name:
                errors.append("manual thumbnail differs from the approved package")
            if user_approved is not True:
                errors.append("title-thumbnail package is not user-approved")

    duplicate_warning: str | None = None
    existing = data.get("existing_upload")
    if existing is not None:
        existing = require_mapping(existing, "existing_upload", errors)
        video_id = require_text(
            existing.get("video_id"), "existing_upload.video_id", errors
        )
        existing_visibility = require_text(
            existing.get("visibility"), "existing_upload.visibility", errors
        )
        note = require_text(
            existing.get("note"), "existing_upload.note", errors
        )
        if video_id and existing_visibility and note:
            duplicate_warning = (
                f"이 영상은 이미 {existing_visibility} 상태로 업로드되어 있습니다 "
                f"(video ID: {video_id}). {note}"
            )
            warnings.append("existing upload recorded; do not create a duplicate")

    hashes: dict[str, str] = {}
    if not errors:
        hashes = {
            key: sha256(resolved[key])
            for key in ("video", "thumbnail", "captions")
        }

    guide_path = (
        args.guide.resolve()
        if args.guide
        else package_path.with_name("YOUTUBE-MANUAL-UPLOAD.md")
    )
    if not errors and not args.check:
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        guide_path.write_text(
            render_guide(
                package_path,
                data,
                resolved,
                keep_files,
                hashes,
                duplicate_warning,
            ),
            encoding="utf-8",
            newline="\n",
        )

    output = {
        "status": "ready" if not errors else "invalid",
        "package": str(package_path),
        "guide": str(guide_path) if not args.check else None,
        "artifacts": {key: str(value) for key, value in resolved.items()},
        "hashes": hashes,
        "errors": errors,
        "warnings": warnings,
        "external_actions": "none",
        "retention": {
            "keep_files": [str(path) for path in keep_files],
            "guide": str(guide_path),
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
