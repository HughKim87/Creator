"""Final Cut Pro 7 XML builder ported from the legacy
``skills/premiere-editing-export/scripts/make_premiere_xml.py``.

The algorithm and XML structure are preserved verbatim (characterization
tests frozen from the legacy suite guard this):

- xmeml version 4, master clip with uuid + self masterclipid + ismasterclip;
- mono-exploded audio tracks with premiereTrackType="Stereo" (CS6 limit);
- sequences start at 0, deterministic ordering, duplicate ids / zero-frame
  cuts / out-of-range cuts / mixed FPS / mixed channel counts are refused.

Intentional changes from legacy (recorded in the stage 04 report):
- media metadata comes through the frozen ``MediaProbe`` port instead of an
  ffprobe call with silent defaults;
- uuids are injectable so identical inputs can produce byte-identical XML
  in tests (default remains random uuid4, matching legacy).
"""

from __future__ import annotations

import csv
import uuid as uuid_module
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote

from video_workflow.adapters.media_probe import MediaInfo, MediaProbe


@dataclass
class Cut:
    index: int
    start: float
    end: float
    label: str
    role: str = ""
    source: str = ""
    sequence: str = ""
    cut_id: str = ""
    order: int = 0
    timeline_start: float | None = None
    video_track: int = 1
    audio_mode: str = "linked"
    audio_start: float | None = None
    audio_end: float | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start


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
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _column(header: dict[str, int], names: tuple[str, ...]) -> int | None:
    for name in names:
        if name in header:
            return header[name]
    return None


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def read_cuts(path: Path) -> list[Cut]:
    rows: list[list[str]] = []
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if not row or not any(cell.strip() for cell in row):
                continue
            if row[0].strip().startswith("#"):
                continue
            rows.append(row)
    if not rows:
        raise ValueError("컷리스트가 비어 있음")

    first = [cell.strip().lower() for cell in rows[0]]
    has_header = any(
        key in first for key in ("시작", "start", "start_time", "끝", "end", "end_time")
    )

    cuts: list[Cut] = []
    if has_header:
        header = {name: i for i, name in enumerate(first)}
        start_i = _column(header, ("시작", "start", "start_time"))
        end_i = _column(header, ("끝", "end", "end_time"))
        if start_i is None or end_i is None:
            raise ValueError("헤더 컷리스트에는 시작/끝 컬럼이 필요함")
        label_i = _column(header, ("구간명", "label", "name", "segment_name", "title"))
        role_i = _column(header, ("역할", "role", "note", "notes"))
        source_i = _column(header, ("원본파일", "원본", "source", "file", "filename"))
        sequence_i = _column(header, ("시퀀스", "sequence", "sequence_name"))
        cut_id_i = _column(header, ("cut_id", "컷id", "컷_id", "id"))
        order_i = _column(header, ("순서", "order"))
        timeline_start_i = _column(header, ("timeline_start", "타임라인시작"))
        video_track_i = _column(header, ("video_track", "비디오트랙"))
        audio_mode_i = _column(header, ("audio_mode", "오디오모드"))
        audio_start_i = _column(header, ("audio_start", "오디오시작"))
        audio_end_i = _column(header, ("audio_end", "오디오끝"))
        for i, row in enumerate(rows[1:], 1):
            start = parse_ts(row[start_i])
            end = parse_ts(row[end_i])
            if end <= start:
                raise ValueError(f"끝이 시작보다 빠름: {row}")
            label = _cell(row, label_i) or f"cut_{i:03d}"
            cut_id = _cell(row, cut_id_i) or f"cut_{i:03d}"
            order_text = _cell(row, order_i)
            timeline_text = _cell(row, timeline_start_i)
            video_track_text = _cell(row, video_track_i)
            audio_mode = _cell(row, audio_mode_i).lower() or "linked"
            audio_start_text = _cell(row, audio_start_i)
            audio_end_text = _cell(row, audio_end_i)
            cuts.append(
                Cut(
                    i,
                    start,
                    end,
                    label,
                    _cell(row, role_i),
                    _cell(row, source_i),
                    _cell(row, sequence_i),
                    cut_id,
                    int(order_text) if order_text else i,
                    parse_ts(timeline_text) if timeline_text else None,
                    int(video_track_text) if video_track_text else 1,
                    audio_mode,
                    parse_ts(audio_start_text) if audio_start_text else None,
                    parse_ts(audio_end_text) if audio_end_text else None,
                )
            )
    else:
        for i, row in enumerate(rows, 1):
            if len(row) < 2:
                raise ValueError(f"컷리스트 행에는 시작/끝이 필요함: {row}")
            start = parse_ts(row[0])
            end = parse_ts(row[1])
            if end <= start:
                raise ValueError(f"끝이 시작보다 빠름: {row}")
            label = row[2].strip() if len(row) > 2 else f"cut_{i:03d}"
            cuts.append(Cut(i, start, end, label, cut_id=f"cut_{i:03d}", order=i))
    return cuts


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


