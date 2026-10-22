"""Render an original-based MP4 review candidate; never grants semantic approval."""
from __future__ import annotations
import argparse
from copy import deepcopy
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'extension/src'))
from creator_workspace import current_job_paths, runtime_path
from video_editing.delivery import _locked_source, _sha256_handle
from video_editing.editorial_state import validate_editorial_state
from video_editing.timeline_v2 import validate_timeline_v2, editorial_fingerprint
from video_editing.review_proxy import _check_streams, _check_timestamps


def checked_spec(value, state, **references):
    timeline = validate_timeline_v2(value, **references)
    if timeline['revision']['status'] != 'working_candidate' or timeline['validation']['semantic_status'] != 'not_run':
        raise ValueError('Only a working_candidate with semantic_status=not_run is accepted')
    if any(b['boundary_review'] == 'failed' for b in timeline['editorial_evidence']['microbeats']):
        raise ValueError('Known failed boundary must be fixed before rendering')
    evidence = validate_editorial_state(timeline, state)
    source = timeline['source_manifest']
    rate = Fraction(source['frame_rate']['numerator'], source['frame_rate']['denominator'])
    spf = Fraction(source['audio']['sample_rate'], 1) / rate
    if spf.denominator != 1:
        raise ValueError('Fractional audio samples per frame require a separate verified adapter')
    if source['audio']['channels'] not in (1, 2):
        raise ValueError('Only mono/stereo is supported')
    if source['video']['width'] % 2 or source['video']['height'] % 2:
        raise ValueError('yuv420p requires even dimensions; do not silently resize')
    for track in ('video', 'audio'):
        if any(c['gap_before'] for c in timeline['sequence'][track + '_clips']):
            raise ValueError('Source-native continuous A/V required; synthetic gaps are unsupported')
    frames = timeline['sequence']['video_clips'][-1]['timeline_end']
    return timeline, rate, int(spf), frames, evidence


def speech_findings(timeline, raw):
    """ASR hints only: an edge within a word is not a perceptual verdict."""
    rate = Fraction(timeline['source_manifest']['frame_rate']['numerator'], timeline['source_manifest']['frame_rate']['denominator'])
    words = [w for segment in raw.get('segments', []) for w in segment.get('words', [])]
    findings = []
    for clip in timeline['sequence']['audio_clips']:
        for edge in ('source_in', 'source_out'):
            point = float(Fraction(clip[edge], 1) / rate)
            for word in words:
                if float(word['start']) < point < float(word['end']):
                    findings.append(dict(clip_id=clip['id'], edge=edge, source_seconds=point,
                                         word=word.get('word'), status='needs_observation'))
    return findings


def run(args, cwd):
    result = subprocess.run([str(x) for x in args], cwd=cwd, stdin=subprocess.DEVNULL,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-3000:])
    return result.stdout


def probe(binary, media, cwd):
    result = json.loads(run([binary, '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', media], cwd))
    videos = [s for s in result['streams'] if s['codec_type'] == 'video']
    audios = [s for s in result['streams'] if s['codec_type'] == 'audio']
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError('Exactly one video and one audio stream required; select/mix tracks explicitly first')
    return {'video': videos[0], 'audio': audios[0]}


def canonical(path):
    path = Path(path)
    if not path.is_absolute() or os.path.normcase(str(path)) != os.path.normcase(str(path.resolve())):
        raise ValueError('An absolute canonical path is required')
    return path


