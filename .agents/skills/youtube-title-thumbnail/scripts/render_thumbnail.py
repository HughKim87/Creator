#!/usr/bin/env python3
"""Render exact thumbnail text over a generated background."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it only after user approval."
    ) from exc


DEFAULT_FONTS = (
    Path(r"C:\Windows\Fonts\malgunbd.ttf"),
    Path(r"C:\Windows\Fonts\malgun.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a 1280x720 thumbnail with exact local text."
    )
    parser.add_argument("background", type=Path)
    parser.add_argument("--output-png", required=True, type=Path)
    parser.add_argument("--output-jpg", required=True, type=Path)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--line-1", required=True)
    parser.add_argument("--line-2", required=True)
    parser.add_argument("--line-3", required=True)
    parser.add_argument("--badge", default="")
    parser.add_argument("--font", type=Path)
    parser.add_argument(
        "--text-max-width",
        type=int,
        default=600,
        help="Maximum width for each text block inside the left safe area.",
    )
    parser.add_argument(
        "--text-min-size",
        type=int,
        default=48,
        help="Smallest font size allowed when fitting a text block.",
    )
    parser.add_argument("--accent-color", default="#FFCD4A")
    parser.add_argument("--underline-color", default="#00C9FF")
    parser.add_argument("--glow-color", default="#00B0FF")
    parser.add_argument("--badge-outline-color", default="#39D5FF")
    parser.add_argument("--jpeg-quality", type=int, default=92)
    return parser.parse_args()


def find_font(explicit: Path | None) -> Path:
    candidates: Iterable[Path] = (explicit,) if explicit else DEFAULT_FONTS
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise SystemExit("No usable font found. Pass --font <font.ttf>.")


def fit_font(text: str, font_path: Path, initial_size: int, max_width: int, min_size: int) -> ImageFont.FreeTypeFont:
    if not text.strip():
        raise SystemExit("Text blocks must not be empty.")
    if max_width < 1 or min_size < 1 or min_size > initial_size:
        raise SystemExit("Invalid text fitting bounds.")
    for size in range(initial_size, min_size - 1, -1):
        font = ImageFont.truetype(str(font_path), size)
        bbox = font.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return font
    raise SystemExit(
        f"Text does not fit within {max_width}px at the minimum font size: {text}"
    )


def parse_color(value: str) -> tuple[int, int, int, int]:
    normalized = value.removeprefix("#")
    if len(normalized) != 6:
        raise SystemExit(f"Expected #RRGGBB color, got: {value}")
    try:
        red, green, blue = (
            int(normalized[index : index + 2], 16) for index in (0, 2, 4)
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid color: {value}") from exc
    return red, green, blue, 255


def crop_to_ratio(image: Image.Image, ratio: float) -> Image.Image:
    current = image.width / image.height
    if current > ratio:
        width = round(image.height * ratio)
        left = (image.width - width) // 2
        return image.crop((left, 0, left + width, image.height))
    if current < ratio:
        height = round(image.width / ratio)
        top = (image.height - height) // 2
        return image.crop((0, top, image.width, top + height))
    return image


def add_left_gradient(image: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()
    for x in range(760):
        alpha = int(118 * max(0, 1 - x / 760))
        for y in range(720):
            pixels[x, y] = (0, 4, 18, alpha)
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def render(args: argparse.Namespace) -> dict[str, object]:
    if not args.background.is_file():
        raise SystemExit(f"Background not found: {args.background}")
    if not 1 <= args.jpeg_quality <= 100:
        raise SystemExit("--jpeg-quality must be between 1 and 100")
    if args.text_max_width < 300:
        raise SystemExit("--text-max-width must be at least 300px")

    font_path = find_font(args.font)
    accent = parse_color(args.accent_color)
    underline = parse_color(args.underline_color)
    glow_color = parse_color(args.glow_color)
    badge_outline = parse_color(args.badge_outline_color)

    with Image.open(args.background) as source:
        image = crop_to_ratio(source.convert("RGB"), 16 / 9)
        image = image.resize((1280, 720), Image.Resampling.LANCZOS)

    image = add_left_gradient(image)
    font_line_1 = fit_font(
        args.line_1, font_path, 92, args.text_max_width, args.text_min_size
    )
    font_line_2 = fit_font(
        args.line_2, font_path, 92, args.text_max_width, args.text_min_size
    )
    font_line_3 = fit_font(
        args.line_3, font_path, 108, args.text_max_width, args.text_min_size
    )
    font_badge = fit_font(
        args.badge, font_path, 34, args.text_max_width - 54, max(28, args.text_min_size - 14)
    ) if args.badge else ImageFont.truetype(str(font_path), 34)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.text(
        (62, 78),
        args.line_1,
        font=font_line_1,
        fill=(*glow_color[:3], 200),
        stroke_width=4,
        stroke_fill=(*glow_color[:3], 120),
    )
    image = Image.alpha_composite(
        image, glow.filter(ImageFilter.GaussianBlur(12))
    )
    draw = ImageDraw.Draw(image)
    dark_stroke = (2, 12, 35, 255)
    draw.text(
        (62, 78),
        args.line_1,
        font=font_line_1,
        fill=(244, 250, 255, 255),
        stroke_width=2,
        stroke_fill=(4, 16, 44, 255),
    )
    draw.rounded_rectangle(
        (64, 200, 370, 211), radius=5, fill=underline
    )
    draw.text(
        (62, 242),
        args.line_2,
        font=font_line_2,
        fill=(255, 255, 255, 255),
        stroke_width=4,
        stroke_fill=dark_stroke,
    )
    draw.text(
        (60, 350),
        args.line_3,
        font=font_line_3,
        fill=accent,
        stroke_width=4,
        stroke_fill=dark_stroke,
    )

    if args.badge:
        bbox = draw.textbbox((0, 0), args.badge, font=font_badge)
        badge_width = bbox[2] - bbox[0] + 54
        badge_height = bbox[3] - bbox[1] + 30
        badge_x, badge_y = 66, 560
        draw.rounded_rectangle(
            (
                badge_x,
                badge_y,
                badge_x + badge_width,
                badge_y + badge_height,
            ),
            radius=badge_height // 2,
            fill=(5, 29, 69, 235),
            outline=badge_outline,
            width=3,
        )
        draw.text(
            (badge_x + 27, badge_y + 9 - bbox[1]),
            args.badge,
            font=font_badge,
            fill=(225, 247, 255, 255),
        )

    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    args.output_jpg.parent.mkdir(parents=True, exist_ok=True)
    rgb = image.convert("RGB")
    rgb.save(args.output_png, format="PNG", optimize=True)
    rgb.save(
        args.output_jpg,
        format="JPEG",
        quality=args.jpeg_quality,
        optimize=True,
        progressive=True,
        subsampling=0,
    )
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        rgb.resize((320, 180), Image.Resampling.LANCZOS).save(
            args.preview, format="JPEG", quality=90, optimize=True
        )

    result = {
        "status": "complete",
        "background": str(args.background.resolve()),
        "output_png": str(args.output_png.resolve()),
        "output_jpg": str(args.output_jpg.resolve()),
        "preview": str(args.preview.resolve()) if args.preview else None,
        "font": str(font_path),
        "text_max_width": args.text_max_width,
        "text_sizes": [
            font_line_1.size,
            font_line_2.size,
            font_line_3.size,
            font_badge.size if args.badge else None,
        ],
        "size": [1280, 720],
        "jpeg_bytes": os.path.getsize(args.output_jpg),
    }
    return result


def main() -> int:
    args = parse_args()
    print(json.dumps(render(args), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
