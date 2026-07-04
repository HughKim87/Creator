#!/usr/bin/env python3
"""컷리스트를 Premiere에서 가져올 수 있는 Final Cut Pro 7 XML로 만든다.

원본 영상은 복사하거나 수정하지 않고, XML에서 로컬 원본 경로를 참조한다.
여러 원본 파일을 지원한다: 컷리스트의 `원본파일` 컬럼 + 소스 폴더 인자.

XML 구조는 사용자 Premiere(CS6)가 직접 내보낸 참조 XML의 구조를 그대로 따른다:

- xmeml version 4
- 마스터 클립: uuid + 자기참조 masterclipid + ismasterclip TRUE
- 오디오: 모노 2트랙 분해 + premiereTrackType="Stereo" 트랙 속성
  (CS6는 XML 가져오기에서 스테레오 1트랙 복원이 불가능 — 알려진 제약)
- 클립아이템에는 rate를 쓰지 않는다 (시퀀스 rate 상속)

컷리스트는 두 형식을 지원한다.

1. 헤더 없음: 시작,끝[,라벨]  (원본은 소스 인자 파일 하나)
2. 헤더 있음: 시작/끝/구간명/원본파일/역할 컬럼
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
import uuid as uuid_mod
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
    source: str = ""

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
        source_i = None
        for key in ("구간명", "label", "name", "segment_name", "title"):
            if key in header:
                label_i = header[key]
                break
        for key in ("역할", "role", "note", "notes"):
            if key in header:
                role_i = header[key]
                break
        for key in ("원본파일", "원본", "source", "file", "filename"):
            if key in header:
                source_i = header[key]
                break
        if start_i is None or end_i is None:
            raise ValueError("헤더 컷리스트에는 시작/끝 컬럼이 필요함")
        data_rows = rows[1:]
        for i, row in enumerate(data_rows, 1):
            start = parse_ts(row[start_i])
            end = parse_ts(row[end_i])
            label = row[label_i].strip() if label_i is not None and label_i < len(row) else f"cut_{i:03d}"
            role = row[role_i].strip() if role_i is not None and role_i < len(row) else ""
            src_name = row[source_i].strip() if source_i is not None and source_i < len(row) else ""
            if end <= start:
                raise ValueError(f"끝이 시작보다 빠름: {row}")
            cuts.append(Cut(i, start, end, label, role, src_name))
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


@dataclass
class SourceInfo:
    index: int
    path: Path
    media: MediaInfo
    frames: int

    @property
    def file_id(self) -> str:
        return f"file-{self.index}"

    @property
    def clip_id(self) -> str:
        return f"masterclip-{self.index}"


def resolve_sources(cuts: list[Cut], source_arg: Path) -> dict[str, SourceInfo]:
    """소스 인자(파일 또는 폴더)와 컷의 원본파일 컬럼으로 소스 맵을 만든다."""
    if source_arg.is_dir():
        names: list[str] = []
        for cut in cuts:
            if not cut.source:
                raise ValueError(f"폴더 모드에서는 컷마다 원본파일이 필요함: 컷 {cut.index}")
            if cut.source not in names:
                names.append(cut.source)
        paths = {name: source_arg / name for name in names}
    else:
        name = source_arg.name
        for cut in cuts:
            cut.source = name
        paths = {name: source_arg}

    sources: dict[str, SourceInfo] = {}
    for i, (name, path) in enumerate(paths.items(), 1):
        if not path.exists():
            raise FileNotFoundError(f"원본 없음: {path}")
        fallback = max((c.end for c in cuts if c.source == name), default=0.0)
        media = read_media_info(path, fallback)
        frames = seconds_to_frames(media.duration, media.fps)
        sources[name] = SourceInfo(i, path, media, frames)
    return sources


def add(parent: ET.Element, tag: str, text: str | int | None = None, **attrs: str) -> ET.Element:
    element = ET.SubElement(parent, tag, attrs)
    if text is not None:
        element.text = str(text)
    return element


def add_rate(parent: ET.Element, media: MediaInfo) -> ET.Element:
    # 참조 XML은 ntsc가 아니면 ntsc 요소를 쓰지 않는다
    rate = add(parent, "rate")
    add(rate, "timebase", media.timebase)
    if media.ntsc:
        add(rate, "ntsc", "TRUE")
    return rate


def add_timecode(parent: ET.Element, media: MediaInfo, with_reel: bool) -> ET.Element:
    timecode = add(parent, "timecode")
    add_rate(timecode, media)
    add(timecode, "string", "00:00:00:00")
    add(timecode, "frame", 0)
    add(timecode, "displayformat", "NDF")
    if with_reel:
        reel = add(timecode, "reel")
        add(reel, "name", "")
    return timecode


def path_url(path: Path) -> str:
    posix = path.resolve().as_posix()
    return "file://localhost/" + quote(posix, safe="/:")


_FILES_WRITTEN: set[str] = set()


def add_file(parent: ET.Element, src: SourceInfo) -> ET.Element:
    # 소스별 전체 file 정의는 문서에서 처음 한 번만 쓰고, 이후에는 id 참조만 쓴다.
    file_el = add(parent, "file", id=src.file_id)
    if src.file_id in _FILES_WRITTEN:
        return file_el
    _FILES_WRITTEN.add(src.file_id)
    media = src.media
    add(file_el, "name", src.path.name)
    add(file_el, "pathurl", path_url(src.path))
    add_rate(file_el, media)
    add(file_el, "duration", src.frames)
    add_timecode(file_el, media, with_reel=True)
    file_media = add(file_el, "media")
    file_video = add(file_media, "video")
    add(file_video, "duration", src.frames)
    sample = add(file_video, "samplecharacteristics")
    add_rate(sample, media)
    add(sample, "width", media.width)
    add(sample, "height", media.height)
    add(sample, "anamorphic", "FALSE")
    add(sample, "pixelaspectratio", "square")
    add(sample, "fielddominance", "none")
    file_audio = add(file_media, "audio")
    audio_sample = add(file_audio, "samplecharacteristics")
    add(audio_sample, "depth", 16)
    add(audio_sample, "samplerate", media.sample_rate)
    add(file_audio, "channelcount", media.channels)
    return file_el


def n_audio(media: MediaInfo) -> int:
    return min(media.channels, 2)


def add_links(clipitem: ET.Element, video_id: str, audio_ids: list[str], clip_index: int) -> None:
    link = add(clipitem, "link")
    add(link, "linkclipref", video_id)
    add(link, "mediatype", "video")
    add(link, "trackindex", 1)
    add(link, "clipindex", clip_index)
    for channel, audio_id in enumerate(audio_ids, 1):
        link = add(clipitem, "link")
        add(link, "linkclipref", audio_id)
        add(link, "mediatype", "audio")
        add(link, "trackindex", channel)
        add(link, "clipindex", clip_index)
        add(link, "groupindex", 1)


def add_master_clip(parent: ET.Element, src: SourceInfo) -> None:
    # 참조 XML 구조: uuid + 자기참조 masterclipid + ismasterclip TRUE.
    # 이 3요소가 없으면 Premiere가 타임라인 클립을 마스터 클립과 연결하지 못한다.
    media = src.media
    clip = add(parent, "clip", id=src.clip_id, frameBlend="FALSE")
    add(clip, "uuid", str(uuid_mod.uuid4()))
    add(clip, "masterclipid", src.clip_id)
    add(clip, "ismasterclip", "TRUE")
    add(clip, "duration", src.frames)
    add_rate(clip, media)
    add(clip, "name", src.path.name)
    clip_media = add(clip, "media")

    video_id = f"{src.clip_id}-v"
    audio_ids = [f"{src.clip_id}-a{c}" for c in range(1, n_audio(media) + 1)]

    video = add(clip_media, "video")
    video_track = add(video, "track")
    clipitem = add(video_track, "clipitem", id=video_id, frameBlend="FALSE")
    add(clipitem, "masterclipid", src.clip_id)
    add(clipitem, "name", src.path.name)
    add(clipitem, "alphatype", "none")
    add(clipitem, "pixelaspectratio", "square")
    add(clipitem, "anamorphic", "FALSE")
    add_file(clipitem, src)
    add_links(clipitem, video_id, audio_ids, 1)

    audio = add(clip_media, "audio")
    for channel in range(1, n_audio(media) + 1):
        track = add(audio, "track")
        clipitem = add(track, "clipitem", id=audio_ids[channel - 1], frameBlend="FALSE")
        add(clipitem, "masterclipid", src.clip_id)
        add(clipitem, "name", src.path.name)
        add_file(clipitem, src)
        sourcetrack = add(clipitem, "sourcetrack")
        add(sourcetrack, "mediatype", "audio")
        add(sourcetrack, "trackindex", channel)
        add_links(clipitem, video_id, audio_ids, 1)


def add_sequence(
    parent: ET.Element,
    name: str,
    cuts: list[Cut],
    sources: dict[str, SourceInfo],
    *,
    seq_id: str = "sequence-1",
    id_prefix: str = "seq-clip",
    audio_layout: str = "exploded",
) -> None:
    ref_media = sources[cuts[0].source].media

    def cut_src(cut: Cut) -> SourceInfo:
        return sources[cut.source]

    cut_frames = [(cut, seconds_to_frames(cut.duration, cut_src(cut).media.fps)) for cut in cuts]
    sequence_frames = sum(frames for _, frames in cut_frames)

    sequence = add(parent, "sequence", id=seq_id)
    add(sequence, "uuid", str(uuid_mod.uuid4()))
    add(sequence, "duration", sequence_frames)
    add_rate(sequence, ref_media)
    add(sequence, "name", name)
    sequence_media = add(sequence, "media")

    n_a = 1 if audio_layout == "single" else n_audio(ref_media)

    def clip_ids(cut: Cut) -> tuple[str, list[str]]:
        video_id = f"{id_prefix}-{cut.index:03d}-v"
        audio_ids = [f"{id_prefix}-{cut.index:03d}-a{c}" for c in range(1, n_a + 1)]
        return video_id, audio_ids

    # ── 비디오 ──────────────────────────────────────────
    video = add(sequence_media, "video")
    fmt = add(video, "format")
    sample = add(fmt, "samplecharacteristics")
    add_rate(sample, ref_media)
    add(sample, "width", ref_media.width)
    add(sample, "height", ref_media.height)
    add(sample, "anamorphic", "FALSE")
    add(sample, "pixelaspectratio", "square")
    add(sample, "fielddominance", "none")

    video_track = add(video, "track")
    add(video_track, "enabled", "TRUE")
    add(video_track, "locked", "FALSE")
    timeline_pos = 0
    for clip_index, (cut, duration) in enumerate(cut_frames, 1):
        src = cut_src(cut)
        in_frame = seconds_to_frames(cut.start, src.media.fps)
        out_frame = seconds_to_frames(cut.end, src.media.fps)
        video_id, audio_ids = clip_ids(cut)
        clipitem = add(video_track, "clipitem", id=video_id, frameBlend="FALSE")
        add(clipitem, "masterclipid", src.clip_id)
        add(clipitem, "name", f"{cut.index:02d}_{cut.label}")
        add(clipitem, "enabled", "TRUE")
        add(clipitem, "duration", duration)
        add(clipitem, "start", timeline_pos)
        add(clipitem, "end", timeline_pos + duration)
        add(clipitem, "in", in_frame)
        add(clipitem, "out", out_frame)
        add(clipitem, "alphatype", "none")
        add_file(clipitem, src)
        add_links(clipitem, video_id, audio_ids, clip_index)
        timeline_pos += duration

    # ── 오디오 ──────────────────────────────────────────
    # 참조 XML 구조: 모노 2트랙 분해 + premiereTrackType="Stereo" 트랙 속성.
    # CS6 제약으로 가져오기 시 L/R 링크 2트랙이 된다 (스테레오 1트랙 복원 불가).
    audio = add(sequence_media, "audio")
    audio_format = add(audio, "format")
    audio_sample = add(audio_format, "samplecharacteristics")
    add(audio_sample, "depth", 16)
    add(audio_sample, "samplerate", ref_media.sample_rate)
    outputs = add(audio, "outputs")
    for channel in range(1, n_audio(ref_media) + 1):
        group = add(outputs, "group")
        add(group, "index", channel)
        add(group, "numchannels", 1)
        add(group, "downmix", 0)
        add(add(group, "channel"), "index", channel)

    stereo = n_audio(ref_media) == 2
    for channel in range(1, n_a + 1):
        track_attrs = {}
        if stereo and audio_layout == "single":
            track_attrs = {"premiereTrackType": "Stereo"}
        elif stereo:
            track_attrs = {
                "currentExplodedTrackIndex": str(channel - 1),
                "totalExplodedTrackCount": "2",
                "premiereTrackType": "Stereo",
            }
        track = add(audio, "track", **track_attrs)
        add(track, "enabled", "TRUE")
        add(track, "locked", "FALSE")
        timeline_pos = 0
        for clip_index, (cut, duration) in enumerate(cut_frames, 1):
            src = cut_src(cut)
            in_frame = seconds_to_frames(cut.start, src.media.fps)
            out_frame = seconds_to_frames(cut.end, src.media.fps)
            video_id, audio_ids = clip_ids(cut)
            clipitem = add(track, "clipitem", id=audio_ids[channel - 1], frameBlend="FALSE")
            add(clipitem, "masterclipid", src.clip_id)
            add(clipitem, "name", f"{cut.index:02d}_{cut.label}")
            add(clipitem, "enabled", "TRUE")
            add(clipitem, "duration", duration)
            add(clipitem, "start", timeline_pos)
            add(clipitem, "end", timeline_pos + duration)
            add(clipitem, "in", in_frame)
            add(clipitem, "out", out_frame)
            add_file(clipitem, src)
            sourcetrack = add(clipitem, "sourcetrack")
            add(sourcetrack, "mediatype", "audio")
            add(sourcetrack, "trackindex", channel)
            add_links(clipitem, video_id, audio_ids, clip_index)
            timeline_pos += duration
        if audio_layout != "single":
            add(track, "outputchannelindex", channel)

    add_timecode(sequence, ref_media, with_reel=False)


def build_xml(
    project_name: str,
    sequence_name: str,
    cuts: list[Cut],
    sources: dict[str, SourceInfo],
    *,
    master_bin: bool = True,
    candidates: bool = True,
    audio_layout: str = "exploded",
) -> ET.Element:
    # 참조 XML(사용자 Premiere 내보내기)과 동일하게 version 4를 쓴다
    root = ET.Element("xmeml", version="4")
    project = add(root, "project")
    add(project, "name", project_name)
    children = add(project, "children")

    if master_bin:
        original_bin = add(children, "bin")
        add(original_bin, "name", "00_원본")
        original_children = add(original_bin, "children")
        for src in sources.values():
            add_master_clip(original_children, src)

    # 후보 구간은 clip(in/out)이 아니라 컷별 미니 시퀀스로 만든다.
    # Premiere는 bin clip의 in/out을 서브클립으로 인식하지 못하고
    # 원본 전체의 마스터 클립을 중복 생성하기 때문 (FCP7 XML 알려진 제약).
    if candidates:
        candidates_bin = add(children, "bin")
        add(candidates_bin, "name", "01_후보클립")
        candidates_children = add(candidates_bin, "children")
        for cut in cuts:
            add_sequence(
                candidates_children,
                f"{cut.index:02d}_{cut.label}",
                [cut],
                sources,
                seq_id=f"sequence-cand-{cut.index:03d}",
                id_prefix=f"cand-{cut.index:03d}",
                audio_layout=audio_layout,
            )

    sequence_bin = add(children, "bin")
    add(sequence_bin, "name", "02_시퀀스")
    sequence_children = add(sequence_bin, "children")
    add_sequence(sequence_children, sequence_name, cuts, sources, audio_layout=audio_layout)

    return root


def write_xml(path: Path, root: ET.Element) -> None:
    if path.exists():
        raise FileExistsError(f"출력 파일이 이미 존재함(덮어쓰기 금지): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="utf-8")
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + body + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="원본 영상 파일 또는 원본들이 있는 폴더 (폴더면 컷리스트의 원본파일 컬럼 사용)")
    parser.add_argument("cutlist", help="컷리스트 CSV")
    parser.add_argument("output_xml", help="생성할 Final Cut Pro 7 XML")
    parser.add_argument("--project-name", default="EDIT_ASSIST_V1")
    parser.add_argument("--sequence-name", default="러프컷_추천순서_v1")
    parser.add_argument(
        "--no-master-bin",
        action="store_true",
        help="00_원본 빈을 생략하고 Premiere가 마스터 클립을 자동 생성하게 한다",
    )
    parser.add_argument(
        "--no-candidates",
        action="store_true",
        help="01_후보클립 빈(컷별 미니 시퀀스)을 생략하고 원본+러프컷 시퀀스만 만든다",
    )
    parser.add_argument(
        "--audio-layout",
        choices=["exploded", "single"],
        default="exploded",
        help="exploded: 참조 XML의 모노 2트랙 분해 / single: 오디오 클립 1개",
    )
    args = parser.parse_args()

    source = Path(args.source)
    cutlist = Path(args.cutlist)
    output_xml = Path(args.output_xml)
    if not source.exists():
        sys.exit(f"원본 없음: {source}")
    if not cutlist.exists():
        sys.exit(f"컷리스트 없음: {cutlist}")

    cuts = read_cuts(cutlist)
    sources = resolve_sources(cuts, source)
    root = build_xml(args.project_name, args.sequence_name, cuts, sources, master_bin=not args.no_master_bin, candidates=not args.no_candidates, audio_layout=args.audio_layout)
    write_xml(output_xml, root)

    total = sum(cut.duration for cut in cuts)
    print(f"[premiere-xml] 원본 {len(sources)}개, 컷 {len(cuts)}개, 시퀀스 약 {format_seconds(total)}")
    print(f"[premiere-xml] 완료: {output_xml}")


if __name__ == "__main__":
    main()
