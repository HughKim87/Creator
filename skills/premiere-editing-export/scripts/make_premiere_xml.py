#!/usr/bin/env python3
"""컷리스트를 Premiere에서 가져올 수 있는 Final Cut Pro 7 XML로 만든다.

원본 영상은 복사하거나 수정하지 않고, XML에서 로컬 원본 경로를 참조한다.
컷리스트는 두 형식을 지원한다.

1. 헤더 없음: 시작,끝[,라벨]
2. 헤더 있음: 시작/끝/구간명 또는 start/end/label 계열 컬럼
"""
import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Cut:
    index: int
    start: float
    end: float
    label: str
    role: str = ""

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class MediaInfo:
    duration: float
    width: int
    height: int
    fps: Fraction
    sample_rate: int
    channels: int

    @property
    def timebase(self) -> int:
        return max(1, int(round(float(self.fps))))

    @property
    def ntsc(self) -> bool:
        return self.fps.denominator == 1001


def parse_ts(value: str) -> float:
    text = value.strip()
    if not text:
        raise ValueError("빈 시각 값")
    parts = [float(p) for p in text.split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"시각 형식 오류: {value}")


def seconds_to_frames(seconds: float, fps: Fraction) -> int:
    return int(round(seconds * float(fps)))


def format_seconds(seconds: float) -> str:
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def read_cuts(path: Path) -> list[Cut]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or not any(cell.strip() for cell in row):
                continue
            if row[0].strip().startswith("#"):
                continue
            rows.append(row)
    if not rows:
        raise ValueError("컷리스트가 비어 있음")

    first = [cell.strip().lower() for cell in rows[0]]
    has_header = (
        "시작" in first
        or "start" in first
        or "start_time" in first
        or "끝" in first
        or "end" in first
        or "end_time" in first
    )

    cuts: list[Cut] = []
    if has_header:
        header = {name: i for i, name in enumerate(first)}
        start_i = first.index("시작") if "시작" in first else header.get("start", header.get("start_time"))
        end_i = first.index("끝") if "끝" in first else header.get("end", header.get("end_time"))
        label_i = None
        role_i = None
        for key in ("구간명", "label", "name", "segment_name", "title"):
            if key in header:
                label_i = header[key]
                break
        for key in ("역할", "role", "note", "notes"):
            if key in header:
                role_i = header[key]
                break
        if start_i is None or end_i is None:
            raise ValueError("헤더 컷리스트에는 시작/끝 컬럼이 필요함")
        data_rows = rows[1:]
        for i, row in enumerate(data_rows, 1):
            start = parse_ts(row[start_i])
            end = parse_ts(row[end_i])
            label = row[label_i].strip() if label_i is not None and label_i < len(row) else f"cut_{i:03d}"
            role = row[role_i].strip() if role_i is not None and role_i < len(row) else ""
            if end <= start:
                raise ValueError(f"끝이 시작보다 빠름: {row}")
            cuts.append(Cut(i, start, end, label, role))
    else:
        for i, row in enumerate(rows, 1):
            if len(row) < 2:
                raise ValueError(f"컷리스트 행에는 시작/끝이 필요함: {row}")
            start = parse_ts(row[0])
            end = parse_ts(row[1])
            label = row[2].strip() if len(row) > 2 else f"cut_{i:03d}"
            if end <= start:
                raise ValueError(f"끝이 시작보다 빠름: {row}")
            cuts.append(Cut(i, start, end, label))

    return cuts