@dataclass
class BuildContext:
    files_written: set[str]
    uuid_factory: Callable[[], str] = field(default=lambda: str(uuid_module.uuid4()))


def resolve_sources(cuts: list[Cut], source_arg: Path, probe: MediaProbe) -> dict[str, SourceInfo]:
    """Map cut sources (file or folder argument) through the MediaProbe port."""
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
    for i, (source_name, path) in enumerate(paths.items(), 1):
        if not path.exists():
            raise FileNotFoundError(f"원본 없음: {path}")
        media = probe.probe(path)
        frames = seconds_to_frames(media.duration, media.fps)
        sources[source_name] = SourceInfo(i, path, media, frames)
    return sources


def validate_cuts(cuts: list[Cut], sources: dict[str, SourceInfo]) -> None:
    """조용한 보정 없이 XML 생성 전에 입력 결함을 명시적으로 실패시킨다."""
    if not cuts:
        raise ValueError("컷리스트가 비어 있음")

    fps_values = {src.media.fps for src in sources.values()}
    channel_values = {src.media.channels for src in sources.values()}
    if len(fps_values) > 1:
        raise ValueError(f"혼합 FPS는 지원하지 않음: {sorted(str(v) for v in fps_values)}")
    if len(channel_values) > 1:
        raise ValueError(f"혼합 오디오 채널 수는 지원하지 않음: {sorted(channel_values)}")

    seen_ids: set[str] = set()
    for cut in cuts:
        if cut.cut_id in seen_ids:
            raise ValueError(f"중복 cut_id: {cut.cut_id}")
        seen_ids.add(cut.cut_id)
        if cut.source not in sources:
            raise ValueError(f"알 수 없는 원본: {cut.source}")
        src = sources[cut.source]
        in_frame = seconds_to_frames(cut.start, src.media.fps)
        out_frame = seconds_to_frames(cut.end, src.media.fps)
        if in_frame < 0 or out_frame > src.frames:
            raise ValueError(
                f"소스 범위 밖 컷: {cut.cut_id} ({in_frame}~{out_frame}, source=0~{src.frames})"
            )
        if out_frame <= in_frame:
            raise ValueError(f"0프레임 컷: {cut.cut_id}")
        if cut.timeline_start is not None and cut.timeline_start < 0:
            raise ValueError(f"음수 timeline_start: {cut.cut_id}")
        if cut.video_track < 1:
            raise ValueError(f"video_track은 1 이상이어야 함: {cut.cut_id}")
        if cut.audio_mode not in {"linked", "none"}:
            raise ValueError(f"지원하지 않는 audio_mode: {cut.cut_id}={cut.audio_mode}")
        if cut.audio_mode == "none" and (cut.audio_start is not None or cut.audio_end is not None):
            raise ValueError(f"audio_mode=none에는 audio_start/end를 쓸 수 없음: {cut.cut_id}")
        if (cut.audio_start is None) != (cut.audio_end is None):
            raise ValueError(f"audio_start/end는 함께 지정해야 함: {cut.cut_id}")
        if cut.audio_mode != "none":
            audio_start = cut.start if cut.audio_start is None else cut.audio_start
            audio_end = cut.end if cut.audio_end is None else cut.audio_end
            audio_in = seconds_to_frames(audio_start, src.media.fps)
            audio_out = seconds_to_frames(audio_end, src.media.fps)
            if audio_in < 0 or audio_out > src.frames:
                raise ValueError(f"소스 범위 밖 오디오: {cut.cut_id}")
            if audio_out <= audio_in:
                raise ValueError(f"0프레임 오디오: {cut.cut_id}")


