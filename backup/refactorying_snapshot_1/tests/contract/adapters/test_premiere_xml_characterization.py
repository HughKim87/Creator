"""Characterization tests frozen from the legacy make_premiere_xml suite.

Assertions are ported 1:1 from ``backup/tests/test_make_premiere_xml.py``
(commit d5f5fb5). Expected values must not be adjusted to fit the new
implementation; a semantic difference from legacy is a failure.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from video_workflow.adapters.media_probe import MediaInfo
from video_workflow.adapters.premiere_xml import (
    Cut,
    SourceInfo,
    build_xml,
    group_cuts,
    read_cuts,
    seconds_to_frames,
    xml_bytes,
)


def _source(
    index: int = 1,
    name: str = "source.mp4",
    fps: Fraction = Fraction(60, 1),
    channels: int = 2,
) -> SourceInfo:
    media = MediaInfo(5000.0, 1920, 1080, fps, 48000, channels)
    return SourceInfo(index, Path(name), media, seconds_to_frames(media.duration, fps))


def _cut(
    index: int,
    start: float,
    end: float,
    *,
    sequence: str = "",
    cut_id: str = "",
    source: str = "source.mp4",
    order: int = 0,
    timeline_start: float | None = None,
    video_track: int = 1,
    audio_mode: str = "linked",
    audio_start: float | None = None,
    audio_end: float | None = None,
) -> Cut:
    return Cut(
        index,
        start,
        end,
        f"label_{index}",
        source=source,
        sequence=sequence,
        cut_id=cut_id or f"cut_{index}",
        order=order or index,
        timeline_start=timeline_start,
        video_track=video_track,
        audio_mode=audio_mode,
        audio_start=audio_start,
        audio_end=audio_end,
    )


def _build(cuts: list[Cut], sources: dict[str, SourceInfo] | None = None):  # type: ignore[no-untyped-def]
    sources = sources or {"source.mp4": _source()}
    return build_xml("TEST", "LEGACY_SEQUENCE", cuts, sources, candidates=False)


def test_source_and_timeline_frame_lengths_match() -> None:
    root = _build([_cut(1, 2119.78, 2120.29)])
    clip = root.find(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
    assert clip is not None
    timeline = int(clip.findtext("end") or 0) - int(clip.findtext("start") or 0)
    source = int(clip.findtext("out") or 0) - int(clip.findtext("in") or 0)
    assert source == timeline
    assert int(clip.findtext("duration") or 0) == 300000


def test_multi_sequence_groups_start_at_zero_and_follow_order() -> None:
    cuts = [
        _cut(1, 2.0, 3.0, sequence="SEQ_A", cut_id="A2", order=2),
        _cut(2, 0.0, 1.0, sequence="SEQ_A", cut_id="A1", order=1),
        _cut(3, 4.0, 5.0, sequence="SEQ_B", cut_id="B1", order=1),
    ]
    root = _build(cuts)
    sequences = root.findall(".//bin[name='02_시퀀스']/children/sequence")
    assert [s.findtext("name") for s in sequences] == ["SEQ_A", "SEQ_B"]
    assert [c.findtext("name") for c in sequences[0].findall("media/video/track/clipitem")] == [
        "02_label_2",
        "01_label_1",
    ]
    assert all(s.findtext("media/video/track/clipitem/start") == "0" for s in sequences)


def test_build_context_is_fresh_for_each_xml() -> None:
    cuts = [_cut(1, 0.0, 1.0)]
    first = _build(cuts)
    second = _build(cuts)
    assert len(first.findall(".//file/name")) == 1
    assert len(second.findall(".//file/name")) == 1


def test_rejects_duplicate_ids_zero_frame_and_mixed_media() -> None:
    with pytest.raises(ValueError, match="중복 cut_id"):
        _build([_cut(1, 0.0, 1.0, cut_id="dup"), _cut(2, 2.0, 3.0, cut_id="dup")])
    with pytest.raises(ValueError, match="0프레임 컷"):
        _build([_cut(1, 1.001, 1.002)])
    with pytest.raises(ValueError, match="소스 범위 밖 컷"):
        _build([_cut(1, 4999.0, 5001.0)])

    sources = {
        "source.mp4": _source(),
        "source2.mp4": _source(index=2, name="source2.mp4", fps=Fraction(30, 1)),
    }
    with pytest.raises(ValueError, match="혼합 FPS"):
        _build([_cut(1, 0.0, 1.0), _cut(2, 0.0, 1.0, source="source2.mp4")], sources)
    sources["source2.mp4"] = _source(index=2, name="source2.mp4", channels=1)
    with pytest.raises(ValueError, match="혼합 오디오 채널"):
        _build([_cut(1, 0.0, 1.0), _cut(2, 0.0, 1.0, source="source2.mp4")], sources)


def test_legacy_and_extended_csv_parsing(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.csv"
    legacy.write_text("0,1,one\n1,2,two\n", encoding="utf-8")
    legacy_cuts = read_cuts(legacy)
    assert [cut.label for cut in legacy_cuts] == ["one", "two"]
    assert [cut.cut_id for cut in legacy_cuts] == ["cut_001", "cut_002"]

    extended = tmp_path / "extended.csv"
    extended.write_text(
        "sequence,order,cut_id,start,end,label\nSEQ,2,C2,2,3,two\nSEQ,1,C1,0,1,one\n",
        encoding="utf-8",
    )
    grouped = group_cuts(read_cuts(extended), "fallback")
    assert [cut.cut_id for cut in grouped["SEQ"]] == ["C1", "C2"]


def test_cutaway_uses_second_video_track_without_interrupting_audio() -> None:
    cuts = [
        _cut(1, 0.0, 10.0, sequence="CAL", cut_id="BASE", timeline_start=0.0),
        _cut(
            2,
            20.0,
            23.0,
            sequence="CAL",
            cut_id="CUTAWAY",
            timeline_start=2.0,
            video_track=2,
            audio_mode="none",
        ),
    ]
    root = _build(cuts)
    sequence = root.find(".//bin[name='02_시퀀스']/children/sequence")
    assert sequence is not None
    video_tracks = sequence.findall("media/video/track")
    assert len(video_tracks) == 2
    assert [
        (item.findtext("start"), item.findtext("end"))
        for item in video_tracks[1].findall("clipitem")
    ] == [("120", "300")]
    audio_tracks = sequence.findall("media/audio/track")
    assert [len(track.findall("clipitem")) for track in audio_tracks] == [1, 1]
    assert sequence.findtext("duration") == "600"


def test_audio_source_range_can_differ_from_video_range() -> None:
    cuts = [_cut(1, 0.0, 5.0, audio_start=10.0, audio_end=16.0)]
    root = _build(cuts)
    sequence = root.find(".//bin[name='02_시퀀스']/children/sequence")
    assert sequence is not None
    video_clip = sequence.find("media/video/track/clipitem")
    audio_clip = sequence.find("media/audio/track/clipitem")
    assert video_clip is not None and audio_clip is not None
    assert (video_clip.findtext("in"), video_clip.findtext("out")) == ("0", "300")
    assert (audio_clip.findtext("in"), audio_clip.findtext("out")) == ("600", "960")
    assert (audio_clip.findtext("start"), audio_clip.findtext("end")) == ("0", "360")
    assert sequence.findtext("duration") == "360"


def test_extended_csv_parses_cutaway_fields(tmp_path: Path) -> None:
    path = tmp_path / "cutaway.csv"
    path.write_text(
        "sequence,order,cut_id,start,end,label,timeline_start,video_track,"
        "audio_mode,audio_start,audio_end\n"
        "CAL,1,C1,20,23,insert,2,2,none,,\n",
        encoding="utf-8",
    )
    cut = read_cuts(path)[0]
    assert cut.timeline_start == 2.0
    assert cut.video_track == 2
    assert cut.audio_mode == "none"


def test_sequential_layout_uses_absolute_source_frame_boundaries() -> None:
    cuts = [
        _cut(1, 2244.040, 2249.978, sequence="CAL", cut_id="B_HIDE"),
        _cut(2, 2253.990, 2260.940, sequence="CAL", cut_id="B_DOOR"),
    ]
    root = _build(cuts)
    clips = root.findall(".//bin[name='02_시퀀스']/children/sequence/media/video/track/clipitem")
    assert clips[0].findtext("end") == clips[1].findtext("start")
    for clip in clips:
        timeline = int(clip.findtext("end") or 0) - int(clip.findtext("start") or 0)
        source = int(clip.findtext("out") or 0) - int(clip.findtext("in") or 0)
        assert timeline == source


def test_identical_inputs_with_injected_uuids_are_byte_identical() -> None:
    """New guarantee: deterministic uuid injection -> byte-identical XML."""

    def build_once() -> bytes:
        counter = iter(range(1000))
        root = build_xml(
            "TEST",
            "SEQ",
            [_cut(1, 0.0, 1.0)],
            {"source.mp4": _source()},
            candidates=False,
            uuid_factory=lambda: f"00000000-0000-4000-8000-{next(counter):012d}",
        )
        return xml_bytes(root)

    assert build_once() == build_once()