def project_tool(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    exe = f"{name}.exe" if sys.platform.startswith("win") else name
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "tools" / "ffmpeg" / "bin" / exe
        if candidate.exists():
            return str(candidate)
    return None


def parse_fraction(value: str | None, fallback: Fraction) -> Fraction:
    if not value or value == "0/0":
        return fallback
    try:
        return Fraction(value)
    except ZeroDivisionError:
        return fallback


def read_media_info(source: Path, fallback_end: float) -> MediaInfo:
    ffprobe = project_tool("ffprobe")
    if ffprobe is None:
        return MediaInfo(fallback_end, 1920, 1080, Fraction(30, 1), 48000, 2)

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-show_entries",
        "stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
        "-of",
        "json",
        str(source),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return MediaInfo(fallback_end, 1920, 1080, Fraction(30, 1), 48000, 2)

    data = json.loads(result.stdout)
    duration = float(data.get("format", {}).get("duration") or fallback_end)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fps = parse_fraction(video.get("avg_frame_rate"), Fraction(30, 1))
    if fps == 0:
        fps = parse_fraction(video.get("r_frame_rate"), Fraction(30, 1))
    return MediaInfo(
        duration=max(duration, fallback_end),
        width=int(video.get("width") or 1920),
        height=int(video.get("height") or 1080),
        fps=fps,
        sample_rate=int(audio.get("sample_rate") or 48000),
        channels=max(1, int(audio.get("channels") or 2)),
    )


def add(parent: ET.Element, tag: str, text: str | int | None = None, **attrs: str) -> ET.Element:
    element = ET.SubElement(parent, tag, attrs)
    if text is not None:
        element.text = str(text)
    return element


def add_rate(parent: ET.Element, media: MediaInfo) -> ET.Element:
    rate = add(parent, "rate")
    add(rate, "timebase", media.timebase)
    add(rate, "ntsc", "TRUE" if media.ntsc else "FALSE")
    return rate


def add_video_characteristics(parent: ET.Element, media: MediaInfo) -> ET.Element:
    sample = add(parent, "samplecharacteristics")
    add_rate(sample, media)
    add(sample, "width", media.width)
    add(sample, "height", media.height)
    add(sample, "anamorphic", "FALSE")
    add(sample, "pixelaspectratio", "square")
    add(sample, "fielddominance", "none")
    return sample


def add_audio_characteristics(parent: ET.Element, media: MediaInfo) -> ET.Element:
    sample = add(parent, "samplecharacteristics")
    add(sample, "depth", 16)
    add(sample, "samplerate", media.sample_rate)
    return sample


def path_url(path: Path) -> str:
    posix = path.resolve().as_posix()
    return "file://localhost/" + quote(posix, safe="/:")


def add_file(parent: ET.Element, source: Path, media: MediaInfo, source_frames: int, full: bool) -> ET.Element:
    file_el = add(parent, "file", id="file-1")
    if not full:
        return file_el
    add(file_el, "name", source.name)
    add(file_el, "pathurl", path_url(source))
    add_rate(file_el, media)
    add(file_el, "duration", source_frames)
    file_media = add(file_el, "media")
    file_video = add(file_media, "video")
    add(file_video, "duration", source_frames)
    add_video_characteristics(file_video, media)
    file_audio = add(file_media, "audio")
    add_audio_characteristics(file_audio, media)
    add(file_audio, "channelcount", media.channels)
    return file_el


def add_links(clipitem: ET.Element, links: list[tuple[str, str, int, int]]) -> None:
    for link_id, mediatype, track_index, clip_index in links:
        link = add(clipitem, "link")
        add(link, "linkclipref", link_id)
        add(link, "mediatype", mediatype)
        add(link, "trackindex", track_index)
        add(link, "clipindex", clip_index)
        if mediatype == "audio":
            add(link, "groupindex", 1)


def add_clipitem(
    parent: ET.Element,
    *,
    item_id: str,
    name: str,
    media: MediaInfo,
    source: Path,
    source_frames: int,
    start: int,
    end: int,
    in_frame: int,
    out_frame: int,
    mediatype: str,
    track_index: int,
    include_file: bool = False,
) -> ET.Element:
    clipitem = add(parent, "clipitem", id=item_id)
    add(clipitem, "masterclipid", "masterclip-1")
    add(clipitem, "name", name)
    add(clipitem, "enabled", "TRUE")
    add(clipitem, "duration", max(0, out_frame - in_frame))
    add_rate(clipitem, media)
    add(clipitem, "start", start)
    add(clipitem, "end", end)
    add(clipitem, "in", in_frame)
    add(clipitem, "out", out_frame)
    add_file(clipitem, source, media, source_frames, include_file)
    sourcetrack = add(clipitem, "sourcetrack")
    add(sourcetrack, "mediatype", mediatype)
    add(sourcetrack, "trackindex", track_index)
    return clipitem


def add_master_clip(parent: ET.Element, source: Path, media: MediaInfo, source_frames: int) -> None:
    clip = add(parent, "clip", id="masterclip-1")
    add(clip, "name", source.name)
    add(clip, "duration", source_frames)
    add_rate(clip, media)
    clip_media = add(clip, "media")

    video = add(clip_media, "video")
    video_track = add(video, "track")
    add_clipitem(
        video_track,
        item_id="masterclip-1-v",
        name=source.name,
        media=media,
        source=source,
        source_frames=source_frames,
        start=0,
        end=source_frames,
        in_frame=0,
        out_frame=source_frames,
        mediatype="video",
        track_index=1,
        include_file=True,
    )

    audio = add(clip_media, "audio")
    for channel in range(1, min(media.channels, 2) + 1):
        track = add(audio, "track")
        add_clipitem(
            track,
            item_id=f"masterclip-1-a{channel}",
            name=source.name,
            media=media,
            source=source,
            source_frames=source_frames,
            start=0,
            end=source_frames,
            in_frame=0,
            out_frame=source_frames,
            mediatype="audio",
            track_index=channel,
        )


def add_candidate_clip(parent: ET.Element, cut: Cut, source: Path, media: MediaInfo, source_frames: int) -> None:
    in_frame = seconds_to_frames(cut.start, media.fps)
    out_frame = seconds_to_frames(cut.end, media.fps)
    duration = max(0, out_frame - in_frame)
    name = f"{cut.index:02d}_{cut.label}"

    clip = add(parent, "clip", id=f"candidate-{cut.index:03d}")
    add(clip, "name", name)
    add(clip, "duration", duration)
    add_rate(clip, media)
    add(clip, "in", in_frame)
    add(clip, "out", out_frame)
    clip_media = add(clip, "media")

    video = add(clip_media, "video")
    video_track = add(video, "track")
    add_clipitem(
        video_track,
        item_id=f"candidate-{cut.index:03d}-v",
        name=name,
        media=media,
        source=source,
        source_frames=source_frames,
        start=0,
        end=duration,
        in_frame=in_frame,
        out_frame=out_frame,
        mediatype="video",
        track_index=1,
    )

    audio = add(clip_media, "audio")
    for channel in range(1, min(media.channels, 2) + 1):
        track = add(audio, "track")
        add_clipitem(
            track,
            item_id=f"candidate-{cut.index:03d}-a{channel}",
            name=name,
            media=media,
            source=source,
            source_frames=source_frames,
            start=0,
            end=duration,
            in_frame=in_frame,
            out_frame=out_frame,
            mediatype="audio",
            track_index=channel,
        )


def add_sequence(parent: ET.Element, name: str, cuts: list[Cut], source: Path, media: MediaInfo, source_frames: int) -> None:
    cut_frames = [(cut, seconds_to_frames(cut.duration, media.fps)) for cut in cuts]
    sequence_frames = sum(frames for _, frames in cut_frames)

    sequence = add(parent, "sequence", id="sequence-1")
    add(sequence, "name", name)
    add(sequence, "duration", sequence_frames)
    add_rate(sequence, media)

    timecode = add(sequence, "timecode")
    add_rate(timecode, media)
    add(timecode, "string", "00:00:00:00")
    add(timecode, "frame", 0)
    add(timecode, "displayformat", "NDF")

    sequence_media = add(sequence, "media")
    video = add(sequence_media, "video")
    fmt = add(video, "format")
    add_video_characteristics(fmt, media)
    video_track = add(video, "track")

    timeline_pos = 0
    for clip_index, (cut, duration) in enumerate(cut_frames, 1):
        in_frame = seconds_to_frames(cut.start, media.fps)
        out_frame = seconds_to_frames(cut.end, media.fps)
        clip_name = f"{cut.index:02d}_{cut.label}"
        video_id = f"seq-clip-{cut.index:03d}-v"
        audio_ids = [f"seq-clip-{cut.index:03d}-a{channel}" for channel in range(1, min(media.channels, 2) + 1)]
        links = [(video_id, "video", 1, clip_index)] + [
            (audio_id, "audio", channel, clip_index) for channel, audio_id in enumerate(audio_ids, 1)
        ]
        clipitem = add_clipitem(
            video_track,
            item_id=video_id,
            name=clip_name,
            media=media,
            source=source,
            source_frames=source_frames,
            start=timeline_pos,
            end=timeline_pos + duration,
            in_frame=in_frame,
            out_frame=out_frame,
            mediatype="video",
            track_index=1,
        )
        add_links(clipitem, links)
        timeline_pos += duration

    audio = add(sequence_media, "audio")
    add(audio, "numOutputChannels", min(media.channels, 2))
    for channel in range(1, min(media.channels, 2) + 1):
        audio_format = add(audio, "format")
        add_audio_characteristics(audio_format, media)
        track = add(audio, "track")
        timeline_pos = 0
        for clip_index, (cut, duration) in enumerate(cut_frames, 1):
            in_frame = seconds_to_frames(cut.start, media.fps)
            out_frame = seconds_to_frames(cut.end, media.fps)
            clip_name = f"{cut.index:02d}_{cut.label}"
            video_id = f"seq-clip-{cut.index:03d}-v"
            audio_ids = [f"seq-clip-{cut.index:03d}-a{audio_channel}" for audio_channel in range(1, min(media.channels, 2) + 1)]
            links = [(video_id, "video", 1, clip_index)] + [
                (audio_id, "audio", audio_channel, clip_index)
                for audio_channel, audio_id in enumerate(audio_ids, 1)
            ]
            clipitem = add_clipitem(
                track,
                item_id=f"seq-clip-{cut.index:03d}-a{channel}",
                name=clip_name,
                media=media,
                source=source,
                source_frames=source_frames,
                start=timeline_pos,
                end=timeline_pos + duration,
                in_frame=in_frame,
                out_frame=out_frame,
                mediatype="audio",
                track_index=channel,
            )
            add_links(clipitem, links)
            timeline_pos += duration


def build_xml(project_name: str, sequence_name: str, cuts: list[Cut], source: Path, media: MediaInfo) -> ET.Element:
    source_frames = seconds_to_frames(media.duration, media.fps)

    root = ET.Element("xmeml", version="5")
    project = add(root, "project")
    add(project, "name", project_name)
    children = add(project, "children")

    original_bin = add(children, "bin")
    add(original_bin, "name", "00_원본")
    original_children = add(original_bin, "children")
    add_master_clip(original_children, source, media, source_frames)

    candidates_bin = add(children, "bin")
    add(candidates_bin, "name", "01_후보클립")
    candidates_children = add(candidates_bin, "children")
    for cut in cuts:
        add_candidate_clip(candidates_children, cut, source, media, source_frames)

    sequence_bin = add(children, "bin")
    add(sequence_bin, "name", "02_시퀀스")
    sequence_children = add(sequence_bin, "children")
    add_sequence(sequence_children, sequence_name, cuts, source, media, source_frames)

    return root


def write_xml(path: Path, root: ET.Element) -> None:
    if path.exists():
        raise FileExistsError(f"출력 파일이 이미 존재함(덮어쓰기 금지): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="utf-8")
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + body + b"\n")


def write_guide(
    path: Path,
    xml_path: Path,
    source: Path,
    cuts: list[Cut],
    media: MediaInfo,
    project_name: str,
    sequence_name: str,
) -> None:
    if path.exists():
        raise FileExistsError(f"안내 문서가 이미 존재함(덮어쓰기 금지): {path}")
    total = sum(cut.duration for cut in cuts)
    lines = [
        f"# {project_name} Premiere XML 사용 방법",
        "",
        "## 생성 목적",
        "",
        "이 파일은 완성 컷편집본이 아니라 Premiere에서 바로 다듬기 위한 편집 준비 패키지다.",
        "원본 영상은 복사하지 않고 XML에서 원본 경로만 참조한다.",
        "",
        "## 생성 파일",
        "",
        f"- XML: `{xml_path.name}`",
        f"- 원본 참조: `{source}`",
        f"- 컷 수: {len(cuts)}개",
        f"- 연결 시퀀스 길이: 약 {format_seconds(total)}",
        f"- 소스 정보: {media.width}x{media.height}, {float(media.fps):.3f}fps, audio {media.sample_rate}Hz/{media.channels}ch",
        "",
        "## Premiere에서 여는 방법",
        "",
        "1. Premiere Pro에서 `파일 > 가져오기`를 누른다.",
        f"2. `{xml_path.name}`을 선택한다.",
        "3. 미디어 연결 창이 뜨면 위 원본 영상을 선택한다.",
        "4. 프로젝트 패널에서 `00_원본`, `01_후보클립`, `02_시퀀스`가 들어왔는지 확인한다.",
        f"5. `{sequence_name}` 시퀀스를 열고 컷 경계, 오디오, 빠진 장면을 직접 다듬는다.",
        "",
        "## 기대 구조",
        "",
        "- `00_원본`: 원본 mkv 참조",
        "- `01_후보클립`: 컷리스트 기준 후보 구간",
        "- `02_시퀀스`: 후보 구간을 순서대로 연결한 러프컷 타임라인",
        "",
        "## 실패 시 대체 경로",
        "",
        "- XML 가져오기가 실패하면 기존 EDL을 먼저 가져오고 원본을 다시 연결한다.",
        "- MKV 연결이 불안정하면 원본을 ProRes/DNxHR 같은 편집용 중간 파일로 별도 변환한 뒤, 같은 컷리스트로 XML을 다시 만든다.",
        "- 이 XML은 컷 순서와 원본 참조를 위한 자료이며, 자막/효과/전환/색보정까지 자동 재현하는 파일은 아니다.",
        "",
        "## 참고 근거",
        "",
        "- Adobe Premiere는 Final Cut Pro XML 내보내기/가져오기 흐름을 지원한다: https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/export-a-project-as-a-final-cut-pro-xml-file.html",
        "- FCPX의 `.fcpxml`은 Premiere가 직접 읽는 표준 XML과 다르므로 변환이 필요하다: https://helpx.adobe.com/premiere/desktop/organize-media/import-files/migrate-from-final-cut-pro-x.html",
        "- EDL은 단순 프로젝트에 적합하므로 후보 클립/빈/풍부한 구조에는 XML이 더 맞다: https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/export-a-project-as-an-edl-file.html",
        "",
        "## 컷 목록",
        "",
        "| 번호 | 구간명 | 시작 | 끝 | 길이 | 역할 |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for cut in cuts:
        lines.append(
            f"| {cut.index} | {cut.label} | {format_seconds(cut.start)} | "
            f"{format_seconds(cut.end)} | {format_seconds(cut.duration)} | {cut.role} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="원본 영상 경로")
    parser.add_argument("cutlist", help="컷리스트 CSV")
    parser.add_argument("output_xml", help="생성할 Final Cut Pro 7 XML")
    parser.add_argument("--project-name", default="CRA_PLAY_EDIT_ASSIST_V1")
    parser.add_argument("--sequence-name", default="러프컷_추천순서_v1")
    parser.add_argument("--guide", help="생성할 사용 방법 Markdown")
    args = parser.parse_args()

    source = Path(args.source)
    cutlist = Path(args.cutlist)
    output_xml = Path(args.output_xml)
    if not source.exists():
        sys.exit(f"원본 없음: {source}")
    if not cutlist.exists():
        sys.exit(f"컷리스트 없음: {cutlist}")

    cuts = read_cuts(cutlist)
    media = read_media_info(source, max(cut.end for cut in cuts))
    root = build_xml(args.project_name, args.sequence_name, cuts, source, media)
    write_xml(output_xml, root)

    if args.guide:
        write_guide(Path(args.guide), output_xml, source.resolve(), cuts, media, args.project_name, args.sequence_name)

    total = sum(cut.duration for cut in cuts)
    print(f"[premiere-xml] 컷 {len(cuts)}개, 시퀀스 약 {format_seconds(total)}")
    print(f"[premiere-xml] 완료: {output_xml}")


if __name__ == "__main__":
    main()