def group_cuts(cuts: list[Cut], fallback_name: str) -> OrderedDict[str, list[Cut]]:
    groups: OrderedDict[str, list[Cut]] = OrderedDict()
    for cut in cuts:
        groups.setdefault(cut.sequence or fallback_name, []).append(cut)
    for name in groups:
        groups[name].sort(key=lambda cut: (cut.order, cut.index))
    return groups


def add(parent: ET.Element, tag: str, text: str | int | None = None, **attrs: str) -> ET.Element:
    element = ET.SubElement(parent, tag, attrs)
    if text is not None:
        element.text = str(text)
    return element


def add_rate(parent: ET.Element, media: MediaInfo) -> ET.Element:
    # 참조 XML은 ntsc가 아니면 ntsc 요소를 쓰지 않는다.
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


def add_file(parent: ET.Element, src: SourceInfo, context: BuildContext) -> ET.Element:
    # 소스별 전체 file 정의는 문서에서 처음 한 번만 쓰고, 이후에는 id 참조만 쓴다.
    file_el = add(parent, "file", id=src.file_id)
    if src.file_id in context.files_written:
        return file_el
    context.files_written.add(src.file_id)
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


def add_links(
    clipitem: ET.Element,
    video_id: str,
    audio_ids: list[str],
    clip_index: int,
    *,
    video_track_index: int = 1,
    audio_clip_index: int | None = None,
) -> None:
    audio_clip_index = clip_index if audio_clip_index is None else audio_clip_index
    link = add(clipitem, "link")
    add(link, "linkclipref", video_id)
    add(link, "mediatype", "video")
    add(link, "trackindex", video_track_index)
    add(link, "clipindex", clip_index)
    for channel, audio_id in enumerate(audio_ids, 1):
        link = add(clipitem, "link")
        add(link, "linkclipref", audio_id)
        add(link, "mediatype", "audio")
        add(link, "trackindex", channel)
        add(link, "clipindex", audio_clip_index)
        add(link, "groupindex", 1)


def add_master_clip(parent: ET.Element, src: SourceInfo, context: BuildContext) -> None:
    # 참조 XML 구조: uuid + 자기참조 masterclipid + ismasterclip TRUE.
    media = src.media
    clip = add(parent, "clip", id=src.clip_id, frameBlend="FALSE")
    add(clip, "uuid", context.uuid_factory())
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
    add_file(clipitem, src, context)
    add_links(clipitem, video_id, audio_ids, 1)

    audio = add(clip_media, "audio")
    for channel in range(1, n_audio(media) + 1):
        track = add(audio, "track")
        clipitem = add(track, "clipitem", id=audio_ids[channel - 1], frameBlend="FALSE")
        add(clipitem, "masterclipid", src.clip_id)
        add(clipitem, "name", src.path.name)
        add_file(clipitem, src, context)
        sourcetrack = add(clipitem, "sourcetrack")
        add(sourcetrack, "mediatype", "audio")
        add(sourcetrack, "trackindex", channel)
        add_links(clipitem, video_id, audio_ids, 1)


@dataclass
class _LayoutItem:
    cut: Cut
    video_duration: int
    audio_duration: int
    audio_in: int | None
    audio_out: int | None
    timeline_start: int
    timeline_end: int
    video_clip_index: int
    audio_clip_index: int | None


