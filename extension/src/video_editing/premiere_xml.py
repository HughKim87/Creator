from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping
from urllib.parse import quote
import xml.etree.ElementTree as ET

from .model import validate_timeline


class PremiereXmlError(ValueError):
    pass


def _child(parent: ET.Element, tag: str, text: str | int | None = None) -> ET.Element:
    element = ET.SubElement(parent, tag)
    if text is not None:
        element.text = str(text)
    return element


def _rate(parent: ET.Element, numerator: int, denominator: int) -> tuple[int, str]:
    if denominator == 1001 and numerator in {24000, 30000, 60000}:
        timebase = numerator // 1000
        ntsc = "TRUE"
    elif numerator % denominator == 0:
        timebase = numerator // denominator
        ntsc = "FALSE"
    else:
        raise PremiereXmlError(
            f"unsupported frame rate for Premiere XML: {numerator}/{denominator}"
        )
    rate = _child(parent, "rate")
    _child(rate, "timebase", timebase)
    _child(rate, "ntsc", ntsc)
    return timebase, ntsc


def _path_url(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("/"):
        rendered = normalized
    else:
        rendered = "/" + normalized
    return "file://localhost" + quote(rendered, safe="/:")


def _sample_characteristics(
    parent: ET.Element,
    *,
    source: Mapping[str, Any],
    media_type: str,
) -> None:
    sample = _child(parent, "samplecharacteristics")
    frame_rate = source["frame_rate"]
    _rate(sample, frame_rate["numerator"], frame_rate["denominator"])
    if media_type == "video":
        _child(sample, "width", source["video"]["width"])
        _child(sample, "height", source["video"]["height"])
        _child(sample, "anamorphic", "FALSE")
        _child(sample, "pixelaspectratio", "square")
        _child(sample, "fielddominance", "none")
    else:
        _child(sample, "depth", 16)
        _child(sample, "samplerate", source["audio"]["sample_rate"])
        _child(sample, "channelcount", source["audio"]["channels"])


def _source_file(
    parent: ET.Element,
    *,
    source: Mapping[str, Any],
    first_reference: bool,
) -> None:
    file_element = _child(parent, "file")
    file_element.set("id", "file-1")
    if not first_reference:
        return
    _child(file_element, "name", Path(source["path"]).name)
    _child(file_element, "pathurl", _path_url(source["path"]))
    _rate(
        file_element,
        source["frame_rate"]["numerator"],
        source["frame_rate"]["denominator"],
    )
    _child(file_element, "duration", source["total_frames"])
    timecode = _child(file_element, "timecode")
    _rate(
        timecode,
        source["frame_rate"]["numerator"],
        source["frame_rate"]["denominator"],
    )
    _child(timecode, "string", "00:00:00:00")
    _child(timecode, "frame", 0)
    _child(timecode, "displayformat", "NDF")
    media = _child(file_element, "media")
    video = _child(media, "video")
    _sample_characteristics(video, source=source, media_type="video")
    audio = _child(media, "audio")
    _sample_characteristics(audio, source=source, media_type="audio")


def _clip_item(
    track: ET.Element,
    *,
    xml_id: str,
    clip: Mapping[str, Any],
    source: Mapping[str, Any],
    media_type: str,
    channel: int | None,
    first_reference: bool,
) -> ET.Element:
    item = _child(track, "clipitem")
    item.set("id", xml_id)
    _child(item, "masterclipid", "masterclip-1")
    _child(item, "name", clip["id"])
    _child(item, "enabled", "TRUE")
    _child(item, "duration", source["total_frames"])
    _rate(
        item,
        source["frame_rate"]["numerator"],
        source["frame_rate"]["denominator"],
    )
    _child(item, "start", clip["timeline_start"])
    _child(item, "end", clip["timeline_end"])
    _child(item, "in", clip["source_in"])
    _child(item, "out", clip["source_out"])
    _source_file(item, source=source, first_reference=first_reference)
    source_track = _child(item, "sourcetrack")
    _child(source_track, "mediatype", media_type)
    if channel is not None:
        _child(source_track, "trackindex", channel)
    labels = _child(item, "labels")
    _child(labels, "label2", "Forest")
    logging_info = _child(item, "logginginfo")
    _child(logging_info, "description", clip["edit_reason"])
    return item


def _add_links(specs: list[dict[str, Any]]) -> None:
    groups: dict[tuple[int, int, int, int], list[dict[str, Any]]] = {}
    for spec in specs:
        clip = spec["clip"]
        key = (
            clip["source_in"],
            clip["source_out"],
            clip["timeline_start"],
            clip["timeline_end"],
        )
        groups.setdefault(key, []).append(spec)
    for group in groups.values():
        if len(group) < 2:
            continue
        ordered = sorted(
            group,
            key=lambda item: (
                0 if item["media_type"] == "video" else 1,
                item["track_index"],
                item["clip_index"],
            ),
        )
        for owner in ordered:
            for linked in ordered:
                link = _child(owner["element"], "link")
                _child(link, "linkclipref", linked["xml_id"])
                _child(link, "mediatype", linked["media_type"])
                _child(link, "trackindex", linked["track_index"])
                _child(link, "clipindex", linked["clip_index"])
                _child(link, "groupindex", 1)


def build_premiere_xml(value: Mapping[str, Any]) -> bytes:
    timeline = validate_timeline(value)
    if timeline["semantic_gate"]["status"] != "passed":
        raise PremiereXmlError("semantic_gate must be passed before XML generation")
    source = timeline["source"]
    sequence_value = timeline["sequence"]
    root = ET.Element("xmeml", {"version": "5"})
    sequence = _child(root, "sequence")
    sequence.set("id", "sequence-1")
    _child(sequence, "name", sequence_value["name"])
    duration = sequence_value["video_clips"][-1]["timeline_end"]
    _child(sequence, "duration", duration)
    _rate(
        sequence,
        source["frame_rate"]["numerator"],
        source["frame_rate"]["denominator"],
    )
    _child(sequence, "in", -1)
    _child(sequence, "out", -1)
    timecode = _child(sequence, "timecode")
    _rate(
        timecode,
        source["frame_rate"]["numerator"],
        source["frame_rate"]["denominator"],
    )
    _child(timecode, "string", "00:00:00:00")
    _child(timecode, "frame", 0)
    _child(timecode, "displayformat", "NDF")
    media = _child(sequence, "media")
    specs: list[dict[str, Any]] = []
    first_reference = True

    video = _child(media, "video")
    video_format = _child(video, "format")
    _sample_characteristics(video_format, source=source, media_type="video")
    video_track = _child(video, "track")
    for clip_index, clip in enumerate(sequence_value["video_clips"], start=1):
        xml_id = f"video-{clip['id']}"
        element = _clip_item(
            video_track,
            xml_id=xml_id,
            clip=clip,
            source=source,
            media_type="video",
            channel=None,
            first_reference=first_reference,
        )
        first_reference = False
        specs.append(
            {
                "xml_id": xml_id,
                "element": element,
                "clip": clip,
                "media_type": "video",
                "track_index": 1,
                "clip_index": clip_index,
            }
        )
    _child(video_track, "enabled", "TRUE")
    _child(video_track, "locked", "FALSE")

    audio = _child(media, "audio")
    audio_format = _child(audio, "format")
    _sample_characteristics(audio_format, source=source, media_type="audio")
    for channel in range(1, source["audio"]["channels"] + 1):
        audio_track = _child(audio, "track")
        audio_track.set("currentExplodedTrackIndex", str(channel))
        audio_track.set("totalExplodedTrackCount", str(source["audio"]["channels"]))
        audio_track.set("premiereTrackType", "Stereo")
        for clip_index, clip in enumerate(sequence_value["audio_clips"], start=1):
            xml_id = f"audio-{channel}-{clip['id']}"
            element = _clip_item(
                audio_track,
                xml_id=xml_id,
                clip=clip,
                source=source,
                media_type="audio",
                channel=channel,
                first_reference=first_reference,
            )
            first_reference = False
            specs.append(
                {
                    "xml_id": xml_id,
                    "element": element,
                    "clip": clip,
                    "media_type": "audio",
                    "track_index": channel,
                    "clip_index": clip_index,
                }
            )
        _child(audio_track, "enabled", "TRUE")
        _child(audio_track, "locked", "FALSE")

    _add_links(specs)
    ET.indent(root, space="  ")
    rendered = ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )
    return rendered + b"\n"


def write_premiere_xml(
    value: Mapping[str, Any],
    output_path: Path | str,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    target = Path(output_path)
    if not target.parent.is_dir():
        raise PremiereXmlError(f"output directory does not exist: {target.parent}")
    if target.exists() and not overwrite:
        raise PremiereXmlError(f"output already exists: {target}")
    rendered = build_premiere_xml(value)
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
        if target.exists() and not overwrite:
            raise PremiereXmlError(f"output already exists: {target}")
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "output": str(target),
        "bytes": len(rendered),
        "sha256": hashlib.sha256(rendered).hexdigest(),
        "source_id": value["source"]["id"],
        "source_references": 1,
    }