def render(value, state, *, work, output, ffmpeg, ffprobe, references=None):
    before = deepcopy(value)
    timeline, rate, spf, frames, editorial = checked_spec(value, state, **(references or {}))
    source = timeline['source_manifest']
    source_path = canonical(source['path'])
    target, scratch = canonical(output), canonical(work)
    if target.suffix.lower() != '.mp4' or target.exists() or target == source_path:
        raise ValueError('A new non-colliding .mp4 output is required')
    if not target.parent.is_dir() or not scratch.is_dir():
        raise ValueError('Exact existing output and work directories required')
    expected = (source['content_sha256'], source['byte_size'])
    with _locked_source(source_path) as handle:
        if _sha256_handle(handle) != expected:
            raise ValueError('Source hash/size mismatch')
        observed = probe(ffprobe, source_path, scratch)
        _check_streams(observed, source, source['total_frames'])
        _check_timestamps(ffprobe, source_path, scratch, observed, rate)
        with tempfile.TemporaryDirectory(prefix='candidate-', dir=scratch) as directory:
            temp = Path(directory)
            # Decode audio once, then copy exact sample ranges. Container seek
            # can quantize audio and shift speech even when duration is correct.
            original_pcm = temp / 'source-audio.f32'
            assembled_pcm = temp / 'assembled-audio.f32'
            run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-i', source_path,
                 '-map', '0:a:0', '-vn', '-c:a', 'pcm_f32le', '-f', 'f32le', '-n', original_pcm], temp)
            sample_bytes = source['audio']['channels'] * 4
            with original_pcm.open('rb') as decoded, assembled_pcm.open('xb') as assembled:
                for clip in timeline['sequence']['audio_clips']:
                    decoded.seek(clip['source_in'] * spf * sample_bytes)
                    remaining = clip['frames'] * spf * sample_bytes
                    while remaining:
                        chunk = decoded.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError('Original decoded audio is shorter than the planned source samples')
                        assembled.write(chunk)
                        remaining -= len(chunk)
            names = []
            for index, clip in enumerate(timeline['sequence']['video_clips']):
                a, b = clip['source_in'], clip['source_out']
                name = f'video-{index:05d}.mp4'
                seek = format(float(Fraction(a, 1) / rate), '.12f')
                run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-ss', seek, '-i', source_path,
                     '-map', '0:v:0', '-an', '-vf', f'trim=start_frame=0:end_frame={b-a},setpts=PTS-STARTPTS',
                     '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-pix_fmt', 'yuv420p',
                     '-fps_mode', 'passthrough', '-n', temp / name], temp)
                names.append(name)
            listing = temp / 'video.ffconcat'
            listing.write_text('ffconcat version 1.0\n' + ''.join('file ' + n + '\n' for n in names), encoding='utf-8')
            joined_video = temp / 'joined-video.mp4'
            run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-f', 'concat', '-safe', '0', '-i', listing,
                 '-map', '0:v:0', '-c:v', 'copy', '-n', joined_video], temp)
            result = temp / 'candidate.mp4'
            run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-i', joined_video,
                 '-f', 'f32le', '-ar', source['audio']['sample_rate'], '-ac', source['audio']['channels'], '-i', assembled_pcm,
                 '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                 '-movflags', '+faststart', '-n', result], temp)
            measured = probe(ffprobe, result, temp)
            _check_streams(measured, source, frames)
            _check_timestamps(ffprobe, result, temp, measured, rate)
            # Count full decoded audio without keeping a huge PCM file in memory.
            pcm = temp / 'audio-check.f32'
            run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-i', result, '-map', '0:a:0', '-c:a', 'pcm_f32le', '-f', 'f32le', '-n', pcm], temp)
            samples, remainder = divmod(pcm.stat().st_size, 4 * source['audio']['channels'])
            padding = samples - frames * spf
            if remainder or not 0 <= padding < 1024:
                raise ValueError('Decoded audio length differs beyond AAC tail padding')
            if _sha256_handle(handle) != expected:
                raise ValueError('Source drift before publication')
            with result.open('rb') as rendered:
                digest, size = _sha256_handle(rendered)
            # Atomic no-clobber, including a race after the initial existence check.
            os.link(result, target)
    assert value == before
    return dict(status='working_candidate', output=str(target), video_sha256=digest, bytes=size,
                editorial_fingerprint=editorial_fingerprint(timeline), editorial_structure=editorial,
                frames=frames, duration_seconds=float(Fraction(frames, 1) / rate), decoded_audio_samples=samples,
                aac_tail_padding_samples=padding, technical_status='passed', semantic_status='not_run',
                direct_listening='not_run', user_approval='not_run',
                limitations=['Source and output geometry/rate/count/continuous timestamps checked; visual meaning, speech quality, colour fidelity and user approval are not established.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeline-json', required=True, type=Path)
    parser.add_argument('--editorial-state-json', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--raw-json', type=Path, help='Original raw transcript, for ASR word-edge hints only')
    parser.add_argument('--check-only', action='store_true', help='Metadata checks only; no media access or approval')
    parser.add_argument('--calibration-timeline-json', type=Path)
    parser.add_argument('--baseline-timeline-json', type=Path)
    parser.add_argument('--reference-timeline-json', type=Path, action='append', default=[])
    args = parser.parse_args()
    read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    value, state = read(args.timeline_json), read(args.editorial_state_json)
    refs = dict(calibration_reference=read(args.calibration_timeline_json) if args.calibration_timeline_json else None,
                baseline_reference=read(args.baseline_timeline_json) if args.baseline_timeline_json else None,
                reference_payloads=[read(p) for p in args.reference_timeline_json])
    timeline, _, _, frames, editorial = checked_spec(value, state, **refs)
    # Optional input must be readable and analyzable before render can publish.
    findings = speech_findings(timeline, read(args.raw_json)) if args.raw_json else None
    if args.check_only:
        result = dict(status='structure_checked', frames=frames, editorial_structure=editorial, semantic_status='not_run')
    else:
        paths = current_job_paths(ROOT)
        if paths is None or args.output is None:
            raise ValueError('Run under creator_job.py run with --output')
        target = canonical(args.output)
        if not target.is_relative_to(paths['outputs']) or target == paths['outputs']:
            raise ValueError('Output must stay inside the current job outputs')
        tools = runtime_path('ffmpeg', ROOT) / 'bin'
        result = render(value, state, work=paths['work'], output=target,
                        ffmpeg=tools / 'ffmpeg.exe', ffprobe=tools / 'ffprobe.exe', references=refs)
    if findings is not None:
        result['asr_word_edge_findings'] = findings
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)