def add_sequence(
    parent: ET.Element,
    name: str,
    cuts: list[Cut],
    sources: dict[str, SourceInfo],
    *,
    context: BuildContext,
    seq_id: str = "sequence-1",
    id_prefix: str = "seq-clip",
    audio_layout: str = "exploded",
) -> None:
    ref_media = sources[cuts[0].source].media

    def cut_src(cut: Cut) -> SourceInfo:
        return sources[cut.source]

    layout: list[_LayoutItem] = []
    cursor = 0
    video_clip_counts: dict[int, int] = defaultdict(int)
    audio_clip_count = 0
    for cut in cuts:
        src = cut_src(cut)
        in_frame = seconds_to_frames(cut.start, src.media.fps)
        out_frame = seconds_to_frames(cut.end, src.media.fps)
        video_duration = out_frame - in_frame
        timeline_start = (
            seconds_to_frames(cut.timeline_start, ref_media.fps)
            if cut.timeline_start is not None
            else cursor
        )
        audio_enabled = cut.audio_mode != "none"
        audio_in: int | None = None
        audio_out: int | None = None
        audio_duration = 0
        if audio_enabled:
            audio_in = seconds_to_frames(
                cut.start if cut.audio_start is None else cut.audio_start,
                src.media.fps,
            )
            audio_out = seconds_to_frames(
                cut.end if cut.audio_end is None else cut.audio_end,
                src.media.fps,
            )
            audio_duration = audio_out - audio_in
            audio_clip_count += 1
        video_clip_counts[cut.video_track] += 1
        timeline_end = timeline_start + max(video_duration, audio_duration)
        cursor = max(cursor, timeline_end)
        layout.append(
            _LayoutItem(
                cut=cut,
                video_duration=video_duration,
                audio_duration=audio_duration,
                audio_in=audio_in,
                audio_out=audio_out,
                timeline_start=timeline_start,
                timeline_end=timeline_end,
                video_clip_index=video_clip_counts[cut.video_track],
                audio_clip_index=audio_clip_count if audio_enabled else None,
            )
        )

    for track_index in sorted(video_clip_counts):
        intervals = sorted(
            (
                item.timeline_start,
                item.timeline_start + item.video_duration,
                item.cut.cut_id,
            )
            for item in layout
            if item.cut.video_track == track_index
        )
        for previous, current in zip(intervals, intervals[1:], strict=False):
            if current[0] < previous[1]:
                raise ValueError(
                    f"같은 비디오 트랙의 타임라인 중복: V{track_index} {previous[2]} / {current[2]}"
                )

    audio_intervals = sorted(
        (
            item.timeline_start,
            item.timeline_start + item.audio_duration,
            item.cut.cut_id,
        )
        for item in layout
        if item.audio_clip_index is not None
    )
    for previous, current in zip(audio_intervals, audio_intervals[1:], strict=False):
        if current[0] < previous[1]:
            raise ValueError(f"같은 오디오 레인의 타임라인 중복: {previous[2]} / {current[2]}")

    sequence_frames = max(item.timeline_end for item in layout)

    sequence = add(parent, "sequence", id=seq_id)
    add(sequence, "uuid", context.uuid_factory())
    add(sequence, "duration", sequence_frames)
    add_rate(sequence, ref_media)
    add(sequence, "name", name)
    sequence_media = add(sequence, "media")

    n_a = 1 if audio_layout == "single" else n_audio(ref_media)

    def clip_ids(cut: Cut) -> tuple[str, list[str]]:
        video_id = f"{id_prefix}-{cut.index:03d}-v"
        audio_ids = (
            [f"{id_prefix}-{cut.index:03d}-a{c}" for c in range(1, n_a + 1)]
            if cut.audio_mode != "none"
            else []
        )
        return video_id, audio_ids

    video = add(sequence_media, "video")
    fmt = add(video, "format")
    sample = add(fmt, "samplecharacteristics")
    add_rate(sample, ref_media)
    add(sample, "width", ref_media.width)
    add(sample, "height", ref_media.height)
    add(sample, "anamorphic", "FALSE")
    add(sample, "pixelaspectratio", "square")
    add(sample, "fielddominance", "none")

    for track_index in range(1, max(video_clip_counts) + 1):
        video_track = add(video, "track")
        add(video_track, "enabled", "TRUE")
        add(video_track, "locked", "FALSE")
        for item in layout:
            cut = item.cut
            if cut.video_track != track_index:
                continue
            src = cut_src(cut)
            in_frame = seconds_to_frames(cut.start, src.media.fps)
            out_frame = seconds_to_frames(cut.end, src.media.fps)
            video_id, audio_ids = clip_ids(cut)
            clipitem = add(video_track, "clipitem", id=video_id, frameBlend="FALSE")
            add(clipitem, "masterclipid", src.clip_id)
            add(clipitem, "name", f"{cut.index:02d}_{cut.label}")
            add(clipitem, "enabled", "TRUE")
            add(clipitem, "duration", src.frames)
            add(clipitem, "start", item.timeline_start)
            add(clipitem, "end", item.timeline_start + item.video_duration)
            add(clipitem, "in", in_frame)
            add(clipitem, "out", out_frame)
            add(clipitem, "alphatype", "none")
            add_file(clipitem, src, context)
            add_links(
                clipitem,
                video_id,
                audio_ids,
                item.video_clip_index,
                video_track_index=track_index,
                audio_clip_index=item.audio_clip_index,
            )

    # 참조 XML 구조: 모노 2트랙 분해 + premiereTrackType="Stereo" 트랙 속성.
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
        track_attrs: dict[str, str] = {}
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
        for item in layout:
            cut = item.cut
            if item.audio_clip_index is None:
                continue
            src = cut_src(cut)
            video_id, audio_ids = clip_ids(cut)
            clipitem = add(track, "clipitem", id=audio_ids[channel - 1], frameBlend="FALSE")
            add(clipitem, "masterclipid", src.clip_id)
            add(clipitem, "name", f"{cut.index:02d}_{cut.label}")
            add(clipitem, "enabled", "TRUE")
            add(clipitem, "duration", src.frames)
            add(clipitem, "start", item.timeline_start)
            add(clipitem, "end", item.timeline_start + item.audio_duration)
            add(clipitem, "in", item.audio_in)
            add(clipitem, "out", item.audio_out)
            add_file(clipitem, src, context)
            sourcetrack = add(clipitem, "sourcetrack")
            add(sourcetrack, "mediatype", "audio")
            add(sourcetrack, "trackindex", channel)
            add_links(
                clipitem,
                video_id,
                audio_ids,
                item.video_clip_index,
                video_track_index=cut.video_track,
                audio_clip_index=item.audio_clip_index,
            )
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
    uuid_factory: Callable[[], str] | None = None,
) -> ET.Element:
    validate_cuts(cuts, sources)
    context = BuildContext(files_written=set())
    if uuid_factory is not None:
        context.uuid_factory = uuid_factory
    sequence_groups = group_cuts(cuts, sequence_name)

    root = ET.Element("xmeml", version="4")
    project = add(root, "project")
    add(project, "name", project_name)
    children = add(project, "children")

    if master_bin:
        original_bin = add(children, "bin")
        add(original_bin, "name", "00_원본")
        original_children = add(original_bin, "children")
        for src in sources.values():
            add_master_clip(original_children, src, context)

    # 후보 구간은 clip(in/out)이 아니라 컷별 미니 시퀀스로 만든다 (FCP7 제약).
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
                context=context,
                seq_id=f"sequence-cand-{cut.index:03d}",
                id_prefix=f"cand-{cut.index:03d}",
                audio_layout=audio_layout,
            )

    sequence_bin = add(children, "bin")
    add(sequence_bin, "name", "02_시퀀스")
    sequence_children = add(sequence_bin, "children")
    for group_index, (group_name, group) in enumerate(sequence_groups.items(), 1):
        single_group = len(sequence_groups) == 1
        add_sequence(
            sequence_children,
            group_name,
            group,
            sources,
            context=context,
            seq_id="sequence-1" if single_group else f"sequence-main-{group_index:03d}",
            id_prefix="seq-clip" if single_group else f"seq-{group_index:03d}-clip",
            audio_layout=audio_layout,
        )

    return root


def write_xml(path: Path, root: ET.Element) -> None:
    if path.exists():
        raise FileExistsError(f"출력 파일이 이미 존재함(덮어쓰기 금지): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="utf-8")
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + body + b"\n")


def xml_bytes(root: ET.Element) -> bytes:
    """Serialized XML bytes (same layout as ``write_xml`` without the file)."""
    ET.indent(root, space="  ")
    body = bytes(ET.tostring(root, encoding="utf-8"))
    return b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + body + b"\n"
