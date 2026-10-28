"""Content-bound scene cache for job-owned renderers, under the caller's job lease.

This is not a compositor or semantic reviewer. Callers supply exact authorized
inputs (including overlays), renderer dependencies, settings and output validation.
Final deliveries and historical revisions are never replaced here.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import uuid


def file_identity(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f'Not an input file: {path}')
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def scene_identity(scene_id, inputs, settings, renderer_inputs):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', scene_id):
        raise ValueError('Scene ID must be a simple name')
    if not inputs or not renderer_inputs:
        raise ValueError('Explicit media and renderer inputs are required')
    record = {'version': 1, 'scene': scene_id,
              'inputs': {k: file_identity(p) for k, p in inputs.items()},
              'renderers': {k: file_identity(p) for k, p in renderer_inputs.items()},
              'cache_implementation': file_identity(__file__), 'settings': settings}
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest(), record


def render_cached_scene(root, cache_dir, scene_id, *, inputs, settings,
                        renderer_inputs, render, validate):
    """Return (immutable-cache-path, reused); fail on missing/drifting inputs.

    render(output_path) must produce a scene MP4. validate(output_path) must
    raise if the real output is invalid (frames/PTS/decode as appropriate).
    Reuse checks content identity, not merely the existence of a segment.
    Caller holds the job lease; independent concurrent writers are unsupported.
    """
    root = Path(root).resolve(strict=True)
    cache = Path(cache_dir).resolve()
    jobs = (root / 'extension/jobs').resolve()
    core = (root / 'core').resolve()
    if (not jobs.is_relative_to(root) or jobs.is_relative_to(core)
            or not cache.is_relative_to(jobs) or cache == jobs
            or cache.is_relative_to(core)):
        raise ValueError('Scene cache must be inside a Consumer job')
    key, record = scene_identity(scene_id, inputs, settings, renderer_inputs)
    cache.mkdir(parents=True, exist_ok=True)
    target, metadata = cache / f'{key}.mp4', cache / f'{key}.json'
    if target.exists() or metadata.exists():
        if not target.is_file() or not metadata.is_file():
            raise ValueError('Incomplete scene cache; do not reuse')
        saved = json.loads(metadata.read_text(encoding='utf-8'))
        if saved.get('identity') != record or saved.get('output') != file_identity(target):
            raise ValueError('Damaged or mismatched scene cache; do not reuse')
        return target, True
    temporary = cache / f'.{key}.{uuid.uuid4().hex}.part.mp4'
    pending = cache / f'.{key}.{uuid.uuid4().hex}.part.json'
    try:
        render(temporary)
        validate(temporary)
        if scene_identity(scene_id, inputs, settings, renderer_inputs)[0] != key:
            raise ValueError('Scene inputs changed during rendering')
        output = file_identity(temporary)
        output['path'] = str(target)
        pending.write_text(json.dumps({'identity': record, 'output': output},
                                     ensure_ascii=False, sort_keys=True), encoding='utf-8')
        if target.exists() or metadata.exists():
            raise ValueError('Concurrent scene writer detected')
        os.replace(temporary, target)
        os.replace(pending, metadata)
        return target, False
    finally:
        temporary.unlink(missing_ok=True)
        pending.unlink(missing_ok=True)
