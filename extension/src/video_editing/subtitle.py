from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping


TIMESTAMP_PATTERN = re.compile(
    r"^(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})"
    r"(?P<separator>[,.])(?P<milliseconds>\d{3})$"
)
TIMELINE_PATTERN = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})(?:\s+.*)?$"
)


class SubtitleError(ValueError):
    pass


@dataclass(frozen=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text_lines: tuple[str, ...]


def _timestamp_ms(value: str) -> int:
    match = TIMESTAMP_PATTERN.fullmatch(value)
    if match is None:
        raise SubtitleError(f"invalid timestamp: {value}")
    minutes = int(match.group("minutes"))
    seconds = int(match.group("seconds"))
    if minutes > 59 or seconds > 59:
        raise SubtitleError(f"invalid timestamp: {value}")
    return (
        (
            int(match.group("hours")) * 60
            + minutes
        )
        * 60
        + seconds
    ) * 1000 + int(match.group("milliseconds"))


def _format_timestamp(value: int) -> str:
    if value < 0:
        raise SubtitleError("timestamp cannot be negative")
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _parse_text(raw: str) -> list[Cue]:
    normalized = raw.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.strip("\n")
    if not normalized.strip():
        raise SubtitleError("subtitle is empty")
    cues: list[Cue] = []
    for block_number, block in enumerate(
        re.split(r"\n(?:[ \t]*\n)+", normalized),
        start=1,
    ):
        lines = block.split("\n")
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise SubtitleError(f"invalid SRT block: {block_number}")
        timeline = TIMELINE_PATTERN.fullmatch(lines[1].strip())
        if timeline is None:
            raise SubtitleError(f"invalid SRT timeline at block: {block_number}")
        cues.append(
            Cue(
                index=int(lines[0].strip()),
                start_ms=_timestamp_ms(timeline.group("start")),
                end_ms=_timestamp_ms(timeline.group("end")),
                text_lines=tuple(lines[2:]),
            )
        )
    return cues


def parse_srt(path: Path | str) -> list[Cue]:
    subtitle_path = Path(path)
    try:
        raw = subtitle_path.read_bytes().decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise SubtitleError("subtitle must be strict UTF-8") from exc
    except OSError as exc:
        raise SubtitleError(f"cannot read subtitle: {subtitle_path}") from exc
    return _parse_text(raw)


def _validate_indices_and_text(cues: list[Cue]) -> None:
    if not cues:
        raise SubtitleError("subtitle must contain at least one cue")
    for expected_index, cue in enumerate(cues, start=1):
        if cue.index != expected_index:
            raise SubtitleError(
                f"subtitle indices must be sequential: expected {expected_index}, got {cue.index}"
            )
        if not cue.text_lines or not any(line.strip() for line in cue.text_lines):
            raise SubtitleError(f"cue {cue.index} has no text")


def validate_cues(cues: list[Cue], *, media_end_ms: int | None = None) -> None:
    _validate_indices_and_text(cues)
    if media_end_ms is not None and media_end_ms < 1:
        raise SubtitleError("media_end_ms must be a positive integer")
    previous: Cue | None = None
    for cue in cues:
        if cue.end_ms <= cue.start_ms:
            raise SubtitleError(f"cue {cue.index} must have a positive duration")
        if media_end_ms is not None and cue.end_ms > media_end_ms:
            raise SubtitleError(f"cue {cue.index} exceeds the media duration")
        if previous is not None:
            if cue.start_ms < previous.start_ms:
                raise SubtitleError(f"cue {cue.index} starts before the previous cue")
            if cue.start_ms < previous.end_ms:
                raise SubtitleError(f"cue {cue.index} overlaps the previous cue")
        previous = cue


def validate_srt(
    path: Path | str,
    *,
    media_end_ms: int | None = None,
) -> dict[str, object]:
    source = Path(path)
    cues = parse_srt(source)
    validate_cues(cues, media_end_ms=media_end_ms)
    source_bytes = source.read_bytes()
    return {
        "source": str(source),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "cues": len(cues),
        "start_ms": cues[0].start_ms,
        "end_ms": cues[-1].end_ms,
    }


def _render(cues: list[Cue]) -> str:
    blocks = []
    for cue in cues:
        blocks.append(
            "\n".join(
                (
                    str(cue.index),
                    f"{_format_timestamp(cue.start_ms)} --> {_format_timestamp(cue.end_ms)}",
                    *cue.text_lines,
                )
            )
        )
    return "\n\n".join(blocks) + "\n"


def _write_atomic(target: Path, rendered: bytes, *, overwrite: bool) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, target)
        else:
            try:
                os.link(temporary, target)
            except FileExistsError as exc:
                raise SubtitleError(f"destination already exists: {target}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def clean_srt(
    source: Path | str,
    destination: Path | str,
    *,
    media_end_ms: int,
    timestamp_overrides: Mapping[int, Mapping[str, int]],
    excluded_indices: frozenset[int] = frozenset(),
    overwrite: bool = False,
) -> dict[str, object]:
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if source_path == destination_path:
        raise SubtitleError("source and destination must be different files")
    if not destination_path.parent.is_dir():
        raise SubtitleError(
            f"destination directory does not exist: {destination_path.parent}"
        )
    if destination_path.exists() and not overwrite:
        raise SubtitleError(f"destination already exists: {destination_path}")
    previous_destination: bytes | None = None
    if destination_path.exists():
        try:
            previous_destination = destination_path.read_bytes()
        except OSError as exc:
            raise SubtitleError(
                f"cannot read existing destination: {destination_path}"
            ) from exc

    try:
        source_bytes = source_path.read_bytes()
    except OSError as exc:
        raise SubtitleError(f"cannot read subtitle: {source_path}") from exc
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    original = parse_srt(source_path)
    _validate_indices_and_text(original)
    original_by_index = {cue.index: cue for cue in original}

    unknown = (set(timestamp_overrides) | set(excluded_indices)) - set(original_by_index)
    if unknown:
        raise SubtitleError(f"unknown cue indices: {sorted(unknown)}")
    conflict = set(timestamp_overrides) & set(excluded_indices)
    if conflict:
        raise SubtitleError(f"excluded cues cannot have overrides: {sorted(conflict)}")

    retained: list[tuple[Cue, Cue]] = []
    changed_indices: list[int] = []
    for cue in original:
        if cue.index in excluded_indices:
            changed_indices.append(cue.index)
            continue
        override = dict(timestamp_overrides.get(cue.index, {}))
        unknown_fields = set(override) - {"start_ms", "end_ms"}
        if unknown_fields:
            raise SubtitleError(
                f"unknown timestamp override fields for cue {cue.index}: "
                f"{sorted(unknown_fields)}"
            )
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in override.values()
        ):
            raise SubtitleError(
                f"timestamp overrides for cue {cue.index} must be integers >= 0"
            )
        updated = replace(
            cue,
            start_ms=override.get("start_ms", cue.start_ms),
            end_ms=override.get("end_ms", cue.end_ms),
        )
        if updated != cue:
            changed_indices.append(cue.index)
        retained.append((cue, updated))

    cleaned = [
        replace(updated, index=index)
        for index, (_, updated) in enumerate(retained, start=1)
    ]
    validate_cues(cleaned, media_end_ms=media_end_ms)
    for (original_cue, _), cleaned_cue in zip(retained, cleaned, strict=True):
        if cleaned_cue.text_lines != original_cue.text_lines:
            raise SubtitleError(f"cue text changed unexpectedly: {original_cue.index}")

    rendered = _render(cleaned).encode("utf-8")
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise SubtitleError("source subtitle changed during cleanup")
    _write_atomic(destination_path, rendered, overwrite=overwrite)
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        if previous_destination is None and destination_path.exists():
            destination_path.unlink()
        elif previous_destination is not None:
            _write_atomic(destination_path, previous_destination, overwrite=True)
        raise SubtitleError("source subtitle changed during cleanup")
    return {
        "source": str(source_path),
        "destination": str(destination_path),
        "source_sha256": source_hash,
        "destination_sha256": hashlib.sha256(rendered).hexdigest(),
        "source_cues": len(original),
        "cleaned_cues": len(cleaned),
        "changed_indices": sorted(changed_indices),
        "excluded_indices": sorted(excluded_indices),
    }
