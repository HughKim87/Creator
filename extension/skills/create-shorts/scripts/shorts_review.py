"""Local preview/gallery/confirmation helpers. Editorial choices and ASR are agent work."""
import argparse
import functools
import hashlib
import http.server
import json
import math
import mimetypes
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('Time must be a finite number')
    return value


def duration(clip):
    return sum(p['end'] - p['start'] for p in clip['parts'])


def read_manifest(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', data['job_id']):
        raise ValueError('Invalid job_id')
    if not Path(data['source']).is_absolute():
        raise ValueError('Source must be absolute')
    limit = number(data['source_duration'])
    if limit <= 0 or not data['clips']:
        raise ValueError('Positive source duration and candidates required')
    ids, files = set(), set()
    for c in data['clips']:
        if not re.fullmatch(r'\d{3,}', c['id']) or c['id'] in ids:
            raise ValueError('Stable unique numeric IDs required')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', c['revision']):
            raise ValueError('Invalid revision')
        ids.add(c['id'])
        if not c['title'] or not c['reason'] or not c['category'] or not c['parts']:
            raise ValueError('Title, reason, category and parts required')
        last = -1
        for p in c['parts']:
            start, end = number(p['start']), number(p['end'])
            if not 0 <= start < end <= limit or start < last:
                raise ValueError('Parts must be ordered, disjoint and within source')
            last = end
        d = duration(c)
        if c.get('caption_status') not in ['unverified', 'aligned', 'user_confirmed']:
            raise ValueError('caption_status required')
        end = 0
        for cue in c.get('captions', []):
            start, stop = number(cue['start']), number(cue['end'])
            if not end <= start < stop <= d + .001 or not cue['text']:
                raise ValueError('Caption bounds/overlap/text invalid')
            end = stop
        issues = set()
        for issue in c.get('uncertain', []):
            if issue['id'] in issues or not issue['id'] or not issue['text'] or not issue['reason']:
                raise ValueError('Uncertainty IDs must be unique with text/reason')
            issues.add(issue['id'])
            if not 0 <= number(issue['start']) < number(issue['end']) <= d + .001:
                raise ValueError('Uncertainty bounds invalid')
        rel = c['file']
        if rel in files or Path(rel).is_absolute() or '..' in Path(rel).parts or '\\' in rel or ':' in rel:
            raise ValueError('Unique relative media paths inside root required')
        if not rel.lower().endswith('.mp4'):
            raise ValueError('MP4 previews required')
        files.add(rel)
    return data


def inside(root, relative):
    root = Path(root).resolve()
    p = (root / relative).resolve()
    if not p.is_relative_to(root):
        raise ValueError('Resolved path escapes job root')
    return p


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type,width,height,sample_aspect_ratio', '-of', 'json', str(path)]))


def check_preview(path, clip):
    info = probe(path)
    kinds = {s['codec_type'] for s in info['streams']}
    if not {'video', 'audio'} <= kinds or abs(float(info['format']['duration']) - duration(clip)) > .15:
        raise ValueError('Preview streams or duration mismatch: ' + clip['id'])


def previews(data, root):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise ValueError('Existing ffmpeg/ffprobe required; no installation performed')
    if not Path(data['source']).is_file():
        raise ValueError('Specified source does not exist')
    root.mkdir(parents=True, exist_ok=True)
    marker = root / '.preview-owner.json'
    source = Path(data['source']).resolve()
    stamp = source.stat()
    identity = hashlib.sha256((str(source) + ':' + str(stamp.st_size) + ':' + str(stamp.st_mtime_ns)).encode()).hexdigest()
    current = {'job_id': data['job_id'], 'source_identity': identity,
               'clips': {c['file']: {'id': c['id'], 'parts': c['parts'], 'revision': c['revision']} for c in data['clips']}}
    old = {}
    if marker.exists():
        old = json.loads(marker.read_text(encoding='utf-8'))
        if any(old.get(k) != current[k] for k in ['job_id', 'source_identity']):
            raise ValueError('Preview root belongs to another job/source')
    for c in data['clips']:
        path = inside(root, c['file'])
        old_clip = old.get('clips', {}).get(c['file'])
        if path.exists() and old_clip != current['clips'][c['file']]:
            raise ValueError('Unowned or changed existing preview; use a new revision/root')
    current['clips'] = {**old.get('clips', {}), **current['clips']}
    marker.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
    for c in data['clips']:
        if not c.get('active', True):
            continue
        out = inside(root, c['file'])
        if out == Path(data['source']).resolve():
            raise ValueError('Cannot write original source')
        if out.exists():
            check_preview(out, c)
            print('REUSED', c['id'], flush=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        temp = out.with_name(out.stem + '.partial.mp4')
        if temp.exists():
            raise ValueError('Partial collision; inspect it or choose new revision')
        args, filters = ['ffmpeg', '-v', 'error'], []
        for i, part in enumerate(c['parts']):
            length = part['end'] - part['start']
            args += ['-ss', str(part['start']), '-t', str(length), '-i', data['source']]
            filters += [f'[{i}:v]trim=duration={length},setpts=PTS-STARTPTS,fps=30,scale=640:-2,setsar=1,format=yuv420p[v{i}]',
                        f'[{i}:a]atrim=duration={length},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]']
        filters += [''.join(f'[v{i}][a{i}]' for i in range(len(c['parts']))) +
                    f'concat=n={len(c["parts"])}:v=1:a=1[v][a]']
        subprocess.run(args + ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
                       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '26', '-threads', '2',
                       '-filter_complex_threads', '2', '-c:a', 'aac', '-b:a', '96k',
                       '-t', str(duration(c)), '-movflags', '+faststart', '-n', str(temp)], check=True)
        check_preview(temp, c)
        if out.exists():
            raise ValueError('Destination appeared while rendering; not replaced')
        temp.rename(out)
        print('PREVIEW_READY', c['id'], flush=True)


def gallery(data, root):
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / 'manifest.json'
    if manifest.exists():
        previous = json.loads(manifest.read_text(encoding='utf-8'))
        if previous.get('job_id') != data['job_id']:
            raise ValueError('Gallery root belongs to another job')
    elif (root / 'index.html').exists():
        raise ValueError('Existing unowned index.html; choose a new job root')
    public = {k: data[k] for k in ['job_id', 'source_label', 'actual_listening'] if k in data}
    public['clips'] = []
    for c in data['clips']:
        if c.get('active', True) and not inside(root, c['file']).is_file():
            raise ValueError('Active preview missing: ' + c['id'])
        c = dict(c, duration=duration(c))
        public['clips'].append(c)
    template = (Path(__file__).resolve().parents[1] / 'assets/review.html').read_text(encoding='utf-8')
    encoded = json.dumps(public, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    (root / 'index.html').write_text(template.replace('__REVIEW_DATA__', encoded), encoding='utf-8')
    # Public data intentionally omits absolute input path and private ASR output.
    manifest.write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')
    print('GALLERY_READY', str(root / 'index.html'))


def final_gate(data, result):
    if result.get('job_id') != data['job_id'] or result.get('selection_only') is not True:
        raise ValueError('Wrong job or non-selection result')
    by_id = {c['id']: c for c in data['clips'] if c.get('active', True)}
    rows, seen = result.get('clips', []), set()
    if not rows:
        raise ValueError('No selected candidates')
    for row in rows:
        if row.get('selected') is not True or row['id'] not in by_id or row['id'] in seen:
            raise ValueError('Unknown/duplicate/inactive selection')
        seen.add(row['id'])
        c = by_id[row['id']]
        if row.get('revision') != c['revision'] or row.get('parts') != c['parts'] or c['caption_status'] == 'unverified':
            raise ValueError('Stale revision or unverified captions: ' + c['id'])
        confirmations = row.get('confirmations', [])
        if len({v['id'] for v in confirmations}) != len(confirmations):
            raise ValueError('Duplicate confirmations')
        confirms = {v['id']: v for v in confirmations}
        for issue in c.get('uncertain', []):
            v = confirms.get(issue['id'], {})
            if (v.get('confirmed') is not True or not str(v.get('replacement', '')).strip()
                    or any(v.get(k) != issue[k] for k in ['start', 'end', 'text'])):
                raise ValueError('User confirmation missing/stale: ' + c['id'] + '/' + issue['id'])
    return sorted(seen)


class RangeHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, root, **kwargs):
        self.root = Path(root).resolve()
        super().__init__(*args, **kwargs)

    def log_message(self, *args):
        pass

    def do_HEAD(self):
        self.respond(False)

    def do_GET(self):
        self.respond(True)

    def respond(self, body):
        raw = unquote(urlsplit(self.path).path)
        try:
            p = inside(self.root, raw.lstrip('/') or 'index.html')
        except (ValueError, OSError):
            self.send_error(403)
            return
        if not p.is_file():
            self.send_error(404)
            return
        size = p.stat().st_size
        start, end = 0, size - 1
        request = self.headers.get('Range')
        status = 200
        if request:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', request)
            if not match or not any(match.groups()) or size == 0:
                self.send_error(416)
                return
            left, right = match.groups()
            if left:
                start = int(left)
                end = min(int(right), end) if right else end
            else:
                start = max(0, size - int(right))
            if start >= size or end < start:
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            status = 206
        try:
            stream = p.open('rb')
        except OSError:
            self.send_error(404)
            return
        with stream:
            self.send_response(status)
            self.send_header('Content-Type', mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(max(0, end - start + 1)))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            if status == 206:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            if body:
                stream.seek(start)
                remaining = end - start + 1
                try:
                    while remaining > 0:
                        chunk = stream.read(min(262144, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['previews', 'gallery', 'final-gate']:
        p = sub.add_parser(name)
        p.add_argument('manifest')
        if name == 'final-gate':
            p.add_argument('--selection', required=True)
        else:
            p.add_argument('--root', type=Path, required=True)
    p = sub.add_parser('serve')
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    if args.command == 'serve':
        root = args.root.resolve(strict=True)
        if not (root / 'index.html').is_file() or not (root / 'manifest.json').is_file():
            parser.error('Owned gallery root required')
        server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(RangeHandler, root=root))
        print(f'REVIEW_URL=http://127.0.0.1:{server.server_port}/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return
    data = read_manifest(args.manifest)
    if args.command == 'previews':
        previews(data, args.root.resolve())
    elif args.command == 'gallery':
        gallery(data, args.root.resolve())
    else:
        result = json.loads(Path(args.selection).read_text(encoding='utf-8-sig'))
        print('CONFIRMATION_GATE_PASSED', ','.join(final_gate(data, result)))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'ERROR: {exc}')
