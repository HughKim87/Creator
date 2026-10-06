"""Source-authored scene intent, omission coverage and persistent feedback.

Checks declared evidence, not perceptual truth. Callers supply the authoritative
latest state; an omitted newer state cannot be discovered from a snapshot.
"""
from copy import deepcopy
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
import re

from .premiere_xml import PremiereXmlError
from .timeline_v2 import editorial_fingerprint, source_manifest_fingerprint


def _require(ok, message):
    if not ok:
        raise PremiereXmlError('editorial state: ' + message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _object(value, fields, label):
    _require(isinstance(value, Mapping) and set(value) == set(fields.split()), label + ' fields invalid')


def _list(value, label, nonempty=False):
    _require(isinstance(value, list) and (not nonempty or bool(value)), label + ' list required')
    return value


def _range(value, total, label):
    a, b = value.get('source_in'), value.get('source_out')
    _require(type(a) is int and type(b) is int and 0 <= a < b <= total, label + ' range invalid')
    return a, b


def _union(ranges):
    result = []
    for a, b in sorted(ranges):
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def _subtract(a, b, ranges):
    cursor = a
    result = []
    for x, y in _union(ranges):
        x, y = max(x, a), min(y, b)
        if y <= cursor or x >= b:
            continue
        if cursor < x:
            result.append((cursor, x))
        cursor = max(cursor, y)
    if cursor < b:
        result.append((cursor, b))
    return result


def editorial_state_fingerprint(state):
    return 'sha256:' + hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def editorial_basis_fingerprint(state):
    """Bind a review to the exact plan and feedback, excluding review records."""
    return editorial_state_fingerprint({k: v for k, v in state.items() if k != "reviews"})


def _plan(timeline, state, *, allow_draft=False):
    _object(state, 'version source_manifest_fingerprint generation scenes feedback reviews', 'state')
    _require(state['version'] == 'editorial-state-v1', 'unsupported version')
    _require(state['source_manifest_fingerprint'] == source_manifest_fingerprint(timeline['source_manifest']), 'source mismatch')
    _require(type(state['generation']) is int and state['generation'] >= 1, 'generation invalid')
    total = timeline['source_manifest']['total_frames']
    scenes = _list(state['scenes'], 'scenes', not allow_draft)
    ids, anchors, ranges = set(), {}, []
    for scene in scenes:
        _object(scene, 'id source_in source_out show viewer_learns next_action_reason depends_on anchors', 'scene')
        _require(_text(scene['id']) and scene['id'] not in ids, 'duplicate or missing scene id')
        for name in ('show', 'viewer_learns', 'next_action_reason'):
            _require(_text(scene[name]), 'scene ' + name + ' required')
        dependencies = _list(scene['depends_on'], 'scene dependencies')
        _require(all(_text(i) and i in ids for i in dependencies) and len(set(dependencies)) == len(dependencies), 'scene dependency must precede scene')
        ids.add(scene['id'])
        a, b = _range(scene, total, 'scene')
        _require(not any(a < y and x < b for x, y in ranges), 'overlapping scene scopes')
        ranges.append((a, b))
        for anchor in _list(scene['anchors'], 'anchors', True):
            _object(anchor, 'id source_in source_out media_scope observation', 'anchor')
            _require(_text(anchor['id']) and anchor['id'] not in anchors, 'duplicate or missing anchor id')
            x, y = _range(anchor, total, 'anchor')
            _require(a <= x < y <= b, 'anchor outside scene')
            _require(anchor['media_scope'] in ('video', 'audio', 'both'), 'anchor media scope invalid')
            _require(_text(anchor['observation']), 'anchor observation required')
            anchors[anchor['id']] = anchor
    return scenes, anchors, ranges


def derive_omissions(timeline, state):
    """Complement of selected source union in each declared scene, per medium.

Does not invent reasons or infer unexamined source outside those scene scopes.
"""
    scenes, _, scopes = _plan(timeline, state)
    result = []
    for track in ('video', 'audio'):
        clips = timeline['sequence'][track + '_clips']
        retained = [(c['source_in'], c['source_out']) for c in clips]
        for a, b in retained:
            _require(not _subtract(a, b, scopes), 'retained source outside planned scenes')
        for scene in scenes:
            for a, b in _subtract(scene['source_in'], scene['source_out'], retained):
                result.append(dict(scene_id=scene['id'], track=track, source_in=a, source_out=b))
    return result


def _feedback(state):
    seen = set()
    for item in _list(state['feedback'], 'feedback'):
        _object(item, 'id target_editorial_fingerprint symptom required_anchor_ids reported_by reported_at', 'feedback')
        _require(_text(item['id']) and item['id'] not in seen, 'duplicate or missing feedback id')
        seen.add(item['id'])
        _require(isinstance(item['target_editorial_fingerprint'], str) and re.fullmatch(r'sha256:[0-9a-f]{64}', item['target_editorial_fingerprint']), 'feedback target invalid')
        _require(_text(item['symptom']) and _text(item['reported_by']), 'feedback provenance required')
        try:
            stamp = datetime.fromisoformat(item['reported_at'])
            _require(stamp.tzinfo is not None and stamp <= datetime.now(timezone.utc), 'feedback time invalid')
        except (TypeError, ValueError):
            raise PremiereXmlError('editorial state: feedback time invalid') from None
        ids = _list(item['required_anchor_ids'], 'feedback anchors')
        _require(all(_text(i) for i in ids) and len(set(ids)) == len(ids), 'feedback anchors invalid')
    return seen


def validate_editorial_state(timeline, state):
    scenes, anchors, _ = _plan(timeline, state)
    omissions = derive_omissions(timeline, state)
    fp = editorial_fingerprint(timeline)
    feedback_ids = _feedback(state)
    _require(all(f['target_editorial_fingerprint'] != fp for f in state['feedback']), 'reported defective edit cannot be re-exported')
    matches = []
    for review in _list(state['reviews'], 'reviews'):
        _object(review, 'editorial_fingerprint state_basis_fingerprint generation omissions resolutions', 'candidate review')
        if review['editorial_fingerprint'] == fp:
            matches.append(review)
    _require(len(matches) == 1, 'exactly one current candidate review required')
    review = matches[0]
    _require(review['state_basis_fingerprint'] == editorial_basis_fingerprint(state), 'candidate review uses a stale plan or feedback')
    _require(type(review['generation']) is int and review['generation'] == state['generation'], 'stale candidate review')
    expected = {(d['scene_id'], d['track'], d['source_in'], d['source_out']) for d in omissions}
    actual = set()
    for decision in _list(review['omissions'], 'omission decisions'):
        _object(decision, 'scene_id track source_in source_out reason observation certainty', 'omission')
        _range(decision, timeline['source_manifest']['total_frames'], 'omission')
        _require(_text(decision['scene_id']) and decision['track'] in ('video', 'audio'), 'omission identity invalid')
        key = (decision['scene_id'], decision['track'], decision['source_in'], decision['source_out'])
        _require(key not in actual, 'duplicate omission decision')
        actual.add(key)
        _require(decision['certainty'] == 'confirmed', 'uncertain omission must be retained or inspected')
        _require(_text(decision['reason']) and _text(decision['observation']), 'omission observation and reason required')
    _require(actual == expected, 'every actual omission needs an exact decision; stale or missing coverage')
    # Retention must form one forward, uninterrupted timeline run. Union alone
    # would incorrectly accept a reversed or reordered look-back action.
    locations = {}
    for aid, anchor in anchors.items():
        positions = []
        tracks = ('video', 'audio') if anchor['media_scope'] == 'both' else (anchor['media_scope'],)
        for track in tracks:
            a, b = anchor['source_in'], anchor['source_out']
            pieces = []
            for clip in timeline['sequence'][track + '_clips']:
                x, y = max(a, clip['source_in']), min(b, clip['source_out'])
                if x < y:
                    pieces.append((clip['timeline_start'] + x - clip['source_in'], x, y))
            pieces.sort()
            cursor, end = a, None
            _require(bool(pieces), 'required anchor missing: ' + aid)
            for start, x, y in pieces:
                _require(x == cursor and (end is None or start == end), 'required anchor cut or reordered: ' + aid)
                cursor, end = y, start + y - x
            _require(cursor == b, 'required anchor partially deleted: ' + aid)
            positions.append((pieces[0][0], end))
        locations[aid] = (min(a for a, _ in positions), max(b for _, b in positions))
    scene_positions = {}
    for scene in scenes:
        p = [locations[a['id']] for a in scene['anchors']]
        start, end = min(a for a, _ in p), max(b for _, b in p)
        for dep in scene['depends_on']:
            _require(scene_positions[dep][1] <= start, 'required scene cause appears after its result')
        scene_positions[scene['id']] = (start, end)
    resolutions = {}
    for resolution in _list(review['resolutions'], 'resolutions'):
        _object(resolution, 'feedback_id anchor_ids evidence', 'resolution')
        fid = resolution['feedback_id']
        _require(_text(fid) and fid in feedback_ids and fid not in resolutions, 'unknown or duplicate feedback resolution')
        aids = _list(resolution['anchor_ids'], 'resolution anchors', True)
        _require(all(_text(i) and i in anchors for i in aids) and len(set(aids)) == len(aids), 'resolution needs known retained anchors')
        _require(_text(resolution['evidence']), 'resolution evidence required')
        resolutions[fid] = resolution
    _require(set(resolutions) == feedback_ids, 'unresolved feedback must carry forward to every candidate')
    for item in state['feedback']:
        _require(set(item['required_anchor_ids']) <= set(resolutions[item['id']]['anchor_ids']), 'resolution omits required feedback anchors')
    return dict(status='structure_checked', editorial_state_fingerprint=editorial_state_fingerprint(state), omissions=len(omissions), required_anchors=len(anchors), feedback=len(feedback_ids), semantic_status=timeline['validation']['semantic_status'], limitation='Declared evidence checked; perceptual truth and unprovided newer state are not verified.')


def record_editorial_feedback(timeline, state, *, feedback_id, symptom, reported_by, required_anchor_ids=()):
    """Return a new state; preserve plan and prior feedback, invalidate all reviews.

Save as the authoritative task state before further delivery. No approval or
semantic pass is granted or carried by this transition.
"""
    _plan(timeline, state, allow_draft=True)
    seen = _feedback(state)
    _require(_text(feedback_id) and feedback_id not in seen, 'feedback id already exists or invalid')
    _require(_text(symptom) and _text(reported_by), 'feedback symptom and reporter required')
    result = deepcopy(state)
    result['generation'] += 1
    result['reviews'] = []
    result['feedback'].append(dict(id=feedback_id, target_editorial_fingerprint=editorial_fingerprint(timeline), symptom=symptom, required_anchor_ids=list(required_anchor_ids), reported_by=reported_by, reported_at=datetime.now(timezone.utc).isoformat()))
    _feedback(result)
    return result
